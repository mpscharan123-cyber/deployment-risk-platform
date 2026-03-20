import os
import requests
import json
import logging
from typing import Dict, Any
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class GitHubAnalyzer:
    """
    Service to analyze code changes from GitHub repositories 
    and output structured JSON for ML model input.
    """
    
    def __init__(self, token: str = None):
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"
        else:
            logger.warning("No GITHUB_TOKEN provided. API rate limits will be restricted to 60 requests/hr.")

    def get_commit_details(self, owner: str, repo: str, commit_sha: str) -> Dict[str, Any]:
        """Fetch detailed stats (files changed, line additions/deletions) for a specific commit."""
        url = f"{self.base_url}/repos/{owner}/{repo}/commits/{commit_sha}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            stats = data.get("stats", {})
            return {
                "files_changed": len(data.get("files", [])),
                "lines_added": stats.get("additions", 0),
                "lines_deleted": stats.get("deletions", 0),
                "author": data.get("commit", {}).get("author", {}).get("name", "Unknown"),
                "date": data.get("commit", {}).get("author", {}).get("date")
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch commit {commit_sha}: {e}")
            return None

    def analyze_recent_activity(self, owner: str, repo: str, days: int = 30) -> Dict[str, Any]:
        """
        Analyze commits over the last X days to calculate:
        - Commit frequency
        - Developer contributions
        """
        since_date = (datetime.utcnow() - timedelta(days=days)).isoformat() + "Z"
        url = f"{self.base_url}/repos/{owner}/{repo}/commits"
        params = {"since": since_date, "per_page": 100}
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            commits = response.json()
            
            author_counts = {}
            for c in commits:
                author_name = c.get("commit", {}).get("author", {}).get("name", "Unknown")
                author_counts[author_name] = author_counts.get(author_name, 0) + 1
                
            return {
                "total_commits_period": len(commits),
                "active_developers": len(author_counts),
                "developer_contributions": author_counts
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch repo activity for {owner}/{repo}: {e}")
            return None

    def generate_ml_payload(self, owner: str, repo: str, commit_sha: str) -> str:
        """
        Generates structured JSON required for the ML Risk Prediction Model
        by heavily extracting GitHub analytics.
        """
        logger.info(f"Analyzing commit {commit_sha} in {owner}/{repo}...")
        
        commit_data = self.get_commit_details(owner, repo, commit_sha)
        if not commit_data:
            return json.dumps({"error": "Failed to fetch commit data"})
            
        activity_data = self.analyze_recent_activity(owner, repo, days=30)
        
        # Calculate heuristics for the ML model
        author = commit_data["author"]
        commit_date = datetime.fromisoformat(commit_data["date"].replace("Z", "+00:00"))
        
        # Estimate developer contribution (commits over last 30 days)
        dev_commits = activity_data.get("developer_contributions", {}).get(author, 0) if activity_data else 0
        repo_commits = activity_data.get("total_commits_period", 1) if activity_data else 1
        dev_contribution_pct = round((dev_commits / repo_commits) * 100, 2)
        
        # Prepare structured JSON payload exactly as the ML service expects
        payload = {
            "files_changed": commit_data["files_changed"],
            "lines_added": commit_data["lines_added"],
            "lines_deleted": commit_data["lines_deleted"],
            "author": author,
            "time_of_deployment": commit_date.hour,
            "previous_failures": 0, # Integrate with incidents DB inside backend in production
            "code_complexity": min(10.0, commit_data["files_changed"] * 0.5), # Heuristic approx
            "metadata": {
                "commit_hash": commit_sha,
                "repo": f"{owner}/{repo}",
                "author_recent_commits_30d": dev_commits,
                "author_repo_contribution_pct": dev_contribution_pct,
                "total_repo_commits_30d": repo_commits
            }
        }
        
        return json.dumps(payload, indent=2)

if __name__ == "__main__":
    # Test execution evaluating a public open-source project
    analyzer = GitHubAnalyzer()
    
    owner = "tiangolo"
    repo = "fastapi"
    
    print(f"Fetching latest commit for {owner}/{repo}...")
    try:
        # Dynamically grab the latest commit
        latest_commit_url = f"https://api.github.com/repos/{owner}/{repo}/commits?per_page=1"
        latest_sha = requests.get(latest_commit_url).json()[0]["sha"]
        
        # Generate the structured ML JSON payload
        ml_input = analyzer.generate_ml_payload(owner, repo, latest_sha)
        
        print("\n--- ML Model JSON Payload ---")
        print(ml_input)
    except Exception as e:
        logger.error(f"Failed to execute demo: {e}")
