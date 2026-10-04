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

## 5. Current Suite Performance

```powershell
pytest tests/ai -q           # 251 passed in 1.43s
pytest tests/evaluation -q   # 25 passed in 0.83s
python -m evaluation.benchmark # All 4 suites passing, 0 false matches
```

---

## 6. Remaining Limitations & Future Work

1. **Devanagari Transliteration:** Current fuzzy matching operates in Latin script. Names in Marathi (*शशिकांत अहिरे*) compared against English records require phonetic transliteration normalization (e.g. IndicSoundex or Double Metaphone).
2. **Compound Surnames:** Compound names with prefixes (*Deshmukh*, *Kulkarni*, *Patil-Bhosale*) require continuous expansion in synthetic test sets.
3. **Synthetic Data Constraint:** Metrics reflect development fixtures and validate algorithmic guardrails; they do not establish production accuracy on uncalibrated camera photos.
