from __future__ import annotations

import json
import os
from typing import List

from mistralai.client import Mistral

from src.config import Config, load_config
from src.esrs_ontology import enrich_with_ontology
from src.models import ESRSExtractionResult
from src.prompts import system_prompt
from src.utils.merge import merge_extractions
from src.utils.text import approx_tokens, chunk_markdown, clean_markdown


def _read_user_markdown(input_path: str) -> str:
    if not os.path.isfile(input_path):
        raise RuntimeError(f"Input markdown file not found: {input_path}")
    with open(input_path, "r", encoding="utf-8") as f:
        return f.read()


def run_pipeline(cfg: Config) -> None:
    # Read and clean input
    user_text = _read_user_markdown(cfg.input_path)
    user_text = clean_markdown(user_text)

    # Chunking logic
    approx_total = approx_tokens(user_text)

    if approx_total > cfg.max_total_tokens:
        chunks = chunk_markdown(user_text, cfg.chunk_tokens, cfg.chunk_overlap_tokens)
        print(
            f"Input is ~{approx_total} tokens (> {cfg.max_total_tokens}). Splitting into {len(chunks)} chunks of ~{cfg.chunk_tokens} tokens with {cfg.chunk_overlap_tokens} overlap."
        )
    else:
        if approx_total > cfg.chunk_tokens:
            chunks = chunk_markdown(user_text, cfg.chunk_tokens, cfg.chunk_overlap_tokens)
            print(
                f"Input is ~{approx_total} tokens. Splitting into {len(chunks)} chunks of ~{cfg.chunk_tokens} tokens with {cfg.chunk_overlap_tokens} overlap."
            )
        else:
            chunks = [user_text]
            print(f"Input is ~{approx_total} tokens. Sending as a single request.")

    # Mistral client
    client = Mistral(api_key=cfg.api_key)

    # Call model over chunks with structured output
    extractions: List[ESRSExtractionResult] = []
    for idx, chunk in enumerate(chunks, start=1):
        try:
            chat_response = client.chat.parse(
                model=cfg.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": chunk},
                ],
                response_format=ESRSExtractionResult,
                max_tokens=cfg.max_generation_tokens,
            )
            parsed: ESRSExtractionResult = chat_response.choices[0].message.parsed
            extractions.append(parsed)
            print(f"Chunk {idx}/{len(chunks)} processed: {len(parsed.disclosures)} disclosures")
        except Exception as e:
            print(f"Chunk {idx}/{len(chunks)} failed: {e}")

    # Merge results
    result = merge_extractions(extractions) if extractions else ESRSExtractionResult(disclosures=[])

    # Enrich and write output
    enriched = enrich_with_ontology(result.model_dump())

    stem = os.path.splitext(os.path.basename(cfg.input_path))[0]
    output_key = f"{stem}.json"
    payload = {output_key: enriched}

    os.makedirs(os.path.dirname(cfg.output_path), exist_ok=True)
    with open(cfg.output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"Wrote output to {cfg.output_path}")
    print(f"Key: {output_key} | Enriched disclosures: {len(enriched)}")


def main() -> None:
    cfg = load_config()
    run_pipeline(cfg)
