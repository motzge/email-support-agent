"""Drafter node: generates a short reply draft for actionable emails."""

from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger

from agent.state import AgentState
from utils.llm import build_llm, invoke_llm
import config

SYSTEM_PROMPT = f"""You are a professional email assistant.
Write a short, professional draft reply to the given email.

Rules:
- Maximum 3-4 sentences
- Professional but friendly tone
- Do not use placeholders like [Your Name] or [Date]
- If a sign-off is needed, sign with: {config.USER_NAME}
- Write the reply body only, no subject line, no headers
- If the email is urgent, acknowledge the urgency immediately"""

_llm = build_llm(temperature=0.3)


def draft_node(state: AgentState) -> dict:
    """Generates a draft reply for emails that require a response."""
    email = state["email"]
    logger.info(f"Drafting reply for email id='{email.id}' category='{state['category']}'")

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"Category: {state['category']}\n"
                f"Priority: {state['priority']}\n"
                f"From: {email.sender}\n"
                f"Subject: {email.subject}\n"
                f"Body: {email.body}\n\n"
                "Write a draft reply:"
            )
        ),
    ]

    draft = invoke_llm(_llm, messages)
    logger.info(f"Draft generated for email id='{email.id}'")
    return {"draft_reply": draft}
