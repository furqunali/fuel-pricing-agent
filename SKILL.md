# Fuel pricing — system overview

This folder is the **Demo Petroleum Fuel Pricing System**. The fuel team
drops the daily PDI reports in and clicks one button; the reports rebuild
themselves. Nobody edits data by hand.

```
Fuel pricing/
├── ▶ RUN FUEL UPDATE.bat        ← the team clicks this
├── README - How To Use.html     ← 1-page guide (Eng + Urdu)
├── 1_Drop_PDI_Reports_Here/     ← put the 5 PDI files here
├── 2_Reports_Output/            ← updated Excel + HTML land here
├── Backups/                     ← dated archive (auto)
└── Agent/                       ← the domain-expert agent (the engine)
    ├── SKILL.md                 ← full agent spec + rules  ◀ read this
    ├── run_agent.py             ← one full update
    ├── loop_runner.py           ← loop engine (single / watch modes)
    ├── config/mapping.json      ← terminal→column map (editable)
    ├── template/                ← pristine Excel + HTML templates
    └── tools/                   ← reusable tools (pdi_reader, pricing,
                                    mapping_engine, excel_writer,
                                    html_writer, backup, notify)
```

**The agent is a separate module** (`Agent/`) so it can grow into full
automation (PDI API + daily email) without changing anything else.

See **`Agent/SKILL.md`** for the domain rules, the reusable tools, run modes,
and the phased roadmap.
