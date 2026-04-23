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


    ollama_model = "gemma4:26b"
    llm = ChatOllama(model=ollama_model, temperature=0)

    messages = [
        SystemMessage(content=render_markdown("PAPER_SUMMARY.md")),
        HumanMessage(content=read_pdf(str(_RAW_PAPER_HOME / paper_path)))
    ]

    ret = llm.invoke(messages)
    with open(_SUMMARY_PAPER_HOME / f"{paper_name}.md", "w") as f:
        f.write(ret.content)