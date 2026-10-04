"""PreFlight AI pipeline orchestration.

Integrates preprocessing, classification, extraction, normalization,
cross-document matching, instruction extraction, and confidence verification
into a unified deterministic AI service.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from ai.classification.document_classifier import DocumentClassifier
from ai.exceptions import DocumentProcessingError
from ai.extraction.extractor import DocumentExtractor
from ai.extraction.vision_extractor import VisionExtractor
from ai.instructions.instruction_extractor import InstructionExtractor
from ai.matching.cross_document import CrossDocumentMatcher
from ai.normalization import DocumentNormalizer
from ai.preprocessing.document_loader import DocumentLoader
from ai.preprocessing.models import PreprocessedDocument
from ai.schemas.comparison import ComparisonFinding
from ai.schemas.document import ClassificationResult, DocumentType
from ai.schemas.extraction import ExtractedDocument, ExtractedField
from ai.schemas.instructions import InstructionRequirement
from ai.schemas.result import AIProcessingResult
from ai.verification.confidence_service import ConfidenceService, VerificationResult

# Deterministic document ordering priority
DOCUMENT_TYPE_ORDER: Dict[DocumentType, int] = {
    DocumentType.APPLICATION_FORM: 0,
    DocumentType.AADHAAR_OR_IDENTITY: 1,
    DocumentType.MARKSHEET: 2,
    DocumentType.INCOME_CERTIFICATE: 3,
    DocumentType.CASTE_CERTIFICATE: 4,
    DocumentType.PHOTOGRAPH: 5,
    DocumentType.INSTRUCTIONS: 6,
    DocumentType.UNKNOWN: 7,
}


class AIPipeline:
    """Orchestrates the end-to-end AI document validation pipeline for scholarship applications."""

    def __init__(
        self,
        loader: Optional[DocumentLoader] = None,
        classifier: Optional[DocumentClassifier] = None,
        extractor: Optional[DocumentExtractor] = None,
        normalizer: Optional[DocumentNormalizer] = None,
        matcher: Optional[CrossDocumentMatcher] = None,
        instruction_extractor: Optional[InstructionExtractor] = None,
        confidence_service: Optional[ConfidenceService] = None,
        vision_extractor: Optional[VisionExtractor] = None,
    ) -> None:
        """Initialize pipeline with modular components supporting dependency injection."""
        self.loader = loader or DocumentLoader()
        self.classifier = classifier or DocumentClassifier()
        self.vision_extractor = vision_extractor
        self.extractor = extractor or DocumentExtractor(
            vision_extractor=self.vision_extractor,
            classifier=self.classifier,
        )
        self.normalizer = normalizer or DocumentNormalizer()
        self.matcher = matcher or CrossDocumentMatcher()
        self.instruction_extractor = (
            instruction_extractor
            or InstructionExtractor(vision_extractor=self.vision_extractor)
        )
        self.confidence_service = confidence_service or ConfidenceService()

    def process(
        self,
        document_inputs: Optional[
            Union[List[Union[str, Path, PreprocessedDocument]], str, Path, PreprocessedDocument]
        ] = None,
        document_paths: Optional[List[Union[str, Path]]] = None,
        documents: Optional[List[PreprocessedDocument]] = None,
        allow_partial_failure: bool = False,
    ) -> AIProcessingResult:
        """Execute the end-to-end AI pipeline on input documents.

        Args:
            document_inputs: List or single instance of file paths or PreprocessedDocuments.
            document_paths: Optional explicit list of document file paths.
            documents: Optional explicit list of PreprocessedDocuments.
            allow_partial_failure: If True, preserves successfully processed documents
                and records failed documents as UNKNOWN rather than failing the entire run.

        Returns:
            AIProcessingResult: Unified deterministic result containing documents,
                cross_document_findings, instruction_requirements, and verification.
        """
        # 1. Normalize input collection
        raw_items: List[Union[str, Path, PreprocessedDocument]] = []
        if documents:
            raw_items.extend(documents)
        if document_paths:
            raw_items.extend(document_paths)
        if document_inputs:
            if isinstance(document_inputs, (list, tuple)):
                raw_items.extend(document_inputs)
            else:
                raw_items.append(document_inputs)

        if not raw_items:
            return AIProcessingResult(
                documents=[],
                cross_document_findings=[],
                instruction_requirements=[],
                verification=self.confidence_service._build_result([]),
            )

        # 2. Preprocess / Load documents
        preprocessed_docs: List[PreprocessedDocument] = []
        failed_items: List[Tuple[str, Exception]] = []

        for item in raw_items:
            if isinstance(item, PreprocessedDocument):
                preprocessed_docs.append(item)
            elif isinstance(item, (str, Path)):
                try:
                    preprocessed = self.loader.load(item)
                    preprocessed_docs.append(preprocessed)
                except Exception as exc:
                    if not allow_partial_failure:
                        raise
                    failed_items.append((str(item), exc))
            else:
                if not allow_partial_failure:
                    raise DocumentProcessingError(
                        f"Unsupported document input type: {type(item).__name__}"
                    )
                failed_items.append(
                    (str(item), DocumentProcessingError(f"Unsupported type: {type(item).__name__}"))
                )

        # 3. Classify, Extract, and Normalize each document
        extracted_documents: List[ExtractedDocument] = []
        classification_results: List[ClassificationResult] = []
        instruction_requirements: List[InstructionRequirement] = []

        for p_doc in preprocessed_docs:
            # 3a. Classification
            classification = self.classifier.classify(p_doc)
            classification_results.append(classification)
            doc_type = classification.document_type

            # 3b. Extraction
            extracted = self.extractor.extract_document(p_doc, document_type=doc_type)

            # Ensure document_id is populated from file_name if absent
            if not extracted.document_id or extracted.document_id == "unknown_doc":
                extracted.document_id = p_doc.file_name or "document"

            # 3c. Normalization
            normalized = self.normalizer.normalize_document(extracted)
            extracted_documents.append(normalized)

            # 3d. Instruction extraction (if instructions document)
            if doc_type == DocumentType.INSTRUCTIONS:
                reqs = self.instruction_extractor.extract_instructions(p_doc)
                instruction_requirements.extend(reqs)

        # 4. Handle partially failed documents (if permitted)
        for failed_path, exc in failed_items:
            failed_id = Path(failed_path).name if failed_path else "unknown_document"
            failed_doc = ExtractedDocument(
                document_id=failed_id,
                document_type=DocumentType.UNKNOWN,
                additional_fields={
                    "processing_error": ExtractedField(
                        field_name="processing_error",
                        original=str(exc),
                        normalized=None,
                        confidence=0.0,
                    )
                },
            )
            extracted_documents.append(failed_doc)
            classification_results.append(
                ClassificationResult(
                    document_type=DocumentType.UNKNOWN,
                    confidence=0.0,
                    needs_verification=True,
                )
            )

        # 5. Cross-Document Matching across applicant documents
        applicant_docs = [
            d for d in extracted_documents
            if d.document_type != DocumentType.INSTRUCTIONS
        ]
        cross_document_findings: List[ComparisonFinding] = []
        if len(applicant_docs) >= 2:
            cross_document_findings = self.matcher.match_documents(applicant_docs)

        # 6. Confidence and Verification aggregation
        verification_result: VerificationResult = self.confidence_service.evaluate_all(
            classifications=classification_results,
            documents=extracted_documents,
            findings=cross_document_findings,
        )

        # 7. Deterministic sorting of final outputs
        def doc_sort_key(doc: ExtractedDocument) -> Tuple[int, str]:
            priority = DOCUMENT_TYPE_ORDER.get(doc.document_type, 99)
            return (priority, doc.document_id or "")

        sorted_documents = sorted(extracted_documents, key=doc_sort_key)
        sorted_requirements = sorted(
            instruction_requirements,
            key=lambda r: r.requirement_id or "",
        )

        # 8. Assemble unified result
        return AIProcessingResult(
            documents=sorted_documents,
            cross_document_findings=cross_document_findings,
            instruction_requirements=sorted_requirements,
            verification=verification_result,
        )

    def run(self, document_inputs: Any) -> AIProcessingResult:
        """Alias for process() conforming to existing pipeline interface."""
        return self.process(document_inputs=document_inputs)


# Alias for explicit naming
PreFlightAIPipeline = AIPipeline

__all__ = [
    "AIPipeline",
    "PreFlightAIPipeline",
]
