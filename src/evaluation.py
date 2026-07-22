"""
Hàm dùng chung để đánh giá và tổng hợp kết quả các model fraud detection.
Dùng lại cho toàn bộ đồ án: baseline (LR/KNN/DT/RF), XGBoost+SMOTE, v.v.
"""
import pandas as pd  # FIX: thiếu import này ở bản gốc -> gây NameError khi gọi print_metrics_table
import time
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, confusion_matrix
)


def evaluate_model(model, X_test, y_test, model_name, train_time=None):
    """Đánh giá model đã fit và trả về dict metrics, khớp format với anchor paper.

    Args:
        model: model đã được .fit() trước đó (bắt buộc phải fitted).
        X_test, y_test: tập test dùng để đánh giá.
        model_name: tên hiển thị trong bảng kết quả (VD: 'Logistic Regression').
        train_time: thời gian train (giây), truyền vào từ ngoài để ghi log.

    Returns:
        dict chứa các metrics: accuracy, precision, recall, f1, roc_auc,
        train_time_sec, predict_time_sec.
    """
    start = time.time()
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    predict_time = time.time() - start

    results = {
        'model': model_name,
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred),
        'recall': recall_score(y_test, y_pred),
        'f1': f1_score(y_test, y_pred),
        'roc_auc': roc_auc_score(y_test, y_proba),
        'train_time_sec': round(train_time, 3) if train_time is not None else None,
        'predict_time_sec': round(predict_time, 3),
    }
    return results


def get_confusion_matrix(model, X_test, y_test):
    """Trả về confusion matrix dạng array [[TN, FP], [FN, TP]]."""
    y_pred = model.predict(X_test)
    return confusion_matrix(y_test, y_pred)


def print_metrics_table(results_list):
    """In bảng metrics dạng DataFrame, dễ đối chiếu với anchor paper."""
    df_results = pd.DataFrame(results_list)
    return df_results.round(4)


# Bảng kết quả gốc từ anchor paper (Alumona et al., 2025) — dùng để đối chiếu trực tiếp
ANCHOR_PAPER_RESULTS = pd.DataFrame([
    {'model': 'Logistic Regression', 'accuracy': 0.9705, 'precision': 0.0382, 'recall': 0.9018, 'f1': 0.0732, 'roc_auc': 0.9838},
    {'model': 'KNN',                 'accuracy': 0.9954, 'precision': 0.1952, 'recall': 0.8255, 'f1': 0.3157, 'roc_auc': 0.9186},
    {'model': 'Decision Tree',       'accuracy': 0.9994, 'precision': 0.6835, 'recall': 0.9696, 'f1': 0.8018, 'roc_auc': 0.9845},
    {'model': 'Random Forest',       'accuracy': 0.9932, 'precision': 0.1576, 'recall': 0.9838, 'f1': 0.2716, 'roc_auc': 0.9990},
])


def compare_with_anchor_paper(my_results_df):
    """So sánh trực tiếp kết quả của bạn với anchor paper, theo từng model.

    Args:
        my_results_df: DataFrame trả về từ print_metrics_table(), phải có cột 'model'
                        khớp tên với ANCHOR_PAPER_RESULTS (VD: 'Logistic Regression', 'KNN').

    Returns:
        DataFrame ghép cạnh nhau: cột của bạn vs cột paper, cho từng metric.
    """
    merged = my_results_df.merge(
        ANCHOR_PAPER_RESULTS,
        on='model',
        suffixes=('_yours', '_paper'),
        how='left'
    )
    cols = ['model']
    for metric in ['accuracy', 'precision', 'recall', 'f1', 'roc_auc']:
        cols += [f'{metric}_yours', f'{metric}_paper']
    return merged[cols].round(4)