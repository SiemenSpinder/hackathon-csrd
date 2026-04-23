# CSRD Sustainability Reporting Analyzer

A pipeline that analyzes corporate annual reports against EU sustainability standards, determining whether companies have reported adequately on their nature-related impacts.

## Example dashboard

[CSRD Dashboard](https://siemenspinder.github.io/hackathon-csrd-dashboard/)

## Problem Statement

Given a company's annual report, answer three questions:

1. What should be reported? — Which ESRS sub-topics are material for this company?
2. Is it reported? — Are those topics actually disclosed in the annual report?
3. Is it reported sufficiently? — Does the disclosure include concrete metrics, targets, and evidence?

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

Maturity levels: 0 = Non-aligned, 1 = Compliant, 2 = Coherent, 3 = Credible

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
  Streamlit dashboard (interactive) or static HTML generator
```

Core pipeline entry points:
- [main()](src/pipeline.py:146) orchestrates configuration and execution.
- [run_pipeline()](src/pipeline.py:79) performs chunking, parallel calls, merging, enrichment, and writing output.
- Azure structured outputs via client.beta.chat.completions.parse using Pydantic schemas from [ESRSExtractionResult](src/models.py:95), [NTPScoringResult](src/models.py:83), and [CombinedExtractionResult](src/models.py:103).
- Ontology enrichment and NTP score aggregation occur in [enrich_with_ontology()](src/esrs_ontology.py:270).

## Setup

Prerequisites:
- Python 3.8+
- Access to an Azure OpenAI deployment (model name must match your Azure deployment name)

Install dependencies from [requirements.txt](requirements.txt:1):

```bash
pip install -r requirements.txt
```

Create a .env file in the project root:

```env
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-12-01-preview
MODEL=gpt-5-mini
DATA_FOLDER=data
```

Notes:
- API key fallback: [load_config()](src/config.py:51) also accepts API_KEY if AZURE_OPENAI_API_KEY is unset.
- MODEL default is gpt-5-mini as per [Config](src/config.py:7); ensure it matches your Azure model deployment name.
- If DATA_FOLDER is set, input resolution in [_resolve_input_path()](src/config.py:40) prefers a file named rick_output_Airbus_2024.md in that folder, otherwise input.md.

## Usage

### 1) Run the pipeline

Place the annual report as Markdown at [data/input.md](data/input.md) (or set DATA_FOLDER as noted above), then execute:

```bash
python main.py
```

What happens:
- The app reads your input via [load_config()](src/config.py:51) and [_read_user_markdown()](src/pipeline.py:21).
- It estimates token length and splits if needed via [approx_tokens()](src/utils/text.py:1) and [chunk_markdown()](src/utils/text.py:1).
- For each chunk, it makes two parallel calls: [
  _call_esrs()](src/pipeline.py:28) and [_call_ntp()](src/pipeline.py:41).
- Chunk results are merged with [merge_extractions()](src/utils/merge.py:17) and [merge_ntp_scores()](src/utils/merge.py:75).
- Disclosures are enriched and NTP total score computed by [enrich_with_ontology()](src/esrs_ontology.py:270).
- Output is written to [data/output.json](data/output.json).

### 2) Launch the interactive Streamlit dashboard (optional)

The Streamlit app expects a JSON file at [examples/output.json](examples/output.json:1) by default. After running the pipeline, copy your output:

```bash
cp data/output.json examples/output.json
```

Start the app:

```bash
streamlit run src/streamlit_app.py
```

Data source: the default path is controlled by the [DATA_FILE](src/streamlit_app.py:15) constant.

### 3) Generate a static HTML dashboard (optional)

You can also produce a self-contained HTML report using [generate_dashboard.py](src/generate_dashboard.py:153) and the provided template [template.html](html/template.html:1):

```bash
python src/generate_dashboard.py data/output.json -t html/template.html -o html/index.html
```

This writes a portable HTML dashboard that you can open locally or publish (e.g., GitHub Pages).

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

The ontology layer fills in titles, descriptions, and standard codes based on ESRS definitions via [ESRS_DISCLOSURES](src/esrs_ontology.py:233).

## Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| AZURE_OPENAI_API_KEY | — | Required (or API_KEY) |
| AZURE_OPENAI_ENDPOINT | — | Required |
| AZURE_OPENAI_API_VERSION | 2024-12-01-preview | API version (required for structured outputs) |
| MODEL | gpt-5-mini | Azure deployment name used by the client |
| MAX_TOTAL_TOKENS | 100000 | Process whole doc below this; chunk above |
| CHUNK_TOKENS | 100000 | Target chunk size in tokens |
| CHUNK_OVERLAP_TOKENS | 200 | Overlap between chunks for context |
| MAX_GENERATION_TOKENS | 20000 | Max tokens per LLM response |
| TIMEOUT_MS | 600000 | Request timeout (ms) |
| DATA_FOLDER | data | Directory for input/output discovery |

Implementation details: see [Config](src/config.py:7) and defaults in [load_config()](src/config.py:51).

## Project Structure

```
├── main.py                  # Entry point
├── requirements.txt
├── src/
│   ├── pipeline.py          # Core processing pipeline
│   ├── config.py            # Config loader (.env → settings)
│   ├── models.py            # Pydantic schemas for structured outputs
│   ├── esrs_ontology.py     # ESRS definitions & NTP weights, enrichment
│   ├── prompts.py           # System prompts for extraction and scoring
│   ├── generate_dashboard.py # Static HTML dashboard generator
│   ├── streamlit_app.py     # Streamlit dashboard (interactive)
│   └── utils/
│       ├── text.py          # Markdown cleaning and chunking
│       └── merge.py         # Merge chunk-level results
├── data/
│   ├── input.md             # Input annual report (Markdown)
│   └── output.json          # Pipeline output
├── examples/
│   └── output.json          # Example/output for Streamlit
└── html/
    ├── template.html        # HTML dashboard template
    └── index.html           # Example generated dashboard
```

## Troubleshooting

- Missing credentials: The pipeline raises clear errors if AZURE_OPENAI_API_KEY or AZURE_OPENAI_ENDPOINT are absent in [load_config()](src/config.py:51).
- Input path: When DATA_FOLDER is set, input resolution in [_resolve_input_path()](src/config.py:40) looks for rick_output_Airbus_2024.md first, then input.md. If neither exists, [
  _read_user_markdown()](src/pipeline.py:21) will fail with “Input markdown file not found”.
- Azure rate limits: Parallelism per chunk is 2, and across chunks is capped by _MAX_CHUNK_WORKERS=5 in [pipeline](src/pipeline.py:17). Reduce these if throttled.
- Streamlit data source: Copy your pipeline output to [examples/output.json](examples/output.json:1) or modify [DATA_FILE](src/streamlit_app.py:15).
