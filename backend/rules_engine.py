import logging
from typing import Dict, Any

logger = logging.getLogger("risk-rules")

class RiskRuleEngine:
    """
    Configurable Rule Engine for Deployment Approval Recommendations.
    """
    
    def __init__(self, low_threshold: float = 30.0, high_threshold: float = 70.0):
        self.low_threshold = low_threshold
        self.high_threshold = high_threshold

    def evaluate(self, risk_score: float, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates risk score and features to provide a multi-level recommendation.
        """
        explanation = []
        
        # Determine base recommendation level
        if risk_score < self.low_threshold:
            recommendation = "Auto approve"
            level = "Low"
            required_approval = "System (Automated)"
            delay_hours = 0
            explanation.append(f"Risk score ({risk_score}) is below the confidence threshold of {self.low_threshold}.")
        elif risk_score < self.high_threshold:
            recommendation = "Manager approval"
            level = "Medium"
            required_approval = "Engineering Manager"
            delay_hours = 4  # Estimated review wait time
            explanation.append(f"Moderate risk score ({risk_score}) exceeds auto-approval threshold.")
        else:
            recommendation = "Senior approval + delay"
            level = "High"
            required_approval = "Senior AI Architect / CTO"
            delay_hours = 24 # Standard cooldown/deep-dive period
            explanation.append(f"High risk score ({risk_score}) detected. Safety protocol requires senior deep-dive.")

        # Add feature-specific explanations
        if features.get("contains_db_migration"):
            explanation.append("Decision influenced by presence of database schema migrations.")
        if features.get("files_changed", 0) > 20:
            explanation.append(f"Large impact area detected ({features['files_changed']} files modified).")
        if features.get("previous_failures", 0) > 0:
            explanation.append(f"Calculated risk includes penalty for {features['previous_failures']} recent historical incidents.")

        return {
            "risk_score": risk_score,
            "risk_level": level,
            "recommendation": recommendation,
            "required_approval": required_approval,
            "estimated_delay_hours": delay_hours,
            "decision_explanation": " ".join(explanation),
            "thresholds": {
                "low": self.low_threshold,
                "high": self.high_threshold
            }
        }

# Default singleton instance
default_engine = RiskRuleEngine()
