# Ground Truth Formats and Specifications

This directory specifies the ground-truth formats and annotations against which PreFlight AI components are evaluated.

## Evaluation Case Schema Reference

### 1. Classification Ground Truth
```json
{
  "case_id": "class_01",
  "file_name": "app.pdf",
  "text_content": "MAHARASHTRA STATE SCHOLARSHIP APPLICATION FORM...",
  "expected_document_type": "application_form",
  "expected_needs_verification": false
}
```

### 2. Matching Ground Truth
```json
{
  "case_id": "match_01",
  "field_name": "name",
  "value_a": "Priti Shashikant Ahire",
  "value_b": "Priti Shashikant Ahire",
  "expected_status": "match",
  "expected_needs_verification": false
}
```

### 3. Instructions Ground Truth
```json
{
  "case_id": "inst_01",
  "instruction_text": "Aadhaar card must be uploaded by the applicant.",
  "expected_requirement_types": ["required_document"],
  "expected_document_types": ["aadhaar_or_identity"]
}
```

### 4. Field Extraction Ground Truth
```json
{
  "case_id": "ext_01",
  "document_type": "marksheet",
  "document_text": "STATEMENT OF MARKS...",
  "expected_fields": {
    "name": "Priti Ahire",
    "marks": "450/500",
    "percentage": "90.0%"
  }
}
```
