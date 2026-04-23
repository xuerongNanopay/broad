"""A collection of AI robots"""
import typer

bots = typer.Typer(
    name="AI robots",
    help="A collection of AI robots.",
    no_args_is_help=True,
)

from bots.github_bot import github_bot
bots.add_typer(github_bot, name="github_bot")

from bots.wiki_bot import wiki_bot
bots.add_typer(wiki_bot, name="wiki_bot")

from bots.research_paper_bot import research_paper_bot
bots.add_typer(research_paper_bot, name="research_paper_bot")

from broad.utils.path import develop_journal_home

ROBOT_JOURNAL_HOME = develop_journal_home() / "bots"