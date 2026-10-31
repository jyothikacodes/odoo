from dataclasses import dataclass
from decimal import Decimal
from typing import List, Dict, Any, Optional
from app.core.money import q2, ZERO, D

@dataclass(frozen=True)
class TaxRule:
    id: Any
    name: str
    kind: str            # 'percentage' | 'fixed'
    rate: Decimal
    price_included: bool

@dataclass
class TaxResult:
    net: Decimal
    tax_total: Decimal
    line_total: Decimal
    breakdown: List[Dict[str, Any]]

def compute_line_tax(
    amount: Decimal,
    quantity: int,
    taxes: List[TaxRule],
    customer_exempt: bool = False
) -> TaxResult:
    """`amount` = line amount AFTER discount."""
    amount = q2(amount)
    if customer_exempt or not taxes:
        return TaxResult(amount, ZERO, amount, [])

    incl = {t.price_included for t in taxes}
    if len(incl) > 1:
        raise ValueError("Cannot mix tax-inclusive and tax-exclusive taxes on one line")

    if incl == {True}:
        if any(t.kind != "percentage" for t in taxes):
            raise ValueError("Inclusive taxes must be percentages")
        total_rate = sum(D(t.rate) for t in taxes)
        net = q2(amount / (Decimal(1) + total_rate / Decimal(100)))
        tax_total = amount - net
        parts, allocated = [], ZERO
        for i, t in enumerate(taxes):
            part = (tax_total - allocated) if i == len(taxes) - 1 else q2(tax_total * D(t.rate) / total_rate)
            allocated += part
            parts.append(_row(t, part))
        return TaxResult(net, tax_total, amount, parts)

    parts, tax_total = [], ZERO
    for t in taxes:
        part = q2(amount * D(t.rate) / Decimal(100)) if t.kind == "percentage" else q2(D(t.rate) * quantity)
        tax_total += part
        parts.append(_row(t, part))
    return TaxResult(amount, tax_total, amount + tax_total, parts)

def _row(t: TaxRule, amt: Decimal) -> Dict[str, Any]:
    return {
        "tax_id": str(t.id),
        "name": t.name,
        "kind": t.kind,
        "rate": str(t.rate),
        "price_included": t.price_included,
        "amount": str(amt)
    }
