from datetime import date
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.schema import (
    User, Customer, Tax, PaymentTerm, Product, ProductAttribute, ProductVariant,
    Plan, QuotationTemplate, Discount, Subscription, SubscriptionLine, Invoice
)
from app.core.security import hash_password
from app.core.money import q2, D
from app.services.subscription_service import create_subscription, transition_subscription
from app.services.billing_service import run_billing_engine
from app.services.payment_service import record_payment

def seed_database(db: Session) -> None:
    # If already seeded, skip
    if db.query(User).filter(User.email == "admin@brightloop.example").first():
        return

    # 1. Taxes
    gst18 = Tax(name="GST 18%", kind="percentage", rate=Decimal("18.00"), price_included=False)
    gst5 = Tax(name="GST 5%", kind="percentage", rate=Decimal("5.00"), price_included=False)
    gst18_incl = Tax(name="GST 18% (incl.)", kind="percentage", rate=Decimal("18.00"), price_included=True)
    db.add_all([gst18, gst5, gst18_incl])
    db.flush()

    # 2. Payment Terms
    pt_imm = PaymentTerm(name="Immediate", due_days=0)
    pt_15 = PaymentTerm(name="Net 15", due_days=15)
    pt_30 = PaymentTerm(name="Net 30", due_days=30)
    pt_60 = PaymentTerm(name="Net 60", due_days=60)
    db.add_all([pt_imm, pt_15, pt_30, pt_60])
    db.flush()

    # 3. Users & Customers
    admin_user = User(
        email="admin@brightloop.example",
        full_name="Sarah Connor (Admin)",
        role="admin",
        password_hash=hash_password("Admin@12345!")
    )
    staff_user = User(
        email="staff@brightloop.example",
        full_name="Meera Staff",
        role="internal",
        password_hash=hash_password("Staff@12345!")
    )
    cust_user = User(
        email="customer@acme.example",
        full_name="Rajiv Sharma",
        role="customer",
        password_hash=hash_password("Customer@12345!")
    )
    db.add_all([admin_user, staff_user, cust_user])
    db.flush()

    c_acme = Customer(
        user_id=cust_user.id,
        company_name="Acme Pvt Ltd",
        contact_name="Rajiv Sharma",
        email="customer@acme.example",
        phone="+91 98765 43210",
        address="104 Brigade Gateway, Bangalore 560055",
        tax_id="29ABCDE1234F1Z5",
        is_tax_exempt=False
    )
    c_zenith = Customer(
        company_name="Zenith Retail",
        contact_name="Anita Desai",
        email="anita@zenithretail.example",
        phone="+91 98123 45678",
        address="42 Commercial Street, Mumbai 400001",
        tax_id="27AABCT1234C1Z1",
        is_tax_exempt=False
    )
    c_northwind = Customer(
        company_name="Northwind Traders",
        contact_name="Vikram Singh",
        email="vikram@northwind.example",
        phone="+91 99887 76655",
        address="Plot 9, Cyber City, Gurgaon 122002",
        tax_id="06AAACN4321B1Z2",
        is_tax_exempt=True  # Tax Exempt Customer
    )
    db.add_all([c_acme, c_zenith, c_northwind])
    db.flush()

    # 4. Catalog: Products & Variants
    p_seat = Product(
        name="Brightloop ERP Seat",
        product_type="software",
        sales_price=Decimal("1000.00"),
        cost_price=Decimal("400.00"),
        notes="Core enterprise ERP seat license with full module access",
        tax_ids=[gst18.id]
    )
    p_support = Product(
        name="Priority Support",
        product_type="addon",
        sales_price=Decimal("250.00"),
        cost_price=Decimal("100.00"),
        notes="24/7 dedicated telephone and slack support channel",
        tax_ids=[gst18.id]
    )
    p_crm = Product(
        name="CRM Module",
        product_type="software",
        sales_price=Decimal("800.00"),
        cost_price=Decimal("300.00"),
        notes="Lead tracking, quotation pipeline, and sales automation",
        tax_ids=[gst18.id]
    )
    db.add_all([p_seat, p_support, p_crm])
    db.flush()

    # Attribute & Variants for p_seat
    attr_brand = ProductAttribute(product_id=p_seat.id, name="Brand")
    db.add(attr_brand)
    db.flush()

    var_odoo = ProductVariant(product_id=p_seat.id, attribute_id=attr_brand.id, value="Odoo", extra_price=Decimal("560.00"))
    var_custom = ProductVariant(product_id=p_seat.id, attribute_id=attr_brand.id, value="Custom", extra_price=Decimal("0.00"))
    db.add_all([var_odoo, var_custom])
    db.flush()

    # 5. Plans
    plan_monthly = Plan(
        name="Business Monthly",
        price=Decimal("500.00"),
        billing_period="monthly",
        period_interval=1,
        min_quantity=1,
        available_from=date(2026, 1, 1),
        is_active=True,
        auto_close=False,
        closable=True,
        pausable=True,
        renewable=True,
        tax_ids=[gst18.id]
    )
    plan_yearly = Plan(
        name="Business Yearly",
        price=Decimal("5000.00"),
        billing_period="yearly",
        period_interval=1,
        min_quantity=1,
        available_from=date(2026, 1, 1),
        is_active=True,
        auto_close=False,
        closable=False,
        pausable=False,
        renewable=True,
        tax_ids=[gst18.id]
    )
    plan_trial = Plan(
        name="Weekly Trial",
        price=Decimal("0.00"),
        billing_period="weekly",
        period_interval=1,
        min_quantity=1,
        available_from=date(2026, 1, 1),
        available_to=date(2026, 12, 31),
        is_active=True,
        auto_close=True,
        closable=True,
        pausable=False,
        renewable=False,
        tax_ids=[gst18.id]
    )
    db.add_all([plan_monthly, plan_yearly, plan_trial])
    db.flush()

    # 6. Quotation Template
    tpl = QuotationTemplate(
        name="Standard Annual",
        plan_id=plan_monthly.id,
        validity_days=15,
        lines_json=[
            {"product_id": p_seat.id, "quantity": 2, "variant_ids": [var_odoo.id]},
            {"product_id": p_support.id, "quantity": 1, "variant_ids": []}
        ]
    )
    db.add(tpl)

    # 7. Discounts
    d_vol10 = Discount(
        name="Volume 10%",
        kind="percentage",
        value=Decimal("10.00"),
        scope="subscription",
        min_purchase=Decimal("0.00"),
        min_quantity=3,
        priority=10,
        usage_limit=12,
        valid_from=date(2026, 1, 1),
        valid_to=date(2026, 12, 31),
        is_active=True
    )
    d_supp100 = Discount(
        name="Support Flat 100",
        kind="fixed",
        value=Decimal("100.00"),
        scope="product",
        min_purchase=Decimal("0.00"),
        min_quantity=1,
        priority=5,
        usage_limit=None,
        valid_from=date(2026, 1, 1),
        valid_to=date(2026, 12, 31),
        is_active=True,
        product_ids=[p_support.id]
    )
    db.add_all([d_vol10, d_supp100])
    db.commit()

    # 8. Golden Subscription for Acme Pvt Ltd (§P13.2)
    # Plan Business Monthly, Net 30, Start 2026-10-01, ERP Seat with Odoo variant qty 2
    sub_acme = create_subscription(
        db=db,
        customer_id=c_acme.id,
        plan_id=plan_monthly.id,
        payment_term_id=pt_30.id,
        start_date=date(2026, 10, 1),
        term_months=12,
        lines_in=[
            {"product_id": p_seat.id, "quantity": 2, "variant_ids": [var_odoo.id]}
        ]
    )
    # Move through lifecycle: draft -> quotation -> confirmed -> active
    transition_subscription(db, sub_acme.id, "send_quotation", role="admin")
    transition_subscription(db, sub_acme.id, "confirm", role="customer")
    transition_subscription(db, sub_acme.id, "activate", role="admin")

    # 9. Additional Demo Subscriptions
    # Zenith Retail: Quotation stage
    sub_zenith = create_subscription(
        db=db,
        customer_id=c_zenith.id,
        plan_id=plan_yearly.id,
        payment_term_id=pt_15.id,
        start_date=date(2026, 10, 15),
        term_months=12,
        lines_in=[
            {"product_id": p_crm.id, "quantity": 3, "variant_ids": []}
        ]
    )
    transition_subscription(db, sub_zenith.id, "send_quotation", role="admin")

    # Northwind Traders: Draft stage
    sub_northwind = create_subscription(
        db=db,
        customer_id=c_northwind.id,
        plan_id=plan_monthly.id,
        payment_term_id=pt_imm.id,
        start_date=date(2026, 11, 1),
        term_months=6,
        lines_in=[
            {"product_id": p_seat.id, "quantity": 5, "variant_ids": [var_custom.id]}
        ]
    )

    # 10. Run initial billing for 2026-10-01 to generate the Golden Invoice!
    run_billing_engine(db, date(2026, 10, 1))

    # Partial payment on golden invoice: pay 1000.00
    inv = db.query(Invoice).filter(Invoice.subscription_id == sub_acme.id).first()
    if inv:
        record_payment(
            db=db,
            invoice_id=inv.id,
            method="bank_transfer",
            amount=Decimal("1000.00"),
            paid_on=date(2026, 10, 5),
            reference="TXN-BANK-9988",
            note="Initial partial payment via NEFT"
        )

    db.commit()
