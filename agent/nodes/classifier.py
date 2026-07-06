"""Classifier node: assigns exactly one category to an email."""

from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger

from agent.state import AgentState
from utils.llm import build_llm, invoke_llm

VALID_CATEGORIES = {"urgent", "reply_needed", "info", "newsletter", "spam"}
FALLBACK_CATEGORY = "info"

SYSTEM_PROMPT = """You are an email classification assistant.
Classify the email into exactly one of these categories:

- urgent: requires immediate attention or action, time-sensitive
- reply_needed: requires a response but is not time-critical
- info: informational only, no action or reply needed
- newsletter: automated newsletter or digest
- spam: unsolicited commercial email, promotions, or junk

Respond with ONLY the category name in lowercase.
No punctuation, no explanation, no extra words."""

_llm = build_llm(temperature=0.0)


def classify_node(state: AgentState) -> dict:
    """Sends the email to the LLM and writes the category into the state."""
    email = state["email"]
    logger.info(f"Classifying email id='{email.id}' subject='{email.subject[:60]}'")

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"From: {email.sender}\n"
                f"Subject: {email.subject}\n"
                f"Body: {email.body}\n\n"
                "Category:"
            )
        ),
    ]

    category = invoke_llm(_llm, messages).lower()

    if category not in VALID_CATEGORIES:
        logger.warning(
            f"Unexpected category '{category}' for id='{email.id}', "
            f"falling back to '{FALLBACK_CATEGORY}'"
        )
        return {"category": FALLBACK_CATEGORY, "degraded": True}

    logger.info(f"Email id='{email.id}' classified as '{category}'")
    return {"category": category}
