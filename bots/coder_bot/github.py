from tools.repo import GitHubRepoExplorer, fetch_github_issues


def sample_fetch_github_issues():
    issues = fetch_github_issues("surrealdb/surrealdb", limit=1)
    for issue in issues:
        print(f"#{issue['number']} {issue['title']}")


def sample_explore_github_repo():
    explorer = GitHubRepoExplorer("surrealdb/surrealdb")
    summary = explorer.summary()

    repo = summary["repo"]
    print(f"{repo['full_name']}: {repo['description']}")
    print(f"stars={repo['stars']} forks={repo['forks']} open_issues={repo['open_issues']}")
    print(f"languages={summary['languages']}")

    print("recent open issues:")
    for issue in summary["recent_open_issues"]:
        print(f"#{issue['number']} {issue['title']}")
