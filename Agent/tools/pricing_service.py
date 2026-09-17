"""Validated service wrapper around the existing pricing rules."""
from datetime import date
from .pricing import first_price_daily_series


def build_daily_prices(events, dates):
    """Return daily prices while validating the requested date sequence."""
    if not dates:
        return {}
    if list(dates) != sorted(dates):
        raise ValueError("dates must be ordered")
    if any(d is None for d in dates):
        raise ValueError("dates cannot contain None")
    result = first_price_daily_series(events, dates)
    return {day: price for day, price in result.items() if isinstance(day, date)}
