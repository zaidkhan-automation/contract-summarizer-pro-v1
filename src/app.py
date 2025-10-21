# Contract Summarizer Pro — Streamlit app (freemium + Razorpay unlock)
# -------------------------------------------------------------------
# Env: API_BASE, CONTRACT_ENDPOINT=/summarize, FREE_LIMIT_PER_DAY=3, DEMO_MAX_MB=8, REQUEST_TIMEOUT=240

import os, json, datetime as dt, requests, streamlit as st

st.set_page_config(page_title="Contract Summarizer Pro", page_icon="📑", layout="centered")

API_BASE = os.getenv("API_BASE", "http://localhost:8000")
CONTRACT_ENDPOINT = os.getenv("CONTRACT_ENDPOINT", "/summarize")
FREE_LIMIT_PER_DAY = int(os.getenv("FREE_LIMIT_PER_DAY", "3"))
MAX_MB = float(os.getenv("DEMO_MAX_MB", "8"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "240"))
PAYMENT_URL = "https://rzp.io/rzp/taskmindai-payment"
CONTACT = "mailto:contact@taskmindai.net"

if "usage_count" not in st.session_state:
    st.session_state.usage_count = 0
if "last_reset" not in st.session_state:
    st.session_state.last_reset = dt.date.today()
if st.session_state.last_reset != dt.date.today():
    st.session_state.usage_count = 0
    st.session_state.last_reset = dt.date.today()

st.markdown(f"""
<div style="background:#0f1425;border:1px solid #1d2b48;padding:12px;border-radius:12px;margin:4px 0 16px">
  <b>Demo mode:</b> {st.session_state['usage_count']} / {FREE_LIMIT_PER_DAY} free runs today.
  <div style="margin-top:6px">
    Need unlimited runs? <a href="{PAYMENT_URL}" target="_blank" style="color:#9cc9ff;font-weight:600">Unlock via Razorpay</a> ·
    <a href="{CONTACT}" style="color:#9cc9ff">Contact</a>
  </div>
</div>
""", unsafe_allow_html=True)

def guard_or_stop():
    if st.session_state.usage_count >= FREE_LIMIT_PER_DAY:
        st.error("Daily demo limit reached. Unlock full access to continue.")
        st.link_button("💳 Unlock via Razorpay", PAYMENT_URL, use_container_width=True)
        st.stop()

with st.sidebar:
    st.subheader("Usage")
    st.progress(min(st.session_state.usage_count / FREE_LIMIT_PER_DAY, 1.0))
    st.caption(f"API: {API_BASE}{CONTRACT_ENDPOINT}")
    st.caption(f"Max size: {MAX_MB:.0f} MB")

st.title("📑 Contract Summarizer Pro")
st.write("Upload 1–3 contract PDFs and get clean summaries. Demo gives 3 free runs/day.")

c1, c2 = st.columns(2)
with c1:
    files = st.file_uploader("Choose contract PDF(s)", type=["pdf"], accept_multiple_files=True,
                             help=f"Up to 3 files • {int(MAX_MB)}MB each")
with c2:
    concise = st.checkbox("Concise TL;DR", value=True)
    risk = st.checkbox("Highlight risks/red flags", value=True)

if files:
    if st.button("🧠 Summarize", type="primary", use_container_width=True):
        guard_or_stop()
        files = files[:3]
        for f in files:
            if f.size / (1024*1024) > MAX_MB:
                st.error(f"'{f.name}' exceeds {MAX_MB:.0f} MB demo cap.")
                st.stop()

        with st.spinner("Summarizing…"):
            try:
                mp = [("files", (f.name, f.getvalue(), "application/pdf")) for f in files]
                data = {"concise": "true" if concise else "false",
                        "risks": "true" if risk else "false"}
                resp = requests.post(f"{API_BASE}{CONTRACT_ENDPOINT}", files=mp, data=data,
                                     timeout=REQUEST_TIMEOUT)
            except Exception as e:
                st.error(f"Backend unreachable: {e}")
                st.stop()

        if resp.status_code == 200:
            try:
                payload = resp.json()
            except Exception:
                payload = json.loads(resp.text)

            results = payload.get("results") or payload.get("summaries") or []
            if not isinstance(results, list):
                results = []

            if results:
                st.success("✅ Summaries ready")
                out = []
                for item in results:
                    fname = item.get("file") or "contract.pdf"
                    text = item.get("summary") or item.get("text") or ""
                    st.subheader(f"📎 {fname}")
                    st.markdown(text if text else "No summary returned.")
                    out.append({"file": fname, "summary": text})

                st.download_button("📥 Download all (JSON)",
                                   data=json.dumps({"results": out}, indent=2).encode("utf-8"),
                                   file_name="contract_summaries.json",
                                   mime="application/json",
                                   use_container_width=True)
                st.caption("Generated via TaskMindAI · taskmindai.net")
                st.session_state.usage_count += 1
            else:
                st.info("No summaries returned. Try fewer pages or clearer PDFs.")
        else:
            st.error(f"Summarization failed ({resp.status_code}). {resp.text[:300] or ''}")
else:
    st.info("Upload contract PDFs to begin.")