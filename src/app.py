"""
src/app.py

Streamlit UI for Contract Summarizer Pro v1.
- Upload PDF/DOCX
- Extract & chunk text
- Summarize with OpenAI if OPENAI_API_KEY is provided, otherwise a simple fallback summary
- Preview chunks and download summary
"""

import os
import streamlit as st
from extractor import uploaded_file_to_chunks
from io import BytesIO
import base64
import textwrap

# Try to import openai; app still works without it (fallback summary)
try:
    import openai
    OPENAI_AVAILABLE = True
except Exception:
    OPENAI_AVAILABLE = False

st.set_page_config(page_title="Contract Summarizer Pro v1", layout="centered")
st.title("📝 Contract Summarizer — Pro v1")
st.write("Upload a contract (PDF or DOCX). The app extracts text, chunks it, and provides a short summary.")

# Sidebar options
st.sidebar.header("Options")
chunk_size = st.sidebar.number_input("Chunk size (chars, approx)", min_value=300, max_value=3000, value=1000, step=100)
overlap = st.sidebar.number_input("Chunk overlap (chars)", min_value=0, max_value=500, value=150, step=50)
summary_chunks = st.sidebar.number_input("Number of chunks to include in quick summary", min_value=1, max_value=10, value=3, step=1)
openai_model = st.sidebar.selectbox("OpenAI model (if key provided)", ["gpt-4o-mini", "gpt-4o", "gpt-4.1", "gpt-4"], index=0)

# File uploader
uploaded = st.file_uploader("Upload contract (PDF or DOCX)", type=["pdf", "docx"])

if uploaded is not None:
    st.info("Extracting text and creating chunks...")
    try:
        chunks = uploaded_file_to_chunks(uploaded, chunk_size=chunk_size, overlap=overlap)
    except Exception as e:
        st.error(f"Failed to extract text: {e}")
        st.stop()

    if not chunks:
        st.warning("No text found in file. If the PDF is scanned, OCR is required (future feature).")
    else:
        st.success(f"Extracted {len(chunks)} chunks from file.")

        # Show first few chunks preview
        st.subheader("Preview — first chunks")
        preview_count = min(5, len(chunks))
        for i in range(preview_count):
            st.markdown(f"*Chunk {i}*")
            st.code(textwrap.shorten(chunks[i]["text"], width=800, placeholder="..."))

        # Summarize section
        st.subheader("Summarize")

        use_openai = False
        if "OPENAI_API_KEY" in os.environ and OPENAI_AVAILABLE:
            st.write("OpenAI key found in environment. You may use OpenAI for an abstractive summary.")
            use_openai = st.checkbox("Use OpenAI for summary (abstractive)", value=True)
        else:
            st.write("No OpenAI key found or openai package missing. Fallback extractive summary will be used.")
            use_openai = False

        # Buttons
        if st.button("Generate Summary"):
            with st.spinner("Generating summary..."):
                try:
                    if use_openai:
                        # Prepare prompt: concatenate top N chunks
                        top_n = min(summary_chunks, len(chunks))
                        context = "\n\n".join([chunks[i]["text"] for i in range(top_n)])
                        prompt = (
                            "You are a concise legal assistant. Read the following contract excerpts and produce a clear, "
                            "concise summary (5-8 bullet points) highlighting parties, purpose, key obligations, payment terms, "
                            "important dates, and risks or termination clauses if present.\n\n"
                            f"CONTEXT:\\n{context}\\n\\nSUMMARY:"
                        )

                        # Use OpenAI API
                        openai.api_key = os.environ.get("OPENAI_API_KEY")
                        resp = openai.ChatCompletion.create(
                            model=openai_model,
                            messages=[{"role": "user", "content": prompt}],
                            max_tokens=400,
                            temperature=0.0,
                        )
                        # get content (compatible with ChatCompletion)
                        summary_text = resp["choices"][0]["message"]["content"].strip()
                    else:
                        # Fallback: join first N chunks and return that as "summary"
                        top_n = min(summary_chunks, len(chunks))
                        summary_text = "\n\n".join([chunks[i]["text"] for i in range(top_n)])
                        # Trim to reasonable length
                        summary_text = summary_text[:3000] + ("..." if len(summary_text) > 3000 else "")

                    # Show summary
                    st.subheader("Summary")
                    st.write(summary_text)

                    # Offer download
                    b = summary_text.encode("utf-8")
                    b64 = base64.b64encode(b).decode()
                    href = f'<a href="data:text/plain;base64,{b64}" download="summary.txt">Download summary (TXT)</a>'
                    st.markdown(href, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Summary generation failed: {e}")

        # Optionally show all chunks
        with st.expander("Show all chunks"):
            for c in chunks:
                st.code(c["text"][:1200] + ("..." if len(c["text"]) > 1200 else ""))

        # Small note for clients
        st.markdown(
            "<small>Note: This is a v1 summarizer. For scanned PDFs, enable OCR (Tesseract) or use cloud OCR. "
            "For production we offer private deployments with authentication and auto-delete of uploaded files.</small>",
            unsafe_allow_html=True,
        )