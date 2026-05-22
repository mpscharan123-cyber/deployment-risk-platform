from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
import datetime
from database import Base

class Deployment(Base):
    __tablename__ = "deployments"

    id = Column(Integer, primary_key=True, index=True)
    commit_hash = Column(String(40), unique=True, index=True, nullable=False)
    author = Column(String(100), nullable=False)
    status = Column(String(50), default="pending")  # pending, approved, rejected, deployed
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    code_changes = relationship("CodeChange", back_populates="deployment", uselist=False)
    risk_prediction = relationship("RiskPrediction", back_populates="deployment", uselist=False)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    role = Column(String(50), default="Developer") # Admin, Architect, Developer
    is_active = Column(Integer, default=1) # 1 for True, 0 for False (SQLite compat)

class CodeChange(Base):
    __tablename__ = "code_changes"

    id = Column(Integer, primary_key=True, index=True)
    deployment_id = Column(Integer, ForeignKey("deployments.id"), unique=True, nullable=False)
    lines_added = Column(Integer, default=0)
    lines_deleted = Column(Integer, default=0)
    files_changed = Column(Integer, default=0)

    deployment = relationship("Deployment", back_populates="code_changes")

class RiskPrediction(Base):
    __tablename__ = "risk_predictions"

    id = Column(Integer, primary_key=True, index=True)
    deployment_id = Column(Integer, ForeignKey("deployments.id"), unique=True, nullable=False)
    risk_score = Column(Float, nullable=False)  # 0 to 100
    risk_level = Column(String(20), nullable=False)  # Low, Medium, High
    recommendation = Column(String(50), nullable=False)  # Auto-Approve, Manual Review, Reject
    reasoning = Column(Text, nullable=True)

    deployment = relationship("Deployment", back_populates="risk_prediction")
