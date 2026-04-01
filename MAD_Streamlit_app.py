# MAD_Streamlit_app.py
# Multi-Agent Document Intelligence Pipeline — Streamlit UI
# Runs all 4 agents sequentially, shows live progress + results.

import streamlit as st
import os
import json
import subprocess
import sys
from datetime import datetime

# ── PAGE CONFIG ──────────────────────────────────────────────
st.set_page_config(
    page_title="Document Intelligence Pipeline",
    page_icon="🤖",
    layout="wide"
)

# ── CUSTOM CSS ───────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 2rem;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 2rem;
    }
    .main-header h1 { color: white; font-size: 2rem; margin: 0; }
    .main-header p  { color: #aaaaaa; margin: 0.5rem 0 0 0; font-size: 0.95rem; }

    .agent-card {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.8rem;
        background: #fafafa;
    }
    .agent-card.running  { border-left: 4px solid #f59e0b; background: #fffbeb; }
    .agent-card.done     { border-left: 4px solid #10b981; background: #f0fdf4; }
    .agent-card.waiting  { border-left: 4px solid #d1d5db; background: #f9fafb; }

    .metric-box {
        background: #1a1a2e;
        color: white;
        border-radius: 10px;
        padding: 1.2rem;
        text-align: center;
    }
    .metric-box .value { font-size: 2rem; font-weight: bold; color: #10b981; }
    .metric-box .label { font-size: 0.85rem; color: #aaaaaa; margin-top: 0.3rem; }

    .field-row {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        padding: 0.7rem 0;
        border-bottom: 1px solid #f0f0f0;
    }
    .field-label { font-weight: 600; color: #374151; font-size: 0.9rem; min-width: 200px; }
    .field-value { color: #111827; font-size: 0.9rem; flex: 1; padding-left: 1rem; }
    .field-not-found { color: #9ca3af; font-style: italic; font-size: 0.9rem; }

    .badge-supported    { background:#d1fae5; color:#065f46; padding:2px 10px; border-radius:20px; font-size:0.78rem; font-weight:600; }
    .badge-not-found    { background:#f3f4f6; color:#6b7280; padding:2px 10px; border-radius:20px; font-size:0.78rem; font-weight:600; }
    .badge-partial      { background:#fef3c7; color:#92400e; padding:2px 10px; border-radius:20px; font-size:0.78rem; font-weight:600; }
    .badge-unsupported  { background:#fee2e2; color:#991b1b; padding:2px 10px; border-radius:20px; font-size:0.78rem; font-weight:600; }

    .zenith-footer {
        text-align: center;
        color: #9ca3af;
        font-size: 0.8rem;
        margin-top: 3rem;
        padding-top: 1rem;
        border-top: 1px solid #e5e7eb;
    }
</style>
""", unsafe_allow_html=True)

# ── HEADER ───────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🤖 Multi-Agent Document Intelligence Pipeline</h1>
    <p>Upload a contract PDF → 4 AI agents extract, analyse, and validate key fields automatically</p>
</div>
""", unsafe_allow_html=True)

# ── HELPER: RUN AGENT SCRIPT ─────────────────────────────────
def run_agent(script_name):
    """Runs an agent script as a subprocess. Returns (success, output)."""
    result = subprocess.run(
        [sys.executable, script_name],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    success = result.returncode == 0
    output  = result.stdout + (result.stderr if not success else "")
    return success, output

# ── HELPER: LOAD JSON SAFELY ─────────────────────────────────
def load_json(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return None

# ── HELPER: STATUS BADGE HTML ────────────────────────────────
def status_badge(status):
    mapping = {
        "SUPPORTED":     ("badge-supported",   "✓ Supported"),
        "NOT_FOUND":     ("badge-not-found",   "– Not Found"),
        "PARTIAL":       ("badge-partial",     "~ Partial"),
        "NOT_SUPPORTED": ("badge-unsupported", "✗ Mismatch"),
    }
    cls, label = mapping.get(status, ("badge-not-found", status))
    return f'<span class="{cls}">{label}</span>'

# ── SIDEBAR ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Pipeline Control")
    st.markdown("---")
    st.markdown("**How it works:**")
    st.markdown("""
    1. 📄 **Agent 1** — Load & chunk PDF into FAISS  
    2. 🔍 **Agent 2** — Extract contract fields via semantic search  
    3. 📋 **Agent 3** — Generate formatted PDF report  
    4. ✅ **Agent 4** — Validate extractions against source  
    """)
    st.markdown("---")
    st.markdown("**Pipeline Files:**")
    for fname in ["agent1_metadata.json", "agent2_extractions.json",
                  "agent3_contract_report.pdf", "agent4_validation_report.json"]:
        exists = "✅" if os.path.exists(fname) else "⬜"
        st.markdown(f"{exists} `{fname}`")
    st.markdown("---")
    st.markdown("**Built by**")
    st.markdown("🚀 [ZenithQuest](https://github.com/JohnDBSDSN)")

# ── MAIN: FILE UPLOAD ────────────────────────────────────────
st.markdown("### 📄 Step 1 — Upload Contract PDF")

uploaded_file = st.file_uploader(
    "Upload your contract PDF",
    type=["pdf"],
    help="Supported: Business contracts, agreements, NDAs"
)

if uploaded_file:
    # Save uploaded file as sample_document.pdf (agents expect this name)
    with open("sample_document.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success(f"✅ Uploaded: **{uploaded_file.name}** ({uploaded_file.size // 1024} KB)")

# ── MAIN: RUN PIPELINE BUTTON ────────────────────────────────
st.markdown("### 🚀 Step 2 — Run Pipeline")

col_btn, col_info = st.columns([1, 3])
with col_btn:
    run_pipeline = st.button(
        "▶ Run All Agents",
        type="primary",
        disabled=not os.path.exists("sample_document.pdf")
    )
with col_info:
    if not os.path.exists("sample_document.pdf"):
        st.info("Upload a PDF first to enable the pipeline.")
    else:
        st.info("Click to run all 4 agents sequentially.")

# ── MAIN: PIPELINE EXECUTION ─────────────────────────────────
if run_pipeline:
    st.markdown("### ⚙️ Pipeline Running...")

    agents = [
        ("agent1_loader.py",    "Agent 1 — PDF Loader & FAISS Indexer"),
        ("agent2_extractor.py", "Agent 2 — Contract Field Extractor"),
        ("agent3_generator.py", "Agent 3 — PDF Report Generator"),
        ("agent4_validator.py", "Agent 4 — Extraction Validator"),
    ]

    all_passed = True

    for script, label in agents:
        with st.status(f"🔄 Running {label}...", expanded=False) as status:
            success, output = run_agent(script)
            if success:
                status.update(label=f"✅ {label}", state="complete")
                st.code(output, language="bash")
            else:
                status.update(label=f"❌ {label} — FAILED", state="error")
                st.code(output, language="bash")
                all_passed = False
                break

    if all_passed:
        st.success("🎉 All 4 agents completed successfully!")
        st.rerun()

# ── MAIN: RESULTS DISPLAY ────────────────────────────────────
agent2_data = load_json("agent2_extractions.json")
agent4_data = load_json("agent4_validation_report.json")

if agent2_data and agent4_data:
    st.markdown("---")
    st.markdown("### 📊 Pipeline Results")

    # — Metrics row —
    m1, m2, m3, m4 = st.columns(4)

    total    = agent4_data["total_fields"]
    supported= agent4_data["supported"]
    flags    = agent4_data["flags_raised"]
    score    = agent4_data["pipeline_score"]

    with m1:
        st.markdown(f"""
        <div class="metric-box">
            <div class="value">{total}</div>
            <div class="label">Fields Queried</div>
        </div>""", unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="metric-box">
            <div class="value">{supported}</div>
            <div class="label">Confirmed</div>
        </div>""", unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="metric-box">
            <div class="value">{flags}</div>
            <div class="label">Flags Raised</div>
        </div>""", unsafe_allow_html=True)
    with m4:
        st.markdown(f"""
        <div class="metric-box">
            <div class="value">{score}</div>
            <div class="label">Pipeline Score</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # — Extracted fields table —
    st.markdown("#### 🔍 Extracted Contract Fields")

    field_labels = {
        "parties_involved":   "Parties Involved",
        "contract_date":      "Contract Date",
        "contract_duration":  "Contract Duration",
        "payment_terms":      "Payment Terms",
        "deliverables":       "Deliverables / Services",
        "termination_clause": "Termination Clause",
        "governing_law":      "Governing Law",
        "confidentiality":    "Confidentiality Clause"
    }

    # Build validation lookup
    val_lookup = {
        v["field"]: v for v in agent4_data["field_validations"]
    }

    extracted = agent2_data["extracted_fields"]

    for key, label in field_labels.items():
        value     = extracted.get(key, "Not found")
        val_data  = val_lookup.get(key, {})
        status    = val_data.get("status", "UNKNOWN")
        confidence= val_data.get("confidence", 0)
        badge     = status_badge(status)

        col_label, col_value, col_status, col_conf = st.columns([2, 4, 1.5, 1])
        with col_label:
            st.markdown(f"**{label}**")
        with col_value:
            if value == "Not found":
                st.markdown("*— Not found in document*")
            else:
                st.markdown(value)
        with col_status:
            st.markdown(badge, unsafe_allow_html=True)
        with col_conf:
            st.markdown(f"`{confidence}%`")

        st.divider()

    # — Download PDF report —
    st.markdown("#### 📥 Download Report")
    if os.path.exists("agent3_contract_report.pdf"):
        with open("agent3_contract_report.pdf", "rb") as f:
            st.download_button(
                label="⬇ Download Contract Intelligence Report (PDF)",
                data=f,
                file_name=f"contract_report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf",
                type="primary"
            )

# ── FOOTER ───────────────────────────────────────────────────
st.markdown("""
<div class="zenith-footer">
    Multi-Agent Document Intelligence Pipeline · Built by ZenithQuest · 
    Powered by LangChain · OpenAI · FAISS · ReportLab · Streamlit
</div>
""", unsafe_allow_html=True)