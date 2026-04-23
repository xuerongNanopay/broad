"""CLI module for broad."""
import typer

app = typer.Typer(
    name="broad",
    # context_settings={"help_option_names": ["-h", "--help"]},
    help="Broad - AI Robots.",
    no_args_is_help=True,
)

from bots import bots
app.add_typer(bots, name="bots")

@app.command()
def bots(name: str):
    print(f"bots")
