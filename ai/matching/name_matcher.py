"""Name matcher using RapidFuzz for fuzzy name comparison."""

from typing import Any, Callable, Optional, Union
from rapidfuzz import fuzz
from ai.schemas.comparison import ComparisonFinding, MatchStatus


class NameMatcher:
    """Compares person names across documents and computes similarity scores."""

    def __init__(
        self,
        likely_match_threshold: float = 0.90,
        verification_threshold: float = 0.75,
        scorer: Union[str, Callable[[str, str], float]] = "token_set_ratio",
    ):
        """Initialize NameMatcher with configurable thresholds and RapidFuzz scorer.

        Default Thresholds:
        - similarity == 1.0 (exact normalized equality) -> MATCH (needs_verification=False)
        - similarity >= likely_match_threshold (0.90) -> LIKELY_MATCH (needs_verification=True)
        - verification_threshold (0.75) <= similarity < likely_match_threshold -> VERIFICATION_REQUIRED (needs_verification=True)
        - similarity < verification_threshold -> MISMATCH (needs_verification=False)
        """
        self.likely_match_threshold = likely_match_threshold
        self.verification_threshold = verification_threshold
        self.scorer_name = scorer if isinstance(scorer, str) else getattr(scorer, "__name__", "custom")

        if callable(scorer):
            self._scorer = scorer
        elif scorer == "token_sort_ratio":
            self._scorer = fuzz.token_sort_ratio
        elif scorer == "token_set_ratio":
            self._scorer = fuzz.token_set_ratio
        elif scorer == "WRatio":
            self._scorer = fuzz.WRatio
        elif scorer == "ratio":
            self._scorer = fuzz.ratio
        else:
            self._scorer = fuzz.token_set_ratio

    def similarity(self, name_a: Optional[str], name_b: Optional[str]) -> Optional[float]:
        """Calculate similarity score between two normalized names as a float between 0.0 and 1.0.

        Returns None if either name is missing/empty.
        """
        if name_a is None or name_b is None:
            return None

        s_a = str(name_a).strip()
        s_b = str(name_b).strip()
        if not s_a or not s_b:
            return None

        if s_a == s_b:
            return 1.0

        raw_score = self._scorer(s_a, s_b)
        normalized_score = raw_score / 100.0 if raw_score > 1.0 else raw_score
        return round(float(normalized_score), 4)

    def compare(
        self,
        name_a: Optional[str],
        name_b: Optional[str],
        source_document: str = "document_a",
        comparison_document: str = "document_b",
        field_name: str = "name",
        source_value: Optional[Any] = None,
        comparison_value: Optional[Any] = None,
    ) -> ComparisonFinding:
        """Compare two names and produce a structured ComparisonFinding."""
        # Handle missing inputs
        if name_a is None or name_b is None:
            explanation = "Comparison could not be completed because " + (
                "both values are missing." if (name_a is None and name_b is None)
                else f"{field_name.replace('_', ' ')} is missing from one document."
            )
            return ComparisonFinding(
                field_name=field_name,
                source_document=source_document,
                comparison_document=comparison_document,
                source_value=source_value,
                comparison_value=comparison_value,
                normalized_source_value=name_a,
                normalized_comparison_value=name_b,
                similarity_score=None,
                status=MatchStatus.MISSING,
                needs_verification=False,
                explanation=explanation,
            )

        norm_a = str(name_a).strip()
        norm_b = str(name_b).strip()

        if not norm_a or not norm_b:
            return ComparisonFinding(
                field_name=field_name,
                source_document=source_document,
                comparison_document=comparison_document,
                source_value=source_value,
                comparison_value=comparison_value,
                normalized_source_value=name_a,
                normalized_comparison_value=name_b,
                similarity_score=None,
                status=MatchStatus.MISSING,
                needs_verification=False,
                explanation=f"Comparison could not be completed because {field_name.replace('_', ' ')} is empty.",
            )

        # Exact match
        if norm_a == norm_b:
            return ComparisonFinding(
                field_name=field_name,
                source_document=source_document,
                comparison_document=comparison_document,
                source_value=source_value,
                comparison_value=comparison_value,
                normalized_source_value=name_a,
                normalized_comparison_value=name_b,
                similarity_score=1.0,
                status=MatchStatus.MATCH,
                needs_verification=False,
                explanation=f"{field_name.replace('_', ' ').capitalize()} matches exactly after normalization.",
            )

        # Fuzzy comparison
        sim = self.similarity(norm_a, norm_b)
        if sim is None:
            return ComparisonFinding(
                field_name=field_name,
                source_document=source_document,
                comparison_document=comparison_document,
                source_value=source_value,
                comparison_value=comparison_value,
                normalized_source_value=name_a,
                normalized_comparison_value=name_b,
                similarity_score=None,
                status=MatchStatus.MISSING,
                needs_verification=False,
                explanation="Comparison could not compute similarity.",
            )

        field_label = field_name.replace("_", " ").capitalize()
        if sim >= self.likely_match_threshold:
            status = MatchStatus.LIKELY_MATCH
            needs_verification = True
            explanation = f"{field_label} values are highly similar but not identical; manual verification is recommended."
        elif sim >= self.verification_threshold:
            status = MatchStatus.VERIFICATION_REQUIRED
            needs_verification = True
            explanation = f"{field_label} values show partial similarity; verification is required."
        else:
            status = MatchStatus.MISMATCH
            needs_verification = False
            explanation = f"{field_label} values differ significantly between the two documents."

        return ComparisonFinding(
            field_name=field_name,
            source_document=source_document,
            comparison_document=comparison_document,
            source_value=source_value,
            comparison_value=comparison_value,
            normalized_source_value=name_a,
            normalized_comparison_value=name_b,
            similarity_score=sim,
            status=status,
            needs_verification=needs_verification,
            explanation=explanation,
        )

    # Alias for convenience
    match = compare


def compare_names(
    name_a: Optional[str],
    name_b: Optional[str],
    likely_match_threshold: float = 0.90,
    verification_threshold: float = 0.75,
) -> ComparisonFinding:
    """Helper function to compare two normalized names."""
    matcher = NameMatcher(
        likely_match_threshold=likely_match_threshold,
        verification_threshold=verification_threshold,
    )
    return matcher.compare(name_a, name_b)
