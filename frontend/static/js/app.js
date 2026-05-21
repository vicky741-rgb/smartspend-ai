const SmartSpend = (() => {
  const categories = ["Food", "Shopping", "Bills", "Travel", "Entertainment", "Health", "Education", "Investments", "Others"];
  const money = (value) => `$${Number(value || 0).toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
  const getToken = () => localStorage.getItem("smartspend_token");
  const headers = () => ({ "Content-Type": "application/json", ...(getToken() ? { Authorization: `Bearer ${getToken()}` } : {}) });
  const api = async (url, options = {}) => {
    const res = await fetch(url, { credentials: "include", ...options, headers: { ...headers(), ...(options.headers || {}) } });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || "Request failed");
    return data;
  };
  const fillCategories = () => {
    document.querySelectorAll('select[name="category"], #expenseCategory').forEach((select) => {
      const first = select.id === "expenseCategory" ? '<option value="">All categories</option>' : "";
      select.innerHTML = first + categories.map((cat) => `<option>${cat}</option>`).join("");
    });
  };
  const chartState = {};
  const makeChart = (id, type, labels, data, colors) => {
    const ctx = document.getElementById(id);
    if (!ctx) return;
    chartState[id]?.destroy();
    chartState[id] = new Chart(ctx, {
      type,
      data: { labels, datasets: [{ data, label: "Amount", borderColor: "#4d8dff", backgroundColor: colors, tension: .35, fill: type === "line" }] },
      options: { responsive: true, plugins: { legend: { labels: { color: getComputedStyle(document.documentElement).getPropertyValue("--text") } } }, scales: { x: { ticks: { color: "#aab8d4" }, grid: { color: "rgba(255,255,255,.08)" } }, y: { ticks: { color: "#aab8d4" }, grid: { color: "rgba(255,255,255,.08)" } } } }
    });
  };
  const bindTheme = () => {
    const saved = localStorage.getItem("smartspend_theme") || "dark";
    document.documentElement.dataset.theme = saved;
    document.getElementById("themeToggle")?.addEventListener("click", () => {
      const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
      document.documentElement.dataset.theme = next;
      localStorage.setItem("smartspend_theme", next);
    });
  };

  document.addEventListener("DOMContentLoaded", () => {
    bindTheme();
    document.querySelectorAll("[data-auth-tab]").forEach((button) => button.addEventListener("click", () => {
      document.querySelectorAll("[data-auth-tab]").forEach((b) => b.classList.remove("active"));
      button.classList.add("active");
      ["login", "register", "forgot"].forEach((name) => document.getElementById(`${name}Form`).classList.toggle("hidden", name !== button.dataset.authTab));
    }));
    const authMsg = document.getElementById("authMessage");
    document.getElementById("loginForm")?.addEventListener("submit", async (event) => {
      event.preventDefault();
      const payload = Object.fromEntries(new FormData(event.target));
      try {
        const data = await api("/api/login", { method: "POST", body: JSON.stringify(payload) });
        localStorage.setItem("smartspend_token", data.token);
        location.href = "/dashboard";
      } catch (err) { authMsg.textContent = err.message; }
    });
    document.getElementById("registerForm")?.addEventListener("submit", async (event) => {
      event.preventDefault();
      const payload = Object.fromEntries(new FormData(event.target));
      try {
        const data = await api("/api/register", { method: "POST", body: JSON.stringify(payload) });
        localStorage.setItem("smartspend_token", data.token);
        location.href = "/dashboard";
      } catch (err) { authMsg.textContent = err.message; }
    });
    document.getElementById("forgotForm")?.addEventListener("submit", async (event) => {
      event.preventDefault();
      const payload = Object.fromEntries(new FormData(event.target));
      try { authMsg.textContent = (await api("/api/forgot-password", { method: "POST", body: JSON.stringify(payload) })).message; }
      catch (err) { authMsg.textContent = err.message; }
    });
  });

  async function dashboard() {
    const load = async () => {
      const data = await api("/api/dashboard");
      document.querySelector('[data-metric="budget"] b').textContent = money(data.budget.monthly_budget);
      document.querySelector('[data-metric="expenses"] b').textContent = money(data.total_expenses);
      document.querySelector('[data-metric="remaining"] b').textContent = money(data.remaining);
      document.querySelector('[data-metric="prediction"] b').textContent = money(data.prediction.prediction.predicted_expense);
      document.querySelectorAll(".metric").forEach((card) => { card.classList.remove("green", "red", "orange"); card.classList.add(data.status); });
      const labels = Object.keys(data.category_breakdown);
      const values = Object.values(data.category_breakdown);
      makeChart("categoryChart", "doughnut", labels, values, ["#21c878", "#ff4d5e", "#ffb84d", "#4d8dff", "#9b7bff", "#00c2a8", "#f06", "#7ce38b", "#92a4ff"]);
      makeChart("dailyChart", "line", Object.keys(data.daily_spending), Object.values(data.daily_spending), "rgba(77,141,255,.22)");
      Plotly.newPlot("gaugeChart", [{ type: "indicator", mode: "gauge+number", value: data.utilization, gauge: { axis: { range: [0, 120] }, bar: { color: data.status === "red" ? "#ff4d5e" : data.status === "orange" ? "#ffb84d" : "#21c878" } } }], { paper_bgcolor: "rgba(0,0,0,0)", font: { color: "#aab8d4" }, height: 280, margin: { t: 15, b: 10 } });
      document.getElementById("recommendations").innerHTML = data.recommendations.map((tip) => `<p>${tip}</p>`).join("");
    };
    document.getElementById("refreshDashboard")?.addEventListener("click", load);
    await load();
    setInterval(load, 30000);
  }

  async function expenses() {
    fillCategories();
    document.querySelector('input[name="date"]').valueAsDate = new Date();
    const render = async () => {
      const params = new URLSearchParams();
      if (document.getElementById("expenseSearch").value) params.set("search", document.getElementById("expenseSearch").value);
      if (document.getElementById("expenseCategory").value) params.set("category", document.getElementById("expenseCategory").value);
      const rows = await api(`/api/expenses?${params}`);
      document.getElementById("expenseRows").innerHTML = rows.map((item) => `<tr><td>${item.date}</td><td>${item.category}</td><td>${item.description}</td><td>${item.payment_method}</td><td>${money(item.amount)}</td><td><span class="row-actions"><button data-edit='${JSON.stringify(item)}'>Edit</button><button data-delete="${item.id}">Delete</button></span></td></tr>`).join("");
    };
    document.getElementById("expenseForm").addEventListener("submit", async (event) => {
      event.preventDefault();
      const payload = Object.fromEntries(new FormData(event.target));
      const id = payload.id;
      delete payload.id;
      await api(id ? `/api/expenses/${id}` : "/api/expenses", { method: id ? "PUT" : "POST", body: JSON.stringify(payload) });
      event.target.reset();
      document.querySelector('input[name="date"]').valueAsDate = new Date();
      await render();
    });
    document.getElementById("expenseRows").addEventListener("click", async (event) => {
      const edit = event.target.dataset.edit;
      const del = event.target.dataset.delete;
      if (edit) {
        const item = JSON.parse(edit);
        Object.entries(item).forEach(([key, value]) => { const input = document.querySelector(`[name="${key}"]`); if (input) input.value = value; });
      }
      if (del && confirm("Delete this expense?")) { await api(`/api/expenses/${del}`, { method: "DELETE" }); await render(); }
    });
    ["expenseSearch", "expenseCategory"].forEach((id) => document.getElementById(id).addEventListener("input", render));
    document.getElementById("voiceExpense").addEventListener("click", () => {
      const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!Recognition) return alert("Speech recognition is not available in this browser.");
      const recognition = new Recognition();
      recognition.onresult = (event) => { document.querySelector('[name="description"]').value = event.results[0][0].transcript; };
      recognition.start();
    });
    await render();
  }

  async function analytics() {
    const data = await api("/api/analytics");
    makeChart("monthlyChart", "bar", data.monthly.map((m) => m.month), data.monthly.map((m) => m.total), "#4d8dff");
    Plotly.newPlot("forecastChart", [{ type: "bar", x: Object.keys(data.forecast.category_forecast), y: Object.values(data.forecast.category_forecast), marker: { color: ["#21c878", "#ff4d5e", "#ffb84d", "#4d8dff", "#9b7bff", "#00c2a8", "#f06", "#7ce38b", "#92a4ff"] } }], { paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)", font: { color: "#aab8d4" } });
    document.getElementById("healthScore").textContent = data.summary.financial_health_score;
    document.getElementById("analyticsTips").innerHTML = data.summary.recommendations.map((tip) => `<p>${tip}</p>`).join("");
  }

  async function reports() {
    const data = await api("/api/dashboard");
    document.getElementById("reportAssistant").innerHTML = data.recommendations.map((tip) => `<p>${tip}</p>`).join("") + `<p>Predicted next month spend: ${money(data.prediction.prediction.predicted_expense)}.</p>`;
  }

  async function settings() {
    const budget = await api("/api/budget");
    document.querySelector('[name="monthly_budget"]').value = budget.monthly_budget;
    document.getElementById("budgetForm").addEventListener("submit", async (event) => {
      event.preventDefault();
      await api("/api/budget", { method: "POST", body: JSON.stringify(Object.fromEntries(new FormData(event.target))) });
      alert("Budget updated.");
    });
    const notifications = await api("/api/notifications");
    document.getElementById("notificationList").innerHTML = notifications.map((item) => `<p>${item.type.toUpperCase()}: ${item.message}</p>`).join("") || "<p>No alerts yet.</p>";
  }

  async function admin() {
    const stats = await api("/api/admin/stats");
    document.getElementById("adminUsers").textContent = stats.total_users;
    document.getElementById("adminExpenses").textContent = money(stats.total_expenses);
    document.getElementById("adminInactive").textContent = stats.inactive_users;
    document.getElementById("adminRows").innerHTML = stats.users.map((user) => `<tr><td>${user.name}</td><td>${user.email}</td><td>${user.role}</td><td>${user.is_verified}</td></tr>`).join("");
  }

  return { dashboard, expenses, analytics, reports, settings, admin };
})();
