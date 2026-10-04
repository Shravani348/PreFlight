import re
from typing import List
from difflib import SequenceMatcher
from backend.models.schemas import Requirement, DocumentMetadata, Issue

def check_required_documents(
    required_documents: List[Requirement],
    provided_documents: List[DocumentMetadata]
) -> List[Issue]:
    issues = []
    provided_types = {doc.document_type for doc in provided_documents}
    
    for req in required_documents:
        if req.required and req.document_type not in provided_types:
            issues.append(Issue(
                type="MISSING_DOCUMENT",
                severity="CRITICAL",
                message=f"Required document is missing: {req.document_type}",
                evidence=[],
                document_type=req.document_type
            ))
            
    return issues

def check_file_formats(
    required_documents: List[Requirement],
    provided_documents: List[DocumentMetadata]
) -> List[Issue]:
    issues = []
    req_dict = {req.document_type: req for req in required_documents}
    
    for doc in provided_documents:
        req = req_dict.get(doc.document_type)
        if req and req.allowed_formats:
            if doc.format not in req.allowed_formats:
                issues.append(Issue(
                    type="INVALID_FORMAT",
                    severity="WARNING",
                    message=f"Invalid format for {doc.document_type}: {doc.format}. Allowed: {', '.join(req.allowed_formats)}",
                    evidence=[f"Format: {doc.format}"],
                    document_type=doc.document_type
                ))
    return issues

def check_file_sizes(
    required_documents: List[Requirement],
    provided_documents: List[DocumentMetadata]
) -> List[Issue]:
    issues = []
    req_dict = {req.document_type: req for req in required_documents}
    
    for doc in provided_documents:
        req = req_dict.get(doc.document_type)
        if req and req.max_size_kb:
            if doc.size_kb > req.max_size_kb:
                issues.append(Issue(
                    type="FILE_TOO_LARGE",
                    severity="WARNING",
                    message=f"File {doc.document_type} exceeds maximum size of {req.max_size_kb}KB",
                    evidence=[f"Size: {doc.size_kb}KB"],
                    document_type=doc.document_type
                ))
    return issues

def normalize_date(date_str: str) -> str:
    date_str = str(date_str).strip()
    if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        return date_str
    
    match = re.match(r"^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$", date_str)
    if match:
        d, m, y = match.groups()
        return f"{y}-{int(m):02d}-{int(d):02d}"
        
    return date_str

def check_dob_consistency(provided_documents: List[DocumentMetadata]) -> List[Issue]:
    issues = []
    dobs = {}
    for doc in provided_documents:
        if "dob" in doc.extracted_data:
            normalized = normalize_date(doc.extracted_data["dob"])
            dobs[doc.document_type] = (normalized, doc.extracted_data["dob"])
            
    if len(dobs) > 1:
        unique_dates = set(norm for norm, orig in dobs.values())
        if len(unique_dates) > 1:
            evidence = [f"{dtype} dob: {orig}" for dtype, (norm, orig) in dobs.items()]
            issues.append(Issue(
                type="DOB_MISMATCH",
                severity="CRITICAL",
                message="Date of Birth mismatch across documents",
                evidence=evidence
            ))
    return issues

def normalize_name(name: str) -> str:
    name = re.sub(r'[^\w\s]', '', name).lower()
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def compare_names(name1: str, name2: str) -> str:
    norm1 = normalize_name(name1)
    norm2 = normalize_name(name2)
    
    if norm1 == norm2:
        return "MATCH"
        
    parts1 = norm1.split()
    parts2 = norm2.split()
    
    if len(parts1) == len(parts2):
        match_count = 0
        for p1, p2 in zip(parts1, parts2):
            if p1 == p2 or (len(p1) == 1 and p2.startswith(p1)) or (len(p2) == 1 and p1.startswith(p2)):
                match_count += 1
        if match_count == len(parts1):
            return "LIKELY_MATCH"
            
    ratio = SequenceMatcher(None, norm1, norm2).ratio()
    if ratio > 0.8:
        return "LIKELY_MATCH"
    elif ratio > 0.6:
        return "NEEDS_VERIFICATION"
    else:
        return "MISMATCH"

def check_name_consistency(provided_documents: List[DocumentMetadata]) -> List[Issue]:
    issues = []
    names = {}
    for doc in provided_documents:
        if "name" in doc.extracted_data:
            names[doc.document_type] = doc.extracted_data["name"]
            
    if len(names) > 1:
        doc_types = list(names.keys())
        for i in range(len(doc_types)):
            for j in range(i + 1, len(doc_types)):
                t1, t2 = doc_types[i], doc_types[j]
                n1, n2 = names[t1], names[t2]
                result = compare_names(n1, n2)
                
                if result == "MISMATCH":
                    issues.append(Issue(
                        type="NAME_MISMATCH",
                        severity="CRITICAL",
                        message=f"Name mismatch between {t1} and {t2}",
                        evidence=[f"{t1} name: {n1}", f"{t2} name: {n2}"]
                    ))
                elif result == "NEEDS_VERIFICATION":
                    issues.append(Issue(
                        type="NAME_NEEDS_VERIFICATION",
                        severity="WARNING",
                        message=f"Name consistency needs verification between {t1} and {t2}",
                        evidence=[f"{t1} name: {n1}", f"{t2} name: {n2}"]
                    ))
    return issues

def validate_documents(
    required_documents: List[Requirement],
    provided_documents: List[DocumentMetadata]
) -> List[Issue]:
    issues = []
    issues.extend(check_required_documents(required_documents, provided_documents))
    issues.extend(check_file_formats(required_documents, provided_documents))
    issues.extend(check_file_sizes(required_documents, provided_documents))
    issues.extend(check_dob_consistency(provided_documents))
    issues.extend(check_name_consistency(provided_documents))
    return issues
