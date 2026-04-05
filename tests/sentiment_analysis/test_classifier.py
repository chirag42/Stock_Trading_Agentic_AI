import pytest
from unittest.mock import patch, MagicMock
from services.sentiment_analysis.classifier import SentimentClassifier
from services.sentiment_analysis.exceptions import ClassifierError


class TestSentimentClassifier:

    @pytest.fixture
    def classifier(self):
        """Builds classifier with mocked pipeline — no FinBERT download."""
        with patch("services.sentiment_analysis.classifier.pipeline") as mock_pipeline:
            mock_pipeline.return_value = MagicMock()
            svc = SentimentClassifier()
            svc._pipeline = MagicMock()
            return svc

    def test_positive_classification(self, classifier):
        classifier._pipeline.return_value = [[{"label": "positive", "score": 0.95}]]
        result = classifier.classify("Apple stock soars to record highs.")
        assert result["label"] == "positive"
        assert result["score"] == 0.95

    def test_negative_classification(self, classifier):
        classifier._pipeline.return_value = [[{"label": "negative", "score": 0.88}]]
        result = classifier.classify("Company faces massive losses and bankruptcy.")
        assert result["label"] == "negative"

    def test_neutral_classification(self, classifier):
        classifier._pipeline.return_value = [[{"label": "neutral", "score": 0.76}]]
        result = classifier.classify("Company releases quarterly earnings report.")
        assert result["label"] == "neutral"

    def test_empty_text_raises(self, classifier):
        with pytest.raises(ClassifierError, match="empty text"):
            classifier.classify("")

    def test_whitespace_only_raises(self, classifier):
        with pytest.raises(ClassifierError, match="empty text"):
            classifier.classify("   ")

    def test_returns_label_and_score(self, classifier):
        classifier._pipeline.return_value = [[{"label": "positive", "score": 0.91}]]
        result = classifier.classify("Strong earnings beat expectations.")
        assert "label" in result
        assert "score" in result

    def test_score_rounded_to_4_decimal_places(self, classifier):
        classifier._pipeline.return_value = [[{"label": "positive", "score": 0.912345678}]]
        result = classifier.classify("Markets rally on positive news.")
        assert result["score"] == round(0.912345678, 4)

    def test_text_truncated_to_512_chars(self, classifier):
        classifier._pipeline.return_value = [[{"label": "neutral", "score": 0.80}]]
        long_text = "word " * 300  # way over 512 chars
        classifier.classify(long_text)
        actual_input = classifier._pipeline.call_args[0][0]
        assert len(actual_input) <= 512

    def test_pipeline_failure_raises_classifier_error(self, classifier):
        classifier._pipeline.side_effect = Exception("Model crashed")
        with pytest.raises(ClassifierError, match="classification failed"):
            classifier.classify("Some financial news text.")

    def test_label_returned_in_lowercase(self, classifier):
        classifier._pipeline.return_value = [[{"label": "POSITIVE", "score": 0.90}]]
        result = classifier.classify("Good news for investors.")
        assert result["label"] == "positive"