import datetime
import random
import uuid
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models

def seed_data():
    db = SessionLocal()
    
    # Ensure tables are created
    models.Base.metadata.create_all(bind=engine)
    
    print("Seeding sample data...")
    
    sample_authors = ["mpscharan123-cyber", "dev_master", "alpha_tester", "release_lead"]
    sample_statuses = ["approved", "deployed", "pending", "rejected", "flagged_high_risk"]
    risk_levels = [("Low", 15.5, "Auto-Approve", "Low impact code changes."),
                   ("Medium", 42.0, "Manual Review", "Moderate complexity detected."),
                   ("High", 88.5, "Reject", "High risk of regression in core modules.")]

    for i in range(10):
        commit_hash = uuid.uuid4().hex
        author = random.choice(sample_authors)
        status = random.choice(sample_statuses)
        timestamp = datetime.datetime.utcnow() - datetime.timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
        
        # Create Deployment
        deployment = models.Deployment(
            commit_hash=commit_hash,
            author=author,
            status=status,
            timestamp=timestamp
        )
        db.add(deployment)
        db.commit()
        db.refresh(deployment)
        
        # Create CodeChange
        lines_added = random.randint(10, 500)
        lines_deleted = random.randint(0, 300)
        files_changed = random.randint(1, 15)
        
        code_change = models.CodeChange(
            deployment_id=deployment.id,
            lines_added=lines_added,
            lines_deleted=lines_deleted,
            files_changed=files_changed
        )
        db.add(code_change)
        
        # Create RiskPrediction
        level_data = random.choice(risk_levels)
        risk_prediction = models.RiskPrediction(
            deployment_id=deployment.id,
            risk_score=level_data[1] + random.uniform(-5, 5),
            risk_level=level_data[0],
            recommendation=level_data[2],
            reasoning=level_data[3]
        )
        db.add(risk_prediction)
        
        db.commit()
        print(f"  - Added deployment {commit_hash[:8]} by {author}")

    db.close()
    print("Successfully seeded 10 sample records.")

if __name__ == "__main__":
    seed_data()
