# -*- coding: utf-8 -*-
"""Loop engine for the Fuel Pricing agent.

Two modes:
  * single  (default) : run the agent once and exit  -> used by the RUN button.
  * watch             : keep running; every INTERVAL seconds check the drop
                        folder and re-run the agent whenever the PDI files
                        change (new day's reports dropped in). This is the
                        "always-on" mode for full automation.

Usage:
  python loop_runner.py            # run once
  python loop_runner.py watch      # watch every 5 min
  python loop_runner.py watch 900  # watch every 15 min
"""
import os
import sys
import time
import hashlib
import datetime

AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(AGENT_DIR)
PDI_DIR = os.path.join(ROOT, "1_Drop_PDI_Reports_Here")

sys.path.insert(0, AGENT_DIR)
import run_agent


def _signature():
    """Fingerprint of the drop folder (names + sizes + mtimes)."""
    parts = []
    for f in sorted(os.listdir(PDI_DIR)):
        if f.lower().endswith((".xls", ".xlsx", ".csv")):
            st = os.stat(os.path.join(PDI_DIR, f))
            parts.append("%s:%d:%d" % (f, st.st_size, int(st.st_mtime)))
    return hashlib.md5("|".join(parts).encode()).hexdigest()


def watch(interval=300):
    print("Watch mode: checking every %d s. Drop new PDI files anytime. Ctrl+C to stop." % interval)
    last = None
    while True:
        sig = _signature()
        if sig and sig != last:
            print("\n[%s] change detected -> running agent..."
                  % datetime.datetime.now().strftime("%H:%M:%S"))
            try:
                run_agent.run()
                last = sig
            except Exception as e:
                print("Run failed: %s (will retry next cycle)" % e)
        time.sleep(interval)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "single"
    if mode == "watch":
        every = int(sys.argv[2]) if len(sys.argv) > 2 else 300
        watch(every)
    else:
        run_agent.run()
