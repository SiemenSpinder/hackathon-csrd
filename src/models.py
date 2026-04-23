from pydantic import BaseModel, Field
from typing import List, Optional, Literal


# =========================
# METRICS (EXTRACT ONLY)
# =========================

class MetricValue(BaseModel):
    name: str = Field(..., description="Metric name as stated or inferred from text")
    value: float
    unit: str
    year: Optional[int] = None


# =========================
# EVIDENCE (VERBATIM ONLY)
# =========================

class Evidence(BaseModel):
    quote: str = Field(..., description="Exact text span from the annual report")


# =========================
# DISCLOSURE EXTRACTION
# =========================

ESRSCode = Literal[
    "E2-1", "E2-2", "E2-3", "E2-4", "E2-5", "E2-6",
    "E3-1", "E3-2", "E3-3", "E3-4", "E3-5",
    "E4-1", "E4-2", "E4-3", "E4-4", "E4-5", "E4-6",
    "E5-1", "E5-2", "E5-3", "E5-4", "E5-5", "E5-6"
]


class DisclosureExtraction(BaseModel):
    code: ESRSCode = Field(..., description="Must be one of the ESRS disclosure codes")

    is_present: bool
    confidence: float = Field(..., ge=0, le=1)

    evidence: List[Evidence] = Field(default_factory=list)

    metrics: List[MetricValue] = Field(default_factory=list)


# =========================
# STANDARD GROUPING (NO METADATA)
# =========================

class ESRSExtractionResult(BaseModel):
    disclosures: List[DisclosureExtraction]