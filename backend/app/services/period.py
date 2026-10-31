from datetime import date, timedelta
from typing import Tuple, Any
from dateutil.relativedelta import relativedelta

def _delta(period: str, interval: int, k: int) -> relativedelta:
    n = interval * k
    mapping = {
        "daily": relativedelta(days=n),
        "weekly": relativedelta(weeks=n),
        "monthly": relativedelta(months=n),
        "yearly": relativedelta(years=n),
    }
    return mapping[period.lower()]

def period_start(anchor: date, period: str, interval: int, k: int) -> date:
    """Start of period k, ALWAYS computed from the anchor (never chained) so month-end clamping doesn't drift."""
    return anchor + _delta(period, interval, k)

def period_bounds(anchor: date, period: str, interval: int, k: int, expiry: date) -> Tuple[date, date]:
    """[start, end) — end is exclusive and capped at expiry_date + 1 day."""
    start = period_start(anchor, period, interval, k)
    end = min(period_start(anchor, period, interval, k + 1), expiry + timedelta(days=1))
    return start, end

_APPROX_DAYS = {"daily": 1.0, "weekly": 7.0, "monthly": 30.4375, "yearly": 365.25}

def locate_k(anchor: date, period: str, interval: int, d: date) -> int:
    """Smallest k >= 0 with period_start(k) >= d."""
    if d <= anchor:
        return 0
    p = period.lower()
    k = max(int((d - anchor).days / (_APPROX_DAYS[p] * interval)) - 2, 0)
    while period_start(anchor, p, interval, k) < d:
        k += 1
    while k > 0 and period_start(anchor, p, interval, k - 1) >= d:
        k -= 1
    return k

def default_expiry(start: date, term_months: int) -> date:
    return start + relativedelta(months=term_months) - timedelta(days=1)

def renewed_expiry(expiry: date, term_months: int) -> date:
    return (expiry + timedelta(days=1)) + relativedelta(months=term_months) - timedelta(days=1)

def plan_available(plan: Any, on: date) -> bool:
    if not getattr(plan, "is_active", True):
        return False
    from_date = getattr(plan, "available_from", None)
    to_date = getattr(plan, "available_to", None)
    if from_date and from_date > on:
        return False
    if to_date and on > to_date:
        return False
    return True
