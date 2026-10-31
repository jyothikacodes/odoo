from datetime import date
from typing import Optional, Any
from sqlalchemy.orm import Session
from app.models.schema import Invoice, Payment
from app.core.money import q2, ZERO, D
from app.core.clock import today, now
from app.core.numbering import next_number
from app.core.errors import (
    NotFoundError, ValidationError, PaymentExceedsDueError, InvoiceNotPayableError
)

def record_payment(
    db: Session,
    invoice_id: str,
    method: str,
    amount: Any,
    paid_on: Optional[date] = None,
    reference: Optional[str] = None,
    note: Optional[str] = None
) -> Payment:
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not inv:
        raise NotFoundError("Invoice")

    if inv.status != "confirmed":
        raise InvoiceNotPayableError(inv.status)

    p_amount = q2(D(amount))
    if p_amount <= ZERO:
        raise ValidationError("amount", "Payment amount must be greater than zero")

    amount_due = q2(inv.total - inv.amount_paid)
    if p_amount > amount_due:
        raise PaymentExceedsDueError(amount_due)

    p_date = paid_on or today()
    if p_date > today():
        raise ValidationError("paid_on", "Payment date cannot be in the future")

    pay_num = next_number("PAY", p_date.year)
    pay = Payment(
        number=pay_num,
        invoice_id=inv.id,
        method=method,
        amount=p_amount,
        paid_on=p_date,
        reference=reference,
        note=note,
        status="posted"
    )
    db.add(pay)

    inv.amount_paid = q2(inv.amount_paid + p_amount)
    if inv.amount_paid >= inv.total:
        inv.status = "paid"
        inv.paid_at = p_date

    db.commit()
    db.refresh(pay)
    return pay

def reverse_payment(db: Session, payment_id: str, reason: Optional[str] = None) -> Payment:
    pay = db.query(Payment).filter(Payment.id == payment_id).first()
    if not pay:
        raise NotFoundError("Payment")

    if pay.status != "posted":
        raise ValidationError("status", "Only posted payments can be reversed")

    inv = pay.invoice
    pay.status = "reversed"
    pay.reversed_at = now()
    pay.reverse_reason = reason or "Reversed by admin"

    inv.amount_paid = q2(inv.amount_paid - pay.amount)
    if inv.status == "paid" and inv.amount_paid < inv.total:
        inv.status = "confirmed"
        inv.paid_at = None

    db.commit()
    db.refresh(pay)
    return pay
