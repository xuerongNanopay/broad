"""Github AI agent"""
import typer

github_bot = typer.Typer(
    name="Github Agent",
    # context_settings={"help_option_names": ["-h", "--help"]},
    help="GitHub AI Agent",
    # no_args_is_help=True,
)

@github_bot.callback(invoke_without_command=True)
def _run_github_bot(
    short: bool = typer.Option(
        False,
        "--short",
        help="Short Running"
    )
):
    print(f"This is github bot: {short}")
    from .run import run
    run()


