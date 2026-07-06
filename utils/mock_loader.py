"""Loads the mock email dataset from disk."""

import json
from pathlib import Path

from loguru import logger

from agent.state import Email

DATA_PATH = Path(__file__).parent.parent / "data" / "mock_emails.json"


def load_mock_emails() -> list[Email]:
    """Loads mock emails from JSON and returns validated Email objects."""
    logger.info(f"Loading mock emails from {DATA_PATH}")

    if not DATA_PATH.exists():
        logger.error(f"Mock data file not found: {DATA_PATH}")
        raise FileNotFoundError(f"Mock data file not found: {DATA_PATH}")

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    emails = [Email(**entry) for entry in raw_data]
    logger.info(f"Loaded {len(emails)} mock emails")
    return emails
