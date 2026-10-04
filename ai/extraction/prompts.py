"""Document-aware extraction prompts for scholarship documents with strict no-hallucination rules."""

from ai.schemas.document import DocumentType

SYSTEM_EXTRACTION_PROMPT = """You are an accurate, strict document information extraction system for scholarship applications.
Your duty is to extract ONLY information that is explicitly stated and visibly present in the document.
STRICT NO-HALLUCINATION RULES:
1. If any field or piece of information is not present or visible in the document, return null for that field.
2. Never infer, guess, complete, extrapolate, or fabricate any value.
3. Do NOT derive date of birth from age.
4. Do NOT derive person names from file names.
5. Do NOT derive certificate numbers from unrelated numbers or barcodes.
6. Preserve the original text exactly as written in the document.
7. Provide a confidence score between 0.0 and 1.0 for each extracted field based on text clarity.
8. Provide the exact text snippet from the document as evidence for each extracted field when available.
9. Return output strictly in valid JSON matching the specified schema.
"""

APPLICATION_FORM_PROMPT = """Extract information from this Scholarship Application Form.
Fields to extract:
- name: Full name of the applicant / student as printed on the form.
- date_of_birth: Date of birth of the applicant.
- father_name: Father's full name.
- mother_name: Mother's full name.
- address: Complete address of the applicant.
- additional_fields:
  - application_id: Application or registration number.
  - scheme_name: Name of the scholarship scheme applied for.
  - category: Caste or reservation category if mentioned.
  - course: Course or degree enrolled in.
  - institution: School, college, or university name.

Remember: If any field is absent, set its value to null.
"""

AADHAAR_IDENTITY_PROMPT = """Extract information from this Identity / Aadhaar Document.
Fields to extract:
- name: Full name of the person as written on the identity card.
- date_of_birth: Date of birth (DOB) or Year of Birth (YOB).
- address: Full residential address as printed.
- additional_fields:
  - identity_number: Masked or unmasked Aadhaar / ID number exactly as printed. Never guess missing digits.
  - gender: Gender (Male / Female / Transgender).

Remember: If any field is absent, set its value to null.
"""

MARKSHEET_PROMPT = """Extract information from this Academic Marksheet / Grade Card / Transcript.
Fields to extract:
- name: Candidate / Student full name.
- marks: Total marks obtained (e.g. 450/500 or 450).
- percentage: Overall percentage or percentile (e.g. 85.5%).
- additional_fields:
  - examination: Examination name (e.g. SSC, HSC, B.Tech Sem V).
  - board_or_university: Issuing educational board or university.
  - roll_number: Roll number, seat number, or registration number.
  - passing_year: Year or session of passing.
  - cgpa: Cumulative Grade Point Average if stated.
  - sgpa: Semester Grade Point Average if stated.
  - result_status: Pass / Fail status.

Remember: If any field is absent, set its value to null.
"""

INCOME_CERTIFICATE_PROMPT = """Extract information from this Income Certificate.
Fields to extract:
- name: Full name of the certificate holder or family head.
- certificate_number: Unique certificate number or barcode reference.
- issue_date: Date on which the certificate was issued.
- expiry_date: Expiry date or validity period if explicitly stated.
- additional_fields:
  - annual_income: Annual / Gross family income amount in figures or words.
  - issuing_authority: Authority who issued the certificate (e.g. Tehsildar, Sub-Divisional Magistrate).
  - financial_year: Financial year for which income is certified.

Remember: If any field is absent, set its value to null.
"""

CASTE_CERTIFICATE_PROMPT = """Extract information from this Caste / Community Certificate.
Fields to extract:
- name: Full name of the applicant or beneficiary.
- certificate_number: Official certificate number or registration reference.
- issue_date: Date of issuance.
- additional_fields:
  - caste: Specific caste, tribe, or community name.
  - sub_caste: Sub-caste name if explicitly mentioned.
  - category: Category classification (SC, ST, OBC, General, etc.).
  - issuing_authority: Designation of the issuing authority.

Remember: If any field is absent, set its value to null.
"""

PHOTOGRAPH_PROMPT = """Verify candidate photograph document.
Do not perform OCR on text. Confirm image validity, aspect ratio, and portrait framing.
Extract metadata into additional_fields:
- is_portrait_photograph: true/false
- framing_notes: Notes on image quality or framing.
"""

INSTRUCTIONS_PROMPT = """Extract application guidelines and document submission instructions.
Extract into additional_fields:
- required_documents: List of required documents to be submitted.
- accepted_formats: Allowed file formats (e.g. PDF, JPG, PNG).
- max_file_size: Maximum allowed file size if specified.
- application_deadline: Submission deadline or last date.
- eligibility_requirements: Key eligibility criteria stated.
"""

DEFAULT_PROMPT = """Extract any explicitly present scholarship application fields:
- name: Person's full name.
- date_of_birth: Date of birth.
- father_name: Father's name.
- mother_name: Mother's name.
- address: Residential address.
- certificate_number: Any document or certificate identification number.
- issue_date: Date of issue.
- expiry_date: Date of expiry.
- marks: Total marks obtained.
- percentage: Percentage or score.

If a field is not present in the document, return null. Never guess.
"""

PROMPT_REGISTRY = {
    DocumentType.APPLICATION_FORM: APPLICATION_FORM_PROMPT,
    DocumentType.AADHAAR_OR_IDENTITY: AADHAAR_IDENTITY_PROMPT,
    DocumentType.MARKSHEET: MARKSHEET_PROMPT,
    DocumentType.INCOME_CERTIFICATE: INCOME_CERTIFICATE_PROMPT,
    DocumentType.CASTE_CERTIFICATE: CASTE_CERTIFICATE_PROMPT,
    DocumentType.PHOTOGRAPH: PHOTOGRAPH_PROMPT,
    DocumentType.INSTRUCTIONS: INSTRUCTIONS_PROMPT,
    DocumentType.UNKNOWN: DEFAULT_PROMPT,
}


def get_extraction_prompt(doc_type: DocumentType) -> str:
    """Retrieve the document-specific extraction prompt for a given DocumentType."""
    return PROMPT_REGISTRY.get(doc_type, DEFAULT_PROMPT)
