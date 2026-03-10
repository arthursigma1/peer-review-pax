"""Analyze the standardized matrix and produce a data gap report for targeted backfill."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path


# Missing-reason strings that indicate the firm was never attempted for this metric.
_NEVER_ATTEMPTED_PATTERNS = frozenset({
    "not collected or not disclosed",
    "not calculated",
    "not disclosed or not calculable",
    "contextual metric not collected",
})

# Missing-reason strings where the firm is known not to report this metric.
_NOT_DISCLOSED_PATTERNS = frozenset({
    "GAAP EPS not collected or not applicable",
    "asset class breakdown not available for HHI computation",
    "organic growth decomposition not available from public sources for most firms",
    "fundraising as % of AUM not standardized across universe",
    "permanent capital percentage not disclosed or not collected",
    "credit AUM percentage not separately confirmed",
    "performance fee share not standardized across universe",
    "comp-to-revenue not collected at standardized level",
    "insufficient data for fee rate calculation",
    "FRE margin not available",
    "FRE growth not calculable",
    "insufficient DE/share history for 3-year CAGR",
    "insufficient FEAUM history for 3-year CAGR",
    "insufficient FEAUM data for YoY calculation",
    "FEAUM not separately disclosed",
    "AUM not available",
    "headcount or FEAUM not available",
})

# Pre-computed lowercase versions of pattern sets for O(1) membership testing.
_NEVER_ATTEMPTED_PATTERNS_LOWER = frozenset(r.lower() for r in _NEVER_ATTEMPTED_PATTERNS)
_NOT_DISCLOSED_PATTERNS_LOWER = frozenset(r.lower() for r in _NOT_DISCLOSED_PATTERNS)

# Correlation threshold: 60% of total firms.
COVERAGE_THRESHOLD_PCT = 0.60

# Market structure category — always skip.
_MARKET_STRUCTURE_CATEGORY = "market_structure"

# How far back from run date before a value is "stale" (6 months).
_STALE_MONTHS = 6

# Canonical component metric IDs referenced in calculation formulas.
# Keyed by metric_id → list of component metric_ids required to derive it.
# Derived from reading calculation_notes in metric_taxonomy.json.
_DERIVATION_COMPONENTS: dict[str, list[str]] = {
    # FRE margin = FRE / mgmt fee revenue.  FRE growth (MET-VD-014) is a proxy
    # for FRE availability.  If FRE growth exists, FRE exists.
    "MET-VD-013": ["MET-VD-014"],
    # FRE growth YoY requires FRE to exist at two time points — proxied by FEAUM
    # and FRE margin both present.
    "MET-VD-014": ["MET-VD-004"],
    # DE growth 3yr needs DE/share (MET-VD-001) to exist.
    "MET-VD-003": ["MET-VD-001"],
    # FEAUM 3yr CAGR needs FEAUM YoY (MET-VD-006) — a proxy for multi-year data.
    "MET-VD-007": ["MET-VD-006"],
    # FEAUM per employee is the inverse of Headcount/FEAUM.
    "MET-VD-019": ["MET-VD-018"],
    # Headcount/FEAUM requires FEAUM.
    "MET-VD-018": ["MET-VD-004"],
    # Comp & Benefits / FEAUM requires FEAUM.
    "MET-VD-020": ["MET-VD-004"],
    # G&A / FEAUM requires FEAUM.
    "MET-VD-021": ["MET-VD-004"],
    # OpEx-Rev growth gap requires FEAUM YoY as a proxy for revenue data.
    "MET-VD-022": ["MET-VD-006"],
    # Management fee rate = mgmt fee revenue / FEAUM * bps.
    # Proxied by FEAUM existing.
    "MET-VD-016": ["MET-VD-004"],
    # HHI requires asset class breakdown — proxied by FEAUM.
    "MET-VD-010": ["MET-VD-004"],
    # Permanent capital % requires AUM breakdown.
    "MET-VD-011": ["MET-VD-005"],
    # Credit % requires AUM breakdown.
    "MET-VD-012": ["MET-VD-005"],
    # Fundraising ratio = capital raised / AUM.
    "MET-VD-009": ["MET-VD-005"],
    # Performance fee share requires revenue decomposition (proxied by DE/share).
    "MET-VD-017": ["MET-VD-001"],
    # Comp-to-revenue requires both compensation expense and revenue data.
    "MET-VD-015": ["MET-VD-004"],
}


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def analyze_data_gaps(run_dir: Path) -> dict[str, object]:
    """Read the standardized matrix for *run_dir* and return a gap report dict."""
    matrix_path = run_dir / "3-analysis" / "standardized_matrix.json"
    taxonomy_path = run_dir / "1-universe" / "metric_taxonomy.json"

    matrix_data = _load_json(matrix_path)
    taxonomy_data = _load_json(taxonomy_path)

    run_id = _parse_run_id(run_dir)
    run_date = _parse_run_date(run_id)

    metrics_index = _build_metrics_index(taxonomy_data)
    driver_metric_ids = [mid for mid, meta in metrics_index.items() if meta["is_driver"]]
    firms = matrix_data["matrix"]
    total_firms = len(firms)
    total_driver_metrics = len(driver_metric_ids)
    total_cells = total_firms * total_driver_metrics
    coverage_threshold = int(total_firms * COVERAGE_THRESHOLD_PCT)

    # Per-firm lookup: firm_id → {metric_id: cell}
    firm_data: dict[str, dict[str, dict[str, object]]] = {}
    firm_ticker: dict[str, str] = {}
    for firm in firms:
        firm_id = str(firm["firm_id"])
        ticker = str(firm.get("ticker", ""))
        firm_data[firm_id] = {mid: cell for mid, cell in firm["metrics"].items()}
        firm_ticker[firm_id] = ticker

    # Classify every (firm, driver_metric) gap.
    gap_records: list[dict[str, object]] = []
    filled_cells = 0
    stale_cells = 0

    # Track per-metric filled counts for coverage stats.
    metric_filled_counts: dict[str, int] = defaultdict(int)
    metric_gap_type_counts: dict[str, dict[str, int]] = {
        mid: {"never_attempted": 0, "not_disclosed": 0, "derivable_not_derived": 0, "stale": 0}
        for mid in driver_metric_ids
    }

    for firm_id, ticker in firm_ticker.items():
        firm_cells = firm_data[firm_id]
        for metric_id in driver_metric_ids:
            meta = metrics_index[metric_id]
            cell = firm_cells.get(metric_id, {})
            value = cell.get("value")
            missing_reason = str(cell.get("missing_reason", "")).strip()
            as_of = str(cell.get("as_of", "")).strip()

            if value is not None:
                # A cell with a value always counts as filled (for coverage/correlation purposes).
                filled_cells += 1
                metric_filled_counts[metric_id] += 1
                # Additionally flag as stale when the data is older than 6 months.
                if _is_stale(as_of, run_date):
                    stale_cells += 1
                    metric_gap_type_counts[metric_id]["stale"] += 1
                    gap_records.append(
                        _make_gap_record(
                            firm_id=firm_id,
                            ticker=ticker,
                            metric_id=metric_id,
                            metric_name=meta["name"],
                            gap_type="stale",
                            missing_reason=f"Value exists but as_of '{as_of}' is >6 months before {run_date}",
                            derivable_from=None,
                        )
                    )
            else:
                # Null cell — classify the gap type.
                gap_type, derivable_from = _classify_gap(
                    metric_id=metric_id,
                    missing_reason=missing_reason,
                    firm_id=firm_id,
                    firm_cells=firm_cells,
                )
                metric_gap_type_counts[metric_id][gap_type] += 1
                gap_records.append(
                    _make_gap_record(
                        firm_id=firm_id,
                        ticker=ticker,
                        metric_id=metric_id,
                        metric_name=meta["name"],
                        gap_type=gap_type,
                        missing_reason=missing_reason or "not recorded",
                        derivable_from=derivable_from,
                    )
                )

    null_cells = total_cells - filled_cells
    fill_rate_pct = round(filled_cells / total_cells * 100, 1) if total_cells else 0.0

    # Second pass: patch metric_filled_count and high_impact into gap records.
    for record in gap_records:
        mid = str(record["metric_id"])
        filled = metric_filled_counts[mid]
        record["_filled"] = filled  # temporary — removed below

    # Build metric_coverage list.
    metric_coverage: list[dict[str, object]] = []
    for metric_id in driver_metric_ids:
        meta = metrics_index[metric_id]
        firms_with_data = metric_filled_counts[metric_id]
        coverage_pct = round(firms_with_data / total_firms * 100, 1) if total_firms else 0.0
        above_threshold = firms_with_data >= coverage_threshold
        gap_to_threshold = max(0, coverage_threshold - firms_with_data)
        metric_coverage.append(
            {
                "metric_id": metric_id,
                "metric_name": meta["name"],
                "category": meta["category"],
                "is_driver": True,
                "firms_with_data": firms_with_data,
                "firms_total": total_firms,
                "coverage_pct": coverage_pct,
                "above_correlation_threshold": above_threshold,
                "gap_to_threshold": gap_to_threshold,
                "gap_types": metric_gap_type_counts[metric_id],
            }
        )

    # Build firm_coverage list.
    firm_coverage: list[dict[str, object]] = []
    for firm in firms:
        firm_id = str(firm["firm_id"])
        ticker = firm_ticker[firm_id]
        filled = sum(
            1
            for mid in driver_metric_ids
            if firm_data[firm_id].get(mid, {}).get("value") is not None
        )
        coverage_pct = round(filled / total_driver_metrics * 100, 1) if total_driver_metrics else 0.0
        firm_coverage.append(
            {
                "firm_id": firm_id,
                "ticker": ticker,
                "metrics_with_data": filled,
                "metrics_total": total_driver_metrics,
                "coverage_pct": coverage_pct,
            }
        )

    # Build high-impact backfill targets.
    high_impact_targets = _build_high_impact_targets(
        metric_coverage=metric_coverage,
        gap_records=gap_records,
        coverage_threshold=coverage_threshold,
        driver_metric_ids=driver_metric_ids,
    )

    # Mark high_impact on gap records and assign backfill_priority.
    high_impact_metric_ids = {t["metric_id"] for t in high_impact_targets}
    for record in gap_records:
        mid = str(record["metric_id"])
        record["high_impact"] = mid in high_impact_metric_ids
        record["backfill_priority"] = _assign_priority(record=record, meta=metrics_index[mid])
        del record["_filled"]

    # Summary block.
    above_threshold = sum(1 for mc in metric_coverage if mc["above_correlation_threshold"])
    below_threshold = sum(1 for mc in metric_coverage if not mc["above_correlation_threshold"])
    zero_coverage = sum(1 for mc in metric_coverage if mc["firms_with_data"] == 0)

    if zero_coverage > 0 or below_threshold > above_threshold:
        recommended_action = "backfill_critical"
    elif below_threshold > 0:
        recommended_action = "proceed_with_warning"
    else:
        recommended_action = "sufficient_coverage"

    report = {
        "metadata": {
            "pipeline": "VDA",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "run_id": run_id,
            "total_firms": total_firms,
            "total_driver_metrics": total_driver_metrics,
            "total_cells": total_cells,
            "filled_cells": filled_cells,
            "null_cells": null_cells,
            "fill_rate_pct": fill_rate_pct,
            "stale_cells": stale_cells,
            "coverage_threshold_pct": int(COVERAGE_THRESHOLD_PCT * 100),
            "coverage_threshold_firms": coverage_threshold,
        },
        "metric_coverage": metric_coverage,
        "firm_coverage": firm_coverage,
        "gaps": gap_records,
        "high_impact_backfill_targets": high_impact_targets,
        "summary": {
            "metrics_above_threshold": above_threshold,
            "metrics_below_threshold": below_threshold,
            "metrics_zero_coverage": zero_coverage,
            "recommended_action": recommended_action,
        },
    }
    return report


# ---------------------------------------------------------------------------
# Gap classification helpers
# ---------------------------------------------------------------------------


def _classify_gap(
    *,
    metric_id: str,
    missing_reason: str,
    firm_id: str,
    firm_cells: dict[str, dict[str, object]],
) -> tuple[str, list[str] | None]:
    """Return (gap_type, derivable_from) for a null cell."""
    # Check if reason matches a "not disclosed" pattern.
    if _matches_not_disclosed(missing_reason):
        # Even if not_disclosed, check whether it's derivable from components.
        derivable_from = _check_derivable(metric_id=metric_id, firm_cells=firm_cells)
        if derivable_from:
            return "derivable_not_derived", derivable_from
        return "not_disclosed", None

    # Even if reason says never attempted, still check derivability — a metric
    # is derivable_not_derived regardless of the collection reason.
    derivable_from = _check_derivable(metric_id=metric_id, firm_cells=firm_cells)
    if derivable_from:
        return "derivable_not_derived", derivable_from

    # Check if it was never attempted (generic "not collected" language).
    if _matches_never_attempted(missing_reason):
        return "never_attempted", None

    # Default: treat as never_attempted if we have no other signal.
    return "never_attempted", None


def _matches_never_attempted(reason: str) -> bool:
    return reason.lower() in _NEVER_ATTEMPTED_PATTERNS_LOWER


def _matches_not_disclosed(reason: str) -> bool:
    return reason.lower() in _NOT_DISCLOSED_PATTERNS_LOWER


def _check_derivable(*, metric_id: str, firm_cells: dict[str, dict[str, object]]) -> list[str] | None:
    """Return list of component metric IDs if this metric is derivable, else None."""
    components = _DERIVATION_COMPONENTS.get(metric_id)
    if not components:
        return None
    # All components must have non-null values for this firm.
    available = []
    for comp_id in components:
        comp_cell = firm_cells.get(comp_id, {})
        if comp_cell.get("value") is not None:
            available.append(comp_id)
    if len(available) == len(components):
        return available
    return None



# ---------------------------------------------------------------------------
# Staleness
# ---------------------------------------------------------------------------


def _is_stale(as_of: str, run_date: date) -> bool:
    """Return True if the as_of date is more than 6 months before run_date."""
    if not as_of:
        return False
    parsed = _parse_as_of_date(as_of)
    if parsed is None:
        return False
    cutoff = run_date - timedelta(days=_STALE_MONTHS * 30)
    return parsed < cutoff


def _parse_as_of_date(as_of: str) -> date | None:
    """Parse an as_of string like 'FY2024', 'Q3 2023', 'FY2023' → approximate date."""
    as_of_clean = as_of.strip()
    # FY2024 → December 31, 2024
    fy_match = re.match(r"^FY(\d{4})$", as_of_clean, re.IGNORECASE)
    if fy_match:
        year = int(fy_match.group(1))
        return date(year, 12, 31)
    # Q3 2023 or Q3/2023 → September 30
    q_match = re.match(r"^Q([1-4])[\s/](\d{4})$", as_of_clean, re.IGNORECASE)
    if q_match:
        quarter = int(q_match.group(1))
        year = int(q_match.group(2))
        quarter_end_months = {1: 3, 2: 6, 3: 9, 4: 12}
        month = quarter_end_months[quarter]
        return date(year, month, 30 if month in {6, 9} else 31)
    # ISO date: 2024-12-31
    iso_match = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", as_of_clean)
    if iso_match:
        try:
            return date(int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3)))
        except ValueError:
            return None
    # Year only: 2024
    year_match = re.match(r"^(\d{4})$", as_of_clean)
    if year_match:
        return date(int(year_match.group(1)), 12, 31)
    return None


# ---------------------------------------------------------------------------
# Backfill priority
# ---------------------------------------------------------------------------


def _assign_priority(*, record: dict[str, object], meta: dict[str, object]) -> str:
    """Return a backfill_priority label for a gap record."""
    category = str(meta.get("category", ""))
    gap_type = str(record.get("gap_type", ""))
    high_impact = bool(record.get("high_impact", False))
    derivable_from = record.get("derivable_from")

    if category == _MARKET_STRUCTURE_CATEGORY:
        return "skip"

    if not meta.get("is_driver", False):
        return "low"

    if high_impact:
        if gap_type in {"never_attempted", "derivable_not_derived"}:
            return "critical"
        return "high"

    if gap_type in {"never_attempted", "derivable_not_derived"}:
        return "high"

    if gap_type == "not_disclosed" and derivable_from:
        return "medium"

    return "low"


# ---------------------------------------------------------------------------
# High-impact target detection
# ---------------------------------------------------------------------------


def _build_high_impact_targets(
    *,
    metric_coverage: list[dict[str, object]],
    gap_records: list[dict[str, object]],
    coverage_threshold: int,
    driver_metric_ids: list[str],
) -> list[dict[str, object]]:
    """Identify metrics where backfilling N cells would cross (or already exceeds) the 60% threshold."""
    # Only consider driver metrics below threshold OR already above but with actionable gaps.
    targets: list[dict[str, object]] = []
    coverage_by_metric = {mc["metric_id"]: mc for mc in metric_coverage}

    for metric_id in driver_metric_ids:
        mc = coverage_by_metric.get(metric_id)
        if mc is None:
            continue

        current = int(mc["firms_with_data"])
        target = coverage_threshold
        already_above = current >= target

        # Collect actionable gap firms for this metric (never_attempted or derivable_not_derived).
        actionable_gaps = [
            r for r in gap_records
            if str(r["metric_id"]) == metric_id
            and r.get("gap_type") in {"never_attempted", "derivable_not_derived"}
        ]

        # Only include if: below threshold AND there are actionable gaps, OR above threshold
        # but there are still actionable gaps that improve reliability.
        if not already_above and not actionable_gaps:
            continue
        if already_above and not actionable_gaps:
            continue

        firms_to_backfill = [str(r["firm_id"]) for r in actionable_gaps]

        if already_above:
            reason = "Already above threshold but backfill improves correlation reliability"
        else:
            needed = target - current
            reason = (
                f"Backfilling {needed} more cell(s) would cross the {int(COVERAGE_THRESHOLD_PCT*100)}% "
                f"threshold (need {target}, have {current})"
            )

        targets.append(
            {
                "metric_id": metric_id,
                "metric_name": mc["metric_name"],
                "current_coverage": current,
                "target_coverage": target,
                "already_above_threshold": already_above,
                "firms_to_backfill": firms_to_backfill,
                "reason": reason,
            }
        )

    return targets


# ---------------------------------------------------------------------------
# Gap record builder
# ---------------------------------------------------------------------------


def _make_gap_record(
    *,
    firm_id: str,
    ticker: str,
    metric_id: str,
    metric_name: str,
    gap_type: str,
    missing_reason: str,
    derivable_from: list[str] | None,
) -> dict[str, object]:
    return {
        "firm_id": firm_id,
        "ticker": ticker,
        "metric_id": metric_id,
        "metric_name": metric_name,
        "gap_type": gap_type,
        "missing_reason": missing_reason,
        "high_impact": False,  # patched later
        "derivable_from": derivable_from,
        "backfill_priority": "low",  # patched later
    }


# ---------------------------------------------------------------------------
# Index helpers
# ---------------------------------------------------------------------------


def _build_metrics_index(taxonomy_data: dict[str, object]) -> dict[str, dict[str, object]]:
    """Return a dict metric_id → {name, category, is_driver} from taxonomy."""
    index: dict[str, dict[str, object]] = {}
    for metric in taxonomy_data.get("metrics", []):
        if not isinstance(metric, dict):
            continue
        metric_id = str(metric.get("metric_id", ""))
        if not metric_id:
            continue
        index[metric_id] = {
            "name": str(metric.get("name", "")),
            "abbreviation": str(metric.get("abbreviation", "")),
            "category": str(metric.get("category", "")),
            "is_driver": bool(metric.get("is_driver_candidate", False)),
        }
    return index


# ---------------------------------------------------------------------------
# Run-id / date parsing
# ---------------------------------------------------------------------------


def _parse_run_id(run_dir: Path) -> str:
    """Extract the run_id from the run directory path (last component)."""
    return run_dir.name


def _parse_run_date(run_id: str) -> date:
    """Extract the date from a run_id like '2026-03-09' or '2026-03-09-run2'."""
    match = re.match(r"^(\d{4}-\d{2}-\d{2})", run_id)
    if match:
        return date.fromisoformat(match.group(1))
    raise ValueError(f"Cannot parse date from run_id: {run_id!r}")


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
        description="Analyze the standardized matrix and produce a data gap report for targeted backfill."
    )
    parser.add_argument(
        "--run-dir",
        required=True,
        type=Path,
        help="Path to the VDA run directory (e.g. data/processed/pax/2026-03-09-run2/).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output path for data_gaps.json. Defaults to <run-dir>/3-analysis/data_gaps.json.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    run_dir: Path = args.run_dir.resolve()
    output_path: Path = args.output or (run_dir / "3-analysis" / "data_gaps.json")

    report = analyze_data_gaps(run_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(output_path, report)

    meta = report["metadata"]
    summary = report["summary"]
    print(
        f"Data gap report written to {output_path}\n"
        f"  Firms: {meta['total_firms']}  |  Driver metrics: {meta['total_driver_metrics']}\n"
        f"  Total cells: {meta['total_cells']}  |  Filled: {meta['filled_cells']}  "
        f"|  Fill rate: {meta['fill_rate_pct']}%  |  Stale: {meta['stale_cells']}\n"
        f"  Metrics above 60% threshold: {summary['metrics_above_threshold']}  "
        f"|  Below: {summary['metrics_below_threshold']}  "
        f"|  Zero coverage: {summary['metrics_zero_coverage']}\n"
        f"  Recommended action: {summary['recommended_action']}"
    )


if __name__ == "__main__":
    main()
