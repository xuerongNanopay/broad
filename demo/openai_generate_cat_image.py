import argparse
import asyncio
import base64
import os
from pathlib import Path
from typing import Any

import httpx

from utils.env import load_env


OPENAI_IMAGES_URL = "https://api.openai.com/v1/images/generations"
DEFAULT_MODEL = "gpt-image-1"
DEFAULT_PROMPT = (
    "A cozy, realistic orange tabby cat sitting on a sunny windowsill, "
    "soft morning light, detailed fur, warm home interior."
)
DEFAULT_OUTPUT = Path("demo/cat.png")


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a cat image with OpenAI and save it locally.",
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        default=DEFAULT_PROMPT,
        help="Image prompt to generate. Defaults to a cozy cat prompt.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output image path. Defaults to {DEFAULT_OUTPUT}.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"OpenAI image model to use. Defaults to {DEFAULT_MODEL}.",
    )
    parser.add_argument(
        "--size",
        default="1024x1024",
        choices=("1024x1024", "1024x1536", "1536x1024"),
        help="Generated image size.",
    )
    args = parser.parse_args()

    load_env()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required.")

    payload = {
        "model": args.model,
        "prompt": args.prompt,
        "size": args.size,
    }

    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            OPENAI_IMAGES_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()

        data = response.json()
        image = _first_image(data)
        image_bytes = await _image_bytes(client, image)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(image_bytes)

    print(f"Saved image to {args.output}")
    if image.get("revised_prompt"):
        print("\nRevised prompt:")
        print(image["revised_prompt"])


def _first_image(response: dict[str, Any]) -> dict[str, Any]:
    data = response.get("data")
    if not isinstance(data, list) or not data:
        raise RuntimeError("OpenAI did not return image data.")
    image = data[0]
    if not isinstance(image, dict):
        raise RuntimeError("OpenAI returned image data in an unexpected format.")
    return image


async def _image_bytes(client: httpx.AsyncClient, image: dict[str, Any]) -> bytes:
    if image.get("b64_json"):
        return base64.b64decode(str(image["b64_json"]))

    if image.get("url"):
        response = await client.get(str(image["url"]))
        response.raise_for_status()
        return response.content

    raise RuntimeError("OpenAI response did not include b64_json or url image data.")


if __name__ == "__main__":
    asyncio.run(main())
