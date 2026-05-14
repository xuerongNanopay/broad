import argparse
import asyncio

from agents import (
    Agent,
    GuardrailFunctionOutput,
    InputGuardrailTripwireTriggered,
    RunContextWrapper,
    Runner,
    TResponseInputItem,
    input_guardrail,
)
from pydantic import BaseModel

from utils.env import load_env


DEFAULT_MODEL = "gpt-5.4-mini-2026-03-17"
DEFAULT_PROMPT = "Can you check why my order broad-1002 is delayed?"


class SupportTopicCheck(BaseModel):
    is_support_request: bool
    reasoning: str


def build_support_topic_guardrail(model: str):
    guardrail_agent = Agent(
        name="Support topic guardrail",
        instructions=(
            "Decide whether the user's request is about customer support, "
            "orders, delivery, billing, returns, or account help."
        ),
        model=model,
        output_type=SupportTopicCheck,
    )

    @input_guardrail(run_in_parallel=False)
    async def support_topic_guardrail(
        ctx: RunContextWrapper[None],
        checked_agent: Agent,
        input: str | list[TResponseInputItem],
    ) -> GuardrailFunctionOutput:
        result = await Runner.run(guardrail_agent, input, context=ctx.context)
        check = result.final_output

        return GuardrailFunctionOutput(
            output_info=check,
            tripwire_triggered=not check.is_support_request,
        )

    return support_topic_guardrail


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run an OpenAI Agents SDK input guardrail demo.",
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        default=DEFAULT_PROMPT,
        help="User prompt. Defaults to a customer support question.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"OpenAI model to use. Defaults to {DEFAULT_MODEL}.",
    )
    args = parser.parse_args()

    load_env()

    support_agent = Agent(
        name="Customer support agent",
        instructions=(
            "You are a concise customer support agent. Help with orders, "
            "delivery, billing, returns, and account questions."
        ),
        model=args.model,
        input_guardrails=[build_support_topic_guardrail(args.model)],
    )

    try:
        result = await Runner.run(support_agent, args.prompt)
    except InputGuardrailTripwireTriggered as exc:
        check = exc.guardrail_result.output.output_info
        print("Guardrail tripped: request is outside customer support.")
        print(f"Reasoning: {check.reasoning}")
        return

    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
