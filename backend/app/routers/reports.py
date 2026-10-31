from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.services.report_service import get_dashboard_kpis
from app.services.ai_copilot_service import analyze_customer_health, generate_smart_dunning_email

router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])

@router.get("/dashboard")
def dashboard_metrics(db: Session = Depends(get_db)):
    return get_dashboard_kpis(db)

@router.get("/ai-copilot/health/{customer_id}")
def customer_health(customer_id: str, db: Session = Depends(get_db)):
    return analyze_customer_health(db, customer_id)

@router.get("/ai-copilot/dunning/{invoice_id}")
def dunning_notice(invoice_id: str, db: Session = Depends(get_db)):
    return generate_smart_dunning_email(db, invoice_id)
