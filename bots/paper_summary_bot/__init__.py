"""PAPER SUMMARY AI agent"""
import typer

paper_summary_bot = typer.Typer(
    name="PAPER SUMMARY Agent",
    # context_settings={"help_option_names": ["-h", "--help"]},
    help="PAPER SUMMARY AI Agent",
    # no_args_is_help=True,
)

@paper_summary_bot.callback(invoke_without_command=True)
def _run_paper_summary_bot(
    short: bool = typer.Option(
        False,
        "--short",
        help="Short Running"
    )
):
    _run()

def _run():
    print("Summary mamer")