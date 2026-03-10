"""Generate a per-tier metric checklist for VDA data collectors."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path

from src.analyzer._shared import (
    FirmRecord,
    load_firms_from_payload,
    split_firms_into_tiers,
    utcnow_iso,
)


# Metric names/abbreviations that signal a "high" priority core driver.
# These are checked against the metric name and abbreviation (case-insensitive).
_HIGH_PRIORITY_NAMES: tuple[str, ...] = (
    "de/share",
    "distributable earnings per share",
    "eps",
    "earnings per share",
    "feaum",
    "fee-earning aum",
    "aum",
    "total aum",
    "fre margin",
    "fee-related earnings margin",
    "mgmt fee rate",
    "management fee rate",
    "perm capital",
    "permanent capital",
    "credit %",
    "credit percentage",
    "comp ratio",
    "compensation-to-revenue",
    "perf fee share",
    "performance fee share",
)

# Metric abbreviations/names that are "low" priority (sparse disclosure expected).
_LOW_PRIORITY_NAMES: tuple[str, ...] = (
    "integration/rev",
    "integration costs to revenue",
    "capex/feaum",
    "capex to feaum",
    "cc rev growth",
    "constant currency revenue growth",
)

# Formula-detection pattern: matches calculation formulas found in calculation_notes.
# We distinguish formulas from prose by requiring:
#   - Division "/" where the left operand is a formula token (starts with uppercase
#     or underscore, or contains a digit) — avoids matching "assets/infrastructure".
#   - Multiplication "*" between a formula token and any word.
#   - Space-padded "+" or "-" to avoid matching hyphenated compound words.
# A formula token starts with an uppercase letter or underscore (e.g., "FRE",
# "FEAUM_t", "AUM"), or contains a digit (e.g., "10,000", "t-1").
_FORMULA_OPERAND = r"(?:[A-Z_][A-Za-z0-9_,\.]*|[A-Za-z_]*[0-9][A-Za-z0-9_,\.]*)"
# Right-hand side of division may be any word token (allows "FRE / management fee revenue").
_WORD_TOKEN = r"[A-Za-z_]\w*"
_FORMULA_RE = re.compile(
    r"(?:"
    + _FORMULA_OPERAND + r"\s*/\s*" + _WORD_TOKEN   # division: formula-token / any-word
    + r"|"
    + _FORMULA_OPERAND + r"\s*\*\s*" + r"[\w][A-Za-z0-9_,\.]+"  # multiplication
    + r"|"
    + r"\b[A-Za-z_]\w*\s+[-+]\s+[A-Za-z_]\w*"  # space-padded add/subtract
    + r")"
)


@dataclass(frozen=True)
class MetricRecord:
    metric_id: str
    name: str
    abbreviation: str
    category: str
    is_driver_candidate: bool
    calculation_notes: str


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a per-tier metric checklist for VDA data collectors."
    )
    parser.add_argument(
        "--run-dir",
        required=True,
        help="Path to a VDA run directory (e.g. data/processed/pax/2026-03-09-run2/).",
    )
    parser.add_argument(
        "--peer-universe",
        help="Explicit peer_universe.json path. Defaults to <run-dir>/1-universe/peer_universe.json.",
    )
    parser.add_argument(
        "--metric-taxonomy",
        help="Explicit metric_taxonomy.json path. Defaults to <run-dir>/1-universe/metric_taxonomy.json.",
    )
    parser.add_argument(
        "--output-dir",
        help="Output directory. Defaults to <run-dir>/2-data/.",
    )
    return parser


def generate_checklist(args: argparse.Namespace) -> dict[str, object]:
    run_dir = Path(args.run_dir)

    peer_universe_path = (
        Path(args.peer_universe)
        if args.peer_universe
        else run_dir / "1-universe" / "peer_universe.json"
    )
    metric_taxonomy_path = (
        Path(args.metric_taxonomy)
        if args.metric_taxonomy
        else run_dir / "1-universe" / "metric_taxonomy.json"
    )
    output_dir = Path(args.output_dir) if args.output_dir else run_dir / "2-data"
    output_dir.mkdir(parents=True, exist_ok=True)

    firms = load_firms(peer_universe_path)
    metrics = load_metrics(metric_taxonomy_path)

    tier1, tier2, tier3 = split_firms_into_tiers(firms)

    driver_metrics = [m for m in metrics if m.is_driver_candidate]

    checklist: dict[str, object] = {
        "metadata": {
            "generated_at": utcnow_iso(),
            "run_dir": str(run_dir),
            "total_firms": len(firms),
            "total_metrics": len(metrics),
            "driver_metrics": len(driver_metrics),
            "tiers": {
                "tier1": len(tier1),
                "tier2": len(tier2),
                "tier3": len(tier3),
            },
        },
        "priority_rules": {
            "critical": "Valuation multiples — must populate for correlation analysis",
            "high": "Core driver metrics with expected >60% disclosure rate",
            "medium": "Derivable from components — search for inputs even if ratio not disclosed",
            "low": "Sparse disclosure expected — attempt but do not block on failure",
            "skip": "Market structure / contextual-only — excluded from correlation",
        },
        "tiers": {
            "tier1": build_tier_block(tier1, metrics),
            "tier2": build_tier_block(tier2, metrics),
            "tier3": build_tier_block(tier3, metrics),
        },
    }

    output_path = output_dir / "metric_checklist.json"
    _write_json(output_path, checklist)
    return {"checklist_path": str(output_path), "total_firms": len(firms), "total_metrics": len(metrics)}


def load_firms(path: Path) -> list[FirmRecord]:
    payload = _load_json(path)
    return load_firms_from_payload(payload)


def load_metrics(path: Path) -> list[MetricRecord]:
    payload = _load_json(path)
    metrics: list[MetricRecord] = []
    for item in payload.get("metrics", []):
        metrics.append(
            MetricRecord(
                metric_id=str(item.get("metric_id", "")).strip(),
                name=str(item.get("name", "")).strip(),
                abbreviation=str(item.get("abbreviation", "")).strip(),
                category=str(item.get("category", "")).strip(),
                is_driver_candidate=bool(item.get("is_driver_candidate", False)),
                calculation_notes=str(item.get("calculation_notes", "")).strip(),
            )
        )
    return metrics



def assign_collection_priority(metric: MetricRecord) -> str:
    """Return the collection priority label for a single metric."""
    # Skip: market structure metrics are excluded from correlation entirely.
    if metric.category == "market_structure":
        return "skip"

    # Critical: valuation multiples (is_driver_candidate=False with "multiple" unit
    # or name containing "P/" or "EV/").
    if not metric.is_driver_candidate:
        name_lower = metric.name.lower()
        abbrev_lower = metric.abbreviation.lower()
        unit_lower = (metric.calculation_notes or "").lower()
        if (
            "p/" in abbrev_lower
            or "ev/" in abbrev_lower
            or "p/fre" in name_lower
            or "p/de" in name_lower
            or "multiple" in unit_lower
            or metric.category == "valuation_multiples"
        ):
            return "critical"
        # Non-driver-candidate but not valuation multiple — treat as skip.
        return "skip"

    name_lower = metric.name.lower()
    abbrev_lower = metric.abbreviation.lower()

    # Low: operational feasibility metrics with sparse expected disclosure.
    for pattern in _LOW_PRIORITY_NAMES:
        if pattern in name_lower or pattern in abbrev_lower:
            return "low"

    # High: core driver metrics expected to have >60% disclosure.
    # Checked before medium so named high-priority metrics are not demoted.
    for pattern in _HIGH_PRIORITY_NAMES:
        if pattern in name_lower or pattern in abbrev_lower:
            return "high"

    # Medium: derivable metrics — has a formula-like expression in calculation_notes.
    if extract_derivable_formula(metric.calculation_notes) is not None:
        return "medium"

    # Default for remaining driver candidates: medium.
    return "medium"


def extract_derivable_formula(calculation_notes: str) -> str | None:
    """
    Return a formula string if calculation_notes contains an arithmetic expression,
    otherwise return None.
    """
    if not calculation_notes:
        return None
    # Look for a pattern that resembles a formula: token op token (with possible spaces).
    match = _FORMULA_RE.search(calculation_notes)
    if match:
        # Walk forward from the match start to collect the full formula up to a period
        # or parenthesis that closes the expression.
        start = match.start()
        # Extract a reasonable window (up to 120 chars) and stop at the first
        # sentence terminator to keep the formula clean.
        window = calculation_notes[start : start + 120]
        # Trim at first period followed by space/end, or at first closing paren group.
        trimmed = re.split(r"\.\s", window, maxsplit=1)[0].strip()
        return trimmed
    return None


def build_tier_block(
    tier_firms: list[FirmRecord], metrics: list[MetricRecord]
) -> dict[str, object]:
    """Build the checklist block for a single tier."""
    # Pre-compute priority and formula per metric (metric-only, firm-independent).
    priority_cache: dict[str, str] = {}
    formula_cache: dict[str, str | None] = {}
    for m in metrics:
        priority_cache[m.metric_id] = assign_collection_priority(m)
        formula_cache[m.metric_id] = (
            extract_derivable_formula(m.calculation_notes)
            if priority_cache[m.metric_id] == "medium"
            else None
        )
    return {
        "firms": [f.firm_id for f in tier_firms],
        "checklist": [
            build_firm_checklist(firm, metrics, priority_cache, formula_cache)
            for firm in tier_firms
        ],
    }


def build_firm_checklist(
    firm: FirmRecord,
    metrics: list[MetricRecord],
    priority_cache: dict[str, str] | None = None,
    formula_cache: dict[str, str | None] | None = None,
) -> dict[str, object]:
    """Build the metric checklist entry for a single firm.

    priority_cache and formula_cache are optional pre-computed lookups from
    build_tier_block. When omitted (direct calls from tests), priorities are
    computed inline as before.
    """
    metric_entries: list[dict[str, object]] = []
    for metric in metrics:
        if priority_cache is not None:
            priority = priority_cache[metric.metric_id]
            derivable = formula_cache[metric.metric_id] if formula_cache is not None else None
        else:
            priority = assign_collection_priority(metric)
            derivable = extract_derivable_formula(metric.calculation_notes) if priority == "medium" else None
        metric_entries.append(
            {
                "metric_id": metric.metric_id,
                "metric_name": metric.name,
                "category": metric.category,
                "collection_priority": priority,
                "derivable_from": derivable,
                "status": "pending",
            }
        )
    return {
        "firm_id": firm.firm_id,
        "ticker": firm.ticker,
        "metrics": metric_entries,
    }


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    summary = generate_checklist(args)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
