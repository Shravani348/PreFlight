"""Name matcher using RapidFuzz for fuzzy name comparison with subset and initial hardening."""

from itertools import permutations
from typing import Any, Callable, List, Optional, Set, Union
from rapidfuzz import fuzz

from ai.normalization.name_normalizer import normalize_name
from ai.schemas.comparison import ComparisonFinding, MatchStatus

# Recognized titles and honorifics that may appear in identity or application records
HONORIFICS: Set[str] = {
    "mr",
    "mrs",
    "ms",
    "miss",
    "shri",
    "shrimati",
    "smt",
    "dr",
    "prof",
    "kumar",
    "kumari",
}


def _check_initials_alignment(tokens_a: List[str], tokens_b: List[str]) -> bool:
    """Check whether two token lists of the same length align via exact matches and initials."""
    if len(tokens_a) != len(tokens_b) or len(tokens_a) == 0:
        return False

    if len(tokens_a) <= 5:
        for p_b in permutations(tokens_b):
            all_aligned = True
            has_initial = False
            for t1, t2 in zip(tokens_a, p_b):
                if t1 == t2:
                    continue
                elif len(t1) == 1 and t2.startswith(t1):
                    has_initial = True
                elif len(t2) == 1 and t1.startswith(t2):
                    has_initial = True
                else:
                    all_aligned = False
                    break
            if all_aligned and has_initial:
                return True
        return False

    return False


class NameMatcher:
    """Compares person names across documents with subset protection against family-member confusion."""

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

        Protects against 1.0 false matches when one name is a strict subset of the other.
        """
        if name_a is None or name_b is None:
            return None

        s_a = normalize_name(name_a) if isinstance(name_a, str) else str(name_a).strip().lower()
        s_b = normalize_name(name_b) if isinstance(name_b, str) else str(name_b).strip().lower()
        if not s_a or not s_b:
            return None

        if s_a == s_b:
            return 1.0

        tokens_a = s_a.split()
        tokens_b = s_b.split()

        # Token permutation (reordered tokens)
        if sorted(tokens_a) == sorted(tokens_b):
            return 1.0

        # Subset penalty: if one is a strict subset of the other, use token_sort_ratio
        # to avoid 1.0 false match from token_set_ratio
        set_a = set(tokens_a)
        set_b = set(tokens_b)
        if (set_a < set_b or set_b < set_a) and len(set_a) != len(set_b):
            raw_score = fuzz.token_sort_ratio(s_a, s_b)
            return round(float(raw_score / 100.0), 4)

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
        """Compare two names defensively and produce a structured ComparisonFinding."""
        field_label = field_name.replace("_", " ").capitalize()

        # 1. Handle missing inputs
        if name_a is None or name_b is None:
            explanation = "Comparison could not be completed because " + (
                "both values are missing." if (name_a is None and name_b is None)
                else f"{field_label.lower()} is missing from one document."
            )
            return ComparisonFinding(
                field_name=field_name,
                source_document=source_document,
                comparison_document=comparison_document,
                source_value=source_value if source_value is not None else name_a,
                comparison_value=comparison_value if comparison_value is not None else name_b,
                normalized_source_value=None,
                normalized_comparison_value=None,
                similarity_score=None,
                status=MatchStatus.MISSING,
                needs_verification=False,
                explanation=explanation,
            )

        norm_a = normalize_name(name_a) if isinstance(name_a, str) else str(name_a).strip()
        norm_b = normalize_name(name_b) if isinstance(name_b, str) else str(name_b).strip()

        if not norm_a or not norm_b:
            return ComparisonFinding(
                field_name=field_name,
                source_document=source_document,
                comparison_document=comparison_document,
                source_value=source_value if source_value is not None else name_a,
                comparison_value=comparison_value if comparison_value is not None else name_b,
                normalized_source_value=norm_a,
                normalized_comparison_value=norm_b,
                similarity_score=None,
                status=MatchStatus.MISSING,
                needs_verification=False,
                explanation=f"Comparison could not be completed because {field_label.lower()} is empty.",
            )

        # 2. Exact match after normalization
        if norm_a == norm_b:
            return ComparisonFinding(
                field_name=field_name,
                source_document=source_document,
                comparison_document=comparison_document,
                source_value=source_value if source_value is not None else name_a,
                comparison_value=comparison_value if comparison_value is not None else name_b,
                normalized_source_value=norm_a,
                normalized_comparison_value=norm_b,
                similarity_score=1.0,
                status=MatchStatus.MATCH,
                needs_verification=False,
                explanation=f"{field_label} matches exactly after normalization.",
            )

        tokens_a = norm_a.split()
        tokens_b = norm_b.split()

        # 3. Honorific stripping check (e.g. 'Ms. Priti Ahire' vs 'Priti Ahire')
        clean_a = [t for t in tokens_a if t not in HONORIFICS]
        clean_b = [t for t in tokens_b if t not in HONORIFICS]
        if clean_a == clean_b and clean_a:
            return ComparisonFinding(
                field_name=field_name,
                source_document=source_document,
                comparison_document=comparison_document,
                source_value=source_value if source_value is not None else name_a,
                comparison_value=comparison_value if comparison_value is not None else name_b,
                normalized_source_value=norm_a,
                normalized_comparison_value=norm_b,
                similarity_score=1.0,
                status=MatchStatus.MATCH,
                needs_verification=False,
                explanation=f"{field_label} matches exactly after disregarding honorific titles.",
            )

        # 4. Token permutation (reordered tokens, e.g. 'Ahire Priti Shashikant' vs 'Priti Shashikant Ahire')
        if sorted(clean_a) == sorted(clean_b) and clean_a:
            return ComparisonFinding(
                field_name=field_name,
                source_document=source_document,
                comparison_document=comparison_document,
                source_value=source_value if source_value is not None else name_a,
                comparison_value=comparison_value if comparison_value is not None else name_b,
                normalized_source_value=norm_a,
                normalized_comparison_value=norm_b,
                similarity_score=1.0,
                status=MatchStatus.MATCH,
                needs_verification=False,
                explanation=f"{field_label} tokens match exactly with reordered token sequence.",
            )

        # 5. Initials alignment check (e.g. 'Priti S Ahire' or 'P S Ahire' vs 'Priti Shashikant Ahire')
        if _check_initials_alignment(clean_a, clean_b):
            initial_sim = max(self.similarity(norm_a, norm_b) or 0.0, self.verification_threshold)
            if initial_sim >= self.likely_match_threshold:
                initial_status = MatchStatus.LIKELY_MATCH
                initial_explanation = f"{field_label} values are highly similar with abbreviated initials; manual verification is recommended."
            else:
                initial_status = MatchStatus.VERIFICATION_REQUIRED
                initial_explanation = f"{field_label} values match with abbreviated initials; manual verification is required."

            return ComparisonFinding(
                field_name=field_name,
                source_document=source_document,
                comparison_document=comparison_document,
                source_value=source_value if source_value is not None else name_a,
                comparison_value=comparison_value if comparison_value is not None else name_b,
                normalized_source_value=norm_a,
                normalized_comparison_value=norm_b,
                similarity_score=initial_sim,
                status=initial_status,
                needs_verification=True,
                explanation=initial_explanation,
            )

        # 6. Subset protection check (e.g. 'Shashikant Ahire' vs 'Priti Shashikant Ahire')
        set_a = set(clean_a)
        set_b = set(clean_b)
        if set_a != set_b and (set_a.issubset(set_b) or set_b.issubset(set_a)):
            shorter_tokens = clean_a if len(set_a) < len(set_b) else clean_b
            longer_tokens = clean_b if len(set_a) < len(set_b) else clean_a
            diff = set(longer_tokens) - set(shorter_tokens)

            # Single token against 3+ tokens is insufficient evidence
            if len(set(shorter_tokens)) == 1 and len(set(longer_tokens)) >= 3:
                return ComparisonFinding(
                    field_name=field_name,
                    source_document=source_document,
                    comparison_document=comparison_document,
                    source_value=source_value if source_value is not None else name_a,
                    comparison_value=comparison_value if comparison_value is not None else name_b,
                    normalized_source_value=norm_a,
                    normalized_comparison_value=norm_b,
                    similarity_score=round(fuzz.token_sort_ratio(norm_a, norm_b) / 100.0, 4),
                    status=MatchStatus.MISMATCH,
                    needs_verification=False,
                    explanation=f"{field_label} contains only a single token against a multi-token name; insufficient evidence of identity.",
                )

            # Subset with missing full-name tokens: NEVER allow MATCH or LIKELY_MATCH
            penalized_sim = self.similarity(norm_a, norm_b) or 0.0
            missing_tokens_str = ", ".join(f"'{t}'" for t in sorted(diff))
            return ComparisonFinding(
                field_name=field_name,
                source_document=source_document,
                comparison_document=comparison_document,
                source_value=source_value if source_value is not None else name_a,
                comparison_value=comparison_value if comparison_value is not None else name_b,
                normalized_source_value=norm_a,
                normalized_comparison_value=norm_b,
                similarity_score=penalized_sim,
                status=MatchStatus.VERIFICATION_REQUIRED,
                needs_verification=True,
                explanation=(
                    f"{field_label} is a subset of the comparison name with missing tokens ({missing_tokens_str}); "
                    "manual verification is required to confirm identity and avoid family-member confusion."
                ),
            )

        # 7. Standard fuzzy comparison
        sim = self.similarity(norm_a, norm_b)
        if sim is None:
            return ComparisonFinding(
                field_name=field_name,
                source_document=source_document,
                comparison_document=comparison_document,
                source_value=source_value if source_value is not None else name_a,
                comparison_value=comparison_value if comparison_value is not None else name_b,
                normalized_source_value=norm_a,
                normalized_comparison_value=norm_b,
                similarity_score=None,
                status=MatchStatus.MISSING,
                needs_verification=False,
                explanation="Comparison could not compute similarity.",
            )

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
            source_value=source_value if source_value is not None else name_a,
            comparison_value=comparison_value if comparison_value is not None else name_b,
            normalized_source_value=norm_a,
            normalized_comparison_value=norm_b,
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
