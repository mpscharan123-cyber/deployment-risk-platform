import requests
import random
import uuid
import time
import datetime

API_URL = "http://localhost:8000/api/deployments"

authors = ["junior-dev", "senior-dev", "lead", "newbi", "frontend-guru", "backend-wizard"]

def send_webhook():
    commit_hash = uuid.uuid4().hex[:40]
    author = random.choice(authors)
    
    # Randomly generate code changes
    lines_added = random.randint(10, 2000)
    lines_deleted = random.randint(0, 500)
    files_changed = random.randint(1, 50)
    
    payload = {
        "commit_hash": commit_hash,
        "author": author,
        "code_changes": {
            "lines_added": lines_added,
            "lines_deleted": lines_deleted,
            "files_changed": files_changed
        }
    }
    
    print(f"Sending deployment from {author}: +{lines_added} -{lines_deleted} in {files_changed} files")
    try:
        res = requests.post(API_URL, json=payload)
        res.raise_for_status()
        print("Success:", res.json())
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    print("Simulating GitHub Webhook payloads...")
    for _ in range(5):
        send_webhook()
        time.sleep(1)
