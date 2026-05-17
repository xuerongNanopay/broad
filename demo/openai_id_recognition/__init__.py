import argparse
import asyncio
import base64
import json
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
    "You are a strict OCR extraction engine for ID documents. Extract only "
    "text that is clearly visible in the image. Do not infer, normalize, "
    "correct, redact, or guess values. Use empty strings for unknown string "
    "fields and empty arrays when no matching text is visible."
)

ID_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "document_type": {
            "type": "string",
            "description": "Type of ID document, such as driver license or passport.",
        },
        "issuing_region": {
            "type": "string",
            "description": "Issuing country, state, province, or region.",
        },
        "full_name": {
            "type": "string",
            "description": "Full name shown on the ID.",
        },
        "date_of_birth": {
            "type": "string",
            "description": "Date of birth exactly as visible on the ID.",
        },
        "address": {
            "type": "string",
            "description": "Address exactly as visible on the ID.",
        },
        "id_number": {
            "type": "string",
            "description": "Visible ID or license number.",
        },
        "issue_date": {
            "type": "string",
            "description": "Issue date exactly as visible on the ID.",
        },
        "expiration_date": {
            "type": "string",
            "description": "Expiration date exactly as visible on the ID.",
        },
        "sex": {
            "type": "string",
            "description": "Sex or gender marker exactly as visible on the ID.",
        },
        "height": {
            "type": "string",
            "description": "Height exactly as visible on the ID.",
        },
        "license_class": {
            "type": "string",
            "description": "License class or category exactly as visible.",
        },
        "restrictions": {
            "type": "string",
            "description": "Restrictions exactly as visible.",
        },
        "endorsements": {
            "type": "string",
            "description": "Endorsements exactly as visible.",
        },
        "visible_text": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Other visible text snippets on the document.",
        },
        "confidence": {
            "type": "string",
            "enum": ["low", "medium", "high"],
            "description": "Overall confidence in the extraction.",
        },
        "notes": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Short notes about blurry, cropped, or unreadable fields.",
        },
    },
    "required": [
        "document_type",
        "issuing_region",
        "full_name",
        "date_of_birth",
        "address",
        "id_number",
        "issue_date",
        "expiration_date",
        "sex",
        "height",
        "license_class",
        "restrictions",
        "endorsements",
        "visible_text",
        "confidence",
        "notes",
    ],
    "additionalProperties": False,
}
REQUIRED_KEYS = set(ID_SCHEMA["required"])
ARRAY_KEYS = {"visible_text", "notes"}
CONFIDENCE_VALUES = {"low", "medium", "high"}


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract ID information as JSON with the OpenAI Responses API.",
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
        "text": {
            "format": {
                "type": "json_schema",
                "name": "id_document_extraction",
                "description": "Visible information extracted from an ID document image.",
                "strict": True,
                "schema": ID_SCHEMA,
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

    id_info = json.loads(output_text)
    _validate_id_info(id_info)
    print(json.dumps(id_info, indent=2, ensure_ascii=False))


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


def _validate_id_info(value: Any) -> None:
    if not isinstance(value, dict):
        raise RuntimeError("Structured output is not a JSON object.")

    actual_keys = set(value)
    if actual_keys != REQUIRED_KEYS:
        extra = sorted(actual_keys - REQUIRED_KEYS)
        missing = sorted(REQUIRED_KEYS - actual_keys)
        raise RuntimeError(f"Structured output keys do not match schema. Extra={extra}, missing={missing}.")

    for key, item in value.items():
        if key in ARRAY_KEYS:
            if not isinstance(item, list) or not all(isinstance(entry, str) for entry in item):
                raise RuntimeError(f"Structured output field {key!r} must be a list of strings.")
            continue

        if not isinstance(item, str):
            raise RuntimeError(f"Structured output field {key!r} must be a string.")

    if value["confidence"] not in CONFIDENCE_VALUES:
        raise RuntimeError("Structured output field 'confidence' has an invalid value.")


if __name__ == "__main__":
    asyncio.run(main())
