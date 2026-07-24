import logging
import os

import anthropic

from .exceptions import LLMConnectionError, LLMResponseError

logger = logging.getLogger("ClaudeClient")

SYSTEM_PROMPT = (
    "You are a financial analysis assistant. "
    "Be concise, structured, and data-driven. "
    "Always start your response with exactly one word: BUY, SELL, or HOLD."
)


class ClaudeClient:
    """
    Claude API client that mirrors LLMClient (the Ollama client) exactly:
    same query(prompt) -> str interface, same system prompt, and the same
    LLMConnectionError / LLMResponseError exceptions — so StrategyAgent can swap
    backends without any other code change.

    The API key is read from the environment (ANTHROPIC_API_KEY), matching how
    NewsFetcher reads BRAVE_API_KEY. It is never hard-coded.
    """

    def __init__(self, model: str = "claude-sonnet-4-6", max_tokens: int = 512):
        self.model = model
        self.max_tokens = max_tokens

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise LLMConnectionError(
                "ANTHROPIC_API_KEY not found in environment. "
                "Set it in your shell (e.g. export ANTHROPIC_API_KEY=...)."
            )
        self.client = anthropic.Anthropic(api_key=api_key)

    def query(self, prompt: str) -> str:
        """
        Sends a prompt to the Claude API and returns the raw text response.
        Raises LLMResponseError if the prompt is empty or the response is empty.
        Raises LLMConnectionError for auth / connection / rate-limit failures.
        """
        if not prompt or not prompt.strip():
            raise LLMResponseError("Cannot send empty prompt to LLM.")

        try:
            logger.info(f"Querying {self.model} via Claude API...")
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )

            # Response content is a list of blocks; collect the text blocks.
            parts = [
                block.text for block in response.content
                if getattr(block, "type", None) == "text"
            ]
            content = "".join(parts).strip()

            if not content:
                raise LLMResponseError("Claude returned an empty response.")

            logger.info(f"Claude response received ({len(content)} chars)")
            return content

        except LLMResponseError:
            raise
        except anthropic.AuthenticationError as exc:
            raise LLMConnectionError(
                f"Claude API authentication failed — check ANTHROPIC_API_KEY. ({exc})"
            )
        except anthropic.RateLimitError as exc:
            raise LLMConnectionError(f"Claude API rate limit hit: {exc}")
        except anthropic.APIConnectionError as exc:
            raise LLMConnectionError(f"Cannot connect to Claude API: {exc}")
        except Exception as exc:  # noqa: BLE001
            raise LLMConnectionError(f"Claude query failed: {exc}")
