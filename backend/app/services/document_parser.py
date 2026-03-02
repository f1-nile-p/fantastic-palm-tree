import io
import logging

logger = logging.getLogger(__name__)


def parse_document(file_bytes: bytes, filename: str) -> str:
    """Parse uploaded document and return extracted text."""
    name_lower = filename.lower()

    try:
        if name_lower.endswith(".pdf"):
            return _parse_pdf(file_bytes)
        elif name_lower.endswith(".docx"):
            return _parse_docx(file_bytes)
        elif name_lower.endswith(".txt"):
            return _parse_txt(file_bytes)
        else:
            # Attempt plain text fallback
            return _parse_txt(file_bytes)
    except Exception as exc:
        logger.error("Failed to parse document %s: %s", filename, exc)
        return ""


def _parse_pdf(file_bytes: bytes) -> str:
    import PyPDF2

    reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
    parts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            parts.append(text)
    return "\n".join(parts)


def _parse_docx(file_bytes: bytes) -> str:
    from docx import Document

    doc = Document(io.BytesIO(file_bytes))
    return "\n".join(para.text for para in doc.paragraphs if para.text.strip())


def _parse_txt(file_bytes: bytes) -> str:
    for encoding in ("utf-8", "latin-1", "cp1252"):
        try:
            return file_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    return file_bytes.decode("utf-8", errors="replace")
