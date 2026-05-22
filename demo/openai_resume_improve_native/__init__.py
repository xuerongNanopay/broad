import argparse
import asyncio
import os
import sys
from html import escape
from pathlib import Path
from typing import Any

import httpx
import pymupdf
from playwright.async_api import Error as PlaywrightError
from playwright.async_api import async_playwright

DEMO_DIR = Path(__file__).resolve().parent
ROOT = DEMO_DIR.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.env import load_env


OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = "gpt-5.4-mini-2026-03-17"
APP_JOURNAL_HOME = ROOT / ".broad" / "demo" / "openai_resume_improve_native"
DEFAULT_RESUME = APP_JOURNAL_HOME / "origin_resume.pdf"
DEFAULT_RESUME_HTML = APP_JOURNAL_HOME / "origin_resume.html"
DEFAULT_HTML_OUTPUT = APP_JOURNAL_HOME / "improved_resume.html"
DEFAULT_PDF_OUTPUT = APP_JOURNAL_HOME / "improved_resume.pdf"
DEFAULT_TARGET_ROLE = "Senior Backend Engineer, fintech"

SYSTEM_PROMPT = """
You are a senior technical resume editor.

Update the resume for the target role while preserving truthfulness:
- Keep the same UI style.
- Keep the candidate's original identity, dates, employers, education, and contact placeholders.
- Do not invent companies, degrees, certifications, projects, or metrics.
- You may rewrite vague bullets into stronger resume language when the source supports it.
- Keep the resume concise, ATS-friendly, and readable as HTML.
- Return a complete standalone, print-ready HTML document with semantic tags and minimal inline CSS.
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

Update the source resume HTML for this role and write the updated resume in HTML.
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
    parser.add_argument(
        "--resume",
        type=Path,
        default=DEFAULT_RESUME,
        help=f"Resume PDF to improve. Defaults to {DEFAULT_RESUME}.",
    )
    args = parser.parse_args()
    resume_path = args.resume.expanduser()
    source_resume_html = _pdf_to_html(resume_path, DEFAULT_RESUME_HTML)

    load_env()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required.")

    async with httpx.AsyncClient(timeout=120) as client:
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
                                "type": "input_text",
                                "text": f"{USER_PROMPT}\n\nSource resume HTML:\n{source_resume_html}",
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

    DEFAULT_HTML_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_HTML_OUTPUT.write_text(improved_resume.rstrip() + "\n", encoding="utf-8")
    await _html_to_pdf(DEFAULT_HTML_OUTPUT, DEFAULT_PDF_OUTPUT)

    print(improved_resume)
    print(f"\nSaved source resume HTML to {DEFAULT_RESUME_HTML}")
    print(f"\nSaved improved resume HTML to {DEFAULT_HTML_OUTPUT}")
    print(f"Saved improved resume PDF to {DEFAULT_PDF_OUTPUT}")


def _pdf_to_html(pdf_path: Path, html_path: Path) -> str:
    if not pdf_path.exists():
        raise FileNotFoundError(f"Resume PDF not found: {pdf_path}")

    html_path.parent.mkdir(parents=True, exist_ok=True)
    with pymupdf.open(pdf_path) as doc:
        pages = [
            f'<section class="page" data-page="{page_number}">\n'
            f'{page.get_text("html")}\n'
            f"</section>"
            for page_number, page in enumerate(doc, start=1)
        ]

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{escape(pdf_path.stem)}</title>
  <style>
    body {{
      background: #f6f6f6;
      color: #111;
      font-family: Arial, sans-serif;
      margin: 0;
      padding: 24px;
    }}
    .page {{
      background: white;
      box-shadow: 0 1px 4px rgba(0, 0, 0, 0.12);
      margin: 0 auto 24px;
      overflow: hidden;
      position: relative;
    }}
  </style>
</head>
<body>
{chr(10).join(pages)}
</body>
</html>
"""
    html_path.write_text(html, encoding="utf-8")
    return html


async def _html_to_pdf(html_path: Path, pdf_path: Path) -> None:
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as playwright:
        try:
            browser = await playwright.chromium.launch()
        except PlaywrightError as exc:
            raise RuntimeError(
                "Playwright Chromium is not installed. Run `uv run playwright install chromium` "
                "before converting HTML to PDF.",
            ) from exc
        page = await browser.new_page()
        await page.goto(html_path.resolve().as_uri(), wait_until="networkidle")
        await page.pdf(
            path=str(pdf_path),
            format="Letter",
            print_background=True,
            margin={
                "top": "0.5in",
                "right": "0.5in",
                "bottom": "0.5in",
                "left": "0.5in",
            },
        )
        await browser.close()


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
