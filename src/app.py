# Invoice Extractor SaaS — Streamlit app (freemium + Razorpay unlock)
# -------------------------------------------------------------------
# Env: API_BASE, INVOICE_ENDPOINT=/extract, FREE_LIMIT_PER_DAY=3, DEMO_MAX_MB=8, REQUEST_TIMEOUT=180

import os, json, datetime as dt, requests, streamlit as st

st.set_page_config(page_title="Invoice Extractor SaaS", page_icon="📄", layout="centered")

API_BASE = os.getenv("API_BASE", "http://localhost:8000")
INVOICE_ENDPOINT = os.getenv("INVOICE_ENDPOINT", "/extract")
FREE_LIMIT_PER_DAY = int(os.getenv("FREE_LIMIT_PER_DAY", "3"))
MAX_MB = float(os.getenv("DEMO_MAX_MB", "8"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "180"))
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
    st.caption(f"API: {API_BASE}{INVOICE_ENDPOINT}")
    st.caption(f"Max size: {MAX_MB:.0f} MB")

st.title("📄 Invoice Extractor")
st.write("Upload a PDF invoice and get structured data (JSON/CSV) instantly.")

col1, col2 = st.columns(2)
with col1:
    pdf = st.file_uploader("Choose a PDF invoice", type=["pdf"])
with col2:
    use_ocr = st.checkbox("Enable OCR (for scanned PDFs)", value=False)

if pdf:
    if st.button("🔎 Extract Data", type="primary", use_container_width=True):
        guard_or_stop()
        size_mb = pdf.size / (1024*1024)
        if size_mb > MAX_MB:
            st.error(f"File is {size_mb:.2f} MB. Demo cap is {MAX_MB:.0f} MB.")
            st.stop()

        with st.spinner("Extracting…"):
            try:
                resp = requests.post(f"{API_BASE}{INVOICE_ENDPOINT}",
                                     files={"file": (pdf.name, pdf.getvalue(), "application/pdf")},
                                     data={"ocr": "true" if use_ocr else "false"},
                                     timeout=REQUEST_TIMEOUT)
            except Exception as e:
                st.error(f"Backend unreachable: {e}")
                st.stop()

        ctype = resp.headers.get("content-type","")
        if resp.status_code == 200 and ("application/json" in ctype or resp.text.strip().startswith("{")):
            data = resp.json()
            st.success("✅ Extracted JSON")
            keys = ["invoice_number","invoice_no","invoice_date","date","supplier","buyer","subtotal","tax","total","currency"]
            st.subheader("Summary")
            st.json({k:v for k,v in data.items() if k in keys and v is not None})
            items = data.get("items") or data.get("line_items")
            if isinstance(items, list) and items:
                st.subheader("Line Items")
                st.dataframe(items, use_container_width=True)
            st.download_button("📥 Download JSON",
                               data=json.dumps(data, indent=2).encode("utf-8"),
                               file_name=f"invoice_{pdf.name.rsplit('.',1)[0]}.json",
                               mime="application/json",
                               use_container_width=True)
            st.caption("Generated via TaskMindAI · taskmindai.net")
            st.session_state.usage_count += 1
        elif resp.status_code == 200:
            st.success("✅ Extracted file")
            ext = ".csv"
            if "spreadsheetml" in ctype: ext = ".xlsx"
            elif "zip" in ctype: ext = ".zip"
            st.download_button("📥 Download Result", resp.content,
                               file_name=f"invoice_{pdf.name.rsplit('.',1)[0]}{ext}",
                               mime=ctype or "application/octet-stream",
                               use_container_width=True)
            st.caption("Generated via TaskMindAI · taskmindai.net")
            st.session_state.usage_count += 1
        else:
            st.error(f"Extraction failed ({resp.status_code}). {resp.text[:300] or ''}")
else:
    st.info("Upload a PDF invoice to begin.")