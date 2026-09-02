import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


FRAUD_LIKE_TRANSACTION = {
    "step": 1,
    "type": "TRANSFER",
    "amount": 181.0,
    "oldbalanceOrg": 181.0,
    "newbalanceOrig": 0.0,
    "oldbalanceDest": 0.0,
    "newbalanceDest": 0.0,
}

NORMAL_TRANSACTION = {
    "step": 10,
    "type": "PAYMENT",
    "amount": 25.5,
    "oldbalanceOrg": 5000.0,
    "newbalanceOrig": 4974.5,
    "oldbalanceDest": 0.0,
    "newbalanceDest": 0.0,
}
