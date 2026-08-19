# -*- coding: utf-8 -*-
"""TOOL: html_writer — merge the price matrix into the HTML app's embedded SEED.

Rewrites the single `<script>const SEED=...;</script>` line, preserving the app.
Idempotent: new dates are added, existing date/product rows are replaced.
"""
import json


def write_html(template_html, out_html, colseries, dates, brands, products):
    lines = open(template_html, encoding="utf-8").read().split("\n")
    seed_idx = next(i for i, ln in enumerate(lines)
                    if ln.startswith("<script>const SEED="))
    raw = lines[seed_idx]
    js = raw[len("<script>const SEED="):]
    js = js[:js.rfind(";</script>")]
    seed = json.loads(js)

    # build new rows from the price matrix
    new_rows = {}
    for d in dates:
        ds = d.isoformat()
        for p in products:
            prices = {}
            for col, series in colseries.items():
                v = series.get(p, {}).get(d)
                if v is not None:
                    prices[col] = v
            if prices:
                new_rows[(ds, p)] = {"date": ds, "product": p, "prices": prices}

    merged = {(r["date"], r["product"]): r for r in seed["rows"]}
    merged.update(new_rows)
    seed["rows"] = sorted(
        merged.values(),
        key=lambda r: (r["date"], products.index(r["product"]) if r["product"] in products else 9))

    lines[seed_idx] = "<script>const SEED=" + json.dumps(seed, separators=(",", ":")) + ";</script>"
    open(out_html, "w", encoding="utf-8").write("\n".join(lines))
    return len(new_rows)
