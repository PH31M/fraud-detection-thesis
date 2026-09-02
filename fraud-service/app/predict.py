import logging

import numpy as np

from app.config import SHAP_TOP_N, THRESHOLD
from app.features import engineer_features
from app.model_loader import ModelBundle

logger = logging.getLogger(__name__)


def predict_transaction(bundle: ModelBundle, raw_input: dict) -> dict:
    try:
        features = engineer_features(raw_input)
        fraud_probability = float(bundle.model.predict_proba(features)[0, 1])

        shap_values = np.asarray(bundle.explainer.shap_values(features))
        if shap_values.ndim == 3:
            shap_values = shap_values[:, :, -1]
        sample_shap = shap_values[0]

        ranked = sorted(
            zip(features.columns, sample_shap),
            key=lambda pair: abs(pair[1]),
            reverse=True,
        )
        top_features = [
            {"feature": name, "shap_value": float(value)}
            for name, value in ranked[:SHAP_TOP_N]
        ]

        return {
            "fraud_probability": fraud_probability,
            "is_fraud_flag": fraud_probability >= THRESHOLD,
            "threshold_used": THRESHOLD,
            "top_features": top_features,
        }
    except Exception:
        logger.exception("Prediction failed for input: %s", raw_input)
        raise
