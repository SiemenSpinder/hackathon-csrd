# CSRD Sustainability Reporting Analyzer

A pipeline that analyzes corporate annual reports against EU sustainability standards, determining whether companies have reported adequately on their nature-related impacts.

## Problem Statement

Given a company's annual report, answer three questions:

1. **What should be reported?** — Which ESRS sub-topics are material for this company?
2. **Is it reported?** — Are those topics actually disclosed in the annual report?
3. **Is it reported sufficiently?** — Does the disclosure include concrete metrics, targets, and evidence?

## Standards Covered

### ESRS E2–E5 (EU Corporate Sustainability Reporting Directive)
| Code | Topic |
|------|-------|
| E2 | Pollution (air, water, soil, hazardous substances) |
| E3 | Water and Marine Resources |
| E4 | Biodiversity and Ecosystems |
| E5 | Resource Use and Circular Economy |

22 specific disclosure requirements are checked (E2-1 through E5-6).

### WWF NAT40 — Nature Transition Plan (NTP)
Maturity scored 0–3 across five dimensions:
| Dimension | Weight |
|-----------|--------|
| Implementation Strategy | 30% |
| Foundations (materiality analysis) | 25% |
| Metrics & Targets | 20% |
| Engagement Strategy | 15% |
| Governance | 10% |

Maturity levels: `0 = Non-aligned`, `1 = Compliant`, `2 = Coherent`, `3 = Credible`

## Architecture

```
Annual report (Markdown)
        │
        ▼
  Clean & chunk text
        │
        ▼
ThreadPoolExecutor (parallel LLM calls per chunk)
    ├── ESRS extraction  →  is_present, confidence, evidence, metrics
    └── NTP scoring      →  maturity score + rationale per dimension
        │
        ▼
  Merge chunk results
  (OR presence, MAX confidence, deduplicate evidence/metrics)
        │
        ▼
  Enrich with ESRS ontology
  (add standard definitions, compute weighted NTP total score)
        │
        ▼
  data/output.json
        │
        ▼
  Streamlit dashboard (optional)
```

## Setup

**Prerequisites:** Python 3.8+, access to an Azure OpenAI deployment.

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-12-01-preview
MODEL=gpt-4o-mini
DATA_FOLDER=data
```

## Usage

### Run the pipeline

Place the annual report as a Markdown file in `data/input.md` (or set `DATA_FOLDER` to point elsewhere), then:

```bash
python main.py
```

Results are written to `data/output.json` and a summary is printed to the console.

### Launch the dashboard

```bash
streamlit run src/app_2.py
```

The dashboard lets you filter disclosures by ESRS code, presence status, or keyword, and drill into evidence quotes and extracted metrics.

## Output Format

```json
{
  "input_filename.json": {
    "disclosures": [
      {
        "code": "E2-1",
        "title": "Policies on pollution",
        "standard": "E2",
        "is_present": true,
        "confidence": 0.95,
        "evidence": [{ "quote": "verbatim excerpt..." }],
        "metrics": [
          { "name": "Regulated substances analyzed", "value": 16000, "unit": "No.", "year": 2024 }
        ]
      }
    ],
    "ntp_scoring": {
      "foundations": {
        "score": 2,
        "maturity": "Coherent",
        "weight": 25,
        "weighted_contribution": 16.7,
        "rationale": "...",
        "evidence": [{ "quote": "..." }]
      },
      "total_score": 72.3
    }
  }
}
```

## Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `AZURE_OPENAI_API_KEY` | — | Required |
| `AZURE_OPENAI_ENDPOINT` | — | Required |
| `AZURE_OPENAI_API_VERSION` | `2024-12-01-preview` | API version |
| `MODEL` | `gpt-4o-mini` | Deployment name |
| `MAX_TOTAL_TOKENS` | `100000` | Process whole doc below this; chunk above |
| `CHUNK_TOKENS` | `100000` | Target chunk size in tokens |
| `CHUNK_OVERLAP_TOKENS` | `200` | Overlap between chunks for context continuity |
| `MAX_GENERATION_TOKENS` | `20000` | Max tokens per LLM response |
| `TIMEOUT_MS` | `600000` | Request timeout (ms) |
| `DATA_FOLDER` | `data` | Directory for input/output files |

## Project Structure

```
├── main.py                  # Entry point
├── requirements.txt
├── src/
│   ├── pipeline.py          # Core processing pipeline
│   ├── config.py            # Config loader (.env → settings)
│   ├── models.py            # Pydantic schemas for LLM output
│   ├── esrs_ontology.py     # ESRS standard definitions & NTP weights
│   ├── prompts.py           # System prompts for extraction and scoring
│   ├── app_2.py             # Streamlit dashboard
│   └── utils/
│       ├── text.py          # Markdown cleaning and chunking
│       └── merge.py         # Merge chunk-level results
├── data/
│   ├── input.md             # Input annual report (Markdown)
│   └── output.json          # Pipeline output
└── docs/
    └── presentation.pdf     # Hackathon presentation
```
