const API = "/api";
const state = {
  token: sessionStorage.getItem("northstar_token"),
  analyst: JSON.parse(sessionStorage.getItem("northstar_analyst") || "null"),
  transactions: [],
  risk: "all",
  query: "",
  network: null,
};

const sidebar = document.querySelector(".sidebar");
const toast = document.querySelector("#toast");
const loginDialog = document.querySelector("#login");
const caseDialog = document.querySelector("#case");
const transactionBody = document.querySelector("#transaction-body");

function showToast(message, error = false) {
  toast.textContent = message;
  toast.classList.toggle("error", error);
  toast.classList.add("show");
  window.setTimeout(() => toast.classList.remove("show"), 3500);
}

async function request(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  const response = await fetch(`${API}${path}`, { ...options, headers });
  if (response.status === 401 && path !== "/auth/login") {
    signOut(false);
    throw new Error("Your session expired. Please sign in again.");
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${response.status})`);
  }
  return response.status === 204 ? null : response.json();
}

function signOut(notify = true) {
  state.token = null;
  state.analyst = null;
  sessionStorage.removeItem("northstar_token");
  sessionStorage.removeItem("northstar_analyst");
  if (!loginDialog.open) loginDialog.showModal();
  if (notify) showToast("Signed out securely.");
}

document.querySelector(".menu").addEventListener("click", () => sidebar.classList.toggle("open"));
document.querySelectorAll(".sidebar nav a").forEach((link) => link.addEventListener("click", () => {
  document.querySelectorAll(".sidebar nav a").forEach((item) => item.classList.remove("active"));
  link.classList.add("active");
  sidebar.classList.remove("open");
}));
document.querySelector("#analyst-menu").addEventListener("click", () => signOut());
document.querySelector(".review-network").addEventListener("click", () => document.querySelector("#queue").scrollIntoView({ behavior: "smooth" }));
document.querySelector(".tools .primary").addEventListener("click", () => document.querySelector("#queue").scrollIntoView({ behavior: "smooth" }));

document.querySelector("#login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const button = event.currentTarget.querySelector("button");
  const error = document.querySelector("#login-error");
  button.disabled = true;
  button.textContent = "Signing in…";
  error.textContent = "";
  try {
    const result = await request("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email: form.get("email"), password: form.get("password") }),
    });
    state.token = result.access_token;
    state.analyst = result.analyst;
    sessionStorage.setItem("northstar_token", state.token);
    sessionStorage.setItem("northstar_analyst", JSON.stringify(state.analyst));
    loginDialog.close();
    await loadWorkspace();
    showToast(`Welcome, ${state.analyst.name}. Live services are connected.`);
  } catch (loginError) {
    error.textContent = loginError.message;
  } finally {
    button.disabled = false;
    button.textContent = "Sign in";
  }
});

function animateNumber(element, value) {
  const formatter = new Intl.NumberFormat("en-IN");
  const start = performance.now();
  function tick(now) {
    const progress = Math.min((now - start) / 650, 1);
    element.textContent = formatter.format(Math.floor(value * (1 - (1 - progress) ** 3)));
    if (progress < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

function renderSummary(summary) {
  animateNumber(document.querySelector("#accounts-analyzed"), summary.accounts_analyzed);
  animateNumber(document.querySelector("#suspected-mules"), summary.suspected_mules);
  document.querySelector("#suspicious-funds").textContent = `₹${(summary.suspicious_funds / 100000).toFixed(1)}L`;
  const minutes = Math.floor(summary.average_investigation_seconds / 60);
  const seconds = summary.average_investigation_seconds % 60;
  document.querySelector("#investigation-time").textContent = `${minutes}m ${seconds}s`;
}

function relativeTime(value) {
  const seconds = Math.max(1, Math.floor((Date.now() - new Date(value).getTime()) / 1000));
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes} min ago`;
  return `${Math.floor(minutes / 60)}h ago`;
}

function initials(name) {
  return name.split(" ").map((part) => part[0]).join("").slice(0, 2).toUpperCase();
}

function formatAmount(amount) {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(Number(amount));
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" })[character]);
}

function caseReference(transaction) {
  if (transaction.transaction_ref === "TXN-829104") return "MULE-2048";
  return `CASE-${transaction.transaction_ref.replace("TXN-", "")}`;
}

function renderTransactions() {
  const filtered = state.transactions.filter((transaction) => {
    const riskMatches = state.risk === "all" || transaction.risk_level === state.risk;
    const haystack = `${transaction.transaction_ref} ${transaction.customer_name} ${transaction.customer_ref}`.toLowerCase();
    return riskMatches && haystack.includes(state.query.toLowerCase());
  });
  transactionBody.innerHTML = filtered.map((transaction) => `
    <tr data-risk="${escapeHtml(transaction.risk_level)}">
      <td><b>${escapeHtml(transaction.transaction_ref)}</b><small>${escapeHtml(transaction.route)}</small></td>
      <td><span class="person"><i>${initials(transaction.customer_name)}</i><span><b>${escapeHtml(transaction.customer_name)}</b><small>${escapeHtml(transaction.customer_ref)}</small></span></span></td>
      <td><b>${formatAmount(transaction.amount)}</b><small>${escapeHtml(transaction.transaction_type)}</small></td>
      <td><mark class="${escapeHtml(transaction.risk_level)}">${transaction.risk_score}</mark><b>${escapeHtml(transaction.risk_level[0].toUpperCase() + transaction.risk_level.slice(1))}</b></td>
      <td><b>◈ ${escapeHtml(transaction.primary_signal)}</b><small>${escapeHtml(transaction.signal_detail)}</small></td>
      <td>${escapeHtml(transaction.channel)}</td>
      <td><b>${relativeTime(transaction.occurred_at)}</b><small>${new Date(transaction.occurred_at).toLocaleTimeString("en-IN")}</small></td>
      <td><button class="review" data-transaction="${escapeHtml(transaction.transaction_ref)}">Review →</button></td>
    </tr>`).join("");
  document.querySelector("#empty").hidden = filtered.length > 0;
  document.querySelector("#queue-count").textContent = `Showing ${filtered.length} of ${state.transactions.length} priority cases`;
  transactionBody.querySelectorAll(".review").forEach((button) => button.addEventListener("click", () => openCase(button.dataset.transaction)));
}

document.querySelector("#search").addEventListener("input", (event) => {
  state.query = event.target.value;
  renderTransactions();
});
document.querySelector("#filter").addEventListener("click", () => {
  const chips = document.querySelector("#chips");
  chips.hidden = !chips.hidden;
});
document.querySelectorAll("#chips button").forEach((button) => button.addEventListener("click", () => {
  state.risk = button.dataset.risk;
  document.querySelectorAll("#chips button").forEach((item) => item.classList.toggle("active", item === button));
  renderTransactions();
}));

const detail = {
  type: document.querySelector("#detail-type"), score: document.querySelector("#detail-score"),
  name: document.querySelector("#detail-name"), id: document.querySelector("#detail-id"),
  summary: document.querySelector("#detail-summary"), signal: document.querySelector("#detail-signal"),
  value: document.querySelector("#detail-value"),
};

function selectEntity(node) {
  document.querySelectorAll(".entity-node").forEach((item) => item.classList.toggle("active", item === node));
  detail.type.textContent = node.dataset.type;
  detail.score.textContent = `${node.dataset.score} risk`;
  detail.name.textContent = node.dataset.name;
  detail.id.textContent = node.dataset.id;
  detail.summary.textContent = node.dataset.summary;
  detail.signal.textContent = node.dataset.signal;
  detail.value.textContent = node.dataset.value;
}

function renderNetwork(network) {
  state.network = network;
  network.nodes.forEach((entity) => {
    const node = document.querySelector(`.entity-node[data-id="${CSS.escape(entity.id)}"]`);
    if (!node) return;
    Object.assign(node.dataset, {
      type: entity.type, name: entity.name, score: entity.score, summary: entity.summary,
      signal: entity.signal, value: entity.value,
    });
    node.querySelector("b").textContent = entity.label;
    node.querySelector("small").textContent = entity.role;
  });
  document.querySelector("#trace-status").textContent = `Graph source: ${network.source}`;
}

document.querySelectorAll(".entity-node").forEach((node) => node.addEventListener("click", () => selectEntity(node)));

const traceButton = document.querySelector("#trace-funds");
const networkCanvas = document.querySelector(".network-canvas");
traceButton.addEventListener("click", () => {
  const trace = state.network?.trace || { amount: 594000, destination: "Orion Exports", duration_minutes: 18, entity_count: 7 };
  networkCanvas.classList.remove("tracing");
  void networkCanvas.offsetWidth;
  networkCanvas.classList.add("tracing");
  traceButton.disabled = true;
  traceButton.textContent = "Tracing…";
  document.querySelector("#trace-status").textContent = `Following ${formatAmount(trace.amount)} to ${trace.destination}`;
  window.setTimeout(() => {
    traceButton.disabled = false;
    traceButton.textContent = "Trace again";
    document.querySelector("#trace-status").textContent = `Path completed in ${trace.duration_minutes} minutes · ${trace.entity_count} linked entities`;
  }, 2200);
});

function openCase(transactionRef) {
  const transaction = state.transactions.find((item) => item.transaction_ref === transactionRef);
  if (!transaction) return;
  document.querySelector("#case-content").innerHTML = `
    <h2>${escapeHtml(transaction.transaction_ref)}</h2>
    <p class="case-meta">${escapeHtml(transaction.customer_name)} · ${escapeHtml(transaction.customer_ref)}</p>
    <div class="case-amount">${formatAmount(transaction.amount)}</div>
    <div class="facts"><div><span>Risk score</span><b>${transaction.risk_score} / 100</b></div><div><span>Primary signal</span><b>${escapeHtml(transaction.primary_signal)}</b></div><div><span>Payment route</span><b>${escapeHtml(transaction.route)}</b></div><div><span>Channel</span><b>${escapeHtml(transaction.channel)}</b></div></div>`;
  caseDialog.dataset.caseRef = caseReference(transaction);
  caseDialog.dataset.transactionRef = transaction.transaction_ref;
  document.querySelector("#decision-note").value = "";
  caseDialog.showModal();
}

caseDialog.querySelector(".close").addEventListener("click", () => caseDialog.close());
caseDialog.querySelector("form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const decision = event.submitter?.value;
  const note = document.querySelector("#decision-note").value.trim();
  if (!decision || note.length < 3) {
    showToast("Add a short analyst note before recording the decision.", true);
    return;
  }
  const buttons = caseDialog.querySelectorAll("form button");
  buttons.forEach((button) => { button.disabled = true; });
  try {
    await request(`/cases/${caseDialog.dataset.caseRef}/decisions`, { method: "POST", body: JSON.stringify({ decision, note }) });
    caseDialog.close();
    showToast(`${caseDialog.dataset.transactionRef} ${decision === "safe" ? "marked as safe" : "blocked and escalated"}. Audit event saved.`);
    await loadWorkspace();
  } catch (error) {
    showToast(error.message, true);
  } finally {
    buttons.forEach((button) => { button.disabled = false; });
  }
});

function renderAudit(events) {
  document.querySelector("#audit-events").innerHTML = events.slice(0, 2).map((event) => `
    <div class="decision ${event.action === "blocked" ? "blocked" : ""}"><i>${event.action === "blocked" ? "⊘" : "✓"}</i><span><b>${escapeHtml(event.entity_ref)} ${escapeHtml(event.action)}</b><small>${escapeHtml(event.actor)} · ${relativeTime(event.created_at)} · ${escapeHtml(event.detail)}</small></span></div>`).join("");
}

async function checkHealth() {
  try {
    const response = await fetch(`${API}/health`);
    if (!response.ok) throw new Error();
    const health = await response.json();
    const degraded = Object.values(health.dependencies).filter((value) => !["connected"].includes(value)).length;
    document.querySelector("#system-status").textContent = degraded ? "Core system operational" : "All systems operational";
    document.querySelector("#system-detail").textContent = degraded ? `${degraded} optional services using fallback` : "PostgreSQL · Neo4j · Redis · Kafka";
  } catch {
    document.querySelector("#system-status").textContent = "API unavailable";
    document.querySelector("#system-detail").textContent = "Start the backend to continue";
  }
}

async function loadWorkspace() {
  if (state.analyst) document.querySelector("#analyst-name").textContent = state.analyst.name;
  try {
    const [summary, transactions, network, audit] = await Promise.all([
      request("/dashboard/summary"), request("/transactions"), request("/investigations/MULE-2048/network"), request("/cases/audit/recent?limit=5"),
    ]);
    state.transactions = transactions;
    renderSummary(summary);
    renderTransactions();
    renderNetwork(network);
    renderAudit(audit);
  } catch (error) {
    showToast(error.message, true);
  }
}

async function bootstrap() {
  await checkHealth();
  if (!state.token) {
    loginDialog.showModal();
    return;
  }
  await loadWorkspace();
}

bootstrap();
