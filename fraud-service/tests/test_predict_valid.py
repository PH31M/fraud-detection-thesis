from tests.conftest import FRAUD_LIKE_TRANSACTION, NORMAL_TRANSACTION

REQUIRED_FIELDS = {
    "fraud_probability",
    "is_fraud_flag",
    "threshold_used",
    "top_features",
    "model_version",
}


def test_response_has_required_fields(client):
    response = client.post("/predict", json=NORMAL_TRANSACTION)
    assert response.status_code == 200
    assert REQUIRED_FIELDS.issubset(response.json().keys())


def test_fraud_probability_in_unit_interval(client):
    for payload in (FRAUD_LIKE_TRANSACTION, NORMAL_TRANSACTION):
        body = client.post("/predict", json=payload).json()
        assert 0.0 <= body["fraud_probability"] <= 1.0


def test_top_features_shape(client):
    body = client.post("/predict", json=FRAUD_LIKE_TRANSACTION).json()
    top_features = body["top_features"]
    assert 3 <= len(top_features) <= 5
    for entry in top_features:
        assert set(entry.keys()) == {"feature", "shap_value"}
        assert isinstance(entry["feature"], str)
        assert isinstance(entry["shap_value"], float)


def test_threshold_used_matches_configured_threshold(client):
    body = client.post("/predict", json=NORMAL_TRANSACTION).json()
    assert body["threshold_used"] == 0.95


def test_known_fraud_case_regression(client):
    """Regression test pinned against results/xgb_provenance_v2_64_16_20_val_split.json
    and a manual replay of the trained pipeline (see conversation history / model
    build notes). If the packaged model is ever swapped without updating this
    test, a materially different score here is the signal to investigate."""
    body = client.post("/predict", json=FRAUD_LIKE_TRANSACTION).json()
    assert body["fraud_probability"] > 0.99
    assert body["is_fraud_flag"] is True
    assert body["top_features"][0]["feature"] == "errorBalanceOrig"


def test_normal_payment_case_scores_low(client):
    body = client.post("/predict", json=NORMAL_TRANSACTION).json()
    assert body["fraud_probability"] < 0.5
    assert body["is_fraud_flag"] is False
