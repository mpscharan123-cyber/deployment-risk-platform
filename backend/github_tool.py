from github import Github
from dotenv import load_dotenv
import os

load_dotenv()

g = Github(os.getenv("GITHUB_TOKEN"))
repo = g.get_repo(os.getenv("GITHUB_REPO"))

def get_commit_data(commit_sha: str) -> dict:
    """Pull commit metadata for ML model input."""
    commit = repo.get_commit(commit_sha)
    return {
        "sha": commit_sha,
        "author": commit.author.login if commit.author else "unknown",
        "lines_added": commit.stats.additions,
        "lines_deleted": commit.stats.deletions,
        "files_changed": len(commit.files),
        "message": commit.commit.message,
    }

def get_open_prs() -> list:
    """Fetch all open pull requests."""
    prs = repo.get_pulls(state='open', sort='created')
    return [
        {
            "number": pr.number,
            "title": pr.title,
            "author": pr.user.login,
            "files_changed": pr.changed_files,
            "additions": pr.additions,
            "deletions": pr.deletions,
        }
        for pr in prs
    ]

def post_pr_comment(pr_number: int, risk_score: float, reasoning: str):
    """Post risk prediction result as a PR comment."""
    pr = repo.get_pull(pr_number)
    message = f"""## 🤖 Deployment Risk Report
**Risk Score**: `{risk_score}/100`
**Reasoning**: {reasoning}
{"🔴 BLOCKED — High risk detected." if risk_score > 70 else "🟡 Manual review required." if risk_score > 30 else "🟢 Auto-approved."}
"""
    pr.create_issue_comment(message)
