from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import requests
import os
import logging
import time
import hmac
import hashlib
from typing import List

from database import engine, Base, get_db
import models
import schemas
from github_analyzer import GitHubAnalyzer
from rules_engine import default_engine
from notifications import notifier
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
import auth

try:
    from github_tool import get_commit_data, post_pr_comment
except ImportError:
    logger = logging.getLogger("risk-backend")
    logger.warning("github_tool not available; webhook features disabled")
    get_commit_data = None
    post_pr_comment = None

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

# --- Startup Events ---
@app.on_event("startup")
def startup_db_seed():
    db = next(get_db())
    # Create default admin users if not exists
    default_admins = [
        {
            "username": "purna",
            "email": "purna@company.ai",
            "password": "purna1234",
            "full_name": "Purna"
        },
        {
            "username": "nithin",
            "email": "nithin@company.ai",
            "password": "nithin123",
            "full_name": "Nithin"
        },
        {
            "username": "meera",
            "email": "meera@company.ai",
            "password": "meera123",
            "full_name": "Meera"
        }
    ]
    for admin_info in default_admins:
        admin = db.query(models.User).filter(models.User.username == admin_info["username"]).first()
        if not admin:
            logger.info(f"Seeding default admin user '{admin_info['username']}'...")
            hashed_pw = auth.get_password_hash(admin_info["password"])
            new_admin = models.User(
                username=admin_info["username"],
                email=admin_info["email"],
                hashed_password=hashed_pw,
                full_name=admin_info["full_name"],
                role="Admin"
            )
            db.add(new_admin)
    db.commit()

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

@app.post("/api/auth/register", response_model=schemas.User, tags=["Auth"])
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
        role=user.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/api/auth/token", response_model=schemas.Token, tags=["Auth"])
async def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/auth/me", response_model=schemas.User, tags=["Auth"])
async def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

@app.post("/api/analyze-code", tags=["Analysis"])
async def analyze_code(request: schemas.CodeAnalysisRequest, current_user: models.User = Depends(auth.get_current_user)):
    """1. Endpoint: /analyze-code - Fetches and returns commit stats from GitHub."""
    logger.info(f"Analyzing code for {request.owner}/{request.repo} @ {request.commit_sha}")
    result = analyzer.get_commit_details(request.owner, request.repo, request.commit_sha)
    if not result:
        raise HTTPException(status_code=404, detail="Commit or repository not found via GitHub API.")
    return result

@app.post("/api/predict-risk", tags=["ML"])
async def predict_risk(request: schemas.RiskPredictionRequest, current_user: models.User = Depends(auth.get_current_user)):
    """2. Endpoint: /predict-risk - Proxies to ML service for an ad-hoc prediction."""
    try:
        response = requests.post(f"{ML_SERVICE_URL}/predict", json=request.dict(), timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"ML Service connection error: {e}")
        raise HTTPException(status_code=503, detail="Machine Learning service is currently unavailable.")

@app.get("/api/deployments", response_model=List[schemas.Deployment], tags=["Data"])
async def list_deployments(skip: int = 0, limit: int = 50, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """3. Endpoint: /deployments - Lists recent deployment records."""
    return db.query(models.Deployment).order_by(models.Deployment.timestamp.desc()).offset(skip).limit(limit).all()

@app.get("/api/risk-history", response_model=List[schemas.RiskPrediction], tags=["Data"])
async def get_risk_history(skip: int = 0, limit: int = 50, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """4. Endpoint: /risk-history - Fetches historical risk scoring data."""
    return db.query(models.RiskPrediction).order_by(models.RiskPrediction.id.desc()).offset(skip).limit(limit).all()

@app.get("/api/approval-recommendation/{deployment_id}", response_model=schemas.ApprovalRecommendation, tags=["Analysis"])
async def get_recommendation(deployment_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
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
async def update_rules_config(config: schemas.RuleConfig, current_user: models.User = Depends(auth.get_current_user)):
    """Update risk thresholds in real-time."""
    default_engine.low_threshold = config.low_threshold
    default_engine.high_threshold = config.high_threshold
    logger.info(f"Thresholds updated to: Low={config.low_threshold}, High={config.high_threshold}")
    return {"status": "updated", "config": config}

# Original creation endpoint for full flow integration
@app.post("/api/deployments", response_model=schemas.Deployment, tags=["Data"])
async def create_deployment(deployment: schemas.DeploymentCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
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
        **deployment.code_changes.dict(),
        "author": deployment.author
    }
    background_tasks.add_task(fetch_and_store_risk, new_deployment.id, ml_payload, db)

    return new_deployment

@app.get("/api/analytics", tags=["Analysis"])
async def get_analytics(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
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

# --- GitHub Webhook ---
@app.post("/webhook/github", tags=["Webhooks"])
async def github_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Handle GitHub webhook events for PR auto-analysis."""
    payload = await request.json()
    event = request.headers.get("X-GitHub-Event")
    
    # Verify webhook signature (optional but recommended)
    github_secret = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    if github_secret:
        signature = request.headers.get("X-Hub-Signature-256", "")
        if not verify_github_signature(signature, await request.body(), github_secret):
            logger.warning("Invalid GitHub webhook signature")
            raise HTTPException(status_code=403, detail="Invalid signature")
    
    logger.info(f"Received GitHub webhook: {event}")
    
    if event == "pull_request" and payload.get("action") in ["opened", "synchronize"]:
        try:
            if not get_commit_data or not post_pr_comment:
                logger.warning("GitHub tool not available; skipping webhook processing")
                return {"status": "skipped", "reason": "github_tool unavailable"}
            
            pr_data = payload.get("pull_request", {})
            sha = pr_data.get("head", {}).get("sha")
            pr_number = pr_data.get("number")
            
            if not sha or not pr_number:
                return {"status": "skipped", "reason": "missing sha or pr_number"}
            
            logger.info(f"Processing PR#{pr_number} commit {sha}")
            
            # Background task to fetch commit data and predict risk
            background_tasks.add_task(
                process_pr_webhook,
                sha=sha,
                pr_number=pr_number,
                repo_owner=payload.get("repository", {}).get("owner", {}).get("login"),
                repo_name=payload.get("repository", {}).get("name"),
                db=db
            )
            return {"status": "queued"}
        except Exception as e:
            logger.error(f"Webhook processing error: {e}")
            return {"status": "error", "detail": str(e)}
    
    return {"status": "ok"}

def verify_github_signature(signature: str, body: bytes, secret: str) -> bool:
    """Verify GitHub webhook signature."""
    if not signature:
        return False
    try:
        hash_object = hmac.new(secret.encode(), body, hashlib.sha256)
        expected = f"sha256={hash_object.hexdigest()}"
        return hmac.compare_digest(signature, expected)
    except Exception as e:
        logger.error(f"Signature verification error: {e}")
        return False

def process_pr_webhook(sha: str, pr_number: int, repo_owner: str, repo_name: str, db: Session):
    """Background task to process PR webhook."""
    try:
        logger.info(f"Processing PR webhook for {repo_owner}/{repo_name}#{pr_number} @{sha}")
        
        # Get commit data using github_tool
        commit_data = get_commit_data(sha)
        
        # Prepare ML payload
        ml_payload = {
            "files_changed": commit_data.get("files_changed", 0),
            "lines_added": commit_data.get("lines_added", 0),
            "lines_deleted": commit_data.get("lines_deleted", 0),
            "author": commit_data.get("author", "unknown"),
            "time_of_deployment": datetime.utcnow().hour,
            "previous_failures": 0,
            "code_complexity": min(10.0, commit_data.get("files_changed", 0) * 0.5),
        }
        
        # Call ML service
        response = requests.post(
            f"{ML_SERVICE_URL}/predict",
            json=ml_payload,
            timeout=10
        )
        response.raise_for_status()
        ml_data = response.json()
        
        # Evaluate with rule engine
        evaluation = default_engine.evaluate(ml_data.get("risk_score", 0), ml_payload)
        
        # Post result as PR comment
        post_pr_comment(
            pr_number=pr_number,
            risk_score=evaluation.get("risk_score", 0),
            reasoning=evaluation.get("decision_explanation", "No reasoning available")
        )
        
        logger.info(f"PR#{pr_number} analysis complete: {evaluation.get('risk_level')} risk")
    except Exception as e:
        logger.error(f"PR webhook processing failed: {e}")

