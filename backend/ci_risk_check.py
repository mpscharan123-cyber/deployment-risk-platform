import os
import requests
import sys
import json

# Configuration from Environment Variables
API_BASE_URL = os.environ.get("RISK_API_URL", "https://api.your-risk-platform.com")
COMMIT_SHA = os.environ.get("GITHUB_SHA")
AUTHOR = os.environ.get("GITHUB_ACTOR")
FILES_CHANGED = int(os.environ.get("FILES_CHANGED", 0))
LINES_ADDED = int(os.environ.get("LINES_ADDED", 0))
LINES_DELETED = int(os.environ.get("LINES_DELETED", 0))

def run_risk_check():
    print(f"--- Deployment Risk Check for {COMMIT_SHA[:7]} ---")
    
    payload = {
        "commit_hash": COMMIT_SHA,
        "author": AUTHOR,
        "code_changes": {
            "lines_added": LINES_ADDED,
            "lines_deleted": LINES_DELETED,
            "files_changed": FILES_CHANGED
        }
    }

    try:
        # 1. Register deployment and trigger prediction
        response = requests.post(f"{API_BASE_URL}/api/deployments", json=payload, timeout=15)
        response.raise_for_status()
        deployment = response.json()
        deployment_id = deployment["id"]
        
        # 2. Poll for the prediction result (as it's processed in a background task)
        print("Waiting for AI risk assessment...")
        import time
        for _ in range(10):  # Poll for max 20 seconds
            time.sleep(2)
            rec_res = requests.get(f"{API_BASE_URL}/api/approval-recommendation/{deployment_id}")
            if rec_res.status_code == 200:
                result = rec_res.json()
                print_analysis_result(result)
                handle_exit_logic(result)
                return
            
        print("Error: Risk assessment timed out.")
        sys.exit(1)
        
    except Exception as e:
        print(f"CRITICAL: Failed to connect to Risk Platform: {e}")
        # In many production scenarios, we might default to 'fail closed' for security
        sys.exit(1)

def print_analysis_result(result):
    print("\n========================================")
    print(f"AI RISK LEVEL: {result['risk_level']}")
    print(f"RISK SCORE:    {result['risk_score']}/100")
    print(f"RECOMMENDATION: {result['recommendation']}")
    print(f"REASONING:      {result['reasoning']}")
    print("========================================\n")

def handle_exit_logic(result):
    level = result['risk_level']
    
    if level == "High":
        print("🚨 DEPLOYMENT BLOCKED: High risk predicted. Please review and refactor.")
        sys.exit(1)  # Fail the CI build
    elif level == "Medium":
        print("⚠️ MANUAL APPROVAL REQUIRED: Moderate risk detected. Build marked as failed to prevent auto-merge.")
        # In a real setup, you might use a specific exit code or GitHub Deployment APIs to mark "Pending"
        sys.exit(1)
    else:
        print("✅ DEPLOYMENT ALLOWED: Low risk detected. Confidence score is high.")
        sys.exit(0)  # Pass the CI build

if __name__ == "__main__":
    if not COMMIT_SHA:
        print("Error: GITHUB_SHA not found in environment.")
        sys.exit(1)
    run_risk_check()
