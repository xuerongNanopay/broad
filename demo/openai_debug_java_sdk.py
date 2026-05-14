import argparse
import asyncio

from openai import AsyncOpenAI
from openai.types.responses import Response

from utils.env import load_env


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
        description="Use OpenAI to debug a Java snippet or file.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"OpenAI model to use. Defaults to {DEFAULT_MODEL}.",
    )
    args = parser.parse_args()

    load_env()
    client = AsyncOpenAI()

    response: Response = await client.responses.create(
        model=args.model,
        input=[
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
        max_output_tokens=1200,
    )

    print(response.output_text)


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


if __name__ == "__main__":
    asyncio.run(main())
