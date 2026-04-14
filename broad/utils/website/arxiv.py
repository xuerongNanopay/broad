from typing import TypedDict, List
import arxiv

from enum import StrEnum

class ArxivCategory(StrEnum):
    AI = "cs.AI" # Artificial Intelligence)
    DB = "cs.DB" # Databases
    DC = "cs.DC" # Distributed, Parallel, and Cluster Computing
    NE = "cs.NE" # Neural and Evolutionary Computing
    CL = "cs.CL" # Computation and Language(LLM)
    LG = "cs.LG" # Machine Learning

class ArvixQuery(TypedDict):
    category: ArxivCategory
    keywords: List[str] = []

def search_arvix_paper(query: str|ArvixQuery, *, max_results: int = 10):
    client = arxiv.Client()
    query = query if not isinstance(query, dict) else _format_query(query)
    print(query)
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )
    results = client.results(search)

    for result in results:
        print(result.title)
        print(result.entry_id)
        print(result.summary)
        print(result.published)
        print("---")

def _format_query(query: ArxivCategory) -> str:
    if not query["category"]:
        return f"cat:{str(query["category"])}"
    else:
        return f"cat:{str(query["category"])} AND {" AND ".join(query['keywords'])}"
# def download_paper(path: Path):
#     pass