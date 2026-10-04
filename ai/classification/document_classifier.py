"""Deterministic, explainable document classifier for PreFlight scholarship applications."""

import re
from typing import Dict, List, Optional, Tuple
from ai.exceptions import DocumentProcessingError
from ai.preprocessing.models import PreprocessedDocument
from ai.schemas.document import ClassificationResult, DocumentType, Evidence
from ai.classification.classification_signals import (
    CLASSIFICATION_SIGNALS,
    PHOTO_FILENAME_CLUES,
    Signal,
)


class DocumentClassifier:
    """Classifies preprocessed documents using deterministic signal matching and evidence extraction."""

    def __init__(self, verification_threshold: float = 0.75) -> None:
        """Initialize classifier with a configurable confidence verification threshold."""
        self.verification_threshold = verification_threshold

    def classify(self, document: PreprocessedDocument) -> ClassificationResult:
        """Classify a preprocessed document into a supported DocumentType with confidence and evidence."""
        if not isinstance(document, PreprocessedDocument):
            raise DocumentProcessingError(
                f"DocumentClassifier expects a PreprocessedDocument, got {type(document).__name__}"
            )

        # 1. Handle documents with usable text (or partial text)
        if document.full_text and document.full_text.strip():
            return self._classify_by_text(document)

        # 2. Handle image documents (or scanned PDFs with images)
        if document.images:
            return self._classify_by_image(document)

        # 3. Empty document with neither text nor images
        return ClassificationResult(
            document_type=DocumentType.UNKNOWN,
            confidence=0.0,
            needs_verification=True,
            evidence=[
                Evidence(
                    source_document=document.file_name,
                    page_number=1 if document.page_count > 0 else None,
                    snippet="Document contains neither extractable text nor readable images",
                )
            ],
        )

    def _classify_by_text(self, document: PreprocessedDocument) -> ClassificationResult:
        """Score text signals across document pages and evaluate confidence and conflicts."""
        scores: Dict[DocumentType, float] = {doc_type: 0.0 for doc_type in CLASSIFICATION_SIGNALS}
        evidence_by_type: Dict[DocumentType, List[Evidence]] = {
            doc_type: [] for doc_type in CLASSIFICATION_SIGNALS
        }

        # Scan each page for signal matches
        for page in document.pages:
            page_text = (page.text or "").strip()
            if not page_text:
                continue

            lower_text = page_text.lower()
            for doc_type, signals in CLASSIFICATION_SIGNALS.items():
                for signal in signals:
                    pattern = signal.pattern.lower()
                    if self._matches_pattern(lower_text, pattern):
                        scores[doc_type] += signal.weight
                        if len(evidence_by_type[doc_type]) < 3:
                            snippet = self._extract_snippet(page_text, pattern)
                            evidence_by_type[doc_type].append(
                                Evidence(
                                    source_document=document.file_name,
                                    page_number=page.page_number,
                                    snippet=snippet,
                                )
                            )

        # Sort categories by accumulated signal scores
        sorted_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        top_type, top_score = sorted_scores[0]
        runner_up_type, runner_up_score = sorted_scores[1]

        # Case A: No text signals matched
        if top_score == 0.0:
            evidence = []
            if document.requires_vision_processing:
                evidence.append(
                    Evidence(
                        source_document=document.file_name,
                        page_number=1,
                        snippet="Scanned or visual document requires vision processing",
                    )
                )
            return ClassificationResult(
                document_type=DocumentType.UNKNOWN,
                confidence=0.10 if document.requires_vision_processing else 0.0,
                needs_verification=True,
                evidence=evidence,
            )

        # Case B: Conflicting / Ambiguous signals
        # If runner up has strong evidence (score >= 2.5) or if relative margin is narrow (< 35%)
        is_close_margin = (
            runner_up_score > 0.0 and ((top_score - runner_up_score) / top_score) < 0.35
        )
        has_competing_strong_signals = (
            runner_up_score >= 2.5 and top_score <= (3.5 * runner_up_score)
        )

        if is_close_margin or has_competing_strong_signals:
            # Exact tie -> return UNKNOWN with combined evidence
            if top_score == runner_up_score:
                combined_evidence = (
                    evidence_by_type[top_type][:2] + evidence_by_type[runner_up_type][:2]
                )
                return ClassificationResult(
                    document_type=DocumentType.UNKNOWN,
                    confidence=0.40,
                    needs_verification=True,
                    evidence=combined_evidence,
                )

            # Close contention: select top type with low confidence and require verification
            confidence = 0.55
            combined_evidence = (
                evidence_by_type[top_type][:2] + evidence_by_type[runner_up_type][:2]
            )
            return ClassificationResult(
                document_type=top_type,
                confidence=round(confidence, 2),
                needs_verification=True,
                evidence=combined_evidence,
            )

        # Case C: Clear signal winner
        confidence = self._calculate_confidence(top_score)
        needs_verification = (confidence < self.verification_threshold) or (
            top_type == DocumentType.UNKNOWN
        )

        return ClassificationResult(
            document_type=top_type,
            confidence=round(confidence, 2),
            needs_verification=needs_verification,
            evidence=evidence_by_type[top_type],
        )

    def _classify_by_image(self, document: PreprocessedDocument) -> ClassificationResult:
        """Classify image-only documents using filename clues, dimensions, and aspect ratio."""
        file_name_lower = document.file_name.lower()
        width = document.metadata.get("width")
        height = document.metadata.get("height")

        # 1. Explicit photograph clues in filename
        for clue in PHOTO_FILENAME_CLUES:
            if clue in file_name_lower:
                return ClassificationResult(
                    document_type=DocumentType.PHOTOGRAPH,
                    confidence=0.92,
                    needs_verification=False,
                    evidence=[
                        Evidence(
                            source_document=document.file_name,
                            page_number=1,
                            snippet=f"File name '{document.file_name}' contains explicit photo indicator '{clue}'",
                        )
                    ],
                )

        # 2. Check aspect ratio if width and height metadata are available
        if width and height and height > 0:
            aspect_ratio = width / height
            # Standard passport / portrait photo aspect ratio: ~0.65 to 0.95
            if 0.65 <= aspect_ratio <= 0.95 and document.page_count == 1:
                return ClassificationResult(
                    document_type=DocumentType.PHOTOGRAPH,
                    confidence=0.68,
                    needs_verification=True,  # Low confidence without textual/filename confirmation
                    evidence=[
                        Evidence(
                            source_document=document.file_name,
                            page_number=1,
                            snippet=f"Dimensions {width}x{height} (aspect ratio {aspect_ratio:.2f}) align with portrait photograph",
                        )
                    ],
                )

        # 3. Image without specific photograph characteristics -> unknown
        return ClassificationResult(
            document_type=DocumentType.UNKNOWN,
            confidence=0.25,
            needs_verification=True,
            evidence=[
                Evidence(
                    source_document=document.file_name,
                    page_number=1,
                    snippet="Visual document without clear text or photograph characteristics",
                )
            ],
        )

    def _matches_pattern(self, text: str, pattern: str) -> bool:
        """Check if signal pattern appears in text with word boundary considerations."""
        if " " in pattern:
            return pattern in text
        # Word boundary check supporting both ASCII and Indic script characters (including combining marks)
        regex = rf"(?<![\w\u0900-\u097f]){re.escape(pattern)}(?![\w\u0900-\u097f])"
        return bool(re.search(regex, text))

    def _extract_snippet(self, page_text: str, pattern: str) -> str:
        """Extract a readable context snippet around the matched pattern."""
        idx = page_text.lower().find(pattern)
        if idx == -1:
            return pattern
        start = max(0, idx - 25)
        end = min(len(page_text), idx + len(pattern) + 25)
        prefix = "..." if start > 0 else ""
        suffix = "..." if end < len(page_text) else ""
        snippet = page_text[start:end].replace("\n", " ").strip()
        return f"{prefix}{snippet}{suffix}"

    def _calculate_confidence(self, score: float) -> float:
        """Convert accumulated signal score to a calibrated 0.0 - 1.0 confidence value."""
        if score <= 0.0:
            return 0.0
        if score >= 7.0:
            return min(0.98, 0.90 + (score - 7.0) * 0.02)
        if score >= 4.0:
            return 0.80 + (score - 4.0) * 0.033
        if score >= 2.0:
            return 0.60 + (score - 2.0) * 0.10
        return 0.35 + (score * 0.12)
