"""CLI module for broad."""
import typer

app = typer.Typer(
    name="broad",
    # context_settings={"help_option_names": ["-h", "--help"]},
    help="Broad - AI Robots.",
    no_args_is_help=True,
)

from bots import app_bots
app.add_typer(app_bots, name="robots")

@app.command()
def robots(name: str):
    print(f"robots")
