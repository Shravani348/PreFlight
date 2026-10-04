# PreFlight Backend API Contract

This document outlines the JSON contracts for the PreFlight backend endpoints. This is intended for Member 3 (Frontend Integration).

## 1. `POST /analyze`

Analyzes an application consisting of multiple documents, checking them against required rules, calculating risk, and generating a fix plan.

### Request Body
```json
{
  "application_type": "string",
  "documents": [
    {
      "document_type": "string",
      "format": "string",
      "size_kb": 0,
      "document_name": "string",
      "page": 1,
      "confidence": 1.0,
      "extracted_data": {
        "key": "value"
      }
    }
  ]
}
```

### Response Body
```json
{
  "status": "READY | FIX_REQUIRED",
  "readiness_score": 0,
  "risk": "LOW | MEDIUM | HIGH",
  "message": "string",
  "summary": {
    "passed": 0,
    "warnings": 0,
    "critical": 0
  },
  "issues": [
    {
      "type": "string",
      "severity": "WARNING | CRITICAL",
      "message": "string",
      "evidence": [
        "string"
      ],
      "document_type": "string"
    }
  ],
  "fix_plan": [
    {
      "step": 1,
      "issue_type": "string",
      "priority": "LOW | MEDIUM | HIGH | VERY_HIGH",
      "title": "string",
      "action": "string",
      "why": "string",
      "evidence": [
        "string"
      ]
    }
  ],
  "report_id": "string-uuid"
}
```

## 2. `POST /recheck`

Rechecks the application after the user has made fixes. 

### Request Body
Exactly the same as `POST /analyze`. Send the full updated document state.

### Response Body
Exactly the same as `POST /analyze`. 

## 3. `GET /report/{report_id}`

Downloads the generated PDF report.

### Request Params
- `report_id` (Path): The UUID string returned in the `report_id` field from `/analyze` or `/recheck`.

### Response
- Content-Type: `application/pdf`
- Body: Raw PDF binary data.

## 4. `GET /health`

Basic liveness check.

### Response Body
```json
{
  "status": "ok",
  "service": "PreFlight Backend"
}
```
