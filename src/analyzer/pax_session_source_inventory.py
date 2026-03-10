"""Inventory PS-VD source usage across processed PAX sessions."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from src.ingestion.source_catalog import SourceRecord, load_catalog


SESSION_DIR_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(?:-run\d+)?$")
SOURCE_ID_RE = re.compile(r"\bPS-VD-\d{3}\b")
TEXT_SUFFIXES = {".json", ".md", ".html", ".txt"}
OUTPUT_STAGE_DIRS = ("2-data", "3-analysis", "4-deep-dives", "5-playbook")


@dataclass(frozen=True)
class CatalogOccurrence:
    session: str
    source_id: str
    firm: str
    title: str
    url: str
    document_type: str
    bias_tag: str


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inventory source coverage across processed PAX sessions.")
    parser.add_argument(
        "--processed-root",
        default="data/processed/pax",
        help="Root directory containing processed PAX session outputs.",
    )
    parser.add_argument(
        "--baseline-session",
        default="2026-03-09-run2",
        help="Session to use as the baseline for comparison.",
    )
    parser.add_argument(
        "--output-dir",
        help="Output directory. Defaults to <processed-root>/source_inventory/.",
    )
    return parser


def discover_sessions(processed_root: str | Path) -> list[Path]:
    root = Path(processed_root)
    return sorted(path for path in root.iterdir() if path.is_dir() and SESSION_DIR_RE.match(path.name))


def extract_source_ids(text: str) -> list[str]:
    return sorted(set(SOURCE_ID_RE.findall(text)))


def normalize_url(url: str | None) -> str:
    if not url:
        return ""
    parsed = urlparse(url)
    path = (parsed.path or "").rstrip("/")
    return f"{parsed.netloc.lower()}{path}"


def iter_stage_files(session_dir: Path, *, include_crawl_vda: bool) -> list[Path]:
    files: list[Path] = []
    for stage_dir_name in OUTPUT_STAGE_DIRS:
        stage_dir = session_dir / stage_dir_name
        if not stage_dir.exists():
            continue
        for path in stage_dir.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            if not include_crawl_vda and path.name.startswith("crawl_vda_"):
                continue
            files.append(path)
    return sorted(files)


def collect_output_usage(session_dir: Path, *, include_crawl_vda: bool) -> tuple[set[str], list[dict[str, object]]]:
    source_ids: set[str] = set()
    files: list[dict[str, object]] = []
    for path in iter_stage_files(session_dir, include_crawl_vda=include_crawl_vda):
        text = path.read_text(encoding="utf-8", errors="ignore")
        ids = extract_source_ids(text)
        if not ids:
            continue
        source_ids.update(ids)
        files.append(
            {
                "path": str(path),
                "source_id_count": len(ids),
                "source_ids": ids,
            }
        )
    files.sort(key=lambda item: (-int(item["source_id_count"]), str(item["path"])))
    return source_ids, files


def load_session_catalog(session_dir: Path) -> list[SourceRecord]:
    catalog_path = session_dir / "1-universe" / "source_catalog.json"
    if not catalog_path.exists():
        return []
    return load_catalog(catalog_path)


def load_baseline_crawl_source_ids(session_dir: Path) -> set[str]:
    crawl_results_path = session_dir / "1-universe" / "crawl" / "crawl_results.json"
    if not crawl_results_path.exists():
        return set()
    payload = json.loads(crawl_results_path.read_text(encoding="utf-8"))
    return {
        str(item.get("source_id", "")).strip()
        for item in payload
        if isinstance(item, dict) and str(item.get("source_id", "")).strip()
    }


def build_session_snapshot(session_dir: Path) -> dict[str, object]:
    catalog_records = load_session_catalog(session_dir)
    catalog_source_ids = sorted({record.source_id for record in catalog_records if record.source_id})
    catalog_urls = sorted({normalize_url(record.url) for record in catalog_records if record.url})

    output_source_ids, output_files = collect_output_usage(session_dir, include_crawl_vda=False)
    augmented_source_ids, augmented_output_files = collect_output_usage(session_dir, include_crawl_vda=True)

    return {
        "session_name": session_dir.name,
        "path": str(session_dir),
        "has_catalog": bool(catalog_records),
        "catalog_source_count": len(catalog_source_ids),
        "catalog_url_count": len(catalog_urls),
        "catalog_source_ids": catalog_source_ids,
        "output_source_count": len(output_source_ids),
        "output_source_ids": sorted(output_source_ids),
        "augmented_output_source_count": len(augmented_source_ids),
        "augmented_output_source_ids": sorted(augmented_source_ids),
        "output_citation_file_count": len(output_files),
        "top_output_files": output_files[:10],
        "top_augmented_output_files": augmented_output_files[:10],
        "catalog_only_source_ids": sorted(set(catalog_source_ids) - output_source_ids),
        "output_only_source_ids": sorted(output_source_ids - set(catalog_source_ids)),
    }


def choose_canonical_occurrence(
    occurrences: list[CatalogOccurrence],
    *,
    baseline_session: str,
) -> CatalogOccurrence:
    for occurrence in occurrences:
        if occurrence.session == baseline_session:
            return occurrence
    return occurrences[-1]


def build_inventory(args: argparse.Namespace) -> dict[str, object]:
    processed_root = Path(args.processed_root)
    output_dir = Path(args.output_dir) if args.output_dir else processed_root / "source_inventory"
    output_dir.mkdir(parents=True, exist_ok=True)

    session_dirs = discover_sessions(processed_root)
    session_snapshots = [build_session_snapshot(session_dir) for session_dir in session_dirs]
    session_by_name = {snapshot["session_name"]: snapshot for snapshot in session_snapshots}

    baseline_session = args.baseline_session
    if baseline_session not in session_by_name:
        raise FileNotFoundError(f"Baseline session {baseline_session} was not found under {processed_root}")

    catalog_occurrences_by_source_id: dict[str, list[CatalogOccurrence]] = defaultdict(list)
    url_occurrences: list[tuple[str, str, str, str, str]] = []
    for session_dir in session_dirs:
        for record in load_session_catalog(session_dir):
            if not record.source_id:
                continue
            catalog_occurrences_by_source_id[record.source_id].append(
                CatalogOccurrence(
                    session=session_dir.name,
                    source_id=record.source_id,
                    firm=record.firm,
                    title=record.title,
                    url=record.url,
                    document_type=record.document_type,
                    bias_tag=record.bias_tag,
                )
            )
            url_occurrences.append(
                (
                    session_dir.name,
                    record.source_id,
                    normalize_url(record.url),
                    record.firm,
                    record.title,
                )
            )

    all_source_ids = set(catalog_occurrences_by_source_id)
    for snapshot in session_snapshots:
        all_source_ids.update(snapshot["output_source_ids"])
        all_source_ids.update(snapshot["augmented_output_source_ids"])

    baseline_snapshot = session_by_name[baseline_session]
    baseline_catalog_ids = set(baseline_snapshot["catalog_source_ids"])
    baseline_output_ids = set(baseline_snapshot["output_source_ids"])
    baseline_augmented_ids = set(baseline_snapshot["augmented_output_source_ids"])
    baseline_crawl_ids = load_baseline_crawl_source_ids(processed_root / baseline_session)

    older_catalog_ids: set[str] = set()
    for snapshot in session_snapshots:
        if snapshot["session_name"] == baseline_session:
            continue
        older_catalog_ids.update(snapshot["catalog_source_ids"])

    historical_url_records: dict[str, dict[str, object]] = {}
    baseline_url_set = {
        normalize_url(record.url)
        for record in load_session_catalog(processed_root / baseline_session)
        if record.url
    }
    baseline_crawl_payload_path = processed_root / baseline_session / "1-universe" / "crawl" / "crawl_results.json"
    baseline_crawl_url_set: set[str] = set()
    if baseline_crawl_payload_path.exists():
        payload = json.loads(baseline_crawl_payload_path.read_text(encoding="utf-8"))
        for item in payload:
            if not isinstance(item, dict):
                continue
            baseline_crawl_url_set.add(normalize_url(str(item.get("seed_url", ""))))
            baseline_crawl_url_set.add(normalize_url(str(item.get("loaded_url", ""))))

    for session_name, source_id, normalized_url, firm, title in url_occurrences:
        if not normalized_url or session_name == baseline_session or normalized_url in baseline_url_set:
            continue
        record = historical_url_records.setdefault(
            normalized_url,
            {
                "normalized_url": normalized_url,
                "source_id": source_id,
                "firm": firm,
                "title": title,
                "sessions": [],
                "covered_by_baseline_crawl": normalized_url in baseline_crawl_url_set,
            },
        )
        record["sessions"].append(session_name)

    source_rows: list[dict[str, object]] = []
    for source_id in sorted(all_source_ids):
        occurrences = sorted(
            catalog_occurrences_by_source_id.get(source_id, []),
            key=lambda occurrence: occurrence.session,
        )
        canonical = choose_canonical_occurrence(occurrences, baseline_session=baseline_session) if occurrences else None
        catalog_sessions = sorted({occurrence.session for occurrence in occurrences})
        output_sessions = sorted(
            snapshot["session_name"]
            for snapshot in session_snapshots
            if source_id in snapshot["output_source_ids"]
        )
        augmented_output_sessions = sorted(
            snapshot["session_name"]
            for snapshot in session_snapshots
            if source_id in snapshot["augmented_output_source_ids"]
        )

        baseline_in_catalog = source_id in baseline_catalog_ids
        baseline_in_original_outputs = source_id in baseline_output_ids
        baseline_in_augmented_outputs = source_id in baseline_augmented_ids
        baseline_in_crawl_results = source_id in baseline_crawl_ids

        if baseline_in_catalog and baseline_in_original_outputs:
            status_vs_baseline = "baseline_used"
        elif baseline_in_catalog and baseline_in_augmented_outputs:
            status_vs_baseline = "baseline_surfaced_by_crawl_vda"
        elif baseline_in_catalog:
            status_vs_baseline = "baseline_catalog_unused"
        elif catalog_sessions:
            status_vs_baseline = "historical_catalog_only"
        else:
            status_vs_baseline = "output_only"

        row = {
            "source_id": source_id,
            "firm": canonical.firm if canonical else None,
            "title": canonical.title if canonical else None,
            "canonical_url": canonical.url if canonical else None,
            "document_type": canonical.document_type if canonical else None,
            "bias_tag": canonical.bias_tag if canonical else None,
            "first_catalog_session": catalog_sessions[0] if catalog_sessions else None,
            "last_catalog_session": catalog_sessions[-1] if catalog_sessions else None,
            "catalog_sessions": catalog_sessions,
            "output_sessions": output_sessions,
            "augmented_output_sessions": augmented_output_sessions,
            "catalog_session_count": len(catalog_sessions),
            "output_session_count": len(output_sessions),
            "augmented_output_session_count": len(augmented_output_sessions),
            "baseline_in_catalog": baseline_in_catalog,
            "baseline_in_original_outputs": baseline_in_original_outputs,
            "baseline_in_augmented_outputs": baseline_in_augmented_outputs,
            "baseline_in_crawl_results": baseline_in_crawl_results,
            "status_vs_baseline": status_vs_baseline,
        }
        for snapshot in session_snapshots:
            session_name = snapshot["session_name"]
            row[f"catalog__{slugify(session_name)}"] = source_id in set(snapshot["catalog_source_ids"])
            row[f"output__{slugify(session_name)}"] = source_id in set(snapshot["output_source_ids"])
        source_rows.append(row)

    baseline_diff = {
        "source_ids_only_in_older_catalogs": sorted(older_catalog_ids - baseline_catalog_ids),
        "source_ids_only_in_baseline_catalog": sorted(baseline_catalog_ids - older_catalog_ids),
        "source_ids_in_baseline_catalog_not_used_original": sorted(baseline_catalog_ids - baseline_output_ids),
        "source_ids_in_baseline_catalog_not_used_augmented": sorted(baseline_catalog_ids - baseline_augmented_ids),
        "historical_urls_not_in_baseline_catalog": sorted(historical_url_records.values(), key=lambda item: (item["firm"], item["source_id"])),
        "historical_urls_uncovered_by_baseline_crawl": sorted(
            (item for item in historical_url_records.values() if not item["covered_by_baseline_crawl"]),
            key=lambda item: (item["firm"], item["source_id"]),
        ),
    }

    inventory = {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "processed_root": str(processed_root),
            "baseline_session": baseline_session,
            "session_count": len(session_snapshots),
            "catalog_session_count": sum(1 for snapshot in session_snapshots if snapshot["has_catalog"]),
            "source_id_universe_count": len(source_rows),
            "catalog_url_universe_count": len({url for _, _, url, _, _ in url_occurrences if url}),
        },
        "sessions": session_snapshots,
        "sources": source_rows,
        "baseline_diff": baseline_diff,
    }

    inventory_path = output_dir / "session_source_inventory.json"
    matrix_path = output_dir / "session_source_matrix.csv"
    summary_path = output_dir / "session_source_inventory.md"

    inventory_path.write_text(json.dumps(inventory, indent=2, ensure_ascii=False), encoding="utf-8")
    write_source_matrix(matrix_path, source_rows, session_snapshots)
    summary_path.write_text(render_summary(inventory), encoding="utf-8")

    return {
        "inventory_path": str(inventory_path),
        "matrix_path": str(matrix_path),
        "summary_path": str(summary_path),
        "session_count": len(session_snapshots),
        "source_id_universe_count": len(source_rows),
    }


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def write_source_matrix(path: Path, source_rows: list[dict[str, object]], session_snapshots: list[dict[str, object]]) -> None:
    fieldnames = [
        "source_id",
        "firm",
        "title",
        "canonical_url",
        "document_type",
        "bias_tag",
        "first_catalog_session",
        "last_catalog_session",
        "catalog_session_count",
        "output_session_count",
        "augmented_output_session_count",
        "baseline_in_catalog",
        "baseline_in_original_outputs",
        "baseline_in_augmented_outputs",
        "baseline_in_crawl_results",
        "status_vs_baseline",
        "catalog_sessions",
        "output_sessions",
        "augmented_output_sessions",
    ]
    for snapshot in session_snapshots:
        fieldnames.append(f"catalog__{slugify(snapshot['session_name'])}")
        fieldnames.append(f"output__{slugify(snapshot['session_name'])}")

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in source_rows:
            writer.writerow(
                {
                    **{
                        key: value
                        for key, value in row.items()
                        if key in fieldnames and not isinstance(value, list)
                    },
                    "catalog_sessions": ",".join(row["catalog_sessions"]),
                    "output_sessions": ",".join(row["output_sessions"]),
                    "augmented_output_sessions": ",".join(row["augmented_output_sessions"]),
                    **{
                        f"catalog__{slugify(snapshot['session_name'])}": row[f"catalog__{slugify(snapshot['session_name'])}"]
                        for snapshot in session_snapshots
                    },
                    **{
                        f"output__{slugify(snapshot['session_name'])}": row[f"output__{slugify(snapshot['session_name'])}"]
                        for snapshot in session_snapshots
                    },
                }
            )


def render_summary(inventory: dict[str, object]) -> str:
    metadata = inventory["metadata"]
    sessions = inventory["sessions"]
    baseline_diff = inventory["baseline_diff"]
    output_only_sessions = [session for session in sessions if session["output_only_source_ids"]]

    lines = [
        "# Session Source Inventory",
        "",
        f"Generated at: {metadata['generated_at']}",
        f"Baseline session: `{metadata['baseline_session']}`",
        f"Session count: `{metadata['session_count']}`",
        f"PS-VD source universe across catalogs and outputs: `{metadata['source_id_universe_count']}`",
        "",
        "## Session Overview",
        "",
        "| Session | Catalog Sources | Output Citations | Augmented Citations | Catalog Only | Output Only | Has Catalog |",
        "|---------|-----------------|------------------|---------------------|--------------|-------------|-------------|",
    ]
    for session in sessions:
        lines.append(
            f"| {session['session_name']} | {session['catalog_source_count']} | "
            f"{session['output_source_count']} | {session['augmented_output_source_count']} | "
            f"{len(session['catalog_only_source_ids'])} | {len(session['output_only_source_ids'])} | "
            f"{'Y' if session['has_catalog'] else 'N'} |"
        )

    lines.extend(
        [
            "",
            "## Baseline Coverage",
            "",
            f"- Sources only in older catalogs: `{len(baseline_diff['source_ids_only_in_older_catalogs'])}`",
            f"- Sources only in baseline catalog: `{len(baseline_diff['source_ids_only_in_baseline_catalog'])}`",
            f"- Baseline catalog sources not used in original outputs: `{len(baseline_diff['source_ids_in_baseline_catalog_not_used_original'])}`",
            f"- Baseline catalog sources not used even after crawl VDA augmentation: `{len(baseline_diff['source_ids_in_baseline_catalog_not_used_augmented'])}`",
            f"- Historical URLs still uncovered by baseline crawl: `{len(baseline_diff['historical_urls_uncovered_by_baseline_crawl'])}`",
            "",
            "### Older Catalog Sources Missing From Baseline Catalog",
            "",
        ]
    )

    for source_id in baseline_diff["source_ids_only_in_older_catalogs"]:
        lines.append(f"- `{source_id}`")

    lines.extend(
        [
            "",
            "### Baseline Catalog Sources Not Used In Original Outputs",
            "",
        ]
    )
    for source_id in baseline_diff["source_ids_in_baseline_catalog_not_used_original"]:
        lines.append(f"- `{source_id}`")

    lines.extend(
        [
            "",
            "### Output IDs Without Session Catalog Coverage",
            "",
        ]
    )
    for session in output_only_sessions:
        ids = ", ".join(session["output_only_source_ids"][:20])
        suffix = "" if len(session["output_only_source_ids"]) <= 20 else ", ..."
        lines.append(
            f"- `{session['session_name']}`: `{len(session['output_only_source_ids'])}` IDs not present in that session's catalog"
            f" ({ids}{suffix})"
        )

    lines.extend(
        [
            "",
            "### Historical URLs Uncovered By Baseline Crawl",
            "",
        ]
    )
    for record in baseline_diff["historical_urls_uncovered_by_baseline_crawl"]:
        sessions_csv = ", ".join(record["sessions"])
        lines.append(
            f"- `{record['source_id']}` | {record['firm']} | {record['title']} | sessions: {sessions_csv}"
        )

    return "\n".join(lines) + "\n"


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    summary = build_inventory(args)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
