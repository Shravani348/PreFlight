"""Signal keywords and phrase definitions for scholarship document classification."""

from typing import Dict, List, NamedTuple
from ai.schemas.document import DocumentType


class Signal(NamedTuple):
    """Signal phrase or keyword with its associated weight."""

    pattern: str
    weight: float


# Dictionary mapping supported document types to lists of weighted pattern signals
CLASSIFICATION_SIGNALS: Dict[DocumentType, List[Signal]] = {
    DocumentType.APPLICATION_FORM: [
        Signal("application form", 3.0),
        Signal("scholarship application", 3.0),
        Signal("online application", 2.5),
        Signal("applicant details", 2.5),
        Signal("registration number", 2.0),
        Signal("application id", 2.0),
        Signal("student registration", 2.0),
        Signal("scheme name", 2.0),
        Signal("applicant", 1.0),
        Signal("application", 1.0),
        Signal("scholarship", 1.0),
        Signal("student details", 1.5),
        Signal("candidate signature", 1.5),
    ],
    DocumentType.AADHAAR_OR_IDENTITY: [
        Signal("unique identification authority of india", 3.5),
        Signal("government of india", 2.0),
        Signal("aadhaar", 3.0),
        Signal("uidai", 2.5),
        Signal("election commission of india", 3.0),
        Signal("identity card", 2.5),
        Signal("voter id", 2.5),
        Signal("date of birth", 1.5),
        Signal("dob", 1.0),
        Signal("enrollment no", 2.0),
        Signal("help@uidai.gov.in", 3.0),
        Signal("male", 0.5),
        Signal("female", 0.5),
    ],
    DocumentType.MARKSHEET: [
        Signal("statement of marks", 3.5),
        Signal("mark sheet", 3.0),
        Signal("marksheet", 3.0),
        Signal("academic transcript", 3.0),
        Signal("grade card", 2.5),
        Signal("board of secondary education", 2.5),
        Signal("university examination", 2.5),
        Signal("total marks", 2.0),
        Signal("marks obtained", 2.0),
        Signal("percentage", 1.5),
        Signal("cgpa", 2.0),
        Signal("sgpa", 2.0),
        Signal("semester", 1.5),
        Signal("passed", 1.0),
        Signal("examination", 1.0),
        Signal("subjects", 1.0),
        Signal("maximum marks", 1.5),
    ],
    DocumentType.INCOME_CERTIFICATE: [
        Signal("income certificate", 3.5),
        Signal("family income", 3.0),
        Signal("annual income", 3.0),
        Signal("annual family income", 3.5),
        Signal("tahasildar", 2.5),
        Signal("tehsildar", 2.5),
        Signal("revenue department", 2.0),
        Signal("competent authority", 2.0),
        Signal("sub divisional magistrate", 2.5),
        Signal("sdm", 1.5),
        Signal("gross annual income", 2.5),
        Signal("income from all sources", 3.0),
        Signal("financial year", 1.0),
    ],
    DocumentType.CASTE_CERTIFICATE: [
        Signal("caste certificate", 3.5),
        Signal("community certificate", 3.0),
        Signal("scheduled caste", 3.0),
        Signal("scheduled tribe", 3.0),
        Signal("other backward class", 3.0),
        Signal("caste validity", 3.0),
        Signal("sub-caste", 2.0),
        Signal("constitution (scheduled castes) order", 3.5),
        Signal("category", 1.0),
        Signal("sc", 0.8),
        Signal("st", 0.8),
        Signal("obc", 1.5),
        Signal("sebc", 1.5),
        Signal("vjnt", 1.5),
    ],
    DocumentType.INSTRUCTIONS: [
        Signal("general instructions", 3.5),
        Signal("instructions to candidates", 3.5),
        Signal("guidelines for applicants", 3.0),
        Signal("how to apply", 2.5),
        Signal("eligibility criteria", 2.5),
        Signal("required documents", 2.5),
        Signal("documents to be uploaded", 2.5),
        Signal("upload instructions", 2.5),
        Signal("maximum file size", 2.0),
        Signal("file format", 1.5),
        Signal("terms and conditions", 2.0),
        Signal("mandatory requirements", 2.0),
        Signal("application procedure", 2.0),
    ],
}

# Clues indicative of photograph documents
PHOTO_FILENAME_CLUES: List[str] = [
    "photo",
    "photograph",
    "passport_photo",
    "passport_size",
    "profile_pic",
    "candidate_photo",
    "headshot",
]
