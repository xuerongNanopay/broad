from bots import ROBOT_JOURNAL_HOME
_JOURNAL_HOME = ROBOT_JOURNAL_HOME / "paper_summary_bot"
# _RAW_PAPER_HOME = _JOURNAL_HOME / "paper"
# _SUMMARY_PAPER_HOME = _JOURNAL_HOME / "summary"

def run():
    from langchain_ollama import ChatOllama
    from langchain_core.prompts import ChatPromptTemplate
    from utils.markdown import render_markdown

    print(render_markdown("PAPER_SUMMARY.md"))
    # ollama_model = "gemma4:26b"
    # llm = ChatOllama(model=ollama_model, temperature=0)

    # prompt = ChatPromptTemplate.from_messages([
    #     ("system", "You are a senior database engineer."),
    #     ("user", "Explain {topic}")
    # ])

    # chain = prompt | llm
    # chain.invoke({"topic": "MVCC"})