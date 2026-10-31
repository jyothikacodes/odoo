from datetime import date
from decimal import Decimal
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.schema import Subscription, Invoice, Payment, Customer
from app.core.money import q2, ZERO, D
from app.core.clock import today

def get_dashboard_kpis(db: Session) -> Dict[str, Any]:
    curr_today = today()

    # Subscriptions counts
    all_subs = db.query(Subscription).all()
    active_count = sum(1 for s in all_subs if s.status == "active")
    paused_count = sum(1 for s in all_subs if s.status == "active" and s.is_paused)
    confirmed_count = sum(1 for s in all_subs if s.status == "confirmed")
    quotation_count = sum(1 for s in all_subs if s.status == "quotation")

    # MRR calculation (active, unpaused)
    mrr = ZERO
    for s in all_subs:
        if s.status == "active" and not s.is_paused:
            plan = s.plan
            interval = plan.period_interval if plan else 1
            bp = plan.billing_period.lower() if plan else "monthly"
            untaxed = D(s.untaxed_total)
            if bp == "monthly":
                mrr += untaxed / Decimal(interval)
            elif bp == "yearly":
                mrr += (untaxed / Decimal(interval)) / Decimal(12)
            elif bp == "weekly":
                mrr += (untaxed / Decimal(interval)) * (Decimal(52) / Decimal(12))
            elif bp == "daily":
                mrr += (untaxed / Decimal(interval)) * (Decimal(365) / Decimal(12))

    mrr = q2(mrr)
    arr = q2(mrr * Decimal(12))

    # Payments collected (posted only)
    posted_payments = db.query(Payment).filter(Payment.status == "posted").all()
    collected_revenue = q2(sum((D(p.amount) for p in posted_payments), ZERO))

    # Invoices (confirmed or paid)
    invoices = db.query(Invoice).all()
    total_invoiced = q2(sum((D(i.total) for i in invoices if i.status in ("confirmed", "paid")), ZERO))

    # Outstanding & Overdue
    outstanding_amt = ZERO
    outstanding_count = 0
    overdue_amt = ZERO
    overdue_count = 0

    aging = {
        "1_30": ZERO,
        "31_60": ZERO,
        "61_90": ZERO,
        "90_plus": ZERO
    }

    overdue_by_customer: Dict[str, Dict[str, Any]] = {}

    for inv in invoices:
        if inv.status == "confirmed":
            due = D(inv.total) - D(inv.amount_paid)
            if due > ZERO:
                outstanding_amt += due
                outstanding_count += 1
                if inv.due_date < curr_today:
                    overdue_amt += due
                    overdue_count += 1
                    days_overdue = (curr_today - inv.due_date).days
                    if 1 <= days_overdue <= 30:
                        aging["1_30"] += due
                    elif 31 <= days_overdue <= 60:
                        aging["31_60"] += due
                    elif 61 <= days_overdue <= 90:
                        aging["61_90"] += due
                    else:
                        aging["90_plus"] += due

                    # Top overdue customer mapping
                    cid = inv.customer_id
                    cname = inv.customer.company_name if inv.customer else "Unknown"
                    if cid not in overdue_by_customer:
                        overdue_by_customer[cid] = {"id": cid, "name": cname, "amount": ZERO, "count": 0}
                    overdue_by_customer[cid]["amount"] += due
                    overdue_by_customer[cid]["count"] += 1

    top_overdue = sorted(overdue_by_customer.values(), key=lambda x: x["amount"], reverse=True)[:5]
    for c in top_overdue:
        c["amount"] = str(q2(c["amount"]))

    return {
        "active_subscriptions": active_count,
        "paused_subscriptions": paused_count,
        "confirmed_subscriptions": confirmed_count,
        "quotation_subscriptions": quotation_count,
        "mrr": str(mrr),
        "arr": str(arr),
        "collected_revenue": str(collected_revenue),
        "total_invoiced": str(total_invoiced),
        "outstanding_amount": str(q2(outstanding_amt)),
        "outstanding_count": outstanding_count,
        "overdue_amount": str(q2(overdue_amt)),
        "overdue_count": overdue_count,
        "aging_buckets": {k: str(q2(v)) for k, v in aging.items()},
        "top_overdue_customers": top_overdue
    }
