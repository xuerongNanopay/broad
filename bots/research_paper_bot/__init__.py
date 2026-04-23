import typer

research_paper_bot = typer.Typer(
    name="PAPER SUMMARY Agent",
    # context_settings={"help_option_names": ["-h", "--help"]},
    help="PAPER SUMMARY AI Agent",
    # no_args_is_help=True,
)

@research_paper_bot.callback(invoke_without_command=True)
def _run_research_paper_bot(
    short: bool = typer.Option(
        False,
        "--short",
        help="Short Running"
    )
):
    _run()

def _run():
    from .run_bot import run
    run()