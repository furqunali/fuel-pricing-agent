from datetime import date, datetime

import pytest

from Agent.tools.pricing_service import build_daily_prices


def test_build_daily_prices_uses_existing_business_rule():
    events = [
        (datetime(2026, 1, 2, 12), 3.25, "regular"),
        (datetime(2026, 1, 2, 8), 3.10, "regular"),
    ]
    dates = [date(2026, 1, 2), date(2026, 1, 3)]
    assert build_daily_prices(events, dates) == {
        date(2026, 1, 2): 3.10,
        date(2026, 1, 3): 3.10,
    }


def test_build_daily_prices_rejects_unordered_dates():
    dates = [date(2026, 1, 3), date(2026, 1, 2)]
    with pytest.raises(ValueError, match="ordered"):
        build_daily_prices([], dates)
