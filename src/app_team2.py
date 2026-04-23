import json
import html
import streamlit as st
from pathlib import Path
from collections import defaultdict

st.set_page_config(
    page_title="ESRS Document Review",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Load data ──────────────────────────────────────────────────────────────────
DATA_FILE = Path(__file__).parent / "siemen_output.json"

@st.cache_data
def load_documents(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

try:
    DOCUMENTS = load_documents(DATA_FILE)
except FileNotFoundError:
    st.error(f"Data file not found: `{DATA_FILE.name}`. Place `siemen_output.json` in the same folder as `app_3.py`.")
    st.stop()
except json.JSONDecodeError as e:
    st.error(f"Could not parse `siemen_output.json`: {e}")
    st.stop()

# ── Helpers ────────────────────────────────────────────────────────────────────
def group_by_standard(criteria):
    groups = defaultdict(list)
    for c in criteria:
        standard = c.get("standard", "Unknown")
        groups[standard].append(c)
    return dict(sorted(groups.items()))

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }

section[data-testid="stSidebar"] {
    background-color: #0f1117;
    border-right: 1px solid #2a2d3a;
}
section[data-testid="stSidebar"] * { color: #e0e0e0 !important; }

.main .block-container { padding-top: 2rem; max-width: 1100px; }

.page-header { border-bottom: 2px solid #1a1a2e; padding-bottom: 1rem; margin-bottom: 2rem; }
.page-header h1 { font-family: 'IBM Plex Mono', monospace; font-size: 1.6rem; font-weight: 600; color: #1a1a2e; letter-spacing: -0.02em; margin: 0; }
.page-header p { color: #666; font-size: 0.85rem; margin: 0.3rem 0 0 0; }

.stats-bar { display: flex; gap: 1.5rem; margin-bottom: 2rem; flex-wrap: wrap; }
.stat-card { background: #f8f9fc; border: 1px solid #e8eaf0; border-radius: 8px; padding: 0.8rem 1.2rem; min-width: 120px; flex: 1; }
.stat-card .stat-value { font-family: 'IBM Plex Mono', monospace; font-size: 1.8rem; font-weight: 600; color: #1a1a2e; line-height: 1; }
.stat-card .stat-label { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.08em; color: #888; margin-top: 0.25rem; }
.stat-card.found .stat-value { color: #1a7a4a; }
.stat-card.notfound .stat-value { color: #c0392b; }

.topic-group { margin-bottom: 1.5rem; border: 1px solid #e8eaf0; border-radius: 10px; overflow: hidden; }
.topic-header { background: #1a1a2e; padding: 0.65rem 1rem; display: flex; align-items: center; gap: 0.75rem; }
.topic-code { font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; background: rgba(255,255,255,0.15); padding: 0.15rem 0.5rem; border-radius: 4px; letter-spacing: 0.05em; color: white; }
.topic-name { font-weight: 500; font-size: 0.9rem; flex: 1; color: white; }
.topic-badge { font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; padding: 0.2rem 0.6rem; border-radius: 20px; background: rgba(255,255,255,0.1); color: white; }

.criterion-row { padding: 0.75rem 1rem; border-bottom: 1px solid #f0f1f5; display: flex; align-items: flex-start; gap: 1rem; background: white; }
.criterion-row:last-child { border-bottom: none; }

.found-pill { font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem; font-weight: 600; padding: 0.2rem 0.55rem; border-radius: 20px; white-space: nowrap; margin-top: 0.15rem; }
.found-pill.yes { background: #e6f4ee; color: #1a7a4a; border: 1px solid #b7dfc9; }
.found-pill.no  { background: #fdecea; color: #c0392b; border: 1px solid #f5c0bb; }

.example-box { background: #f5f6fa; border-left: 3px solid #5a6ef0; border-radius: 0 6px 6px 0; padding: 0.6rem 0.9rem; margin: 0.3rem 1rem 0.5rem 1rem; font-size: 0.78rem; color: #333; line-height: 1.6; font-style: italic; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📋 ESRS Review")
    st.markdown("---")
    st.markdown("**DOCUMENT**")
    selected_doc = st.selectbox(
        "document",
        list(DOCUMENTS.keys()),
        format_func=lambda x: x.replace(".json", ""),
        label_visibility="collapsed",
    )
    st.markdown("---")

    # Get criteria for selected document
    criteria_all = DOCUMENTS[selected_doc].get("disclosures", [])
    all_standards = sorted(set(c.get("standard", "Unknown") for c in criteria_all))
    all_codes = sorted(set(c.get("code", "") for c in criteria_all))

    st.markdown("**FILTERS**")
    filter_standard = st.multiselect(
        "Standard",
        all_standards,
        placeholder="All standards",
        label_visibility="collapsed",
    )
    filter_code = st.multiselect(
        "Code",
        all_codes,
        placeholder="All codes",
        label_visibility="collapsed",
    )
    filter_found = st.selectbox("Status", ["All", "Found", "Not found"])
    search = st.text_input("Search", placeholder="keyword…")

# ── Apply filters ──────────────────────────────────────────────────────────────
criteria = criteria_all
if filter_standard:
    criteria = [c for c in criteria if c.get("standard") in filter_standard]
if filter_code:
    criteria = [c for c in criteria if c.get("code") in filter_code]
if filter_found == "Found":
    criteria = [c for c in criteria if c["is_present"]]
elif filter_found == "Not found":
    criteria = [c for c in criteria if not c["is_present"]]
if search:
    q = search.lower()
    criteria = [
        c for c in criteria
        if q in c.get("title", "").lower() or q in c.get("description", "").lower()
        or q in c.get("code", "").lower() or q in c.get("standard", "").lower()
    ]

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="page-header">
  <h1>ESRS Criteria Review</h1>
  <p>{selected_doc.replace('.json', '')}</p>
</div>
""", unsafe_allow_html=True)

# Stats (always based on full unfiltered list)
total   = len(criteria_all)
n_found = sum(1 for c in criteria_all if c["is_present"])
n_not   = total - n_found
pct     = round(100 * n_found / total) if total else 0

st.markdown(f"""
<div class="stats-bar">
  <div class="stat-card"><div class="stat-value">{total}</div><div class="stat-label">Total criteria</div></div>
  <div class="stat-card found"><div class="stat-value">{n_found}</div><div class="stat-label">Found</div></div>
  <div class="stat-card notfound"><div class="stat-value">{n_not}</div><div class="stat-label">Not found</div></div>
  <div class="stat-card"><div class="stat-value">{pct}%</div><div class="stat-label">Coverage</div></div>
</div>
""", unsafe_allow_html=True)

if not criteria:
    st.info("No criteria match the current filters.")
    st.stop()

# ── Scorecard display grouped by standard ──────────────────────────────────────────
groups = group_by_standard(criteria)

for standard, items in groups.items():
    g_found = sum(1 for i in items if i["is_present"])
    g_total = len(items)

    with st.expander(f"**{standard}** ({g_found}/{g_total} present)", expanded=False):

        for item in items:
            is_present = item["is_present"]
            evidence = item.get("evidence", [])
            metrics = item.get("metrics", [])

            found_color = "#1a7a4a" if is_present else "#c0392b"
            found_label = "✓ FOUND" if is_present else "✗ NOT FOUND"
            code_escaped = html.escape(str(item.get("code", "")))
            title_escaped = html.escape(str(item.get("title", "")))
            description_escaped = html.escape(str(item.get("description", "")))

            html_content = f"""<div style="border: 1px solid #e8eaf0; border-radius: 8px; padding: 1rem; background: white; margin-bottom: 1.5rem;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem;">
                    <div>
                        <div style="font-family: 'IBM Plex Mono', monospace; font-size: 0.85rem; font-weight: 600; color: #666; margin-bottom: 0.25rem;">
                            {code_escaped}
                        </div>
                        <div style="font-size: 1rem; font-weight: 600; color: #1a1a2e; margin-bottom: 0.3rem;">
                            {title_escaped}
                        </div>
                    </div>
                    <span style="color: {found_color}; font-weight: 600; font-size: 0.75rem; font-family: 'IBM Plex Mono', monospace; background: {'#e6f4ee' if is_present else '#fdecea'}; padding: 0.25rem 0.5rem; border-radius: 4px; border: 1px solid {'#b7dfc9' if is_present else '#f5c0bb'};">
                        {found_label}
                    </span>
                </div>
                <div style="font-size: 0.9rem; color: #555; line-height: 1.5;">
                    {description_escaped}
                </div>
            </div>"""

            st.markdown(html_content, unsafe_allow_html=True)

            if evidence:
                evidence_html = f"""<details style="margin-bottom: 1rem; cursor: pointer;">
                    <summary style="background: #f5f6fa; padding: 0.6rem 1rem; border-radius: 6px; font-size: 0.9rem; font-weight: 500; color: #1a1a2e; user-select: none;">
                        📄 {len(evidence)} evidence{'s' if len(evidence) > 1 else ''}
                    </summary>
                    <div style="margin-top: 1rem;">"""

                for ev in evidence:
                    quote_escaped = html.escape(ev.get("quote", ""))
                    evidence_html += f"""
                        <div style="background: #f8f9fc; border-left: 3px solid #5a6ef0; border-radius: 0 6px 6px 0; padding: 0.8rem; margin-bottom: 0.75rem;">
                            <div style="font-size: 0.85rem; color: #1a1a2e; line-height: 1.6; font-style: italic;">
                                "{quote_escaped}"
                            </div>
                        </div>"""

                evidence_html += """
                    </div>
                </details>"""
                st.markdown(evidence_html, unsafe_allow_html=True)

            if metrics:
                metrics_html = f"""<details style="margin-bottom: 1.5rem; cursor: pointer;">
                    <summary style="background: #f5f6fa; padding: 0.6rem 1rem; border-radius: 6px; font-size: 0.9rem; font-weight: 500; color: #1a1a2e; user-select: none;">
                        📊 {len(metrics)} metric{'s' if len(metrics) > 1 else ''}
                    </summary>
                    <div style="margin-top: 1rem;">"""

                for metric in metrics:
                    name_escaped = html.escape(metric.get("name", ""))
                    unit_escaped = html.escape(metric.get("unit", ""))
                    year = metric.get("year", "")

                    metrics_html += f"""
                        <div style="background: #f8f9fc; border-left: 3px solid #9b59b6; border-radius: 0 6px 6px 0; padding: 0.8rem; margin-bottom: 0.75rem;">
                            <div style="font-size: 0.85rem; color: #1a1a2e; font-weight: 500; margin-bottom: 0.3rem;">
                                {name_escaped}
                            </div>
                            <div style="font-size: 0.9rem; color: #333; font-weight: 600; margin-bottom: 0.2rem;">
                                {f"{metric.get('value', 0):,.0f}" if isinstance(metric.get("value"), (int, float)) else metric.get("value", "N/A")} {unit_escaped}
                            </div>
                            <div style="font-size: 0.75rem; color: #888; font-family: 'IBM Plex Mono', monospace;">
                                Year: {year}
                            </div>
                        </div>"""

                metrics_html += """
                    </div>
                </details>"""
                st.markdown(metrics_html, unsafe_allow_html=True)

        st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)
