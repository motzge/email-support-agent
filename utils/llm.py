"""Shared LLM client factory and retry wrapper.

Every node uses build_llm() so model, base URL, context size and
request timeout are configured in exactly one place (config.py / .env).
"""

import httpx
from langchain_core.messages import BaseMessage
from langchain_ollama import ChatOllama
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

import config

# Only transient transport-level errors are retried. Anything else
# (bad request, model errors) fails fast and is handled by the caller.
TRANSIENT_ERRORS = (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError)


def build_llm(temperature: float = 0.0, json_mode: bool = False) -> ChatOllama:
    """Returns a configured ChatOllama client with a hard request timeout."""
    return ChatOllama(
        model=config.OLLAMA_MODEL,
        base_url=config.OLLAMA_BASE_URL,
        temperature=temperature,
        num_ctx=config.LLM_NUM_CTX,
        format="json" if json_mode else None,
        client_kwargs={"timeout": config.LLM_TIMEOUT_SECONDS},
    )


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(TRANSIENT_ERRORS),
    reraise=True,
)
def invoke_llm(llm: ChatOllama, messages: list[BaseMessage]) -> str:
    """Invokes the LLM with retry on transient connection errors.

    Retries up to 3 times with exponential backoff, then re-raises.
    Returns the stripped text content of the response.
    """
    response = llm.invoke(messages)
    return str(response.content).strip()
