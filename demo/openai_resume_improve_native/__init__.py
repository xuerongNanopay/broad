import argparse
import asyncio
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
OPENAI_FILES_URL = "https://api.openai.com/v1/files"
DEFAULT_MODEL = "gpt-5.4-mini-2026-03-17"
DEFAULT_RESUME = Path(__file__).with_name("resume_template.pdf")
DEFAULT_OUTPUT = Path(".broad/demo/improved_resume.html")
DEFAULT_TARGET_ROLE = "Senior Backend Engineer, fintech"

SYSTEM_PROMPT = """
You are a senior technical resume editor.

Update the resume for the target role while preserving truthfulness:
- Keep the candidate's original identity, dates, employers, education, and contact placeholders.
- Do not invent companies, degrees, certifications, projects, or metrics.
- You may rewrite vague bullets into stronger resume language when the source supports it.
- Keep the resume concise, ATS-friendly, and readable as HTML.
- Return a complete standalone HTML document with semantic tags and minimal inline CSS.
- Return only HTML, with no Markdown fences or commentary before or after it.
""".strip()

JOB_DESCRIPTION = """
About the Role
We are hiring a Senior Software Engineer, Backend to join our product team. You'll be a key player in designing and building Centari's core AI technology, working alongside engineers who share a bias for action. As one team, you'll write code, shape the product, interact with customers, and drive initiatives from concept to completion.

Our systems are built with Go and React/TypeScript, leveraging cutting-edge LLM technologies across infrastructure, search, and persistence layers. If you're passionate about building impactful LLM applications and thrive on owning complex challenges, we want to hear from you.

Requirements
At least 5+ years of experience building production-ready applications in Go or another strongly typed language.

Some experience with or strong interest in LLMs, knowledge graphs, semantic search, and other AI/ML technologies.

Proven ability to work with cutting-edge technology and eagerness to learn new skills.

Willingness to roll up sleeves and get things done - our engineers are comfortable switching between different technical domains as needed.

Strong collaboration skills and ability to work effectively in a fast-paced environment.

Experience as a tech lead or driving projects end to end.

Nice to have
Experience in enterprise SaaS or with highly regulated industries (e.g., legal, financial services, healthcare).

Experience in a startup environment.

Specialized experience and skills in either full-stack product development or data/ML infrastructure.

What we offer
Build at the frontier of AI for knowledge work, with a highly engaged user base from top firms.

Flat organizational structure promoting autonomy and direct impact.

Meaningful equity in a high-growth startup.

Competitive salary

100% remote. Flexible PTO.
""".strip()

USER_PROMPT = f"""
Target role: {DEFAULT_TARGET_ROLE}

Job description:
{JOB_DESCRIPTION}

Update the attached resume PDF for this role and write the updated resume in HTML.
""".strip()


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Improve a resume PDF with the OpenAI Responses API.",
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

    async with httpx.AsyncClient(timeout=120) as client:
        file_id = await _upload_resume(client, api_key, DEFAULT_RESUME)

        response = await client.post(
            OPENAI_RESPONSES_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
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
                                "type": "input_file",
                                "file_id": file_id,
                            },
                            {
                                "type": "input_text",
                                "text": USER_PROMPT,
                            },
                        ],
                    },
                ],
                "max_output_tokens": 4800,
            },
        )
        response.raise_for_status()

    data = response.json()
    improved_resume = _response_text(data)
    if improved_resume is None:
        raise RuntimeError("OpenAI did not return output_text.")

    DEFAULT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_OUTPUT.write_text(improved_resume.rstrip() + "\n", encoding="utf-8")

    print(improved_resume)
    print(f"\nSaved improved resume to {DEFAULT_OUTPUT}")


async def _upload_resume(client: httpx.AsyncClient, api_key: str, path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Resume PDF not found: {path}")

    response = await client.post(
        OPENAI_FILES_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        data={"purpose": "user_data"},
        files={"file": (path.name, path.read_bytes(), "application/pdf")},
    )
    response.raise_for_status()

    data = response.json()
    file_id = data.get("id")
    if not isinstance(file_id, str):
        raise RuntimeError("OpenAI file upload did not return a file id.")
    return file_id


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
