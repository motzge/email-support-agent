"""State definitions for the email support agent graph."""

from typing import Literal, Optional

from pydantic import BaseModel
from typing_extensions import TypedDict

Category = Literal["urgent", "reply_needed", "info", "newsletter", "spam"]


class Email(BaseModel):
    """A single raw email as it enters the pipeline."""

    id: str
    sender: str
    subject: str
    body: str
    timestamp: str


class AgentState(TypedDict):
    """The single state object that flows through every node in the graph.

    Each node receives the current state, returns its partial update,
    and LangGraph merges it back in.
    """

    # Input
    email: Email

    # Set by classifier node
    category: Optional[Category]

    # Set by prioritizer node
    priority: Optional[int]
    priority_reason: Optional[str]

    # Set by drafter node
    draft_reply: Optional[str]

    # True if any node had to fall back to defaults (LLM failure etc.)
    degraded: Optional[bool]
