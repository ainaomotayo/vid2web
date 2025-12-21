from pydantic import BaseModel
from typing import List, Optional

class ValidationIssue(BaseModel):
    severity: str
    description: str
    location: Optional[str]

class ValidationResults(BaseModel):
    passed: bool
    issues: List[ValidationIssue]
    metrics: dict
