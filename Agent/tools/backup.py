# -*- coding: utf-8 -*-
"""TOOL: backup — immutable dated archive of each run.

Copies the raw PDI inputs + a snapshot.json into Backups/YYYY-MM-DD/ so past
data is never lost and any future upgrade can rebuild everything from history.
"""
import os
import json
import shutil


def archive(pdi_dir, backups_dir, run_date, meta):
    dest = os.path.join(backups_dir, run_date)
    os.makedirs(dest, exist_ok=True)
    copied = []
    for fname in os.listdir(pdi_dir):
        if fname.lower().endswith((".xls", ".xlsx", ".csv")):
            shutil.copy2(os.path.join(pdi_dir, fname), os.path.join(dest, fname))
            copied.append(fname)
    with open(os.path.join(dest, "snapshot.json"), "w") as f:
        json.dump({"run_date": run_date, "raw_files": copied, **meta}, f, indent=2)
    return dest, copied
