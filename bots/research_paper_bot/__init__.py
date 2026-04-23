import typer

research_paper_bot = typer.Typer(
    name="PAPER SUMMARY Agent",
    context_settings={"help_option_names": ["-h", "--help"]},
    help="""
    Search and download paper from arxiv, and summarize the paper.
    """,
    # no_args_is_help=True,
)

@research_paper_bot.callback(invoke_without_command=True)
def _run_research_paper_bot(
    model: str = typer.Option(
        "qwen3.6:35b",
        "--model",
        "-m",
        help="LLM Model, Eg: gemma4:26b, qwen3.6:35b, gpt-5.4-nano"
    ),
    paper: str = typer.Option(
        ...,
        "--paper",
        "-p",
        help="""
        paper id or paper name
        """
    )
):
    from .run_bot import run
    run(model.strip(), paper.strip())

def _run():
    from .run_bot import run
    run()