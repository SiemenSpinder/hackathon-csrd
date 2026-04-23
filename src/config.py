from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    azure_api_key: str
    azure_endpoint: str
    azure_api_version: str
    model: str
    max_total_tokens: int
    chunk_tokens: int
    chunk_overlap_tokens: int
    max_generation_tokens: int
    timeout_ms: int

    root_dir: str
    data_dir: str
    input_path: str
    output_path: str


def _maybe_load_dotenv() -> None:
    try:
        from dotenv import load_dotenv  # type: ignore
        load_dotenv()
    except Exception:
        pass


def _resolve_paths() -> tuple[str, str]:
    src_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(src_dir, os.pardir))
    data_dir = os.path.join(root_dir, "data")
    return root_dir, data_dir


def _resolve_input_path(data_dir: str) -> str:
    data_folder_env = os.getenv("DATA_FOLDER")
    if data_folder_env:
        candidate = os.path.join(data_folder_env, "rick_output_Airbus_2024.md")
        if os.path.isfile(candidate):
            return candidate
        alt = os.path.join(data_folder_env, "input.md")
        return alt if os.path.isfile(alt) else candidate
    return os.path.join(data_dir, "input.md")


def load_config() -> Config:
    _maybe_load_dotenv()

    azure_api_key = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("API_KEY")
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

    if not azure_api_key:
        raise RuntimeError(
            "Missing API key: set AZURE_OPENAI_API_KEY in a .env file or environment variables."
        )
    if not azure_endpoint:
        raise RuntimeError(
            "Missing endpoint: set AZURE_OPENAI_ENDPOINT in a .env file or environment variables."
        )

    model = os.getenv("MODEL", "gpt-5-mini")
    max_total_tokens = int(os.getenv("MAX_TOTAL_TOKENS", "100000"))
    chunk_tokens = int(os.getenv("CHUNK_TOKENS", "100000"))
    chunk_overlap_tokens = int(os.getenv("CHUNK_OVERLAP_TOKENS", "200"))
    max_generation_tokens = int(os.getenv("MAX_GENERATION_TOKENS", "20000"))
    timeout_ms = int(os.getenv("TIMEOUT_MS", "600000"))

    root_dir, data_dir = _resolve_paths()
    input_path = _resolve_input_path(data_dir)
    output_path = os.path.join(data_dir, "output.json")

    return Config(
        azure_api_key=azure_api_key,
        azure_endpoint=azure_endpoint,
        azure_api_version=azure_api_version,
        model=model,
        max_total_tokens=max_total_tokens,
        chunk_tokens=chunk_tokens,
        chunk_overlap_tokens=chunk_overlap_tokens,
        max_generation_tokens=max_generation_tokens,
        timeout_ms=timeout_ms,
        root_dir=root_dir,
        data_dir=data_dir,
        input_path=input_path,
        output_path=output_path,
    )
