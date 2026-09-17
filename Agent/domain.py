"""Typed domain objects for fuel pricing workflows."""
from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class PriceEvent:
    effective_at: datetime
    cost: float
    grade: str

    def __post_init__(self):
        if self.cost < 0:
            raise ValueError("cost cannot be negative")
        if not self.grade.strip():
            raise ValueError("grade is required")


@dataclass(frozen=True)
class DailyPrice:
    day: date
    price: float
    grade: str
