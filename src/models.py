from typing import List, Dict

from pydantic import BaseModel


# ---- RAMSIS-like schema (matches data/ramsis_documentsExamples.json structure at the item level) ----
class ESRSResult(BaseModel):
    code: str               # e.g., "ESRS E2", "ESRS E3", "ESRS E4", "ESRS E5"
    topic: str              # high-level topic (e.g., "Pollution", "Water and marine resources")
    subtopic: str           # mid-level grouping (e.g., "Air pollution", "Water")
    subsubtopic: str        # specific subject (e.g., "NOx / SOx emissions")
    found: bool             # whether evidence exists in the document
    examples: List[str]     # 0–2 concise verbatim quotes (≤ 280 chars each)


class ESRSResponse(BaseModel):
    items: List[ESRSResult]
