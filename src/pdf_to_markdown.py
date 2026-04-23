import logging
import os
from pathlib import Path
from typing import Optional

from google.cloud import secretmanager
from mistralai.client import Mistral

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration — adjust these before running
# ---------------------------------------------------------------------------
INPUT_DIR  = "/content/mnt/gcs/rick/input"   # folder containing .pdf files
OUTPUT_DIR = "/content/mnt/gcs/rick/output"   # folder where .md files will be saved
MODEL = "mistral-ocr-latest"

# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

DEFAULT_TIMEOUT_MS = 900_000  # 10 minutes — OCR can be slow for large PDFs


def get_client(api_key: str, timeout_ms: int = DEFAULT_TIMEOUT_MS) -> Mistral:
    """Return an authenticated Mistral client with a custom timeout."""
    return Mistral(api_key=api_key, timeout_ms=timeout_ms)


def upload_pdf(client: Mistral, pdf_path: Path) -> str:
    """Upload a PDF to Mistral and return a signed URL for OCR."""
    with open(pdf_path, "rb") as fh:
        uploaded = client.files.upload(
            file={"file_name": pdf_path.name, "content": fh},
            purpose="ocr",
        )
    signed = client.files.get_signed_url(file_id=uploaded.id)
    logger.info("Uploaded %s -> file_id=%s", pdf_path.name, uploaded.id)
    return signed.url


def run_ocr(client: Mistral, document_url: str, model: str = MODEL):
    """Run Mistral OCR on a signed document URL."""
    result = client.ocr.process(
        model=model,
        document={"type": "document_url", "document_url": document_url},
    )
    logger.info("OCR completed — %d page(s)", len(result.pages))
    return result


def extract_markdown(ocr_result) -> str:
    """Join all page markdowns with a horizontal rule separator."""
    return "\n\n---\n\n".join(page.markdown for page in ocr_result.pages)


def save_markdown(markdown: str, output_path: Path) -> Path:
    """Write markdown to output_path, creating parent dirs as needed."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")
    logger.info("Saved %s (%d chars)", output_path, len(markdown))
    return output_path


# ---------------------------------------------------------------------------
# Single-file converter
# ---------------------------------------------------------------------------

def convert_pdf_to_md(
    client: Mistral,
    pdf_path: Path,
    output_dir: Path,
    model: str = MODEL,
) -> Path:
    """End-to-end conversion of one PDF to Markdown.

    Steps: upload -> OCR -> extract markdown -> save .md file.
    Returns the path to the generated .md file.
    """
    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)

    url = upload_pdf(client, pdf_path)
    ocr_result = run_ocr(client, url, model=model)
    markdown = extract_markdown(ocr_result)

    md_filename = pdf_path.stem + ".md"
    return save_markdown(markdown, output_dir / md_filename)


# ---------------------------------------------------------------------------
# Batch pipeline — convert all PDFs in a folder
# ---------------------------------------------------------------------------

def run_pipeline(
    input_dir: str,
    output_dir: str,
    api_key: str,
    model: str = MODEL,
    glob_pattern: str = "*.pdf",
) -> dict:
    """Convert every PDF in *input_dir* to Markdown in *output_dir*.

    Parameters
    ----------
    input_dir : str
        Directory containing PDF files.
    output_dir : str
        Directory where .md files will be written.
    api_key : str
        Mistral API key.
    model : str
        OCR model name.
    glob_pattern : str
        Glob pattern to match PDF files (default ``*.pdf``).

    Returns
    -------
    dict
        Summary with keys ``converted``, ``failed``, ``skipped``.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    client = get_client(api_key)

    pdf_files = sorted(input_path.glob(glob_pattern))
    logger.info("Found %d PDF file(s) in %s", len(pdf_files), input_path)

    converted, failed, skipped = [], [], []

    for pdf in pdf_files:
        # Skip if already converted
        target_md = output_path / (pdf.stem + ".md")
        if target_md.exists():
            logger.info("Skipping %s (already exists)", target_md.name)
            skipped.append(str(pdf))
            continue

        try:
            result_path = convert_pdf_to_md(client, pdf, output_path, model=model)
            converted.append(str(result_path))
        except Exception as exc:
            logger.error("Failed to convert %s: %s", pdf.name, exc)
            failed.append({"file": str(pdf), "error": str(exc)})

    summary = {
        "converted": converted,
        "failed": failed,
        "skipped": skipped,
    }
    logger.info(
        "Pipeline complete — converted: %d, skipped: %d, failed: %d",
        len(converted), len(skipped), len(failed),
    )
    return summary


# ---------------------------------------------------------------------------
# Run the pipeline
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Fetch secrets from GCP Secret Manager
    sm_client = secretmanager.SecretManagerServiceClient()

    response = sm_client.access_secret_version(
        request={"name": "projects/207348376998/secrets/hackathon-mistral-key/versions/1"}
    )
    api_key = response.payload.data.decode("UTF-8")
    os.environ["MISTRAL_API_KEY"] = api_key

    response = sm_client.access_secret_version(
        request={"name": "projects/207348376998/secrets/hackathon-pinecone-key/versions/1"}
    )
    database_api_key = response.payload.data.decode("UTF-8")

    # Run batch conversion
    summary = run_pipeline(
        input_dir=INPUT_DIR,
        output_dir=OUTPUT_DIR,
        api_key=api_key,
        model=MODEL,
    )

    print(f"\n{'='*50}")
    print(f"Converted : {len(summary['converted'])} file(s)")
    print(f"Skipped   : {len(summary['skipped'])} file(s)")
    print(f"Failed    : {len(summary['failed'])} file(s)")
    print(f"{'='*50}")

    if summary["failed"]:
        print("\nFailed files:")
        for item in summary["failed"]:
            print(f"  - {item['file']}: {item['error']}")
