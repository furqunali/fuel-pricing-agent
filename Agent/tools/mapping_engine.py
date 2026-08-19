# -*- coding: utf-8 -*-
"""TOOL: mapping_engine — turn raw PDI files + config into a price matrix.

Output:
  dates      : ordered list of datetime.date covering the PDI range
  colseries  : {app_column: {product: {date: price}}}  (mapped columns only)
  vendor_events : {vendor: [events]}  (kept for the backup/audit trail)
"""
import os
import datetime
from collections import defaultdict

from .pdi_reader import read_pdi_file, classify_product
from .pricing import first_price_daily_series

PRODUCTS = ["Regular", "Midgrade", "Premium", "Diesel"]


def build_price_matrix(pdi_dir, config):
    products_map = config["products"]
    diesel_grade = config["diesel_grade"]

    vendor_events = {}
    index = defaultdict(list)          # (vendor, terminal, product) -> [(dt,cost,grade)]
    all_dates = set()

    for vendor, fname in config["vendor_files"].items():
        path = os.path.join(pdi_dir, fname)
        if not os.path.exists(path):
            continue
        evs = read_pdi_file(path)
        vendor_events[vendor] = evs
        for e in evs:
            product = classify_product(e["grade"], products_map)
            if not product:
                continue
            index[(vendor, e["terminal"], product)].append(
                (e["effective"], e["cost"], e["grade"]))
            all_dates.add(e["effective"].date())

    if not all_dates:
        return [], {}, vendor_events

    start, end = min(all_dates), max(all_dates)
    dates = [start + datetime.timedelta(days=i) for i in range((end - start).days + 1)]

    colseries = {}
    for column, mapping in config["column_map"].items():
        if not mapping:
            continue
        vendor, terminal = mapping
        colseries[column] = {}
        for product in PRODUCTS:
            evs = index.get((vendor, terminal, product), [])
            if product == "Diesel":
                preferred = [e for e in evs if e[2] == diesel_grade]
                if preferred:
                    evs = preferred
            colseries[column][product] = first_price_daily_series(evs, dates)

    return dates, colseries, vendor_events
