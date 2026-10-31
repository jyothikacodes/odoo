from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field

# Auth
class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    company_name: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    customer_id: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# Taxes
class TaxResponse(BaseModel):
    id: str
    name: str
    kind: str
    rate: Decimal
    price_included: bool
    is_active: bool

# Products & Variants
class VariantResponse(BaseModel):
    id: str
    attribute_name: str
    value: str
    extra_price: Decimal

class ProductResponse(BaseModel):
    id: str
    name: str
    product_type: str
    sales_price: Decimal
    cost_price: Optional[Decimal] = None
    notes: Optional[str] = None
    is_active: bool
    tax_ids: List[str] = []
    variants: List[VariantResponse] = []

class PlanResponse(BaseModel):
    id: str
    name: str
    price: Decimal
    billing_period: str
    period_interval: int
    min_quantity: int
    available_from: date
    available_to: Optional[date] = None
    is_active: bool
    auto_close: bool
    closable: bool
    pausable: bool
    renewable: bool
    tax_ids: List[str] = []

# Quotation Template
class QuotationTemplateResponse(BaseModel):
    id: str
    name: str
    plan_id: str
    validity_days: int
    lines: List[Dict[str, Any]]

# Discounts
class DiscountResponse(BaseModel):
    id: str
    name: str
    kind: str
    value: Decimal
    scope: str
    min_purchase: Decimal
    min_quantity: int
    priority: int
    usage_limit: Optional[int] = None
    usage_count: int
    valid_from: date
    valid_to: Optional[date] = None
    is_active: bool
    product_ids: List[str] = []
    subscription_ids: List[str] = []

# Subscription
class SubscriptionLineIn(BaseModel):
    product_id: Optional[str] = None
    description: Optional[str] = None
    quantity: int = 1
    variant_ids: List[str] = []
    tax_ids: Optional[List[str]] = None

class SubscriptionCreate(BaseModel):
    customer_id: str
    plan_id: str
    payment_term_id: Optional[str] = None
    start_date: Optional[date] = None
    term_months: int = 12
    lines: List[SubscriptionLineIn] = []
    auto_renew: bool = True
    notes: Optional[str] = None

class SubscriptionLineResponse(BaseModel):
    id: str
    product_id: Optional[str] = None
    is_plan_fee: bool
    description: str
    quantity: int
    unit_price: Decimal
    tax_ids: List[str] = []
    amount: Decimal

class SubscriptionResponse(BaseModel):
    id: str
    number: str
    customer_id: str
    customer_name: Optional[str] = None
    plan_id: str
    plan_name: Optional[str] = None
    status: str
    start_date: date
    expiry_date: date
    anchor_date: date
    next_billing_date: Optional[date] = None
    last_billed_through: Optional[date] = None
    is_paused: bool
    paused_from: Optional[date] = None
    auto_renew: bool
    untaxed_total: Decimal
    tax_total: Decimal
    total: Decimal
    allowed_actions: List[str] = []
    lines: List[SubscriptionLineResponse] = []
    notes: Optional[str] = None

class TransitionRequest(BaseModel):
    action: str
    reason: Optional[str] = None

# Invoices
class InvoiceLineResponse(BaseModel):
    id: str
    product_id: Optional[str] = None
    description: str
    quantity: int
    unit_price: Decimal
    base_amount: Decimal
    discount_amount: Decimal
    net_amount: Decimal
    tax_amount: Decimal
    line_total: Decimal
    tax_breakdown: List[Dict[str, Any]] = []

class InvoiceResponse(BaseModel):
    id: str
    number: Optional[str] = None
    subscription_id: Optional[str] = None
    customer_id: str
    customer_name: Optional[str] = None
    status: str
    invoice_date: date
    due_date: date
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    untaxed_total: Decimal
    discount_total: Decimal
    tax_total: Decimal
    total: Decimal
    amount_paid: Decimal
    amount_due: Decimal
    is_overdue: bool
    lines: List[InvoiceLineResponse] = []

# Payments
class PaymentRecordRequest(BaseModel):
    method: str
    amount: Decimal
    paid_on: Optional[date] = None
    reference: Optional[str] = None
    note: Optional[str] = None

class PaymentResponse(BaseModel):
    id: str
    number: str
    invoice_id: str
    invoice_number: Optional[str] = None
    customer_name: Optional[str] = None
    method: str
    amount: Decimal
    paid_on: date
    reference: Optional[str] = None
    note: Optional[str] = None
    status: str
