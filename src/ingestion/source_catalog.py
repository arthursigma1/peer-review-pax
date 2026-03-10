"""Load VDA source catalogs from JSON and legacy Markdown files."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

HTTP_URL_RE = re.compile(r"https?://[^\s|)>\]]+")
HEADING_COMPANY_RE = re.compile(r"^#+\s+(?:[A-Z]\.\s+)?(.+?)(?:\s+\(([^)]+)\))?$")


@dataclass(frozen=True)
class SourceRecord:
    source_id: str
    firm: str
    title: str
    date: str
    document_type: str
    bias_tag: str
    url: str
    notes: str
    catalog_path: str


def discover_catalog_files(processed_root: str | Path) -> list[Path]:
    """Discover structured and legacy source catalogs under the processed PAX tree."""
    root = Path(processed_root)
    json_catalogs = sorted(root.glob("*/1-universe/source_catalog.json"))
    legacy_catalogs = [
        path
        for path in (root / "stage_0_sources.md", root / "peer_p0_sources.md")
        if path.exists()
    ]
    return json_catalogs + legacy_catalogs


def find_latest_catalog_file(processed_root: str | Path) -> Path | None:
    """Return the most recent run-level source catalog, if one exists."""
    catalogs = sorted(Path(processed_root).glob("*/1-universe/source_catalog.json"))
    return catalogs[-1] if catalogs else None


def load_sources(processed_root: str | Path, *, latest_only: bool = False) -> list[SourceRecord]:
    """Load and de-duplicate source records from PAX processed outputs."""
    root = Path(processed_root)
    catalog_files = [find_latest_catalog_file(root)] if latest_only else discover_catalog_files(root)

    records: list[SourceRecord] = []
    for catalog_file in catalog_files:
        if catalog_file is None:
            continue
        records.extend(load_catalog(catalog_file))

    deduped: dict[tuple[str, str], SourceRecord] = {}
    for record in records:
        key = (record.source_id or "", record.url)
        deduped[key] = record
    return list(deduped.values())


def load_catalog(path: str | Path) -> list[SourceRecord]:
    """Load a single JSON or Markdown source catalog."""
    catalog_path = Path(path)
    if catalog_path.suffix == ".json":
        return _load_json_catalog(catalog_path)
    return _load_markdown_catalog(catalog_path)


def _load_json_catalog(path: Path) -> list[SourceRecord]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        payload = payload.get("sources", [])
    records: list[SourceRecord] = []
    for row in payload:
        if not isinstance(row, dict):
            continue
        url = _extract_http_url(row.get("url_or_reference") or row.get("url") or "")
        if not url:
            continue
        records.append(
            SourceRecord(
                source_id=str(row.get("source_id", "")).strip(),
                firm=str(row.get("firm", "")).strip(),
                title=str(row.get("title", "")).strip(),
                date=str(row.get("date", "")).strip(),
                document_type=str(row.get("document_type", row.get("type", ""))).strip(),
                bias_tag=str(row.get("bias_tag", row.get("bias_classification", ""))).strip(),
                url=url,
                notes=str(row.get("relevance_notes", row.get("metrics_covered", ""))).strip(),
                catalog_path=str(path),
            )
        )
    return records


def _load_markdown_catalog(path: Path) -> list[SourceRecord]:
    lines = path.read_text(encoding="utf-8").splitlines()
    current_firm = "PAX"
    records: list[SourceRecord] = []
    index = 0

    while index < len(lines):
        line = lines[index].strip()
        heading = _extract_heading_company(line)
        if heading:
            current_firm = heading

        if line.startswith("|") and index + 1 < len(lines) and _is_separator_row(lines[index + 1]):
            header_cells = _split_table_row(line)
            index += 2
            while index < len(lines) and lines[index].strip().startswith("|"):
                row_cells = _split_table_row(lines[index])
                if len(row_cells) == len(header_cells):
                    record = _markdown_row_to_record(
                        header_cells=header_cells,
                        row_cells=row_cells,
                        path=path,
                        default_firm=current_firm,
                    )
                    if record:
                        records.append(record)
                index += 1
            continue

        index += 1

    return records


def _markdown_row_to_record(
    *,
    header_cells: list[str],
    row_cells: list[str],
    path: Path,
    default_firm: str,
) -> SourceRecord | None:
    row = { _normalize_header(header): value.strip() for header, value in zip(header_cells, row_cells) }
    url = _extract_http_url(row.get("urlreference") or row.get("url") or "")
    if not url:
        return None

    firm = row.get("company") or default_firm
    notes = row.get("relevance") or row.get("metricscovered") or ""

    return SourceRecord(
        source_id=row.get("sourceid", ""),
        firm=firm.strip(),
        title=row.get("title", "").strip(),
        date=row.get("date", "").strip(),
        document_type=(row.get("type", "") or row.get("documenttype", "")).strip(),
        bias_tag=(row.get("biasclassification", "") or row.get("biastag", "")).strip(),
        url=url,
        notes=notes.strip(),
        catalog_path=str(path),
    )


def _extract_heading_company(line: str) -> str | None:
    match = HEADING_COMPANY_RE.match(line.strip())
    if not match:
        return None
    full_label, ticker = match.groups()
    if (
        "Stage " in full_label
        or full_label in {"Checklist", "Coverage Matrix"}
        or full_label.endswith("Sources")
        or full_label.endswith("Source Catalog")
        or full_label.endswith("Assessment")
        or full_label.endswith("Statistics")
        or full_label.endswith("Gaps and Recommendations")
    ):
        return None
    if ticker and ticker.isupper():
        return ticker
    return full_label.strip()


def _normalize_header(header: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", header.lower())


def _split_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _is_separator_row(line: str) -> bool:
    stripped = line.strip().replace("|", "").replace("-", "").replace(":", "")
    return stripped == ""


def _extract_http_url(value: str) -> str:
    match = HTTP_URL_RE.search(value)
    return match.group(0).rstrip(".,;") if match else ""
