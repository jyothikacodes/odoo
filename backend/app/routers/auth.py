from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.security import verify_password, hash_password, create_access_token, decode_access_token
from app.core.errors import EmailTakenError
from app.models.schema import User, Customer
from app.services.password_policy import check_password_or_raise
from app.schemas.api_schemas import RegisterRequest, LoginRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])

def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthenticated")
    token = authorization.split(" ")[1]
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user

@router.post("/register", response_model=TokenResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    email_clean = req.email.strip().lower()
    existing = db.query(User).filter(User.email == email_clean).first()
    if existing:
        raise EmailTakenError()

    check_password_or_raise(req.password, email=email_clean, name=req.full_name)

    user = User(
        email=email_clean,
        full_name=req.full_name,
        role="customer",
        password_hash=hash_password(req.password)
    )
    db.add(user)
    db.flush()

    cust = Customer(
        user_id=user.id,
        company_name=req.company_name or req.full_name,
        contact_name=req.full_name,
        email=email_clean
    )
    db.add(cust)
    db.commit()

    token = create_access_token({"sub": user.id, "role": user.role})
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            customer_id=cust.id
        )
    )

@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    email_clean = req.email.strip().lower()
    user = db.query(User).filter(User.email == email_clean).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    cust_id = user.customer_profile.id if user.customer_profile else None
    token = create_access_token({"sub": user.id, "role": user.role})
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            customer_id=cust_id
        )
    )

@router.get("/me", response_model=UserResponse)
def get_me(user: User = Depends(get_current_user)):
    cust_id = user.customer_profile.id if user.customer_profile else None
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        customer_id=cust_id
    )
