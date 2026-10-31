from datetime import date, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.schema import (
    Subscription, Invoice, InvoiceLine, Discount, Tax, Customer, BillingRun
)
from app.core.money import q2, ZERO, D
from app.core.clock import today, now
from app.core.numbering import next_number
from app.services.period import period_bounds, locate_k
from app.services.tax_service import TaxRule, compute_line_tax
from app.services.discount_service import DiscountRule, DLine, plan_discounts

def load_eligible_discounts(db: Session, run_date: date) -> List[DiscountRule]:
    discs = db.query(Discount).filter(
        Discount.is_active == True,
        Discount.valid_from <= run_date
    ).all()
    valid = []
    for d in discs:
        if d.valid_to and run_date > d.valid_to:
            continue
        if d.usage_limit is not None and d.usage_count >= d.usage_limit:
            continue
        valid.append(DiscountRule(
            id=d.id,
            kind=d.kind,
            value=D(d.value),
            scope=d.scope,
            min_purchase=D(d.min_purchase),
            min_quantity=d.min_quantity,
            priority=d.priority,
            created_at=d.created_at,
            product_ids=frozenset(d.product_ids or []),
            subscription_ids=frozenset(d.subscription_ids or [])
        ))
    return valid

def build_invoice(
    db: Session,
    sub: Subscription,
    p_start: date,
    p_end: date,
    run_date: date,
    discounts: List[DiscountRule],
    auto_confirm: bool = True
) -> Invoice:
    customer = sub.customer
    plan = sub.plan
    lines = sorted(sub.lines, key=lambda l: l.sort_order)

    # Preload taxes
    all_taxes = {tax.id: TaxRule(
        id=tax.id, name=tax.name, kind=tax.kind, rate=D(tax.rate), price_included=tax.price_included
    ) for tax in db.query(Tax).filter(Tax.is_active == True).all()}

    dlines = [DLine(
        key=str(l.id),
        product_id=l.product_id,
        quantity=l.quantity,
        base=q2(D(l.quantity) * D(l.unit_price))
    ) for l in lines]

    plan_disc = plan_discounts(dlines, discounts, sub_id=sub.id, stacking=False)

    # Reserve discount usage
    for did in plan_disc.consumed:
        d_rec = db.query(Discount).filter(Discount.id == did).first()
        if d_rec:
            d_rec.usage_count += 1

    due_days = sub.payment_term.due_days if sub.payment_term else 0
    inv_number = next_number("INV", run_date.year) if auto_confirm else None

    inv = Invoice(
        number=inv_number,
        subscription_id=sub.id,
        customer_id=customer.id,
        status="confirmed" if auto_confirm else "draft",
        invoice_date=run_date,
        due_date=run_date + timedelta(days=due_days),
        period_start=p_start,
        period_end=p_end,
        currency="INR",
        customer_snapshot={
            "company_name": customer.company_name,
            "contact_name": customer.contact_name,
            "email": customer.email,
            "address": customer.address,
            "tax_id": customer.tax_id
        },
        confirmed_at=now() if auto_confirm else None
    )
    db.add(inv)
    db.flush()

    totals = {"untaxed": ZERO, "discount": ZERO, "tax": ZERO, "total": ZERO}

    for idx, (l, dl) in enumerate(zip(lines, dlines)):
        applied = plan_disc.per_line.get(dl.key, [])
        disc_amt = sum((a for _, a in applied), ZERO)
        primary = applied[0][0] if applied else None
        after = dl.base - disc_amt

        tax_rules = [all_taxes[tid] for tid in (l.tax_ids or []) if tid in all_taxes]
        res = compute_line_tax(after, l.quantity, tax_rules, customer.is_tax_exempt)

        inv_line = InvoiceLine(
            invoice_id=inv.id,
            product_id=l.product_id,
            description=l.description,
            quantity=l.quantity,
            unit_price=l.unit_price,
            base_amount=dl.base,
            discount_id=primary,
            discount_amount=disc_amt,
            net_amount=res.net,
            tax_breakdown=res.breakdown,
            tax_amount=res.tax_total,
            line_total=res.line_total,
            sort_order=idx
        )
        db.add(inv_line)

        totals["untaxed"] += res.net
        totals["discount"] += disc_amt
        totals["tax"] += res.tax_total
        totals["total"] += res.line_total

    inv.untaxed_total = q2(totals["untaxed"])
    inv.discount_total = q2(totals["discount"])
    inv.tax_total = q2(totals["tax"])
    inv.total = q2(totals["total"])

    return inv

def bill_subscription(
    db: Session,
    sub_id: str,
    run_date: date,
    auto_confirm: bool = True
) -> List[Invoice]:
    sub = db.query(Subscription).filter(Subscription.id == sub_id).first()
    if not sub or sub.status != "active" or sub.is_paused:
        return []

    plan = sub.plan
    invoices = []
    discounts = load_eligible_discounts(db, run_date)

    while sub.next_billing_date and sub.next_billing_date <= run_date and sub.next_billing_date <= sub.expiry_date:
        k = locate_k(sub.anchor_date, plan.billing_period, plan.period_interval, sub.next_billing_date)
        p_start, p_end = period_bounds(sub.anchor_date, plan.billing_period, plan.period_interval, k, sub.expiry_date)

        # Check existing invoice for this period
        existing = db.query(Invoice).filter(
            Invoice.subscription_id == sub.id,
            Invoice.period_start == p_start,
            Invoice.period_end == p_end,
            Invoice.status != "cancelled"
        ).first()

        if not existing:
            inv = build_invoice(db, sub, p_start, p_end, run_date, discounts, auto_confirm=auto_confirm)
            invoices.append(inv)

        sub.last_billed_through = p_end
        sub.next_billing_date = p_end

    db.commit()
    return invoices

def run_billing_engine(db: Session, run_date: Optional[date] = None) -> BillingRun:
    d = run_date or today()
    due_subs = db.query(Subscription).filter(
        Subscription.status == "active",
        Subscription.is_paused == False,
        Subscription.next_billing_date <= d,
        Subscription.next_billing_date <= Subscription.expiry_date
    ).all()

    run = BillingRun(run_date=d, status="running", due_count=len(due_subs))
    db.add(run)
    db.commit()

    billed = 0
    failed = 0
    log = []

    for sub in due_subs:
        try:
            invs = bill_subscription(db, sub.id, d)
            billed += len(invs)
            log.append({"subscription": sub.number, "invoices_created": len(invs), "status": "success"})
        except Exception as e:
            failed += 1
            log.append({"subscription": sub.number, "error": str(e), "status": "failed"})

    run.status = "completed" if failed == 0 else ("partial" if billed > 0 else "failed")
    run.billed_count = billed
    run.failed_count = failed
    run.log = log
    db.commit()
    db.refresh(run)
    return run
