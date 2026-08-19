---
name: fuel-pricing-agent
description: >
  Domain-expert agent for Demo Petroleum daily fuel pricing. Reads the PDI
  "FI Fuel Costs" vendor exports, picks the first (earliest-effective) price per
  day per vendor terminal, maps terminals to the 25 report columns, and rewrites
  the Excel workbook + HTML dashboard with a dated backup. Use it whenever new
  PDI reports arrive (daily). Built to grow into full automation (PDI API +
  daily email) without changing the tool structure.
version: 1.0
owner: Furqan Ali (SLP)
---

# Fuel Pricing — Domain Expert Agent

## What it does
Turns raw daily PDI vendor pricing files into the team's finished reports,
automatically, with no manual data entry.

```
1_Drop_PDI_Reports_Here/  ->  [AGENT]  ->  2_Reports_Output/  +  Backups/
   (5 vendor .XLS files)                    Excel + HTML         dated archive
```

## When to use
- Every day, after the fuel team saves the PDI exports into the drop folder.
- Any time the reports need to be rebuilt from the current PDI files
  (the run is idempotent — safe to re-run).

## Domain rules (the "expertise")
1. **First price of the day.** A vendor may post 2–4 prices in a day; use the
   one with the **earliest Effective time**. Carry it forward on days with no
   new posting (weekends therefore inherit Friday's price).
2. **Product mapping.** `Unl 87`→Regular, `Mid 89`→Midgrade, `Pre 93`→Premium,
   `ULSD…`→Diesel (standard diesel grade = `ULSD#2 LED DC`).
3. **Conventional vs RFG** resolves automatically — each terminal carries only
   one (Houston = RFG; Austin / San Antonio / Dallas = Conventional).
4. **Terminal → column mapping** lives in `config/mapping.json` (editable, no
   code changes). Columns with no PDI source are left blank.

## Reusable tools (`tools/`)
| Tool | Responsibility |
|------|----------------|
| `pdi_reader.py`     | Parse a PDI `.XLS` export → price events (auto-detects columns) |
| `pricing.py`        | First-price-of-day + carry-forward series |
| `mapping_engine.py` | Combine all vendors + `mapping.json` → price matrix |
| `excel_writer.py`   | Fill DATA_ENTRY, force recalc, auto-formula SUMMARY & VALERO (keeps charts) |
| `html_writer.py`    | Merge prices into the HTML app's embedded data |
| `backup.py`         | Immutable `Backups/YYYY-MM-DD/` archive |
| `notify.py`         | Plain notification file now; Gmail email in Phase 2 |

## How to run
- **Button:** double-click `RUN FUEL UPDATE` (root of the Fuel pricing folder).
- **Once:** `python Agent/run_agent.py`
- **Always-on (loop):** `python Agent/loop_runner.py watch 300`
  (re-runs automatically whenever new PDI files are dropped).

## Inputs / outputs
- **Input:**  `1_Drop_PDI_Reports_Here/` — the 5 vendor PDI files.
- **Output:** `2_Reports_Output/Fuel_Price_Tracker.xlsx`,
  `2_Reports_Output/Demo_Fuel_Price_App.html`, a notification file.
- **Archive:** `Backups/YYYY-MM-DD/` (raw files + `snapshot.json`).

## Config
`Agent/config/mapping.json` — vendor files, product rules, diesel grade, and the
terminal→column map. Update the map after the mapping worksheet is confirmed.

## Roadmap (unchanged tool structure)
- **Phase 1 (now):** drop files → click button → reports rebuilt + backup.
- **Phase 2:** plain **daily email** notification (Gmail/Workspace) via `notify.send_email`.
- **Phase 3:** **PDI API** pulls the reports automatically (replace the drop folder)
  and the loop runs on a schedule — no clicks.

## Known gaps (waiting on data/decisions)
- 8 columns unmapped until the mapping worksheet is returned (Motiva Unbranded-SA,
  Valero Dilley, CITGO city, Marathon, Global×3, Roadys, Sunoco).
- `MOTIVA_CMPRSN` and `COMPARISONS` tabs need Global rack + **retail Sale Price**
  data, which is **not** in the PDI cost reports.
