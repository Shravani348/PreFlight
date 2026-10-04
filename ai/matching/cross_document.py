"""Cross-document matcher for scholarship application documents."""

from typing import Any, List, Optional
from rapidfuzz import fuzz
from ai.matching.name_matcher import NameMatcher
from ai.schemas.comparison import ComparisonFinding, MatchStatus
from ai.schemas.document import DocumentType
from ai.schemas.extraction import ExtractedDocument

# Priority order for canonical pair sorting
DOCUMENT_TYPE_ORDER = {
    DocumentType.APPLICATION_FORM: 0,
    DocumentType.AADHAAR_OR_IDENTITY: 1,
    DocumentType.MARKSHEET: 2,
    DocumentType.INCOME_CERTIFICATE: 3,
    DocumentType.CASTE_CERTIFICATE: 4,
    DocumentType.PHOTOGRAPH: 5,
    DocumentType.INSTRUCTIONS: 6,
    DocumentType.UNKNOWN: 7,
}


class CrossDocumentMatcher:
    """Matches fields across multiple extracted scholarship documents."""

    def __init__(
        self,
        name_matcher: Optional[NameMatcher] = None,
        address_likely_threshold: float = 0.85,
        address_verification_threshold: float = 0.70,
    ):
        """Initialize CrossDocumentMatcher with configurable thresholds and components."""
        self.name_matcher = name_matcher or NameMatcher()
        self.address_likely_threshold = address_likely_threshold
        self.address_verification_threshold = address_verification_threshold

    def _get_doc_label(self, doc: ExtractedDocument) -> str:
        """Resolve a consistent, human-readable document label."""
        if hasattr(doc.document_type, "value") and doc.document_type != DocumentType.UNKNOWN:
            return doc.document_type.value
        return doc.document_id or "unknown_document"

    def compare_date(
        self,
        date_a: Optional[str],
        date_b: Optional[str],
        source_doc: str,
        comp_doc: str,
        field_name: str = "date_of_birth",
        orig_a: Optional[Any] = None,
        orig_b: Optional[Any] = None,
    ) -> ComparisonFinding:
        """Compare two normalized ISO dates strictly without fuzzy matching."""
        field_label = field_name.replace("_", " ").capitalize()

        if date_a is None or date_b is None:
            explanation = "Comparison could not be completed because " + (
                "both values are missing." if (date_a is None and date_b is None)
                else f"{field_label.lower()} is missing from one document."
            )
            return ComparisonFinding(
                field_name=field_name,
                source_document=source_doc,
                comparison_document=comp_doc,
                source_value=orig_a,
                comparison_value=orig_b,
                normalized_source_value=date_a,
                normalized_comparison_value=date_b,
                similarity_score=None,
                status=MatchStatus.MISSING,
                needs_verification=False,
                explanation=explanation,
            )

        norm_a = str(date_a).strip()
        norm_b = str(date_b).strip()

        if not norm_a or not norm_b:
            return ComparisonFinding(
                field_name=field_name,
                source_document=source_doc,
                comparison_document=comp_doc,
                source_value=orig_a,
                comparison_value=orig_b,
                normalized_source_value=date_a,
                normalized_comparison_value=date_b,
                similarity_score=None,
                status=MatchStatus.MISSING,
                needs_verification=False,
                explanation=f"Comparison could not be completed because {field_label.lower()} is empty.",
            )

        if norm_a == norm_b:
            return ComparisonFinding(
                field_name=field_name,
                source_document=source_doc,
                comparison_document=comp_doc,
                source_value=orig_a,
                comparison_value=orig_b,
                normalized_source_value=date_a,
                normalized_comparison_value=date_b,
                similarity_score=1.0,
                status=MatchStatus.MATCH,
                needs_verification=False,
                explanation=f"{field_label} matches exactly after normalization.",
            )
        else:
            return ComparisonFinding(
                field_name=field_name,
                source_document=source_doc,
                comparison_document=comp_doc,
                source_value=orig_a,
                comparison_value=orig_b,
                normalized_source_value=date_a,
                normalized_comparison_value=date_b,
                similarity_score=0.0,
                status=MatchStatus.MISMATCH,
                needs_verification=False,
                explanation=f"{field_label} differs between the two documents.",
            )

    def compare_address(
        self,
        addr_a: Optional[str],
        addr_b: Optional[str],
        source_doc: str,
        comp_doc: str,
        orig_a: Optional[Any] = None,
        orig_b: Optional[Any] = None,
    ) -> ComparisonFinding:
        """Compare two normalized address strings."""
        if addr_a is None or addr_b is None:
            explanation = "Comparison could not be completed because " + (
                "both values are missing." if (addr_a is None and addr_b is None)
                else "address is missing from one document."
            )
            return ComparisonFinding(
                field_name="address",
                source_document=source_doc,
                comparison_document=comp_doc,
                source_value=orig_a,
                comparison_value=orig_b,
                normalized_source_value=addr_a,
                normalized_comparison_value=addr_b,
                similarity_score=None,
                status=MatchStatus.MISSING,
                needs_verification=False,
                explanation=explanation,
            )

        norm_a = str(addr_a).strip()
        norm_b = str(addr_b).strip()

        if not norm_a or not norm_b:
            return ComparisonFinding(
                field_name="address",
                source_document=source_doc,
                comparison_document=comp_doc,
                source_value=orig_a,
                comparison_value=orig_b,
                normalized_source_value=addr_a,
                normalized_comparison_value=addr_b,
                similarity_score=None,
                status=MatchStatus.MISSING,
                needs_verification=False,
                explanation="Comparison could not be completed because address is empty.",
            )

        if norm_a == norm_b:
            return ComparisonFinding(
                field_name="address",
                source_document=source_doc,
                comparison_document=comp_doc,
                source_value=orig_a,
                comparison_value=orig_b,
                normalized_source_value=addr_a,
                normalized_comparison_value=addr_b,
                similarity_score=1.0,
                status=MatchStatus.MATCH,
                needs_verification=False,
                explanation="Address matches exactly after normalization.",
            )

        # Token set ratio for address comparison
        raw_sim = fuzz.token_set_ratio(norm_a, norm_b) / 100.0
        sim = round(float(raw_sim), 4)

        if sim >= self.address_likely_threshold:
            status = MatchStatus.LIKELY_MATCH
            needs_verification = True
            explanation = "Address values are similar but not identical; manual verification is recommended."
        elif sim >= self.address_verification_threshold:
            status = MatchStatus.VERIFICATION_REQUIRED
            needs_verification = True
            explanation = "Address values show partial similarity; verification is required."
        else:
            status = MatchStatus.MISMATCH
            needs_verification = False
            explanation = "Address values differ significantly between the two documents."

        return ComparisonFinding(
            field_name="address",
            source_document=source_doc,
            comparison_document=comp_doc,
            source_value=orig_a,
            comparison_value=orig_b,
            normalized_source_value=addr_a,
            normalized_comparison_value=addr_b,
            similarity_score=sim,
            status=status,
            needs_verification=needs_verification,
            explanation=explanation,
        )

    def compare_pair(
        self,
        doc_a: ExtractedDocument,
        doc_b: ExtractedDocument,
        fields: Optional[List[str]] = None,
    ) -> List[ComparisonFinding]:
        """Compare relevant fields between two extracted documents."""
        findings: List[ComparisonFinding] = []
        source_doc = self._get_doc_label(doc_a)
        comp_doc = self._get_doc_label(doc_b)

        target_fields = fields or ["name", "date_of_birth", "father_name", "mother_name", "address"]

        for f_name in target_fields:
            field_a = getattr(doc_a, f_name, None)
            field_b = getattr(doc_b, f_name, None)

            # If fields argument was explicitly provided, or at least one doc has the field, or it's name/dob
            if fields is not None or (field_a is not None or field_b is not None):
                val_a = field_a.normalized if field_a else None
                val_b = field_b.normalized if field_b else None
                orig_a = field_a.original if field_a else None
                orig_b = field_b.original if field_b else None

                if f_name in ("name", "father_name", "mother_name"):
                    finding = self.name_matcher.compare(
                        name_a=val_a,
                        name_b=val_b,
                        source_document=source_doc,
                        comparison_document=comp_doc,
                        field_name=f_name,
                        source_value=orig_a,
                        comparison_value=orig_b,
                    )
                elif f_name in ("date_of_birth", "issue_date", "expiry_date"):
                    finding = self.compare_date(
                        date_a=val_a,
                        date_b=val_b,
                        source_doc=source_doc,
                        comp_doc=comp_doc,
                        field_name=f_name,
                        orig_a=orig_a,
                        orig_b=orig_b,
                    )
                elif f_name == "address":
                    finding = self.compare_address(
                        addr_a=val_a,
                        addr_b=val_b,
                        source_doc=source_doc,
                        comp_doc=comp_doc,
                        orig_a=orig_a,
                        orig_b=orig_b,
                    )
                else:
                    # Generic exact text comparison
                    finding = self._compare_generic_text(
                        val_a=val_a,
                        val_b=val_b,
                        source_doc=source_doc,
                        comp_doc=comp_doc,
                        field_name=f_name,
                        orig_a=orig_a,
                        orig_b=orig_b,
                    )

                findings.append(finding)

        return findings

    def _compare_generic_text(
        self,
        val_a: Optional[Any],
        val_b: Optional[Any],
        source_doc: str,
        comp_doc: str,
        field_name: str,
        orig_a: Optional[Any],
        orig_b: Optional[Any],
    ) -> ComparisonFinding:
        """Compare generic fields by normalized equality."""
        if val_a is None or val_b is None:
            return ComparisonFinding(
                field_name=field_name,
                source_document=source_doc,
                comparison_document=comp_doc,
                source_value=orig_a,
                comparison_value=orig_b,
                normalized_source_value=val_a,
                normalized_comparison_value=val_b,
                similarity_score=None,
                status=MatchStatus.MISSING,
                needs_verification=False,
                explanation=f"Comparison could not be completed because {field_name} is missing from one document.",
            )

        if val_a == val_b:
            return ComparisonFinding(
                field_name=field_name,
                source_document=source_doc,
                comparison_document=comp_doc,
                source_value=orig_a,
                comparison_value=orig_b,
                normalized_source_value=val_a,
                normalized_comparison_value=val_b,
                similarity_score=1.0,
                status=MatchStatus.MATCH,
                needs_verification=False,
                explanation=f"{field_name.replace('_', ' ').capitalize()} matches exactly after normalization.",
            )
        else:
            return ComparisonFinding(
                field_name=field_name,
                source_document=source_doc,
                comparison_document=comp_doc,
                source_value=orig_a,
                comparison_value=orig_b,
                normalized_source_value=val_a,
                normalized_comparison_value=val_b,
                similarity_score=0.0,
                status=MatchStatus.MISMATCH,
                needs_verification=False,
                explanation=f"{field_name.replace('_', ' ').capitalize()} differs between the two documents.",
            )

    def match_documents(
        self,
        documents: List[ExtractedDocument],
        fields: Optional[List[str]] = None,
    ) -> List[ComparisonFinding]:
        """Perform deterministic cross-document matching without duplicate A/B and B/A pairs."""
        if len(documents) < 2:
            return []

        # Sort deterministically by document type priority, then document_id
        def doc_sort_key(doc: ExtractedDocument):
            priority = DOCUMENT_TYPE_ORDER.get(doc.document_type, 99)
            return (priority, doc.document_id)

        sorted_docs = sorted(documents, key=doc_sort_key)

        all_findings: List[ComparisonFinding] = []

        # Compare each unique pair systematically (i < j prevents duplicates)
        for i in range(len(sorted_docs)):
            for j in range(i + 1, len(sorted_docs)):
                doc_a = sorted_docs[i]
                doc_b = sorted_docs[j]
                pair_findings = self.compare_pair(doc_a, doc_b, fields=fields)
                all_findings.extend(pair_findings)

        return all_findings


def compare_documents(
    documents: List[ExtractedDocument],
    name_matcher: Optional[NameMatcher] = None,
    fields: Optional[List[str]] = None,
) -> List[ComparisonFinding]:
    """Convenience function to match fields across a list of documents."""
    matcher = CrossDocumentMatcher(name_matcher=name_matcher)
    return matcher.match_documents(documents, fields=fields)
