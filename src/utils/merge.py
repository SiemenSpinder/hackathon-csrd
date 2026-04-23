from __future__ import annotations

from typing import Dict, List, Tuple

from src.models import (
    CombinedExtractionResult,
    DisclosureExtraction,
    Evidence,
    MetricValue,
    NTPDimensionScore,
    NTPScoringResult,
)

__all__ = ["merge_extractions", "merge_ntp_scores"]


def merge_extractions(extractions: List[CombinedExtractionResult]) -> List[DisclosureExtraction]:
    """
    Merge chunk-level disclosure extractions into a single deduplicated list.
    - is_present: OR over chunks
    - confidence: max over chunks
    - evidence: union, unique by quote, capped to 3
    - metrics: union, unique by (name, value, unit, year), capped to 20
    """

    def _dedup_evidence(evs: List[Evidence]) -> List[Evidence]:
        seen: set[str] = set()
        out: List[Evidence] = []
        for e in evs:
            key = (e.quote or "").strip()
            if key in seen or not key:
                continue
            seen.add(key)
            out.append(e)
            if len(out) >= 3:
                break
        return out

    def _dedup_metrics(ms: List[MetricValue]) -> List[MetricValue]:
        seen: set[Tuple] = set()
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

    return [acc[k] for k in sorted(acc.keys())]


def merge_ntp_scores(extractions: List[CombinedExtractionResult]) -> NTPScoringResult:
    """
    Merge chunk-level NTP scores into a single result.
    For each dimension, keep the chunk with the highest score (most evidence found).
    Evidence for the winning chunk is preserved; rationale from winning chunk is used.
    """
    dimensions = ("foundations", "metrics_and_targets", "implementation_strategy", "engagement_strategy", "governance")

    best: Dict[str, NTPDimensionScore] = {}

    for r in extractions:
        scoring = r.ntp_scoring
        for dim in dimensions:
            candidate: NTPDimensionScore = getattr(scoring, dim)
            if dim not in best or candidate.score > best[dim].score:
                best[dim] = candidate

    return NTPScoringResult(
        foundations=best.get("foundations", NTPDimensionScore(score=0, rationale="No data", evidence=[])),
        metrics_and_targets=best.get("metrics_and_targets", NTPDimensionScore(score=0, rationale="No data", evidence=[])),
        implementation_strategy=best.get("implementation_strategy", NTPDimensionScore(score=0, rationale="No data", evidence=[])),
        engagement_strategy=best.get("engagement_strategy", NTPDimensionScore(score=0, rationale="No data", evidence=[])),
        governance=best.get("governance", NTPDimensionScore(score=0, rationale="No data", evidence=[])),
    )
