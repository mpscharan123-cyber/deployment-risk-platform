from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import requests
import os
import logging
import time
from typing import List

from database import engine, Base, get_db
import models
import schemas
from github_analyzer import GitHubAnalyzer
from rules_engine import default_engine
from notifications import notifier
from fastapi.middleware.cors import CORSMiddleware

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("risk-backend")

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Deployment Risk Prediction Platform Architecture",
    description="""
    ## 🧠 AI-Driven Release Governance
    A production-ready platform designed to forecast deployment risk before production releases using machine learning and historical code analysis.
    
    ### Key Features:
    * **Automated Risk Gating**: Integration with GitHub Actions for automated pull request blocking.
    * **Explainable AI Integration**: Rules-based engine translating ML outputs into actionable recommendations.
    * **High-Performance Microservices**: Decoupled backend and inference services for high scalability.
    """,
    version="1.0.5",
    contact={
        "name": "DevSecOps Engineering",
        "url": "https://company.ai/risk-platform",
    },
    license_info={
        "name": "Proprietary",
    },
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
ML_SERVICE_URL = os.getenv("ML_SERVICE_URL", "http://localhost:8001")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
analyzer = GitHubAnalyzer(token=GITHUB_TOKEN)

# --- Exception Handlers ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred.", "type": str(type(exc).__name__)}
    )

# --- Background Tasks ---
def fetch_and_store_risk(deployment_id: int, payload: dict, db: Session):
    """Async task to get a risk prediction and evaluate against the rule engine."""
    try:
        logger.info(f"Requesting ML prediction for deployment {deployment_id}...")
        response = requests.post(f"{ML_SERVICE_URL}/predict", json=payload, timeout=10)
        response.raise_for_status()
        ml_data = response.json()
        
        # Evaluate with the configurable rule engine for "explainable" results
        evaluation = default_engine.evaluate(ml_data["risk_score"], payload)
        
        # Enterprise Alerts
        if ml_data.get("is_anomaly"):
            notifier.notify_on_anomaly(deployment_id)
            
        if evaluation["risk_level"] == "High":
            notifier.send_slack_alert(deployment_id, evaluation["risk_level"], evaluation["risk_score"], evaluation["decision_explanation"])
            notifier.send_email_alert(deployment_id, evaluation["risk_level"], evaluation["risk_score"], evaluation["decision_explanation"])

        db_prediction = models.RiskPrediction(
            deployment_id=deployment_id,
            risk_score=evaluation["risk_score"],
            risk_level=evaluation["risk_level"],
            recommendation=evaluation["recommendation"],
            reasoning=f"{evaluation['decision_explanation']} | SHAP Importance: {ml_data.get('shap_values', {})}"
        )
        db.add(db_prediction)
        
        # Update deployment status based on engine's specific logic
        db_deployment = db.query(models.Deployment).filter(models.Deployment.id == deployment_id).first()
        if evaluation["recommendation"] == "Auto approve":
            db_deployment.status = "approved"
        elif "Senior approval" in evaluation["recommendation"]:
            db_deployment.status = "flagged_high_risk"
        else:
            db_deployment.status = "pending_manager_review"
            
        db.commit()
    except Exception as e:
        logger.error(f"Failed to fetch risk prediction for {deployment_id}: {e}")

# --- API Endpoints ---

@app.post("/api/analyze-code", tags=["Analysis"])
async def analyze_code(request: schemas.CodeAnalysisRequest):
    """1. Endpoint: /analyze-code - Fetches and returns commit stats from GitHub."""
    logger.info(f"Analyzing code for {request.owner}/{request.repo} @ {request.commit_sha}")
    result = analyzer.get_commit_details(request.owner, request.repo, request.commit_sha)
    if not result:
        raise HTTPException(status_code=404, detail="Commit or repository not found via GitHub API.")
    return result

@app.post("/api/predict-risk", tags=["ML"])
async def predict_risk(request: schemas.RiskPredictionRequest):
    """2. Endpoint: /predict-risk - Proxies to ML service for an ad-hoc prediction."""
    try:
        response = requests.post(f"{ML_SERVICE_URL}/predict", json=request.model_dump(), timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"ML Service connection error: {e}")
        raise HTTPException(status_code=503, detail="Machine Learning service is currently unavailable.")

@app.get("/api/deployments", response_model=List[schemas.Deployment], tags=["Data"])
async def list_deployments(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """3. Endpoint: /deployments - Lists recent deployment records."""
    return db.query(models.Deployment).order_by(models.Deployment.timestamp.desc()).offset(skip).limit(limit).all()

@app.get("/api/risk-history", response_model=List[schemas.RiskPrediction], tags=["Data"])
async def get_risk_history(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """4. Endpoint: /risk-history - Fetches historical risk scoring data."""
    return db.query(models.RiskPrediction).order_by(models.RiskPrediction.id.desc()).offset(skip).limit(limit).all()

@app.get("/api/approval-recommendation/{deployment_id}", response_model=schemas.ApprovalRecommendation, tags=["Analysis"])
async def get_recommendation(deployment_id: int, db: Session = Depends(get_db)):
    """5. Endpoint: /approval-recommendation - Returns specific logic and approval level."""
    prediction = db.query(models.RiskPrediction).filter(models.RiskPrediction.deployment_id == deployment_id).first()
    if not prediction:
        raise HTTPException(status_code=404, detail="Risk prediction for this deployment not found.")
    
    # Enrichment from the active rule engine state
    return {
        "deployment_id": deployment_id,
        "recommendation": prediction.recommendation,
        "risk_score": prediction.risk_score,
        "risk_level": prediction.risk_level,
        "reasoning": prediction.reasoning,
        "required_approval": "Senior Staff" if prediction.risk_level == "High" else ("Manager" if prediction.risk_level == "Medium" else "None"),
        "estimated_delay_hours": 24 if prediction.risk_level == "High" else (4 if prediction.risk_level == "Medium" else 0)
    }

@app.get("/api/rules/config", tags=["Rules"])
async def get_rules_config():
    """Fetch current risk thresholds."""
    return {"low_threshold": default_engine.low_threshold, "high_threshold": default_engine.high_threshold}

@app.post("/api/rules/config", tags=["Rules"])
async def update_rules_config(config: schemas.RuleConfig):
    """Update risk thresholds in real-time."""
    default_engine.low_threshold = config.low_threshold
    default_engine.high_threshold = config.high_threshold
    logger.info(f"Thresholds updated to: Low={config.low_threshold}, High={config.high_threshold}")
    return {"status": "updated", "config": config}

# Original creation endpoint for full flow integration
@app.post("/api/deployments", response_model=schemas.Deployment, tags=["Data"])
async def create_deployment(deployment: schemas.DeploymentCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    db_deployment = db.query(models.Deployment).filter(models.Deployment.commit_hash == deployment.commit_hash).first()
    if db_deployment:
        raise HTTPException(status_code=400, detail="Deployment with this commit hash already exists.")

    new_deployment = models.Deployment(
        commit_hash=deployment.commit_hash,
        author=deployment.author
    )
    db.add(new_deployment)
    db.commit()
    db.refresh(new_deployment)

    new_code_changes = models.CodeChange(
        deployment_id=new_deployment.id,
        lines_added=deployment.code_changes.lines_added,
        lines_deleted=deployment.code_changes.lines_deleted,
        files_changed=deployment.code_changes.files_changed
    )
    db.add(new_code_changes)
    db.commit()

    ml_payload = {
        **deployment.code_changes.model_dump(),
        "author": deployment.author
    }
    background_tasks.add_task(fetch_and_store_risk, new_deployment.id, ml_payload, db)

    return new_deployment

@app.get("/api/analytics", tags=["Analysis"])
async def get_analytics(db: Session = Depends(get_db)):
    total = db.query(models.Deployment).count()
    status_counts = db.query(models.Deployment.status).all()
    risk_levels = db.query(models.RiskPrediction.risk_level).all()
    
    return {
        "total_deployments": total,
        "status_distribution": {
            "approved": sum(1 for s in status_counts if s[0] == "approved"),
            "rejected": sum(1 for s in status_counts if s[0] == "rejected"),
            "pending": sum(1 for s in status_counts if s[0] in ["pending", "pending_review"])
        },
        "risk_distribution": {
            "high": sum(1 for r in risk_levels if r[0] == "High"),
            "medium": sum(1 for r in risk_levels if r[0] == "Medium"),
            "low": sum(1 for r in risk_levels if r[0] == "Low")
        }
    }
