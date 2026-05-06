from os import getenv
from urllib.parse import urlparse

import httpx


class GitHubRepoExplorer:
    def __init__(
        self,
        repo: str,
        token: str | None = None,
        base_url: str = "https://api.github.com",
        timeout: float = 30,
    ):
        from utils.env import load_env

        load_env()

        self.owner, self.repo = parse_github_repo(repo)
        self.base_url = base_url
        self.timeout = timeout
        self.token = token or getenv("GITHUB_TOKEN")

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.repo}"

    def repo_info(self) -> dict:
        data = self._get(f"/repos/{self.full_name}")
        return {
            "id": data.get("id"),
            "name": data.get("name"),
            "full_name": data.get("full_name"),
            "description": data.get("description"),
            "url": data.get("html_url"),
            "default_branch": data.get("default_branch"),
            "language": data.get("language"),
            "stars": data.get("stargazers_count"),
            "forks": data.get("forks_count"),
            "open_issues": data.get("open_issues_count"),
            "license": (data.get("license") or {}).get("spdx_id"),
            "created_at": data.get("created_at"),
            "updated_at": data.get("updated_at"),
            "pushed_at": data.get("pushed_at"),
        }

    def issues(
        self,
        state: str = "open",
        labels: list[str] | None = None,
        limit: int = 30,
        include_pull_requests: bool = False,
    ) -> list[dict]:
        params = {"state": state}
        if labels:
            params["labels"] = ",".join(labels)

        issues: list[dict] = []
        page = 1

        with httpx.Client(base_url=self.base_url, headers=self._headers(), timeout=self.timeout) as client:
            while len(issues) < limit:
                page_params = {
                    **params,
                    "per_page": 100,
                    "page": page,
                }
                response = client.get(f"/repos/{self.full_name}/issues", params=page_params)
                response.raise_for_status()
                page_items = response.json()
                if not page_items:
                    break

                for issue in page_items:
                    if not include_pull_requests and "pull_request" in issue:
                        continue
                    issues.append(_format_issue(issue))
                    if len(issues) >= limit:
                        break

                page += 1

        return issues

    def pull_requests(self, state: str = "open", limit: int = 30) -> list[dict]:
        pulls = self._paginate(f"/repos/{self.full_name}/pulls", params={"state": state}, limit=limit)
        return [_format_pull_request(pull) for pull in pulls[:limit]]

    def branches(self, limit: int = 100) -> list[dict]:
        branches = self._paginate(f"/repos/{self.full_name}/branches", limit=limit)
        return [
            {
                "name": branch.get("name"),
                "sha": (branch.get("commit") or {}).get("sha"),
                "protected": branch.get("protected"),
            }
            for branch in branches[:limit]
        ]

    def tags(self, limit: int = 100) -> list[dict]:
        tags = self._paginate(f"/repos/{self.full_name}/tags", limit=limit)
        return [
            {
                "name": tag.get("name"),
                "sha": (tag.get("commit") or {}).get("sha"),
                "zipball_url": tag.get("zipball_url"),
                "tarball_url": tag.get("tarball_url"),
            }
            for tag in tags[:limit]
        ]

    def contributors(self, limit: int = 30) -> list[dict]:
        contributors = self._paginate(f"/repos/{self.full_name}/contributors", limit=limit)
        return [
            {
                "login": contributor.get("login"),
                "url": contributor.get("html_url"),
                "contributions": contributor.get("contributions"),
            }
            for contributor in contributors[:limit]
        ]

    def languages(self) -> dict[str, int]:
        return self._get(f"/repos/{self.full_name}/languages")

    def readme(self) -> dict:
        data = self._get(f"/repos/{self.full_name}/readme")
        return {
            "name": data.get("name"),
            "path": data.get("path"),
            "sha": data.get("sha"),
            "download_url": data.get("download_url"),
            "html_url": data.get("html_url"),
        }

    def contents(self, path: str = "", ref: str | None = None) -> list[dict] | dict:
        params = {"ref": ref} if ref else None
        data = self._get(f"/repos/{self.full_name}/contents/{path.strip('/')}", params=params)
        if isinstance(data, list):
            return [_format_content(item) for item in data]
        return _format_content(data)

    def tree(
        self,
        ref: str | None = None,
        recursive: bool = True,
        ignore_paths: list[str] | None = None,
    ) -> list[dict]:
        ref = ref or self.repo_info()["default_branch"]
        params = {"recursive": "1"} if recursive else None
        data = self._get(f"/repos/{self.full_name}/git/trees/{ref}", params=params)
        return [
            {
                "path": item.get("path"),
                "type": item.get("type"),
                "sha": item.get("sha"),
                "size": item.get("size"),
                "url": item.get("url"),
            }
            for item in data.get("tree", [])
            if not _is_ignored_path(item.get("path"), ignore_paths)
        ]

    def is_tree_truncated(self, ref: str | None = None, recursive: bool = True) -> bool:
        ref = ref or self.repo_info()["default_branch"]
        params = {"recursive": "1"} if recursive else None
        data = self._get(f"/repos/{self.full_name}/git/trees/{ref}", params=params)
        return bool(data.get("truncated"))

    def summary(self) -> dict:
        info = self.repo_info()
        return {
            "repo": info,
            "languages": self.languages(),
            "branches": self.branches(limit=10),
            "recent_open_issues": self.issues(limit=10),
        }

    def _get(self, path: str, params: dict | None = None):
        with httpx.Client(base_url=self.base_url, headers=self._headers(), timeout=self.timeout) as client:
            response = client.get(path, params=params)
            response.raise_for_status()
            return response.json()

    def _paginate(self, path: str, params: dict | None = None, limit: int = 30) -> list[dict]:
        items: list[dict] = []
        page = 1

        with httpx.Client(base_url=self.base_url, headers=self._headers(), timeout=self.timeout) as client:
            while len(items) < limit:
                page_params = {
                    **(params or {}),
                    "per_page": min(100, limit - len(items)),
                    "page": page,
                }
                response = client.get(path, params=page_params)
                response.raise_for_status()
                page_items = response.json()
                if not page_items:
                    break

                items.extend(page_items)
                page += 1

        return items[:limit]

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers


def fetch_github_issues(
    repo: str,
    state: str = "open",
    labels: list[str] | None = None,
    limit: int = 30,
    token: str | None = None,
    include_pull_requests: bool = False,
) -> list[dict]:
    explorer = GitHubRepoExplorer(repo, token=token)
    return explorer.issues(
        state=state,
        labels=labels,
        limit=limit,
        include_pull_requests=include_pull_requests,
    )


def parse_github_repo(repo: str) -> tuple[str, str]:
    repo = repo.strip().removesuffix(".git")
    parsed = urlparse(repo)
    if parsed.netloc:
        repo = parsed.path.strip("/")

    parts = repo.split("/")
    if len(parts) < 2 or not parts[0] or not parts[1]:
        raise ValueError("GitHub repo must be in 'owner/repo' format or a GitHub repository URL")

    return parts[0], parts[1]


def _is_ignored_path(path: str | None, ignore_paths: list[str] | None) -> bool:
    if not path or not ignore_paths:
        return False

    normalized_path = path.strip("/")
    for ignore_path in ignore_paths:
        normalized_ignore = ignore_path.strip("/")
        if not normalized_ignore:
            continue
        if normalized_path == normalized_ignore or normalized_path.startswith(f"{normalized_ignore}/"):
            return True

    return False


def _format_issue(issue: dict) -> dict:
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


def _format_pull_request(pull: dict) -> dict:
    return {
        "number": pull.get("number"),
        "title": pull.get("title"),
        "state": pull.get("state"),
        "url": pull.get("html_url"),
        "draft": pull.get("draft"),
        "created_at": pull.get("created_at"),
        "updated_at": pull.get("updated_at"),
        "author": (pull.get("user") or {}).get("login"),
        "base": (pull.get("base") or {}).get("ref"),
        "head": (pull.get("head") or {}).get("ref"),
    }


def _format_content(item: dict) -> dict:
    return {
        "name": item.get("name"),
        "path": item.get("path"),
        "type": item.get("type"),
        "sha": item.get("sha"),
        "size": item.get("size"),
        "download_url": item.get("download_url"),
        "html_url": item.get("html_url"),
    }
