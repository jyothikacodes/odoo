from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.db import get_db
from app.models.schema import Payment
from app.schemas.api_schemas import PaymentRecordRequest
from app.services.payment_service import record_payment, reverse_payment

router = APIRouter(prefix="/api/v1", tags=["Payments"])

def serialize_payment(p: Payment) -> dict:
    inv = p.invoice
    cname = inv.customer.company_name if inv and inv.customer else ""
    return {
        "id": p.id,
        "number": p.number,
        "invoice_id": p.invoice_id,
        "invoice_number": inv.number if inv else "",
        "customer_name": cname,
        "method": p.method,
        "amount": str(p.amount),
        "paid_on": p.paid_on,
        "reference": p.reference,
        "note": p.note,
        "status": p.status,
        "reversed_at": p.reversed_at,
        "reverse_reason": p.reverse_reason
    }

@router.get("/payments")
def list_payments(db: Session = Depends(get_db)):
    pays = db.query(Payment).order_by(Payment.paid_on.desc()).all()
    return [serialize_payment(p) for p in pays]

@router.post("/invoices/{invoice_id}/payments")
def create_payment(invoice_id: str, req: PaymentRecordRequest, db: Session = Depends(get_db)):
    pay = record_payment(
        db=db,
        invoice_id=invoice_id,
        method=req.method,
        amount=req.amount,
        paid_on=req.paid_on,
        reference=req.reference,
        note=req.note
    )
    return serialize_payment(pay)

@router.post("/payments/{id}/reverse")
def run_reverse_payment(id: str, reason: str = "Reversed by admin", db: Session = Depends(get_db)):
    pay = reverse_payment(db, id, reason)
    return serialize_payment(pay)
