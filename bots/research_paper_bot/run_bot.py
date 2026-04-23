from bots import ROBOT_JOURNAL_HOME
_JOURNAL_HOME = ROBOT_JOURNAL_HOME / "research_paper_bot"
_RAW_PAPER_HOME = _JOURNAL_HOME / "paper"
_SUMMARY_PAPER_HOME = _JOURNAL_HOME / "summary"

def run():
    from langchain_ollama import ChatOllama
    from langchain_core.messages import SystemMessage, HumanMessage
    from utils.markdown import render_markdown
    from utils.pdf import read_pdf
    import os

    paper_path = "partially_materialized_view.pdf"
    paper_name, _ = os.path.splitext(paper_path)


    model = "gemma4:26b"
    # model = "gpt-5.4-nano"
    llm = _init_model(model)

    messages = [
        SystemMessage(content=render_markdown("PAPER_SUMMARY.md")),
        HumanMessage(content=read_pdf(str(_RAW_PAPER_HOME / paper_path)))
    ]

    ret = llm.invoke(messages)
    with open(_SUMMARY_PAPER_HOME / f"{paper_name}_{model}.md", "w") as f:
        f.write(ret.content)
    
    print(ret.usage_metadata)
    

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