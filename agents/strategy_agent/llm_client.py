import logging
import ollama

from .exceptions import LLMConnectionError, LLMResponseError

logger = logging.getLogger("LLMClient")


class LLMClient:

    def __init__(self, model: str = "llama3.2"):
        self.model = model

    def query(self, prompt: str) -> str:
        """
        Sends a prompt to the local Ollama LLM and returns
        the raw text response.
        Raises LLMConnectionError if Ollama is not running.
        Raises LLMResponseError if response is empty or malformed.
        """
        if not prompt or not prompt.strip():
            raise LLMResponseError("Cannot send empty prompt to LLM.")

        try:
            logger.info(f"Querying {self.model} via Ollama...")
            response = ollama.chat(
                model=self.model,
                messages=[
                    {
                        "role":    "system",
                        "content": "You are a financial analysis assistant. "
                                   "Be concise, structured, and data-driven. "
                                   "Always start your response with exactly "
                                   "one word: BUY, SELL, or HOLD."
                    },
                    {
                        "role":    "user",
                        "content": prompt
                    }
                ]
            )

            content = response["message"]["content"]

            if not content or not content.strip():
                raise LLMResponseError("LLM returned an empty response.")

            logger.info(f"LLM response received ({len(content)} chars)")
            return content.strip()

        except LLMResponseError:
            raise

        except Exception as exc:
            if "connection" in str(exc).lower() or "refused" in str(exc).lower():
                raise LLMConnectionError(
                    "Cannot connect to Ollama. "
                    "Make sure Ollama is running: ollama serve"
                )
            raise LLMConnectionError(f"LLM query failed: {exc}")