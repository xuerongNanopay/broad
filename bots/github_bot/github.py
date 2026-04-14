import httpx

def fetch_repositories():
    url = "https://api.github.com/search/repositories"

    params = {
        "q": "stars:>1",
        "sort": "stars",
        "order": "desc",
        "per_page": 1
    }

    with httpx.Client() as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
    
    print(data)
    print(len(data["items"]))

    for repo in data["items"]:
        print(repo["full_name"], repo["stargazers_count"])

def tt():
    fetch_repositories()