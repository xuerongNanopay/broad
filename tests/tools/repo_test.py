def test_github_repo_issues():
    from pprint import pprint
    from tools.repo.github import GitHubRepoExplorer

    explorer = GitHubRepoExplorer("surrealdb/surrealdb")
    issues = explorer.issues(limit=1)

    pprint(issues)
