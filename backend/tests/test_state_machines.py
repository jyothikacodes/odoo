import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.db import Base
from app.models.schema import Subscription, Plan
from app.services.seed_data import seed_database
from app.services.subscription_service import transition_subscription, get_allowed_actions
from app.core.errors import InvalidTransitionError, PlanFlagDisallowsError

@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    seed_database(db)
    yield db
    db.close()

def test_subscription_state_transitions(test_db):
    # Acme subscription is active
    sub = test_db.query(Subscription).filter(Subscription.status == "active").first()
    assert sub is not None

    # Active subscription can be paused (Business Monthly is pausable)
    transition_subscription(test_db, sub.id, "pause", role="admin")
    test_db.refresh(sub)
    assert sub.is_paused is True

    # When paused, it can be resumed
    transition_subscription(test_db, sub.id, "resume", role="admin")
    test_db.refresh(sub)
    assert sub.is_paused is False

    # Illegal transition: cannot send_quotation when active
    with pytest.raises(InvalidTransitionError):
        transition_subscription(test_db, sub.id, "send_quotation", role="admin")

    # Renewal extends expiry date
    old_expiry = sub.expiry_date
    transition_subscription(test_db, sub.id, "renew", role="admin")
    test_db.refresh(sub)
    assert sub.expiry_date > old_expiry
    assert sub.renewal_count == 1
