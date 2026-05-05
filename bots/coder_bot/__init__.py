"""Coder AI agent"""
import typer

coder_bot = typer.Typer(
    name="Coder Agent",
    # context_settings={"help_option_names": ["-h", "--help"]},
    help="Coder AI Agent",
    # no_args_is_help=True,
)

@coder_bot.callback(invoke_without_command=True)
def _run_coder_bot(
    short: bool = typer.Option(
        False,
        "--short",
        help="Short Running"
    )
):
    print(f"This is coder bot: {short}")


