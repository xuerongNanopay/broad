import argparse
import asyncio
import json
from typing import Any

from openai import AsyncOpenAI
from openai.types.responses import Response

from utils.env import load_env


DEFAULT_MODEL = "gpt-5.4-mini-2026-03-17"
DEFAULT_PROMPT = "What is the status of order broad-1002? Include the ETA."

ORDERS = {
    "broad-1001": {
        "status": "delivered",
        "eta": "2026-05-11",
        "last_update": "Left at front desk.",
    },
    "broad-1002": {
        "status": "in_transit",
        "eta": "2026-05-16",
        "last_update": "Departed Toronto sorting facility.",
    },
    "broad-1003": {
        "status": "delayed",
        "eta": "2026-05-18",
        "last_update": "Weather delay at transfer hub.",
    },
}

TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "name": "get_order_status",
        "description": "Look up shipping status for a customer order.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "Order id, for example broad-1002.",
                },
            },
            "required": ["order_id"],
            "additionalProperties": False,
        },
        "strict": True,
    },
]


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Use OpenAI function calling with a local Python function.",
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        default=DEFAULT_PROMPT,
        help="User prompt. Defaults to an order status question.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"OpenAI model to use. Defaults to {DEFAULT_MODEL}.",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Also print raw OpenAI responses.",
    )
    args = parser.parse_args()

    load_env()
    client = AsyncOpenAI()
    initial_input = [
        {
            "role": "developer",
            "content": (
                "Use the get_order_status function when the user asks about "
                "an order. Explain the result in one concise sentence."
            ),
        },
        {"role": "user", "content": args.prompt},
    ]

    first_response: Response = await client.responses.create(
        model=args.model,
        input=initial_input,
        tools=TOOLS,
        max_output_tokens=500,
    )

    tool_outputs = _run_tool_calls(first_response)
    if not tool_outputs:
        print(first_response.output_text)
        if args.raw:
            _print_raw(first_response)
        return

    follow_up_input = [
        *initial_input,
        *_response_output_items(first_response),
        *tool_outputs,
    ]
    final_response: Response = await client.responses.create(
        model=args.model,
        input=follow_up_input,
        max_output_tokens=500,
    )

    print(final_response.output_text)

    if args.raw:
        print("\nFirst response:")
        _print_raw(first_response)
        print("\nFinal response:")
        _print_raw(final_response)


def _run_tool_calls(response: Response) -> list[dict[str, str]]:
    outputs: list[dict[str, str]] = []
    for item in response.output:
        if _field(item, "type") != "function_call":
            continue

        name = str(_field(item, "name"))
        call_id = str(_field(item, "call_id"))
        arguments = json.loads(str(_field(item, "arguments") or "{}"))
        result = _call_function(name, arguments)

        outputs.append(
            {
                "type": "function_call_output",
                "call_id": call_id,
                "output": json.dumps(result),
            },
        )

    return outputs


def _response_output_items(response: Response) -> list[dict[str, Any]]:
    return [_dump(item) for item in response.output]


def _call_function(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if name == "get_order_status":
        return get_order_status(str(arguments["order_id"]))
    raise ValueError(f"Unknown function call: {name}")


def get_order_status(order_id: str) -> dict[str, Any]:
    order = ORDERS.get(order_id.lower())
    if order is None:
        return {
            "order_id": order_id,
            "found": False,
            "message": "No order found with that id.",
        }

    return {
        "order_id": order_id,
        "found": True,
        **order,
    }


def _field(value: Any, name: str) -> Any:
    if isinstance(value, dict):
        return value.get(name)
    return getattr(value, name, None)


def _print_raw(response: Response) -> None:
    print(json.dumps(_dump(response), indent=2, ensure_ascii=False, default=str))


def _dump(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, list):
        return [_dump(item) for item in value]
    if isinstance(value, dict):
        return {key: _dump(item) for key, item in value.items()}
    return value


if __name__ == "__main__":
    asyncio.run(main())
