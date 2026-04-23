from typing import TypedDict, List
import arxiv

import re

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
    exact_titles: str|List[str] = []
    title: str|None = None
    ids: List[str]|None = None
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
        arvix_query: str|ArvixQuery,
        *, 
        max_results: int = 10,
        sort_by: ArxivOrder = ArxivOrder.MOST_RELEVANT
    ):
    client = arxiv.Client()
    query = arvix_query if not isinstance(arvix_query, dict) else _format_query(arvix_query)
    ids = arvix_query["ids"] if isinstance(arvix_query, dict) and "ids" in arvix_query else None
    sort_by = _order_mapping[sort_by];

    search = arxiv.Search(
        query=query,
        id_list=ids,
        max_results=max_results,
        sort_by=sort_by,
        sort_order = arxiv.SortOrder.Descending
    )
    results = client.results(search)

    for result in results:
        print(result.title)
        print(result.entry_id)
        print(result.summary)
        print(result.published)
        print("---")

def download_arxiv_pdf_paper(url: str, folder: str, filename: str) -> str:
    paper_id = _parse_paper_id(url)
    client = arxiv.Client()
    search = arxiv.Search(id_list=[paper_id])
    paper = next(client.results(search))
    path = paper.download_pdf(dirpath=folder, filename=_format_paper_filename(filename))
    return path

def _format_paper_filename(origin: str) -> str:
    return f"{re.sub(r"\s+", "_", origin.strip())}.pdf"

def _format_query(query: ArvixQuery) -> str:
    l = []

    if query.get("category"):
        l.append(f"cat:{str(query["category"])}")

    # if query["keywords"]:
    #     l.append(" AND ".join(query['keywords']))

    if query.get("title"):
        l.append(" AND ".join(f'ti:"{k}"' for k in query["title"].split(",")))
    
    if query.get("exact_titles"):
        if isinstance(query.get("exact_titles"), list):
            l.append(" OR ".join(f'ti:"{k}"' for k in query["exact_titles"]))
        else:
            l.append(f'ti:"{query.get("exact_titles")}"')
        
    return " ".join(l)

def _parse_paper_id(url: str) -> str:
    return url.split("/")[-1] 
# def download_paper(path: Path):
#     pass