import uuid
from datetime import datetime, date, timezone
from decimal import Decimal
from sqlalchemy import (
    Column, String, Integer, Numeric, Boolean, Date, DateTime,
    ForeignKey, Text, JSON
)
from sqlalchemy.orm import relationship
from app.core.db import Base
from app.core.money import ZERO, D

def gen_uuid() -> str:
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    role = Column(String(32), nullable=False, default="customer") # 'admin', 'internal', 'customer'
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    customer_profile = relationship("Customer", back_populates="user", uselist=False)

class Customer(Base):
    __tablename__ = "customers"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    company_name = Column(String(255), nullable=False)
    contact_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(64), nullable=True)
    address = Column(Text, nullable=True)
    tax_id = Column(String(64), nullable=True)
    is_tax_exempt = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="customer_profile")
    subscriptions = relationship("Subscription", back_populates="customer")
    invoices = relationship("Invoice", back_populates="customer")

class Tax(Base):
    __tablename__ = "taxes"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(128), nullable=False)
    kind = Column(String(32), nullable=False, default="percentage") # 'percentage' | 'fixed'
    rate = Column(Numeric(10, 4), nullable=False)
    price_included = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class PaymentTerm(Base):
    __tablename__ = "payment_terms"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(64), nullable=False)
    due_days = Column(Integer, default=0) # 0 = Immediate, 15, 30, 60

class Product(Base):
    __tablename__ = "products"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=False)
    product_type = Column(String(32), default="software") # 'software' | 'addon' | 'service'
    sales_price = Column(Numeric(12, 2), nullable=False, default=ZERO)
    cost_price = Column(Numeric(12, 2), nullable=False, default=ZERO)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    tax_ids = Column(JSON, default=list) # list of tax IDs
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    attributes = relationship("ProductAttribute", back_populates="product", cascade="all, delete-orphan")
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")

class ProductAttribute(Base):
    __tablename__ = "product_attributes"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False)
    name = Column(String(64), nullable=False) # e.g. 'Brand'

    product = relationship("Product", back_populates="attributes")
    variants = relationship("ProductVariant", back_populates="attribute")

class ProductVariant(Base):
    __tablename__ = "product_variants"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False)
    attribute_id = Column(String(36), ForeignKey("product_attributes.id"), nullable=False)
    value = Column(String(128), nullable=False) # e.g. 'Odoo' or 'Custom'
    extra_price = Column(Numeric(12, 2), default=ZERO) # e.g. 560.00

    product = relationship("Product", back_populates="variants")
    attribute = relationship("ProductAttribute", back_populates="variants")

class Plan(Base):
    __tablename__ = "plans"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(128), nullable=False)
    price = Column(Numeric(12, 2), nullable=False, default=ZERO)
    billing_period = Column(String(32), nullable=False) # 'daily', 'weekly', 'monthly', 'yearly'
    period_interval = Column(Integer, default=1)
    min_quantity = Column(Integer, default=1)
    available_from = Column(Date, nullable=False)
    available_to = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)
    auto_close = Column(Boolean, default=False)
    closable = Column(Boolean, default=True)
    pausable = Column(Boolean, default=True)
    renewable = Column(Boolean, default=True)
    tax_ids = Column(JSON, default=list)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class QuotationTemplate(Base):
    __tablename__ = "quotation_templates"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(128), nullable=False)
    plan_id = Column(String(36), ForeignKey("plans.id"), nullable=False)
    validity_days = Column(Integer, default=15)
    lines_json = Column(JSON, default=list)

    plan = relationship("Plan")

class Discount(Base):
    __tablename__ = "discounts"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(128), nullable=False)
    kind = Column(String(32), nullable=False) # 'fixed' | 'percentage'
    value = Column(Numeric(12, 2), nullable=False)
    scope = Column(String(32), default="subscription") # 'product' | 'subscription'
    min_purchase = Column(Numeric(12, 2), default=ZERO)
    min_quantity = Column(Integer, default=0)
    priority = Column(Integer, default=10)
    usage_limit = Column(Integer, nullable=True)
    usage_count = Column(Integer, default=0)
    valid_from = Column(Date, nullable=False)
    valid_to = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)
    product_ids = Column(JSON, default=list)
    subscription_ids = Column(JSON, default=list)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    number = Column(String(64), unique=True, nullable=False, index=True)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False)
    plan_id = Column(String(36), ForeignKey("plans.id"), nullable=False)
    payment_term_id = Column(String(36), ForeignKey("payment_terms.id"), nullable=True)

    status = Column(String(32), default="draft", index=True) # draft, quotation, confirmed, active, closed
    start_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=False)
    term_months = Column(Integer, default=12)
    anchor_date = Column(Date, nullable=False)
    next_billing_date = Column(Date, nullable=True, index=True)
    last_billed_through = Column(Date, nullable=True)

    is_paused = Column(Boolean, default=False)
    paused_from = Column(Date, nullable=True)

    quotation_sent_at = Column(DateTime, nullable=True)
    quotation_valid_until = Column(Date, nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    activated_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    close_reason = Column(String(255), nullable=True)

    auto_renew = Column(Boolean, default=True)
    renewal_count = Column(Integer, default=0)

    untaxed_total = Column(Numeric(12, 2), default=ZERO)
    tax_total = Column(Numeric(12, 2), default=ZERO)
    total = Column(Numeric(12, 2), default=ZERO)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    customer = relationship("Customer", back_populates="subscriptions")
    plan = relationship("Plan")
    payment_term = relationship("PaymentTerm")
    lines = relationship("SubscriptionLine", back_populates="subscription", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="subscription")

class SubscriptionLine(Base):
    __tablename__ = "subscription_lines"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    subscription_id = Column(String(36), ForeignKey("subscriptions.id"), nullable=False)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=True)
    is_plan_fee = Column(Boolean, default=False)
    description = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(12, 2), nullable=False, default=ZERO)
    tax_ids = Column(JSON, default=list)
    amount = Column(Numeric(12, 2), nullable=False, default=ZERO)
    sort_order = Column(Integer, default=0)

    subscription = relationship("Subscription", back_populates="lines")
    product = relationship("Product")

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    number = Column(String(64), nullable=True, unique=True, index=True)
    subscription_id = Column(String(36), ForeignKey("subscriptions.id"), nullable=True)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False)

    status = Column(String(32), default="draft", index=True) # draft, confirmed, paid, cancelled
    invoice_date = Column(Date, nullable=False, index=True)
    due_date = Column(Date, nullable=False, index=True)
    period_start = Column(Date, nullable=True)
    period_end = Column(Date, nullable=True)
    currency = Column(String(10), default="INR")

    customer_snapshot = Column(JSON, default=dict)

    untaxed_total = Column(Numeric(12, 2), default=ZERO)
    discount_total = Column(Numeric(12, 2), default=ZERO)
    tax_total = Column(Numeric(12, 2), default=ZERO)
    total = Column(Numeric(12, 2), default=ZERO)
    amount_paid = Column(Numeric(12, 2), default=ZERO)

    confirmed_at = Column(DateTime, nullable=True)
    paid_at = Column(Date, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    cancel_reason = Column(String(255), nullable=True)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    subscription = relationship("Subscription", back_populates="invoices")
    customer = relationship("Customer", back_populates="invoices")
    lines = relationship("InvoiceLine", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="invoice")

class InvoiceLine(Base):
    __tablename__ = "invoice_lines"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    invoice_id = Column(String(36), ForeignKey("invoices.id"), nullable=False)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=True)
    description = Column(String(255), nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(Numeric(12, 2), default=ZERO)
    base_amount = Column(Numeric(12, 2), default=ZERO)
    discount_id = Column(String(36), nullable=True)
    discount_amount = Column(Numeric(12, 2), default=ZERO)
    net_amount = Column(Numeric(12, 2), default=ZERO)
    tax_breakdown = Column(JSON, default=list)
    tax_amount = Column(Numeric(12, 2), default=ZERO)
    line_total = Column(Numeric(12, 2), default=ZERO)
    sort_order = Column(Integer, default=0)

    invoice = relationship("Invoice", back_populates="lines")

class Payment(Base):
    __tablename__ = "payments"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    number = Column(String(64), nullable=False, unique=True)
    invoice_id = Column(String(36), ForeignKey("invoices.id"), nullable=False)
    method = Column(String(32), nullable=False) # 'bank_transfer', 'credit_card', 'upi', 'cheque', 'cash'
    amount = Column(Numeric(12, 2), nullable=False)
    paid_on = Column(Date, nullable=False)
    reference = Column(String(128), nullable=True)
    note = Column(Text, nullable=True)
    status = Column(String(32), default="posted") # 'posted', 'reversed'
    reversed_at = Column(DateTime, nullable=True)
    reverse_reason = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    invoice = relationship("Invoice", back_populates="payments")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), nullable=True)
    user_email = Column(String(255), nullable=True)
    action = Column(String(128), nullable=False)
    entity_type = Column(String(64), nullable=False)
    entity_id = Column(String(64), nullable=False)
    details = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class BillingRun(Base):
    __tablename__ = "billing_runs"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    run_date = Column(Date, nullable=False)
    status = Column(String(32), default="running") # 'running', 'completed', 'partial', 'failed'
    due_count = Column(Integer, default=0)
    billed_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    log = Column(JSON, default=list)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
