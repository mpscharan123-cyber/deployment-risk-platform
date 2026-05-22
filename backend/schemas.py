from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class CodeChangeBase(BaseModel):
    lines_added: int
    lines_deleted: int
    files_changed: int

class CodeChangeCreate(CodeChangeBase):
    pass

class CodeChange(CodeChangeBase):
    id: int
    deployment_id: int
    class Config:
        orm_mode = True

class RiskPredictionBase(BaseModel):
    risk_score: float
    risk_level: str
    recommendation: str
    reasoning: Optional[str] = None

class RiskPrediction(RiskPredictionBase):
    id: int
    deployment_id: int
    class Config:
        orm_mode = True

class DeploymentBase(BaseModel):
    commit_hash: str
    author: str

class DeploymentCreate(DeploymentBase):
    code_changes: CodeChangeCreate

class DeploymentStatusUpdate(BaseModel):
    status: str

class Deployment(DeploymentBase):
    id: int
    status: str
    timestamp: datetime
    code_changes: Optional[CodeChange] = None
    risk_prediction: Optional[RiskPrediction] = None
    class Config:
        orm_mode = True

class CodeAnalysisRequest(BaseModel):
    owner: str
    repo: str
    commit_sha: str

class RiskPredictionRequest(BaseModel):
    files_changed: int
    lines_added: int
    lines_deleted: int
    author: str
    time_of_deployment: Optional[int] = 12
    previous_failures: Optional[int] = 0
    code_complexity: Optional[float] = 5.0

class ApprovalRecommendation(BaseModel):
    deployment_id: int
    recommendation: str
    risk_score: float
    risk_level: str
    reasoning: str
    required_approval: Optional[str] = None
    estimated_delay_hours: Optional[int] = 0

class RuleConfig(BaseModel):
    low_threshold: float = 30.0
    high_threshold: float = 70.0

# --- Authentication Schemas ---

class UserBase(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None
    role: Optional[str] = "Developer"

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None

class User(UserBase):
    id: int
    is_active: int
    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
