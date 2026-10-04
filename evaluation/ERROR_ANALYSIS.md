# PreFlight AI Evaluation & Error Analysis Report

**Task:** Task 15 — Run AI Evaluation and Analyze Results  
**Repository:** `D:\DYP DPU\PreFlight`  
**Branch:** `feature/aiml`  
**Date:** October 2026  
**Status:** Evaluation Complete — Benchmark Executed & Analyzed  

---

## 1. Evaluation Scope & Methodology

This evaluation report benchmarks the core deterministic and structured components of the PreFlight document intelligence pipeline:

1. **Document Classification**: Signal-based deterministic classifier evaluated on multi-class scholarship records and out-of-distribution inputs.
2. **Cross-Document Matching**: RapidFuzz fuzzy name, date of birth, and address comparison across application records.
3. **Instruction Extraction**: Regex and keyword extraction of mandatory documents, formats, sizes, and percentage constraints.
4. **Field Extraction & Normalization**: Field canonicalization across core scholarship schemas.

### Critical Dataset Notice: DEVELOPMENT / SYNTHETIC EVALUATION DATA

* **Dataset Size:** 65 total synthetic cases across 4 suites (22 classification, 22 matching, 11 instructions, 10 extraction cases with 35 evaluated fields).
* **Synthetic & Anonymized:** Contains **zero** genuine student personal records, zero live Aadhaar numbers, and zero scanned government certificates.
* **Non-Production Claim:** This benchmark validates framework plumbing, metric algorithms, and deterministic edge cases. It **does NOT** represent production accuracy on live, messy, scanned government documents.

---

## 2. Benchmark Results Summary

The evaluation suite was executed via `python -m evaluation.benchmark`. All metrics are dynamically computed from ground truth comparisons with safe division.

### Aggregate Performance Table

| Component | Evaluated Cases / Units | Accuracy | Precision (Macro) | Recall (Macro) | F1 (Macro) | False Matches (FP) | False Mismatches (FN) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Document Classification** | 22 cases | **0.8636** | 0.8750 | 0.9018 | 0.8837 | N/A | N/A |
| **Cross-Document Matching** | 22 cases | **0.7727** | 0.8571 | 0.7867 | 0.7826 | **1** | **1** |
| **Instruction Extraction** | 11 cases | N/A | **1.0000** | **1.0000** | **1.0000** | 0 | 0 |
| **Field Extraction & Normalization** | 35 fields | N/A | Exact: **0.8000** | Norm: **1.0000** | Missing: **0.0000** | 0 | 0 |

---

## 3. Detailed Error Analysis

Below is an honest, itemized breakdown of every failure observed during the benchmark run.

### A. Classification Failures (3 out of 22 cases)

#### Error 1: `class_07_photo_aspect_ratio`
* **Expected:** `photograph`
* **Predicted:** `unknown` (Confidence: 0.25, `needs_verification=True`)
* **Why it failed:** The input is an image (`image_001.png`, 300x400) without embedded text and without explicit filename clues. In `DocumentClassifier._classify_by_image`, a portrait aspect ratio matching passport dimensions without filename keywords is assigned a base confidence of 0.25. Because 0.25 < `verification_threshold` (0.75), the document type is downgraded to `UNKNOWN`.
* **Component responsible:** `ai.classification.document_classifier.DocumentClassifier` (`_classify_by_image`)
* **Potential improvement:** Rather than downgrading portrait images to `UNKNOWN` purely due to generic filenames, classify as `photograph` with `needs_verification=True` and moderate confidence (e.g., 0.50), or introduce visual face/edge detection heuristics.

#### Error 2: `class_11_ambiguous_conflicting`
* **Expected:** `unknown`
* **Predicted:** `income_certificate` (Confidence: 0.70)
* **Snippet:** `"Application\nAnnual Income"`
* **Why it failed:** In `CLASSIFICATION_SIGNALS`, the signal "Annual Income" possesses a higher signal weight than "Application". Consequently, `income_certificate` scored higher than `application_form`, breaking the intended tie and predicting `income_certificate` rather than classifying the conflict as ambiguous.
* **Component responsible:** `ai.classification.document_classifier.DocumentClassifier` (`_classify_by_text`)
* **Potential improvement:** When top competing class scores both fall below a decisive threshold and their ratio is within 15%, treat the document as an ambiguous conflict and route to `UNKNOWN` with `needs_verification=True`.

#### Error 3: `class_22_landscape_photo_ambiguous`
* **Expected:** `unknown`
* **Predicted:** `photograph` (Confidence: 0.92)
* **Image Dimensions:** 800x500 (Landscape aspect ratio: 1.6)
* **Why it failed:** The file was named `scan_photo.jpg`. In `_classify_by_image`, filename keyword matching for `"photo"` took absolute precedence and assigned `photograph` with 0.92 confidence, completely ignoring the contradictory landscape aspect ratio.
* **Component responsible:** `ai.classification.document_classifier.DocumentClassifier` (`_classify_by_image`)
* **Potential improvement:** Require both filename clue and non-landscape aspect ratio before assigning high-confidence `photograph`, or penalize confidence when aspect ratio contradicts portrait framing.

---

### B. Cross-Document Matching Failures (5 out of 22 cases)

#### Error 1: `match_02_case_whitespace_name`
* **Expected:** `match`
* **Predicted:** `mismatch` (Similarity Score: 0.0909)
* **Values:** `val_a = "PRITI   SHASHIKANT   AHIRE"`, `val_b = "priti shashikant ahire"`
* **Why it failed:** `NameMatcher.compare()` was evaluated directly on raw strings. RapidFuzz `token_set_ratio` is case-sensitive when comparing un-normalized strings. In the full PreFlight pipeline, `NameNormalizer.normalize()` runs upstream, but `NameMatcher` lacked defensive lowercasing when called in isolation.
* **Component responsible:** `ai.matching.name_matcher.NameMatcher` (isolated interface assumption vs upstream normalization dependency)
* **Potential improvement:** Add defensive lowercasing and whitespace collapse inside `NameMatcher.compare()` as a guardrail against un-normalized upstream inputs.

#### Error 2: `match_03_token_reordering`
* **Expected:** `match`
* **Predicted:** `likely_match` (Similarity Score: 1.0)
* **Values:** `val_a = "Ahire Priti Shashikant"`, `val_b = "Priti Shashikant Ahire"`
* **Why it failed:** RapidFuzz `token_set_ratio` computed a score of 1.0 (100% token set overlap). However, `NameMatcher.compare()` assigns `MatchStatus.MATCH` only if the strings are strictly equal character-for-character (`norm_a == norm_b`). Because string order differed, it conservatively assigned `MatchStatus.LIKELY_MATCH` with `needs_verification=True`.
* **Component responsible:** `ai.matching.name_matcher.NameMatcher`
* **Potential improvement:** If sorted tokens of `norm_a` and `norm_b` are identical, allow promoting to `MatchStatus.MATCH`, or document this as an intentional safety policy where reordered names always require human review.

#### Error 3: `match_04_name_initials`
* **Expected:** `verification_required`
* **Predicted:** `likely_match` (Similarity Score: 0.9167)
* **Values:** `val_a = "Priti S Ahire"`, `val_b = "Priti Shashikant Ahire"`
* **Why it failed:** RapidFuzz `token_set_ratio` computed 0.9167, which exceeded the `likely_match_threshold` (0.90), categorizing it as `LIKELY_MATCH` rather than `VERIFICATION_REQUIRED`.
* **Component responsible:** `ai.matching.name_matcher.NameMatcher` (threshold tuning)
* **Potential improvement:** Detect single-letter initials explicitly; if a single-letter token matches the initial of a full name token, cap status at `VERIFICATION_REQUIRED`.

#### Error 4: `match_14_multitoken_initials`
* **Expected:** `verification_required`
* **Predicted:** `mismatch` (Similarity Score: 0.625)
* **Values:** `val_a = "P. S. Ahire"`, `val_b = "Priti Shashikant Ahire"`
* **Why it failed:** Two single-letter initials ("P." and "S.") dropped the token ratio to 0.625, falling below the `verification_threshold` (0.75). The system flagged this as a `MISMATCH` (**False Negative / False Mismatch**).
* **Component responsible:** `ai.matching.name_matcher.NameMatcher`
* **Potential improvement:** Implement initial-expansion heuristics for Indian patronymic naming conventions before computing string ratios.

#### Error 5: `match_17_family_member_confusion` *(CRITICAL SAFETY ERROR)*
* **Expected:** `mismatch`
* **Predicted:** `likely_match` (Similarity Score: 1.0)
* **Values:** `val_a = "Shashikant Ahire"` (Father), `val_b = "Priti Shashikant Ahire"` (Applicant Daughter)
* **Why it failed:** High-risk **FALSE MATCH (False Positive)**. Because all tokens of the father's name `{"Shashikant", "Ahire"}` form a subset of the applicant's name `{"Priti", "Shashikant", "Ahire"}`, RapidFuzz `token_set_ratio` scored the comparison as 1.0 (100%). The matcher declared a `LIKELY_MATCH`.
* **Component responsible:** `ai.matching.name_matcher.NameMatcher` (choice of `token_set_ratio` without token count penalty)
* **Potential improvement:** Switch from pure `token_set_ratio` to a token-count-penalized score or `token_sort_ratio` when token lengths differ by more than 1 token, preventing father/mother names from matching the applicant.

---

### C. Instruction Extraction Findings (0 errors)
* Evaluated 11 synthetic cases covering required documents, file formats, file sizes, photograph background/dimensions, and eligibility percentage thresholds.
* Precision: **1.0000**, Recall: **1.0000**, F1: **1.0000**.
* **Key Finding:** Regex and keyword parsing for English instruction brochures is reliable on clean text, but requires future evaluation on Marathi and mixed-script circulars.

---

### D. Field Extraction & Normalization Findings
* Evaluated 35 fields across 10 structured document cases.
* **Exact Match Rate:** 0.8000 (28/35 fields)
* **Normalized Match Rate:** **1.0000** (35/35 fields)
* **Missing Field Rate:** **0.0000**
* **Key Finding:** The `DocumentNormalizer` provided an immediate +20.00% boost in field match accuracy by successfully resolving date formats (`15/08/2004` -> `2004-08-15`), certificate numbers (`INC/2026/8899` -> `inc/2026/8899`), and name casing.

---

## 4. Strengths of the Current Pipeline

1. **Deterministic Baseline Integrity:** Classification correctly categorized 19 out of 22 documents (86.36% accuracy) across diverse categories without machine learning models.
2. **Normalization Effectiveness:** Value canonicalization achieved 100% consistency across dates, names, and certificate numbers.
3. **Instruction Parsing Accuracy:** Successfully extracted required documents, format constraints, size thresholds, and eligibility percentages with zero false alarms.
4. **Deterministic & Offline:** Benchmarks execute in under 2 seconds without external cloud calls, API keys, or internet connectivity.

---

## 5. Limitations of This Evaluation

1. **Synthetic & Development Only:** Fixtures do not represent the physical noise, folds, tears, stamps, or watermarks of genuine government records.
2. **No Live Multimodal Vision LLM Measurement:** Offline extraction uses deterministic mocks; it does not measure multimodal LLM hallucinations or optical OCR errors.
3. **No Multilingual Testing:** Does not yet test Marathi (Devanagari script) or Hindi documents.
4. **Small Sample Size:** 65 total synthetic cases provide directional engineering signals, but cannot establish statistical population-level performance.

---

## 6. Decision on Production AI Modifications

Per Step 7 of the evaluation protocol:

### Selected Decision: **D. Dataset expansion needed before changing the model**

**Engineering Rationale:**
* While Error Analysis identified specific algorithmic edge cases (e.g., father-vs-daughter subset matching in `NameMatcher`), all 242 existing AI tests pass.
* Changing production matching thresholds or classifier signal weights right now would risk regressions across existing unit tests and would constitute tuning to a synthetic test set.
* The correct scientific progression is to preserve the production AI codebase, expand the evaluation dataset with realistic variations, and implement targeted algorithmic hardening in a dedicated task backed by regression benchmarks.

---

## 7. Priority-Ranked Improvement Roadmap

Based on empirical evidence from this benchmark:

1. **Priority 1 — Prevent Family Member False Matches in Name Matching**  
   * *Evidence:* `match_17_family_member_confusion` produced a high-risk False Positive (score 1.0) between father and daughter due to unpenalized subset token matching.  
   * *Action:* Replace pure `token_set_ratio` with token-count-penalized fuzzy comparison.

2. **Priority 2 — Improve Ambiguity Routing in Document Classification**  
   * *Evidence:* `class_11` and `class_22` showed that signal weights can override conflicting cues.  
   * *Action:* Implement strict conflict detection when competing classes have close scores or contradictory aspect ratios.

3. **Priority 3 — Add Multilingual (Marathi/Hindi) Evaluation Fixtures**  
   * *Evidence:* Most Maharashtra state scholarship records (Tahsildar certificates, caste validity) are issued in Marathi, but the current benchmark only contains English text.  
   * *Action:* Build synthetic Marathi evaluation fixtures to benchmark multilingual OCR/Vision readiness.
