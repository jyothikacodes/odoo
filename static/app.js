// Brightloop Software Application Client
let currentRole = "admin";
let cashflowChart = null;
let currentSubscriptions = [];
let currentInvoices = [];
let currentCustomers = [];
let currentProducts = [];
let currentPlans = [];

document.addEventListener("DOMContentLoaded", () => {
  lucide.createIcons();
  setupNavigation();
  setupTimeTravel();
  setupRoleSwitcher();
  setupModals();
  refreshAll();
});

function setupNavigation() {
  document.querySelectorAll(".nav-tab").forEach(tab => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".nav-tab").forEach(t => {
        t.classList.remove("active", "border-indigo-600", "text-indigo-600");
        t.classList.add("border-transparent", "text-slate-600");
      });
      tab.classList.add("active", "border-indigo-600", "text-indigo-600");
      tab.classList.remove("border-transparent", "text-slate-600");

      const target = tab.dataset.tab;
      document.querySelectorAll(".tab-pane").forEach(pane => pane.classList.add("hidden"));
      const activePane = document.getElementById(`tab-${target}`);
      if (activePane) activePane.classList.remove("hidden");
    });
  });
}

function setupRoleSwitcher() {
  const sel = document.getElementById("role-selector");
  sel.addEventListener("change", (e) => {
    currentRole = e.target.value;
    if (currentRole === "customer") {
      // Switch directly to Customer Portal tab
      const portalTab = document.querySelector('[data-tab="portal"]');
      if (portalTab) portalTab.click();
    }
    refreshAll();
  });
}

function setupTimeTravel() {
  const advBtn = document.getElementById("btn-advance-month");
  advBtn.addEventListener("click", async () => {
    try {
      const res = await fetch("/api/v1/simulation/advance-clock", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ days: 30 })
      });
      const data = await res.json();
      document.getElementById("virtual-date-badge").innerText = data.current_date;
      alert(`⏱ Time Travel: Clock advanced to ${data.current_date}!\nNow click 'Run Billing Engine' to process due subscriptions.`);
      refreshAll();
    } catch (e) {
      alert("Failed to advance clock: " + e.message);
    }
  });

  const billBtn = document.getElementById("btn-trigger-billing");
  const manualBillBtn = document.getElementById("btn-manual-billing");
  const runBilling = async () => {
    try {
      const res = await fetch("/api/v1/simulation/run-billing", { method: "POST" });
      const data = await res.json();
      alert(`⚡ Billing Run Complete!\nStatus: ${data.status.toUpperCase()}\nDue Subscriptions: ${data.due_count}\nInvoices Generated: ${data.billed_count}\nErrors: ${data.failed_count}`);
      refreshAll();
    } catch (e) {
      alert("Billing run failed: " + e.message);
    }
  };

  if (billBtn) billBtn.addEventListener("click", runBilling);
  if (manualBillBtn) manualBillBtn.addEventListener("click", runBilling);
}

function setupModals() {
  const payForm = document.getElementById("form-record-payment");
  payForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const invId = document.getElementById("pay-invoice-id").value;
    const method = document.getElementById("pay-method").value;
    const amount = document.getElementById("pay-amount").value;
    const paid_on = document.getElementById("pay-date").value;
    const reference = document.getElementById("pay-reference").value;
    const note = document.getElementById("pay-note").value;

    try {
      const res = await fetch(`/api/v1/invoices/${invId}/payments`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ method, amount, paid_on, reference, note })
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.message || "Payment rejected");
      }
      document.getElementById("modal-record-payment").classList.add("hidden");
      alert("✅ Payment recorded successfully! Invoice status and aging updated.");
      refreshAll();
    } catch (err) {
      alert("Payment Error: " + err.message);
    }
  });

  // Copilot smart dunning generator
  const genBtn = document.getElementById("btn-generate-dunning");
  genBtn.addEventListener("click", async () => {
    const invId = document.getElementById("copilot-invoice-select").value;
    if (!invId) return;
    try {
      const res = await fetch(`/api/v1/reports/ai-copilot/dunning/${invId}`);
      const data = await res.json();
      document.getElementById("dunning-tone-badge").innerText = data.tone;
      document.getElementById("dunning-subject").innerText = data.subject;
      document.getElementById("dunning-body").value = data.email_body;
      document.getElementById("copilot-dunning-output").classList.remove("hidden");
    } catch (e) {
      alert("Failed to generate AI dunning: " + e.message);
    }
  });

  const refCopilot = document.getElementById("btn-refresh-copilot");
  if (refCopilot) refCopilot.addEventListener("click", loadAiCopilot);
}

async function refreshAll() {
  // Update clock display
  const clockRes = await fetch("/api/v1/simulation/clock");
  const clockData = await clockRes.json();
  document.getElementById("virtual-date-badge").innerText = clockData.current_date;

  await loadDashboard();
  await loadSubscriptions();
  await loadInvoices();
  await loadPayments();
  await loadCatalog();
  await loadAiCopilot();
  await loadPortal();
  lucide.createIcons();
}

async function loadDashboard() {
  const res = await fetch("/api/v1/reports/dashboard");
  const d = await res.json();

  document.getElementById("kpi-mrr").innerText = `₹${d.mrr}`;
  document.getElementById("kpi-arr").innerText = `₹${d.arr}`;
  document.getElementById("kpi-collected").innerText = `₹${d.collected_revenue}`;
  document.getElementById("kpi-invoiced").innerText = `₹${d.total_invoiced}`;
  document.getElementById("kpi-overdue-amt").innerText = `₹${d.overdue_amount}`;
  document.getElementById("kpi-overdue-count").innerText = d.overdue_count;
  document.getElementById("kpi-active-subs").innerText = d.active_subscriptions;
  document.getElementById("kpi-paused-subs").innerText = d.paused_subscriptions;
  document.getElementById("kpi-quote-subs").innerText = d.quotation_subscriptions;

  // Aging buckets
  const b1 = parseFloat(d.aging_buckets["1_30"]) || 0;
  const b2 = parseFloat(d.aging_buckets["31_60"]) || 0;
  const b3 = parseFloat(d.aging_buckets["61_90"]) || 0;
  const b4 = parseFloat(d.aging_buckets["90_plus"]) || 0;
  const maxB = Math.max(b1, b2, b3, b4, 1);

  document.getElementById("aging-1-30").innerText = `₹${d.aging_buckets["1_30"]}`;
  document.getElementById("aging-31-60").innerText = `₹${d.aging_buckets["31_60"]}`;
  document.getElementById("aging-61-90").innerText = `₹${d.aging_buckets["61_90"]}`;
  document.getElementById("aging-90-plus").innerText = `₹${d.aging_buckets["90_plus"]}`;

  document.getElementById("bar-1-30").style.width = `${(b1 / maxB) * 100}%`;
  document.getElementById("bar-31-60").style.width = `${(b2 / maxB) * 100}%`;
  document.getElementById("bar-61-90").style.width = `${(b3 / maxB) * 100}%`;
  document.getElementById("bar-90-plus").style.width = `${(b4 / maxB) * 100}%`;

  // Top overdue list
  const topList = document.getElementById("top-overdue-list");
  if (d.top_overdue_customers && d.top_overdue_customers.length > 0) {
    topList.innerHTML = d.top_overdue_customers.map(c => `
      <div class="flex items-center justify-between p-2 rounded bg-slate-50 border border-slate-100">
        <div>
          <div class="font-bold text-slate-800">${c.name}</div>
          <div class="text-[10px] text-rose-600 font-semibold">${c.count} unpaid invoice(s)</div>
        </div>
        <div class="font-mono font-bold text-rose-600">₹${c.amount}</div>
      </div>
    `).join("");
  } else {
    topList.innerHTML = `<div class="text-slate-400 italic">No overdue accounts detected!</div>`;
  }

  // Render Cashflow Chart
  renderChart(parseFloat(d.total_invoiced) || 0, parseFloat(d.collected_revenue) || 0);
}

function renderChart(invoiced, collected) {
  const ctx = document.getElementById("cashflow-chart").getContext("2d");
  if (cashflowChart) cashflowChart.destroy();

  cashflowChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: ["Aug 2026", "Sep 2026", "Oct 2026 (Current)"],
      datasets: [
        {
          label: "Invoiced Revenue (Accrual)",
          data: [invoiced * 0.7, invoiced * 0.85, invoiced],
          backgroundColor: "#6366f1",
          borderRadius: 6
        },
        {
          label: "Cash Collected",
          data: [collected * 0.8, collected * 0.9, collected],
          backgroundColor: "#10b981",
          borderRadius: 6
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "top" }
      },
      scales: {
        y: {
          ticks: {
            callback: (v) => "₹" + v
          }
        }
      }
    }
  });
}

async function loadSubscriptions() {
  const res = await fetch("/api/v1/subscriptions");
  currentSubscriptions = await res.json();

  const tbody = document.getElementById("subscriptions-table-body");
  tbody.innerHTML = currentSubscriptions.map(s => {
    const statusBadge = getStatusBadge(s.status, s.is_paused);
    const actionBtns = s.allowed_actions.map(act => `
      <button onclick="triggerSubAction('${s.id}', '${act}')" class="px-2 py-0.5 rounded text-[11px] font-semibold uppercase tracking-wider bg-slate-100 hover:bg-slate-200 text-slate-700 ml-1">
        ${act.replace('_', ' ')}
      </button>
    `).join("");

    return `
      <tr class="hover:bg-slate-50">
        <td class="p-3 font-mono font-bold text-indigo-600">${s.number}</td>
        <td class="p-3 font-semibold text-slate-800">${s.customer_name}</td>
        <td class="p-3">${s.plan_name}</td>
        <td class="p-3">${statusBadge}</td>
        <td class="p-3 text-slate-600">${s.start_date}</td>
        <td class="p-3 text-slate-600">${s.expiry_date}</td>
        <td class="p-3 text-indigo-700 font-semibold">${s.next_billing_date || '—'}</td>
        <td class="p-3 text-right font-mono font-bold">₹${s.total}</td>
        <td class="p-3 text-right">${actionBtns || '<span class="text-slate-400">None</span>'}</td>
      </tr>
    `;
  }).join("");
}

async function triggerSubAction(subId, action) {
  try {
    const res = await fetch(`/api/v1/subscriptions/${subId}/transition`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.message || "Transition disallowed");
    }
    refreshAll();
  } catch (e) {
    alert("Action Failed: " + e.message);
  }
}

async function loadInvoices() {
  const res = await fetch("/api/v1/invoices");
  currentInvoices = await res.json();

  // Populate dunning select box
  const overdueInvs = currentInvoices.filter(i => i.is_overdue || (i.status === "confirmed" && parseFloat(i.amount_due) > 0));
  const sel = document.getElementById("copilot-invoice-select");
  sel.innerHTML = overdueInvs.map(i => `
    <option value="${i.id}">${i.number} — ${i.customer_name} (Due: ₹${i.amount_due})</option>
  `).join("") || `<option value="">No overdue invoices found</option>`;

  const tbody = document.getElementById("invoices-table-body");
  tbody.innerHTML = currentInvoices.map(inv => {
    const isOverdue = inv.is_overdue;
    const statusChip = getInvoiceStatusChip(inv.status, isOverdue);
    const canPay = inv.status === "confirmed" && parseFloat(inv.amount_due) > 0;

    return `
      <tr class="hover:bg-slate-50">
        <td class="p-3 font-mono font-bold text-indigo-600 cursor-pointer hover:underline" onclick="openInvoiceModal('${inv.id}')">${inv.number}</td>
        <td class="p-3 font-semibold text-slate-800">${inv.customer_name}</td>
        <td class="p-3 text-slate-600">${inv.invoice_date}</td>
        <td class="p-3 text-slate-600">${inv.due_date}</td>
        <td class="p-3 text-right font-mono">₹${inv.untaxed_total}</td>
        <td class="p-3 text-right font-mono text-emerald-600">₹${inv.discount_total}</td>
        <td class="p-3 text-right font-mono">₹${inv.tax_total}</td>
        <td class="p-3 text-right font-mono font-bold">₹${inv.total}</td>
        <td class="p-3 text-right font-mono text-emerald-700">₹${inv.amount_paid}</td>
        <td class="p-3 text-right font-mono font-bold ${parseFloat(inv.amount_due) > 0 ? 'text-rose-600' : 'text-slate-400'}">₹${inv.amount_due}</td>
        <td class="p-3">${statusChip}</td>
        <td class="p-3 text-right">
          ${canPay ? `
            <button onclick="openPaymentModal('${inv.id}', '${inv.number}', '${inv.amount_due}')" class="bg-indigo-600 hover:bg-indigo-700 text-white px-2.5 py-1 rounded text-[11px] font-semibold">
              Pay
            </button>
          ` : ''}
          <button onclick="openInvoiceModal('${inv.id}')" class="bg-slate-100 hover:bg-slate-200 text-slate-700 px-2 py-1 rounded text-[11px] font-semibold ml-1">
            Receipt
          </button>
        </td>
      </tr>
    `;
  }).join("");
}

async function loadPayments() {
  const res = await fetch("/api/v1/payments");
  const payments = await res.json();

  const tbody = document.getElementById("payments-table-body");
  tbody.innerHTML = payments.map(p => `
    <tr class="hover:bg-slate-50">
      <td class="p-3 font-mono font-bold text-slate-800">${p.number}</td>
      <td class="p-3 font-mono text-indigo-600 font-semibold">${p.invoice_number}</td>
      <td class="p-3 font-semibold text-slate-800">${p.customer_name}</td>
      <td class="p-3 uppercase text-[11px] font-bold text-slate-600">${p.method.replace('_', ' ')}</td>
      <td class="p-3 text-slate-600">${p.paid_on}</td>
      <td class="p-3 font-mono text-slate-500">${p.reference || '—'}</td>
      <td class="p-3 text-right font-mono font-bold text-emerald-600">₹${p.amount}</td>
      <td class="p-3"><span class="px-2 py-0.5 rounded text-[10px] font-bold ${p.status === 'posted' ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-200 text-slate-600'}">${p.status.toUpperCase()}</span></td>
      <td class="p-3 text-right">
        ${p.status === 'posted' && currentRole === 'admin' ? `
          <button onclick="reversePayment('${p.id}')" class="text-rose-600 hover:text-rose-800 font-semibold text-[11px]">Reverse</button>
        ` : '—'}
      </td>
    </tr>
  `).join("");
}

async function reversePayment(id) {
  if (!confirm("Are you sure you want to reverse this payment? This will restore the invoice balance.")) return;
  try {
    const res = await fetch(`/api/v1/payments/${id}/reverse`, { method: "POST" });
    if (!res.ok) throw new Error("Reversal failed");
    alert("Payment reversed successfully.");
    refreshAll();
  } catch (e) {
    alert(e.message);
  }
}

async function loadCatalog() {
  const [prodRes, planRes] = await Promise.all([
    fetch("/api/v1/products"),
    fetch("/api/v1/plans")
  ]);
  currentProducts = await prodRes.json();
  currentPlans = await planRes.json();

  const prodList = document.getElementById("catalog-products-list");
  prodList.innerHTML = currentProducts.map(p => `
    <div class="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-1">
      <div class="flex items-center justify-between">
        <span class="font-bold text-slate-900">${p.name}</span>
        <span class="font-mono font-bold text-indigo-700">₹${p.sales_price}</span>
      </div>
      <div class="text-xs text-slate-500">${p.notes || ''}</div>
      ${p.variants.length > 0 ? `
        <div class="pt-1 flex flex-wrap gap-1">
          ${p.variants.map(v => `
            <span class="text-[10px] bg-white border border-slate-200 px-2 py-0.5 rounded font-mono">
              ${v.attribute_name}=${v.value} (+₹${v.extra_price})
            </span>
          `).join("")}
        </div>
      ` : ''}
    </div>
  `).join("");

  const planList = document.getElementById("catalog-plans-list");
  planList.innerHTML = currentPlans.map(pl => `
    <div class="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-1">
      <div class="flex items-center justify-between">
        <span class="font-bold text-slate-900">${pl.name}</span>
        <span class="font-mono font-bold text-emerald-700">₹${pl.price} / ${pl.billing_period}</span>
      </div>
      <div class="text-[11px] text-slate-500 flex flex-wrap gap-2 pt-1">
        <span>Pausable: <b>${pl.pausable ? 'Yes' : 'No'}</b></span>
        <span>•</span>
        <span>Renewable: <b>${pl.renewable ? 'Yes' : 'No'}</b></span>
        <span>•</span>
        <span>Closable: <b>${pl.closable ? 'Yes' : 'No'}</b></span>
      </div>
    </div>
  `).join("");
}

async function loadAiCopilot() {
  const custRes = await fetch("/api/v1/customers");
  currentCustomers = await custRes.json();

  const tableBody = document.getElementById("copilot-customer-table");
  const rows = await Promise.all(currentCustomers.map(async c => {
    const hRes = await fetch(`/api/v1/reports/ai-copilot/health/${c.id}`);
    const h = await hRes.json();
    if (!h.health_score) return '';

    const riskBadge = h.churn_risk === 'Low'
      ? `<span class="bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded font-bold">Low Risk</span>`
      : h.churn_risk === 'Medium'
        ? `<span class="bg-amber-100 text-amber-800 px-2 py-0.5 rounded font-bold">Medium Risk</span>`
        : `<span class="bg-rose-100 text-rose-800 px-2 py-0.5 rounded font-bold">Critical Risk</span>`;

    return `
      <tr>
        <td class="p-3 font-semibold text-slate-900">${c.company_name}</td>
        <td class="p-3 font-mono font-bold text-sm ${h.health_score >= 80 ? 'text-emerald-600' : (h.health_score >= 50 ? 'text-amber-600' : 'text-rose-600')}">
          ${h.health_score} / 100
        </td>
        <td class="p-3">${riskBadge}</td>
        <td class="p-3 font-mono ${h.max_days_overdue > 0 ? 'text-rose-600 font-bold' : 'text-slate-500'}">
          ${h.max_days_overdue} days
        </td>
        <td class="p-3 text-slate-600 text-[11px]">${h.recommendation}</td>
        <td class="p-3 text-right">
          <button onclick="document.querySelector('[data-tab=\\'ai-copilot\\']').click()" class="bg-purple-100 text-purple-700 hover:bg-purple-200 px-2 py-1 rounded font-semibold text-[11px]">
            Action
          </button>
        </td>
      </tr>
    `;
  }));
  tableBody.innerHTML = rows.join("");
}

async function loadPortal() {
  // Demo customer Rajiv Sharma (Acme Pvt Ltd)
  const acme = currentCustomers.find(c => c.company_name.includes("Acme"));
  if (!acme) return;

  const [subsRes, invsRes] = await Promise.all([
    fetch(`/api/v1/portal/customer/${acme.id}/subscriptions`),
    fetch(`/api/v1/portal/customer/${acme.id}/invoices`)
  ]);

  const pSubs = await subsRes.json();
  const pInvs = await invsRes.json();

  const subsContainer = document.getElementById("portal-subs-container");
  subsContainer.innerHTML = pSubs.map(s => `
    <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3">
      <div class="flex items-center justify-between">
        <span class="font-mono font-bold text-indigo-600">${s.number}</span>
        ${getStatusBadge(s.status, s.is_paused)}
      </div>
      <div>
        <div class="text-base font-bold text-slate-900">${s.plan_name}</div>
        <div class="text-xs text-slate-500">Contract End: ${s.expiry_date}</div>
      </div>
      <div class="pt-2 border-t flex items-center justify-between">
        <span class="font-mono font-black text-slate-900">₹${s.total}</span>
        <div class="space-x-1">
          ${s.allowed_actions.map(act => `
            <button onclick="portalAction('${acme.id}', '${s.id}', '${act}')" class="bg-indigo-50 hover:bg-indigo-100 text-indigo-700 px-2.5 py-1 rounded text-xs font-semibold">
              ${act}
            </button>
          `).join("")}
        </div>
      </div>
    </div>
  `).join("");

  const invsBody = document.getElementById("portal-invoices-body");
  invsBody.innerHTML = pInvs.map(i => `
    <tr>
      <td class="p-3 font-mono font-bold text-indigo-600">${i.number}</td>
      <td class="p-3">${i.invoice_date}</td>
      <td class="p-3">${i.due_date}</td>
      <td class="p-3 text-right font-mono font-bold">₹${i.total}</td>
      <td class="p-3 text-right font-mono text-emerald-600">₹${i.amount_paid}</td>
      <td class="p-3">${getInvoiceStatusChip(i.status, i.is_overdue)}</td>
      <td class="p-3 text-right">
        <button onclick="openInvoiceModal('${i.id}')" class="bg-slate-100 hover:bg-slate-200 px-2.5 py-1 rounded font-semibold text-slate-700">
          View Receipt
        </button>
      </td>
    </tr>
  `).join("");
}

async function portalAction(customerId, subId, action) {
  try {
    const res = await fetch(`/api/v1/portal/customer/${customerId}/subscriptions/${subId}/action`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action })
    });
    if (!res.ok) throw new Error("Action denied");
    refreshAll();
  } catch (e) {
    alert(e.message);
  }
}

function openPaymentModal(invoiceId, invoiceNumber, amountDue) {
  document.getElementById("pay-invoice-id").value = invoiceId;
  document.getElementById("pay-invoice-number").value = invoiceNumber;
  document.getElementById("pay-max-amount").value = `₹${amountDue}`;
  document.getElementById("pay-amount").value = amountDue;
  document.getElementById("pay-date").value = document.getElementById("virtual-date-badge").innerText;
  document.getElementById("modal-record-payment").classList.remove("hidden");
  document.getElementById("modal-record-payment").classList.add("flex");
}

function openInvoiceModal(invoiceId) {
  const inv = currentInvoices.find(i => i.id === invoiceId);
  if (!inv) return;

  const content = document.getElementById("invoice-modal-content");
  content.innerHTML = `
    <div class="flex justify-between items-start border-b pb-4">
      <div>
        <div class="text-sm font-bold text-slate-800">Billed To:</div>
        <div class="text-base font-black text-slate-900">${inv.customer_snapshot.company_name || inv.customer_name}</div>
        <div class="text-slate-500">${inv.customer_snapshot.contact_name || ''}</div>
        <div class="text-slate-500">${inv.customer_snapshot.address || ''}</div>
        <div class="text-slate-500">GSTIN: <span class="font-mono">${inv.customer_snapshot.tax_id || 'N/A'}</span></div>
      </div>
      <div class="text-right">
        <div class="font-mono text-base font-black text-indigo-600">${inv.number}</div>
        <div>Date: <b>${inv.invoice_date}</b></div>
        <div>Due Date: <b>${inv.due_date}</b></div>
        <div class="mt-1">${getInvoiceStatusChip(inv.status, inv.is_overdue)}</div>
      </div>
    </div>

    <!-- Lines Table -->
    <table class="w-full text-left text-xs border">
      <thead class="bg-slate-100 font-semibold border-b">
        <tr>
          <th class="p-2">Item Description</th>
          <th class="p-2 text-center">Qty</th>
          <th class="p-2 text-right">Unit Price</th>
          <th class="p-2 text-right">Discount</th>
          <th class="p-2 text-right">Tax (GST)</th>
          <th class="p-2 text-right">Amount</th>
        </tr>
      </thead>
      <tbody class="divide-y">
        ${inv.lines.map(l => `
          <tr>
            <td class="p-2 font-medium">${l.description}</td>
            <td class="p-2 text-center">${l.quantity}</td>
            <td class="p-2 text-right font-mono">₹${l.unit_price}</td>
            <td class="p-2 text-right font-mono text-emerald-600">₹${l.discount_amount}</td>
            <td class="p-2 text-right font-mono">₹${l.tax_amount}</td>
            <td class="p-2 text-right font-mono font-bold">₹${l.line_total}</td>
          </tr>
        `).join("")}
      </tbody>
    </table>

    <!-- Totals Summary -->
    <div class="flex justify-end pt-2">
      <div class="w-64 space-y-1 text-right">
        <div class="flex justify-between"><span>Untaxed Base:</span> <span class="font-mono">₹${inv.untaxed_total}</span></div>
        <div class="flex justify-between text-emerald-600 font-medium"><span>Discount Savings:</span> <span class="font-mono">-₹${inv.discount_total}</span></div>
        <div class="flex justify-between"><span>GST Taxes:</span> <span class="font-mono">₹${inv.tax_total}</span></div>
        <div class="flex justify-between font-black text-base border-t pt-1"><span>Total Invoice:</span> <span class="font-mono text-indigo-700">₹${inv.total}</span></div>
        <div class="flex justify-between text-emerald-700 font-bold"><span>Amount Paid:</span> <span class="font-mono">₹${inv.amount_paid}</span></div>
        <div class="flex justify-between text-rose-600 font-black"><span>Balance Due:</span> <span class="font-mono">₹${inv.amount_due}</span></div>
      </div>
    </div>
  `;

  document.getElementById("modal-view-invoice").classList.remove("hidden");
  document.getElementById("modal-view-invoice").classList.add("flex");
}

function getStatusBadge(status, isPaused) {
  if (isPaused) {
    return `<span class="bg-purple-100 text-purple-800 text-[10px] font-bold px-2 py-0.5 rounded">PAUSED</span>`;
  }
  const map = {
    draft: "bg-slate-100 text-slate-700",
    quotation: "bg-blue-100 text-blue-700",
    confirmed: "bg-amber-100 text-amber-800",
    active: "bg-emerald-100 text-emerald-800",
    closed: "bg-slate-200 text-slate-700"
  };
  return `<span class="${map[status] || 'bg-slate-100'} text-[10px] font-bold px-2 py-0.5 rounded uppercase">${status}</span>`;
}

function getInvoiceStatusChip(status, isOverdue) {
  if (status === "paid") {
    return `<span class="bg-emerald-100 text-emerald-800 text-[10px] font-bold px-2 py-0.5 rounded">PAID</span>`;
  }
  if (isOverdue) {
    return `<span class="bg-rose-100 text-rose-800 text-[10px] font-bold px-2 py-0.5 rounded">OVERDUE</span>`;
  }
  if (status === "confirmed") {
    return `<span class="bg-amber-100 text-amber-800 text-[10px] font-bold px-2 py-0.5 rounded">PENDING</span>`;
  }
  return `<span class="bg-slate-100 text-slate-700 text-[10px] font-bold px-2 py-0.5 rounded uppercase">${status}</span>`;
}
