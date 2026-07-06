"""CLI entry point: runs the full mock inbox through the agent graph."""

from loguru import logger

import config
from agent.graph import build_graph
from utils.mock_loader import load_mock_emails


def main() -> None:
    config.setup_logging()
    graph = build_graph()
    emails = load_mock_emails()

    failed = 0
    for email in emails:
        try:
            result = graph.invoke({"email": email})
        except Exception as e:
            failed += 1
            logger.error(f"Processing failed for email id='{email.id}': {e}")
            continue

        print(f"{email.subject[:50]:<50} -> {result['category']:<12} P{result['priority']}")
        if result.get("draft_reply"):
            print(f"  Draft: {result['draft_reply']}\n")

    logger.info(f"Run complete: {len(emails) - failed} processed, {failed} failed")


if __name__ == "__main__":
    main()
