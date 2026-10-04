import json
import os
from typing import List
from backend.models.schemas import ApplicationRequirements, Requirement

def get_requirements(application_type: str) -> ApplicationRequirements:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    req_path = os.path.join(current_dir, "..", "requirements", f"{application_type}.json")
    
    if not os.path.exists(req_path):
        raise ValueError(f"Unsupported application type: {application_type}")
        
    with open(req_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    return ApplicationRequirements(**data)

def get_required_documents(application_type: str) -> List[Requirement]:
    app_reqs = get_requirements(application_type)
    return [req for req in app_reqs.requirements if req.required]
