import httpx

def fetch_repositories():
    url = "https://api.github.com/search/repositories"

    params = {
        "q": "stars:>1",
        "sort": "stars",
        "order": "desc",
        "per_page": 10
    }

    with httpx.Client() as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
    
    print(data)

def tt():
    fetch_repositories()