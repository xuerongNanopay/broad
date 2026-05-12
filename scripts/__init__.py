from pathlib import Path
import runpy
import sys
from typing import Any

import typer

SCRIPTS_DIR = Path(__file__).resolve().parent

script_cli = typer.Typer(
    name="Execute script",
    help="Executing scripts that under scripts module"
)


def run_script(script_name: str, args: list[str] | None = None, *, scripts_dir: Path = SCRIPTS_DIR) -> dict[str, Any]:
    script_path = _script_path(script_name, scripts_dir)
    old_argv = sys.argv[:]

    try:
        sys.argv = [str(script_path), *(args or [])]
        return runpy.run_path(str(script_path), run_name="__main__")
    finally:
        sys.argv = old_argv


@script_cli.callback(
    invoke_without_command=True,
    context_settings={
        "allow_extra_args": True,
        "ignore_unknown_options": True,
    },
)
def invoke_script(ctx: typer.Context, script_name: str):
    run_script(script_name, list(ctx.args))


def _script_path(script_name: str, scripts_dir: Path) -> Path:
    name = script_name if script_name.endswith(".py") else f"{script_name}.py"
    path = Path(name)
    if path.name != name:
        raise ValueError(f"Invalid script name: {script_name!r}")

    script_path = scripts_dir / name
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")
    if not script_path.is_file():
        raise ValueError(f"Script path is not a file: {script_path}")

    return script_path


__all__ = ["script_cli"]
