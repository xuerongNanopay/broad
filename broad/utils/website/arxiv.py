from typing import TypedDict, List
import arxiv

from enum import StrEnum, Enum

class ArxivCategory(StrEnum):
    AI = "cs.AI" # Artificial Intelligence)
    DB = "cs.DB" # Databases
    DC = "cs.DC" # Distributed, Parallel, and Cluster Computing
    NE = "cs.NE" # Neural and Evolutionary Computing
    CL = "cs.CL" # Computation and Language(LLM)
    LG = "cs.LG" # Machine Learning

class ArvixQuery(TypedDict):
    category: ArxivCategory = None
    # keywords: List[str] = []
    exact_titles: List[str] = []
    title: str = ""
    # exact_titles: List[str] = []

class ArxivOrder(Enum):
    NEWEST = 1
    MOST_RELEVANT = 2
    LAST_UPDATE = 3

_order_mapping = {
    ArxivOrder.NEWEST: arxiv.SortCriterion.SubmittedDate,
    ArxivOrder.MOST_RELEVANT: arxiv.SortCriterion.Relevance,
    ArxivOrder.LAST_UPDATE: arxiv.SortCriterion.LastUpdatedDate
}

def search_arvix_paper(
        query: str|ArvixQuery,
        *, 
        max_results: int = 10,
        sort_by: ArxivOrder = ArxivOrder.MOST_RELEVANT
    ):
    client = arxiv.Client()
    query = query if not isinstance(query, dict) else _format_query(query)
    print(query)
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=_order_mapping[sort_by],
        sort_order = arxiv.SortOrder.Descending
    )
    results = client.results(search)

    for result in results:
        print(result.title)
        print(result.entry_id)
        print(result.summary)
        print(result.published)
        print("---")

def _format_query(query: ArvixQuery) -> str:
    l = []

    if query.get("category"):
        l.append(f"cat:{str(query["category"])}")

    # if query["keywords"]:
    #     l.append(" AND ".join(query['keywords']))

    if query.get("title"):
        l.append(" AND ".join(f'ti:"{k}"' for k in query["title"].split(",")))
    
    if query.get("exact_titles"):
        l.append(" OR ".join(f'ti:"{k}"' for k in query["exact_titles"]))
        
    return " ".join(l)
# def download_paper(path: Path):
#     pass