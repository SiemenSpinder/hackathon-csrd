from typing import List, Dict

from pydantic import BaseModel

class Example(BaseModel):
    sentence: str
    category: str # Type from metric, target, policy, risk, value chain scope

# ---- RAMSIS-like schema (matches data/ramsis_documentsExamples.json structure at the item level) ----
class ESRSResult(BaseModel):
    code: str  # e.g., "ESRS E2", "ESRS E3", "ESRS E4", "ESRS E5"
    topic: str  # high-level topic (e.g., "Pollution", "Water and marine resources")
    subcode: str # e.g. "ESRS E2-1", "E2-2", etc.
    subtopic: str  # mid-level grouping (e.g., "Air pollution", "Water")
    found: bool  # whether evidence exists in the document
    examples: List[Example]  # concise verbatim quotes (≤ 280 chars each)


class ESRSResponse(BaseModel):
    items: List[ESRSResult]
