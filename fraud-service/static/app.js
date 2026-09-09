const PRESETS = {
  fraud: {
    step: 1,
    type: "TRANSFER",
    amount: 181000.0,
    oldbalanceOrg: 181000.0,
    newbalanceOrig: 0.0,
    oldbalanceDest: 0.0,
    newbalanceDest: 0.0,
  },
  normal: {
    step: 10,
    type: "PAYMENT",
    amount: 25.5,
    oldbalanceOrg: 5000.0,
    newbalanceOrig: 4974.5,
    oldbalanceDest: 0.0,
    newbalanceDest: 0.0,
  },
  edge: {
    step: 5,
    type: "CASH_OUT",
    amount: 500.0,
    oldbalanceOrg: 0.0,
    newbalanceOrig: 0.0,
    oldbalanceDest: 1000.0,
    newbalanceDest: 1500.0,
  },
  error: {
    step: 10,
    type: "PAYMENT",
    amount: -100,
    oldbalanceOrg: 5000.0,
    newbalanceOrig: 4900.0,
    oldbalanceDest: 0.0,
    newbalanceDest: 0.0,
  },
};

const FORM_FIELDS = [
  "step",
  "type",
  "amount",
  "oldbalanceOrg",
  "newbalanceOrig",
  "oldbalanceDest",
  "newbalanceDest",
];

const AMOUNT_LABELS = {
  TRANSFER: "Số tiền muốn chuyển",
  CASH_OUT: "Số tiền muốn rút",
  PAYMENT: "Số tiền thanh toán",
  CASH_IN: "Số tiền muốn nạp",
  DEBIT: "Số tiền bị ghi nợ",
};

const FEATURE_LABELS = {
  step: "Thời điểm",
  amount: "Số tiền",
  oldbalanceOrg: "Số dư gửi (trước)",
  newbalanceOrig: "Số dư gửi (sau)",
  oldbalanceDest: "Số dư nhận (trước)",
  newbalanceDest: "Số dư nhận (sau)",
  errorBalanceOrig: "Lệch số dư gửi",
  errorBalanceDest: "Lệch số dư nhận",
  balance_change_orig: "%Δ số dư gửi",
  balance_change_dest: "%Δ số dư nhận",
  type_TRANSFER: "Là Chuyển tiền?",
  type_CASH_OUT: "Là Rút tiền?",
  type_PAYMENT: "Là Thanh toán?",
  type_CASH_IN: "Là Nạp tiền?",
  type_DEBIT: "Là Ghi nợ?",
};

// Chỉ 3 loại này đã được đối chiếu khớp công thức errorBalanceOrig/errorBalanceDest
// trong app/features.py (xem "Claude outputs/thiet-ke-lai-giao-dien-test.md", mục 7.1).
const AUTO_SYNC_SUPPORTED_TYPES = ["TRANSFER", "CASH_OUT", "PAYMENT"];

const historyEntries = [];

const balanceSync = {
  origState: "auto", // "auto" | "manual"
  destState: "auto",
  suppressEvents: false,
};

function fillForm(preset) {
  for (const key of FORM_FIELDS) {
    document.getElementById(`field-${key}`).value = preset[key];
  }
  updateAmountLabel();
  evaluateBalanceSyncState();
  refreshBalanceSync();
}

function translateFeatureName(name) {
  return FEATURE_LABELS[name] || name;
}

function updateAmountLabel() {
  const type = document.getElementById("field-type").value;
  document.getElementById("amount-label").textContent =
    AMOUNT_LABELS[type] || "Số tiền giao dịch";
}

function round2(n) {
  return Math.round(n * 100) / 100;
}

function computeAutoOrig(oldOrig, amount) {
  return round2(oldOrig - amount);
}

function computeAutoDest(oldDest, amount, type) {
  if (type === "PAYMENT") return round2(oldDest);
  return round2(oldDest + amount);
}

function readBalanceInputs() {
  return {
    type: document.getElementById("field-type").value,
    amount: Number(document.getElementById("field-amount").value) || 0,
    oldOrig: Number(document.getElementById("field-oldbalanceOrg").value) || 0,
    oldDest: Number(document.getElementById("field-oldbalanceDest").value) || 0,
  };
}

function evaluateBalanceSyncState() {
  const { type, amount, oldOrig, oldDest } = readBalanceInputs();
  const supported = AUTO_SYNC_SUPPORTED_TYPES.includes(type);
  if (!supported) {
    balanceSync.origState = "manual";
    balanceSync.destState = "manual";
    return;
  }
  const curOrig = Number(document.getElementById("field-newbalanceOrig").value) || 0;
  const curDest = Number(document.getElementById("field-newbalanceDest").value) || 0;
  const expectedOrig = computeAutoOrig(oldOrig, amount);
  const expectedDest = computeAutoDest(oldDest, amount, type);
  balanceSync.origState = Math.abs(curOrig - expectedOrig) < 0.005 ? "auto" : "manual";
  balanceSync.destState = Math.abs(curDest - expectedDest) < 0.005 ? "auto" : "manual";
}

function setFieldValueProgrammatically(id, value) {
  balanceSync.suppressEvents = true;
  document.getElementById(id).value = value;
  balanceSync.suppressEvents = false;
}

function updateBalanceField(kind) {
  const isOrig = kind === "orig";
  const inputId = isOrig ? "field-newbalanceOrig" : "field-newbalanceDest";
  const wrapId = isOrig ? "orig-balance-field" : "dest-balance-field";
  const badge = document.getElementById(isOrig ? "orig-sync-badge" : "dest-sync-badge");
  const wrap = document.getElementById(wrapId);
  const state = isOrig ? balanceSync.origState : balanceSync.destState;

  const { type, amount, oldOrig, oldDest } = readBalanceInputs();
  const supported = AUTO_SYNC_SUPPORTED_TYPES.includes(type);
  const autoSyncOn = document.getElementById("auto-sync-toggle").checked;

  wrap.classList.remove("sync-auto", "sync-manual");

  if (!autoSyncOn) {
    badge.innerHTML = "";
    return;
  }

  if (!supported) {
    badge.innerHTML =
      "⚠️ Loại giao dịch này chưa kiểm chứng công thức số dư — vui lòng tự nhập tay.";
    return;
  }

  const expected = isOrig
    ? computeAutoOrig(oldOrig, amount)
    : computeAutoDest(oldDest, amount, type);

  if (state === "auto") {
    setFieldValueProgrammatically(inputId, expected);
    wrap.classList.add("sync-auto");
    const note =
      !isOrig && type === "PAYMENT"
        ? "✓ Tự động tính — giữ nguyên, bình thường với Thanh toán"
        : "✓ Tự động tính — khớp công thức hợp lệ";
    badge.innerHTML = note;
  } else {
    const actual = Number(document.getElementById(inputId).value) || 0;
    const diff = round2(actual - expected);
    wrap.classList.add("sync-manual");
    badge.innerHTML =
      `✎ Đã sửa tay — lệch ${diff} so với giá trị hợp lệ ` +
      `<button type="button" class="reset-balance-btn" data-target="${kind}">↺ Đặt lại giá trị hợp lệ</button>`;
  }
}

function refreshBalanceSync() {
  updateBalanceField("orig");
  updateBalanceField("dest");
}

async function fetchWithTimeout(url, options, timeoutMs = 4000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } finally {
    clearTimeout(timer);
  }
}

function formatProbability(p) {
  return `${(p * 100).toFixed(2)}%`;
}

function renderResult(result) {
  document.getElementById("result-error").classList.add("hidden");
  document.getElementById("result-empty").classList.add("hidden");
  const content = document.getElementById("result-content");
  content.classList.remove("hidden");

  const isFraud = result.is_fraud_flag;

  const badge = document.getElementById("flag-badge");
  badge.textContent = isFraud ? "FRAUD" : "NOT FRAUD";
  badge.className = `badge ${isFraud ? "fraud" : "normal"}`;

  document.getElementById("threshold-note").textContent =
    `Hệ thống gắn cờ gian lận khi độ tin cậy ≥ ${formatProbability(result.threshold_used)}.`;

  const fill = document.getElementById("prob-bar-fill");
  fill.style.width = formatProbability(result.fraud_probability);
  fill.className = `prob-bar-fill ${isFraud ? "fraud" : ""}`;

  document.getElementById("prob-bar-label").textContent =
    `Mô hình đánh giá ${formatProbability(result.fraud_probability)} khả năng đây là giao dịch gian lận.`;

  const chart = document.getElementById("shap-chart");
  chart.innerHTML = "";
  const maxAbs = Math.max(
    ...result.top_features.map((f) => Math.abs(f.shap_value)),
    1e-9
  );
  for (const feature of result.top_features) {
    const row = document.createElement("div");
    row.className = "shap-row";

    const name = document.createElement("div");
    name.className = "shap-feature-name";
    name.textContent = translateFeatureName(feature.feature);
    name.title = feature.feature;

    const track = document.createElement("div");
    track.className = "shap-bar-track";
    const barFill = document.createElement("div");
    const isPositive = feature.shap_value >= 0;
    barFill.className = `shap-bar-fill ${isPositive ? "positive" : "negative"}`;
    const widthPct = (Math.abs(feature.shap_value) / maxAbs) * 50;
    barFill.style.width = `${widthPct}%`;
    track.appendChild(barFill);

    const value = document.createElement("div");
    value.className = "shap-value";
    value.textContent = feature.shap_value.toFixed(3);

    row.appendChild(name);
    row.appendChild(track);
    row.appendChild(value);
    chart.appendChild(row);
  }
}

function renderErrorBox(title, messages) {
  document.getElementById("result-empty").classList.add("hidden");
  document.getElementById("result-content").classList.add("hidden");
  const box = document.getElementById("result-error");
  box.classList.remove("hidden");

  let html = `<strong>${title}</strong>`;
  if (messages && messages.length) {
    html += "<ul>" + messages.map((m) => `<li>${m}</li>`).join("") + "</ul>";
  }
  box.innerHTML = html;
}

function addHistoryRow(payload, result) {
  const emptyRow = document.getElementById("history-empty-row");
  if (emptyRow) emptyRow.remove();

  historyEntries.push({ payload, result, time: new Date() });

  const tbody = document.getElementById("history-body");
  const tr = document.createElement("tr");
  tr.className = result.is_fraud_flag ? "flag-true" : "flag-false";

  const cells = [
    new Date().toLocaleTimeString("vi-VN"),
    payload.type,
    payload.amount,
    formatProbability(result.fraud_probability),
    result.is_fraud_flag ? "FRAUD" : "NOT FRAUD",
  ];
  for (const value of cells) {
    const td = document.createElement("td");
    td.textContent = value;
    tr.appendChild(td);
  }
  tbody.prepend(tr);
}

function buildPayload() {
  return {
    step: Number(document.getElementById("field-step").value),
    type: document.getElementById("field-type").value,
    amount: Number(document.getElementById("field-amount").value),
    oldbalanceOrg: Number(document.getElementById("field-oldbalanceOrg").value),
    newbalanceOrig: Number(document.getElementById("field-newbalanceOrig").value),
    oldbalanceDest: Number(document.getElementById("field-oldbalanceDest").value),
    newbalanceDest: Number(document.getElementById("field-newbalanceDest").value),
  };
}

async function submitPrediction(event) {
  event.preventDefault();
  const submitBtn = document.getElementById("submit-btn");
  submitBtn.disabled = true;

  const payload = buildPayload();

  try {
    const response = await fetchWithTimeout(
      "/predict",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      },
      8000
    );

    if (response.status === 200) {
      const result = await response.json();
      renderResult(result);
      addHistoryRow(payload, result);
    } else if (response.status === 422) {
      const body = await response.json();
      const messages = (body.detail || []).map((d) => {
        const field = Array.isArray(d.loc) ? d.loc[d.loc.length - 1] : "field";
        return `${field}: ${d.msg}`;
      });
      renderErrorBox("Validation error (422)", messages);
    } else {
      renderErrorBox(`Service error (HTTP ${response.status})`, [
        "Xem console để biết chi tiết.",
      ]);
      console.error("Predict failed", response.status, await response.text());
    }
  } catch (err) {
    renderErrorBox("Service error, xem console", [String(err)]);
    console.error("Predict request failed", err);
  } finally {
    submitBtn.disabled = false;
  }
}

function init() {
  document.getElementById("preset-fraud").addEventListener("click", () =>
    fillForm(PRESETS.fraud)
  );
  document.getElementById("preset-normal").addEventListener("click", () =>
    fillForm(PRESETS.normal)
  );
  document.getElementById("preset-edge").addEventListener("click", () =>
    fillForm(PRESETS.edge)
  );
  document.getElementById("preset-error").addEventListener("click", () =>
    fillForm(PRESETS.error)
  );

  document
    .getElementById("predict-form")
    .addEventListener("submit", submitPrediction);

  document.getElementById("field-type").addEventListener("change", () => {
    updateAmountLabel();
    refreshBalanceSync();
  });

  for (const id of ["field-amount", "field-oldbalanceOrg", "field-oldbalanceDest"]) {
    document.getElementById(id).addEventListener("input", refreshBalanceSync);
  }

  document.getElementById("field-newbalanceOrig").addEventListener("input", () => {
    if (balanceSync.suppressEvents) return;
    balanceSync.origState = "manual";
    updateBalanceField("orig");
  });
  document.getElementById("field-newbalanceDest").addEventListener("input", () => {
    if (balanceSync.suppressEvents) return;
    balanceSync.destState = "manual";
    updateBalanceField("dest");
  });

  document.getElementById("auto-sync-toggle").addEventListener("change", refreshBalanceSync);

  document.querySelector(".balance-groups").addEventListener("click", (event) => {
    const btn = event.target.closest(".reset-balance-btn");
    if (!btn) return;
    const kind = btn.dataset.target;
    if (kind === "orig") balanceSync.origState = "auto";
    if (kind === "dest") balanceSync.destState = "auto";
    updateBalanceField(kind);
  });

  updateAmountLabel();
  evaluateBalanceSyncState();
  refreshBalanceSync();
}

window.addEventListener("DOMContentLoaded", init);
