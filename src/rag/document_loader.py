from __future__ import annotations

import io
import re
from html.parser import HTMLParser
from pathlib import Path

from src.config import settings


class DocumentLoadError(ValueError):
    pass


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() in {"script", "style", "noscript"}:
            self._skip_depth += 1
        elif tag.lower() in {"p", "div", "br", "li", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript"} and self._skip_depth:
            self._skip_depth -= 1
        elif tag.lower() in {"p", "div", "li"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            self.parts.append(data)

    def text(self) -> str:
        return _normalize_text(" ".join(self.parts))


def _normalize_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def _allowed_extensions() -> set[str]:
    return {
        item.strip().lower()
        for item in settings.allowed_upload_extensions.split(",")
        if item.strip()
    }


def load_document_bytes(filename: str, data: bytes) -> str:
    if not filename:
        raise DocumentLoadError("Filename is required")
    if not data:
        raise DocumentLoadError("Uploaded file is empty")
    if len(data) > settings.max_upload_bytes:
        raise DocumentLoadError(
            f"File exceeds MAX_UPLOAD_BYTES ({settings.max_upload_bytes} bytes)"
        )

    ext = Path(filename).suffix.lower()
    if ext not in _allowed_extensions():
        raise DocumentLoadError(
            f"Unsupported file type '{ext or 'unknown'}'. "
            f"Allowed: {', '.join(sorted(_allowed_extensions()))}"
        )

    if ext in {".txt", ".md", ".markdown"}:
        text = data.decode("utf-8-sig", errors="replace")
    elif ext in {".html", ".htm"}:
        parser = _VisibleTextParser()
        parser.feed(data.decode("utf-8-sig", errors="replace"))
        text = parser.text()
    elif ext == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise DocumentLoadError("PDF ingestion requires pypdf") from exc
        try:
            reader = PdfReader(io.BytesIO(data))
            if reader.is_encrypted:
                raise DocumentLoadError("Encrypted PDFs are not supported")
            text = "\n\n".join((page.extract_text() or "") for page in reader.pages)
        except DocumentLoadError:
            raise
        except Exception as exc:
            raise DocumentLoadError("Could not parse PDF") from exc
    else:
        raise DocumentLoadError(f"Unsupported file type: {ext}")

    normalized = _normalize_text(text)
    if not normalized:
        raise DocumentLoadError("Document contains no extractable text")
    return normalized
