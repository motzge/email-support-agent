"""Prioritizer node: assigns a 1-5 priority score with a short reason."""

import json

from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger
from pydantic import BaseModel, Field, ValidationError

from agent.state import AgentState
from utils.llm import build_llm, invoke_llm

FALLBACK_PRIORITY = 2

SYSTEM_PROMPT = """You are an email prioritization assistant.
Assign a priority score from 1 to 5 based on the email content.

Priority scale:
- 5: critical, immediate action required (production down, security breach, legal)
- 4: high, respond or act today
- 3: medium, handle within 1-2 days
- 2: low, handle this week
- 1: minimal, no real action needed

Respond with ONLY a JSON object in this exact format:
{"priority": <number 1-5>, "reason": "<one short sentence>"}

No explanation, no extra text."""


class PriorityResult(BaseModel):
    """Validated LLM output for the prioritizer."""

    priority: int = Field(ge=1, le=5)
    reason: str


_llm = build_llm(temperature=0.0, json_mode=True)


def prioritize_node(state: AgentState) -> dict:
    """Assigns a priority score and reason based on email content and category."""
    email = state["email"]
    logger.info(f"Prioritizing email id='{email.id}' category='{state['category']}'")

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"Category: {state['category']}\n"
                f"From: {email.sender}\n"
                f"Subject: {email.subject}\n"
                f"Body: {email.body}\n\n"
                "JSON:"
            )
        ),
    ]

    raw = invoke_llm(_llm, messages)

    try:
        result = PriorityResult(**json.loads(raw))
    except (json.JSONDecodeError, ValidationError) as e:
        logger.warning(
            f"Invalid priority response for id='{email.id}': {e}. "
            f"Falling back to priority={FALLBACK_PRIORITY}"
        )
        return {
            "priority": FALLBACK_PRIORITY,
            "priority_reason": "Could not determine priority",
            "degraded": True,
        }

    logger.info(
        f"Email id='{email.id}' priority={result.priority} reason='{result.reason}'"
    )
    return {"priority": result.priority, "priority_reason": result.reason}
