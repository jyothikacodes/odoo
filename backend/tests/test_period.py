from datetime import date
from app.services.period import (
    period_start,
    period_bounds,
    locate_k,
    default_expiry,
    renewed_expiry
)

def test_period_math_golden_vectors():
    # 2026-01-31 monthly/1 k=0 -> 2026-01-31 to 2026-02-28
    s, e = period_bounds(date(2026, 1, 31), "monthly", 1, 0, date(2027, 1, 31))
    assert s == date(2026, 1, 31)
    assert e == date(2026, 2, 28)

    # 2026-01-31 monthly/1 k=1 -> 2026-02-28 to 2026-03-31
    s, e = period_bounds(date(2026, 1, 31), "monthly", 1, 1, date(2027, 1, 31))
    assert s == date(2026, 2, 28)
    assert e == date(2026, 3, 31)

    # 2026-01-31 monthly/1 k=2 -> 2026-03-31 to 2026-04-30
    s, e = period_bounds(date(2026, 1, 31), "monthly", 1, 2, date(2027, 1, 31))
    assert s == date(2026, 3, 31)
    assert e == date(2026, 4, 30)

    # 2026-01-31 monthly/1 k=3 -> 2026-04-30 to 2026-05-31
    s, e = period_bounds(date(2026, 1, 31), "monthly", 1, 3, date(2027, 1, 31))
    assert s == date(2026, 4, 30)
    assert e == date(2026, 5, 31)

    # 2024-02-29 yearly/1 k=1 -> 2025-02-28 to 2026-02-28
    s, e = period_bounds(date(2024, 2, 29), "yearly", 1, 1, date(2030, 2, 28))
    assert s == date(2025, 2, 28)
    assert e == date(2026, 2, 28)

    # 2024-02-29 yearly/1 k=4 -> 2028-02-29 to 2029-02-28
    s, e = period_bounds(date(2024, 2, 29), "yearly", 1, 4, date(2030, 2, 28))
    assert s == date(2028, 2, 29)
    assert e == date(2029, 2, 28)

    # 2026-11-02 weekly/1 k=3 -> 2026-11-23 to 2026-11-30
    s, e = period_bounds(date(2026, 11, 2), "weekly", 1, 3, date(2027, 11, 2))
    assert s == date(2026, 11, 23)
    assert e == date(2026, 11, 30)

    # 2026-11-02 daily/1 k=10 -> 2026-11-12 to 2026-11-13
    s, e = period_bounds(date(2026, 11, 2), "daily", 1, 10, date(2027, 11, 2))
    assert s == date(2026, 11, 12)
    assert e == date(2026, 11, 13)

    # 2026-01-01 monthly/3 k=1 -> 2026-04-01 to 2026-07-01
    s, e = period_bounds(date(2026, 1, 1), "monthly", 3, 1, date(2027, 1, 1))
    assert s == date(2026, 4, 1)
    assert e == date(2026, 7, 1)

    # Expiry bounds
    assert default_expiry(date(2026, 11, 1), 12) == date(2027, 10, 31)
    assert renewed_expiry(date(2027, 10, 31), 12) == date(2028, 10, 31)
    assert default_expiry(date(2026, 1, 31), 1) == date(2026, 2, 27)
