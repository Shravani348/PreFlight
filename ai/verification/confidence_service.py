"""AI Confidence and Verification Service.

Evaluates document classifications, extracted fields, and cross-document comparison
findings to determine reliability and flag items requiring human verification.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator

from ai.schemas.comparison import ComparisonFinding, MatchStatus
from ai.schemas.document import ClassificationResult, DocumentType, Evidence
from ai.schemas.extraction import ExtractedDocument, ExtractedField


class ConfidenceLevel(str, Enum):
    """Categorized confidence level for AI outputs."""

    HIGH_CONFIDENCE = "high_confidence"
    MEDIUM_CONFIDENCE = "medium_confidence"
    LOW_CONFIDENCE = "low_confidence"
    MISSING = "missing"


class ConfidenceThresholds(BaseModel):
    """Configuration for confidence classification thresholds."""

    model_config = ConfigDict(extra="forbid")

    high_threshold: float = Field(default=0.90, ge=0.0, le=1.0)
    medium_threshold: float = Field(default=0.75, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_thresholds(self) -> "ConfidenceThresholds":
        """Ensure 0.0 <= medium_threshold < high_threshold <= 1.0."""
        if self.medium_threshold >= self.high_threshold:
            raise ValueError(
                f"Invalid threshold configuration: medium_threshold ({self.medium_threshold}) "
                f"must be strictly less than high_threshold ({self.high_threshold})."
            )
        return self


class VerificationItem(BaseModel):
    """Verification item detailing confidence and review necessity for an individual data point."""

    model_config = ConfigDict(extra="allow")

    source: str
    field_name: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    confidence_level: ConfidenceLevel
    needs_verification: bool = False
    reason: str
    evidence: List[Evidence] = Field(default_factory=list)


class VerificationResult(BaseModel):
    """Aggregated verification result for an application's AI processing outputs."""

    model_config = ConfigDict(extra="allow")

    items: List[VerificationItem] = Field(default_factory=list)
    verification_required: bool = False
    high_confidence_count: int = 0
    medium_confidence_count: int = 0
    low_confidence_count: int = 0
    missing_count: int = 0


class ConfidenceService:
    """Evaluates classification, extraction, and matching outputs for verification."""

    CORE_FIELDS = [
        "name",
        "date_of_birth",
        "father_name",
        "mother_name",
        "address",
        "certificate_number",
        "issue_date",
        "expiry_date",
        "marks",
        "percentage",
    ]

    def __init__(
        self,
        high_threshold: float = 0.90,
        medium_threshold: float = 0.75,
    ) -> None:
        """Initialize service with validated confidence thresholds."""
        self.thresholds = ConfidenceThresholds(
            high_threshold=high_threshold,
            medium_threshold=medium_threshold,
        )

    @property
    def high_threshold(self) -> float:
        """High confidence lower bound."""
        return self.thresholds.high_threshold

    @property
    def medium_threshold(self) -> float:
        """Medium confidence lower bound."""
        return self.thresholds.medium_threshold

    def get_confidence_level(self, confidence: Optional[float]) -> ConfidenceLevel:
        """Map a numeric confidence score to ConfidenceLevel enum."""
        if confidence is None:
            return ConfidenceLevel.MISSING
        if confidence >= self.high_threshold:
            return ConfidenceLevel.HIGH_CONFIDENCE
        if confidence >= self.medium_threshold:
            return ConfidenceLevel.MEDIUM_CONFIDENCE
        return ConfidenceLevel.LOW_CONFIDENCE

    def evaluate_field(
        self,
        field: Optional[ExtractedField],
        field_name: Optional[str] = None,
        source: str = "document",
    ) -> VerificationItem:
        """Evaluate an ExtractedField and return a VerificationItem."""
        target_name = (field.field_name if field else None) or field_name or "unknown_field"

        if field is None:
            return VerificationItem(
                source=source,
                field_name=target_name,
                confidence=None,
                confidence_level=ConfidenceLevel.MISSING,
                needs_verification=True,
                reason="Required value is missing.",
                evidence=[],
            )

        # Missing if both original and normalized are None
        if field.original is None and field.normalized is None:
            return VerificationItem(
                source=source,
                field_name=target_name,
                confidence=None,
                confidence_level=ConfidenceLevel.MISSING,
                needs_verification=True,
                reason="Required value is missing.",
                evidence=field.evidence,
            )

        # Missing confidence score
        if field.confidence is None:
            return VerificationItem(
                source=source,
                field_name=target_name,
                confidence=None,
                confidence_level=ConfidenceLevel.MISSING,
                needs_verification=True,
                reason="Field has no confidence score.",
                evidence=field.evidence,
            )

        level = self.get_confidence_level(field.confidence)
        if level == ConfidenceLevel.HIGH_CONFIDENCE:
            return VerificationItem(
                source=source,
                field_name=target_name,
                confidence=field.confidence,
                confidence_level=level,
                needs_verification=False,
                reason="Extracted field has high confidence.",
                evidence=field.evidence,
            )
        elif level == ConfidenceLevel.MEDIUM_CONFIDENCE:
            return VerificationItem(
                source=source,
                field_name=target_name,
                confidence=field.confidence,
                confidence_level=level,
                needs_verification=True,
                reason="Extracted field has medium confidence.",
                evidence=field.evidence,
            )
        else:
            return VerificationItem(
                source=source,
                field_name=target_name,
                confidence=field.confidence,
                confidence_level=level,
                needs_verification=True,
                reason="Extracted field has low confidence.",
                evidence=field.evidence,
            )

    def evaluate_classification(
        self,
        classification: ClassificationResult,
        source: str = "classification",
    ) -> VerificationItem:
        """Evaluate a ClassificationResult and return a VerificationItem."""
        if classification.document_type == DocumentType.UNKNOWN:
            level = self.get_confidence_level(classification.confidence)
            return VerificationItem(
                source=source,
                field_name="document_type",
                confidence=classification.confidence,
                confidence_level=level,
                needs_verification=True,
                reason="Document type is unknown.",
                evidence=classification.evidence,
            )

        level = self.get_confidence_level(classification.confidence)
        needs_verif = classification.needs_verification or (level != ConfidenceLevel.HIGH_CONFIDENCE)

        if classification.needs_verification and level == ConfidenceLevel.HIGH_CONFIDENCE:
            reason = "Document classification requires verification."
        elif level == ConfidenceLevel.HIGH_CONFIDENCE:
            reason = "Document classification has high confidence."
        elif level == ConfidenceLevel.MEDIUM_CONFIDENCE:
            reason = "Document classification is uncertain."
        elif level == ConfidenceLevel.LOW_CONFIDENCE:
            reason = "Document classification is uncertain."
        else:
            reason = "Document classification confidence is missing."

        return VerificationItem(
            source=source,
            field_name="document_type",
            confidence=classification.confidence,
            confidence_level=level,
            needs_verification=needs_verif,
            reason=reason,
            evidence=classification.evidence,
        )

    def evaluate_finding(
        self,
        finding: ComparisonFinding,
    ) -> VerificationItem:
        """Translate a ComparisonFinding into a VerificationItem."""
        source_label = f"{finding.source_document} vs {finding.comparison_document}"
        status = finding.status

        if status == MatchStatus.MATCH:
            return VerificationItem(
                source=source_label,
                field_name=finding.field_name,
                confidence=finding.similarity_score if finding.similarity_score is not None else 1.0,
                confidence_level=ConfidenceLevel.HIGH_CONFIDENCE,
                needs_verification=False,
                reason="Cross-document values match.",
                evidence=[],
            )
        elif status == MatchStatus.LIKELY_MATCH:
            return VerificationItem(
                source=source_label,
                field_name=finding.field_name,
                confidence=finding.similarity_score,
                confidence_level=ConfidenceLevel.MEDIUM_CONFIDENCE,
                needs_verification=True,
                reason="Cross-document values require verification.",
                evidence=[],
            )
        elif status == MatchStatus.VERIFICATION_REQUIRED:
            return VerificationItem(
                source=source_label,
                field_name=finding.field_name,
                confidence=finding.similarity_score,
                confidence_level=ConfidenceLevel.MEDIUM_CONFIDENCE,
                needs_verification=True,
                reason="Cross-document values require verification.",
                evidence=[],
            )
        elif status == MatchStatus.MISMATCH:
            return VerificationItem(
                source=source_label,
                field_name=finding.field_name,
                confidence=finding.similarity_score if finding.similarity_score is not None else 0.0,
                confidence_level=ConfidenceLevel.LOW_CONFIDENCE,
                needs_verification=True,
                reason="Cross-document values do not match.",
                evidence=[],
            )
        else:  # MatchStatus.MISSING
            return VerificationItem(
                source=source_label,
                field_name=finding.field_name,
                confidence=None,
                confidence_level=ConfidenceLevel.MISSING,
                needs_verification=True,
                reason="Required value is missing.",
                evidence=[],
            )

    def evaluate_document(
        self,
        document: ExtractedDocument,
        required_fields: Optional[List[str]] = None,
    ) -> List[VerificationItem]:
        """Evaluate fields in an ExtractedDocument."""
        items: List[VerificationItem] = []
        source_label = document.document_id or "document"

        # Check required fields explicitly if provided
        if required_fields:
            for req_field in required_fields:
                field_obj = getattr(document, req_field, None)
                if field_obj is None and req_field in document.additional_fields:
                    field_obj = document.additional_fields[req_field]
                items.append(
                    self.evaluate_field(
                        field=field_obj,
                        field_name=req_field,
                        source=source_label,
                    )
                )
            return items

        # Default: evaluate all present core fields in canonical order
        for field_name in self.CORE_FIELDS:
            field_obj = getattr(document, field_name, None)
            if field_obj is not None:
                items.append(
                    self.evaluate_field(
                        field=field_obj,
                        field_name=field_name,
                        source=source_label,
                    )
                )

        # Evaluate additional fields sorted deterministically
        for add_name in sorted(document.additional_fields.keys()):
            field_obj = document.additional_fields[add_name]
            if field_obj is not None:
                items.append(
                    self.evaluate_field(
                        field=field_obj,
                        field_name=add_name,
                        source=source_label,
                    )
                )

        return items

    def _build_result(self, items: List[VerificationItem]) -> VerificationResult:
        """Construct VerificationResult with aggregate counts and verification_required flag."""
        high_c = sum(1 for i in items if i.confidence_level == ConfidenceLevel.HIGH_CONFIDENCE)
        med_c = sum(1 for i in items if i.confidence_level == ConfidenceLevel.MEDIUM_CONFIDENCE)
        low_c = sum(1 for i in items if i.confidence_level == ConfidenceLevel.LOW_CONFIDENCE)
        miss_c = sum(1 for i in items if i.confidence_level == ConfidenceLevel.MISSING)
        verif_req = any(i.needs_verification for i in items)

        return VerificationResult(
            items=items,
            verification_required=verif_req,
            high_confidence_count=high_c,
            medium_confidence_count=med_c,
            low_confidence_count=low_c,
            missing_count=miss_c,
        )

    def evaluate_documents(
        self,
        documents: List[ExtractedDocument],
        required_fields: Optional[List[str]] = None,
    ) -> VerificationResult:
        """Batch evaluate multiple ExtractedDocument objects sorted deterministically."""
        items: List[VerificationItem] = []
        sorted_docs = sorted(documents, key=lambda d: d.document_id or "")
        for doc in sorted_docs:
            items.extend(self.evaluate_document(doc, required_fields=required_fields))
        return self._build_result(items)

    def evaluate_all(
        self,
        classifications: Optional[List[ClassificationResult]] = None,
        documents: Optional[List[ExtractedDocument]] = None,
        findings: Optional[List[ComparisonFinding]] = None,
        required_fields: Optional[List[str]] = None,
    ) -> VerificationResult:
        """Unified aggregate evaluation across classifications, extractions, and findings."""
        items: List[VerificationItem] = []

        # 1. Classifications (sorted by document_type value)
        if classifications:
            sorted_classes = sorted(
                classifications,
                key=lambda c: c.document_type.value if hasattr(c.document_type, "value") else str(c.document_type),
            )
            for c in sorted_classes:
                items.append(self.evaluate_classification(c))

        # 2. Extracted Documents (sorted by document_id)
        if documents:
            sorted_docs = sorted(documents, key=lambda d: d.document_id or "")
            for doc in sorted_docs:
                items.extend(self.evaluate_document(doc, required_fields=required_fields))

        # 3. Cross-Document Findings (sorted by source_document, comparison_document, field_name)
        if findings:
            sorted_findings = sorted(
                findings,
                key=lambda f: (f.source_document, f.comparison_document, f.field_name),
            )
            for f in sorted_findings:
                items.append(self.evaluate_finding(f))

        return self._build_result(items)


# Alias for explicit naming
VerificationService = ConfidenceService
