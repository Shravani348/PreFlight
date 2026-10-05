# ✈️ PreFlight

### A pre-flight check for your application, before a mistake costs you the seat.

PreFlight is an AI-assisted document verification platform that helps applicants identify avoidable mistakes **before submitting important applications**.

It checks application forms, supporting documents, and official requirements to detect inconsistencies, missing documents, and file-related issues.

---

## 🏆 Hackathon

**Track 03 — Everyday Automation**

PreFlight automates a repetitive and error-prone task: manually checking multiple application documents before submission.

### 🎯 Problem

Students and applicants can face rejection because of small mistakes such as:

* Name or DOB mismatches
* Missing required documents
* Expired certificates
* Incorrect file formats
* File-size violations
* Inconsistent information across documents

These issues are often discovered only after submission or after a deadline.

---

## 💡 Solution

PreFlight creates a **pre-submission verification layer**.

Users upload:

* Application form
* Supporting documents
* Official instructions

The system extracts important information, compares documents, validates requirements, and generates a clear report:

> 🟢 **Ready to Submit**

or

> 🔴 **Fix These First**

The goal is simple:

> **Don't discover an application mistake after submission.**

---

## 🚀 Live Demo

### 🌐 Frontend

**[Launch PreFlight]([https://preflight.vercel.app/](https://pre-flight-pearl.vercel.app/))**

### ⚙️ Backend API

**[FastAPI Swagger Documentation](https://preflight-backend-63wo.onrender.com/docs)**

> If your actual Vercel URL is different, replace the frontend link with your deployed URL.

---

## 🏗️ System Architecture

![PreFlight System Architecture](system-architecture.png)

The architecture separates the frontend, FastAPI backend, AI document intelligence, validation services, and reporting layer.

---

## 🔄 How PreFlight Works

![PreFlight Workflow](workflow.png)

PreFlight takes the uploaded application package through extraction, normalization, cross-document verification, rule validation, and final readiness reporting.

---

## ⭐ Key Features

### 📄 Multi-Document Verification

Analyze an application together with its supporting documents.

### 🔍 Cross-Document Checking

Detect inconsistencies in names, dates, certificates, and other important fields.

### 🧠 AI-Assisted Extraction

Extract important information from uploaded documents into structured data.

### ⚡ Fuzzy Matching

Identify variations in names instead of relying only on exact matches.

### 📋 Requirement Checking

Detect missing documents and unmet application requirements.

### 📁 File Validation

Check file formats, sizes, and document constraints.

### 💡 Fix Recommendations

Explain detected problems and what the applicant should review or correct.

### 📊 Readiness Report

Provide a simple **Ready to Submit / Fix These First** result.

---

## 🎬 Demo Scenario

Our primary demo focuses on a **Scholarship Application**.

For example:

```text
Aadhaar:
Rahul Kumar Sharma

Marksheet:
Rahul K. Sharma

⚠ Name mismatch detected
```

Or:

```text
Required Documents:

✓ Identity Proof
✓ Marksheet
✗ Income Certificate

⚠ Required document missing
```

PreFlight identifies these problems **before the applicant submits the application**.

---

## 👥 Target Users

**Primary:** Students, parents, scholarship applicants, college admission and examination applicants.

**Extended:** Job applicants, visa applicants, bank KYC users, and small businesses handling document-heavy applications.

---

## 🛠️ Tech Stack

| Layer               | Technologies                                      |
| ------------------- | ------------------------------------------------- |
| Frontend            | React.js, Vite, JavaScript, HTML, CSS             |
| Backend             | Python, FastAPI, Uvicorn                          |
| Document Processing | PyPDF, Pillow, python-multipart                   |
| Validation          | Pydantic, RapidFuzz, Rule Engine                  |
| AI                  | AI-assisted document extraction & structured JSON |
| API                 | REST, OpenAPI / Swagger                           |
| Deployment          | Vercel + Render                                   |

---

## 🔐 Privacy

PreFlight is designed to minimize unnecessary exposure of sensitive application information. The prototype focuses on processing documents for verification rather than building a permanent document-storage workflow.

---

## 💻 Run Locally

### Backend

```bash
pip install -r backend/requirements.txt
pip install -r requirements-ai.txt
uvicorn backend.main:app --reload --port 8000
```

Backend API:

```text
http://127.0.0.1:8000/docs
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:5173
```

---

## 🧪 Testing

```bash
pytest tests/ai -q
pytest tests/evaluation -q
pytest backend/tests -q
```

---

## 🌍 Vision

Important applications deserve a **pre-flight checklist** before submission.

### Check → Fix → Verify → Submit

**PreFlight — Check before you submit.**

---
