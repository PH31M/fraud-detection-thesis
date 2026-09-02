import pytest

from app.features import FEATURE_COLUMNS, engineer_features

# Two real rows from data/paysim.csv (rows 0 and 2), with the engineered
# columns computed by notebooks/02_feature_engineering.ipynb for the same
# rows. Used to confirm engineer_features() reproduces the notebook exactly.
PAYSIM_ROW_0 = {
    "step": 1,
    "type": "PAYMENT",
    "amount": 9839.64,
    "oldbalanceOrg": 170136.0,
    "newbalanceOrig": 160296.36,
    "oldbalanceDest": 0.0,
    "newbalanceDest": 0.0,
}
PAYSIM_ROW_0_EXPECTED = {
    "errorBalanceOrig": 0.0,
    "errorBalanceDest": 9839.64,
    "balance_change_orig": -0.057834,
    "balance_change_dest": 0.0,
}

PAYSIM_ROW_2 = {
    "step": 1,
    "type": "TRANSFER",
    "amount": 181.0,
    "oldbalanceOrg": 181.0,
    "newbalanceOrig": 0.0,
    "oldbalanceDest": 0.0,
    "newbalanceDest": 0.0,
}
PAYSIM_ROW_2_EXPECTED = {
    "errorBalanceOrig": 0.0,
    "errorBalanceDest": 181.0,
    "balance_change_orig": -1.0,
    "balance_change_dest": 0.0,
}


def test_column_order_matches_training_columns():
    features = engineer_features(PAYSIM_ROW_0)
    assert list(features.columns) == FEATURE_COLUMNS


def test_engineered_values_match_notebook_row_0():
    row = engineer_features(PAYSIM_ROW_0).iloc[0]
    for key, expected in PAYSIM_ROW_0_EXPECTED.items():
        assert row[key] == pytest.approx(expected, rel=1e-6, abs=1e-6)
    assert bool(row["type_PAYMENT"]) is True
    assert bool(row["type_TRANSFER"]) is False


def test_engineered_values_match_notebook_row_2():
    row = engineer_features(PAYSIM_ROW_2).iloc[0]
    for key, expected in PAYSIM_ROW_2_EXPECTED.items():
        assert row[key] == pytest.approx(expected, rel=1e-6, abs=1e-6)
    assert bool(row["type_TRANSFER"]) is True


def test_zero_old_balance_does_not_divide_by_zero():
    payload = {
        "step": 1,
        "type": "CASH_OUT",
        "amount": 100.0,
        "oldbalanceOrg": 0.0,
        "newbalanceOrig": 0.0,
        "oldbalanceDest": 0.0,
        "newbalanceDest": 0.0,
    }
    row = engineer_features(payload).iloc[0]
    assert row["balance_change_orig"] == 0.0
    assert row["balance_change_dest"] == 0.0
