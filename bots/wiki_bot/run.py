from pathlib import Path

from broad.utils.path import ensure_folder

from .. import ROBOT_JOURNAL_HOME

WIKI_JOURNAL_HOME = ROBOT_JOURNAL_HOME / "wiki_bot"
WIKI_RAW_FOLDER = WIKI_JOURNAL_HOME / "raw"
WIKI_PAPER_FOLDER = WIKI_RAW_FOLDER / "paper"


def init():
    ensure_folder(WIKI_RAW_FOLDER)
    ensure_folder(WIKI_PAPER_FOLDER)

def run():
    print("run the wiki")
    # init()
    from broad.utils.website.arxiv import search_arvix_paper, ArxivCategory, download_arxiv_pdf_paper
    # search_arvix_paper("ai")
    search_arvix_paper(
        {
            # "category": ArxivCategory.AI,
            "exact_titles": "A-MEM: Agentic Memory for LLM Agents"
            # "title": "Agentic, Memory, for LLM Agents"
        },
    )
    path = download_arxiv_pdf_paper("http://arxiv.org/abs/2502.12110v11", WIKI_RAW_FOLDER, "A-MEM: Agentic Memory for LLM Agents")

    raw_pdf = extract_pdf_text(path)
    print(raw_pdf)
    print(len(raw_pdf))


def extract_pdf_text(path: str) -> str:
    try:
        from pypdf import PdfReader
        reader = PdfReader(path)
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return "\n".join(pages)
    except Exception:
        return ""

