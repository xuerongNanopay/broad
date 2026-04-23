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
            Accept three types of string: \n
                1. Arvix Id(eg: 2604.20117|2604.20117v1) \n
                    - eg: -p 2604.20117 \n
                2. Paper Title(eg: "To Know is to Construct: Schema-Constrained Generation for Agent Memory") \n
                    - eg: -p "To Know is to Construct: Schema-Constrained Generation for Agent Memory" \n
                3. Categories \n
                    - "cs.AI": Artificial Intelligence) \n
                    - "cs.DB": Databases \n
                    - "cs.DC": Distributed, Parallel, and Cluster Computing \n
                    - "cs.NE": Neural and Evolutionary Computing \n
                    - "cs.CL": Computation and Language(LLM) 
                    - "cs.LG": Machine Learning \n
        """
    ),
    limit: int = typer.Option(
        10,
        "--limit",
        "-l",
        help="Maximum paper to be return"
    )
):
    from .run_bot import run
    run(model.strip(), paper.strip(), max(1, limit))

def _run():
    from .run_bot import run
    run()