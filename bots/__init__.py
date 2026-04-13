"""A collection of AI agents"""
import typer

app_bots = typer.Typer(
    name="AI agents",
    help="A collection of AI agents.",
    no_args_is_help=True,
)

from bots.github_bot import github_bot
app_bots.add_typer(github_bot, name="github_bot")