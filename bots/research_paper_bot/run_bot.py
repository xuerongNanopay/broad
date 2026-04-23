from bots import ROBOT_JOURNAL_HOME
_JOURNAL_HOME = ROBOT_JOURNAL_HOME / "research_paper_bot"
_RAW_PAPER_HOME = _JOURNAL_HOME / "paper"
_SUMMARY_PAPER_HOME = _JOURNAL_HOME / "summary"

def _init_dependencies():
    from utils.path import ensure_folder
    ensure_folder(_RAW_PAPER_HOME)
    ensure_folder(_SUMMARY_PAPER_HOME)

def run(
    model: str,
    paper: str
):
    _init_dependencies()

    _search_paper(paper)
    # from langchain_core.messages import SystemMessage, HumanMessage
    # from utils.markdown import render_markdown
    # from utils.pdf import read_pdf
    # import os

    # paper_path = "partially_materialized_view.pdf"
    # paper_name, _ = os.path.splitext(paper_path)

    # llm = _init_model(model)

    # messages = [
    #     SystemMessage(content=render_markdown("PAPER_SUMMARY.md")),
    #     HumanMessage(content=read_pdf(str(_RAW_PAPER_HOME / paper_path)))
    # ]

    # ret = llm.invoke(messages)
    # with open(_SUMMARY_PAPER_HOME / f"{paper_name}_{model}.md", "w") as f:
    #     f.write(ret.content)
    
    # print(ret.usage_metadata)
    

def _init_openai_model(model: str):
    from langchain_openai import ChatOpenAI
    from utils.env import load_env
    load_env()
    return ChatOpenAI(model=model)

def _init_ollama_model(model: str):
    from langchain_ollama import ChatOllama
    return ChatOllama(model=model)

def _init_model(model:str):
    if model.startswith("gpt"):
        return _init_openai_model(model)
    else:
        return _init_ollama_model(model)
    
def _search_paper(paper: str):
    from utils.www.arxiv import search_arvix_paper, ArvixQuery
    temp = "A-MEM: Agentic Memory for LLM Agents"

    query: ArvixQuery = {
        "ids": [paper]
    }

    search_arvix_paper(query)

def is_arxiv_id(s: str) -> bool:
    import re
    pattern = r'^(?:arXiv:)?(?:(?:\d{4}\.\d{4,5})|(?:[a-z-]+(?:\.[A-Z]{2})?/\d{7}))(?:v\d+)?$'
    return re.fullmatch(pattern, s) is not None