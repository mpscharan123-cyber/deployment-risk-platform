from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, List
import random

app = FastAPI(title="Enterprise Risk ML Service (Mock Mode)")

class PredictionRequest(BaseModel):
    files_changed: int
    lines_added: int
    lines_deleted: int
    author: str
    time_of_deployment: int = 12
    previous_failures: int = 0
    code_complexity: float = 5.0

class PredictionResponse(BaseModel):
    risk_score: float
    risk_level: str
    recommendation: str
    reasoning: str
    is_anomaly: bool
    shap_values: Dict[str, float]

@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest):
    # Heuristic-based risk score (Mock)
    # This replaces the XGBoost model which requires modern build tools
    total_changes = request.lines_added + request.lines_deleted
    risk_score = (total_changes / 500) * 100 + (request.files_changed * 5)
    risk_score = round(max(0.0, min(100.0, risk_score)), 2)
    
    if risk_score < 30:
        risk_level = "Low"
        rec = "Auto-Approve"
    elif risk_score < 70:
        risk_level = "Medium"
        rec = "Manual Review"
    else:
        risk_level = "High"
        rec = "Reject"
    
    is_anomaly = (risk_score > 80 and random.random() > 0.5)
    
    return PredictionResponse(
        risk_score=risk_score,
        risk_level=risk_level,
        recommendation=rec,
        reasoning=f"Engine Heuristics: Flagged as {risk_level} risk due to {total_changes} lines of modification across {request.files_changed} files.",
        is_anomaly=is_anomaly,
        shap_values={
            "lines_added": request.lines_added * 0.1,
            "files_changed": request.files_changed * 2.0,
            "complexity": request.code_complexity * 5.0
        }
    )

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "enterprise-inference-mock"}
