def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_model_info_returns_expected_shape(client):
    response = client.get("/model-info")
    assert response.status_code == 200
    body = response.json()
    assert body["model_version"] == "xgb_smote_v2_64_16_20_val_split"
    assert body["threshold"] == 0.95
    assert set(body["metrics"]) == {"recall", "precision", "f1"}
