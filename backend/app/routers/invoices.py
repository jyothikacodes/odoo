from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.db import get_db
from app.core.clock import today, now
from app.core.money import q2, D, ZERO
from app.core.numbering import next_number
from app.models.schema import Invoice, Payment

router = APIRouter(prefix="/api/v1/invoices", tags=["Invoices"])

def serialize_invoice(inv: Invoice) -> dict:
    curr_today = today()
    due = q2(D(inv.total) - D(inv.amount_paid))
    is_overdue = inv.status == "confirmed" and inv.due_date < curr_today and due > ZERO

    lines = []
    for l in inv.lines:
        lines.append({
            "id": l.id,
            "product_id": l.product_id,
            "description": l.description,
            "quantity": l.quantity,
            "unit_price": str(l.unit_price),
            "base_amount": str(l.base_amount),
            "discount_amount": str(l.discount_amount),
            "net_amount": str(l.net_amount),
            "tax_amount": str(l.tax_amount),
            "line_total": str(l.line_total),
            "tax_breakdown": l.tax_breakdown or []
        })

    payments = []
    for p in inv.payments:
        payments.append({
            "id": p.id,
            "number": p.number,
            "method": p.method,
            "amount": str(p.amount),
            "paid_on": p.paid_on,
            "reference": p.reference,
            "status": p.status
        })

    return {
        "id": inv.id,
        "number": inv.number or "—",
        "subscription_id": inv.subscription_id,
        "customer_id": inv.customer_id,
        "customer_name": inv.customer.company_name if inv.customer else "",
        "status": inv.status,
        "invoice_date": inv.invoice_date,
        "due_date": inv.due_date,
        "period_start": inv.period_start,
        "period_end": inv.period_end,
        "currency": inv.currency,
        "customer_snapshot": inv.customer_snapshot or {},
        "untaxed_total": str(inv.untaxed_total),
        "discount_total": str(inv.discount_total),
        "tax_total": str(inv.tax_total),
        "total": str(inv.total),
        "amount_paid": str(inv.amount_paid),
        "amount_due": str(due),
        "is_overdue": is_overdue,
        "lines": lines,
        "payments": payments
    }

@router.get("")
def list_invoices(
    status: Optional[str] = Query(None),
    customer_id: Optional[str] = Query(None),
    overdue_only: Optional[bool] = Query(False),
    db: Session = Depends(get_db)
):
    q = db.query(Invoice)
    if status:
        q = q.filter(Invoice.status == status)
    if customer_id:
        q = q.filter(Invoice.customer_id == customer_id)
    if overdue_only:
        q = q.filter(Invoice.status == "confirmed", Invoice.due_date < today())

    invs = q.order_by(Invoice.invoice_date.desc()).all()
    return [serialize_invoice(i) for i in invs]

@router.get("/{id}")
def get_invoice_detail(id: str, db: Session = Depends(get_db)):
    inv = db.query(Invoice).filter(Invoice.id == id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return serialize_invoice(inv)

@router.post("/{id}/confirm")
def confirm_invoice(id: str, db: Session = Depends(get_db)):
    inv = db.query(Invoice).filter(Invoice.id == id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if inv.status != "draft":
        raise HTTPException(status_code=400, detail="Only draft invoices can be confirmed")

    inv.status = "confirmed"
    inv.number = next_number("INV", inv.invoice_date.year)
    inv.confirmed_at = now()

    # Zero total invoice auto-paid
    if D(inv.total) == ZERO:
        inv.status = "paid"
        inv.paid_at = inv.invoice_date

    db.commit()
    return serialize_invoice(inv)

@router.post("/{id}/cancel")
def cancel_invoice(id: str, reason: str = "Cancelled by user", db: Session = Depends(get_db)):
    inv = db.query(Invoice).filter(Invoice.id == id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if inv.amount_paid > ZERO:
        raise HTTPException(status_code=400, detail="Cannot cancel invoice with recorded payments")

    inv.status = "cancelled"
    inv.cancel_reason = reason
    inv.cancelled_at = now()
    db.commit()
    return serialize_invoice(inv)
