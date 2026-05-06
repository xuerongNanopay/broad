def test_github_repo_issues():
    from pprint import pprint
    from tools.repo.github import GitHubRepoExplorer

    explorer = GitHubRepoExplorer("surrealdb/surrealdb")

    issues = explorer.issues(limit=1)
    pprint(issues)



def test_github_repo_tree():
    from pprint import pprint
    from tools.repo.github import GitHubRepoExplorer

    explorer = GitHubRepoExplorer("surrealdb/surrealdb")

    tree = explorer.tree(ignore_paths=[".github", "target", "tests"])
    pprint(tree[:100])


def test_github_repo_tree_truncated():
    from tools.repo.github import GitHubRepoExplorer

    explorer = GitHubRepoExplorer("surrealdb/surrealdb")

    print(explorer.is_tree_truncated())
