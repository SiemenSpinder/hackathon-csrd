from __future__ import annotations

from typing import Dict, List, Tuple

from src.models import ESRSExtractionResult, DisclosureExtraction, Evidence, MetricValue

__all__ = ["merge_extractions"]


def merge_extractions(extractions: List[ESRSExtractionResult]) -> ESRSExtractionResult:
    """
    Merge multiple chunk-level ESRSExtractionResult objects into a single result.
    Deduplicate by disclosure code (e.g., E2-1..E5-6).
    - is_present: OR over chunks
    - confidence: max over chunks
    - evidence: union preserving order, unique by quote, capped to 3
    - metrics: union preserving order, unique by (name, value, unit, year), capped to 20
    """

    def _dedup_evidence(evs: List[Evidence]) -> List[Evidence]:
        seen: set[str] = set()
        out: List[Evidence] = []
        for e in evs:
            quote_key = (e.quote or "").strip()
            if quote_key in seen or not quote_key:
                continue
            seen.add(quote_key)
            out.append(e)
            if len(out) >= 3:
                break
        return out

    def _dedup_metrics(ms: List[MetricValue]) -> List[MetricValue]:
        seen: set[Tuple[str | None, str | None, str | None, int | None]] = set()
        out: List[MetricValue] = []
        for m in ms:
            key = (m.name, m.value, m.unit, m.year)
            if key in seen:
                continue
            seen.add(key)
            out.append(m)
            if len(out) >= 20:
                break
        return out

    acc: Dict[str, DisclosureExtraction] = {}

    for r in extractions:
        for d in (r.disclosures or []):
            code = d.code
            if code not in acc:
                acc[code] = DisclosureExtraction(
                    code=d.code,
                    is_present=d.is_present,
                    confidence=d.confidence,
                    evidence=_dedup_evidence(list(d.evidence)),
                    metrics=_dedup_metrics(list(d.metrics)),
                )
            else:
                existing = acc[code]
                existing.is_present = existing.is_present or d.is_present
                existing.confidence = max(existing.confidence, d.confidence)
                existing.evidence = _dedup_evidence(list(existing.evidence) + list(d.evidence))
                existing.metrics = _dedup_metrics(list(existing.metrics) + list(d.metrics))

    merged_list = [acc[k] for k in sorted(acc.keys())]
    return ESRSExtractionResult(disclosures=merged_list)
