"""Document classification package for PreFlight AI."""

from ai.classification.classification_signals import CLASSIFICATION_SIGNALS
from ai.classification.document_classifier import DocumentClassifier

__all__ = [
    "DocumentClassifier",
    "CLASSIFICATION_SIGNALS",
]
