# -*- coding: utf-8 -*-
"""TOOL: pdi_reader — read a PDI 'FI Fuel Costs' .XLS export into price events.

Reusable: auto-detects the Effective/Cost columns from the report header, so it
keeps working if PDI shifts the layout slightly. Returns a list of dicts:
  {terminal, grade, effective (datetime), cost (float)}
"""
import datetime
import xlrd


def _excel_dt(serial):
    return datetime.datetime(1899, 12, 30) + datetime.timedelta(days=float(serial))


def _detect_columns(sheet):
    """Find the column indexes of 'Effective Date' and 'Cost' from the header row."""
    eff_col, cost_col = 10, 16  # PDI defaults (fallback)
    for r in range(min(sheet.nrows, 40)):
        for c in range(sheet.ncols):
            v = str(sheet.cell_value(r, c)).strip().lower()
            if v.startswith("effective date"):
                eff_col = c
            elif v == "cost":
                cost_col = c
    return eff_col, cost_col


def read_pdi_file(path):
    """Parse one vendor PDI .XLS -> list of price events."""
    wb = xlrd.open_workbook(path)
    sh = wb.sheet_by_index(0)
    eff_col, cost_col = _detect_columns(sh)
    terminal = None
    events = []
    for r in range(sh.nrows):
        c0 = str(sh.cell_value(r, 0)).strip()
        if c0.startswith("Terminal:"):
            terminal = c0.replace("Terminal:", "").strip().split(" - ", 1)[0].strip()
            continue
        eff = sh.cell_value(r, eff_col)
        cost = sh.cell_value(r, cost_col)
        if terminal and c0 and isinstance(eff, (int, float)) and eff > 1000 \
                and isinstance(cost, (int, float)):
            events.append({
                "terminal": terminal,
                "grade": c0.split("-")[0].strip(),
                "effective": _excel_dt(eff),
                "cost": float(cost),
            })
    return events


def classify_product(grade, products_map):
    """Map a raw PDI grade string to Regular/Midgrade/Premium/Diesel."""
    for prefix, name in products_map.items():
        if grade.startswith(prefix):
            return name
    return None
