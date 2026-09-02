import logging

import joblib
import shap

from app.config import MODEL_PATH

logger = logging.getLogger(__name__)


class ModelBundle:
    """Holds the model and its SHAP explainer, loaded once at startup."""

    def __init__(self) -> None:
        self.model = None
        self.explainer = None

    def load(self) -> None:
        try:
            self.model = joblib.load(MODEL_PATH)
            self.explainer = shap.TreeExplainer(self.model)
        except Exception:
            logger.exception("Failed to load model from %s", MODEL_PATH)
            raise

    @property
    def is_ready(self) -> bool:
        return self.model is not None and self.explainer is not None


bundle = ModelBundle()
