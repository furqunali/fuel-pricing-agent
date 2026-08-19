# -*- coding: utf-8 -*-
"""Fuel Pricing - Domain Expert Agent (entry point).

Reads the PDI reports dropped in `1_Drop_PDI_Reports_Here`, applies the pricing
rules + terminal->column mapping, and rewrites the Excel + HTML reports in
`2_Reports_Output`, archiving a dated backup. One call = one full update.

Run directly ( python run_agent.py ) or via the RUN FUEL UPDATE button.
"""
import os
import sys
import json
import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tools.mapping_engine import build_price_matrix, PRODUCTS
from tools import excel_writer, html_writer, backup, notify

# When packaged as a .exe (PyInstaller), locate the folder from the exe's own
# location so config/ and template/ stay external and editable next to it.
if getattr(sys, "frozen", False):
    AGENT_DIR = os.path.dirname(sys.executable)
else:
    AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(AGENT_DIR)
PDI_DIR = os.path.join(ROOT, "1_Drop_PDI_Reports_Here")
OUT_DIR = os.path.join(ROOT, "2_Reports_Output")
BACKUP_DIR = os.path.join(ROOT, "Backups")
TPL_DIR = os.path.join(AGENT_DIR, "template")
CFG = os.path.join(AGENT_DIR, "config", "mapping.json")
LOG = os.path.join(AGENT_DIR, "logs", "agent.log")


def log(msg):
    line = "[%s] %s" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), msg)
    print(line)
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run():
    config = json.load(open(CFG, encoding="utf-8"))
    brands = list(config["column_map"].keys())
    run_date = datetime.date.today().isoformat()

    pdi_files = [f for f in os.listdir(PDI_DIR) if f.lower().endswith((".xls", ".xlsx", ".csv"))]
    if not pdi_files:
        log("No PDI files found in 1_Drop_PDI_Reports_Here. Nothing to do.")
        return False

    log("Reading %d PDI file(s): %s" % (len(pdi_files), ", ".join(sorted(pdi_files))))
    dates, colseries, vendor_events = build_price_matrix(PDI_DIR, config)
    if not dates:
        log("No price rows detected in the PDI files. Check the files are the FI Fuel Costs export.")
        return False

    mapped = [c for c, m in config["column_map"].items() if m]
    log("Price range: %s -> %s  (%d days). Mapped columns: %d/%d."
        % (dates[0], dates[-1], len(dates), len(mapped), len(brands)))

    # backup raw inputs first (never lose source data)
    meta = {"date_range": [dates[0].isoformat(), dates[-1].isoformat()],
            "mapped_columns": mapped,
            "vendors": {v: len(e) for v, e in vendor_events.items()}}
    bdir, copied = backup.archive(PDI_DIR, BACKUP_DIR, run_date, meta)
    log("Backup archived: Backups/%s (%d raw files)." % (run_date, len(copied)))

    # Excel
    out_xlsx = os.path.join(OUT_DIR, "Fuel_Price_Tracker.xlsx")
    tpl_xlsx = os.path.join(TPL_DIR, "Fuel_Price_Tracker_template.xlsx")
    n_cells = excel_writer.write_excel(tpl_xlsx, out_xlsx, colseries, dates, brands, config)
    log("Excel updated: %d price cells filled -> 2_Reports_Output/Fuel_Price_Tracker.xlsx" % n_cells)

    # HTML
    out_html = os.path.join(OUT_DIR, "Demo_Fuel_Price_App.html")
    tpl_html = os.path.join(TPL_DIR, "Demo_Fuel_Price_App_template.html")
    n_rows = html_writer.write_html(tpl_html, out_html, colseries, dates, brands, PRODUCTS)
    log("HTML updated: %d date-rows -> 2_Reports_Output/Demo_Fuel_Price_App.html" % n_rows)

    # notification (plain file; email is Phase 2)
    summary = ["Price range: %s to %s" % (dates[0], dates[-1]),
               "Mapped columns: %d of %d" % (len(mapped), len(brands)),
               "Excel cells filled: %d" % n_cells]
    notify.write_notice(OUT_DIR, run_date, summary)
    log("Done. Reports + notification written to 2_Reports_Output.")
    return True


if __name__ == "__main__":
    try:
        ok = run()
        sys.exit(0 if ok else 1)
    except Exception as e:
        log("ERROR: %s" % e)
        import traceback
        traceback.print_exc()
        sys.exit(2)
