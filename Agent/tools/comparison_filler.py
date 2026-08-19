# -*- coding: utf-8 -*-
"""TOOL: comparison_filler — auto-fill monthly comparison tabs from DATA_ENTRY.

Safe by design: a price column is only filled when its header EXACTLY matches a
mapped app column (so the AVERAGEIFS is guaranteed correct). 'Difference' columns
copy the sign convention already used in that block's Jan-May rows. Columns whose
header isn't a mapped brand (Global, 'Sale Price', unmapped Unbranded) are left
blank — never guessed.
"""
import re
from openpyxl.utils import get_column_letter as GL

FILL_MONTHS = {"June", "July", "August", "September", "October", "November", "December"}


def _avg_formula(dcol, product, month, year):
    return ('=IFERROR(AVERAGEIFS(DATA_ENTRY!{c}$5:{c}$2924,DATA_ENTRY!$B$5:$B$2924,"{p}",'
            'DATA_ENTRY!$D$5:$D$2924,"{m}",DATA_ENTRY!$AD$5:$AD$2924,{y}),"")'
            ).format(c=dcol, p=product, m=month, y=year)


def _resolve_left(desc):
    """'Motiva Pasa-Rack' / 'Motiva ATX-Formula' / 'Motiva SA-Rack' -> app column + city."""
    d = desc.lower()
    side = "Formula" if "formula" in d else "Rack"
    if "pasa" in d:
        return "Motiva Pasadena - %s" % side, "Houston", side
    if "atx" in d:
        return "Motiva ATX - %s" % side, "ATX", side
    if "sa" in d:
        return "Motiva SA - %s" % side, "SA", side
    return None, None, side


def _resolve_right(desc, city, side):
    d = desc.lower().strip()
    cvx = {"Houston": "CVX Houston - Rack", "ATX": "CVX ATX - Rack", "SA": "CVX SA - Rack"}
    if "global" in d or "sale price" in d:
        return None
    if d == "chevron":
        return cvx.get(city)
    if d == "valero":
        return "Valero - %s" % side
    if "valero unbranded" in d:
        return "Valero Houston Unbranded - Rack"
    if "p66 unbranded" in d:
        return "P66 Unbranded"
    if "motiva pasa formula" in d or ("pasa" in d and "formula" in d):
        return "Motiva Pasadena - Formula"
    if "unbranded" in d:  # Motiva Unbranded (city-specific; only Pasadena is PDI-mapped)
        return "Motiva Unbranded - Pasadena" if city == "Houston" else "Motiva Unbranded - SA"
    return None


def fill_titled(ws, brands, column_map, year):
    """For tabs with abbreviated headers + 'X vs Y (Product)' titles (MOTIVA_CMPRSN)."""
    b2col = {b: GL(5 + i) for i, b in enumerate(brands)}
    filled = 0
    header_rows = [r for r in range(1, ws.max_row + 1)
                   if any(ws.cell(r, c).value == "Month" for c in range(1, ws.max_column + 1))]
    for hr in header_rows:
        for mc in [c for c in range(1, ws.max_column + 1) if ws.cell(hr, c).value == "Month"]:
            # title with ' vs ' sits a few rows above, same column
            title = None
            for tr in range(hr - 1, max(hr - 5, 0), -1):
                v = ws.cell(tr, mc).value
                if isinstance(v, str) and " vs " in v:
                    title = v
                    break
            if not title:
                continue
            m = re.match(r'(.+?)\s+vs\s+(.+?)\s*\(([^)]+)\)', title)
            if not m:
                continue
            left_desc, right_desc, product = m.group(1), m.group(2), m.group(3).strip()
            left, city, side = _resolve_left(left_desc)
            right = _resolve_right(right_desc, city, side)
            if not left or not right or not column_map.get(left) or not column_map.get(right):
                continue  # skip anything that isn't a real PDI-backed pair
            v1c, v2c, dc = mc + 3, mc + 4, mc + 5
            isdiff = isinstance(ws.cell(hr, dc).value, str) and ws.cell(hr, dc).value.strip().lower().startswith("diff")
            for r in range(hr + 1, hr + 13):
                mon = ws.cell(r, mc).value
                if mon not in FILL_MONTHS:
                    continue
                if ws.cell(r, v1c).value in (None, "-"):
                    ws.cell(r, v1c).value = _avg_formula(b2col[left], product, mon, year)
                    ws.cell(r, v2c).value = _avg_formula(b2col[right], product, mon, year)
                    if isdiff:
                        ws.cell(r, dc).value = '=IFERROR(%s%d-%s%d,"")' % (GL(v1c), r, GL(v2c), r)
                    filled += 1
    return filled


def fill_exact_name(ws, brands, column_map, year):
    """For tabs whose headers are exact app-column names (e.g. COMPARISONS)."""
    mapped = {b for b in brands if column_map.get(b)}
    b2col = {b: GL(5 + i) for i, b in enumerate(brands)}
    header_rows = sorted(r for r in range(1, ws.max_row + 1)
                         if any(ws.cell(r, c).value == "Month" for c in range(1, ws.max_column + 1)))
    filled = 0
    for hi, hr in enumerate(header_rows):
        end = (header_rows[hi + 1] - 1) if hi + 1 < len(header_rows) else ws.max_row
        month_cols = [c for c in range(1, ws.max_column + 1) if ws.cell(hr, c).value == "Month"]
        for mc in month_cols:
            pc = mc + 1
            later = [c for c in month_cols if c > mc]
            span_end = (min(later) - 1) if later else ws.max_column
            # classify columns in this sub-block
            cols = []  # (col, brand) ; diffs handled after
            diffs = []  # col index of Difference/Diff headers
            for c in range(mc + 2, span_end + 1):
                h = ws.cell(hr, c).value
                if isinstance(h, str):
                    t = h.strip()
                    if t in mapped:
                        cols.append((c, t))
                    elif t.lower().startswith("diff"):
                        diffs.append(c)
            colset = {c for c, _ in cols}
            # fill brand columns for June+ rows
            for r in range(hr + 1, end + 1):
                mon, prod = ws.cell(r, mc).value, ws.cell(r, pc).value
                if mon not in FILL_MONTHS:
                    continue
                for c, brand in cols:
                    if ws.cell(r, c).value in (None, "-"):
                        ws.cell(r, c).value = _avg_formula(b2col[brand], prod, mon, year)
                        filled += 1
            # fill Difference columns: infer sign from an existing (Jan-May) row
            for dc in diffs:
                left = [c for c in range(dc - 1, mc + 1, -1) if c in colset][:2]
                if len(left) < 2:
                    continue
                a, b = left[0], left[1]  # a = nearest brand left, b = next
                sample = None
                for r in range(hr + 1, end + 1):
                    dv = ws.cell(r, dc).value
                    av, bv = ws.cell(r, a).value, ws.cell(r, b).value
                    if isinstance(dv, (int, float)) and isinstance(av, (int, float)) and isinstance(bv, (int, float)):
                        sample = (dv, av, bv)
                        break
                if not sample:
                    continue
                dv, av, bv = sample
                # decide a-b vs b-a
                if abs((av - bv) - dv) <= abs((bv - av) - dv):
                    fexpr = "{A}{{r}}-{B}{{r}}".format(A=GL(a), B=GL(b))
                else:
                    fexpr = "{B}{{r}}-{A}{{r}}".format(A=GL(a), B=GL(b))
                for r in range(hr + 1, end + 1):
                    mon = ws.cell(r, mc).value
                    if mon in FILL_MONTHS and ws.cell(r, dc).value in (None, "-"):
                        ws.cell(r, dc).value = '=IFERROR(%s,"")' % fexpr.format(r=r)
                        filled += 1
    return filled
