from pathlib import Path
import runpy
import sys
from typing import Any

import typer

DEMO_DIR = Path(__file__).resolve().parent

demo_cli = typer.Typer(
    name="Run demo",
    help="Run demos under the demo module",
    context_settings={
        "allow_extra_args": True,
        "ignore_unknown_options": True,
    },
)


def run_demo(demo_name: str, args: list[str] | None = None, *, demo_dir: Path = DEMO_DIR) -> dict[str, Any]:
    demo_path = _demo_path(demo_name, demo_dir)
    old_argv = sys.argv[:]

    try:
        sys.argv = [str(demo_path), *(args or [])]
        return runpy.run_path(str(demo_path), run_name="__main__")
    finally:
        sys.argv = old_argv


@demo_cli.callback(
    invoke_without_command=True,
)
def invoke_demo(demo_name: str, args: list[str] | None = typer.Argument(None)):
    run_demo(demo_name, args or [])


def _demo_path(demo_name: str, demo_dir: Path) -> Path:
    path = Path(demo_name)
    if path.name != demo_name:
        raise ValueError(f"Invalid demo name: {demo_name!r}")

    candidates = []
    if demo_name.endswith(".py"):
        candidates.append(demo_dir / demo_name)
    else:
        candidates.append(demo_dir / f"{demo_name}.py")
        candidates.append(demo_dir / demo_name / "__init__.py")

    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate

    raise FileNotFoundError(f"Demo not found: {demo_name!r}")


__all__ = ["demo_cli", "run_demo"]
