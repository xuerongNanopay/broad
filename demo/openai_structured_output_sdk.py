import argparse
import asyncio
import json
from typing import Literal

from openai import AsyncOpenAI
from pydantic import BaseModel, ConfigDict, Field

from utils.env import load_env


DEFAULT_MODEL = "gpt-5.4-mini-2026-03-17"
DEFAULT_TEXT = (
    "Team sync moved to Friday, May 22, 2026 at 2:30 PM in room 4B. "
    "Ada should send the revised roadmap by Wednesday, May 20, and Lin should "
    "bring the launch metrics. This is high priority."
)


class ActionItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    owner: str = Field(description="Person responsible for the action item.")
    task: str = Field(description="Specific task to complete.")
    due_date: str = Field(
        description="Due date in ISO 8601 YYYY-MM-DD format, or empty string if unknown.",
    )


class EventSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(description="Short event title.")
    date: str = Field(
        description="Event date in ISO 8601 YYYY-MM-DD format, or empty string if unknown.",
    )
    start_time: str = Field(
        description="Event start time in 24-hour HH:MM format, or empty string if unknown.",
    )
    location: str = Field(description="Event location, or empty string if unknown.")
    priority: Literal["low", "medium", "high"]
    attendees: list[str] = Field(
        description="People explicitly mentioned as attendees or participants.",
    )
    action_items: list[ActionItem]


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract structured event data with the OpenAI SDK.",
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
    client = AsyncOpenAI()

    response = await client.responses.parse(
        model=args.model,
        input=[
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
        text_format=EventSummary,
        max_output_tokens=800,
    )

    structured_event = response.output_parsed
    if structured_event is None:
        raise RuntimeError("OpenAI did not return parsed structured output.")

    print(structured_event.model_dump_json(indent=2))

    if args.raw:
        print("\nRaw response:")
        print(json.dumps(_dump(response), indent=2, ensure_ascii=False, default=str))


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
