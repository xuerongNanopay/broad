import asyncio
import json
import os
import sys
from typing import Any

import httpx

from utils.env import load_env


OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"


async def main():
    prompt = sys.argv[1] if len(sys.argv) > 1 else "Wirte a welcome sentense to a friend."
    model = sys.argv[2] if len(sys.argv) > 2 else "gpt-5.4-mini-2026-03-17"

    load_env()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required.")

    payload = {
        "model": model,
        "input": [
            {
                "role": "developer",
                "content": "Talk like a professor."
            },
            {"role": "user", "content": prompt},
        ],
        "max_output_tokens": 256,
    }

    async with httpx.AsyncClient(timeout=60) as client:
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
    print("\nRaw response:")
    print(json.dumps(
        data,
        indent=2,
        ensure_ascii=False,
        default=str,
    ))


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
