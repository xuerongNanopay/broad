"""WIKI AI agent"""
import typer

wiki_bot = typer.Typer(
    name="WIKI Agent",
    # context_settings={"help_option_names": ["-h", "--help"]},
    help="WIKI AI Agent",
    # no_args_is_help=True,
)

@wiki_bot.callback(invoke_without_command=True)
def _run_wiki_bot(
    short: bool = typer.Option(
        False,
        "--short",
        help="Short Running"
    )
):
    from .run import run
    run()