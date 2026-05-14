import asyncio
import json
import sys

from openai import AsyncOpenAI
from openai.types.responses import Response

from utils.env import load_env


async def main():
    prompt = sys.argv[1] if len(sys.argv) > 1 else "Write a friendly hello-world sentence."
    model = sys.argv[2] if len(sys.argv) > 2 else "gpt-5.4-mini-2026-03-17"

    load_env()
    client = AsyncOpenAI()
    response: Response = await client.responses.create(
        model=model,
        input=[
            {"role": "user", "content": prompt},
        ],
        max_output_tokens=256,
    )

    print(response.output_text)
    print("\nObservation:")
    print(json.dumps(
        {
            "id": getattr(response, "id", None),
            "model": getattr(response, "model", model),
            "output": _dump(getattr(response, "output", None)),
            "status": getattr(response, "status", None),
            "usage": _dump(getattr(response, "usage", None)),
        },
        indent=2,
        ensure_ascii=False,
        default=str,
    ))


def _dump(value):
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, list):
        return [_dump(item) for item in value]
    if isinstance(value, dict):
        return {key: _dump(item) for key, item in value.items()}
    return value


if __name__ == "__main__":
    asyncio.run(main())
