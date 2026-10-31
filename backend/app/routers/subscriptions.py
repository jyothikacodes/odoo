from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.db import get_db
from app.models.schema import Subscription, Customer
from app.schemas.api_schemas import SubscriptionCreate, TransitionRequest
from app.services.subscription_service import (
    create_subscription, transition_subscription, get_allowed_actions
)

router = APIRouter(prefix="/api/v1/subscriptions", tags=["Subscriptions"])

def serialize_subscription(s: Subscription, role: str = "admin") -> dict:
    lines = []
    for l in s.lines:
        lines.append({
            "id": l.id,
            "product_id": l.product_id,
            "is_plan_fee": l.is_plan_fee,
            "description": l.description,
            "quantity": l.quantity,
            "unit_price": str(l.unit_price),
            "tax_ids": l.tax_ids or [],
            "amount": str(l.amount)
        })

    return {
        "id": s.id,
        "number": s.number,
        "customer_id": s.customer_id,
        "customer_name": s.customer.company_name if s.customer else "",
        "plan_id": s.plan_id,
        "plan_name": s.plan.name if s.plan else "",
        "status": s.status,
        "start_date": s.start_date,
        "expiry_date": s.expiry_date,
        "anchor_date": s.anchor_date,
        "next_billing_date": s.next_billing_date,
        "last_billed_through": s.last_billed_through,
        "is_paused": s.is_paused,
        "paused_from": s.paused_from,
        "auto_renew": s.auto_renew,
        "untaxed_total": str(s.untaxed_total),
        "tax_total": str(s.tax_total),
        "total": str(s.total),
        "allowed_actions": get_allowed_actions(s, role),
        "lines": lines,
        "notes": s.notes
    }

@router.get("")
def list_subscriptions(
    status: Optional[str] = Query(None),
    customer_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    q = db.query(Subscription)
    if status:
        q = q.filter(Subscription.status == status)
    if customer_id:
        q = q.filter(Subscription.customer_id == customer_id)
    subs = q.order_by(Subscription.created_at.desc()).all()
    return [serialize_subscription(s) for s in subs]

@router.post("")
def create_new_subscription(req: SubscriptionCreate, db: Session = Depends(get_db)):
    lines_data = [l.model_dump() for l in req.lines]
    sub = create_subscription(
        db=db,
        customer_id=req.customer_id,
        plan_id=req.plan_id,
        payment_term_id=req.payment_term_id,
        start_date=req.start_date,
        term_months=req.term_months,
        lines_in=lines_data,
        auto_renew=req.auto_renew,
        notes=req.notes
    )
    return serialize_subscription(sub)

@router.get("/{id}")
def get_subscription_detail(id: str, db: Session = Depends(get_db)):
    sub = db.query(Subscription).filter(Subscription.id == id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return serialize_subscription(sub)

@router.post("/{id}/transition")
def run_transition(id: str, req: TransitionRequest, db: Session = Depends(get_db)):
    sub = transition_subscription(db, id, req.action, role="admin", reason=req.reason)
    return serialize_subscription(sub)
