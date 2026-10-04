"""Matching and cross-document comparison package."""

from ai.matching.cross_document import CrossDocumentMatcher, compare_documents
from ai.matching.name_matcher import NameMatcher, compare_names
from ai.schemas.comparison import ComparisonFinding, CrossDocumentFinding, MatchStatus

__all__ = [
    "ComparisonFinding",
    "CrossDocumentFinding",
    "CrossDocumentMatcher",
    "MatchStatus",
    "NameMatcher",
    "compare_documents",
    "compare_names",
]
