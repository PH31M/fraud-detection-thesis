import math


def test_empty_orig_account_from_the_start(client):
    """oldbalanceOrg == newbalanceOrig == 0: errorBalanceOrig must come out as
    a plain finite number (= amount), and balance_change_orig must use the
    notebook's zero-guard (divide by 1, not 0) instead of NaN/inf."""
    payload = {
        "step": 5,
        "type": "CASH_OUT",
        "amount": 500.0,
        "oldbalanceOrg": 0.0,
        "newbalanceOrig": 0.0,
        "oldbalanceDest": 1000.0,
        "newbalanceDest": 1500.0,
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert math.isfinite(body["fraud_probability"])
    assert 0.0 <= body["fraud_probability"] <= 1.0


def test_very_large_amount_does_not_crash(client):
    payload = {
        "step": 5,
        "type": "TRANSFER",
        "amount": 10_000_000.0,
        "oldbalanceOrg": 10_000_000.0,
        "newbalanceOrig": 0.0,
        "oldbalanceDest": 0.0,
        "newbalanceDest": 10_000_000.0,
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert math.isfinite(body["fraud_probability"])
    assert body["fraud_probability"] > 0.5


def test_payment_with_untracked_merchant_destination_balances(client):
    """PaySim does not track balances for PAYMENT destinations (merchants),
    so oldbalanceDest == newbalanceDest == 0 is the normal case for PAYMENT,
    not a data error. It must be scored normally, not rejected."""
    payload = {
        "step": 5,
        "type": "PAYMENT",
        "amount": 1000.0,
        "oldbalanceOrg": 2000.0,
        "newbalanceOrig": 1000.0,
        "oldbalanceDest": 0.0,
        "newbalanceDest": 0.0,
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert math.isfinite(body["fraud_probability"])


def test_non_transfer_cash_out_types_are_not_rejected(client):
    """Per the domain: fraud in PaySim only occurs in TRANSFER/CASH_OUT, but
    other types are still valid input and must be scored, not rejected."""
    for txn_type in ("CASH_IN", "DEBIT"):
        payload = {
            "step": 1,
            "type": txn_type,
            "amount": 100.0,
            "oldbalanceOrg": 1000.0,
            "newbalanceOrig": 900.0,
            "oldbalanceDest": 0.0,
            "newbalanceDest": 0.0,
        }
        response = client.post("/predict", json=payload)
        assert response.status_code == 200
