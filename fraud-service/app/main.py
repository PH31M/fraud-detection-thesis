import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import METRICS, MODEL_VERSION, SERVICE_ROOT, THRESHOLD, TRAINED_ON
from app.model_loader import bundle
from app.predict import predict_transaction
from app.schemas import (
    HealthResponse,
    ModelInfoResponse,
    PredictResponse,
    TransactionRequest,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Fail fast: if the model can't be loaded, the service should not start
    # serving traffic at all.
    bundle.load()
    logger.info("Model loaded: %s", MODEL_VERSION)
    yield


app = FastAPI(title="Fraud Detection Service", version=MODEL_VERSION, lifespan=lifespan)


@app.get("/health", response_model=HealthResponse)
def health():
    """Liveness check. Does not reload the model — just reports whether the
    model that was loaded at startup is still in memory."""
    if not bundle.is_ready:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return {"status": "ok"}


@app.get("/model-info", response_model=ModelInfoResponse)
def model_info():
    return {
        "model_version": MODEL_VERSION,
        "trained_on": TRAINED_ON,
        "metrics": METRICS,
        "threshold": THRESHOLD,
    }


@app.post("/predict", response_model=PredictResponse)
def predict(transaction: TransactionRequest):
    """Predict fraud probability for a raw transaction.

    Transaction types other than TRANSFER/CASH_OUT are valid input and are
    still scored by the model — they are not rejected. Per PaySim domain
    knowledge, fraud in this dataset only occurs in TRANSFER and CASH_OUT
    transactions, so other types will almost always score near-zero fraud
    probability; that is expected model behavior, not an error.
    """
    if not bundle.is_ready:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        result = predict_transaction(bundle, transaction.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Prediction failed") from exc

    return {**result, "model_version": MODEL_VERSION}


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc):
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# Must be mounted last: StaticFiles(html=True) serves "/" and would otherwise
# shadow the API routes declared above it.
app.mount("/", StaticFiles(directory=SERVICE_ROOT / "static", html=True), name="static")
