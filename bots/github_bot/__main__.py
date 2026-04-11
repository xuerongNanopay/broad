import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

import asyncio
from dotenv import load_dotenv
load_dotenv()

from broad.llm import OpenAILLM

async def main():
    llm = OpenAILLM()
    await llm.prompt(
        input="Hello, can you return a greeting"
    )

if __name__ == "__main__":
    asyncio.run(main())
