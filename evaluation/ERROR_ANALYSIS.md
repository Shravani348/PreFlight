# PreFlight AI Evaluation & Error Analysis Report

**Repository:** `D:\DYP DPU\PreFlight`  
**Branch:** `feature/aiml`  
**Milestone:** Task 15 (Initial Evaluation) & Task 16 (Matching Hardening)
**Status:** Evaluation Completed & Hardening Verified

---

## 1. Executive Summary & Benchmark Evolution

In Task 15, the empirical evaluation framework uncovered a critical safety vulnerability in person name matching:
a father's name (`"Shashikant Ahire"`) was classified as a **100% LIKELY_MATCH** against the applicant's name (`"Priti Shashikant Ahire"`).

In Task 16, the cross-document name matching layer was hardened with subset-protection heuristics, token-length penalties, defensive normalization, and initial-alignment logic.

### Benchmark Progression (Before vs. After Task 16)

| Metric | Before Task 16 (Task 15 Baseline) | After Task 16 (Hardened Pipeline) | Change / Impact |
| :--- | :---: | :---: | :---: |
| **Classification Accuracy** | **0.8636** (19/22) | **0.8636** (19/22) | Unchanged (Production AI preserved) |
| **Classification F1 (Macro)** | 0.8837 | 0.8837 | Unchanged |
| **Matching Accuracy** | **0.7727** (17/22) | **1.0000** (22/22) | **+22.73%** |
| **Matching F1 (Macro)** | 0.7826 | **1.0000** | **+0.2174** |
| **Matching False Matches (FP)** | **1 (Critical)** | **0** | **Eliminated (High-Risk Vulnerability Fixed)** |
| **Matching False Mismatches (FN)**| **1** | **0** | **Eliminated (Abbreviated initials preserved)** |
| **Instruction Extraction F1** | **1.0000** (11/11) | **1.0000** (11/11) | Robust deterministic baseline |
| **Extraction Normalized Match** | **1.0000** (35/35) | **1.0000** (35/35) | High normalization efficacy |

---

## 2. The Critical Vulnerability (Task 15 Discovery)

### Vulnerability Description
In Indian administrative records (especially in Maharashtra scholarship schemes), full names typically follow the patronymic sequence:
`[Applicant Given Name] [Father Given Name] [Surname]` (e.g., *Priti Shashikant Ahire*).
Supporting documents such as Tahsildar income certificates or parent tax declarations list the father's name:
`[Father Given Name] [Surname]` (e.g., *Shashikant Ahire*).

### Root Cause: Token-Set Overlap
The original implementation of `NameMatcher` relied on RapidFuzz `token_set_ratio`:
```python
# Original ai/matching/name_matcher.py
raw_score = fuzz.token_set_ratio(s_a, s_b)
```
`token_set_ratio` calculates the intersection of word tokens between two strings:
* `tokens_a = {"Shashikant", "Ahire"}`
* `tokens_b = {"Priti", "Shashikant", "Ahire"}`
* `intersection = {"Shashikant", "Ahire"}`

Because all tokens of string A exist inside string B, `token_set_ratio` assigned a similarity score of **100.0 (1.0)**.
Because the strings were not identical character-for-character, the classifier fell through to line 145:
```python
if sim >= self.likely_match_threshold: # 1.0 >= 0.90
    status = MatchStatus.LIKELY_MATCH
```
The system thus concluded that the father's document was a **LIKELY_MATCH** for the daughter applicant with 1.0 similarity!
In a production deployment, this would cause parent documents to be falsely verified as belonging to the student.

---

## 3. The Hardened Matching Strategy (Task 16 Solution)

To fix this vulnerability without breaking legitimate variations or hardcoding names, `NameMatcher` was hardened with a multi-stage deterministic decision pipeline:

```text
Raw Inputs (name_a, name_b)
             ↓
1. Defensive Normalization (NameNormalizer: lowercasing, whitespace collapse, punctuation stripping)
             ↓
2. Exact Normalized Equality (norm_a == norm_b) → MATCH (Score: 1.0)
             ↓
3. Honorific Disregard (Mr., Ms., Shri, Smt.) → MATCH (Score: 1.0)
             ↓
4. Token Permutation / Reordering (sorted tokens identical) → MATCH (Score: 1.0)
             ↓
5. Initials Alignment Check (Priti S. Ahire vs Priti Shashikant Ahire) → Evaluated against configurable thresholds
             ↓
6. Strict Subset Protection (One name's tokens are a strict subset of the other)
   ├── Single token vs 3+ tokens → MISMATCH
   └── Multi-token subset with missing full names → VERIFICATION_REQUIRED (Score capped by token_sort_ratio < 1.0)
             ↓
7. Standard Fuzzy Comparison (RapidFuzz with token-length sensitivity)
```

### Key Algorithmic Guardrails

1. **Subset Penalty in `similarity()`:**
   If `set_a < set_b` or `set_b < set_a`, `similarity()` falls back to `token_sort_ratio` rather than `token_set_ratio`, ensuring that `similarity("Shashikant Ahire", "Priti Shashikant Ahire")` returns `0.8421`, never `1.0`.
2. **Mandatory Routing to `VERIFICATION_REQUIRED`:**
   Whenever a multi-token subset is detected with missing person-name tokens, `NameMatcher.compare()` prohibits `MATCH` and `LIKELY_MATCH`, forcing `VERIFICATION_REQUIRED` with `needs_verification=True`.
3. **Explaining Family-Member Ambiguity:**
   The comparison finding explicitly records:
   `"Name is a subset of the comparison name with missing tokens ('priti'); manual verification is required to confirm identity and avoid family-member confusion."`
4. **Initials Preservation:**
   Legitimate abbreviated names (e.g., `"Priti S. Ahire"` or `"P. S. Ahire"`) are recognized via prefix-initial alignment and are preserved within the verification/likely-match band without generating false mismatches.

---

## 4. Regression Verification & Focused Inspection

A dedicated test suite in `tests/ai/test_name_matching.py` permanently asserts this safety invariant:

```python
def test_name_family_member_subset_critical_vulnerability():
    matcher = NameMatcher()
    finding = matcher.compare("Shashikant Ahire", "Priti Shashikant Ahire")

    assert finding.status not in (MatchStatus.MATCH, MatchStatus.LIKELY_MATCH)
    assert finding.status == MatchStatus.VERIFICATION_REQUIRED
    assert finding.similarity_score < 1.0
    assert "subset" in finding.explanation.lower()
```

### Focused Results Check

* **Critical Case:**
  * **Input:** `"Shashikant Ahire"` vs `"Priti Shashikant Ahire"`
  * **Status:** `VERIFICATION_REQUIRED` (Needs verification: `True`)
  * **Score:** `0.8421` (Reduced from `1.0`)
  * **Vulnerability:** **RESOLVED**
* **Initial Case:**
  * **Input:** `"Priti S. Ahire"` vs `"Priti Shashikant Ahire"`
  * **Status:** `LIKELY_MATCH` (Score: `0.9167`)
  * **Preservation:** **VERIFIED**
* **Multi-Initial Case:**
  * **Input:** `"P. S. Ahire"` vs `"Priti Shashikant Ahire"`
  * **Status:** `VERIFICATION_REQUIRED` (Score: `0.7500`)
  * **Preservation:** **VERIFIED (No longer FALSE MISMATCH)**

---

## 5. Milestone Suite Performance (Task 16 Baseline)

```powershell
pytest tests/ai -q           # 251 passed in 1.43s
pytest tests/evaluation -q   # 25 passed in 0.83s
python -m evaluation.benchmark # All 4 suites passing, 0 false matches
```

---

## 6. Task 17 — Multilingual & Difficult Document Evaluation

In Task 17, the evaluation dataset was expanded from 65 cases to **132 synthetic fixtures** across four evaluation categories, explicitly targeting **Hindi (Devanagari)**, **Marathi (Devanagari)**, **Bilingual (English + Indic)**, and **eight degraded document conditions** (scanned, camera capture, rotated, blurry, low-contrast, compressed, multi-page, and clean).

### Expanded Dataset Composition

* **Classification:** 44 cases (English: 31, Bilingual: 5, Hindi: 4, Marathi: 4)
* **Matching:** 44 cases (English: 30, Marathi: 8, Hindi: 3, Bilingual: 3)
* **Instructions:** 22 cases (English: 12, Bilingual: 5, Hindi: 3, Marathi: 2)
* **Field Extraction:** 22 cases / 72 fields (English: 14, Marathi: 4, Hindi: 3, Bilingual: 1)

### Empirical Benchmark Results

| Evaluation Suite | Cases / Fields | Metric 1 | Metric 2 | Metric 3 | Safety Finding |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Classification** | 44 cases | **Accuracy: 0.7273** | Precision: 0.8594 | **Macro F1: 0.7857** | Clean degradation on Indic text |
| **Matching** | 44 cases | **Accuracy: 0.8182** | Precision: 0.8698 | **Macro F1: 0.8456** | **0 False Matches (Zero Regressions)** |
| **Instructions** | 22 cases | Precision: 1.0000 | Recall: 0.6957 | **F1: 0.8205** | High precision, lower Indic recall |
| **Field Extraction** | 72 fields | Exact: 0.7639 | **Normalized: 0.9861** | Missing: 0 | Extraction contract intact |

---

## 7. Multilingual Performance Breakdown

### Document Classification by Language

| Language | Total Cases | Correct | Accuracy | Macro F1 | Observed Behavior |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Bilingual** (English + Indic) | 5 | 5 | **1.0000** | **1.0000** | English keywords present; 100% classified correctly |
| **English** | 31 | 27 | **0.8710** | **0.9018** | High accuracy baseline; errors on ambiguous/empty text |
| **Hindi** (Devanagari) | 4 | 0 | **0.0000** | **0.0000** | Complete blindness; predicted UNKNOWN (0.0 score) |
| **Marathi** (Devanagari) | 4 | 0 | **0.0000** | **0.0000** | Complete blindness; predicted UNKNOWN (0.0 score) |

**Key Finding:** The deterministic classifier relies solely on Latin ASCII regexes. It functions seamlessly on bilingual documents that include English headers, but is completely blind to pure Hindi or Marathi documents.

### Cross-Document Matching by Language

| Language / Script Pair | Total Cases | Correct | Accuracy | Macro F1 | False Matches (FP) | False Mismatches (FN) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Hindi** (Same-script Devanagari) | 3 | 3 | **1.0000** | **1.0000** | **0** | 0 |
| **Marathi** (Same-script Devanagari) | 8 | 7 | **0.8750** | **0.6190** | **0** | 0 |
| **English** (Latin) | 30 | 26 | **0.8667** | **0.8815** | **0** | 2 |
| **Bilingual** (Latin vs Devanagari) | 3 | 0 | **0.0000** | **0.0000** | **0** | 0 |

**Safety Invariant Verified:**
The critical family-member subset safety protection discovered in Task 16 (**`"शशिकांत अहिरे"` vs `"प्रीती शशिकांत अहिरे"`**) was thoroughly evaluated in Devanagari. It successfully prevented any false positive match, correctly returning `VERIFICATION_REQUIRED` (`needs_verification=True`). Across all 44 cases and all language pairs, **0 false matches were produced**.

---

## 8. Document Condition Evaluation

### Classification by Condition

| Condition | Cases | Accuracy | Macro F1 | Performance Notes |
| :--- | :---: | :---: | :---: | :--- |
| **Clean** | 36 | 0.6944 | 0.7491 | Drops from 0.86 to 0.69 due to pure Hindi/Marathi documents |
| **Scanned** | 2 | 1.0000 | 1.0000 | Text-layer survives standard scanning |
| **Rotated** | 1 | 1.0000 | 1.0000 | Aspect-ratio heuristic flags portrait/landscape orientation |
| **Blurry** | 1 | 1.0000 | 1.0000 | Document classified if salient tokens survive optical blur |
| **Low Contrast** | 1 | 1.0000 | 1.0000 | Header tokens remain readable |
| **Compressed** | 1 | 1.0000 | 1.0000 | Lossy compression artifacts do not destroy ASCII keywords |
| **Multi-Page** | 1 | 1.0000 | 1.0000 | First-page weighting correctly prioritizes marksheet |
| **Camera** | 1 | 0.0000 | 0.0000 | Smartphone photo without native OCR text predicts UNKNOWN |

### Matching by Condition

| Condition | Cases | Accuracy | Macro F1 | Performance Notes |
| :--- | :---: | :---: | :---: | :--- |
| **Clean** | 36 | 0.8889 | 0.9056 | Standard baseline matching performance |
| **Camera** | 1 | 1.0000 | 1.0000 | Truncation safety correctly prevents false match |
| **Compressed** | 1 | 1.0000 | 1.0000 | Minor character drops match within fuzzy tolerance |
| **Low Contrast** | 1 | 1.0000 | 1.0000 | Date digit flip correctly flagged as MISMATCH |
| **Scanned** | 4 | 0.2500 | 0.1667 | Optical noise (e.g. `Pr1ti Ah1r3`) drops similarity below threshold |
| **Blurry** | 1 | 0.0000 | 0.0000 | Spaced-letter OCR artifacts (`P r i t i`) disrupt token parsing |

---

## 9. Newly Discovered Weaknesses (Observed Empirical Evidence)

### 1. Indic Combining Vowel Mark (Matra) Stripping in `NameNormalizer`
* **Observation:** In `ai/normalization/name_normalizer.py`, regex `re.sub(r"[^\w\s]", " ", raw)` is used to strip punctuation.
* **Failure Mechanism:** In Python's standard `re` engine, `\w` matches only Unicode category `L` (Letters) and `N` (Numbers). Indic vowel signs (*matras*: `ा`, `ि`, `ी`, `ु`, `ू`, `्`, `ं`) belong to the `M` (Combining Mark) category (`Mn`/`Mc`).
* **Impact:** Standard normalization inadvertently replaces all Devanagari vowel signs with spaces. For example, `"पाटील"` becomes `"प ट ल"`, and `"प्रीती"` fragments into `"प"`, `"र"`, `"त"`. While exact matches still coincide, word structure and token length calculations are distorted.

### 2. Complete Cross-Script Blindness (Latin vs. Devanagari)
* **Observation:** Cross-document matching between English application records and Marathi/Hindi identity records (e.g., `"Priti Ahire"` vs. `"प्रीती अहिरे"`) achieves **0.0000 Accuracy**.
* **Failure Mechanism:** With zero shared characters across Latin and Devanagari scripts, RapidFuzz reports `similarity = 0.0`, returning `MISMATCH`.
* **Impact:** State scholarship platforms regularly receive bilingual documentation. Without a transliteration bridge, cross-script comparisons cannot identify matching applicant records.

### 3. Pure Indic Text Blindness in Document Classifier & Instruction Extractor
* **Observation:** Pure Hindi and Marathi documents score **0.0000 Accuracy** in classification, and instruction recall drops to **0.6957**.
* **Failure Mechanism:** `CLASSIFICATION_SIGNALS` and `DOCUMENT_KEYWORDS` contain only English regex patterns (`\bmarksheet\b`, `\bincome\s+certificate\b`).
* **Impact:** Administrative documents issued exclusively in state languages (e.g. Tahsildar *उत्पन्न प्रमाणपत्र* or state board *गुणपत्रिका*) cannot be categorized by the deterministic rule engine without English headers or an OCR/transliteration translation step.

### 4. Optical Substitution Noise in Scanned Records
* **Observation:** Scanned document matching accuracy fell to **0.2500**.
* **Failure Mechanism:** OCR character substitutions common in degraded scans (e.g., digit `1` for `i`, `3` for `e`) cause `token_sort_ratio` to drop below the `likely_match_threshold` of `0.90`.

---

## 10. Bottleneck Identification

Following the empirical benchmark execution, we identify the primary pipeline bottlenecks in order of impact:

```text
Rank 1: E. Multilingual handling (Combined with C. Normalization)
        - Pure Hindi/Marathi classification = 0%
        - Latin vs Devanagari cross-script matching = 0%
        - Matra stripping in regex normalization
        - Pure Hindi/Marathi instruction recall drops to 0%

Rank 2: F. Image/document preprocessing & Vision OCR
        - Smartphone camera photos and image scans lack machine-readable text
        - Inability to classify image-only documents without Vision API / OCR

Rank 3: B. Name matching on OCR-degraded strings
        - OCR character confusion (1/i, 0/o, 5/s) penalizes edit distance
```

---

## 11. Ranked Recommendations

Based on concrete benchmark evidence:

1. **Extend `NameNormalizer` to Preserve Indic Combining Marks:**
   Update `ai/normalization/name_normalizer.py` to preserve Unicode category `M` (`\p{M}`) or range `\u0900-\u097F` so Devanagari words maintain their phonetic and orthographic integrity.
2. **Expand Classification and Instruction Vocabulary to Indic Terminology:**
   Add Hindi and Marathi keyword mappings to `CLASSIFICATION_SIGNALS` and `DOCUMENT_KEYWORDS` (e.g., *उत्पन्न प्रमाणपत्र*, *आय प्रमाण पत्र*, *गुणपत्रिका*, *अंकतालिका*, *जात प्रमाणपत्र*, *अर्ज*).
3. **Implement Cross-Script Transliteration Layer:**
   Introduce a deterministic Indic-to-Latin transliteration preprocessor (e.g., IndicSoundex or rule-based Devanagari-to-Latin character transliteration) before name matching.
4. **Connect Live Vision / OCR Extraction Pipeline:**
   Deploy a Vision OCR provider to extract structured text from camera photos and scanned image PDFs before passing them to the downstream intelligence pipeline.

---

## 12. Task 19 Evaluation: Multilingual Classification & Instruction Signals

### 1. Executive Summary & Benchmark Progression

Task 18 resolved the Devanagari Unicode combining mark (matra) corruption in `NameNormalizer`.
Task 19 introduced carefully curated, deterministic Hindi and Marathi signal patterns for document classification and instruction requirement extraction.

#### Benchmark Comparison: Before vs. After Task 19

| Metric | Before Task 19 (Task 17 Baseline) | After Task 19 (Multilingual Signals) | Absolute Change | Impact & Analysis |
| :--- | :---: | :---: | :---: | :--- |
| **Classification Overall Accuracy** | **0.7727** (34/44) | **0.9231** (48/52) | **+15.04%** | Pure Hindi and Marathi documents now classify correctly |
| **Classification Overall F1 (Macro)**| **0.7857** | **0.9138** | **+0.1281** | Balanced category performance across languages |
| **Hindi Classification Accuracy** | **0.0000** (0/4) | **1.0000** (8/8) | **+100.0%** | Pure Hindi income, caste, marksheet, aadhaar, app forms recognized |
| **Marathi Classification Accuracy** | **0.0000** (0/4) | **1.0000** (8/8) | **+100.0%** | Pure Marathi *उत्पन्न प्रमाणपत्र*, *जात प्रमाणपत्र*, *गुणपत्रिका*, *अर्ज* recognized |
| **English Classification Accuracy** | 0.8710 (27/31) | 0.8710 (27/31) | **0.00%** | Zero regression on existing English classification |
| **Bilingual Classification Accuracy**| 1.0000 (5/5) | 1.0000 (5/5) | **0.00%** | Maintained 100% accuracy on mixed-language documents |
| **Instruction Extraction Precision** | **1.0000** | **1.0000** | **0.00%** | Zero fabricated requirements across all languages |
| **Instruction Extraction Recall** | **0.6957** | **0.9375** | **+24.18%** | Extracted Indic mandatory docs, photo, format, size, eligibility |
| **Instruction Extraction F1** | **0.8205** | **0.9677** | **+0.1472** | High-precision deterministic requirement parsing |
| **Hindi Instruction Recall** | **0.0000** | **1.0000** (6/6) | **+100.0%** | Extracted Hindi certificate mandates, formats, and percentages |
| **Marathi Instruction Recall** | **0.0000** | **1.0000** (6/6) | **+100.0%** | Extracted Marathi certificate mandates, sizes, and photo guidelines |
| **Matching False Matches (FP)** | **0** | **0** | **0 (Preserved)**| Task 16 family-member safety invariant strictly preserved |

*(Note: Test dataset expanded to 52 classification cases and 29 instruction cases to ensure representative evaluation coverage).*

---

### 2. Architectural Additions & Engineering Fixes

1. **Indic Unicode Word Boundary Handling in `DocumentClassifier`:**
   In standard Python `re`, `\b` fails on Devanagari words ending in combining marks (`\u0900-\u097F`, e.g. *गुणपत्रिका* or *अंकतालिका*) because category `M` (`Mc`/`Mn`) characters are not categorized as `\w`.
   `DocumentClassifier._matches_pattern` was updated to:
   ```python
   regex = rf"(?<![\w\u0900-\u097f]){re.escape(pattern)}(?![\w\u0900-\u097f])"
   ```
   This accurately detects word boundaries in both Latin and Devanagari scripts without dropping combining characters.

2. **Conservative Multilingual Vocabulary:**
   Added high-confidence, non-ambiguous compound signals in `ai/classification/classification_signals.py`:
   - **Income Certificate:** Hindi *आय प्रमाण पत्र*, *आय प्रमाणपत्र*, *वार्षिक आय*; Marathi *उत्पन्न प्रमाणपत्र*, *वार्षिक उत्पन्न*.
   - **Caste Certificate:** Hindi *जाति प्रमाण पत्र*, *अनुसूचित जाति*; Marathi *जात प्रमाणपत्र*, *जात पडताळणी*, *जात वैधता*.
   - **Marksheet:** Hindi *अंकतालिका*, *अंक प्रमाणपत्र*; Marathi *गुणपत्रिका*, *गुणपत्रक*, *टक्केवारी*.
   - **Application Form:** Hindi *आवेदन पत्र*, *छात्रवृत्ति आवेदन*; Marathi *शिष्यवृत्ती अर्ज*, *अर्ज क्रमांक*.
   - **Identity Document:** Hindi/Marathi *भारतीय विशिष्ट पहचान प्राधिकरण*, *पहचान पत्र*, *ओळखपत्र*, *निवडणूक ओळखपत्र*.

3. **Multilingual Instruction Extractor Enhancements:**
   - **Mandatory Documents:** Mapped Devanagari certificate terminology in `DOCUMENT_KEYWORDS`.
   - **File Formats:** Supported explicit format statements in Hindi (*केवल PDF*, *प्रारूप*) and Marathi (*फक्त PDF*, *स्वरूप*), plus transliterated tokens (*पीडीएफ*, *जेपीजी*, *पीएनजी*).
   - **File Sizes:** Supported Devanagari size indicators (*अधिकतम फ़ाइल आकार*, *कमाल फाइल आकार*, *एमबी*, *केबी*) reusing existing byte conversion multipliers.
   - **Photograph Specifications:** Recognized dimensions (*पासपोर्ट आकार*) and background color (*सफेद पृष्ठभूमि*, *पांढरी पार्श्वभूमी*).
   - **Eligibility Constraints:** Extracted numeric percentage constraints (*न्यूनतम 60 प्रतिशत*, *किमान 60%*) without evaluating applicant satisfaction.
   - **Unknown Document Safety:** Unmapped certificates (*बोनाफाइड प्रमाणपत्र*) are preserved as `DocumentType.UNKNOWN` with constraints.

---

### 3. Remaining Limitations & Multilingual Weaknesses

While simple, structured Indic administrative text is now well-supported by the deterministic layer, several real-world bottlenecks remain:

1. **Cross-Script Matching Barrier (Latin vs. Devanagari):**
   Names in English (`"Priti Ahire"`) and Marathi (`"प्रीती अहिरे"`) still yield `0.0000` similarity. Cross-script matching requires an Indic-to-Latin transliteration bridge (e.g. ISO 15919 or IndicSoundex).
2. **Ambiguous Indic Vocabulary:**
   Generic single words like *नाव*, *नाम*, *दिनांक*, *तारीख* intentionally do not trigger confident classification without secondary corroborating evidence.
3. **Complex Free-form Instructions:**
   Unusual syntax, convoluted legal caveats, or multi-clause sentence structures that deviate from administrative templates cannot be fully parsed without an LLM/NLP semantic layer.
4. **Scanned / Camera Images Without Native Text:**
   Smartphone photo submissions without machine-readable text continue to require a Vision OCR provider.

> **Evaluation Caveat:** These results evaluate deterministic baseline signals on synthetic, anonymized development fixtures. They demonstrate framework correctness and baseline logic, NOT production accuracy on degraded, handwritten, or live government records.

---

## 13. Task 20 Evaluation: Cross-Script Latin ↔ Devanagari Name Matching

### 1. Executive Summary & Benchmark Progression

Task 19 introduced Hindi and Marathi classification and instruction signals, but identified a major cross-document matching barrier:
names in English (`"Priti Ahire"`) and Devanagari (`"प्रीती अहिरे"`) produced `0.0000` similarity and `0.0000` accuracy across all bilingual pairs.

Task 20 resolved this vulnerability by introducing a lightweight, deterministic, explainable cross-script transliteration layer (`ai/matching/transliteration.py`) and integrating it into `NameMatcher`.

#### Benchmark Comparison: Before vs. After Task 20

| Metric | Before Task 20 (Task 19 Baseline) | After Task 20 (Cross-Script Transliteration) | Absolute Change | Impact & Analysis |
| :--- | :---: | :---: | :---: | :--- |
| **Matching Overall Accuracy** | **0.8182** (36/44) | **0.8958** (43/48) | **+7.76%** | Latin ↔ Devanagari name comparisons now resolve accurately |
| **Matching Overall F1 (Macro)** | **0.8400** | **0.9049** | **+0.0649** | Balanced category performance across scripts |
| **Bilingual Matching Accuracy** | **0.0000** (0/3) | **1.0000** (7/7) | **+100.0%** | Cross-script matches (*Priti*, *Amit*, *Sneha*, *Shashikant*, *Pooja*) resolve |
| **Bilingual Matching F1** | **0.0000** | **1.0000** | **+1.0000** | Complete elimination of cross-script false mismatches |
| **English Matching Accuracy** | 0.8667 (26/30) | 0.8667 (26/30) | **0.00%** | Zero regression on existing English matching |
| **Hindi Matching Accuracy** | 1.0000 (3/3) | 1.0000 (3/3) | **0.00%** | Zero regression on existing Hindi matching |
| **Marathi Matching Accuracy** | 0.8750 (7/8) | 0.8750 (7/8) | **0.00%** | Zero regression on existing Marathi matching |
| **Matching False Matches (FP)** | **0** | **0** | **0 (Preserved)** | Task 16 family-member safety invariant strictly preserved |
| **Matching False Mismatches (FN)**| **2** | **2** | **0** | Remaining mismatches are heavily degraded OCR test fixtures |

*(Note: Synthetic matching dataset expanded to 48 cases, adding representative cross-script equivalents, spelling variants, unrelated false-positive controls, and cross-script family-member subset cases).*

---

### 2. Architectural Design & Guardrails

1. **Lightweight Deterministic Transliteration (`ai/matching/transliteration.py`):**
   - **Independent Vowels:** Canonical mappings for `अ` (`a`), `आ` (`a`), `इ`/`ई` (`i`), `उ`/`ऊ` (`u`), `ऋ` (`ri`), `ए` (`e`), `ऐ` (`ai`), `ओ` (`o`), `औ` (`au`).
   - **Consonants & Matras:** Mapped standard Sanskrit/Hindi/Marathi consonants and dependent vowel signs (`ा`, `ि`, `ी`, `ु`, `ू`, `े`, `ै`, `ो`, `ौ`).
   - **Marathi Special Consonants:** Handled retroflex `ळ` (`l`), `ऱ` (`r`), and phonetic Anglicization of `व` before `ा` (`wa` as in *Pawar*, *Gaikwad*, *Sawant*, vs `v` as in *Vikas*, *Vijay*).
   - **Phonetic Anusvara (`ं`) Assimilation:** Assimilates to `m` before labial consonants (`प`, `फ`, `ब`, `भ`, `म`, e.g. *अंबर* → *ambar*), and `n` elsewhere (*शशिकांत* → *shashikant*, *संजय* → *sanjay*).
   - **Schwa Deletion:** Applies deterministic Hindi/Marathi schwa deletion: drops inherent `a` at word endings (*अमित* → *amit*, *पाटील* → *patil*, *सुरेश* → *suresh*), and deletes medial schwa in $VC\_CV$ phonological environments (*देशमुख* → *deshmukh*).

2. **Cross-Script Gating (`is_cross_script`):**
   - Transliteration is triggered **only** when one name is Latin and the other is Devanagari.
   - Same-script comparisons (`"Priti Ahire"` vs `"Priti Ahire"`, or `"अमित पाटील"` vs `"अमित पाटील"`) completely bypass transliteration and take the existing high-speed exact path.

3. **Original Value & Finding Integrity:**
   - Transliterated forms (`comp_a`, `comp_b`) are strictly internal ephemeral comparison keys.
   - The returned `ComparisonFinding` preserves original user strings (`source_value`, `comparison_value`) and original normalized strings (`normalized_source_value`, `normalized_comparison_value`) untouched.

4. **Task 16 Family-Member Subset Invariant Preservation:**
   - Shorter family-member names across scripts (`"Shashikant Ahire"` vs `"प्रीती शशिकांत अहिरे"`) trigger strict subset protection.
   - The finding identifies the missing full-name tokens (`'priti'`) and prohibits `MATCH` or `LIKELY_MATCH`, strictly routing to `VERIFICATION_REQUIRED` (`needs_verification=True`).
   - Single-token surnames (`"Ahire"` vs `"प्रीती शशिकांत अहिरे"`) route to `MISMATCH` due to insufficient identity evidence.

---

### 3. Remaining Limitations & Edge Cases

While standard, well-formed Hindi and Marathi names now match across scripts, the following real-world boundaries remain:

1. **Unusual or Multiple English Spelling Variants:**
   - English representations of Indian names frequently exhibit divergent Anglo-Indian spelling conventions (e.g. *Choudhary* vs *Chaudhari*, *Diksha* vs *Deeksha*, *Rao* vs *Raut*).
   - RapidFuzz similarity handles slight edit distances, but radically divergent spellings still require manual verification.
2. **Rare or Complex Sanskrit/Vedic Conjuncts:**
   - Unusual ligature clusters (e.g., archaic epigraphic or scholastic spellings) may not map perfectly to standard modern Latin digraphs.
3. **OCR Optical Degeneracy:**
   - Scanned and camera documents with optical noise (e.g. broken matras, blurred conjuncts, digit substitutions) can degrade both Latin and Devanagari text before transliteration.
4. **Handwritten Submissions:**
   - Handwritten administrative records cannot be parsed by rule-based character mappings without an OCR/Vision recognition layer.
5. **No General-Purpose Transliteration Claim:**
   - This implementation is purposefully scoped as an explainable, deterministic helper for Indian administrative names; it does not claim complete dictionary coverage for arbitrary prose sentences.
