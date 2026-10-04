# PreFlight AI Module — Backend Integration Guide

This guide describes how backend services (FastAPI / Celery / background workers) consume Member 1's AI document intelligence module.

---

## 1. Quick Start

```python
from pathlib import Path
from ai.pipeline import AIPipeline

# Initialize the pipeline (offline, deterministic by default)
pipeline = AIPipeline()

# Process an applicant's uploaded documents
result = pipeline.process(
    document_paths=[
        "uploads/application_form.pdf",
        "uploads/aadhaar_card.pdf",
        "uploads/marksheet.pdf",
        "uploads/income_certificate.pdf",
    ],
    allow_partial_failure=True,
)

# Serialize to a clean JSON-ready dictionary
payload = result.model_dump()
```

---

## 2. Pipeline Interface

### Entry Point

```python
from ai.pipeline import AIPipeline
```

### Method Signature

```python
def process(
    self,
    document_inputs: Optional[Union[List[Union[str, Path]], str, Path]] = None,
    document_paths: Optional[List[Union[str, Path]]] = None,
    allow_partial_failure: bool = False,
) -> AIProcessingResult:
```

### Input Parameters

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `document_paths` | `List[Union[str, Path]]` | `None` | List of local filesystem paths to uploaded documents. |
| `document_inputs` | `Union[List, str, Path]` | `None` | Flexible alias for document paths or preprocessed objects. |
| `allow_partial_failure` | `bool` | `False` | When `False`, corrupted/invalid files raise `DocumentProcessingError`. When `True`, failed files are preserved as `DocumentType.UNKNOWN` with `needs_verification=True`. |

---

## 3. Output Schema (`AIProcessingResult`)

The pipeline returns a unified `AIProcessingResult` containing four top-level keys:

```json
{
  "documents": [ ... ],
  "cross_document_findings": [ ... ],
  "instruction_requirements": [ ... ],
  "verification": { ... }
}
```

### A. `documents` (`List[ExtractedDocument]`)

Extracted and normalized data for each processed file:
* `document_id`: Source filename identifier.
* `document_type`: Classified category (`application_form`, `aadhaar_or_identity`, `marksheet`, `income_certificate`, `caste_certificate`, `photograph`, `instructions`, `unknown`).
* Core fields (`name`, `date_of_birth`, `father_name`, `mother_name`, `address`, `certificate_number`, etc.):
  * `original`: Raw extracted text as printed.
  * `normalized`: Canonical representation (e.g. ISO `YYYY-MM-DD` for dates, NFC lowercase for names).
  * `confidence`: Extraction confidence score `[0.0, 1.0]`.
  * `evidence`: List of source snippets and page numbers.

### B. `cross_document_findings` (`List[ComparisonFinding]`)

Pairwise field consistency across documents (Name, Date of Birth, Address):
* `field_name`: Field compared (`name`, `date_of_birth`, `address`).
* `status`: AI matching finding:
  * `MATCH`: Identical or exact phonetic match (similarity `1.0`).
  * `LIKELY_MATCH`: High similarity (`>= 0.90`), human review recommended.
  * `VERIFICATION_REQUIRED`: Significant ambiguity, abbreviated initials, regional spelling variation, or family-member patronymic subset.
  * `MISMATCH`: Conflicting values (`< 0.75`).
  * `MISSING`: Value absent in one or both documents.
* `similarity_score`: Normalized similarity float `[0.0, 1.0]`.
* `needs_verification`: Boolean flag indicating whether human inspection is required.
* `explanation`: Plain-language explanation for administrative officers.
* `source_value` / `comparison_value`: Original unmutated strings.
* `normalized_source_value` / `normalized_comparison_value`: Normalized strings (Devanagari Unicode preserved).

### C. `instruction_requirements` (`List[InstructionRequirement]`)

Extracted requirements from official scholarship scheme circulars:
* `requirement_type`: `mandatory_document`, `photograph_specification`, `file_format`, `file_size_limit`, `eligibility_criteria`.
* `description`: Extracted requirement description.
* `is_mandatory`: `True` / `False`.
* `max_file_size_bytes`: Integer byte constraint when applicable.
* `allowed_formats`: List of allowed extensions (e.g. `["pdf", "jpeg"]`).
* `minimum_percentage`: Minimum academic percentage constraint (e.g. `60.0`).

### D. `verification` (`VerificationResult`)

Aggregated decision support metrics:
* `verification_required`: `True` if any document, field, or match requires officer review.
* `high_confidence_count`: Number of high-confidence items.
* `medium_confidence_count`: Number of medium-confidence items.
* `low_confidence_count`: Number of low-confidence items.
* `missing_count`: Number of missing required items.
* `items`: List of individual flagged items with reasons and evidence.

---

## 4. Critical Architectural Boundary

> **IMPORTANT FOR BACKEND & SCHOLARSHIP WORKFLOWS:**
>
> 1. **No Automated Final Decisions:** The AI module produces **findings**, **signals**, and **verification flags** to assist human scholarship officers. It does **NOT** make final application decisions.
> 2. **Never Treat Flags as Approval/Rejection:** Do NOT map `MATCH` to `APPROVE` or `MISMATCH` to `REJECT`.
> 3. **Eligibility Constraints:** The AI extracts academic criteria (e.g. *minimum 60%*), but does **NOT** evaluate whether an applicant is eligible. That determination belongs to the business rules engine.

---

## 5. Environment Variables & Configuration

The AI module runs fully offline by default without requiring external cloud credentials:

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `AI_API_KEY` | `""` | Optional API key for future vision/LLM provider adapter. |
| `AI_MODEL_NAME` | `"gemini-1.5-flash"` | Optional model name identifier for vision extraction adapter. |
| `AI_TIMEOUT_SECONDS` | `30` | Optional timeout for model calls. |

---

## 6. Multilingual & Script Support

* **Supported Languages:** English, Hindi (हिन्दी), Marathi (मराठी), and mixed bilingual documents.
* **Cross-Script Name Matching:** Transparently matches Latin and Devanagari names (e.g. `Priti Ahire` ↔ `प्रीती अहिरे`, `Amit Patil` ↔ `अमित पाटील`) using deterministic phonetic transliteration.
* **Family-Member Safety:** Shorter patronymic subsets (e.g. `Shashikant Ahire` vs `Priti Shashikant Ahire` or `प्रीती शशिकांत अहिरे`) are strictly flagged as `VERIFICATION_REQUIRED` to prevent father/student identity confusion.
