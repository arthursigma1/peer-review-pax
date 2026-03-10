"""Generate an incremental delta spec for VDA data collectors using a base run."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from src.analyzer._shared import (
    FirmRecord,
    load_firms_from_payload,
    split_firms_into_tiers as _split_firms_into_tiers_shared,
)


# Gap classifications that are eligible for collection.
_COLLECT_GAP_TYPES = frozenset({"never_attempted", "derivable_not_derived", "stale"})

# Priorities that block collection for never_attempted / derivable_not_derived cells.
_SKIP_PRIORITIES = frozenset({"skip", "low"})

# Gap classifications that are skipped unconditionally.
_SKIP_GAP_TYPES = frozenset({"not_disclosed"})


# ---------------------------------------------------------------------------
# Internal records
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MetricRecord:
    metric_id: str
    name: str
    abbreviation: str
    calculation_notes: str


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def build_delta_spec(args: argparse.Namespace) -> dict[str, object]:
    """Build the delta spec and write it to the new run directory."""
    base_run_dir = Path(args.base_run).resolve()
    new_run_dir = Path(args.new_run_dir).resolve()

    data_gaps_path = (
        Path(args.data_gaps)
        if args.data_gaps
        else base_run_dir / "3-analysis" / "data_gaps.json"
    )
    peer_universe_path = (
        Path(args.peer_universe)
        if args.peer_universe
        else base_run_dir / "1-universe" / "peer_universe.json"
    )
    metric_taxonomy_path = (
        Path(args.metric_taxonomy)
        if args.metric_taxonomy
        else base_run_dir / "1-universe" / "metric_taxonomy.json"
    )
    standardized_matrix_path = (
        Path(args.standardized_matrix)
        if args.standardized_matrix
        else base_run_dir / "3-analysis" / "standardized_matrix.json"
    )

    # Load inputs.
    data_gaps = _load_json(data_gaps_path)
    peer_universe = _load_json(peer_universe_path)
    metric_taxonomy = _load_json(metric_taxonomy_path)
    standardized_matrix = _load_json(standardized_matrix_path)

    # Build lookup structures.
    firms = _load_firms(peer_universe)
    metrics_index = _build_metrics_index(metric_taxonomy)
    matrix_cells = _index_matrix(standardized_matrix)
    gap_detail = _index_gap_detail(data_gaps)

    # Tier splitting — same logic as metric_checklist.py.
    tier1, tier2, tier3 = _split_firms_into_tiers(firms)
    tier_map: dict[str, str] = {}
    for firm in tier1:
        tier_map[firm.firm_id] = "tier1"
    for firm in tier2:
        tier_map[firm.firm_id] = "tier2"
    for firm in tier3:
        tier_map[firm.firm_id] = "tier3"

    # Classify every (firm, metric) cell.
    carry_forward_cells: list[dict[str, object]] = []
    skip_cells: list[dict[str, object]] = []
    collect_cells: list[dict[str, object]] = []

    priority_breakdown: dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0}

    all_firm_ids = [f.firm_id for f in firms]
    all_metric_ids = list(metrics_index.keys())

    for firm in firms:
        for metric_id in all_metric_ids:
            metric = metrics_index[metric_id]
            cell = matrix_cells.get((firm.firm_id, metric_id), {})
            value = cell.get("value")
            gap = gap_detail.get((firm.firm_id, metric_id))

            if value is not None:
                # Cell has data — carry forward unchanged.
                carry_forward_cells.append(
                    {
                        "firm_id": firm.firm_id,
                        "ticker": firm.ticker,
                        "metric_id": metric_id,
                        "value": value,
                        "unit": cell.get("unit"),
                        "source": cell.get("source"),
                        "as_of": cell.get("as_of"),
                    }
                )
            else:
                # No value — determine skip vs collect.
                gap_classification = gap.get("gap_type") or gap.get("gap_classification") if gap else None
                backfill_priority = gap.get("backfill_priority") if gap else None

                if gap_classification in _SKIP_GAP_TYPES or backfill_priority == "skip":
                    # Confirmed non-disclosure — skip.
                    skip_cells.append(
                        {
                            "firm_id": firm.firm_id,
                            "ticker": firm.ticker,
                            "metric_id": metric_id,
                            "reason": gap_classification or "not_disclosed",
                        }
                    )
                elif gap_classification in _COLLECT_GAP_TYPES:
                    # Check priority eligibility.
                    if gap_classification == "stale":
                        # Stale cells are always collected regardless of priority.
                        as_of = cell.get("as_of", "unknown")
                        hint = (
                            f"Update from latest filings — base run had {as_of} data"
                        )
                        collection_priority = backfill_priority or "medium"
                        collect_cells.append(
                            _make_collect_cell(
                                firm=firm,
                                metric_id=metric_id,
                                metric=metric,
                                collection_priority=collection_priority,
                                gap_classification=gap_classification,
                                hint=hint,
                            )
                        )
                        _increment_priority(priority_breakdown, collection_priority)
                    elif backfill_priority not in _SKIP_PRIORITIES:
                        # never_attempted + critical/high/medium → collect.
                        # derivable_not_derived + critical/high/medium → collect.
                        hint = _build_hint(
                            gap_classification=gap_classification,
                            ticker=firm.ticker,
                            metric=metric,
                            cell=cell,
                        )
                        collection_priority = backfill_priority or "medium"
                        collect_cells.append(
                            _make_collect_cell(
                                firm=firm,
                                metric_id=metric_id,
                                metric=metric,
                                collection_priority=collection_priority,
                                gap_classification=gap_classification,
                                hint=hint,
                            )
                        )
                        _increment_priority(priority_breakdown, collection_priority)
                    else:
                        # Low priority — not collected, treat as skip.
                        skip_cells.append(
                            {
                                "firm_id": firm.firm_id,
                                "ticker": firm.ticker,
                                "metric_id": metric_id,
                                "reason": f"{gap_classification} (priority: {backfill_priority})",
                            }
                        )
                else:
                    # Unknown gap classification — skip conservatively.
                    skip_cells.append(
                        {
                            "firm_id": firm.firm_id,
                            "ticker": firm.ticker,
                            "metric_id": metric_id,
                            "reason": gap_classification or "unknown",
                        }
                    )

    # Build tier-organized collect blocks.
    collect_tiers = _build_collect_tiers(collect_cells, tier1, tier2, tier3, metrics_index)

    spec: dict[str, object] = {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "base_run_dir": str(base_run_dir),
            "new_run_dir": str(new_run_dir),
            "mode": "incremental",
            "total_cells_to_collect": len(collect_cells),
            "total_cells_existing": len(carry_forward_cells),
            "total_cells_skipped_not_disclosed": len(skip_cells),
            "priority_breakdown": priority_breakdown,
        },
        "carry_forward": {
            "description": "These data points are carried forward unchanged from the base run",
            "cells": carry_forward_cells,
        },
        "skip": {
            "description": "These cells are skipped — firm confirmed non-disclosure in base run",
            "cells": skip_cells,
        },
        "collect": {
            "description": "These cells need collection — organized by tier for parallel dispatch",
            **collect_tiers,
        },
    }

    output_dir = new_run_dir / "2-data"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "delta_spec.json"
    _write_json(output_path, spec)

    return {
        "delta_spec_path": str(output_path),
        "total_cells_to_collect": len(collect_cells),
        "total_cells_existing": len(carry_forward_cells),
        "total_cells_skipped": len(skip_cells),
        "priority_breakdown": priority_breakdown,
    }


# ---------------------------------------------------------------------------
# Collect cell helpers
# ---------------------------------------------------------------------------


def _make_collect_cell(
    *,
    firm: FirmRecord,
    metric_id: str,
    metric: MetricRecord,
    collection_priority: str,
    gap_classification: str,
    hint: str,
) -> dict[str, object]:
    return {
        "firm_id": firm.firm_id,
        "ticker": firm.ticker,
        "metric_id": metric_id,
        "metric_name": metric.name,
        "collection_priority": collection_priority,
        "gap_classification": gap_classification,
        "hint": hint,
    }


def _build_hint(
    *,
    gap_classification: str,
    ticker: str,
    metric: MetricRecord,
    cell: dict[str, object],
) -> str:
    if gap_classification == "never_attempted":
        return (
            f"Search {ticker} 10-K, earnings supplement, or investor presentation"
            f" for {metric.name}"
        )
    if gap_classification == "derivable_not_derived":
        notes = metric.calculation_notes or "component inputs"
        return f"Metric may be derivable — search for component inputs: {notes}"
    if gap_classification == "stale":
        as_of = cell.get("as_of", "unknown")
        return f"Update from latest filings — base run had {as_of} data"
    return f"Search for {metric.name} ({gap_classification})"


def _increment_priority(breakdown: dict[str, int], priority: str) -> None:
    if priority in breakdown:
        breakdown[priority] += 1


def _build_collect_tiers(
    collect_cells: list[dict[str, object]],
    tier1: list[FirmRecord],
    tier2: list[FirmRecord],
    tier3: list[FirmRecord],
    metrics_index: dict[str, MetricRecord],
) -> dict[str, object]:
    """Group collect cells by tier and build per-firm assignment blocks."""
    tier1_ids = {f.firm_id for f in tier1}
    tier2_ids = {f.firm_id for f in tier2}
    tier3_ids = {f.firm_id for f in tier3}

    def build_tier_assignments(
        tier_firms: list[FirmRecord],
        tier_firm_ids: set[str],
    ) -> dict[str, object]:
        tier_cells_by_firm: dict[str, list[dict[str, object]]] = {
            f.firm_id: [] for f in tier_firms
        }
        for cell in collect_cells:
            fid = str(cell["firm_id"])
            if fid in tier_firm_ids:
                tier_cells_by_firm[fid].append(cell)

        assignments: list[dict[str, object]] = []
        for firm in tier_firms:
            firm_cells = tier_cells_by_firm[firm.firm_id]
            if not firm_cells:
                continue
            metrics_to_collect: list[dict[str, object]] = [
                {
                    "metric_id": c["metric_id"],
                    "metric_name": c["metric_name"],
                    "collection_priority": c["collection_priority"],
                    "gap_classification": c["gap_classification"],
                    "hint": c["hint"],
                }
                for c in firm_cells
            ]
            assignments.append(
                {
                    "firm_id": firm.firm_id,
                    "ticker": firm.ticker,
                    "metrics_to_collect": metrics_to_collect,
                }
            )

        return {
            "firms": [f.firm_id for f in tier_firms],
            "assignments": assignments,
        }

    return {
        "tier1": build_tier_assignments(tier1, tier1_ids),
        "tier2": build_tier_assignments(tier2, tier2_ids),
        "tier3": build_tier_assignments(tier3, tier3_ids),
    }


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def _load_firms(peer_universe: dict[str, object]) -> list[FirmRecord]:
    """Load and sort firms by AUM descending — delegates to shared utility."""
    return load_firms_from_payload(peer_universe)


def _build_metrics_index(metric_taxonomy: dict[str, object]) -> dict[str, MetricRecord]:
    """Build metric_id → MetricRecord lookup from taxonomy."""
    index: dict[str, MetricRecord] = {}
    for item in metric_taxonomy.get("metrics", []):
        if not isinstance(item, dict):
            continue
        metric_id = str(item.get("metric_id", "")).strip()
        if not metric_id:
            continue
        index[metric_id] = MetricRecord(
            metric_id=metric_id,
            name=str(item.get("name", "")).strip(),
            abbreviation=str(item.get("abbreviation", "")).strip(),
            calculation_notes=str(item.get("calculation_notes", "")).strip(),
        )
    return index


def _index_matrix(
    standardized_matrix: dict[str, object],
) -> dict[tuple[str, str], dict[str, object]]:
    """Return (firm_id, metric_id) → cell dict from the standardized matrix."""
    index: dict[tuple[str, str], dict[str, object]] = {}
    for firm_row in standardized_matrix.get("matrix", []):
        if not isinstance(firm_row, dict):
            continue
        firm_id = str(firm_row.get("firm_id", ""))
        metrics = firm_row.get("metrics", {})
        if not isinstance(metrics, dict):
            continue
        for metric_id, cell in metrics.items():
            if isinstance(cell, dict):
                index[(firm_id, str(metric_id))] = cell
    return index


def _index_gap_detail(
    data_gaps: dict[str, object],
) -> dict[tuple[str, str], dict[str, object]]:
    """Return (firm_id, metric_id) → gap record from the data gaps report.

    Supports both the documented structure (gap_detail key) and the actual
    data_gaps.py output structure (gaps key).
    """
    index: dict[tuple[str, str], dict[str, object]] = {}
    # data_gaps.py outputs "gaps"; the spec documents "gap_detail" — try both.
    records: object = data_gaps.get("gap_detail") or data_gaps.get("gaps") or []
    if not isinstance(records, list):
        return index
    for record in records:
        if not isinstance(record, dict):
            continue
        firm_id = str(record.get("firm_id", ""))
        metric_id = str(record.get("metric_id", ""))
        if firm_id and metric_id:
            index[(firm_id, metric_id)] = record
    return index


# ---------------------------------------------------------------------------
# Tier splitting — delegates to shared utility
# ---------------------------------------------------------------------------


def _split_firms_into_tiers(
    firms: list[FirmRecord],
) -> tuple[list[FirmRecord], list[FirmRecord], list[FirmRecord]]:
    """Split a list pre-sorted by descending AUM into three roughly equal tiers."""
    return _split_firms_into_tiers_shared(firms)


# ---------------------------------------------------------------------------
# Carry-forward merge
# ---------------------------------------------------------------------------


def merge_carry_forward(new_run_dir: Path) -> dict[str, object]:
    """Inject carry-forward data from delta_spec.json into quantitative tier files.

    After data-collector agents write only the NEW data points to tier files,
    this function reads the carry-forward cells from delta_spec.json and merges
    them into each tier file.  Existing data points in the tier files take
    precedence over carry-forward (newly collected data is fresher).

    Returns a summary dict with counts per tier.
    """
    delta_spec_path = new_run_dir / "2-data" / "delta_spec.json"
    if not delta_spec_path.exists():
        return {"error": "delta_spec.json not found", "merged": False}

    spec = _load_json(delta_spec_path)
    carry_cells = spec.get("carry_forward", {}).get("cells", [])
    if not carry_cells:
        return {"merged": True, "carry_forward_cells": 0, "tiers": {}}

    # Build a set of carry-forward data points keyed by (firm_id, metric_id).
    # Convert to the quantitative tier file format: {firm_id, ticker, metric, period, value, unit, ...}
    cf_by_firm: dict[str, list[dict[str, object]]] = {}
    for cell in carry_cells:
        firm_id = str(cell.get("firm_id", ""))
        if firm_id not in cf_by_firm:
            cf_by_firm[firm_id] = []
        cf_by_firm[firm_id].append({
            "firm_id": firm_id,
            "ticker": str(cell.get("ticker", "")),
            "metric_id": str(cell.get("metric_id", "")),
            "value": cell.get("value"),
            "unit": cell.get("unit"),
            "source": str(cell.get("source", "carry-forward from base run")),
            "period": str(cell.get("as_of", "")),
            "confidence": "high",
            "notes": "carry-forward from base run",
        })

    # Determine tier membership from the collect block.
    collect = spec.get("collect", {})
    tier_firms: dict[str, list[str]] = {}
    for tier_name in ("tier1", "tier2", "tier3"):
        tier_block = collect.get(tier_name, {})
        tier_firms[tier_name] = [str(f) for f in tier_block.get("firms", [])]

    # Assign every carry-forward firm to a tier.
    firm_to_tier: dict[str, str] = {}
    for tier_name, firm_ids in tier_firms.items():
        for fid in firm_ids:
            firm_to_tier[fid] = tier_name

    # Fallback: firms not in any tier (all data carry-forward, no collection needed)
    # assign to tier based on position.
    unassigned = [fid for fid in cf_by_firm if fid not in firm_to_tier]
    for fid in unassigned:
        firm_to_tier[fid] = "tier1"  # default to tier1

    tier_file_names = {
        "tier1": "quantitative_tier1.json",
        "tier2": "quantitative_tier2.json",
        "tier3": "quantitative_tier3.json",
    }

    summary: dict[str, object] = {}
    data_dir = new_run_dir / "2-data"
    data_dir.mkdir(parents=True, exist_ok=True)

    for tier_name, filename in tier_file_names.items():
        tier_path = data_dir / filename

        # Load existing tier data (from delta collection) if it exists.
        if tier_path.exists():
            tier_data = _load_json(tier_path)
        else:
            tier_data = {
                "metadata": {
                    "tier": int(tier_name[-1]),
                    "generated_at": datetime.utcnow().strftime("%Y-%m-%d"),
                    "notes": f"Carry-forward merge for {tier_name}",
                },
                "data_points": [],
            }

        existing_points = tier_data.get("data_points", [])

        # Build set of (firm_id, metric_id) already present in newly collected data.
        # Store both metric_id and metric name as keys to handle agents that write
        # either "metric_id" or "metric" (name) in their tier files.
        existing_keys: set[tuple[str, str]] = set()
        for dp in existing_points:
            fid = str(dp.get("firm_id", ""))
            mid = str(dp.get("metric_id", ""))
            mname = str(dp.get("metric", ""))
            if mid:
                existing_keys.add((fid, mid))
            if mname:
                existing_keys.add((fid, mname))

        # Add carry-forward cells for firms in this tier.
        added = 0
        for firm_id, cells in cf_by_firm.items():
            if firm_to_tier.get(firm_id) != tier_name:
                continue
            for cell in cells:
                key = (str(cell["firm_id"]), str(cell["metric_id"]))
                if key not in existing_keys:
                    existing_points.append(cell)
                    existing_keys.add(key)
                    added += 1

        tier_data["data_points"] = existing_points
        _write_json(tier_path, tier_data)
        summary[tier_name] = {"file": str(tier_path), "carry_forward_added": added}

    total_added = sum(int(v["carry_forward_added"]) for v in summary.values())
    return {
        "merged": True,
        "carry_forward_cells": len(carry_cells),
        "newly_injected": total_added,
        "tiers": summary,
    }


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate an incremental delta spec for VDA data collectors using a base run."
    )
    parser.add_argument(
        "--base-run",
        default=None,
        help="Path to the base run directory (e.g. data/processed/pax/2026-03-09-run2/).",
    )
    parser.add_argument(
        "--new-run-dir",
        default=None,
        help="Path to the new run directory where delta_spec.json will be written.",
    )
    parser.add_argument("--data-gaps", default=None)
    parser.add_argument("--peer-universe", default=None)
    parser.add_argument("--metric-taxonomy", default=None)
    parser.add_argument("--standardized-matrix", default=None)
    parser.add_argument(
        "--merge",
        action="store_true",
        help="Merge carry-forward data into quantitative tier files (requires --new-run-dir).",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.merge:
        if not args.new_run_dir:
            parser.error("--merge requires --new-run-dir")
        result = merge_carry_forward(Path(args.new_run_dir).resolve())
        print(json.dumps(result, indent=2))
    elif args.base_run and args.new_run_dir:
        summary = build_delta_spec(args)
        print(json.dumps(summary, indent=2))
    else:
        parser.error("Provide --base-run and --new-run-dir to generate, or --merge --new-run-dir to merge")


if __name__ == "__main__":
    main()
