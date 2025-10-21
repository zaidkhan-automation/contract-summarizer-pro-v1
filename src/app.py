# app.py — Contract Summarizer Pro (Freemium → Fixed ₹10k Unlock)
# --------------------------------------------------------------
# Features:
# - 3 free runs/day (session-based)
# - Fixed ₹10,000 unlock via Razorpay Payment Page (non-editable)
# - Multi-file upload (up to 3 PDFs per run)
# - Per-file size cap
# - Calls your FastAPI backend: POST {API_BASE}{CONTRACT_ENDPOINT}
# - Pretty JSON summaries + combined JSON download

import os
import json
import datetime as dt
import requests
import streamlit as st

# ------------------- PAGE CONFIG -------------------
st.set_page_config(page_title="Contract Summarizer Pro", page_icon="📑", layout="centered")

# ------------------- ENV / DEFAULTS -------------------
API_BASE = os.getenv("API_BASE", "http://localhost:8000")
CONTRACT_ENDPOINT = os.getenv("CONTRACT_ENDPOINT", "/summarize")  # e.g. "/summarize"
FREE_LIMIT_PER_DAY = int(os.getenv("FREE_LIMIT_PER_DAY", "3"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "240"))
MAX_MB = float(os.getenv("DEMO_MAX_MB", "8"))

# IMPORTANT: put your Razorpay Payment Page URL here (fixed amount ₹10,000)
# Example looks like: "https://pages.razorpay.com/contract-unlock-10k"
RAZORPAY_PAGE = os.getenv("RAZORPAY_PAGE", "https://pages.razorpay.com/REPLACE_WITH_YOURS")
CONTACT_MAILTO = os.getenv("CONTACT_MAILTO",
                           "mailto:contact@taskmindai.net?subject=TaskMindAI%20Contract%20Summarizer%20Access")

# ------------------- SESSION LIMITER -------------------
if "usage_count" not in st.session_state:
    st.session_state.usage_count = 0
if "last_reset" not in st.session_state:
    st.session_state.last_reset = dt.date.today()

if st.session_state.last_reset != dt.date.today():
    st.session_state.usage_count = 0
    st.session_state.last_reset = dt.date.today()

# ------------------- TOP BANNER -------------------
st.markdown(
    f"""
    <div style="background:#111a3a;border:1px solid #223060;padding:10px 12px;border-radius:10px;margin-bottom:12px;">
      ⚙ <b>Daily usage:</b> {st.session_state['usage_count']} / {FREE_LIMIT_PER_DAY} free runs.<br>
      🔓 <span style="color:#9fb7ff">Need full unlimited access?</span><br>
      <a href="{RAZORPAY_PAGE}" target="_blank" style="color:#9cf;font-weight:700;">
        Pay ₹10,000 to Unlock Lifetime Access
      </a> ·
      <a href="{CONTACT_MAILTO}" style="color:#9cf;">Contact us</a>
    </div>
    """,
    unsafe_allow_html=True,
)

def check_limit_or_stop():
    if st.session_state.usage_count >= FREE_LIMIT_PER_DAY:
        st.error("Demo limit reached for today. Unlock full access below.")
        st.link_button("💳 Pay ₹10,000 to Unlock", RAZORPAY_PAGE, use_container_width=True)
        st.link_button("📧 Contact for custom plan", CONTACT_MAILTO, use_container_width=True)
        st.stop()

# ------------------- SIDEBAR -------------------
with st.sidebar:
    st.subheader("Usage")
    st.progress(min(st.session_state.usage_count / FREE_LIMIT_PER_DAY, 1.0))
    st.caption(f"{st.session_state.usage_count} of {FREE_LIMIT_PER_DAY} free runs today")
    st.caption(f"Demo PDF size cap: {MAX_MB:.0f} MB")
    st.markdown("---")
    st.caption(f"API: {API_BASE}{CONTRACT_ENDPOINT}")

# ------------------- UI -------------------
st.title("📑 Contract Summarizer Pro")
st.write("Upload 1–3 contract PDFs and get a clean, structured summary. Demo gives 3 runs/day; unlock for lifetime access.")

col1, col2 = st.columns(2)
with col1:
    files = st.file_uploader(
        "Choose contract PDF(s)",
        type=["pdf"],
        accept_multiple_files=True,
        help=f"Up to 3 files per run • {int(MAX_MB)}MB each",
    )
with col2:
    concise = st.checkbox("Concise mode (shorter TL;DR)", value=True)
    include_risks = st.checkbox("Emphasize risks/red flags", value=True)

# ------------------- PROCESS -------------------
if files:
    st.success(f"{len(files)} file(s) selected.")
    if st.button("🧠 Summarize", type="primary", use_container_width=True):

        # 1) demo limit gate
        check_limit_or_stop()

        # 2) size checks
        for f in files[:3]:
            size_mb = f.size / (1024 * 1024)
            if size_mb > MAX_MB:
                st.error(f"⚠ Demo limit: '{f.name}' is {size_mb:.2f} MB. Max {MAX_MB:.0f} MB per file.")
                st.stop()

        # 3) call backend
        with st.spinner("Summarizing..."):
            try:
                mp = []
                for f in files[:3]:
                    mp.append(("files", (f.name, f.getvalue(), "application/pdf")))
                data = {
                    "concise": "true" if concise else "false",
                    "risks": "true" if include_risks else "false"
                }
                resp = requests.post(
                    f"{API_BASE}{CONTRACT_ENDPOINT}",
                    files=mp,
                    data=data,
                    timeout=REQUEST_TIMEOUT
                )
            except Exception as e:
                st.error(f"Backend unreachable. Check API_BASE/endpoint. Error: {e}")
                st.stop()

        # 4) handle response
        if resp.status_code == 200:
            try:
                payload = resp.json()
            except Exception:
                try:
                    payload = json.loads(resp.text)
                except Exception:
                    st.error("Could not parse server response.")
                    st.stop()

            results = payload.get("results") or payload.get("summaries") or []
            if not isinstance(results, list):
                results = []

            if results:
                st.success("✅ Summaries ready")
                all_out = []
                for item in results:
                    fname = item.get("file") or "contract.pdf"
                    summary = item.get("summary") or item.get("text") or ""
                    st.subheader(f"📎 {fname}")
                    st.markdown(summary if summary else "No summary text returned.")
                    all_out.append({"file": fname, "summary": summary})

                st.download_button(
                    "📥 Download all summaries (JSON)",
                    data=json.dumps({"results": all_out}, indent=2).encode("utf-8"),
                    file_name="contract_summaries.json",
                    mime="application/json",
                    use_container_width=True,
                )
                st.caption("Generated via TaskMindAI · taskmindai.net")
                st.session_state.usage_count += 1
            else:
                st.info("No summaries returned. Try fewer pages or a clearer PDF.")
        else:
            msg = ""
            try:
                msg = resp.json().get("detail", "")
            except Exception:
                msg = resp.text[:500]
            st.error(f"Summarization failed (status {resp.status_code}). {msg or 'Please try another file.'}")

else:
    st.info("Please upload contract PDF(s) to begin.")