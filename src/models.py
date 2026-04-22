from typing import List

from pydantic import BaseModel


# ---- Schema ----
class ESRSResult(BaseModel):
    code: str
    status: str  # YES / NO / PARTIAL
    justification: str
    evidence: List[str]
    confidence: float


class ESRSResponse(BaseModel):
    results: List[ESRSResult]
