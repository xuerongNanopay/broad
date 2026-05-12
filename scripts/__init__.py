import typer

script_cli = typer.Typer(
    name="Execute script",
    help="Executing scripts that under scripts module"
)

@script_cli.callback(invoke_without_command=True)
def invoke_script(script_name: str):
    print(script_name)

__all__ = ["script_cli"]