"""CLI module for broad."""
import typer

app = typer.Typer(
    name="broad",
    # context_settings={"help_option_names": ["-h", "--help"]},
    help="Broad - AI Robots.",
    no_args_is_help=True,
)


@app.callback()
def main():
    pass

    
# def app():
#     print("CLI entry")