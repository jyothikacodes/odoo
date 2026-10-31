from datetime import date, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.core.db import get_db
from app.core.clock import today, set_virtual_today, reset_virtual_today
from app.services.billing_service import run_billing_engine

router = APIRouter(prefix="/api/v1/simulation", tags=["Simulation"])

class AdvanceClockRequest(BaseModel):
    days: Optional[int] = 30
    target_date: Optional[date] = None

@router.get("/clock")
def get_clock():
    return {"current_date": today()}

@router.post("/advance-clock")
def advance_clock(req: AdvanceClockRequest):
    curr = today()
    new_date = req.target_date if req.target_date else (curr + timedelta(days=req.days or 30))
    set_virtual_today(new_date)
    return {
        "previous_date": curr,
        "current_date": new_date,
        "message": f"Virtual clock advanced to {new_date}"
    }

@router.post("/run-billing")
def trigger_billing(db: Session = Depends(get_db)):
    run = run_billing_engine(db, today())
    return {
        "id": run.id,
        "run_date": run.run_date,
        "status": run.status,
        "due_count": run.due_count,
        "billed_count": run.billed_count,
        "failed_count": run.failed_count,
        "log": run.log
    }

@router.post("/reset-clock")
def reset_clock():
    reset_virtual_today()
    return {"current_date": today(), "message": "Clock reset to initial demo date"}
