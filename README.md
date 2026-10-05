# ✈️ PreFlight

### A pre-flight check for your application, before a mistake costs you the seat.

**PreFlight** is an AI-assisted document verification platform designed to help applicants detect avoidable mistakes **before submitting important applications**.

Applications for scholarships, college admissions, examinations, jobs, visas, and KYC often require multiple documents with strict requirements. A small inconsistency — such as a different name spelling, incorrect date of birth, missing certificate, expired document, or invalid file size — can result in rejection.

PreFlight acts as a **pre-submission verification layer** that checks the complete application package and tells users what needs to be fixed before they submit.

---

## 🏆 Hackathon Project

**Track:** Track 03 — Everyday Automation

PreFlight directly addresses the Everyday Automation theme by automating a repetitive and error-prone task: **checking application forms and supporting documents against each other and against official requirements.**

Instead of manually opening every document and comparing information, users can upload their application package and receive a structured readiness report.

---

# 🎯 Problem

People submitting scholarship, examination, college admission, job, visa, and KYC applications frequently have to provide multiple documents.

Common avoidable mistakes include:

* Name spelling differences between documents
* Date of birth inconsistencies
* Missing mandatory certificates
* Expired certificates
* Incorrect document formats
* File-size violations
* Invalid or incomplete supporting documents
* Information that conflicts across submitted documents

These problems are particularly costly because applicants may discover them **only after submission**, when correction may no longer be possible.

A single small mistake can result in:

* Application rejection
* Missed deadlines
* Repeated documentation
* Additional travel or administrative effort
* Loss of an academic, employment, financial, or other opportunity

---

# 💡 Our Solution

PreFlight allows users to upload:

1. Their completed application form
2. Supporting documents
3. Official application instructions

The system then processes the complete document set and performs multiple layers of verification.

### PreFlight checks:

**Document → Document**

Does the information match across documents?

**Document → Requirement**

Does the submitted document satisfy the official requirements?

**File → Constraint**

Does the file satisfy format and size restrictions?

**Application → Readiness**

Is the application ready to submit?

The result is presented as a clear action-oriented report:

> 🟢 **Ready to Submit**

or

> 🔴 **Fix These First**

---

# ⭐ What Makes PreFlight Different?

Most document-processing systems focus primarily on **extracting information from individual documents**.

PreFlight goes one step further.

### It connects three types of verification:

```text
                 ┌──────────────────────┐
                 │  Application Form    │
                 └──────────┬───────────┘
                            │
                            ▼
┌─────────────────┐   ┌───────────────┐   ┌─────────────────────┐
│ Supporting Docs │──▶│   PreFlight   │◀──│ Official Instructions│
└─────────────────┘   └───────┬───────┘   └─────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ Verification     │
                    │ & Rule Engine    │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Readiness Report │
                    └──────────────────┘
```

The goal is not simply:

> "What information is inside this document?"

The goal is:

> **"Is this complete application package safe to submit?"**

---

# 🚀 Key Features

## 1. Multi-Document Upload

Users can submit the complete application package instead of checking documents individually.

Supported demo scenario:

**Scholarship Application**

The architecture can also support:

* College admissions
* Examination applications
* Job applications
* Visa applications
* Bank KYC
* Other document-heavy workflows

---

## 2. AI-Assisted Document Extraction

Important information is extracted from uploaded documents and converted into structured data.

Examples include:

* Full name
* Date of birth
* Document type
* Certificate details
* Identification information
* Other application-specific fields

Structured output makes the extracted information suitable for automated verification.

---

## 3. Cross-Document Consistency Checking

PreFlight compares the same fields across different documents.

For example:

```text
Aadhaar:
Rahul Kumar Sharma

Marksheet:
Rahul K. Sharma
```

The system can flag the inconsistency instead of assuming that both values are identical.

---

## 4. Fuzzy Name Matching

Names are not always written in exactly the same format.

PreFlight uses fuzzy matching to identify potential variations rather than relying only on exact string comparison.

Example:

```text
Rahul Kumar Sharma
Rahul K Sharma
R. K. Sharma
```

The system can identify these as potentially related values and determine whether further verification is required.

---

## 5. Date and Field Validation

Important fields such as date of birth are compared across documents.

Example:

```text
Aadhaar       → 12/05/2005
Marksheet     → 12/05/2005
Certificate   → 12/05/2004
```

Result:

```text
⚠ DOB mismatch detected

Certificate shows a different year.
Review before submission.
```

---

## 6. Missing Document Detection

PreFlight checks the application requirements and identifies required documents that have not been uploaded.

Example:

```text
Required:
✓ Identity Proof
✓ Marksheet
✓ Caste Certificate
✗ Income Certificate
```

The system clearly identifies the missing requirement.

---

## 7. File Validation

PreFlight checks document-level constraints such as:

* File format
* File size
* Supported document types
* Photo/document restrictions

Example:

```text
Photo size: 3 MB
Allowed size: 200 KB

❌ File size exceeds the permitted limit.
```

---

## 8. Certificate and Requirement Checks

The verification workflow can identify issues such as:

* Expired certificates
* Missing certificates
* Invalid document types
* Requirement mismatches

---

## 9. Risk-Based Verification

The backend architecture includes validation and risk-oriented processing to help distinguish between:

* Valid information
* Potential inconsistencies
* Critical issues requiring correction

This allows the final report to focus the user's attention on the most important problems.

---

## 10. Fix Recommendations

PreFlight doesn't stop at detecting an error.

It explains:

**What is wrong → Where it is wrong → What should be checked or fixed**

Example:

```text
Issue:
Name mismatch detected.

Aadhaar:
Rahul Kumar Sharma

Marksheet:
Rahul K. Sharma

Recommended action:
Verify the official name and correct the
application/document where necessary.
```

---

## 11. Final Readiness Report

The final result is designed around a simple question:

### "Can I submit this application?"

The system produces a structured report containing:

* Passed checks
* Failed checks
* Warnings
* Missing documents
* Detected inconsistencies
* File issues
* Recommended fixes

---

# 🧠 AI + Rule-Based Architecture

PreFlight combines **AI-assisted document intelligence** with deterministic validation.

This is important because not every verification problem should be solved using AI alone.

### AI is used for:

* Document understanding
* Information extraction
* Structured field generation
* Document classification
* Normalization
* Cross-document intelligence

### Deterministic logic is used for:

* Required-document checks
* File-size validation
* File-format validation
* Date comparisons
* Rule validation
* Fuzzy name matching
* Readiness determination

This hybrid approach makes the system more predictable and easier to validate.

---

# 🔄 End-to-End Workflow

```text
             USER
               │
               ▼
      Upload Application
      + Supporting Docs
      + Instructions
               │
               ▼
       React / Vite Frontend
               │
               │ REST API
               ▼
          FastAPI Backend
               │
       ┌───────┴────────┐
       ▼                ▼
Document Processing   Requirement
       │              Processing
       ▼                │
AI-Assisted           Rule Engine
Extraction               │
       │                │
       └───────┬────────┘
               ▼
       Normalization
               │
               ▼
   Cross-Document Verification
               │
               ▼
        Risk / Validation
               │
               ▼
     Recommendation & Fix Plan
               │
               ▼
       Final Readiness Report
               │
               ▼
             USER
```

---

# 🏗️ System Architecture

```text
PreFlight
│
├── frontend/
│   ├── React
│   ├── Vite
│   ├── Upload Interface
│   ├── Verification Results
│   ├── Reports
│   └── Responsive UI
│
├── backend/
│   ├── FastAPI
│   ├── REST APIs
│   ├── Rule Engine
│   ├── Risk Engine
│   ├── Recommendation Engine
│   ├── Fix Plan
│   ├── PDF Report Service
│   ├── Models
│   └── Services
│
├── ai/
│   ├── Document Intelligence
│   ├── Classification
│   ├── Extraction
│   ├── Normalization
│   └── Cross-Document Verification
│
└── tests/
    ├── AI Tests
    ├── Evaluation Tests
    └── Backend Tests
```

---

# 🛠️ Technology Stack

### Frontend

* React.js
* Vite
* JavaScript
* HTML
* CSS

### Backend

* Python
* FastAPI
* Uvicorn
* REST APIs

### Document Processing

* PyPDF
* Pillow
* python-multipart

### Data Validation & Matching

* Pydantic
* RapidFuzz
* Rule-based validation

### AI / Document Intelligence

* AI-assisted document extraction
* Structured JSON processing
* Document classification
* Field normalization
* Cross-document verification

### API Testing

* FastAPI Swagger
* OpenAPI

### Deployment

* Vercel — Frontend
* Render — Backend

---

# 🔐 Privacy by Design

Application documents can contain sensitive personal information.

PreFlight is designed around minimizing unnecessary data exposure during the verification process.

For the hackathon prototype, the focus is on processing uploaded documents for verification rather than building a permanent document-storage system.

The interface can also mask sensitive identification information when displaying results.

> **Privacy principle: Verify what is necessary, expose only what is necessary.**

---

# 📊 Example

Imagine a student applying for a scholarship.

They upload:

```text
✓ Application Form
✓ Aadhaar
✓ Marksheet
✓ Caste Certificate
✓ Income Certificate
✓ Photograph
```

The system discovers:

```text
❌ Name mismatch

Aadhaar:
Rahul Kumar Sharma

Marksheet:
Rahul K. Sharma


❌ DOB mismatch

3 documents:
2005

Caste Certificate:
2004


❌ Missing requirement

Income Certificate:
Not detected


❌ File constraint

Photograph:
3 MB

Maximum allowed:
200 KB
```

Instead of discovering these problems after submission, the applicant receives the issues **before submitting the application**.

---

# 🎬 Demo Flow

Our recommended hackathon demonstration follows a simple story.

### Step 1 — Start with a seemingly correct application

Show the application package and say:

> "At first glance, everything looks fine."

### Step 2 — Upload the documents

Upload the application form and supporting documents.

### Step 3 — Run PreFlight

The system processes the documents and performs its checks.

### Step 4 — Show the unexpected mismatch

PreFlight identifies an inconsistency such as:

```text
⚠ Name mismatch detected
```

or:

```text
⚠ Required document missing
```

### Step 5 — Show the fix

The system explains what needs attention.

### Step 6 — Final readiness result

Show:

```text
🔴 Fix These First
```

After correction:

```text
🟢 Ready to Submit
```

This demonstrates the core value of PreFlight in a few minutes.

---

# 🎯 Target Users

### Primary Users

* Students
* Parents
* Scholarship applicants
* College admission applicants
* Examination applicants

### Additional Users

* Job applicants
* Visa applicants
* Bank KYC applicants
* Small businesses handling document-heavy applications

---

# 🌍 Potential Applications

Although the hackathon demo focuses on scholarship applications, the same verification architecture can be adapted to:

| Use Case           | Example Checks                                               |
| ------------------ | ------------------------------------------------------------ |
| Scholarships       | Eligibility documents, income certificate, caste certificate |
| College Admissions | Marksheets, identity documents, certificates                 |
| Exams              | Photo, signature, identity proof, file constraints           |
| Jobs               | Resume, certificates, identity documents                     |
| Visa               | Passport details, photographs, supporting documents          |
| Bank KYC           | Identity, address and supporting documents                   |
| Small Business     | KYC, tenders and compliance documents                        |

---

# 🧪 Testing

The repository contains separate test suites for different parts of the system.

Run AI tests:

```bash
pytest tests/ai -q
```

Run evaluation tests:

```bash
pytest tests/evaluation -q
```

Run backend tests:

```bash
pytest backend/tests -q
```

---

# 💻 Local Setup

## Prerequisites

Make sure you have:

* Python installed
* Node.js and npm installed
* Git installed

---

## 1. Clone the repository

```bash
git clone https://github.com/Shravani348/PreFlight.git
cd PreFlight
```

---

## 2. Backend Setup

Install dependencies:

```bash
pip install -r backend/requirements.txt
```

Install AI/document-processing dependencies:

```bash
pip install -r requirements-ai.txt
```

Start the FastAPI backend:

```bash
uvicorn backend.main:app --reload --port 8000
```

Backend:

```text
http://127.0.0.1:8000
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

---

## 3. Frontend Setup

Move into the frontend directory:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

Frontend:

```text
http://localhost:5173
```

---

# ☁️ Deployment

PreFlight is structured as a separate frontend and backend deployment.

```text
                    GitHub
                      │
             ┌────────┴────────┐
             │                 │
             ▼                 ▼
          Vercel             Render
          Frontend           Backend
          React/Vite         FastAPI
             │                 │
             └────────┬────────┘
                      │
                      ▼
                 Live System
```

### Frontend

Deployed using:

**Vercel**

### Backend

Deployed using:

**Render**

The frontend communicates with the deployed FastAPI backend through REST APIs.

---

# 📁 Project Structure

```text
PreFlight/
│
├── ai/
│   ├── classification/
│   ├── extraction/
│   ├── normalization/
│   └── verification/
│
├── backend/
│   ├── models/
│   ├── services/
│   ├── tests/
│   ├── main.py
│   ├── API_CONTRACT.md
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.*
│
├── tests/
│   ├── ai/
│   └── evaluation/
│
├── requirements-ai.txt
└── README.md
```

---

# 🔮 Future Improvements

Potential future extensions include:

* Support for more application types
* More advanced document authenticity checks
* Additional regional-language explanations
* Improved OCR and handwriting recognition
* More sophisticated requirement extraction from official guidelines
* Secure encrypted document processing
* Institution-specific verification rules
* Application-specific validation templates
* Expanded accessibility features

---

# 💭 Vision

PreFlight is built around a simple idea:

> **Don't wait for an application to be rejected to discover a mistake.**

Important applications should have a **pre-submission safety check**, just like a pre-flight checklist before a flight.

Our goal is to make document-heavy applications:

**less stressful → less error-prone → more predictable → more likely to be submitted correctly the first time.**

---

## 👥 Hackathon Project

Built as a hackathon prototype under:

### **Track 03 — Everyday Automation**

PreFlight demonstrates how AI-assisted document intelligence and automated validation can turn a repetitive manual checking process into a simple, actionable pre-submission workflow.

---
