from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
SERVICE_ROOT = APP_DIR.parent
MODELS_DIR = SERVICE_ROOT / "models"

MODEL_PATH = MODELS_DIR / "xgb_smote_model_v2_64_16_20_val_split.pkl"

# Matches results/xgb_provenance_v2_64_16_20_val_split.json — the artifact this
# service was packaged from. Bump this if the model file is ever replaced.
MODEL_VERSION = "xgb_smote_v2_64_16_20_val_split"
TRAINED_ON = "PaySim v1, stratified 64:16:20 (train:val:test) split, random_state=42"

# Selected on the validation split by minimizing cost = FP*1 + FN*50
# (results/cost_sensitive_selected_thresholds_v2_64_16_20_val_split.csv).
# Metrics below are the one-time confirmation run on the held-out test split
# (results/cost_sensitive_test_final_v2_64_16_20_val_split.csv): tn=1270877,
# fp=4, fn=4, tp=1639 -> precision = recall = f1 = 1639 / 1643.
THRESHOLD = 0.95
METRICS = {
    "recall": 0.997565,
    "precision": 0.997565,
    "f1": 0.997565,
}

SHAP_TOP_N = 5
