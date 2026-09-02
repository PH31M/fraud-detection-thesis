import pytest

from tests.conftest import NORMAL_TRANSACTION


def _payload(**overrides):
    payload = dict(NORMAL_TRANSACTION)
    payload.update(overrides)
    return payload


def _drop(*keys):
    payload = dict(NORMAL_TRANSACTION)
    for key in keys:
        payload.pop(key)
    return payload


INVALID_CASES = [
    pytest.param(_drop("amount"), id="missing_amount"),
    pytest.param(_drop("type"), id="missing_type"),
    pytest.param(_payload(amount="not-a-number"), id="amount_wrong_type"),
    pytest.param(_payload(type="NOT_A_TYPE"), id="type_outside_enum"),
    pytest.param(_payload(amount=-100), id="amount_negative"),
    pytest.param(_payload(amount=0), id="amount_zero"),
    pytest.param(_payload(oldbalanceOrg=-1), id="oldbalanceOrg_negative"),
    pytest.param(_payload(step=-1), id="step_negative"),
]


@pytest.mark.parametrize("payload", INVALID_CASES)
def test_invalid_input_returns_422(client, payload):
    response = client.post("/predict", json=payload)
    assert response.status_code == 422
