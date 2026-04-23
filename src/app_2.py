import json
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
    st.error(f"Data file not found: `{DATA_FILE.name}`. Place `siemen_output.json` in the same folder as `app.py`.")
    st.stop()
except json.JSONDecodeError as e:
    st.error(f"Could not parse `siemen_output.json`: {e}")
    st.stop()

# ── Helpers ────────────────────────────────────────────────────────────────────
def group_by_topic(criteria):
    groups = defaultdict(list)
    for c in criteria:
        groups[(c["code"], c["topic"])].append(c)
    return dict(groups)

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

    criteria_all = DOCUMENTS[selected_doc]
    all_codes = sorted(set(c["code"] for c in criteria_all))

    st.markdown("**FILTERS**")
    filter_code  = st.multiselect("ESRS code", all_codes, placeholder="All codes")
    filter_found = st.selectbox("Status", ["All", "Found", "Not found"])
    search       = st.text_input("Search", placeholder="keyword…")

# ── Apply filters ──────────────────────────────────────────────────────────────
criteria = criteria_all
if filter_code:
    criteria = [c for c in criteria if c["code"] in filter_code]
if filter_found == "Found":
    criteria = [c for c in criteria if c["found"]]
elif filter_found == "Not found":
    criteria = [c for c in criteria if not c["found"]]
if search:
    q = search.lower()
    criteria = [
        c for c in criteria
        if q in c["topic"].lower() or q in c["subtopic"].lower()
        or q in c["code"].lower()
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
n_found = sum(1 for c in criteria_all if c["found"])
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

# ── Scorecard display with columns ────────────────────────────────────────────────
groups = group_by_topic(criteria)

for (code, topic), items in groups.items():
    g_found = sum(1 for i in items if i["found"])
    g_total = len(items)
    
    # Create collapsible section for each topic
    with st.expander(f"{code} — {topic} ({g_found}/{g_total})", expanded=False):
        # Create a grid of criteria cards using columns
        cols_per_row = 4
        for i in range(0, len(items), cols_per_row):
            cols = st.columns(cols_per_row, gap="large")
            
            for col_idx, item in enumerate(items[i:i+cols_per_row]):
                with cols[col_idx]:
                    found_class = "yes" if item["found"] else "no"
                    found_label = "✓ FOUND" if item["found"] else "✗ NOT FOUND"
                    found_color = "#1a7a4a" if item["found"] else "#c0392b"
                    examples = item.get("examples", [])
                    
                    # Card container
                    st.markdown(f"""
                    <div style="
                        border: 1px solid #e8eaf0; 
                        border-radius: 8px; 
                        padding: 0.75rem; 
                        background: white;
                        min-height: 110px;
                        margin-bottom: 1.5rem;
                        display: flex;
                        flex-direction: column;
                    ">
                        <div style="
                            color: {found_color};
                            font-weight: 600;
                            font-size: 0.8rem;
                            margin-bottom: 0.4rem;
                            font-family: 'IBM Plex Mono', monospace;
                        ">
                            {found_label}
                        </div>
                        <div style="
                            font-size: 0.85rem;
                            font-weight: 500;
                            color: #1a1a2e;
                            margin-bottom: 0.2rem;
                            flex-grow: 1;
                            line-height: 1.4;
                        ">
                            {item['subtopic']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Examples expander
                    if examples:
                        with st.expander(f"📄 {len(examples)} example{'s' if len(examples) > 1 else ''}"):
                            for ex in examples:
                                category = ex.get("category", "").title()
                                sentence = ex.get("sentence", "")
                                st.markdown(f'<div class="example-box"><strong>[{category}]</strong> "{sentence}"</div>', unsafe_allow_html=True)
        
        # Add spacing between topic sections
        st.markdown("<div style='margin-bottom: 5rem;'></div>", unsafe_allow_html=True)
