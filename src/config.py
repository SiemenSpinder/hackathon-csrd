from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    api_key: str
    model: str
    max_total_tokens: int
    chunk_tokens: int
    chunk_overlap_tokens: int
    max_generation_tokens: int

    root_dir: str
    data_dir: str
    input_path: str
    output_path: str


def _maybe_load_dotenv() -> None:
    try:
        from dotenv import load_dotenv  # type: ignore

        load_dotenv()
    except Exception:
        # .env loading is optional; ignore if unavailable
        pass


def _resolve_paths() -> tuple[str, str]:
    """
    Returns (root_dir, data_dir). root_dir is project root (parent of src).
    """
    src_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(src_dir, os.pardir))
    data_dir = os.path.join(root_dir, "data")
    return root_dir, data_dir


def _resolve_input_path(data_dir: str) -> str:
    # Prefer DATA_FOLDER if provided; attempt a specific filename first for backward-compat
    data_folder_env = os.getenv("DATA_FOLDER")
    if data_folder_env:
        # historical file name used earlier
        candidate = os.path.join(data_folder_env, "rick_output_Airbus_2024.md")
        if os.path.isfile(candidate):
            return candidate
        # fallback to a conventional default
        alt = os.path.join(data_folder_env, "input.md")
        return alt if os.path.isfile(alt) else candidate

    # Default: repo data/input.md
    return os.path.join(data_dir, "input.md")


def load_config() -> Config:
    _maybe_load_dotenv()

    # API key
    api_key = os.getenv("MISTRAL_API_KEY") or os.getenv("API_KEY")
    if not api_key:
        raise RuntimeError(
            "Missing API key: set MISTRAL_API_KEY or API_KEY in a .env file or environment variables."
        )

    # model and token-related limits
    model = os.getenv("MODEL", "mistral-small-latest")
    max_total_tokens = int(os.getenv("MAX_TOTAL_TOKENS", "100000"))
    chunk_tokens = int(os.getenv("CHUNK_TOKENS", "100000"))
    chunk_overlap_tokens = int(os.getenv("CHUNK_OVERLAP_TOKENS", "200"))
    max_generation_tokens = int(os.getenv("MAX_GENERATION_TOKENS", "20000"))

    root_dir, data_dir = _resolve_paths()
    input_path = _resolve_input_path(data_dir)
    output_path = os.path.join(data_dir, "output.json")

    return Config(
        api_key=api_key,
        model=model,
        max_total_tokens=max_total_tokens,
        chunk_tokens=chunk_tokens,
        chunk_overlap_tokens=chunk_overlap_tokens,
        max_generation_tokens=max_generation_tokens,
        root_dir=root_dir,
        data_dir=data_dir,
        input_path=input_path,
        output_path=output_path,
    )
