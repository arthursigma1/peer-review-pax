"""Document converter using marker-pdf. Converts PDF, DOCX, and PPTX to structured text."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".txt", ".md"}

# Bias tag mapping for common source types
SOURCE_BIAS_HINTS = {
    "sell-side": "third-party-analyst",
    "research": "third-party-analyst",
    "mckinsey": "industry-report",
    "bcg": "industry-report",
    "bain": "industry-report",
    "preqin": "industry-report",
    "annual": "regulatory-filing",
    "10-k": "regulatory-filing",
    "20-f": "regulatory-filing",
    "investor": "company-produced",
    "earnings": "company-produced",
    "presentation": "company-produced",
    "supplement": "company-produced",
}


def _infer_bias_tag(filename: str) -> str:
    """Infer a bias tag from filename keywords."""
    lower = filename.lower()
    for keyword, tag in SOURCE_BIAS_HINTS.items():
        if keyword in lower:
            return tag
    return "third-party-analyst"


def convert_pdf(path: str | Path) -> dict[str, Any]:
    """Convert a single PDF/DOCX/PPTX file to structured text using marker-pdf.

    Returns dict with keys: text, filename, pages, format, bias_tag, confidence.
    """
    from marker.converters.pdf import PdfConverter
    from marker.models import create_model_dict
    from marker.output import text_from_rendered

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    ext = path.suffix.lower()
    if ext == ".txt" or ext == ".md":
        text = path.read_text(encoding="utf-8")
        return {
            "text": text,
            "filename": path.name,
            "pages": 1,
            "format": ext.lstrip("."),
            "bias_tag": _infer_bias_tag(path.name),
            "confidence": 1.0,
        }

    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {ext}. Supported: {SUPPORTED_EXTENSIONS}")

    converter = PdfConverter(artifact_dict=create_model_dict())
    rendered = converter(str(path))
    text, _, _images = text_from_rendered(rendered)

    page_count = rendered.metadata.get("pages", 0) if hasattr(rendered, "metadata") else 0

    return {
        "text": text,
        "filename": path.name,
        "pages": page_count,
        "format": ext.lstrip("."),
        "bias_tag": _infer_bias_tag(path.name),
        "confidence": 0.9 if ext == ".pdf" else 0.95,
    }


def convert_directory(dir_path: str | Path) -> list[dict[str, Any]]:
    """Batch-convert all supported files in a directory.

    Returns list of dicts, each with: text, filename, pages, format, bias_tag, confidence.
    """
    dir_path = Path(dir_path)
    if not dir_path.is_dir():
        raise NotADirectoryError(f"Not a directory: {dir_path}")

    results = []
    for entry in sorted(dir_path.iterdir()):
        if entry.is_file() and entry.suffix.lower() in SUPPORTED_EXTENSIONS:
            try:
                result = convert_pdf(entry)
                results.append(result)
            except Exception as e:
                results.append({
                    "text": "",
                    "filename": entry.name,
                    "pages": 0,
                    "format": entry.suffix.lstrip("."),
                    "bias_tag": _infer_bias_tag(entry.name),
                    "confidence": 0.0,
                    "error": str(e),
                })
    return results
