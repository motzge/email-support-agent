"""Routing function: decides the next node based on the email category."""

from loguru import logger

from agent.state import AgentState


def route_node(state: AgentState) -> str:
    """Returns the edge name matching the conditional edges in graph.py."""
    email_id = state["email"].id

    if state["category"] in ("urgent", "reply_needed"):
        logger.info(f"Email id='{email_id}' -> routing to draft")
        return "draft"

    logger.info(f"Email id='{email_id}' -> routing to archive")
    return "archive"
