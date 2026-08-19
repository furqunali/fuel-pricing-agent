# -*- coding: utf-8 -*-
"""TOOL: excel_writer — fill the Excel workbook from the price matrix.

Preserves every chart/format by editing sheet XML directly (no full re-save):
  1. DATA_ENTRY  : drop values into the pre-built empty brand cells for each date.
  2. workbook    : set fullCalcOnLoad so DASHBOARD/REPORT recalc on open.
  3. SUMMARY     : insert AVERAGEIFS formulas for Jun-Dec (auto-updating).
  4. VALERO      : auto-fill comparison blocks via openpyxl (charts survive).
"""
import os
import re
import shutil
import zipfile
import datetime

import openpyxl
from openpyxl.utils import get_column_letter as GL

MONTHS12 = ["January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"]
FILL_MONTHS = {"June", "July", "August", "September", "October", "November", "December"}
SUM_BASE = {"Regular": 4, "Midgrade": 16, "Premium": 28, "Diesel": 40}
PRODUCTS = ["Regular", "Midgrade", "Premium", "Diesel"]
VALERO_ALIAS = {
    "Valero - Rack": "Valero - Rack",
    "Valero - Formula": "Valero - Formula",
    "Valero Unbranded": "Valero Houston Unbranded - Rack",
}


def _sheet_part(z, sheet_name):
    wbx = z.read('xl/workbook.xml').decode('utf-8', 'ignore')
    rels = z.read('xl/_rels/workbook.xml.rels').decode('utf-8', 'ignore')
    rid = dict(re.findall(r'<sheet name="([^"]+)"[^>]*r:id="(rId\d+)"', wbx))[sheet_name]
    target = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="worksheets/(sheet\d+\.xml)"', rels))[rid]
    return 'xl/worksheets/' + target


def _summary_xml(xml, brands, column_map, year):
    targets = {}
    for product, base in SUM_BASE.items():
        for mi, mon in enumerate(MONTHS12):
            if mon in FILL_MONTHS:
                targets[base + mi] = (product, mon)

    def rebuild(m):
        rowxml = m.group(0)
        rn = int(re.match(r'<row r="(\d+)"', rowxml).group(1))
        if rn not in targets:
            return rowxml
        product, mon = targets[rn]
        opentag = re.match(r'<row[^>]*>', rowxml).group(0)
        acell = re.search(r'<c r="A%d".*?(?:/>|</c>)' % rn, rowxml).group(0)
        bcell = re.search(r'<c r="B%d".*?(?:/>|</c>)' % rn, rowxml).group(0)
        sm = re.search(r'<c r="A%d"[^>]*?s="(\d+)"' % rn, rowxml)
        style = sm.group(1) if sm else "42"
        out = [opentag, acell, bcell]
        for i, brand in enumerate(brands):
            ref = "%s%d" % (GL(3 + i), rn)
            if column_map.get(brand):
                dcol = GL(5 + i)
                f = ('IFERROR(AVERAGEIFS(DATA_ENTRY!%s$5:%s$2924,DATA_ENTRY!$B$5:$B$2924,"%s",'
                     'DATA_ENTRY!$D$5:$D$2924,"%s",DATA_ENTRY!$AD$5:$AD$2924,%d),"")'
                     % (dcol, dcol, product, mon, year))
                out.append('<c r="%s" s="%s"><f>%s</f></c>' % (ref, style, f))
            else:
                ex = re.search(r'<c r="%s".*?(?:/>|</c>)' % ref, rowxml)
                if ex:
                    out.append(ex.group(0))
        out.append("</row>")
        return "".join(out)

    return re.sub(r'<row r="\d+"[^>]*>.*?</row>', rebuild, xml, flags=re.S)


def _fill_valero(ws, brands, column_map, year):
    b2col = {b: GL(5 + i) for i, b in enumerate(brands)}
    header_rows = [r for r in range(1, ws.max_row + 1)
                   if any(ws.cell(r, c).value == "Month" for c in range(1, ws.max_column + 1))]
    filled = 0
    for hr in header_rows:
        for mc in [c for c in range(1, ws.max_column + 1) if ws.cell(hr, c).value == "Month"]:
            v1c, v2c, dc = mc + 3, mc + 4, mc + 5
            h1, h2 = ws.cell(hr, v1c).value, ws.cell(hr, v2c).value
            b1 = VALERO_ALIAS.get(str(h1).strip()) if h1 else None
            b2 = VALERO_ALIAS.get(str(h2).strip()) if h2 else None
            if not b1 or not b2 or not column_map.get(b1) or not column_map.get(b2):
                continue
            de1, de2 = b2col[b1], b2col[b2]
            dhdr = ws.cell(hr, dc).value
            isdiff = isinstance(dhdr, str) and dhdr.strip().lower().startswith("diff")
            for dr in range(hr + 1, hr + 13):
                mon, prod = ws.cell(dr, mc).value, ws.cell(dr, mc + 1).value
                if mon not in FILL_MONTHS or ws.cell(dr, v1c).value not in (None, "-"):
                    continue
                fm = ('=IFERROR(AVERAGEIFS(DATA_ENTRY!{c}$5:{c}$2924,DATA_ENTRY!$B$5:$B$2924,"{p}",'
                      'DATA_ENTRY!$D$5:$D$2924,"{m}",DATA_ENTRY!$AD$5:$AD$2924,{y}),"")')
                ws.cell(dr, v1c).value = fm.format(c=de1, p=prod, m=mon, y=year)
                ws.cell(dr, v2c).value = fm.format(c=de2, p=prod, m=mon, y=year)
                if isdiff:
                    ws.cell(dr, dc).value = '=IFERROR(%s%d-%s%d,"")' % (GL(v1c), dr, GL(v2c), dr)
                filled += 1
    return filled


def write_excel(template_xlsx, out_xlsx, colseries, dates, brands, config):
    year = config.get("year", 2026)
    column_map = config["column_map"]

    # (date, product) -> DATA_ENTRY row
    wb = openpyxl.load_workbook(template_xlsx, data_only=False, read_only=True)
    ws = wb["DATA_ENTRY"]
    rowmap = {}
    for row in ws.iter_rows(min_row=5, max_col=2):
        a, b = row[0].value, row[1].value
        if isinstance(a, datetime.datetime):
            rowmap[(a.date(), b)] = row[0].row
    wb.close()

    targets = {}
    for d in dates:
        for p in PRODUCTS:
            r = rowmap.get((d, p))
            if not r:
                continue
            for i, brand in enumerate(brands):
                if column_map.get(brand):
                    v = colseries.get(brand, {}).get(p, {}).get(d)
                    if v is not None:
                        targets["%s%d" % (GL(5 + i), r)] = v

    zin = zipfile.ZipFile(template_xlsx)
    de_part = _sheet_part(zin, "DATA_ENTRY")
    sum_part = _sheet_part(zin, "SUMMARY")
    de_xml = zin.read(de_part).decode('utf-8')
    zin.close()

    def repl(m):
        ref, s = m.group(1), m.group(2)
        if ref in targets:
            return '<c r="%s" s="%s"><v>%s</v></c>' % (ref, s, targets[ref])
        return m.group(0)
    de_xml2 = re.sub(r'<c r="([A-Z]+\d+)" s="(\d+)"/>', repl, de_xml)

    tmp = out_xlsx + ".tmp"
    with zipfile.ZipFile(template_xlsx) as zin, \
            zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
        for it in zin.infolist():
            data = zin.read(it.filename)
            if it.filename == de_part:
                data = de_xml2.encode('utf-8')
            elif it.filename == sum_part:
                data = _summary_xml(data.decode('utf-8'), brands, column_map, year).encode('utf-8')
            elif it.filename == 'xl/workbook.xml':
                w = data.decode('utf-8')
                if 'fullCalcOnLoad' not in w:
                    w = re.sub(r'(<calcPr[^>]*?)/>', r'\1 fullCalcOnLoad="1"/>', w)
                data = w.encode('utf-8')
            zout.writestr(it, data)
    os.replace(tmp, out_xlsx)

    # Comparison tabs via openpyxl (preserves the charts)
    from . import comparison_filler
    wbx = openpyxl.load_workbook(out_xlsx)
    if "VALERO" in wbx.sheetnames:
        _fill_valero(wbx["VALERO"], brands, column_map, year)
    if "COMPARISONS" in wbx.sheetnames:
        comparison_filler.fill_exact_name(wbx["COMPARISONS"], brands, column_map, year)
    wbx.save(out_xlsx)

    return len(targets)
