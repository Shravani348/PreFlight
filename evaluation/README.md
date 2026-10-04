# PreFlight AI Evaluation & Benchmarking Framework

## 1. Overview & Evaluation Architecture

The `evaluation/` module provides an empirical, reproducible benchmarking framework for evaluating the PreFlight AI/ML pipeline. Instead of relying solely on functional unit tests, this module measures the behavior and decision characteristics of core document intelligence components:

1. **Document Classification**: Evaluates multi-class classification accuracy, macro precision/recall/F1, and ambiguity handling.
2. **Cross-Document Matching**: Measures precision, recall, F1, false-match count, and false-mismatch count across person names, dates of birth, and addresses.
3. **Instruction Extraction**: Evaluates requirement extraction (formats, sizes, percentages, mandatory certificates) from scholarship instruction documents.
4. **Field Extraction & Normalization**: Measures exact match rate, normalized match rate, and missing field handling across structured document schemas.

```text
evaluation/
├── README.md                  # Comprehensive framework documentation & dataset roadmap
├── __init__.py                # Package exports
├── schemas.py                 # Pydantic contracts for test cases, ground truth, and metrics
├── metrics.py                 # Mathematical metric computation functions
├── benchmark.py               # Executable benchmark runner & terminal reporter
├── fixtures/                  # Synthetic evaluation fixtures
│   ├── README.md              # Privacy & dataset categorization notice
│   ├── dataset.py             # Python typed dataset test cases
│   ├── classification/        # 12 synthetic classification JSON cases
│   ├── matching/              # 12 synthetic cross-document matching JSON cases
│   ├── instructions/          # 6 synthetic instruction requirement JSON cases
│   └── extraction/            # 4 synthetic field extraction JSON cases
└── ground_truth/
    └── README.md              # Ground truth schema specifications and guidelines
```

---

## 2. Dataset Classification & Critical Distinction

> ### ⚠️ CRITICAL NOTICE: DEVELOPMENT / SYNTHETIC EVALUATION DATA
>
> All fixtures in this directory are strictly **DEVELOPMENT / SYNTHETIC EVALUATION DATA**.
>
> * **NOT a Real-World Dataset**: Under no circumstances should this benchmark suite be cited as a "real-world evaluation dataset".
> * **NO Production Accuracy Claims**: Metrics generated from this initial suite validate system architecture, deterministic component behavior, and metric computation pipelines. They do **not** reflect real-world production accuracy on live student applications.

---

## 3. Privacy, Anonymization & Data Protection

To comply with Indian data protection laws, privacy mandates, and academic ethics:

* **Zero Personal Identifiable Information (PII)**: This repository contains no genuine student records, live Aadhaar numbers, PAN numbers, contact numbers, or real residential addresses.
* **No Real Document Images**: No scans or photographs of genuine government certificates are committed. Image fixtures are generated synthetically in memory with mock dimensions and aspect ratios.
* **No Secrets or Credentials**: All benchmarks execute in a strictly offline, self-contained environment without external API keys, tokens, or cloud services.

---

## 4. Evaluation Schemas & Metric Formulas

### Classification Metrics
* **Accuracy**: $\frac{\text{Correct Classifications}}{\text{Total Cases}}$
* **Macro Precision**: Arithmetic mean of precision scores across all unique document classes ($\frac{1}{N}\sum P_c$).
* **Macro Recall**: Arithmetic mean of recall scores across all unique document classes ($\frac{1}{N}\sum R_c$).
* **Macro F1**: $\frac{2 \times P_{\text{macro}} \times R_{\text{macro}}}{P_{\text{macro}} + R_{\text{macro}}}$

### Matching Metrics
* **Accuracy**: $\frac{\text{Correct Matching Decisions}}{\text{Total Matching Pairs}}$
* **False Matches (False Positives)**: High-risk scenario where the system predicts `MATCH` or `LIKELY_MATCH` when the ground truth is `MISMATCH`.
* **False Mismatches (False Negatives)**: Scenario where the system flags `MISMATCH` when the ground truth is `MATCH` or `LIKELY_MATCH`.

### Instruction Metrics
* **Set Precision**: $\frac{|Predicted \cap Expected|}{|Predicted|}$
* **Set Recall**: $\frac{|Predicted \cap Expected|}{|Expected|}$
* **Set F1**: Harmonic mean of precision and recall.

### Field Extraction Metrics
* **Exact Match Rate**: Percentage of fields whose raw extracted value exactly matches ground truth.
* **Normalized Match Rate**: Percentage of fields whose normalized value matches ground truth after canonicalization.
* **Missing Field Rate**: Proportion of mandatory fields present in ground truth that were not extracted.

---

## 5. Running the Benchmark

The benchmark runner is fully deterministic and requires no internet access or external APIs.

Run via the Python module runner:

```powershell
python -m evaluation.benchmark
```

Expected terminal output format:

```text
========================================
PreFlight AI Evaluation
========================================

Dataset:
DEVELOPMENT / SYNTHETIC EVALUATION DATA

Classification
---------------
Cases:     12
Accuracy:  0.8333
Precision: 0.9062
Recall:    0.9062
F1:        0.8854

Matching
--------
Cases:            12
Accuracy:         0.7500
Precision:        0.6167
Recall:           0.7200
F1:               0.6214
False matches:    0
False mismatches: 1

Instructions
------------
Cases:     6
Precision: 1.0000
Recall:    1.0000
F1:        1.0000

Field Extraction
----------------
Fields:                13
Exact match rate:      0.8462
Normalized match rate: 1.0000
Missing fields:        0

========================================
IMPORTANT:
These metrics evaluate framework integrity and baseline deterministic logic.
They are NOT production accuracy metrics on live messy government documents.
========================================
```

---

## 6. Dataset Limitations

The synthetic development dataset has clear, deliberate boundaries. It **CANNOT** establish:

1. **Production Accuracy**: Synthetic documents lack the visual clutter, background watermarks, official stamps, and signature blocks found on government records.
2. **Multilingual Performance**: Does not test Marathi (Modi/Devanagari script), Hindi, or mixed-script government forms.
3. **Real OCR Degradation**: Does not capture OCR errors like character confusion (e.g., `0` vs `O`, `1` vs `I`, `8` vs `B`), broken words, or faded dot-matrix printouts.
4. **Physical Camera Artifacts**: Does not evaluate skewed angles, camera blur, perspective distortion, low lighting, glare, or thumb occlusions from mobile phone uploads.
5. **Vision LLM Hallucinations**: Uses deterministic mocks to evaluate pipeline contracts; does not measure real multimodal LLM hallucination frequencies.
6. **Population-Level Robustness**: 34 total test cases across all categories cannot prove statistical significance across diverse state demographic data.
7. **Calibrated Confidence**: Confidence scores on synthetic data do not represent empirical probabilities of correctness in deployment.

---

## 7. Future Real-World Dataset Plan

To establish an academically rigorous, publication-grade, or production-ready evaluation suite, a future benchmark dataset should be constructed according to the following multidimensional taxonomy:

### A. Document Quality & Capture Modality
* **Clean Digital PDFs**: Machine-generated electronic PDFs directly downloaded from portal services (e.g., MahaDBT, DigiLocker).
* **High-Resolution Scans**: 300 DPI flatbed scanner PDFs with straight alignment and clean contrast.
* **Mobile Camera Photos**: Natural smartphone captures under varying ambient lighting (daylight, incandescent, fluorescent).
* **Motion & Focus Blurs**: Handheld smartphone captures with slight blur or lens defocus.
* **Perspective & Rotation**: Images captured at 15°–45° tilt, upside-down, or 90° sideways rotation.
* **Lighting & Shadow Obstructions**: Documents with partial shadow cast by the phone or user's hands.
* **Compression & Downsampling**: JPEG images compressed to low file sizes (< 100 KB) mimicking aggressive portal compression.

### B. Linguistic Diversity
* **English Only**: Standard English application forms and university transcripts.
* **Marathi Only (Devanagari)**: Tehsildar income certificates, gram panchayat residency certificates, and caste certificates issued in Marathi.
* **Hindi Only**: Central government certificates and scholarship guidelines.
* **Bilingual / Code-Mixed**: Maharashtra State Board marksheets and Aadhaar cards containing paired English and Marathi labels/names side by side.

### C. Document Types & Formats
* **Application Forms**: Diverse formats across academic institutions, state scholarship schemes, and national portals.
* **Identity Documents**: Aadhaar cards (both full letter and cut card formats), Voter IDs, and School IDs.
* **Academic Marksheets**: SSC (10th), HSC (12th), university semester grade cards, and CGPA conversion certificates.
* **Income Certificates**: Tahsildar-issued annual income certificates with barcode/QR verification strips.
* **Caste / Category Certificates**: Sub-Divisional Magistrate caste certificates and Caste Validity certificates.
* **Passport Photographs**: Compliant studio photos, non-compliant selfies, group photos requiring crop, and low-contrast snapshots.
* **Official Instruction Broader Guidelines**: Complete multipage government scholarship scheme policy circulars (Government Resolutions / GRs).

### D. Information Extraction Challenges
* **Name Permutations**: Initials (e.g., *P. S. Ahire* vs *Priti Shashikant Ahire*), married surnames, expanded patronymics.
* **Spelling & Transliteration Variants**: Phonetic divergences (*Preeti* vs *Priti*, *Patil* vs *Patle*, *Chavan* vs *Chavhan*).
* **Missing & Discrepant Dates of Birth**: Partial birth dates (year-only on older Aadhaar cards), conflicting Gregorian vs Saka calendars.
* **Date Formatting Diversity**: `DD/MM/YYYY`, `YYYY-MM-DD`, `DD-Mon-YYYY`, `DD.MM.YY`.
* **Multipage & Tabular Complexity**: Marksheets with multi-semester subject breakdown tables and practical vs theory columns.
* **Noisy OCR Outputs**: Smudged ink, low dot-matrix printer resolution, stamps overlaid directly on text.

### E. Cross-Document Matching Edge Cases
* **Exact Identity Matches**: Benchmark controls where all records match identically.
* **Token Inversion / Reordering**: Surname-first (*Ahire Priti Shashikant*) vs Given-name-first (*Priti Shashikant Ahire*).
* **Abbreviated Middle Names**: Single-letter initials vs full spelled names.
* **Minor OCR Typo Tolerances**: 1-character Levenshtein edits on long strings.
* **Hard Negative Controls**: Family members sharing same surname and address (e.g., father *Shashikant Ahire* vs student *Priti Ahire*) that must NOT be falsely matched as the applicant.
* **Transliteration Cross-Language Alignment**: Name in Devanagari (*प्रीती शशिकांत अहिरे*) compared against Latin transcript (*Priti Shashikant Ahire*).

---

## 8. Data Collection & Ethics Guidelines

When assembling the future real-world evaluation dataset:
1. **Informed Consent**: Explicit written consent must be gathered from all participating students and parents.
2. **De-Identification**: Mask all 12-digit Aadhaar numbers (showing only last 4 digits `XXXX-XXXX-1234`), bank account numbers, IFSC codes, and mobile numbers before storage.
3. **Isolated Evaluation Storage**: Real test sets must be stored on encrypted, access-controlled institutional storage, separated from public Git repositories.
4. **Benchmarking Split**: Maintain a strict 70/30 or 50/50 public vs hidden test split to prevent benchmark leakage or overfitting.
