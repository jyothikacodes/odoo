import pytest
from datetime import date
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.db import Base
from app.core.money import D
from app.models.schema import Subscription, Invoice, Payment
from app.services.seed_data import seed_database
from app.services.payment_service import record_payment
from app.core.errors import PaymentExceedsDueError

@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    seed_database(db)
    yield db
    db.close()

def test_golden_invoice_and_payments(test_db):
    sub = test_db.query(Subscription).filter(Subscription.status == "active").first()
    assert sub is not None

    # Check Subscription Header totals (before discount)
    assert sub.untaxed_total == D("3620.00")
    assert sub.tax_total == D("651.60")
    assert sub.total == D("4271.60")

    # Check Golden Invoice generated for Acme
    inv = test_db.query(Invoice).filter(Invoice.subscription_id == sub.id).first()
    assert inv is not None
    assert inv.invoice_date == date(2026, 10, 1)
    assert inv.due_date == date(2026, 10, 31)

    # Check Exact Numeric Golden Values (§P13.2)
    assert inv.untaxed_total == D("3258.00")
    assert inv.discount_total == D("362.00")
    assert inv.tax_total == D("586.44")
    assert inv.total == D("3844.44")

    # The seed script made an initial partial payment of 1000.00
    assert inv.amount_paid == D("1000.00")
    amount_due = inv.total - inv.amount_paid
    assert amount_due == D("2844.44")

    # Check paying more than due raises PaymentExceedsDueError
    with pytest.raises(PaymentExceedsDueError):
        record_payment(test_db, inv.id, "bank_transfer", Decimal("3000.00"), paid_on=date(2026, 10, 10))

    # Pay the exact remaining amount 2844.44
    record_payment(test_db, inv.id, "upi", Decimal("2844.44"), paid_on=date(2026, 10, 15))
    test_db.refresh(inv)

    assert inv.amount_paid == D("3844.44")
    assert inv.status == "paid"
    assert inv.paid_at == date(2026, 10, 15)
