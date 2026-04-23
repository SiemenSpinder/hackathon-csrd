from __future__ import annotations

import re
from typing import List

__all__ = [
    "clean_markdown",
    "approx_tokens",
    "chunk_markdown",
]


def clean_markdown(md: str) -> str:
    """
    Clean and normalize a markdown string for LLM consumption.
    - Remove fenced code blocks
    - Normalize double quotes to single quotes
    - Collapse excessive blank lines
    """
    # remove fenced code blocks (non-greedy across lines)
    md = re.sub(r"```.*?```", "", md, flags=re.DOTALL)

    # normalize quotes
    md = md.replace('"', "'")

    # collapse excessive whitespace
    md = re.sub(r"\n{3,}", "\n\n", md)

    return md


# ---- Token/Chunking utilities ----
# Rough token approximation: ~4 characters per token to avoid tokenizer deps.

def approx_tokens(text: str) -> int:
    """Approximate token count using ~4 chars per token."""
    return max(1, len(text) // 4)


def chunk_markdown(md: str, chunk_tokens: int, overlap_tokens: int) -> List[str]:
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
