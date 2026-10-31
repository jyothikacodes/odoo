from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.db import get_db
from app.models.schema import Subscription, Invoice, Customer
from app.schemas.api_schemas import TransitionRequest
from app.routers.subscriptions import serialize_subscription
from app.routers.invoices import serialize_invoice
from app.services.subscription_service import transition_subscription

router = APIRouter(prefix="/api/v1/portal", tags=["Customer Portal"])

@router.get("/customer/{customer_id}/subscriptions")
def portal_subscriptions(customer_id: str, db: Session = Depends(get_db)):
    subs = db.query(Subscription).filter(Subscription.customer_id == customer_id).all()
    return [serialize_subscription(s, role="customer") for s in subs]

@router.get("/customer/{customer_id}/invoices")
def portal_invoices(customer_id: str, db: Session = Depends(get_db)):
    invs = db.query(Invoice).filter(Invoice.customer_id == customer_id).order_by(Invoice.invoice_date.desc()).all()
    return [serialize_invoice(i) for i in invs]

@router.post("/customer/{customer_id}/subscriptions/{id}/action")
def portal_subscription_action(
    customer_id: str,
    id: str,
    req: TransitionRequest,
    db: Session = Depends(get_db)
):
    sub = db.query(Subscription).filter(Subscription.id == id, Subscription.customer_id == customer_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    updated = transition_subscription(db, id, req.action, role="customer", reason=req.reason)
    return serialize_subscription(updated, role="customer")
