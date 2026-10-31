from datetime import date, datetime, timezone
from typing import Optional

_override_date: Optional[date] = None

def get_virtual_today() -> date:
    global _override_date
    if _override_date is not None:
        return _override_date
    # Month-end at Brightloop Software: 2026-10-31
    return date(2026, 10, 31)

def set_virtual_today(new_date: date) -> None:
    global _override_date
    _override_date = new_date

def reset_virtual_today() -> None:
    global _override_date
    _override_date = None

def today() -> date:
    return get_virtual_today()

def now() -> datetime:
    t = today()
    return datetime(t.year, t.month, t.day, 12, 0, 0, tzinfo=timezone.utc)
