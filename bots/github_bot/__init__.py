"""Github AI agent"""
import typer

github_bot = typer.Typer(
    name="Github Agent",
    # context_settings={"help_option_names": ["-h", "--help"]},
    help="GitHub AI Agent",
    no_args_is_help=True,
)