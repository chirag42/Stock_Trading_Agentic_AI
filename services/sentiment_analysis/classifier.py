import logging
from transformers import pipeline

from .exceptions import ClassifierError

logger = logging.getLogger("SentimentClassifier")

MAX_TEXT_LENGTH = 512


class SentimentClassifier:

    def __init__(self):
        try:
            logger.info("Loading FinBERT model...")
            self._pipeline = pipeline(
                "text-classification",
                model="ProsusAI/finbert",
                top_k=1
            )
            logger.info("FinBERT ready.")
        except Exception as exc:
            raise ClassifierError(f"Failed to load FinBERT model: {exc}")

    def classify(self, text: str) -> dict:
        """
        Classifies a single piece of text.
        Returns dict with label and confidence score.
        Raises ClassifierError on failure.
        """
        if not text or not text.strip():
            raise ClassifierError("Cannot classify empty text.")

        try:
            text   = text.strip()[:MAX_TEXT_LENGTH]
            result = self._pipeline(text)[0][0]
            return {
                "label": result["label"].lower(),
                "score": round(result["score"], 4)
            }
        except ClassifierError:
            raise
        except Exception as exc:
            raise ClassifierError(f"FinBERT classification failed: {exc}")