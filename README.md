# Brightloop Software — Subscription Management & Recurring Billing Platform

A unified, high-performance platform engineered for recurring revenue businesses. Designed to eliminate spreadsheets, automate billing cycles, prevent revenue leakage, and provide real-time financial observability.

---

## 🌟 Executive Summary & Hackathon Innovations

Recurring revenue businesses like Brightloop Software face critical failure points:
- **Missed Renewals & Churn:** Contracts tracked on spreadsheets are forgotten.
- **Invoicing Discrepancies:** Manual calculations introduce tax and discount errors.
- **Unreconciled Payments:** Scrolling bank statements delays cashflow visibility.
- **Delayed Reporting:** Quarterly reports take days to manually compile.

### 🚀 Key Innovations Introduced
1. **Brightloop AI Revenue Copilot & Churn Risk Engine:**
   - **Autonomous Health Scoring (0–100):** Real-time customer evaluation factoring in payment timeliness, subscription duration, and renewal history.
   - **Churn Risk Matrix:** Classifies accounts into Low, Medium, and Critical Risk categories.
   - **Smart Dunning AI Generator:** Generates personalized, tone-calibrated reminder notices (Gentle, Firm, Final Warning) based on invoice delinquency.
2. **Interactive Time-Travel & Billing Day Simulator:**
   - Test recurring cycles on demand by advancing virtual dates and triggering billing runs interactively.
3. **Multi-Role Experience with Instant Switcher:**
   - Seamless role switching between **Admin (Sarah Connor)**, **Staff (Meera Staff)**, and **Customer Portal (Rajiv Sharma - Acme Pvt Ltd)**.

---

## 🏗 System Architecture & Core Engines

```
Product / Plan Catalog ──► Quotation Template ──► Subscription Lifecycle
                                                        │
                      ┌─────────────────────────────────┴─────────────────────────────────┐
                      ▼                                                                   ▼
             Automated Billing Engine                                            Customer Portal
             (Idempotent & Catch-up)                                          (Self-Service Quoting)
                      │
        ┌─────────────┴─────────────┐
        ▼                           ▼
   Tax Engine                 Discount Engine
(GST Incl./Excl.)          (Largest-Remainder Split)
        │                           │
        └─────────────┬─────────────┘
                      ▼
               Invoices (INV)
                      │
                      ▼
            Payments & Aging Buckets ──► Executive Analytics Dashboard
```

### 1. Catalog & Variant Engine
- **Product Variants:** Variant values dynamically modify the base price. Example: selecting the `Odoo` variant on **Brightloop ERP Seat** adds `₹560.00` to the base `₹1,000.00` price.
- **Flexible Plans:** Daily, weekly, monthly, and yearly intervals with plan-level lifecycle controls (`auto_close`, `closable`, `pausable`, `renewable`).

### 2. Subscription Lifecycle State Machine
- Strict state machine: `Draft ▸ Quotation ▸ Confirmed ▸ Active ▸ Closed`.
- Enforces plan rules (e.g., non-closable plans block premature termination until expiry).
- Safe pause/resume semantics preserving billing cursors.

### 3. Automated Billing & Golden Invoice Precision
- **Idempotency:** Billing runs never double-bill or skip periods. Unique constraints on `(subscription_id, period_start, period_end)`.
- **Catch-up Billing:** Automatically catches up multiple unbilled periods up to the run date.
- **Mathematical Rigor:** Strict `Decimal` fixed-point arithmetic with `ROUND_HALF_UP` rounding.
- **Golden Invoice Verification:**
  - Plan Fee: `₹500.00`
  - ERP Seat (Brand=Odoo) × 2: `₹3,120.00`
  - Untaxed Header Base: `₹3,620.00`
  - Volume 10% Discount: `-₹362.00` (allocated `₹50.00` and `₹312.00`)
  - GST 18%: `₹586.44`
  - **Authoritative Total: ₹3,844.44** (matches test vector exactly)

### 4. Payments, Partial Payments & Aging
- Validates payment bounds (`0 < amount <= amount_due`).
- Automatically transitions invoices to `PAID` once the balance reaches zero.
- Reversal workflow for administrators.
- Live aging buckets: `1–30`, `31–60`, `61–90`, and `90+` days overdue.

---

## 🧪 Automated Test Suite

All pure calculation engines and numeric vectors are verified with unit and integration tests:

```bash
# Run test suite
pytest backend/tests -v
```

### Included Test Modules:
- `backend/tests/test_password_policy.py`: Verifies length (>8), character classes, common passwords, and email inclusion.
- `backend/tests/test_period.py`: Golden date vectors for daily, weekly, monthly, and leap-year yearly periods.
- `backend/tests/test_tax.py`: Inclusive, exclusive, mixed, and tax-exempt calculations.
- `backend/tests/test_discount.py`: Largest-remainder penny split and stacking rules.
- `backend/tests/test_golden_invoice.py`: End-to-end numeric verification of the Acme Pvt Ltd golden invoice.
- `backend/tests/test_state_machines.py`: State transition rules, guard conditions, and plan flags.

---

## 🚀 Quickstart & Installation

### Option 1: Native Run (Python 3.12+)

```bash
# 1. Clone repository
git clone https://github.com/jyothikacodes/odoo.git
cd odoo

# 2. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch application (auto-seeds demo data)
python run.py
```

Open your browser to: **`http://localhost:8000`**

### Option 2: Docker / Docker Compose

```bash
docker compose up --build
```

---

## 🔑 Pre-Seeded Demo Credentials

| Role | Email | Password | Persona |
|---|---|---|---|
| **Admin** | `admin@brightloop.example` | `Admin@12345!` | Sarah Connor (Full Platform Access) |
| **Internal Staff** | `staff@brightloop.example` | `Staff@12345!` | Meera Staff (Day-to-day Operations) |
| **Customer** | `customer@acme.example` | `Customer@12345!` | Rajiv Sharma (Acme Pvt Ltd Portal) |

---

## 📽 Demo Video Guide

Refer to [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md) for a ready-to-record 2.5-minute video walkthrough covering every evaluation rubric.
