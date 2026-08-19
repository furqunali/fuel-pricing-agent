# -*- coding: utf-8 -*-
"""TOOL: pricing — apply the company's price rules to a stream of PDI events.

Business rules (confirmed with the fuel team):
  * A vendor may post 2-4 prices in a day -> use the FIRST (earliest Effective time).
  * Carry the last chosen price forward on days with no new posting.
  * (Weekends automatically inherit Friday's price via carry-forward.)
"""


def first_price_daily_series(events, dates):
    """events: list of (effective_datetime, cost, grade), sorted or not.
    dates:  ordered list of datetime.date to produce a value for.
    Returns {date: price} using earliest-effective-of-day + carry forward.
    """
    chosen = {}
    for dt, cost, _grade in sorted(events):
        d = dt.date()
        if d not in chosen or dt < chosen[d][0]:
            chosen[d] = (dt, cost)
    out = {}
    last = None
    for d in dates:
        if d in chosen:
            last = round(chosen[d][1], 4)
        if last is not None:
            out[d] = last
    return out
