# fraud-detection-thesis

Notebook run order:

1. `notebooks/01_eda.ipynb`
2. `notebooks/02_feature_engineering.ipynb`
3. `notebooks/03_prepare_dataset.ipynb`
4. `notebooks/04_extension_smote_xgboost.ipynb`

Current notebook artifacts:

- `01_eda.ipynb` reads `data/paysim.csv`
- `02_feature_engineering.ipynb` reads `data/paysim.csv` and writes `data/engineered_features.pkl`
- `03_prepare_dataset.ipynb` reads `data/engineered_features.pkl` and writes `data/processed_split.pkl`
- `04_extension_smote_xgboost.ipynb` is reserved for extension experiments built on `data/processed_split.pkl`

Why this matters:

- Notebook numbering now matches the real execution order.
- `02_feature_engineering.ipynb` and `03_prepare_dataset.ipynb` no longer depend on variables left in memory from earlier notebooks.
- If an upstream artifact is missing, the downstream notebook now fails with a clear message telling you which notebook to run first.
- Older LR/KNN baseline work is archived under `notebooks/_archive/` so it does not confuse the main thesis scope during review.
