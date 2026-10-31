from datetime import datetime, timezone
from decimal import Decimal
from app.services.discount_service import (
    DiscountRule,
    DLine,
    allocate,
    plan_discounts
)
from app.core.money import D

def test_allocate_largest_remainder():
    # allocate(10.00, [33.33, 33.33, 33.34]) -> [3.33, 3.33, 3.34]
    res = allocate(D("10.00"), [D("33.33"), D("33.33"), D("33.34")])
    assert res == [D("3.33"), D("3.33"), D("3.34")]
    assert sum(res) == D("10.00")

    # allocate(0.01, [1, 1]) -> [0.01, 0.00]
    res = allocate(D("0.01"), [D("1"), D("1")])
    assert res == [D("0.01"), D("0.00")]
    assert sum(res) == D("0.01")

    # allocate(362.00, [500.00, 3120.00]) -> [50.00, 312.00]
    res = allocate(D("362.00"), [D("500.00"), D("3120.00")])
    assert res == [D("50.00"), D("312.00")]
    assert sum(res) == D("362.00")

    # zero total
    res = allocate(D("0.00"), [D("100"), D("200")])
    assert res == [D("0.00"), D("0.00")]

def test_discount_planning():
    now = datetime.now(timezone.utc)
    # Golden subscription lines:
    # Line 1: Plan fee base 500.00, qty 1
    # Line 2: ERP Seat base 3120.00, qty 2
    l1 = DLine(key="line_1", product_id=None, quantity=1, base=D("500.00"))
    l2 = DLine(key="line_2", product_id="prod_erp", quantity=2, base=D("3120.00"))

    # Volume 10% on subscription scope, min_qty=3
    r_sub = DiscountRule(
        id="disc_sub_10",
        kind="percentage",
        value=Decimal("10"),
        scope="subscription",
        min_purchase=Decimal("0"),
        min_quantity=3,
        priority=10,
        created_at=now,
        product_ids=frozenset(),
        subscription_ids=frozenset()
    )

    plan = plan_discounts([l1, l2], [r_sub], sub_id="sub_1", stacking=False)
    assert "disc_sub_10" in plan.consumed
    # Total discount 10% of 3620.00 = 362.00 allocated 50.00 and 312.00
    assert plan.per_line["line_1"] == [("disc_sub_10", D("50.00"))]
    assert plan.per_line["line_2"] == [("disc_sub_10", D("312.00"))]
