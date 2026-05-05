from os import getenv
from urllib.parse import urlparse

import httpx


def fetch_github_issues(
    repo: str,
    state: str = "open",
    labels: list[str] | None = None,
    limit: int = 30,
    token: str | None = None,
    include_pull_requests: bool = False,
) -> list[dict]:
    from utils.env import load_env

    load_env()

    owner, repo_name = _parse_github_repo(repo)
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    github_token = token or getenv("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"

    issues: list[dict] = []
    page = 1

    with httpx.Client(base_url="https://api.github.com", headers=headers, timeout=30) as client:
        while len(issues) < limit:
            per_page = min(100, limit - len(issues))
            params = {
                "state": state,
                "per_page": per_page,
                "page": page,
            }
            if labels:
                params["labels"] = ",".join(labels)

            response = client.get(f"/repos/{owner}/{repo_name}/issues", params=params)
            response.raise_for_status()
            page_items = response.json()
            if not page_items:
                break

            for issue in page_items:
                if not include_pull_requests and "pull_request" in issue:
                    continue
                issues.append(_format_github_issue(issue))
                if len(issues) >= limit:
                    break

            page += 1

    return issues


def _parse_github_repo(repo: str) -> tuple[str, str]:
    repo = repo.strip().removesuffix(".git")
    parsed = urlparse(repo)
    if parsed.netloc:
        repo = parsed.path.strip("/")

    parts = repo.split("/")
    if len(parts) < 2 or not parts[0] or not parts[1]:
        raise ValueError("GitHub repo must be in 'owner/repo' format or a GitHub repository URL")

    return parts[0], parts[1]


def _format_github_issue(issue: dict) -> dict:
    return {
        "number": issue.get("number"),
        "title": issue.get("title"),
        "state": issue.get("state"),
        "url": issue.get("html_url"),
        "labels": [label.get("name") for label in issue.get("labels", [])],
        "created_at": issue.get("created_at"),
        "updated_at": issue.get("updated_at"),
        "author": (issue.get("user") or {}).get("login"),
        "comments": issue.get("comments"),
        "body": issue.get("body"),
    }

def sample_fetch_github_issues():
    issues = fetch_github_issues("surrealdb/surrealdb", limit=10)
    for issue in issues:
        print(f"#{issue['number']} {issue['title']}")