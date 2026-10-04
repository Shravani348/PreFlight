# PreFlight

A pre-flight check for your application, before a mistake costs you the seat.

PreFlight helps detect avoidable application errors before submission, such as:

- Name/DOB mismatches
- Missing documents
- Expired certificates
- Incorrect document formats
- Photo/document size issues
- Inconsistencies across submitted documents

## Supported Demo

Scholarship Application (as well as College, Exam, Job, Visa, and KYC applications)

## Architecture

- `ai/` - AI/ML document intelligence, classification, extraction, normalization, and cross-document verification
- `backend/` - FastAPI backend, Rule Engine, Risk Engine, Recommendation Engine, Fix Plan, and PDF report service
- `frontend/` - Modern React + Vite responsive interface with dark/light themes, live upload, checks, and reports
- `tests/` - Comprehensive test suites across AI, evaluation, and backend

## Quick Start

### 1. Backend
```bash
# Install backend dependencies
pip install -r backend/requirements.txt

# Start FastAPI server (runs on http://127.0.0.1:8000)
uvicorn backend.main:app --reload --port 8000
```

### 2. Frontend
```bash
# Install dependencies
cd frontend
npm install

# Start Vite dev server (runs on http://localhost:5173 with proxy to backend)
npm run dev
```

### 3. Running Tests
```bash
# Run all tests
pytest tests/ai -q
pytest tests/evaluation -q
pytest backend/tests -q
```
