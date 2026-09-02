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

const historyEntries = [];

function fillForm(preset) {
  for (const key of FORM_FIELDS) {
    document.getElementById(`field-${key}`).value = preset[key];
  }
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

async function loadStatusBar() {
  const dot = document.getElementById("health-dot");
  const text = document.getElementById("health-text");
  try {
    const response = await fetchWithTimeout("/health", {}, 4000);
    if (response.ok) {
      const body = await response.json();
      dot.className = "dot ok";
      text.textContent = `Service: ${body.status.toUpperCase()}`;
    } else {
      dot.className = "dot down";
      text.textContent = `Service: DOWN (HTTP ${response.status})`;
    }
  } catch (err) {
    dot.className = "dot down";
    text.textContent = "Service: DOWN (unreachable)";
  }

  const infoText = document.getElementById("model-info-text");
  try {
    const response = await fetchWithTimeout("/model-info", {}, 4000);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const info = await response.json();
    const m = info.metrics;
    infoText.textContent =
      `${info.model_version} · threshold=${info.threshold} · ` +
      `precision=${m.precision} recall=${m.recall} f1=${m.f1}`;
  } catch (err) {
    infoText.textContent = "Model info unavailable";
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
    `threshold_used = ${result.threshold_used}`;

  const fill = document.getElementById("prob-bar-fill");
  fill.style.width = formatProbability(result.fraud_probability);
  fill.className = `prob-bar-fill ${isFraud ? "fraud" : ""}`;

  document.getElementById("prob-bar-label").textContent =
    `fraud_probability = ${formatProbability(result.fraud_probability)} ` +
    `(${result.fraud_probability})`;

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
    name.textContent = feature.feature;
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
  loadStatusBar();

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
}

window.addEventListener("DOMContentLoaded", init);
