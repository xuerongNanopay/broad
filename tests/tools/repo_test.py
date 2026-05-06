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


def test_github_repo_languages():
    from pprint import pprint
    from tools.repo.github import GitHubRepoExplorer

    explorer = GitHubRepoExplorer("surrealdb/surrealdb")

    pprint(explorer.languages())


def test_github_repo_main_language():
    from tools.repo.github import GitHubRepoExplorer

    explorer = GitHubRepoExplorer("surrealdb/surrealdb")

    print(explorer.main_language())


def test_github_repo_file_content_metadata():
    from pprint import pprint
    from tools.repo.github import GitHubRepoExplorer

    explorer = GitHubRepoExplorer("surrealdb/surrealdb")

    pprint(explorer.metadata("README.md"))


def test_download_github_repo_zip():
    from tools.repo.github import GitHubRepoExplorer

    explorer = GitHubRepoExplorer("surrealdb/surrealdb")

    print(explorer.download_zip("/tmp/surrealdb.zip"))


def test_download_and_uncompress_github_repo_zip():
    from tools.repo.github import GitHubRepoExplorer

    explorer = GitHubRepoExplorer("surrealdb/surrealdb")

    zip_path = explorer.download_zip("/tmp/surrealdb.zip")
    print(explorer.uncompress_zip(zip_path, "/tmp/surrealdb", keep_repo_folder=False))


def test_download_github_repo():
    from tools.repo.github import GitHubRepoExplorer

    explorer = GitHubRepoExplorer("surrealdb/surrealdb")

    print(explorer.download("/tmp/surrealdb"))
