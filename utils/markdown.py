from pathlib import Path
_MARKDOWNS_HOME = Path(__file__).resolve().parent.parent / "mds"

from jinja2 import Environment, FileSystemLoader
_env = Environment(
    loader=FileSystemLoader(str(_MARKDOWNS_HOME)),
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
)

from typing import Any

def render_markdown(name: str, **kwargs: Any) -> str:
    return _env.get_template(name).render(**kwargs)