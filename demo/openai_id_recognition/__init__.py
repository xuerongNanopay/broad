import argparse
import asyncio
import base64
import mimetypes
import os
import sys
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.env import load_env


OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = "gpt-5.4-mini-2026-03-17"
DEFAULT_IMAGE = Path(__file__).with_name("driver_license.png")
SYSTEM_PROMPT = (
    "Describe this image. If it is a document, identify the document type and "
    "summarize visible fields. Redact personal identifiers and document numbers."
)


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Recognize and describe an image with the OpenAI Responses API.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"OpenAI model to use. Defaults to {DEFAULT_MODEL}.",
    )
    parser.add_argument(
        "--detail",
        choices=("auto", "low", "high"),
        default="auto",
        help="Image detail level. Defaults to auto.",
    )
    args = parser.parse_args()

    load_env()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required.")

    payload = {
        "model": args.model,
        "input": [
            {
                "role": "developer",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_image",
                        "image_url": _image_url(DEFAULT_IMAGE),
                        "detail": args.detail,
                    },
                ],
            },
        ],
        "max_output_tokens": 800,
    }

    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            OPENAI_RESPONSES_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()

    data = response.json()
    print(_response_text(data) or "")


def _image_url(image: Path) -> str:
    path = Path(image)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")

    mime_type = mimetypes.guess_type(path.name)[0] or "image/png"
    image_base64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{image_base64}"


def _response_text(response: dict[str, Any]) -> str | None:
    parts: list[str] = []
    for item in response.get("output") or []:
        if item.get("type") != "message":
            continue
        for content in item.get("content") or []:
            if content.get("type") == "output_text" and content.get("text") is not None:
                parts.append(str(content["text"]))

    if not parts:
        return None
    return "\n".join(parts)


if __name__ == "__main__":
    asyncio.run(main())
