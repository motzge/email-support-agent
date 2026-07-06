"""Builds and compiles the email support agent graph."""

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from loguru import logger

from agent.nodes.classifier import classify_node
from agent.nodes.drafter import draft_node
from agent.nodes.prioritizer import prioritize_node
from agent.nodes.router import route_node
from agent.state import AgentState


def build_graph() -> CompiledStateGraph:
    """Defines all nodes and edges and returns the compiled graph.

    Flow: classify -> prioritize -> (draft | archive)
    """
    logger.info("Building email support agent graph")

    graph = StateGraph(AgentState)

    graph.add_node("classify", classify_node)
    graph.add_node("prioritize", prioritize_node)
    graph.add_node("draft", draft_node)

    graph.add_edge(START, "classify")
    graph.add_edge("classify", "prioritize")

    # Router decides what happens after prioritization.
    graph.add_conditional_edges(
        "prioritize",
        route_node,
        {
            "draft": "draft",
            "archive": END,
        },
    )

    graph.add_edge("draft", END)

    compiled = graph.compile()
    logger.info("Graph compiled successfully")
    return compiled
