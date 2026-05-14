import argparse
import asyncio
import os
from typing import Any

import httpx

from utils.env import load_env


OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = "gpt-5.4-mini-2026-03-17"

# cast issue in `total = total * (1 - discount);`
# correct `total = (int) (total * (1 - discount));`
DEFAULT_JAVA_CODE = """
public class ShoppingCart {
    public static void main(String[] args) {
        int[] prices = {1200, 799, 250};
        System.out.println("Total: " + totalWithDiscount(prices, 0.10));
    }

    static int totalWithDiscount(int[] prices, double discount) {
        int total = 0;
        for (int i = 0; i <= prices.length; i++) {
            total += prices[i];
        }

        if (discount > 0) {
            total = total * (1 - discount);
        }

        return total;
    }
}
""".strip()


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Use OpenAI over httpx to debug a Java snippet or file.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"OpenAI model to use. Defaults to {DEFAULT_MODEL}.",
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
                    "You are a senior Java debugger. Find compile-time errors, "
                    "runtime errors, and logic bugs. Be concise and practical."
                ),
            },
            {
                "role": "user",
                "content": _debug_prompt(DEFAULT_JAVA_CODE),
            },
        ],
        "max_output_tokens": 1200,
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


def _debug_prompt(java_code: str) -> str:
    return f"""
Debug this Java code.

Return:
1. The likely error or bug.
2. The root cause.
3. The corrected Java code.
4. A short explanation of why the fix works.

Java code:
```java
{java_code}
```
""".strip()


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
