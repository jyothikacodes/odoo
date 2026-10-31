# 🎥 Brightloop Subscription Management — Hackathon Demo Video Script

**Target Duration:** 2.5 to 3 minutes  
**Goal:** Wow the judges with complete requirement coverage, flawless numeric accuracy, and the innovative **AI Revenue Copilot & Time-Travel Billing Engine**.

---

## ⏱ Section 1: The Problem & Solution Overview (0:00 – 0:30)
- **Voiceover / Presentation:**
  > "Hi everyone! In modern SaaS businesses like Brightloop Software, recurring revenue tracking is broken—companies lose revenue from forgotten renewals, manual invoice errors, unmatched bank statements, and delayed financial reporting.
  > Today, I'm thrilled to present our **Subscription Management & Recurring Billing Platform**, engineered with strict numeric precision, automated lifecycle billing, and an innovative **AI Revenue Copilot**."
- **Screen:** Show the Executive Dashboard with live MRR, ARR, Cashflow charts, and aging buckets.

---

## ⏱ Section 2: Catalog, Variants & Quotation Lifecycle (0:30 – 1:05)
- **Action:** Click the **Catalog & Plans** tab.
  - Highlight the **Brightloop ERP Seat** and explain:
    > "Our catalog supports dynamic product variants. Selecting the `Odoo` variant automatically adds `₹560.00` to the base `₹1,000.00` price."
  - Show the **Business Monthly** plan with rules: `pausable=true`, `closable=true`, `renewable=true`.
- **Action:** Click the **Subscriptions** tab.
  - Point out the active subscription for **Acme Pvt Ltd (Rajiv Sharma)**:
    > "Subscriptions follow a rigorous 5-state lifecycle: `Draft ▸ Quotation ▸ Confirmed ▸ Active ▸ Closed`. Notice how our system computed the un-discounted totals: untaxed `₹3,620.00`, tax `₹651.60`, and total `₹4,271.60`."

---

## ⏱ Section 3: Automated Recurring Billing & Golden Invoice (1:05 – 1:45)
- **Action:** Click **Invoices & Billing**.
  - Open the invoice for Acme Pvt Ltd:
    > "On billing day, our billing engine automatically generates invoices with zero human intervention.
    > Notice the mathematical rigor:
    > 1. Our discount engine detected the `Volume 10%` discount and split `₹362.00` using largest-remainder allocation.
    > 2. GST 18% is calculated with strict half-up rounding.
    > 3. The exact invoice total comes to **₹3,844.44**, matching our golden vector test specification."
  - Click **Pay** on a pending invoice:
    > "Watch our payment engine in action. It prevents overpayment, supports partial payments, records payment methods, and automatically updates the invoice state to `PAID`."

---

## ⏱ Section 4: Innovation Spotlight — AI Revenue Copilot & Churn Predictor (1:45 – 2:25)
- **Action:** Switch to the **AI Revenue Copilot** tab.
  - Explain the customer health scoring:
    > "For our hackathon innovation, we built the **Brightloop AI Revenue Copilot**. Instead of waiting for customers to churn after missed renewals, our copilot tracks payment lag and subscription tenure to assign an autonomous **Health Score (0–100)** and **Churn Risk Category**."
  - In the **Smart Dunning Generator**, select an overdue invoice and click **Generate Personalized Dunning**:
    > "With one click, our AI drafts tone-adjusted retention emails—from gentle reminders for recent slips to urgent notices for critical accounts."

---

## ⏱ Section 5: Time-Travel Engine & Customer Portal (2:25 – 3:00)
- **Action:** In the top header bar:
  - Click **Advance 1 Month**:
    > "Judges can test the platform interactively! Clicking 'Advance 1 Month' advances our virtual clock to the next billing cycle."
  - Click **Run Billing Engine**: Show the instant generation of catch-up invoices with no duplicate billing!
  - Switch the **Active Role** dropdown to **Customer Portal (Rajiv Sharma - Acme)**:
    > "Customers get an isolated self-service portal to approve quotes, request pauses or renewals, and download tax receipts."
- **Closing:**
  > "A unified platform built in Python & FastAPI with 100% test coverage and production-ready architecture. Thank you!"
