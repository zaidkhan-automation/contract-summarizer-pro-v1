# streamlit_app.py — Contract Summarizer Pro (demo + unlock CTA)
# --------------------------------------------------------------
# Features:
# - Daily free limit (session-based) + banner
# - Editable-amount Razorpay unlock CTA
# - PDF size guard (per file)
# - Multi-file upload (1 click = 1 run)
# - Calls FastAPI backend: POST {API_BASE}{CONTRACT_ENDPOINT}
# - Smart response handling (JSON summaries), pretty display + download

import os
import io
import json
import datetime as dt
import requests
import streamlit as st

# ------------------- CONFIG -------------------
st.set_page_config(page_title="Contract Summarizer Pro", page_icon="📑", layout="centered")

API_BASE = os.getenv("API_BASE", "http://localhost:8000")
CONTRACT_ENDPOINT = os.getenv("CONTRACT_ENDPOINT", "/summarize")  # e.g. "/summarize" or "/contracts/summarize"
FREE_LIMIT_PER_DAY = int(os.getenv("FREE_LIMIT_PER_DAY", "3"))
RAZORPAY_LINK = os.getenv("RAZORPAY_LINK", "https://razorpay.me/@taskmindai")  # editable amount link
CONTACT_MAILTO = os.getenv(
    "CONTACT_MAILTO",
    "mailto:contact@taskmindai.net?subject=TaskMindAI%20Contract%20Summarizer%20Access"
)
MAX_MB = float(os.getenv("DEMO_MAX_MB", "8"))  # per-file cap
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "240"))

# ------------------- DEMO LIMIT (BANNER) -------------------
if "usage_count" not in st.session_state:
    st.session_state.usage_count = 0
if "last_reset" not in st.session_state:
    st.session_state.last_reset = dt.date.today()

# daily reset
if st.session_state.last_reset != dt.date.today():
    st.session_state.usage_count = 0
    st.session_state.last_reset = dt.date.today()

st.markdown(
    f"""
    <div style="background:#111a3a;border:1px solid #223060;padding:10px 12px;border-radius:10px;margin-bottom:12px;">
      ⚙ <b>Daily usage:</b> {st.session_state['usage_count']} / {FREE_LIMIT_PER_DAY} free runs.<br>
      🔓 <span style="color:#9fb7ff">Need full unlimited access?</span><br>
      <a href="{RAZORPAY_LINK}" target="_blank" style="color:#9cf;font-weight:700;">Pay to Unlock (amount editable)</a> ·
      <a href="{CONTACT_MAILTO}" style="color:#9cf;">Contact us</a>
    </div>
    """,
    unsafe_allow_html=True,
)

def check_limit_or_stop():
    """Stop processing if today's free quota is over."""
    if st.session_state.usage_count >= FREE_LIMIT_PER_DAY:
        st.error("Demo limit reached for today. Unlock full access below.")
        st.link_button("💳 Pay to Unlock (Editable Amount)", RAZORPAY_LINK, use_container_width=True)
        st.link_button("📧 Contact for custom pricing", CONTACT_MAILTO, use_container_width=True)
        st.stop()

# Optional sidebar meter
with st.sidebar:
    st.subheader("Usage")
    st.progress(min(st.session_state.usage_count / FREE_LIMIT_PER_DAY, 1.0))
    st.caption(f"{st.session_state.usage_count} of {FREE_LIMIT_PER_DAY} free runs today")
    st.caption(f"Demo PDF size cap: {MAX_MB:.0f} MB")
    st.markdown("---")
    st.caption(f"API: {API_BASE}{CONTRACT_ENDPOINT}")

# ------------------- UI -------------------
st.title("📑 Contract Summarizer Pro")
st.write("Upload 1–3 PDF contracts and get clean, structured summaries.")

col1, col2 = st.columns(2)
with col1:
    files = st.file_uploader("Choose contract PDF(s)", type=["pdf"], accept_multiple_files=True,
                             help=f"Up to 3 files per run • {int(MAX_MB)}MB each")
with col2:
    concise = st.checkbox("Concise mode (shorter TL;DR)", value=True)
    include_risks = st.checkbox("Emphasize risks/red flags", value=True)

# ------------------- PROCESS -------------------
if files:
    st.success(f"{len(files)} file(s) selected.")
    if st.button("🧠 Summarize", type="primary", use_container_width=True):

        # 1) check demo limit (per click = 1 run)
        check_limit_or_stop()

        # 2) per-file size guard
        for f in files[:3]:
            size_mb = f.size / (1024 * 1024)
            if size_mb > MAX_MB:
                st.error(f"⚠ Demo limit: '{f.name}' is {size_mb:.2f} MB. Max allowed is {MAX_MB:.0f} MB per file.")
                st.stop()

        # 3) call backend
        with st.spinner("Summarizing... give me a moment to read your legal poetry."):
            try:
                # send up to first 3 files
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

        # 4) handle response (expecting JSON: {"results":[{"file":..., "summary": "..."}]})
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
                # download combined JSON
                st.download_button(
                    "📥 Download all summaries (JSON)",
                    data=json.dumps({"results": all_out}, indent=2).encode("utf-8"),
                    file_name="contract_summaries.json",
                    mime="application/json",
                    use_container_width=True,
                )
                st.caption("Generated via TaskMindAI · taskmindai.net")
                # increment quota usage only on success
                st.session_state.usage_count += 1
            else:
                st.info("No summaries returned. Try fewer pages or a clearer PDF.")

        else:
            # try to extract error
            msg = ""
            try:
                msg = resp.json().get("detail", "")
            except Exception:
                msg = resp.text[:500]
            st.error(f"Summarization failed (status {resp.status_code}). {msg or 'Please try another file.'}")

else:
    st.info("Please upload contract PDF(s) to begin.")