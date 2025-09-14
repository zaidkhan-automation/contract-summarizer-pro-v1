"""
src/extractor.py

Functions to extract text from PDF and DOCX contract files, clean it, and chunk it
for summarization / retrieval.

Save as: src/extractor.py
"""

import os
import re
import tempfile
from typing import List, Dict

import pdfplumber
import docx  # python-docx
import nltk

# Ensure nltk punkt is available for sentence tokenization
try:
    nltk.data.find("tokenizers/punkt")
except Exception:
    nltk.download("punkt")

from nltk.tokenize import sent_tokenize


def _read_pdf_text(path: str) -> str:
    """Extract text from a digital PDF using pdfplumber."""
    text_parts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)


def _read_docx_text(path: str) -> str:
    """Extract text from a DOCX file using python-docx."""
    doc = docx.Document(path)
    paragraphs = [p.text for p in doc.paragraphs if p.text and p.text.strip()]
    return "\n".join(paragraphs)


def _clean_text(text: str) -> str:
    """Basic cleaning: normalize whitespace, remove multiple newlines, strip headers/footers noise."""
    if not text:
        return ""
    # Replace weird whitespace and multiple newlines
    text = text.replace("\r", "\n")
    text = re.sub(r"\n{2,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    # Remove long runs of non-text (optional)
    text = re.sub(r"[^\S\r\n]{2,}", " ", text)
    return text.strip()


def chunk_text_by_sentences(text: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
    """
    Chunk text into roughly chunk_size-character blocks using sentence boundaries.
    - chunk_size: approx target number of characters per chunk
    - overlap: number of characters to overlap between chunks
    Returns list of text chunks.
    """
    if not text:
        return []

    sentences = sent_tokenize(text)
    chunks = []
    current_chunk = ""
    for sent in sentences:
        if len(current_chunk) + len(sent) + 1 <= chunk_size:
            current_chunk += (" " + sent) if current_chunk else sent
        else:
            chunks.append(current_chunk.strip())
            # start new chunk with overlap
            if overlap > 0:
                tail = current_chunk[-overlap:] if len(current_chunk) >= overlap else current_chunk
                current_chunk = tail + " " + sent
            else:
                current_chunk = sent
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks


def extract_text_from_file(path: str) -> str:
    """
    Given a local filepath to PDF or DOCX, return extracted text.
    For any other extension, attempts a best-effort read (raises for unknown types).
    """
    path = str(path)
    ext = os.path.splitext(path)[1].lower()
    if ext in [".pdf"]:
        return _clean_text(_read_pdf_text(path))
    elif ext in [".doc", ".docx"]:
        return _clean_text(_read_docx_text(path))
    else:
        # Fallback: try pdfplumber for PDF-like files, otherwise raise
        raise ValueError(f"Unsupported file type: {ext}. Supported: .pdf, .docx")


def file_to_chunks(path: str, chunk_size: int = 800, overlap: int = 100) -> List[Dict]:
    """
    Full pipeline for a single file:
      - extract text
      - chunk into sentence-aware blocks
    Returns a list of dicts: [{'id': 'chunk_0', 'text': '...'}, ...]
    """
    text = extract_text_from_file(path)
    chunks = chunk_text_by_sentences(text, chunk_size=chunk_size, overlap=overlap)
    results = []
    for i, c in enumerate(chunks):
        results.append({"id": f"chunk_{i}", "text": c})
    return results


# Optional convenience helper for bytes-like uploaded files (Streamlit uploader)
def uploaded_file_to_chunks(uploaded_file, chunk_size: int = 800, overlap: int = 100) -> List[Dict]:
    """
    Accepts a Streamlit uploaded file object (or Django/Flask file-like) and returns chunks.
    It writes a temp file and calls file_to_chunks.
    """
    suffix = ""
    filename = getattr(uploaded_file, "name", None)
    if filename:
        suffix = os.path.splitext(filename)[1]
    else:
        # try to infer from content_type
        ct = getattr(uploaded_file, "content_type", "")
        if "pdf" in ct:
            suffix = ".pdf"
        elif "word" in ct or "doc" in ct:
            suffix = ".docx"
        else:
            suffix = ".txt"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getbuffer() if hasattr(uploaded_file, "getbuffer") else uploaded_file.read())
        tmp_path = tmp.name

    try:
        chunks = file_to_chunks(tmp_path, chunk_size=chunk_size, overlap=overlap)
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass

    return chunks