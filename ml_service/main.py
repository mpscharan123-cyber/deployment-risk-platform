from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import pickle
import os
import train_model
from typing import Dict, List

app = FastAPI(title="Enterprise Risk ML Service")

MODEL_PATH = "risk_model.pkl"

# Automatically train/generate model on startup if missing
if not os.path.exists(MODEL_PATH):
    print("Model not found. Training enterprise model now...")
    train_model.main()

with open(MODEL_PATH, 'rb') as f:
    model_data = pickle.load(f)
    clf = model_data['model']
    iso_forest = model_data['anomaly_detector']
    explainer = model_data['explainer']
    features = model_data['features']
    mapper = model_data['mapper']

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
    # Map author to dev_experience heuristic
    dev_experience = 1
    if request.author.lower() in ["junior-dev", "newbie"]:
        dev_experience = 0
    elif request.author.lower() in ["senior-dev", "lead", "architect"]:
        dev_experience = 2
        
    input_data = pd.DataFrame([{
        'files_changed': request.files_changed,
        'lines_added': request.lines_added,
        'lines_deleted': request.lines_deleted,
        'dev_experience': dev_experience,
        'time_of_deployment': request.time_of_deployment,
        'previous_failures': request.previous_failures,
        'code_complexity': request.code_complexity
    }])[features]

    # 1. Predict Risk Probabilities
    probs = clf.predict_proba(input_data)[0]
    pred_idx = probs.argmax()
    risk_level = mapper[pred_idx]
    
    # 2. Risk Score calculation
    risk_score = (probs[2] * 100) + (probs[1] * 50) + (probs[0] * 10)
    risk_score = round(max(0.0, min(100.0, risk_score)), 2)
    
    # 3. Anomaly Detection (-1 = anomaly, 1 = normal)
    is_anomaly = iso_forest.predict(input_data)[0] == -1
    
    # 4. Explainable AI: SHAP Values
    shap_vals = explainer.shap_values(input_data)[pred_idx][0]
    feature_importance = {features[i]: float(shap_vals[i]) for i in range(len(features))}
    
    # Generate Recommendation & Reasoning
    if risk_level == "Low":
        rec = "Auto-Approve"
        reason = "Our XGBoost model indicates high confidence that these changes are safe based on historical patterns."
    elif risk_level == "Medium":
        rec = "Manual Review"
        reason = f"Moderate risk detected (Score: {risk_score}). Please review the code complexity and file modifications."
    else:
        rec = "Reject"
        reason = "High likelihood of deployment incident predicted. This exceeds acceptable risk thresholds."
        
    if is_anomaly:
        reason += " WARNING: This deployment is a statistical outlier/anomaly."
        
    return PredictionResponse(
        risk_score=risk_score,
        risk_level=risk_level,
        recommendation=rec,
        reasoning=reason,
        is_anomaly=is_anomaly,
        shap_values=feature_importance
    )

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "enterprise-inference"}
