from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Set, Tuple, Optional, Any, FrozenSet
from app.core.money import q2, ZERO, D

@dataclass(frozen=True)
class DiscountRule:
    id: Any
    kind: str                         # 'fixed' | 'percentage'
    value: Decimal
    scope: str                        # 'product' | 'subscription'
    min_purchase: Decimal
    min_quantity: int
    priority: int
    created_at: datetime
    product_ids: FrozenSet[Any]       # empty => not restricted by product
    subscription_ids: FrozenSet[Any]  # empty => all subscriptions

@dataclass
class DLine:
    key: str
    product_id: Optional[Any]
    quantity: int
    base: Decimal                     # base = qty * unit_price

@dataclass
class DiscountPlan:
    per_line: Dict[str, List[Tuple[Any, Decimal]]]  # line key -> [(discount_id, amount)]
    consumed: Set[Any]                              # set of discount_ids used

def _amount(rule: DiscountRule, base: Decimal) -> Decimal:
    raw = q2(base * D(rule.value) / Decimal(100)) if rule.kind == "percentage" else q2(D(rule.value))
    return min(raw, base)

def _rank(rule: DiscountRule, amount: Decimal):
    # higher amount wins; then lower priority number; then older created_at; then id
    return (-amount, rule.priority, rule.created_at, str(rule.id))

def allocate(total: Decimal, weights: List[Decimal]) -> List[Decimal]:
    """Largest-remainder split of `total` proportional to weights; result sums EXACTLY to total."""
    total = q2(total)
    wsum = sum(weights)
    if total <= ZERO or wsum <= ZERO:
        return [ZERO] * len(weights)
    cents = int(total * 100)
    exact = [Decimal(cents) * (w / wsum) for w in weights]
    floors = [int(x) for x in exact]
    rest = cents - sum(floors)
    order = sorted(range(len(weights)), key=lambda i: (exact[i] - Decimal(floors[i])), reverse=True)
    for i in order[:rest]:
        floors[i] += 1
    return [Decimal(c) / Decimal(100) for c in floors]

def plan_discounts(
    lines: List[DLine],
    rules: List[DiscountRule],
    sub_id: Any,
    stacking: bool = False
) -> DiscountPlan:
    prod_rules = [r for r in rules if r.scope == "product"]
    sub_rules  = [r for r in rules if r.scope == "subscription" and (not r.subscription_ids or sub_id in r.subscription_ids)]

    # Option A: best product-scope discount per line
    A: Dict[str, Tuple[DiscountRule, Decimal]] = {}
    for ln in lines:
        cands = []
        for r in prod_rules:
            matches_prod = not r.product_ids or ln.product_id in r.product_ids
            if matches_prod and ln.base >= r.min_purchase and ln.quantity >= r.min_quantity:
                cands.append((r, _amount(r, ln.base)))
        cands = [c for c in cands if c[1] > ZERO]
        if cands:
            A[ln.key] = min(cands, key=lambda c: _rank(*c))
    total_A = sum((a for _, a in A.values()), ZERO)

    # Option B: best subscription-scope discount
    sum_base = sum((l.base for l in lines), ZERO)
    sum_qty = sum(l.quantity for l in lines)

    def best_sub(remaining_base: Decimal):
        c = [(r, _amount(r, remaining_base)) for r in sub_rules if sum_base >= r.min_purchase and sum_qty >= r.min_quantity]
        c = [x for x in c if x[1] > ZERO]
        return min(c, key=lambda x: _rank(*x)) if c else None

    plan = DiscountPlan(per_line={}, consumed=set())

    if stacking:
        for k, (r, a) in A.items():
            plan.per_line.setdefault(k, []).append((r.id, a))
            plan.consumed.add(r.id)
        remaining = [l.base - (A[l.key][1] if l.key in A else ZERO) for l in lines]
        rem_sum = sum(remaining, ZERO)
        b = best_sub(rem_sum)
        if b:
            shares = allocate(b[1], remaining)
            for l, s in zip(lines, shares):
                if s > ZERO:
                    plan.per_line.setdefault(l.key, []).append((b[0].id, s))
            plan.consumed.add(b[0].id)
        return plan

    b = best_sub(sum_base)
    total_B = b[1] if b else ZERO

    if total_A >= total_B and A:  # tie -> product-scope option wins
        for k, (r, a) in A.items():
            plan.per_line[k] = [(r.id, a)]
            plan.consumed.add(r.id)
    elif b:
        for l, s in zip(lines, allocate(b[1], [l.base for l in lines])):
            if s > ZERO:
                plan.per_line[l.key] = [(b[0].id, s)]
        plan.consumed.add(b[0].id)

    return plan
