from bots import ROBOT_JOURNAL_HOME
_JOURNAL_HOME = ROBOT_JOURNAL_HOME / "research_paper_bot"
_RAW_PAPER_HOME = _JOURNAL_HOME / "paper"
_SUMMARY_PAPER_HOME = _JOURNAL_HOME / "summary"

def _init_dependencies():
    from utils.path import ensure_folder
    ensure_folder(_RAW_PAPER_HOME)
    ensure_folder(_SUMMARY_PAPER_HOME)

from datetime import date

def run(
    model: str,
    paper: str,
    limit: int,
    date_range: tuple[date, date] | None,
    is_analyze: bool,
):
    from .state import ArxivStore
    arxiv_store = ArxivStore()


    papers = _search_paper(paper, limit, date_range)
    print(f"total find: {len(papers)}")
    for r in papers:
        arxiv_store.upsert_one(r)
    return

    for r in papers:
        print(r.to_json(pretty=True))
    
    # TODO: paper filter(duplicate remove, unneed paper)
    if not is_analyze:
        return

    if len(papers) != 1:
        print("Can't download multiple paper")

    paper = papers[0]
    paper_path = paper.save_pdf_to(str(_RAW_PAPER_HOME), f"{_format_paper_title(paper.title)}.pdf");
    _analyze_paper(model, paper_path=paper_path, result_path=str(_SUMMARY_PAPER_HOME / f"{_format_paper_title(paper.title)}_{model}.md"))
    

def _init_openai_model(model: str):
    from langchain_openai import ChatOpenAI
    from utils.env import load_env
    load_env()
    return ChatOpenAI(model=model, temperature=0)

def _init_ollama_model(model: str):
    from langchain_ollama import ChatOllama
    return ChatOllama(model=model, base_url="http://localhost:11434", temperature=0)

def _init_model(model:str):
    if model.startswith("gpt"):
        return _init_openai_model(model)
    else:
        return _init_ollama_model(model)

def _analyze_paper(model: str, paper_path: str, result_path: str):
    from langchain_core.messages import SystemMessage, HumanMessage
    from utils.markdown import render_markdown
    from utils.pdf import read_pdf

    llm = _init_model(model)

    messages = [
        SystemMessage(content=render_markdown("PAPER_SUMMARY.md")),
        HumanMessage(content=read_pdf(paper_path))
    ]
    ret = llm.invoke(messages)
    with open(result_path, "w") as f:
        f.write(ret.content)

def _search_paper(paper: str, limit: int, date_range):
    from utils.www.arxiv import search_arvix_paper, ArvixQuery, ArxivCategory, ArxivOrder

    query: ArvixQuery = {}
    order = ArxivOrder.MOST_RELEVANT
    if _is_arxiv_id(paper):
        query["ids"] = [paper]
    elif paper.startswith("title:"):
        query["title"] = paper.lstrip("title:")
    elif paper in ArxivCategory._value2member_map_:
        query["category"] = ArxivCategory(paper)
        order = ArxivOrder.NEWEST
    else:
        query["exact_titles"] = [paper]

    query["date_ranges"] = date_range

    rets = search_arvix_paper(query, sort_by=order, max_results=limit)

    return rets

def _is_arxiv_id(s: str) -> bool:
    import re
    pattern = r'^(?:arXiv:)?(?:(?:\d{4}\.\d{4,5})|(?:[a-z-]+(?:\.[A-Z]{2})?/\d{7}))(?:v\d+)?$'
    return re.fullmatch(pattern, s) is not None

def _format_paper_title(origin: str) -> str:
    origin = origin.lower()
    import re
    return f"{re.sub(r"\s+", "_", origin.strip())}"