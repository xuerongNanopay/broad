import asyncio
import sys

from llm import OpenAILLM
from utils.env import load_env

load_env()

async def main():
    model = sys.argv[1] if len(sys.argv) > 1 else "gpt-5-mini"
    prompt = sys.argv[2] if len(sys.argv) > 2 else "Say hello world in one short sentence."

    llm = OpenAILLM(default_model=model)
    response = await llm.invoke(
        [
            {"role": "user", "content": prompt},
        ],
        max_tokens=128,
        temperature=0.2,
    )

    print(response.content)


if __name__ == "__main__":
    asyncio.run(main())
