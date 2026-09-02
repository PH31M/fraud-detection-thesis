# Fraud Detection Service

FastAPI wrapper around the `XGBoost + SMOTE` model trained in this repository's
notebooks (`notebooks/02_feature_engineering.ipynb` through
`notebooks/06_shap_cost_sensitive.ipynb`). Given a raw PaySim-style
transaction, it engineers the same features used at training time, scores it
with the trained model, and returns the fraud probability plus the top SHAP
contributors.

## Model provenance

- Model file: `models/xgb_smote_model_v2_64_16_20_val_split.pkl`, copied
  verbatim from `results/xgb_smote_model_v2_64_16_20_val_split.pkl`
  (`XGBoost + SMOTE`, chosen over the plain model for its higher recall and
  because the SHAP analysis in the thesis was done on this model).
- Trained on PaySim v1, stratified 64:16:20 train:validation:test split,
  `random_state=42` (`data/processed_split.pkl`).
- Classification threshold: **0.95**, selected on the validation split by
  minimizing cost = `FP × 1 + FN × 50`
  (`results/cost_sensitive_selected_thresholds_v2_64_16_20_val_split.csv`).
  Test-set confirmation at this threshold: `tn=1,270,877 fp=4 fn=4 tp=1,639`
  → precision = recall = f1 = 1639/1643 ≈ **0.997565**
  (`results/cost_sensitive_test_final_v2_64_16_20_val_split.csv`).
- **No scaler is applied before prediction.** `data/processed_split.pkl`
  contains a `StandardScaler`, but `notebooks/05_extension_smote_xgboost.ipynb`
  trains `xgb_smote` directly on the *unscaled* `X_train` DataFrame — the
  scaler is only used for the Logistic Regression / KNN baselines in
  `notebooks/04_baseline_models.ipynb`. The SHAP explainer in
  `notebooks/06_shap_cost_sensitive.ipynb` is likewise built on the unscaled
  model. This service reproduces that exactly: engineered features go
  straight into the model, unscaled. (This is a deliberate deviation from an
  earlier draft plan that assumed scaling was required — the notebooks are
  the source of truth.)

## Feature engineering

`app/features.py` reproduces `notebooks/02_feature_engineering.ipynb` exactly:

```
errorBalanceOrig    = newbalanceOrig + amount - oldbalanceOrg
errorBalanceDest    = oldbalanceDest + amount - newbalanceDest
balance_change_orig = (newbalanceOrig - oldbalanceOrg) / oldbalanceOrg   (oldbalanceOrg replaced by 1 if 0)
balance_change_dest = (newbalanceDest - oldbalanceDest) / oldbalanceDest (oldbalanceDest replaced by 1 if 0)
type                 -> one-hot: type_CASH_IN, type_CASH_OUT, type_DEBIT, type_PAYMENT, type_TRANSFER
```

Column order matches the model's trained feature order exactly (`step,
amount, oldbalanceOrg, newbalanceOrig, oldbalanceDest, newbalanceDest,
errorBalanceOrig, errorBalanceDest, balance_change_orig, balance_change_dest,
type_CASH_IN, type_CASH_OUT, type_DEBIT, type_PAYMENT, type_TRANSFER`).

Non-TRANSFER/CASH_OUT transaction types are valid input and are still scored
normally — PaySim fraud only occurs in those two types, so other types will
score near-zero, which is expected model behavior, not an error.

## Running locally

From the `fraud-service/` directory, using the repo's existing virtualenv
(`../.venv`) or a fresh one:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for the interactive Swagger UI, or
`http://127.0.0.1:8000/` for the visual test page described below.

## Running the tests

```bash
pytest -v
```

`tests/test_features.py` checks `engineer_features()` against two real
PaySim rows and the values the notebook computed for them. `tests/test_*`
cover `/health`, `/model-info`, valid `/predict` responses (including a
regression-pinned fraud case and a domain edge-case suite), and invalid input
handling (422s).

## Visual test page (`/`)

Vanilla HTML/CSS/JS page in `static/`, served by the same FastAPI app via
`StaticFiles` (mounted last in `app/main.py` so it can't shadow the API
routes — confirmed by re-running the full pytest suite after adding the
mount). Open `http://127.0.0.1:8000/` after starting the server. It is a
manual-testing/demo aid on top of the API, not a replacement for the pytest
suite in `tests/`.

- **Status bar**: calls `/health` and `/model-info` on load; a red dot with
  "DOWN (unreachable)" appears (bounded by a client-side fetch timeout, no
  infinite spinner) if the API can't be reached. Metrics/threshold shown here
  are always read live from `/model-info`, never hardcoded in the page.
- **Preset buttons**: "🔴 Fraud rõ ràng", "🟢 Normal rõ ràng", "🟡 Case biên"
  fill the form with the same three cases used for manual Swagger testing;
  "⚠️ Gửi request lỗi (test 422)" fills an invalid `amount = -100` so the
  validation error path can be demoed without typing it by hand. None of the
  presets auto-submit.
- **Result panel**: probability progress bar (red/green by `is_fraud_flag`),
  a FRAUD/NOT FRAUD badge, `threshold_used`, and a CSS-only horizontal bar
  chart of the top SHAP features (red bar = pushes toward fraud, green =
  pushes toward normal). A 422 response renders a red box listing each field
  error message instead of raw JSON.
- **History table**: every successful `/predict` call is appended to an
  in-memory (not persisted) table for comparing consecutive test runs during
  a demo.

Manually verified end-to-end in a live browser session: fresh-load status
bar, all three presets, the 422 error preset, `oldbalanceOrg = 0` edge case,
API-down state (red dot, no hang), history accumulation across requests, and
the layout at a 375px mobile width.

## API

### `GET /health`
`{"status": "ok"}` — reports whether the model loaded at startup, does not
reload it per request.

### `GET /model-info`
Model version, training description, confirmed test-set metrics at the
production threshold, and the threshold itself.

### `POST /predict`

Request body:

```json
{
  "step": 1,
  "type": "TRANSFER",
  "amount": 181.0,
  "oldbalanceOrg": 181.0,
  "newbalanceOrig": 0.0,
  "oldbalanceDest": 0.0,
  "newbalanceDest": 0.0
}
```

Response:

```json
{
  "fraud_probability": 0.9999634027481079,
  "is_fraud_flag": true,
  "threshold_used": 0.95,
  "top_features": [
    {"feature": "errorBalanceOrig", "shap_value": 7.979918956756592},
    {"feature": "newbalanceOrig", "shap_value": 2.3437013626098633},
    {"feature": "type_TRANSFER", "shap_value": 1.1824629306793213},
    {"feature": "type_CASH_OUT", "shap_value": -0.6582282781600952},
    {"feature": "errorBalanceDest", "shap_value": -0.3240009844303131}
  ],
  "model_version": "xgb_smote_v2_64_16_20_val_split"
}
```

`type` must be one of `TRANSFER`, `CASH_OUT`, `PAYMENT`, `CASH_IN`, `DEBIT`.
`amount` must be `> 0`; the four balance fields must be `>= 0`; `step` must be
`>= 0`. Any violation returns `422` with Pydantic's validation detail. A
prediction-time failure (unexpected exception in feature engineering or
inference) returns `500`.

## Not yet done

PostgreSQL, Docker, and RabbitMQ integration are out of scope for this
service and are planned for later weeks per the original brief.
