import pandas as pd

TRANSACTION_TYPES = ["CASH_IN", "CASH_OUT", "DEBIT", "PAYMENT", "TRANSFER"]

# Exact order the model was trained on (see notebooks/03_prepare_dataset.ipynb,
# X = df.drop(columns=['isFraud', 'isFlaggedFraud'])). XGBoost validates
# feature names against this on predict, so order/names must match exactly.
FEATURE_COLUMNS = [
    "step",
    "amount",
    "oldbalanceOrg",
    "newbalanceOrig",
    "oldbalanceDest",
    "newbalanceDest",
    "errorBalanceOrig",
    "errorBalanceDest",
    "balance_change_orig",
    "balance_change_dest",
    *[f"type_{t}" for t in TRANSACTION_TYPES],
]


def engineer_features(raw_input: dict) -> pd.DataFrame:
    """Reproduce the feature engineering from notebooks/02_feature_engineering.ipynb.

    Formulas must match the notebook exactly:
    - errorBalanceOrig = newbalanceOrig + amount - oldbalanceOrg
    - errorBalanceDest = oldbalanceDest + amount - newbalanceDest
    - balance_change_orig = (newbalanceOrig - oldbalanceOrg) / oldbalanceOrg,
      with oldbalanceOrg replaced by 1 when it is 0 (notebook uses
      .replace(0, 1) to avoid division by zero — same as pandas' behavior).
    - balance_change_dest = the same ratio for the destination account.
    - type is one-hot encoded into type_CASH_IN/CASH_OUT/DEBIT/PAYMENT/TRANSFER,
      matching pd.get_dummies(df, columns=['type'], prefix='type').
    """
    amount = raw_input["amount"]
    old_orig = raw_input["oldbalanceOrg"]
    new_orig = raw_input["newbalanceOrig"]
    old_dest = raw_input["oldbalanceDest"]
    new_dest = raw_input["newbalanceDest"]
    txn_type = raw_input["type"]

    row = {
        "step": raw_input["step"],
        "amount": amount,
        "oldbalanceOrg": old_orig,
        "newbalanceOrig": new_orig,
        "oldbalanceDest": old_dest,
        "newbalanceDest": new_dest,
        "errorBalanceOrig": new_orig + amount - old_orig,
        "errorBalanceDest": old_dest + amount - new_dest,
        "balance_change_orig": (new_orig - old_orig) / (old_orig if old_orig != 0 else 1),
        "balance_change_dest": (new_dest - old_dest) / (old_dest if old_dest != 0 else 1),
    }
    for t in TRANSACTION_TYPES:
        row[f"type_{t}"] = txn_type == t

    return pd.DataFrame([row], columns=FEATURE_COLUMNS)
