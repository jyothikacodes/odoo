from datetime import date, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.schema import (
    Subscription, SubscriptionLine, Customer, Plan, Product, ProductVariant,
    PaymentTerm, Tax, AuditLog
)
from app.core.money import q2, ZERO, D
from app.core.clock import today, now
from app.core.numbering import next_number
from app.core.errors import (
    NotFoundError, ValidationError, InvalidTransitionError, PlanFlagDisallowsError
)
from app.services.period import (
    period_start, period_bounds, default_expiry, renewed_expiry, plan_available
)
from app.services.pricing import unit_price, line_description
from app.services.tax_service import TaxRule, compute_line_tax

def compute_subscription_totals(sub: Subscription, db: Session) -> None:
    u = t = tot = ZERO
    cust = sub.customer
    is_exempt = cust.is_tax_exempt if cust else False

    # Preload taxes
    all_taxes = {tax.id: TaxRule(
        id=tax.id, name=tax.name, kind=tax.kind, rate=D(tax.rate), price_included=tax.price_included
    ) for tax in db.query(Tax).filter(Tax.is_active == True).all()}

    for line in sub.lines:
        line.amount = q2(D(line.quantity) * D(line.unit_price))
        tax_rules = [all_taxes[tid] for tid in (line.tax_ids or []) if tid in all_taxes]
        res = compute_line_tax(line.amount, line.quantity, tax_rules, customer_exempt=is_exempt)
        u += res.net
        t += res.tax_total
        tot += res.line_total

    sub.untaxed_total = q2(u)
    sub.tax_total = q2(t)
    sub.total = q2(tot)

def create_subscription(
    db: Session,
    customer_id: str,
    plan_id: str,
    payment_term_id: Optional[str] = None,
    start_date: Optional[date] = None,
    term_months: int = 12,
    lines_in: Optional[List[Dict[str, Any]]] = None,
    auto_renew: bool = True,
    notes: Optional[str] = None
) -> Subscription:
    cust = db.query(Customer).filter(Customer.id == customer_id).first()
    if not cust:
        raise NotFoundError("Customer")

    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise NotFoundError("Plan")

    sub_start = start_date or today()
    if not plan_available(plan, sub_start):
        raise ValidationError("plan_id", "Plan is not available on start date")

    sub_expiry = default_expiry(sub_start, term_months)
    sub_number = next_number("SUB", sub_start.year)

    if not payment_term_id:
        pt = db.query(PaymentTerm).filter(PaymentTerm.due_days == 0).first()
        payment_term_id = pt.id if pt else None

    sub = Subscription(
        number=sub_number,
        customer_id=cust.id,
        plan_id=plan.id,
        payment_term_id=payment_term_id,
        status="draft",
        start_date=sub_start,
        expiry_date=sub_expiry,
        term_months=term_months,
        anchor_date=sub_start,
        next_billing_date=sub_start,
        auto_renew=auto_renew,
        notes=notes
    )
    db.add(sub)
    db.flush()

    # Plan fee line if plan price > 0
    sort_idx = 0
    if D(plan.price) > ZERO:
        p_line = SubscriptionLine(
            subscription_id=sub.id,
            product_id=None,
            is_plan_fee=True,
            description=f"Plan Fee: {plan.name}",
            quantity=1,
            unit_price=q2(plan.price),
            tax_ids=plan.tax_ids or [],
            amount=q2(plan.price),
            sort_order=sort_idx
        )
        db.add(p_line)
        sort_idx += 1

    # Product lines
    if lines_in:
        for item in lines_in:
            prod_id = item.get("product_id")
            prod = db.query(Product).filter(Product.id == prod_id).first() if prod_id else None
            qty = int(item.get("quantity", 1))
            if qty < plan.min_quantity:
                raise ValidationError("quantity", f"Quantity must be at least {plan.min_quantity}")

            var_ids = item.get("variant_ids", [])
            variants = db.query(ProductVariant).filter(ProductVariant.id.in_(var_ids)).all() if var_ids else []

            u_price = unit_price(prod, variants) if prod else D(item.get("unit_price", "0.00"))
            desc = line_description(prod, variants) if prod else item.get("description", "Item")
            taxes = item.get("tax_ids") if item.get("tax_ids") is not None else (prod.tax_ids if prod else [])

            s_line = SubscriptionLine(
                subscription_id=sub.id,
                product_id=prod.id if prod else None,
                is_plan_fee=False,
                description=desc,
                quantity=qty,
                unit_price=u_price,
                tax_ids=taxes or [],
                amount=q2(qty * u_price),
                sort_order=sort_idx
            )
            db.add(s_line)
            sort_idx += 1

    db.flush()
    compute_subscription_totals(sub, db)
    db.commit()
    db.refresh(sub)
    return sub

def get_allowed_actions(sub: Subscription, role: str) -> List[str]:
    status = sub.status
    plan = sub.plan
    actions = []

    if status == "draft":
        actions.extend(["send_quotation", "discard"])
    elif status == "quotation":
        actions.extend(["revise", "confirm", "reject"])
    elif status == "confirmed":
        actions.extend(["activate", "cancel"])
    elif status == "active":
        if sub.is_paused:
            actions.append("resume")
        else:
            if plan and plan.pausable:
                actions.append("pause")
        if plan and plan.renewable:
            actions.append("renew")
        if plan and (plan.closable or sub.expiry_date < today()):
            actions.append("close")

    if role == "customer":
        # Customers can only confirm/reject quotation, or pause/resume/renew/close if allowed
        actions = [a for a in actions if a in ["confirm", "reject", "pause", "resume", "renew", "close"]]

    return actions

def transition_subscription(
    db: Session,
    sub_id: str,
    action: str,
    role: str = "admin",
    reason: Optional[str] = None
) -> Subscription:
    sub = db.query(Subscription).filter(Subscription.id == sub_id).first()
    if not sub:
        raise NotFoundError("Subscription")

    allowed = get_allowed_actions(sub, role)
    if action not in allowed:
        raise InvalidTransitionError(action, sub.status, allowed)

    curr_today = today()
    plan = sub.plan

    if action == "send_quotation":
        sub.status = "quotation"
        sub.quotation_sent_at = now()
        sub.quotation_valid_until = curr_today + timedelta(days=15)
    elif action == "discard":
        sub.status = "closed"
        sub.close_reason = reason or "discarded"
        sub.closed_at = now()
    elif action == "revise":
        sub.status = "draft"
        sub.quotation_valid_until = None
    elif action == "confirm":
        if sub.quotation_valid_until and sub.quotation_valid_until < curr_today:
            raise ValidationError("quotation_valid_until", "Quotation has expired")
        sub.status = "confirmed"
        sub.confirmed_at = now()
    elif action == "reject":
        sub.status = "closed"
        sub.close_reason = reason or "rejected"
        sub.closed_at = now()
    elif action == "cancel":
        sub.status = "closed"
        sub.close_reason = reason or "cancelled"
        sub.closed_at = now()
    elif action == "activate":
        sub.status = "active"
        sub.activated_at = now()
        sub.anchor_date = sub.start_date
        sub.next_billing_date = sub.start_date
    elif action == "pause":
        if not plan.pausable:
            raise PlanFlagDisallowsError("Plan does not allow pausing")
        sub.is_paused = True
        sub.paused_from = curr_today
    elif action == "resume":
        sub.is_paused = False
        if sub.next_billing_date and sub.next_billing_date <= curr_today:
            sub.anchor_date = curr_today
            sub.next_billing_date = curr_today
        sub.paused_from = None
    elif action == "renew":
        if not plan.renewable:
            raise PlanFlagDisallowsError("Plan does not allow renewal")
        sub.expiry_date = renewed_expiry(sub.expiry_date, sub.term_months)
        sub.renewal_count += 1
    elif action == "close":
        if not plan.closable and sub.expiry_date >= curr_today:
            raise PlanFlagDisallowsError("Plan cannot be closed early")
        sub.status = "closed"
        sub.closed_at = now()
        sub.close_reason = reason or "closed_by_user"
        sub.next_billing_date = None

    db.commit()
    db.refresh(sub)
    return sub
