import argparse
import asyncio
import json
import os
from typing import Any

import httpx

from utils.env import load_env


OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = "gpt-5.4-mini-2026-03-17"
DEFAULT_TEXT = (
    "Team sync moved to Friday, May 22, 2026 at 2:30 PM in room 4B. "
    "Ada should send the revised roadmap by Wednesday, May 20, and Lin should "
    "bring the launch metrics. This is high priority."
)

EVENT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "title": {
            "type": "string",
            "description": "Short event title.",
        },
        "date": {
            "type": "string",
            "description": "Event date in ISO 8601 YYYY-MM-DD format, or empty string if unknown.",
        },
        "start_time": {
            "type": "string",
            "description": "Event start time in 24-hour HH:MM format, or empty string if unknown.",
        },
        "location": {
            "type": "string",
            "description": "Event location, or empty string if unknown.",
        },
        "priority": {
            "type": "string",
            "enum": ["low", "medium", "high"],
        },
        "attendees": {
            "type": "array",
            "items": {"type": "string"},
            "description": "People explicitly mentioned as attendees or participants.",
        },
        "action_items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "owner": {
                        "type": "string",
                        "description": "Person responsible for the action item.",
                    },
                    "task": {
                        "type": "string",
                        "description": "Specific task to complete.",
                    },
                    "due_date": {
                        "type": "string",
                        "description": "Due date in ISO 8601 YYYY-MM-DD format, or empty string if unknown.",
                    },
                },
                "required": ["owner", "task", "due_date"],
                "additionalProperties": False,
            },
        },
    },
    "required": [
        "title",
        "date",
        "start_time",
        "location",
        "priority",
        "attendees",
        "action_items",
    ],
    "additionalProperties": False,
}


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract structured event data with OpenAI Structured Outputs.",
    )
    parser.add_argument(
        "text",
        nargs="?",
        default=DEFAULT_TEXT,
        help="Unstructured text to extract. Defaults to a short meeting note.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"OpenAI model to use. Defaults to {DEFAULT_MODEL}.",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Also print the raw OpenAI response.",
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
                "content": (
                    "Extract event details from the user's note. "
                    "Use empty strings for unknown string fields and empty arrays "
                    "when no matching items are present."
                ),
            },
            {"role": "user", "content": args.text},
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "event_summary",
                "description": "Normalized event details extracted from unstructured text.",
                "strict": True,
                "schema": EVENT_SCHEMA,
            },
        },
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
    output_text = _response_text(data)
    if output_text is None:
        raise RuntimeError("OpenAI did not return output_text.")

    structured_event = json.loads(output_text)

    print(json.dumps(structured_event, indent=2, ensure_ascii=False))

    if args.raw:
        print("\nRaw response:")
        print(json.dumps(data, indent=2, ensure_ascii=False, default=str))


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
