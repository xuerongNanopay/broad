from broad.utils.path import ensure_folder

from .. import ROBOT_JOURNAL_HOME

WIKI_JOURNAL_HOME = ROBOT_JOURNAL_HOME / "wiki_bot"
WIKI_RAW_FOLDER = WIKI_JOURNAL_HOME / "raw"


def init():
    ensure_folder(WIKI_RAW_FOLDER)

def run():
    print("run the wiki")
    # init()
    from broad.utils.website.arxiv import search_arvix_paper, ArxivCategory
    # search_arvix_paper("ai")
    search_arvix_paper(
        {
            "category": ArxivCategory.AI,
            "keywords": ["GenIR"]
        }
    )