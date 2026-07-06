"""Central configuration and logging setup.

All runtime settings come from environment variables (loaded from .env).
See .env.example for available options.
"""

import os
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

load_dotenv()

# --- LLM settings ---
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:14b")
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_TIMEOUT_SECONDS: float = float(os.getenv("LLM_TIMEOUT_SECONDS", "120"))
LLM_NUM_CTX: int = int(os.getenv("LLM_NUM_CTX", "4096"))

# --- Application settings ---
USER_NAME: str = os.getenv("USER_NAME", "The Support Team")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

LOG_DIR = Path(__file__).parent / "logs"

# Unique ID per process run, attached to every log line.
RUN_ID: str = uuid.uuid4().hex[:8]

_logging_configured = False


def setup_logging() -> None:
    """Configures loguru: console + rotating file sink, run-ID on every line."""
    global _logging_configured
    if _logging_configured:
        return

    LOG_DIR.mkdir(exist_ok=True)
    log_format = (
        "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | run={extra[run_id]} | "
        "{name}:{function} | {message}"
    )

    logger.remove()
    logger.configure(extra={"run_id": RUN_ID})
    logger.add(sys.stderr, level=LOG_LEVEL, format=log_format)
    logger.add(
        LOG_DIR / "agent_{time:YYYY-MM-DD}.log",
        level=LOG_LEVEL,
        format=log_format,
        rotation="10 MB",
        retention="14 days",
        encoding="utf-8",
    )

    _logging_configured = True
    logger.info(f"Logging initialized (run_id={RUN_ID}, model={OLLAMA_MODEL})")
