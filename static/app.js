// Brightloop Software Application Client - Premium Light & Midnight Indigo Edition
let currentRole = "admin";
let cashflowChart = null;
let currentSubscriptions = [];
let currentInvoices = [];
let currentCustomers = [];
let currentProducts = [];
let currentPlans = [];

document.addEventListener("DOMContentLoaded", () => {
  setupThemeToggle();
  setupNavigation();
  setupTimeTravel();
  setupRoleSwitcher();
  setupModals();
  refreshAll();
});

function setupThemeToggle() {
  const toggleBtn = document.getElementById("btn-theme-toggle");
  if (!toggleBtn) return;

  toggleBtn.addEventListener("click", () => {
    const isDark = document.documentElement.classList.contains("dark");
    const newTheme = isDark ? "light" : "dark";
    if (newTheme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
    localStorage.setItem("theme", newTheme);
    updateChartTheme(newTheme === "dark");
    lucide.createIcons();
  });
}

function updateChartTheme(isDark) {
  if (!cashflowChart) return;

  const textColor = isDark ? '#A1A1AA' : '#64748B';
  const headingColor = isDark ? '#F8FAFC' : '#0F172A';
  const gridColor = isDark ? 'rgba(41, 52, 73, 0.4)' : 'rgba(226, 232, 240, 0.8)';
  const tooltipBg = isDark ? '#111A2D' : '#FFFFFF';
  const tooltipBorder = isDark ? '#293449' : '#E2E8F0';

  cashflowChart.options.plugins.legend.labels.color = headingColor;
  cashflowChart.options.plugins.tooltip.backgroundColor = tooltipBg;
  cashflowChart.options.plugins.tooltip.titleColor = headingColor;
  cashflowChart.options.plugins.tooltip.bodyColor = headingColor;
  cashflowChart.options.plugins.tooltip.borderColor = tooltipBorder;

  cashflowChart.options.scales.x.ticks.color = textColor;
  cashflowChart.options.scales.x.grid.color = gridColor;

  cashflowChart.options.scales.y.ticks.color = textColor;
  cashflowChart.options.scales.y.grid.color = gridColor;

  cashflowChart.update();
}

function setupNavigation() {
  document.querySelectorAll(".nav-tab").forEach(tab => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".nav-tab").forEach(t => {
        t.classList.remove("active", "border-[#6366F1]", "text-[#6366F1]", "border-indigo-600", "text-indigo-600");
        t.classList.add("border-transparent", "text-slate-600", "dark:text-[#A1A1AA]");
      });
      tab.classList.add("active", "border-[#6366F1]", "text-[#6366F1]");
      tab.classList.remove("border-transparent", "text-slate-600", "dark:text-[#A1A1AA]");

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
      document.getElementById("modal-record-payment").classList.remove("flex");
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
      <div class="flex items-center justify-between p-3.5 rounded-xl bg-slate-50 dark:bg-[#111A2D] border border-slate-200 dark:border-[#293449] hover:border-indigo-400 dark:hover:border-[#6366F1]/50 transition shadow-sm">
        <div>
          <div class="font-display font-bold text-slate-900 dark:text-white text-sm tracking-tight">${c.name}</div>
          <div class="micro-label text-[9.5px] text-rose-600 dark:text-[#EF4444] font-extrabold mt-0.5">${c.count} unpaid invoice(s)</div>
        </div>
        <div class="font-mono font-black text-sm text-rose-600 dark:text-[#EF4444]">₹${c.amount}</div>
      </div>
    `).join("");
  } else {
    topList.innerHTML = `<div class="text-slate-400 dark:text-[#A1A1AA] text-xs italic py-2">No overdue accounts detected!</div>`;
  }

  // Render Cashflow Chart
  renderChart(parseFloat(d.total_invoiced) || 0, parseFloat(d.collected_revenue) || 0);
}

function renderChart(invoiced, collected) {
  const ctx = document.getElementById("cashflow-chart").getContext("2d");
  if (cashflowChart) cashflowChart.destroy();

  const isDark = document.documentElement.classList.contains("dark");
  const textColor = isDark ? '#A1A1AA' : '#64748B';
  const headingColor = isDark ? '#F8FAFC' : '#0F172A';
  const gridColor = isDark ? 'rgba(41, 52, 73, 0.4)' : 'rgba(226, 232, 240, 0.8)';
  const tooltipBg = isDark ? '#111A2D' : '#FFFFFF';
  const tooltipBorder = isDark ? '#293449' : '#E2E8F0';

  cashflowChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: ["Aug 2026", "Sep 2026", "Oct 2026 (Current)"],
      datasets: [
        {
          label: "Invoiced Revenue (Accrual)",
          data: [invoiced * 0.7, invoiced * 0.85, invoiced],
          backgroundColor: "#6366F1",
          hoverBackgroundColor: "#4F46E5",
          borderRadius: 8
        },
        {
          label: "Cash Collected",
          data: [collected * 0.8, collected * 0.9, collected],
          backgroundColor: isDark ? "#22D3EE" : "#0284C7",
          hoverBackgroundColor: isDark ? "#06B6D4" : "#0369A1",
          borderRadius: 8
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "top",
          labels: {
            color: headingColor,
            font: { family: "'Outfit', 'Plus Jakarta Sans', sans-serif", size: 12, weight: 700 },
            boxWidth: 14,
            padding: 16
          }
        },
        tooltip: {
          backgroundColor: tooltipBg,
          titleColor: headingColor,
          bodyColor: headingColor,
          borderColor: tooltipBorder,
          borderWidth: 1,
          padding: 12,
          cornerRadius: 10,
          titleFont: { family: "'Outfit', sans-serif", size: 13, weight: 'bold' },
          bodyFont: { family: "'JetBrains Mono', monospace", size: 12 }
        }
      },
      scales: {
        x: {
          ticks: {
            color: textColor,
            font: { family: "'Outfit', sans-serif", size: 12, weight: 600 }
          },
          grid: {
            color: gridColor
          }
        },
        y: {
          ticks: {
            color: textColor,
            font: { family: "'JetBrains Mono', monospace", size: 11, weight: 600 },
            callback: (v) => "₹" + Number(v).toLocaleString()
          },
          grid: {
            color: gridColor
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
      <button onclick="triggerSubAction('${s.id}', '${act}')" class="px-2.5 py-1 rounded-lg micro-label text-[10px] font-extrabold bg-slate-100 hover:bg-slate-200 dark:bg-[#111A2D] dark:hover:bg-[#1B2541] text-slate-700 hover:text-slate-900 dark:text-[#A1A1AA] dark:hover:text-[#F8FAFC] border border-slate-200 dark:border-[#293449] hover:border-indigo-400 dark:hover:border-[#6366F1] transition shadow-sm ml-1 tracking-wider">
        ${act.replace('_', ' ')}
      </button>
    `).join("");

    return `
      <tr class="hover:bg-slate-50 dark:hover:bg-[#1B2541]/50 border-b border-slate-100 dark:border-[#293449]/60 transition-colors">
        <td class="p-3.5 font-mono font-black text-xs text-indigo-600 dark:text-[#22D3EE] tracking-wide">${s.number}</td>
        <td class="p-3.5 font-display font-bold text-slate-900 dark:text-white text-sm tracking-tight">${s.customer_name}</td>
        <td class="p-3.5 text-slate-600 dark:text-[#A1A1AA] font-medium">${s.plan_name}</td>
        <td class="p-3.5">${statusBadge}</td>
        <td class="p-3.5 text-slate-600 dark:text-[#A1A1AA] font-mono text-xs font-semibold">${s.start_date}</td>
        <td class="p-3.5 text-slate-600 dark:text-[#A1A1AA] font-mono text-xs font-semibold">${s.expiry_date}</td>
        <td class="p-3.5 text-indigo-600 dark:text-indigo-400 font-bold font-mono text-xs">${s.next_billing_date || '—'}</td>
        <td class="p-3.5 text-right font-mono font-black text-sm text-slate-900 dark:text-white">₹${s.total}</td>
        <td class="p-3.5 text-right whitespace-nowrap">${actionBtns || '<span class="text-slate-400 dark:text-[#A1A1AA]/50 text-xs">—</span>'}</td>
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
      <tr class="hover:bg-slate-50 dark:hover:bg-[#1B2541]/50 border-b border-slate-100 dark:border-[#293449]/60 transition-colors">
        <td class="p-3.5 font-mono font-black text-xs text-indigo-600 dark:text-[#22D3EE] hover:text-indigo-800 dark:hover:text-cyan-300 cursor-pointer transition underline-offset-2 hover:underline tracking-wide" onclick="openInvoiceModal('${inv.id}')">${inv.number}</td>
        <td class="p-3.5 font-display font-bold text-slate-900 dark:text-white text-sm tracking-tight">${inv.customer_name}</td>
        <td class="p-3.5 text-slate-600 dark:text-[#A1A1AA] font-mono text-xs font-semibold">${inv.invoice_date}</td>
        <td class="p-3.5 text-slate-600 dark:text-[#A1A1AA] font-mono text-xs font-semibold">${inv.due_date}</td>
        <td class="p-3.5 text-right font-mono text-xs text-slate-600 dark:text-[#A1A1AA]">₹${inv.untaxed_total}</td>
        <td class="p-3.5 text-right font-mono text-xs text-emerald-600 dark:text-[#22C55E] font-bold">₹${inv.discount_total}</td>
        <td class="p-3.5 text-right font-mono text-xs text-slate-600 dark:text-[#A1A1AA]">₹${inv.tax_total}</td>
        <td class="p-3.5 text-right font-mono font-black text-sm text-slate-900 dark:text-white">₹${inv.total}</td>
        <td class="p-3.5 text-right font-mono font-bold text-xs text-emerald-600 dark:text-[#22C55E]">₹${inv.amount_paid}</td>
        <td class="p-3.5 text-right font-mono font-black text-sm ${parseFloat(inv.amount_due) > 0 ? 'text-rose-600 dark:text-[#EF4444]' : 'text-slate-400 dark:text-[#A1A1AA]'}">₹${inv.amount_due}</td>
        <td class="p-3.5">${statusChip}</td>
        <td class="p-3.5 text-right whitespace-nowrap">
          ${canPay ? `
            <button onclick="openPaymentModal('${inv.id}', '${inv.number}', '${inv.amount_due}')" class="bg-[#6366F1] hover:bg-[#4F46E5] text-white px-3 py-1.5 rounded-lg font-display font-bold text-xs shadow-sm hover:shadow-glow-indigo transition tracking-wide">
              Pay
            </button>
          ` : ''}
          <button onclick="openInvoiceModal('${inv.id}')" class="bg-slate-100 hover:bg-slate-200 dark:bg-[#111A2D] dark:hover:bg-[#1B2541] text-slate-700 hover:text-slate-900 dark:text-[#A1A1AA] dark:hover:text-[#F8FAFC] border border-slate-200 dark:border-[#293449] hover:border-indigo-400 dark:hover:border-[#6366F1] px-2.5 py-1.5 rounded-lg font-display font-bold text-xs transition ml-1 tracking-wide">
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
    <tr class="hover:bg-slate-50 dark:hover:bg-[#1B2541]/50 border-b border-slate-100 dark:border-[#293449]/60 transition-colors">
      <td class="p-3.5 font-mono font-black text-xs text-slate-900 dark:text-white tracking-wide">${p.number}</td>
      <td class="p-3.5 font-mono font-bold text-xs text-indigo-600 dark:text-[#22D3EE]">${p.invoice_number}</td>
      <td class="p-3.5 font-display font-bold text-slate-900 dark:text-white text-sm tracking-tight">${p.customer_name}</td>
      <td class="p-3.5 micro-label text-[10px] text-slate-600 dark:text-[#A1A1AA]">${p.method.replace('_', ' ')}</td>
      <td class="p-3.5 text-slate-600 dark:text-[#A1A1AA] font-mono text-xs font-semibold">${p.paid_on}</td>
      <td class="p-3.5 font-mono text-slate-500 dark:text-[#A1A1AA] text-xs">${p.reference || '—'}</td>
      <td class="p-3.5 text-right font-mono font-black text-sm text-emerald-600 dark:text-[#22C55E]">₹${p.amount}</td>
      <td class="p-3.5">
        <span class="micro-label px-2.5 py-1 rounded-full border ${p.status === 'posted' ? 'bg-emerald-100 dark:bg-emerald-500/15 text-emerald-800 dark:text-[#22C55E] border-emerald-300 dark:border-emerald-500/30' : 'bg-slate-100 dark:bg-slate-700/30 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-600/30'}">
          ${p.status.toUpperCase()}
        </span>
      </td>
      <td class="p-3.5 text-right">
        ${p.status === 'posted' && currentRole === 'admin' ? `
          <button onclick="reversePayment('${p.id}')" class="text-rose-600 dark:text-[#EF4444] hover:text-rose-800 dark:hover:text-red-300 font-display font-bold text-xs transition tracking-wide">Reverse</button>
        ` : '<span class="text-slate-400 dark:text-[#A1A1AA]/50 text-xs">—</span>'}
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
    <div class="p-4 bg-slate-50 dark:bg-[#111A2D] rounded-xl border border-slate-200 dark:border-[#293449] space-y-2 hover:border-indigo-400 dark:hover:border-[#6366F1]/50 transition shadow-sm">
      <div class="flex items-center justify-between">
        <span class="font-display font-bold text-slate-900 dark:text-white text-base tracking-tight">${p.name}</span>
        <span class="font-mono font-black text-sm text-indigo-600 dark:text-[#22D3EE]">₹${p.sales_price}</span>
      </div>
      <div class="text-xs text-slate-500 dark:text-[#A1A1AA] font-medium">${p.notes || ''}</div>
      ${p.variants.length > 0 ? `
        <div class="pt-1 flex flex-wrap gap-1.5">
          ${p.variants.map(v => `
            <span class="text-[10px] bg-white dark:bg-[#151D32] border border-slate-200 dark:border-[#293449] text-slate-700 dark:text-[#A1A1AA] px-2.5 py-1 rounded-md font-mono">
              ${v.attribute_name}=<span class="text-slate-900 dark:text-white font-bold">${v.value}</span> <span class="text-indigo-600 dark:text-indigo-400 font-bold">(+₹${v.extra_price})</span>
            </span>
          `).join("")}
        </div>
      ` : ''}
    </div>
  `).join("");

  const planList = document.getElementById("catalog-plans-list");
  planList.innerHTML = currentPlans.map(pl => `
    <div class="p-4 bg-slate-50 dark:bg-[#111A2D] rounded-xl border border-slate-200 dark:border-[#293449] space-y-2 hover:border-indigo-400 dark:hover:border-[#6366F1]/50 transition shadow-sm">
      <div class="flex items-center justify-between">
        <span class="font-display font-bold text-slate-900 dark:text-white text-base tracking-tight">${pl.name}</span>
        <span class="font-mono font-black text-sm text-emerald-600 dark:text-[#22C55E]">₹${pl.price} <span class="text-xs text-slate-500 dark:text-[#A1A1AA] font-normal font-sans">/ ${pl.billing_period}</span></span>
      </div>
      <div class="text-[11px] text-slate-500 dark:text-[#A1A1AA] flex flex-wrap gap-2 pt-1 font-medium">
        <span class="bg-white dark:bg-[#151D32] border border-slate-200 dark:border-[#293449] px-2.5 py-0.5 rounded-md">Pausable: <b class="${pl.pausable ? 'text-emerald-600 dark:text-emerald-400 font-bold' : 'text-slate-400'}">${pl.pausable ? 'Yes' : 'No'}</b></span>
        <span class="bg-white dark:bg-[#151D32] border border-slate-200 dark:border-[#293449] px-2.5 py-0.5 rounded-md">Renewable: <b class="${pl.renewable ? 'text-emerald-600 dark:text-emerald-400 font-bold' : 'text-slate-400'}">${pl.renewable ? 'Yes' : 'No'}</b></span>
        <span class="bg-white dark:bg-[#151D32] border border-slate-200 dark:border-[#293449] px-2.5 py-0.5 rounded-md">Closable: <b class="${pl.closable ? 'text-emerald-600 dark:text-emerald-400 font-bold' : 'text-slate-400'}">${pl.closable ? 'Yes' : 'No'}</b></span>
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
      ? `<span class="bg-emerald-100 dark:bg-emerald-500/15 text-emerald-800 dark:text-[#22C55E] border border-emerald-300 dark:border-emerald-500/30 px-2.5 py-1 rounded-full micro-label">Low Risk</span>`
      : h.churn_risk === 'Medium'
        ? `<span class="bg-amber-100 dark:bg-amber-500/15 text-amber-800 dark:text-[#F59E0B] border border-amber-300 dark:border-amber-500/30 px-2.5 py-1 rounded-full micro-label">Medium Risk</span>`
        : `<span class="bg-rose-100 dark:bg-rose-500/15 text-rose-800 dark:text-[#EF4444] border border-rose-300 dark:border-rose-500/30 px-2.5 py-1 rounded-full micro-label">Critical Risk</span>`;

    return `
      <tr class="hover:bg-slate-50 dark:hover:bg-[#1B2541]/50 border-b border-slate-100 dark:border-[#293449]/60 transition-colors">
        <td class="p-3.5 font-display font-bold text-slate-900 dark:text-white text-sm tracking-tight">${c.company_name}</td>
        <td class="p-3.5 font-display font-black text-base tracking-tight ${h.health_score >= 80 ? 'text-emerald-600 dark:text-[#22C55E]' : (h.health_score >= 50 ? 'text-amber-600 dark:text-[#F59E0B]' : 'text-rose-600 dark:text-[#EF4444]')}">
          ${h.health_score} <span class="text-xs font-normal text-slate-500 dark:text-[#A1A1AA] font-sans">/ 100</span>
        </td>
        <td class="p-3.5">${riskBadge}</td>
        <td class="p-3.5 font-mono font-semibold ${h.max_days_overdue > 0 ? 'text-rose-600 dark:text-[#EF4444] font-bold' : 'text-slate-600 dark:text-[#A1A1AA]'}">
          ${h.max_days_overdue} days
        </td>
        <td class="p-3.5 text-slate-600 dark:text-[#A1A1AA] text-xs font-medium">${h.recommendation}</td>
        <td class="p-3.5 text-right">
          <button onclick="document.querySelector('[data-tab=\\'ai-copilot\\']').click()" class="bg-indigo-50 hover:bg-indigo-100 dark:bg-indigo-500/15 dark:hover:bg-indigo-500/25 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-500/30 px-3 py-1 rounded-lg font-display font-bold text-xs transition shadow-sm tracking-wide">
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
    <div class="bg-white dark:bg-[#151D32] p-5 rounded-[16px] border border-slate-200 dark:border-[#293449] shadow-sm dark:shadow-card hover:border-indigo-400 dark:hover:border-[#6366F1]/50 transition-all space-y-3">
      <div class="flex items-center justify-between">
        <span class="font-mono font-black text-xs text-indigo-600 dark:text-[#22D3EE] tracking-wide">${s.number}</span>
        ${getStatusBadge(s.status, s.is_paused)}
      </div>
      <div>
        <div class="text-base font-display font-bold text-slate-900 dark:text-white tracking-tight">${s.plan_name}</div>
        <div class="text-xs text-slate-500 dark:text-[#A1A1AA] mt-0.5">Contract End: <span class="font-mono text-slate-800 dark:text-white font-semibold">${s.expiry_date}</span></div>
      </div>
      <div class="pt-3 border-t border-slate-100 dark:border-[#293449] flex items-center justify-between">
        <span class="font-mono font-black text-lg text-slate-900 dark:text-white">₹${s.total}</span>
        <div class="space-x-1.5">
          ${s.allowed_actions.map(act => `
            <button onclick="portalAction('${acme.id}', '${s.id}', '${act}')" class="bg-indigo-50 hover:bg-indigo-100 dark:bg-indigo-500/20 dark:hover:bg-indigo-500/30 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-500/30 px-3 py-1 rounded-lg font-display font-bold text-xs transition tracking-wide">
              ${act}
            </button>
          `).join("")}
        </div>
      </div>
    </div>
  `).join("");

  const invsBody = document.getElementById("portal-invoices-body");
  invsBody.innerHTML = pInvs.map(i => `
    <tr class="hover:bg-slate-50 dark:hover:bg-[#1B2541]/50 border-b border-slate-100 dark:border-[#293449]/60 transition-colors">
      <td class="p-3.5 font-mono font-black text-xs text-indigo-600 dark:text-[#22D3EE] tracking-wide">${i.number}</td>
      <td class="p-3.5 text-slate-600 dark:text-[#A1A1AA] font-mono text-xs font-semibold">${i.invoice_date}</td>
      <td class="p-3.5 text-slate-600 dark:text-[#A1A1AA] font-mono text-xs font-semibold">${i.due_date}</td>
      <td class="p-3.5 text-right font-mono font-black text-sm text-slate-900 dark:text-white">₹${i.total}</td>
      <td class="p-3.5 text-right font-mono font-bold text-xs text-emerald-600 dark:text-[#22C55E]">₹${i.amount_paid}</td>
      <td class="p-3.5">${getInvoiceStatusChip(i.status, i.is_overdue)}</td>
      <td class="p-3.5 text-right">
        <button onclick="openInvoiceModal('${i.id}')" class="bg-slate-100 hover:bg-slate-200 dark:bg-[#111A2D] dark:hover:bg-[#1B2541] border border-slate-200 dark:border-[#293449] hover:border-indigo-400 dark:hover:border-[#6366F1] px-3 py-1.5 rounded-lg font-display font-bold text-xs text-slate-700 hover:text-slate-900 dark:text-[#A1A1AA] dark:hover:text-[#F8FAFC] transition tracking-wide">
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
    <div class="flex justify-between items-start border-b border-slate-200 dark:border-[#293449] pb-4">
      <div>
        <div class="micro-label text-slate-500 dark:text-[#A1A1AA]">Billed To</div>
        <div class="text-xl font-black font-display tracking-tight text-slate-900 dark:text-white mt-1">${inv.customer_snapshot.company_name || inv.customer_name}</div>
        <div class="text-slate-500 dark:text-[#A1A1AA] text-xs mt-0.5">${inv.customer_snapshot.contact_name || ''}</div>
        <div class="text-slate-500 dark:text-[#A1A1AA] text-xs">${inv.customer_snapshot.address || ''}</div>
        <div class="text-slate-500 dark:text-[#A1A1AA] text-xs mt-1 font-medium">GSTIN: <span class="font-mono text-indigo-600 dark:text-[#22D3EE] font-bold">${inv.customer_snapshot.tax_id || 'N/A'}</span></div>
      </div>
      <div class="text-right">
        <div class="font-mono text-xl font-black text-[#6366F1] tracking-tight">${inv.number}</div>
        <div class="text-xs text-slate-500 dark:text-[#A1A1AA] mt-1">Date: <b class="text-slate-900 dark:text-white font-mono">${inv.invoice_date}</b></div>
        <div class="text-xs text-slate-500 dark:text-[#A1A1AA]">Due Date: <b class="text-slate-900 dark:text-white font-mono">${inv.due_date}</b></div>
        <div class="mt-2.5">${getInvoiceStatusChip(inv.status, inv.is_overdue)}</div>
      </div>
    </div>

    <!-- Lines Table -->
    <div class="overflow-x-auto rounded-xl border border-slate-200 dark:border-[#293449]">
      <table class="w-full text-left text-xs">
        <thead class="bg-slate-50 dark:bg-[#111A2D] text-slate-500 dark:text-[#A1A1AA] border-b border-slate-200 dark:border-[#293449]">
          <tr>
            <th class="p-2.5 micro-label">Item Description</th>
            <th class="p-2.5 micro-label text-center">Qty</th>
            <th class="p-2.5 micro-label text-right">Unit Price</th>
            <th class="p-2.5 micro-label text-right">Discount</th>
            <th class="p-2.5 micro-label text-right">Tax (GST)</th>
            <th class="p-2.5 micro-label text-right">Amount</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100 dark:divide-[#293449]/60 bg-white dark:bg-[#151D32]">
          ${inv.lines.map(l => `
            <tr class="hover:bg-slate-50 dark:hover:bg-[#1B2541]/40 transition">
              <td class="p-2.5 font-semibold text-slate-900 dark:text-white">${l.description}</td>
              <td class="p-2.5 text-center text-slate-600 dark:text-[#A1A1AA] font-mono font-bold">${l.quantity}</td>
              <td class="p-2.5 text-right font-mono text-slate-600 dark:text-[#A1A1AA]">₹${l.unit_price}</td>
              <td class="p-2.5 text-right font-mono text-emerald-600 dark:text-[#22C55E] font-bold">₹${l.discount_amount}</td>
              <td class="p-2.5 text-right font-mono text-slate-600 dark:text-[#A1A1AA]">₹${l.tax_amount}</td>
              <td class="p-2.5 text-right font-mono font-black text-slate-900 dark:text-white">₹${l.line_total}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>

    <!-- Totals Summary -->
    <div class="flex justify-end pt-2">
      <div class="w-72 space-y-1.5 text-right bg-slate-50 dark:bg-[#111A2D] p-4 rounded-xl border border-slate-200 dark:border-[#293449] text-xs">
        <div class="flex justify-between text-slate-600 dark:text-[#A1A1AA] font-medium"><span>Untaxed Base:</span> <span class="font-mono text-slate-900 dark:text-white font-bold">₹${inv.untaxed_total}</span></div>
        <div class="flex justify-between text-emerald-600 dark:text-[#22C55E] font-bold"><span>Discount Savings:</span> <span class="font-mono">-₹${inv.discount_total}</span></div>
        <div class="flex justify-between text-slate-600 dark:text-[#A1A1AA] font-medium"><span>GST Taxes:</span> <span class="font-mono text-slate-900 dark:text-white font-bold">₹${inv.tax_total}</span></div>
        <div class="flex justify-between font-black text-sm border-t border-slate-200 dark:border-[#293449] pt-2 mt-1"><span class="font-display font-bold text-slate-900 dark:text-white">Total Invoice:</span> <span class="font-mono text-indigo-600 dark:text-[#22D3EE] font-black text-base">₹${inv.total}</span></div>
        <div class="flex justify-between text-emerald-600 dark:text-[#22C55E] font-bold"><span>Amount Paid:</span> <span class="font-mono">₹${inv.amount_paid}</span></div>
        <div class="flex justify-between text-rose-600 dark:text-[#EF4444] font-black border-t border-slate-200 dark:border-[#293449]/60 pt-1.5"><span>Balance Due:</span> <span class="font-mono">₹${inv.amount_due}</span></div>
      </div>
    </div>
  `;

  document.getElementById("modal-view-invoice").classList.remove("hidden");
  document.getElementById("modal-view-invoice").classList.add("flex");
}

function getStatusBadge(status, isPaused) {
  if (isPaused) {
    return `<span class="bg-purple-100 dark:bg-purple-500/15 text-purple-800 dark:text-purple-300 border border-purple-200 dark:border-purple-500/30 micro-label px-2.5 py-1 rounded-full">PAUSED</span>`;
  }
  const map = {
    draft: "bg-slate-100 dark:bg-slate-500/15 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-500/30",
    quotation: "bg-sky-100 dark:bg-cyan-500/15 text-sky-800 dark:text-[#22D3EE] border-sky-200 dark:border-cyan-500/30",
    confirmed: "bg-amber-100 dark:bg-amber-500/15 text-amber-800 dark:text-[#F59E0B] border-amber-200 dark:border-amber-500/30",
    active: "bg-emerald-100 dark:bg-emerald-500/15 text-emerald-800 dark:text-[#22C55E] border-emerald-200 dark:border-emerald-500/30",
    closed: "bg-zinc-100 dark:bg-zinc-500/15 text-zinc-700 dark:text-[#A1A1AA] border-zinc-200 dark:border-zinc-500/30"
  };
  const cls = map[status] || 'bg-slate-100 dark:bg-slate-500/15 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-500/30';
  return `<span class="${cls} border micro-label px-2.5 py-1 rounded-full">${status}</span>`;
}

function getInvoiceStatusChip(status, isOverdue) {
  if (status === "paid") {
    return `<span class="bg-emerald-100 dark:bg-emerald-500/15 text-emerald-800 dark:text-[#22C55E] border border-emerald-200 dark:border-emerald-500/30 micro-label px-2.5 py-1 rounded-full">PAID</span>`;
  }
  if (isOverdue) {
    return `<span class="bg-rose-100 dark:bg-rose-500/15 text-rose-800 dark:text-[#EF4444] border border-rose-200 dark:border-rose-500/30 micro-label px-2.5 py-1 rounded-full">OVERDUE</span>`;
  }
  if (status === "confirmed") {
    return `<span class="bg-amber-100 dark:bg-amber-500/15 text-amber-800 dark:text-[#F59E0B] border border-amber-200 dark:border-amber-500/30 micro-label px-2.5 py-1 rounded-full">PENDING</span>`;
  }
  return `<span class="bg-slate-100 dark:bg-slate-500/15 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-500/30 micro-label px-2.5 py-1 rounded-full">${status}</span>`;
}
