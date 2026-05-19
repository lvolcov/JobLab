"""Text extraction for uploaded documents.

Purpose: route bytes to the right parser based on MIME / extension.
Safety: parsers are invoked with size already validated; no eval, no shellouts.
Created: 2026-05-19
"""

from __future__ import annotations

import io

from pypdf import PdfReader

ALLOWED_MIME = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "text/plain": "txt",
    "text/markdown": "md",
}

# Some browsers send .md as application/octet-stream; we fall back on extension.
EXT_TO_KIND = {".pdf": "pdf", ".docx": "docx", ".txt": "txt", ".md": "md"}


def resolve_kind(mime: str, filename: str) -> str | None:
    """Return the parsing kind ('pdf'|'docx'|'txt'|'md') or None if unsupported."""
    if mime in ALLOWED_MIME:
        return ALLOWED_MIME[mime]
    lower = filename.lower()
    for ext, kind in EXT_TO_KIND.items():
        if lower.endswith(ext):
            return kind
    return None


def extract_text(kind: str, data: bytes) -> str:
    """Extract plain text from the given bytes according to kind."""
    if kind == "pdf":
        reader = PdfReader(io.BytesIO(data))
        parts: list[str] = []
        for page in reader.pages:
            try:
                parts.append(page.extract_text() or "")
            except Exception:
                parts.append("")
        return "\n".join(parts).strip()
    if kind == "docx":
        # Imported lazily so a missing optional dependency only fails at use time.
        from docx import Document as DocxDocument

        doc = DocxDocument(io.BytesIO(data))
        return "\n".join(p.text for p in doc.paragraphs).strip()
    if kind in {"txt", "md"}:
        for encoding in ("utf-8", "utf-16", "latin-1"):
            try:
                return data.decode(encoding).strip()
            except UnicodeDecodeError:
                continue
        return data.decode("utf-8", errors="replace").strip()
    raise ValueError(f"unsupported kind: {kind}")
