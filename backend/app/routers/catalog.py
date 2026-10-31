from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.core.db import get_db
from app.models.schema import Product, Plan, Tax, PaymentTerm, Discount, QuotationTemplate, Customer

router = APIRouter(prefix="/api/v1", tags=["Catalog"])

@router.get("/products")
def get_products(db: Session = Depends(get_db)):
    products = db.query(Product).filter(Product.is_active == True).all()
    out = []
    for p in products:
        variants = []
        for v in p.variants:
            variants.append({
                "id": v.id,
                "attribute_id": v.attribute_id,
                "attribute_name": v.attribute.name if v.attribute else "Option",
                "value": v.value,
                "extra_price": str(v.extra_price)
            })
        out.append({
            "id": p.id,
            "name": p.name,
            "product_type": p.product_type,
            "sales_price": str(p.sales_price),
            "cost_price": str(p.cost_price),
            "notes": p.notes,
            "is_active": p.is_active,
            "tax_ids": p.tax_ids or [],
            "variants": variants
        })
    return out

@router.get("/plans")
def get_plans(db: Session = Depends(get_db)):
    plans = db.query(Plan).filter(Plan.is_active == True).all()
    return [{
        "id": pl.id,
        "name": pl.name,
        "price": str(pl.price),
        "billing_period": pl.billing_period,
        "period_interval": pl.period_interval,
        "min_quantity": pl.min_quantity,
        "available_from": pl.available_from,
        "available_to": pl.available_to,
        "is_active": pl.is_active,
        "auto_close": pl.auto_close,
        "closable": pl.closable,
        "pausable": pl.pausable,
        "renewable": pl.renewable,
        "tax_ids": pl.tax_ids or []
    } for pl in plans]

@router.get("/taxes")
def get_taxes(db: Session = Depends(get_db)):
    taxes = db.query(Tax).filter(Tax.is_active == True).all()
    return [{
        "id": t.id,
        "name": t.name,
        "kind": t.kind,
        "rate": str(t.rate),
        "price_included": t.price_included,
        "is_active": t.is_active
    } for t in taxes]

@router.get("/payment-terms")
def get_payment_terms(db: Session = Depends(get_db)):
    pts = db.query(PaymentTerm).all()
    return [{
        "id": p.id,
        "name": p.name,
        "due_days": p.due_days
    } for p in pts]

@router.get("/discounts")
def get_discounts(db: Session = Depends(get_db)):
    discs = db.query(Discount).filter(Discount.is_active == True).all()
    return [{
        "id": d.id,
        "name": d.name,
        "kind": d.kind,
        "value": str(d.value),
        "scope": d.scope,
        "min_purchase": str(d.min_purchase),
        "min_quantity": d.min_quantity,
        "priority": d.priority,
        "usage_limit": d.usage_limit,
        "usage_count": d.usage_count,
        "valid_from": d.valid_from,
        "valid_to": d.valid_to,
        "is_active": d.is_active
    } for d in discs]

@router.get("/templates")
def get_templates(db: Session = Depends(get_db)):
    tpls = db.query(QuotationTemplate).all()
    return [{
        "id": t.id,
        "name": t.name,
        "plan_id": t.plan_id,
        "plan_name": t.plan.name if t.plan else "",
        "validity_days": t.validity_days,
        "lines": t.lines_json or []
    } for t in tpls]

@router.get("/customers")
def get_customers(db: Session = Depends(get_db)):
    customers = db.query(Customer).all()
    return [{
        "id": c.id,
        "company_name": c.company_name,
        "contact_name": c.contact_name,
        "email": c.email,
        "phone": c.phone,
        "address": c.address,
        "tax_id": c.tax_id,
        "is_tax_exempt": c.is_tax_exempt
    } for c in customers]
