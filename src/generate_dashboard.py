#!/usr/bin/env python3
"""
generate_dashboard.py — Generate a CSRD dashboard HTML from a JSON report file.

Usage:
    python generate_dashboard.py data/output.json
    python generate_dashboard.py data/output_v4.json -o reports/airbus_2024.html
    python generate_dashboard.py data/output.json -t template.html -o my_report.html
"""

import argparse
import json
import re
import sys
from pathlib import Path


# Canonical metadata for known ESRS environmental standards.
# Unknown standards fall back to a generic entry.
STANDARD_META = {
    "E1": {"name": "Climate Change",      "emoji": "🌡️"},
    "E2": {"name": "Pollution",            "emoji": "💨"},
    "E3": {"name": "Water & Marine",       "emoji": "💧"},
    "E4": {"name": "Biodiversity",         "emoji": "🌱"},
    "E5": {"name": "Circular Economy",     "emoji": "♻️"},
}

# Human-readable labels for NTP scoring dimension keys.
NTP_DIM_LABELS = {
    "foundations":             "Foundations",
    "metrics_and_targets":     "Metrics & Targets",
    "implementation_strategy": "Implementation",
    "engagement_strategy":     "Engagement",
    "governance":              "Governance",
}


# ── helpers ──────────────────────────────────────────────────────────────────

def parse_report_key(key: str) -> tuple[str, int | None]:
    """
    Extract a human-readable company name and year from a JSON top-level key.

    Examples:
        'rick_output_Airbus_2024.json'  →  ('Airbus', 2024)
        'Shell_2023_report.json'        →  ('Shell', 2023)
        'some_company.json'             →  ('Some Company', None)
    """
    clean = re.sub(r'^(rick_output_|output_)', '', key, flags=re.IGNORECASE)
    clean = re.sub(r'\.json$', '', clean, flags=re.IGNORECASE)

    year_match = re.search(r'_?(\d{4})_?', clean)
    year = int(year_match.group(1)) if year_match else None

    if year_match:
        without_year = clean[:year_match.start()] + clean[year_match.end():]
    else:
        without_year = clean

    company = without_year.strip('_').replace('_', ' ').title()
    return company or "Company", year


def sanitize(obj):
    """Recursively strip ASCII control characters from string values."""
    if isinstance(obj, str):
        return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', obj)
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize(i) for i in obj]
    return obj


def load_report(path: Path) -> tuple[str, dict]:
    """Load the JSON file and return (top_level_key, report_data)."""
    raw = json.loads(path.read_text(encoding='utf-8'))
    if not raw:
        raise ValueError(f"{path} is empty or not a valid report file")
    key = next(iter(raw))
    return key, sanitize(raw[key])


def build_ntp_dims(ntp_scoring: dict) -> list[dict]:
    """Convert the flat ntp_scoring dict into an ordered list suitable for the template."""
    dims = []
    for key, label in NTP_DIM_LABELS.items():
        dim = ntp_scoring.get(key)
        if not dim or not isinstance(dim, dict):
            continue
        dims.append({
            "key":                  key,
            "label":                label,
            "score":                dim.get("score", 0),
            "maturity":             dim.get("maturity", ""),
            "weight":               dim.get("weight", 0),
            "weighted_contribution": dim.get("weighted_contribution", 0),
            "rationale":            dim.get("rationale", ""),
        })
    return dims


def build_standard_meta(disclosures: list[dict]) -> dict:
    """Return metadata only for standards that actually appear in the disclosures."""
    codes = sorted({d.get("standard", "") for d in disclosures} - {""})
    return {
        code: STANDARD_META.get(code, {"name": code, "emoji": "📄"})
        for code in codes
    }


def to_js(value) -> str:
    """Serialise a Python value to a JavaScript literal (JSON is valid JS)."""
    return json.dumps(value, ensure_ascii=False)


# ── core ─────────────────────────────────────────────────────────────────────

def build_template_vars(report_key: str, report: dict) -> dict[str, str]:
    """
    Produce a flat dict of {PLACEHOLDER: replacement_string} for the template.
    All replacements are plain strings (numbers are stringified, objects serialised).
    """
    company, year = parse_report_key(report_key)

    disclosures  = report.get("disclosures", [])
    ntp_scoring  = report.get("ntp_scoring", {})
    total_score  = ntp_scoring.get("total_score", 0)
    ntp_dims     = build_ntp_dims(ntp_scoring)
    standard_meta = build_standard_meta(disclosures)

    return {
        "COMPANY":           company,
        "YEAR":              str(year) if year else "null",
        "REPORT_KEY":        report_key,
        "TOTAL_SCORE":       str(total_score) if total_score else "0",
        "DISCLOSURES_JSON":  to_js(disclosures),
        "NTP_DIMS_JSON":     to_js(ntp_dims),
        "STANDARD_META_JSON": to_js(standard_meta),
    }


def render(template_path: Path, vars: dict[str, str]) -> str:
    """Replace every {{KEY}} placeholder in the template with its value."""
    html = template_path.read_text(encoding='utf-8')
    for key, value in vars.items():
        html = html.replace(f"{{{{{key}}}}}", value)
    return html


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a CSRD environmental dashboard from a JSON report.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("json_file",
                        help="Path to the JSON report file")
    parser.add_argument("-o", "--output",
                        help="Output HTML path (default: dashboard_<company>_<year>.html "
                             "next to the input file)")
    parser.add_argument("-t", "--template", default="template.html",
                        help="HTML template path (default: template.html)")
    args = parser.parse_args()

    json_path     = Path(args.json_file)
    template_path = Path(args.template)

    if not json_path.exists():
        sys.exit(f"Error: input file not found: {json_path}")
    if not template_path.exists():
        sys.exit(f"Error: template not found: {template_path}\n"
                 f"Make sure template.html is in the same directory as this script, "
                 f"or pass -t <path>.")

    report_key, report = load_report(json_path)
    vars = build_template_vars(report_key, report)

    if args.output:
        out_path = Path(args.output)
    else:
        company_slug = re.sub(r'[^a-z0-9]+', '_', vars["COMPANY"].lower()).strip('_')
        year_slug    = vars["YEAR"] if vars["YEAR"] != "null" else "unknown"
        out_path     = json_path.parent.parent / f"dashboard_{company_slug}_{year_slug}.html"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render(template_path, vars), encoding='utf-8')
    print(f"✓ Dashboard written to: {out_path}")


if __name__ == "__main__":
    main()
