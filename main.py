import json
import os
import re
from typing import Dict, List, Tuple

from mistralai.client import Mistral

from src.models import ESRSResponse, ESRSResult
from src.prompts import system_prompt


def clean_markdown(md: str) -> str:
    # remove code blocks
    md = re.sub(r"```.*?```", "", md, flags=re.DOTALL)

    # normalize quotes
    md = md.replace('"', "'")

    # collapse excessive whitespace
    md = re.sub(r"\n{3,}", "\n\n", md)

    return md


# ---- Token/Chunking utilities ----
# Rough token approximation: ~4 characters per token
# This avoids adding a tokenizer dependency while being practical for sizing.


def _approx_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def _chunk_markdown(md: str, chunk_tokens: int, overlap_tokens: int) -> List[str]:
    """
    Split markdown into character-based chunks sized by token approximation.
    Uses simple char windows with overlap to preserve context across boundaries.
    """
    if not md:
        return []

    if chunk_tokens <= 0:
        raise ValueError("chunk_tokens must be > 0")

    # Convert token sizes to char counts (~4 chars/token)
    max_chars = max(1, chunk_tokens * 4)
    overlap_chars = max(0, overlap_tokens * 4)

    chunks: List[str] = []
    start = 0
    n = len(md)

    while start < n:
        end = min(n, start + max_chars)
        chunk = md[start:end]
        chunks.append(chunk)
        if end >= n:
            break
        # next window starts with overlap from the tail of current chunk
        start = max(0, end - overlap_chars)

    return chunks


def _merge_esrs_items(items_list: List[List[ESRSResult]]) -> List[ESRSResult]:
    """
    Merge items from multiple chunks, deduplicating by (code, subtopic, subsubtopic).
    - found: OR over chunks
    - examples: union preserving order, capped at 2 per item
    - topic: normalized to match code family mapping
    """
    code_to_topic = {
        "ESRS E2": "Pollution",
        "ESRS E3": "Water and marine resources",
        "ESRS E4": "Biodiversity and ecosystems",
        "ESRS E5": "Resource use and circular economy",
    }

    merged: Dict[Tuple[str, str, str], ESRSResult] = {}

    for items in items_list:
        for it in items:
            key = (it.code, it.subtopic, it.subsubtopic)
            if key not in merged:
                # normalize topic to guarantee consistency
                topic = code_to_topic.get(it.code, it.topic)
                merged[key] = ESRSResult(
                    code=it.code,
                    topic=topic,
                    subtopic=it.subtopic,
                    subsubtopic=it.subsubtopic,
                    found=it.found,
                    examples=list(dict.fromkeys(it.examples))[:2],
                )
            else:
                acc = merged[key]
                acc.found = acc.found or it.found
                # merge examples with order-preserving de-dup
                merged_examples = list(dict.fromkeys(acc.examples + it.examples))
                acc.examples = merged_examples[:2]
                # ensure topic consistency
                acc.topic = code_to_topic.get(acc.code, acc.topic)

    return list(merged.values())


# ---- Load environment variables from .env if available ----
try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

# Read API key from environment
api_key = os.getenv("MISTRAL_API_KEY") or os.getenv("API_KEY")
if not api_key:
    raise RuntimeError(
        "Missing API key: set MISTRAL_API_KEY or API_KEY in a .env file or environment variables."
    )

# ---- Setup client/model ----
model = os.getenv("MODEL", "mistral-small-latest")
client = Mistral(api_key=api_key)

# ---- Read user content from markdown ----
# Prefer DATA_FOLDER/input.md if DATA_FOLDER is set; otherwise fall back to repo-relative data/input.md
_data_folder = os.getenv("DATA_FOLDER")
if _data_folder:
    candidate = os.path.join(_data_folder, "rick_output_Airbus_2024.md")
    if os.path.isfile(candidate):
        input_path = candidate
    else:
        # fallback legacy name if present
        alt = os.path.join(_data_folder, "rick_output_Airbus_2024.md")
        input_path = alt if os.path.isfile(alt) else candidate
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(base_dir, "data", "input.md")

if not os.path.isfile(input_path):
    raise RuntimeError(f"Input markdown file not found: {input_path}")

with open(input_path, "r", encoding="utf-8") as f:
    user_text = f.read()

user_text = clean_markdown(user_text)

# ---- Chunking configuration ----
# If total input exceeds MAX_TOTAL_TOKENS (default 262_144), we split it and send chunks separately.
MAX_TOTAL_TOKENS = int(os.getenv("MAX_TOTAL_TOKENS", "100000"))
# Per-request input chunk target; choose conservatively for small models unless overridden
CHUNK_TOKENS = int(os.getenv("CHUNK_TOKENS", "50000"))
# Overlap between chunks to preserve context
CHUNK_OVERLAP_TOKENS = int(os.getenv("CHUNK_OVERLAP_TOKENS", "200"))

approx_total = _approx_tokens(user_text)

# Build chunks if needed (or if chunk size is explicitly set)
if approx_total > MAX_TOTAL_TOKENS:
    chunks = _chunk_markdown(user_text, CHUNK_TOKENS, CHUNK_OVERLAP_TOKENS)
    print(
        f"Input is ~{approx_total} tokens (> {MAX_TOTAL_TOKENS}). Splitting into {len(chunks)} chunks of ~{CHUNK_TOKENS} tokens with {CHUNK_OVERLAP_TOKENS} overlap."
    )
else:
    # Even if below MAX_TOTAL_TOKENS, ensure we don't exceed per-call context
    if approx_total > CHUNK_TOKENS:
        chunks = _chunk_markdown(user_text, CHUNK_TOKENS, CHUNK_OVERLAP_TOKENS)
        print(
            f"Input is ~{approx_total} tokens. Splitting into {len(chunks)} chunks of ~{CHUNK_TOKENS} tokens with {CHUNK_OVERLAP_TOKENS} overlap."
        )
    else:
        chunks = [user_text]
        print(f"Input is ~{approx_total} tokens. Sending as a single request.")

# ---- Call Mistral with structured output over chunks ----
all_items: List[List[ESRSResult]] = []
for idx, chunk in enumerate(chunks, start=1):
    try:
        chat_response = client.chat.parse(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": chunk},
            ],
            response_format=ESRSResponse,
            max_tokens=int(os.getenv("MAX_GENERATION_TOKENS", "10000")),
            temperature=float(os.getenv("TEMPERATURE", "0")),
        )
        parsed: ESRSResponse = chat_response.choices[0].message.parsed
        all_items.append(parsed.items)
        print(f"Chunk {idx}/{len(chunks)} processed: {len(parsed.items)} items")
    except Exception as e:
        print(f"Chunk {idx}/{len(chunks)} failed: {e}")

# ---- Merge results and write output ----
merged_items = _merge_esrs_items(all_items) if all_items else []
result = ESRSResponse(items=merged_items)

# Envelope: { "<stem>.json": [ {item...}, ... ] }
stem = os.path.splitext(os.path.basename(input_path))[0]
output_key = f"{stem}.json"
items = [i.model_dump() for i in result.items]
payload = {output_key: items}

# Ensure output directory exists and write file
base_dir = os.path.dirname(os.path.abspath(__file__))
out_dir = os.path.join(base_dir, "data")
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "output.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)

print(f"Wrote output to {out_path}")
print(f"Key: {output_key} | Items: {len(items)}")
