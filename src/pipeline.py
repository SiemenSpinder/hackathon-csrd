from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

from openai import AzureOpenAI

from src.config import Config, load_config
from src.esrs_ontology import enrich_with_ontology
from src.models import CombinedExtractionResult, ESRSExtractionResult, NTPScoringResult
from src.prompts import esrs_prompt, ntp_prompt
from src.utils.merge import merge_extractions, merge_ntp_scores
from src.utils.text import approx_tokens, chunk_markdown, clean_markdown

# Max simultaneous chunk requests; tune down if Azure rate-limits you.
_MAX_CHUNK_WORKERS = 5


def _read_user_markdown(input_path: str) -> str:
    if not os.path.isfile(input_path):
        raise RuntimeError(f"Input markdown file not found: {input_path}")
    with open(input_path, "r", encoding="utf-8") as f:
        return f.read()


def _call_esrs(client: AzureOpenAI, cfg: Config, chunk: str) -> ESRSExtractionResult:
    response = client.beta.chat.completions.parse(
        model=cfg.model,
        messages=[
            {"role": "system", "content": esrs_prompt},
            {"role": "user", "content": chunk},
        ],
        response_format=ESRSExtractionResult,
        max_completion_tokens=cfg.max_generation_tokens,
    )
    return response.choices[0].message.parsed


def _call_ntp(client: AzureOpenAI, cfg: Config, chunk: str) -> NTPScoringResult:
    response = client.beta.chat.completions.parse(
        model=cfg.model,
        messages=[
            {"role": "system", "content": ntp_prompt},
            {"role": "user", "content": chunk},
        ],
        response_format=NTPScoringResult,
        max_completion_tokens=cfg.max_generation_tokens,
    )
    return response.choices[0].message.parsed


def _process_chunk(
    client: AzureOpenAI, cfg: Config, chunk: str, idx: int, total: int
) -> CombinedExtractionResult:
    with ThreadPoolExecutor(max_workers=2) as pool:
        esrs_future = pool.submit(_call_esrs, client, cfg, chunk)
        ntp_future = pool.submit(_call_ntp, client, cfg, chunk)
        esrs_result: ESRSExtractionResult = esrs_future.result()
        ntp_result: NTPScoringResult = ntp_future.result()

    combined = CombinedExtractionResult(
        disclosures=esrs_result.disclosures,
        ntp_scoring=ntp_result,
    )
    ntp = combined.ntp_scoring
    print(
        f"Chunk {idx}/{total} — {len(combined.disclosures)} disclosures | "
        f"NTP: foundations={ntp.foundations.score} "
        f"metrics={ntp.metrics_and_targets.score} "
        f"impl={ntp.implementation_strategy.score} "
        f"engagement={ntp.engagement_strategy.score} "
        f"governance={ntp.governance.score}"
    )
    return combined


def run_pipeline(cfg: Config) -> None:
    user_text = _read_user_markdown(cfg.input_path)
    user_text = clean_markdown(user_text)

    approx_total = approx_tokens(user_text)

    if approx_total > cfg.max_total_tokens:
        chunks = chunk_markdown(user_text, cfg.chunk_tokens, cfg.chunk_overlap_tokens)
        print(
            f"Input is ~{approx_total} tokens (> {cfg.max_total_tokens}). "
            f"Splitting into {len(chunks)} chunks of ~{cfg.chunk_tokens} tokens with {cfg.chunk_overlap_tokens} overlap."
        )
    else:
        if approx_total > cfg.chunk_tokens:
            chunks = chunk_markdown(user_text, cfg.chunk_tokens, cfg.chunk_overlap_tokens)
            print(
                f"Input is ~{approx_total} tokens. "
                f"Splitting into {len(chunks)} chunks of ~{cfg.chunk_tokens} tokens with {cfg.chunk_overlap_tokens} overlap."
            )
        else:
            chunks = [user_text]
            print(f"Input is ~{approx_total} tokens. Sending as a single request.")

    client = AzureOpenAI(
        api_key=cfg.azure_api_key,
        azure_endpoint=cfg.azure_endpoint,
        api_version=cfg.azure_api_version,
        timeout=cfg.timeout_ms / 1000,
    )

    extractions: List[CombinedExtractionResult] = []
    n_chunks = len(chunks)

    with ThreadPoolExecutor(max_workers=min(n_chunks, _MAX_CHUNK_WORKERS)) as pool:
        futures = {
            pool.submit(_process_chunk, client, cfg, chunk, idx, n_chunks): idx
            for idx, chunk in enumerate(chunks, start=1)
        }
        for future in as_completed(futures):
            try:
                extractions.append(future.result())
            except Exception as e:
                print(f"Chunk {futures[future]}/{n_chunks} failed: {e}")

    if not extractions:
        disclosures_merged = []
        ntp_merged = None
    else:
        disclosures_merged = merge_extractions(extractions)
        ntp_merged = merge_ntp_scores(extractions)

    enriched = enrich_with_ontology(disclosures_merged, ntp_merged)

    stem = os.path.splitext(os.path.basename(cfg.input_path))[0]
    output_key = f"{stem}.json"
    payload = {output_key: enriched}

    os.makedirs(os.path.dirname(cfg.output_path), exist_ok=True)
    with open(cfg.output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"Wrote output to {cfg.output_path}")
    n_disc = len(enriched.get("disclosures", []))
    total = enriched.get("ntp_scoring", {}).get("total_score", "n/a")
    print(f"Key: {output_key} | Disclosures: {n_disc} | NTP total score: {total}/100")


def main() -> None:
    cfg = load_config()
    run_pipeline(cfg)
