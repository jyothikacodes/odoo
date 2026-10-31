from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Iterable

CENT = Decimal("0.01")
ZERO = Decimal("0.00")

def D(v: Any) -> Decimal:
    if v is None:
        return ZERO
    if isinstance(v, Decimal):
        return v
    return Decimal(str(v))

def q2(v: Any) -> Decimal:
    return D(v).quantize(CENT, rounding=ROUND_HALF_UP)

def sum_money(values: Iterable[Any]) -> Decimal:
    return q2(sum((D(v) for v in values), ZERO))
