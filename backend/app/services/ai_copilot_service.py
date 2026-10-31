from datetime import date
from decimal import Decimal
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.schema import Customer, Subscription, Invoice
from app.core.money import q2, ZERO, D
from app.core.clock import today

def analyze_customer_health(db: Session, customer_id: str) -> Dict[str, Any]:
    cust = db.query(Customer).filter(Customer.id == customer_id).first()
    if not cust:
        return {}

    curr_today = today()
    invoices = cust.invoices
    subs = cust.subscriptions

    total_invoiced = sum((D(i.total) for i in invoices if i.status in ("confirmed", "paid")), ZERO)
    total_paid = sum((D(i.amount_paid) for i in invoices), ZERO)

    overdue_invoices = [i for i in invoices if i.status == "confirmed" and i.due_date < curr_today]
    max_days_overdue = max([(curr_today - i.due_date).days for i in overdue_invoices], default=0)

    # Base score: 100
    score = 100

    # Overdue penalties
    if max_days_overdue > 60:
        score -= 50
    elif max_days_overdue > 30:
        score -= 30
    elif max_days_overdue > 0:
        score -= 15

    # Pause penalty
    paused_subs = [s for s in subs if s.is_paused]
    if paused_subs:
        score -= 15

    # Closed early penalty
    closed_subs = [s for s in subs if s.status == "closed"]
    if closed_subs:
        score -= 10

    # Retention bonus for renewals
    renewals = sum(s.renewal_count for s in subs)
    score += min(renewals * 10, 20)

    score = max(5, min(100, score))

    if score >= 80:
        risk_level = "Low"
        risk_color = "green"
        recommendation = "Healthy account. Prime candidate for plan upgrade or cross-selling."
    elif score >= 50:
        risk_level = "Medium"
        risk_color = "amber"
        recommendation = "Moderate risk. Monitor payment schedule and check in before renewal."
    else:
        risk_level = "High"
        risk_color = "red"
        recommendation = "Critical churn risk. Overdue payments detected. Immediate account manager intervention recommended."

    return {
        "customer_id": cust.id,
        "company_name": cust.company_name,
        "health_score": score,
        "churn_risk": risk_level,
        "risk_color": risk_color,
        "max_days_overdue": max_days_overdue,
        "active_subscriptions": sum(1 for s in subs if s.status == "active"),
        "total_invoiced": str(q2(total_invoiced)),
        "total_paid": str(q2(total_paid)),
        "recommendation": recommendation
    }

def generate_smart_dunning_email(db: Session, invoice_id: str) -> Dict[str, Any]:
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not inv:
        return {}

    curr_today = today()
    due = q2(D(inv.total) - D(inv.amount_paid))
    days_overdue = (curr_today - inv.due_date).days if inv.due_date < curr_today else 0
    cust = inv.customer

    if days_overdue <= 10:
        tone = "Gentle Friendly Reminder"
        subject = f"Friendly Reminder: Brightloop Invoice {inv.number} is Due"
        body = (
            f"Dear {cust.contact_name},\n\n"
            f"We hope this note finds you well. This is a gentle reminder that invoice {inv.number} "
            f"for ₹{due} was due on {inv.due_date}.\n\n"
            f"You can view and settle your invoice directly via your customer portal.\n\n"
            f"Best regards,\nBrightloop Software Billing Team"
        )
    elif days_overdue <= 30:
        tone = "Firm Urgent Notice"
        subject = f"Overdue Notice: Immediate Action Required on Invoice {inv.number}"
        body = (
            f"Dear {cust.contact_name},\n\n"
            f"Our records indicate that invoice {inv.number} for ₹{due} is now {days_overdue} days past due.\n\n"
            f"To prevent any disruption to your active subscription services, please arrange payment "
            f"at your earliest convenience.\n\n"
            f"Best regards,\nBrightloop Software Accounts Department"
        )
    else:
        tone = "Final Notice / Suspension Warning"
        subject = f"FINAL NOTICE: Account Suspension Alert for {cust.company_name}"
        body = (
            f"Dear {cust.contact_name},\n\n"
            f"Invoice {inv.number} (Balance: ₹{due}) is severely overdue by {days_overdue} days.\n"
            f"Please be advised that your services may be paused if outstanding dues are not cleared within 48 hours.\n\n"
            f"Contact billing@brightloop.example or call our emergency desk immediately.\n\n"
            f"Sincerely,\nBrightloop Software Credit Control"
        )

    return {
        "invoice_number": inv.number,
        "customer_email": cust.email,
        "amount_due": str(due),
        "days_overdue": days_overdue,
        "tone": tone,
        "subject": subject,
        "email_body": body
    }
