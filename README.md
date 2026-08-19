# Fuel Pricing Agent

A small, dependency-light automation that turns raw daily **PDI "FI Fuel Costs"
vendor exports** into finished pricing reports — with **no manual data entry**.

Drop the day's vendor spreadsheets into an input folder, run one command, and the
agent maps each vendor terminal to your report columns, applies the pricing rules,
and rewrites:

- an **Excel tracker** (`Fuel_Price_Tracker.xlsx`) — data-entry sheet plus
  auto-updating monthly-average and comparison tabs, **with all charts/formatting
  preserved**, and
- an **HTML price app** (`Demo_Fuel_Price_App.html`) — a self-contained page
  with the latest prices embedded.

Every run also archives the raw inputs to a dated `Backups/` folder, so history is
never lost.

> **Sanitized demo — no real data.** This is a public, sanitized copy. It ships
> **no vendor price data, no store/terminal mappings, and no spreadsheets**. The
> real mapping is replaced by a small fictional sample
> (`Agent/config/mapping.example.json`). To use it for real, supply your own PDI
> exports and your own `mapping.json` (both are git-ignored so they can never be
> committed).

## How it works

```
1_Drop_PDI_Reports_Here/  ->  [ AGENT ]  ->  2_Reports_Output/  +  Backups/
   (vendor .XLS exports)                       Excel + HTML         dated archive
```

### Pricing rules (the domain logic)
1. **First price of the day.** A vendor may post several prices per day; the agent
   keeps the one with the **earliest effective time**.
2. **Carry forward.** Days with no new posting inherit the last chosen price
   (so weekends inherit Friday's price).
3. **Product mapping.** Raw grades (`Unl 87`, `Mid 89`, `Pre 93`, `ULSD…`) map to
   Regular / Midgrade / Premium / Diesel.
4. **Terminal → column mapping** lives in config (`mapping.json`), editable with no
   code changes. Columns with no source are left blank — never guessed.

## Tech stack
- **Python 3** (standard library)
- **openpyxl** — read/write the Excel workbook while preserving charts
- **xlrd** — parse the legacy `.XLS` vendor exports

See `Agent/requirements.txt`.

## The `Agent/tools/` modules

| Module | Responsibility |
|--------|----------------|
| `pdi_reader.py`       | Parse one vendor PDI `.XLS` export into price events (auto-detects the Effective/Cost columns). |
| `pricing.py`          | Apply the first-price-of-day + carry-forward rules to produce a daily price series. |
| `mapping_engine.py`   | Combine all vendors with the config mapping into a price matrix keyed by column/product/date. |
| `excel_writer.py`     | Fill the Excel data-entry sheet and insert auto-updating `AVERAGEIFS` formulas by editing sheet XML directly, so charts and formatting survive. |
| `comparison_filler.py`| Safely auto-fill the monthly comparison tabs; only fills columns whose header exactly matches a mapped column. |
| `html_writer.py`      | Merge the price matrix into the HTML app's embedded data (idempotent). |
| `backup.py`           | Write an immutable `Backups/YYYY-MM-DD/` archive of the raw inputs plus a `snapshot.json`. |
| `notify.py`           | Write a plain notification file now; optional SMTP email in Phase 2 (credentials read from env vars). |

## Setup

```bash
pip install -r Agent/requirements.txt

# create your real config from the sample
cp Agent/config/mapping.example.json Agent/config/mapping.json
# edit mapping.json: your supplier keys, filenames, and terminal->column map

# (optional) enable Phase 2 email notifications
cp .env.example .env
# edit .env with your SMTP settings
```

## Run

1. Put your vendor PDI exports in `1_Drop_PDI_Reports_Here/`.
2. Run one full update:
   ```bash
   python Agent/run_agent.py
   ```
3. Or run "always-on" watch mode (re-runs whenever new files are dropped):
   ```bash
   python Agent/loop_runner.py watch 300   # check every 300s
   ```
4. Find the rebuilt reports in `2_Reports_Output/` and the raw archive in
   `Backups/YYYY-MM-DD/`.

The run is **idempotent** — safe to re-run at any time.

## Roadmap (tool structure stays the same)
- **Phase 1 (now):** drop files → run → reports rebuilt + backup.
- **Phase 2:** daily email notification via `notify.send_email` (env-configured SMTP).
- **Phase 3:** pull PDI reports automatically via API and run on a schedule.

## License
MIT — see [LICENSE](LICENSE).
