"""Document information extraction service for scholarship applications."""

from typing import Any, Dict, List, Optional
from ai.classification.document_classifier import DocumentClassifier
from ai.exceptions import DocumentProcessingError, ExtractionError
from ai.extraction.prompts import get_extraction_prompt
from ai.extraction.vision_extractor import VisionExtractor
from ai.preprocessing.models import PreprocessedDocument
from ai.schemas.document import DocumentType, Evidence
from ai.schemas.extraction import ExtractedDocument, ExtractedField


class DocumentExtractor:
    """Coordinates information extraction from preprocessed scholarship documents."""

    CORE_FIELD_NAMES = {
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
    }

    def __init__(
        self,
        vision_extractor: Optional[VisionExtractor] = None,
        classifier: Optional[DocumentClassifier] = None,
    ) -> None:
        """Initialize DocumentExtractor with vision adapter and document classifier."""
        self.vision_extractor = vision_extractor or VisionExtractor()
        self.classifier = classifier or DocumentClassifier()

    def extract_document(
        self,
        document: PreprocessedDocument,
        document_type: Optional[DocumentType] = None,
    ) -> ExtractedDocument:
        """Extract structured fields from a preprocessed document.

        Args:
            document: Preprocessed document containing text and/or images.
            document_type: Optional document type classification. If None,
                the classifier will determine the type automatically.

        Returns:
            ExtractedDocument: Populated document with standard and additional fields.

        Raises:
            DocumentProcessingError: If input is not a PreprocessedDocument.
            ExtractionError: If extraction fails or model returns malformed data.
        """
        if not isinstance(document, PreprocessedDocument):
            raise DocumentProcessingError(
                f"DocumentExtractor expects a PreprocessedDocument, got {type(document).__name__}"
            )

        # 1. Determine document type
        if document_type is None:
            classification = self.classifier.classify(document)
            document_type = classification.document_type

        document_id = document.file_name

        # 2. Photograph special handling: avoid unnecessary OCR/LLM calls
        if document_type == DocumentType.PHOTOGRAPH:
            return self._extract_photograph(document, document_id)

        # 3. Retrieve prompt instructions
        prompt = get_extraction_prompt(document_type)

        # 4. Invoke vision / text model adapter
        raw_output = self.vision_extractor.extract(
            prompt=prompt,
            text_content=document.full_text,
            images=document.images,
            document_type=document_type,
        )

        if not isinstance(raw_output, dict):
            raise ExtractionError(
                f"Malformed model response: expected dict, got {type(raw_output).__name__}"
            )

        # 5. Build ExtractedDocument
        return self._build_extracted_document(
            document=document,
            document_id=document_id,
            document_type=document_type,
            raw_output=raw_output,
        )

    def _extract_photograph(
        self,
        document: PreprocessedDocument,
        document_id: str,
    ) -> ExtractedDocument:
        """Extract metadata for photograph documents without OCR."""
        additional_fields: Dict[str, ExtractedField] = {}

        # Preserve image metadata if available
        meta = document.metadata or {}
        for key, val in meta.items():
            if val is not None:
                additional_fields[key] = ExtractedField(
                    field_name=key,
                    original=val,
                    normalized=None,
                    confidence=1.0,
                    evidence=[
                        Evidence(
                            source_document=document.file_name,
                            page_number=1,
                            snippet=f"Image metadata {key}={val}",
                        )
                    ],
                )

        return ExtractedDocument(
            document_id=document_id,
            document_type=DocumentType.PHOTOGRAPH,
            additional_fields=additional_fields,
        )

    def _build_extracted_document(
        self,
        document: PreprocessedDocument,
        document_id: str,
        document_type: DocumentType,
        raw_output: Dict[str, Any],
    ) -> ExtractedDocument:
        """Parse structured model response and map fields cleanly into ExtractedDocument."""
        extracted_doc = ExtractedDocument(
            document_id=document_id,
            document_type=document_type,
        )

        confidence_map = raw_output.get("confidence_scores", {})
        evidence_map = raw_output.get("evidence", {})

        # Process core standard fields
        for field_name in self.CORE_FIELD_NAMES:
            if field_name in raw_output:
                raw_field_val = raw_output[field_name]
                field_obj = self._parse_field(
                    field_name=field_name,
                    raw_data=raw_field_val,
                    fallback_confidence=confidence_map.get(field_name),
                    fallback_snippet=evidence_map.get(field_name),
                    document_name=document.file_name,
                )
                setattr(extracted_doc, field_name, field_obj)

        # Process additional fields
        additional_fields: Dict[str, ExtractedField] = {}

        # 1. Check explicit "additional_fields" dictionary in response
        if isinstance(raw_output.get("additional_fields"), dict):
            for add_key, add_val in raw_output["additional_fields"].items():
                parsed = self._parse_field(
                    field_name=add_key,
                    raw_data=add_val,
                    fallback_confidence=confidence_map.get(add_key),
                    fallback_snippet=evidence_map.get(add_key),
                    document_name=document.file_name,
                )
                if parsed is not None:
                    additional_fields[add_key] = parsed

        # 2. Check top-level extra keys
        for key, val in raw_output.items():
            if key not in self.CORE_FIELD_NAMES and key not in (
                "confidence_scores",
                "evidence",
                "additional_fields",
            ):
                if key not in additional_fields:
                    parsed = self._parse_field(
                        field_name=key,
                        raw_data=val,
                        fallback_confidence=confidence_map.get(key),
                        fallback_snippet=evidence_map.get(key),
                        document_name=document.file_name,
                    )
                    if parsed is not None:
                        additional_fields[key] = parsed

        extracted_doc.additional_fields = additional_fields
        return extracted_doc

    def _parse_field(
        self,
        field_name: str,
        raw_data: Any,
        fallback_confidence: Optional[float],
        fallback_snippet: Optional[str],
        document_name: str,
    ) -> Optional[ExtractedField]:
        """Convert raw field payload into ExtractedField while strictly respecting nulls."""
        if raw_data is None:
            return None

        original: Optional[Any] = None
        confidence: Optional[float] = None
        evidence_list: List[Evidence] = []

        # Format A: Rich object {"value": "...", "confidence": 0.95, "snippet": "..."}
        if isinstance(raw_data, dict):
            original = raw_data.get("value", raw_data.get("original"))
            if original is None:
                return None

            raw_conf = raw_data.get("confidence", fallback_confidence)
            confidence = self._sanitize_confidence(raw_conf)

            # Evidence extraction
            if "evidence" in raw_data and isinstance(raw_data["evidence"], list):
                for ev in raw_data["evidence"]:
                    if isinstance(ev, dict):
                        evidence_list.append(
                            Evidence(
                                source_document=ev.get("source_document", document_name),
                                page_number=ev.get("page_number", 1),
                                snippet=ev.get("snippet"),
                            )
                        )
                    elif isinstance(ev, Evidence):
                        evidence_list.append(ev)
            elif "snippet" in raw_data and raw_data["snippet"]:
                evidence_list.append(
                    Evidence(
                        source_document=raw_data.get("source_document", document_name),
                        page_number=raw_data.get("page_number", 1),
                        snippet=str(raw_data["snippet"]),
                    )
                )

        # Format B: Direct scalar value (str, int, float, list, etc.)
        else:
            original = raw_data
            confidence = self._sanitize_confidence(fallback_confidence)
            if fallback_snippet:
                evidence_list.append(
                    Evidence(
                        source_document=document_name,
                        page_number=1,
                        snippet=str(fallback_snippet),
                    )
                )

        return ExtractedField(
            field_name=field_name,
            original=original,
            normalized=None,  # Explicitly deferred to Task 6 (Normalization)
            confidence=confidence,
            evidence=evidence_list,
        )

    def _sanitize_confidence(self, conf: Any) -> Optional[float]:
        """Ensure confidence is between 0.0 and 1.0 or None."""
        if conf is None:
            return None
        try:
            val = float(conf)
            if 0.0 <= val <= 1.0:
                return round(val, 2)
            # If outside 0-1, clamp safely to valid boundaries
            return max(0.0, min(1.0, round(val, 2)))
        except (ValueError, TypeError):
            return None
