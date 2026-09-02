from enum import Enum

from pydantic import BaseModel, Field


class TransactionType(str, Enum):
    TRANSFER = "TRANSFER"
    CASH_OUT = "CASH_OUT"
    PAYMENT = "PAYMENT"
    CASH_IN = "CASH_IN"
    DEBIT = "DEBIT"


class TransactionRequest(BaseModel):
    step: int = Field(..., ge=0)
    type: TransactionType
    amount: float = Field(..., gt=0)
    oldbalanceOrg: float = Field(..., ge=0)
    newbalanceOrig: float = Field(..., ge=0)
    oldbalanceDest: float = Field(..., ge=0)
    newbalanceDest: float = Field(..., ge=0)


class TopFeature(BaseModel):
    feature: str
    shap_value: float


class PredictResponse(BaseModel):
    fraud_probability: float
    is_fraud_flag: bool
    threshold_used: float
    top_features: list[TopFeature]
    model_version: str


class ModelMetrics(BaseModel):
    recall: float
    precision: float
    f1: float


class ModelInfoResponse(BaseModel):
    model_version: str
    trained_on: str
    metrics: ModelMetrics
    threshold: float


class HealthResponse(BaseModel):
    status: str
