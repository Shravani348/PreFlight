"""Instruction extractor for official scholarship guidelines and brochures."""

import hashlib
import re
from typing import Any, Dict, List, Optional, Union
from PIL import Image

from ai.exceptions import ExtractionError
from ai.extraction.vision_extractor import VisionExtractor
from ai.preprocessing.models import PreprocessedDocument, PreprocessedPage
from ai.schemas.document import DocumentType, Evidence
from ai.schemas.instructions import InstructionRequirement

# Supported document keyword mapping
DOCUMENT_KEYWORDS = [
    (
        DocumentType.AADHAAR_OR_IDENTITY,
        [r"\baadhaar\b", r"\baadhar\b", r"\bidentity\s+proof\b", r"\buidai\b", r"\bid\s+proof\b"],
    ),
    (
        DocumentType.MARKSHEET,
        [r"\bmarksheet\b", r"\bmark\s+sheet\b", r"\bgrade\s+card\b", r"\bacademic\s+transcript\b"],
    ),
    (
        DocumentType.INCOME_CERTIFICATE,
        [r"\bincome\s+certificate\b", r"\bfamily\s+income\b"],
    ),
    (
        DocumentType.CASTE_CERTIFICATE,
        [r"\bcaste\s+certificate\b", r"\bcommunity\s+certificate\b", r"\bcategory\s+certificate\b"],
    ),
    (
        DocumentType.PHOTOGRAPH,
        [r"\bphotograph\b", r"\bpassport[- ]size\s+photo(?:graph)?\b", r"\bphoto\b"],
    ),
    (
        DocumentType.APPLICATION_FORM,
        [r"\bapplication\s+form\b", r"\bprinted\s+application\b"],
    ),
]


def parse_file_size(size_str: Optional[str]) -> Optional[int]:
    """Safely convert file size statements (e.g., '200 KB', '2 MB', '1.5 MB') to bytes."""
    if not size_str or not isinstance(size_str, str):
        return None

    match = re.search(r"(\d+(?:\.\d+)?)\s*(B|KB|MB|GB)\b", size_str, re.IGNORECASE)
    if not match:
        return None

    val = float(match.group(1))
    unit = match.group(2).upper()

    multipliers = {
        "B": 1,
        "KB": 1024,
        "MB": 1024 * 1024,
        "GB": 1024 * 1024 * 1024,
    }
    multiplier = multipliers.get(unit, 1)
    return int(val * multiplier)


def parse_formats(text: Optional[str]) -> List[str]:
    """Extract accepted file format extensions from text without guessing."""
    if not text or not isinstance(text, str):
        return []

    formats: List[str] = []
    tokens = re.findall(r"\b(pdf|jpg|jpeg|png)\b", text, re.IGNORECASE)
    for tok in tokens:
        lowered = tok.lower()
        if lowered not in formats:
            formats.append(lowered)
    return formats


def generate_requirement_id(
    requirement_type: str,
    document_type: Optional[DocumentType] = None,
    key_content: str = "",
) -> str:
    """Generate a deterministic requirement ID from content tokens."""
    doc_str = document_type.value if (document_type and hasattr(document_type, "value")) else "general"
    clean_content = re.sub(r"[^\w\s]", "", key_content.lower()).strip()
    slug_tokens = clean_content.split()[:4]
    slug = "_".join(slug_tokens) if slug_tokens else "req"
    content_hash = hashlib.sha256(clean_content.encode("utf-8")).hexdigest()[:8]
    return f"req_{doc_str}_{requirement_type}_{slug}_{content_hash}"


class InstructionExtractor:
    """Extracts application requirements and criteria from official scholarship instructions."""

    def __init__(self, vision_extractor: Optional[VisionExtractor] = None):
        """Initialize extractor with optional vision adapter boundary."""
        self.vision_extractor = vision_extractor

    def extract_from_text(
        self,
        text: str,
        page_number: int = 1,
        source_document: str = "instructions.pdf",
    ) -> List[InstructionRequirement]:
        """Extract requirements deterministically from text content of a single page."""
        if not text or not text.strip():
            return []

        requirements: List[InstructionRequirement] = []
        # Split text into meaningful lines / sentences
        lines = [line.strip() for line in re.split(r"[\n\r]+|[.](?:\s+|$)", text) if line.strip()]

        for line in lines:
            line_reqs = self._parse_line(line, page_number=page_number, source_document=source_document)
            requirements.extend(line_reqs)

        return requirements

    def _parse_line(
        self,
        line: str,
        page_number: int,
        source_document: str,
    ) -> List[InstructionRequirement]:
        """Extract specific requirement types present in an individual sentence or line."""
        found: List[InstructionRequirement] = []
        line_formats = parse_formats(line)
        line_size = parse_file_size(line)

        # 1. Eligibility Check (e.g. minimum percentage requirement)
        eligibility_match = re.search(
            r"(?:at\s+least|minimum|min(?:imum)?\s+of|secured)\s*(\d+(?:\.\d+)?)\s*%",
            line,
            re.IGNORECASE,
        )
        if eligibility_match:
            min_pct = float(eligibility_match.group(1))
            req_id = generate_requirement_id("eligibility", None, line)
            evidence = [Evidence(source_document=source_document, page_number=page_number, snippet=line)]
            found.append(
                InstructionRequirement(
                    requirement_id=req_id,
                    requirement_type="eligibility",
                    document_type_requested=None,
                    is_required=True,
                    accepted_formats=[],
                    max_file_size_bytes=None,
                    constraints={"minimum_percentage": min_pct},
                    evidence=evidence,
                )
            )

        # 2. Known Scholarship Document Check
        matched_doc_type: Optional[DocumentType] = None
        for doc_type, patterns in DOCUMENT_KEYWORDS:
            for pat in patterns:
                if re.search(pat, line, re.IGNORECASE):
                    matched_doc_type = doc_type
                    break
            if matched_doc_type:
                break

        if matched_doc_type:
            req_type = "photograph" if matched_doc_type == DocumentType.PHOTOGRAPH else "required_document"
            constraints: Dict[str, Any] = {}

            # Conditionality
            is_conditional = bool(
                re.search(
                    r"\b(?:for applicable categories|if applicable|where applicable|reserved category|optional)\b",
                    line,
                    re.IGNORECASE,
                )
            )
            if is_conditional:
                constraints["conditional"] = True
                constraints["condition"] = "for applicable categories"

            # Photograph specific constraints
            if matched_doc_type == DocumentType.PHOTOGRAPH:
                if re.search(r"passport[- ]size", line, re.IGNORECASE):
                    constraints["dimensions"] = "passport size"
                if re.search(r"white\s+background", line, re.IGNORECASE):
                    constraints["background"] = "white"
                elif re.search(r"light\s+background", line, re.IGNORECASE):
                    constraints["background"] = "light"

            req_id = generate_requirement_id(req_type, matched_doc_type, line)
            evidence = [Evidence(source_document=source_document, page_number=page_number, snippet=line)]

            found.append(
                InstructionRequirement(
                    requirement_id=req_id,
                    requirement_type=req_type,
                    document_type_requested=matched_doc_type,
                    is_required=True,
                    accepted_formats=line_formats,
                    max_file_size_bytes=line_size,
                    constraints=constraints,
                    evidence=evidence,
                )
            )
            return found

        # 3. Unknown Document Check (e.g. "Bonafide certificate is required")
        unknown_match = re.search(
            r"\b([a-zA-Z]+(?:\s+[a-zA-Z]+)?\s+certificate)\b\s*(?:is mandatory|must be uploaded|must be submitted|is required)",
            line,
            re.IGNORECASE,
        )
        if unknown_match:
            doc_name = unknown_match.group(1).lower()
            req_id = generate_requirement_id("required_document", DocumentType.UNKNOWN, line)
            evidence = [Evidence(source_document=source_document, page_number=page_number, snippet=line)]
            found.append(
                InstructionRequirement(
                    requirement_id=req_id,
                    requirement_type="required_document",
                    document_type_requested=DocumentType.UNKNOWN,
                    is_required=True,
                    accepted_formats=line_formats,
                    max_file_size_bytes=line_size,
                    constraints={"document_name": doc_name},
                    evidence=evidence,
                )
            )
            return found

        # 4. Standalone File Format Statement (e.g. "Documents must be uploaded in PDF format.")
        if line_formats and re.search(r"\b(?:format|documents?|files?)\b", line, re.IGNORECASE):
            req_id = generate_requirement_id("file_format", None, line)
            evidence = [Evidence(source_document=source_document, page_number=page_number, snippet=line)]
            found.append(
                InstructionRequirement(
                    requirement_id=req_id,
                    requirement_type="file_format",
                    document_type_requested=None,
                    is_required=True,
                    accepted_formats=line_formats,
                    max_file_size_bytes=None,
                    constraints={},
                    evidence=evidence,
                )
            )

        # 5. Standalone File Size Statement (e.g. "Maximum file size is 2 MB.")
        if line_size and re.search(r"\b(?:size|limit|maximum|max)\b", line, re.IGNORECASE):
            req_id = generate_requirement_id("file_size", None, line)
            evidence = [Evidence(source_document=source_document, page_number=page_number, snippet=line)]
            found.append(
                InstructionRequirement(
                    requirement_id=req_id,
                    requirement_type="file_size",
                    document_type_requested=None,
                    is_required=True,
                    accepted_formats=[],
                    max_file_size_bytes=line_size,
                    constraints={},
                    evidence=evidence,
                )
            )

        return found

    def _merge_duplicate_requirements(
        self,
        requirements: List[InstructionRequirement],
    ) -> List[InstructionRequirement]:
        """Merge identical requirements across pages, preserving evidence and keeping conflicts separate."""
        merged: List[InstructionRequirement] = []

        for req in requirements:
            # Check for existing match
            duplicate: Optional[InstructionRequirement] = None
            for existing in merged:
                if (
                    existing.requirement_type == req.requirement_type
                    and existing.document_type_requested == req.document_type_requested
                    and existing.accepted_formats == req.accepted_formats
                    and existing.max_file_size_bytes == req.max_file_size_bytes
                    and existing.constraints == req.constraints
                ):
                    duplicate = existing
                    break

            if duplicate is not None:
                # Merge evidence
                for ev in req.evidence:
                    if not any(
                        e.source_document == ev.source_document
                        and e.page_number == ev.page_number
                        and e.snippet == ev.snippet
                        for e in duplicate.evidence
                    ):
                        duplicate.evidence.append(ev)
            else:
                merged.append(req)

        return merged

    def extract_instructions(
        self,
        instruction_source: Union[PreprocessedDocument, str],
        use_vision: bool = False,
    ) -> List[InstructionRequirement]:
        """Extract structured application requirements from preprocessed document or text."""
        # 1. Vision/Model boundary path if requested and configured
        if use_vision or (
            isinstance(instruction_source, PreprocessedDocument)
            and instruction_source.requires_vision_processing
            and self.vision_extractor is not None
        ):
            return self._extract_via_vision(instruction_source)

        # 2. Textual / Selectable PDF extraction path
        all_reqs: List[InstructionRequirement] = []

        if isinstance(instruction_source, str):
            all_reqs = self.extract_from_text(instruction_source)
        elif isinstance(instruction_source, PreprocessedDocument):
            source_name = instruction_source.file_name or "instructions.pdf"

            if instruction_source.pages:
                for page in instruction_source.pages:
                    if page.text:
                        page_reqs = self.extract_from_text(
                            text=page.text,
                            page_number=page.page_number,
                            source_document=source_name,
                        )
                        all_reqs.extend(page_reqs)
            elif instruction_source.page_texts:
                for idx, text in enumerate(instruction_source.page_texts, start=1):
                    if text:
                        page_reqs = self.extract_from_text(
                            text=text,
                            page_number=idx,
                            source_document=source_name,
                        )
                        all_reqs.extend(page_reqs)
            elif instruction_source.full_text:
                all_reqs = self.extract_from_text(
                    text=instruction_source.full_text,
                    page_number=1,
                    source_document=source_name,
                )

        return self._merge_duplicate_requirements(all_reqs)

    def _extract_via_vision(
        self,
        instruction_source: Union[PreprocessedDocument, str],
    ) -> List[InstructionRequirement]:
        """Extract requirements via VisionExtractor model boundary."""
        if self.vision_extractor is None:
            raise ExtractionError("VisionExtractor is required for vision-based instruction extraction.")

        text_content = (
            instruction_source.full_text
            if isinstance(instruction_source, PreprocessedDocument)
            else str(instruction_source)
        )
        images = (
            instruction_source.images
            if isinstance(instruction_source, PreprocessedDocument)
            else None
        )

        prompt = (
            "Extract structured scholarship instruction requirements. "
            "Return JSON with a 'requirements' list of objects."
        )

        try:
            response = self.vision_extractor.extract(
                prompt=prompt,
                text_content=text_content,
                images=images,
                document_type=DocumentType.INSTRUCTIONS,
            )
        except Exception as exc:
            raise ExtractionError(f"Model boundary execution failed: {exc}") from exc

        if not isinstance(response, dict) or "requirements" not in response:
            raise ExtractionError("Malformed model response: missing 'requirements' list.")

        raw_reqs = response["requirements"]
        if not isinstance(raw_reqs, list):
            raise ExtractionError("Malformed model response: 'requirements' must be a list.")

        parsed_requirements: List[InstructionRequirement] = []
        for item in raw_reqs:
            if not isinstance(item, dict):
                raise ExtractionError(f"Malformed requirement item: {type(item).__name__}")
            try:
                # Map document type if provided as string
                doc_type = None
                if item.get("document_type_requested"):
                    try:
                        doc_type = DocumentType(item["document_type_requested"])
                    except ValueError:
                        doc_type = DocumentType.UNKNOWN

                req = InstructionRequirement(
                    requirement_id=item.get("requirement_id") or generate_requirement_id(
                        item.get("requirement_type", "general"), doc_type, item.get("snippet", "")
                    ),
                    requirement_type=item.get("requirement_type", "required_document"),
                    document_type_requested=doc_type,
                    is_required=item.get("is_required", True),
                    accepted_formats=item.get("accepted_formats", []),
                    max_file_size_bytes=item.get("max_file_size_bytes"),
                    constraints=item.get("constraints", {}),
                    evidence=[
                        Evidence(
                            source_document=item.get("source_document", "instructions.pdf"),
                            page_number=item.get("page_number", 1),
                            snippet=item.get("snippet", ""),
                        )
                    ] if item.get("snippet") else [],
                )
                parsed_requirements.append(req)
            except Exception as exc:
                raise ExtractionError(f"Failed to parse requirement item: {exc}") from exc

        return self._merge_duplicate_requirements(parsed_requirements)
