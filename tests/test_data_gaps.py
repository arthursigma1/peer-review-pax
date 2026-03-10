"""Tests for src/analyzer/data_gaps.py — gap classification, priority, and pipeline integration."""

from __future__ import annotations

import json
import unittest
from datetime import date
from pathlib import Path

import pytest

from src.analyzer.data_gaps import (
    COVERAGE_THRESHOLD_PCT,
    _DERIVATION_COMPONENTS,
    _NOT_DISCLOSED_PATTERNS,
    _assign_priority,
    _build_high_impact_targets,
    _build_metrics_index,
    _check_derivable,
    _classify_gap,
    _is_stale,
    _matches_never_attempted,
    _matches_not_disclosed,
    _parse_as_of_date,
    _parse_run_date,
    _write_json,
    analyze_data_gaps,
)


# ---------------------------------------------------------------------------
# Helpers for building synthetic fixtures
# ---------------------------------------------------------------------------


def _make_taxonomy(metrics: list[dict]) -> dict:
    return {"metrics": metrics}


def _make_metric_entry(
    metric_id: str,
    name: str,
    category: str = "earnings",
    is_driver_candidate: bool = True,
    calculation_notes: str = "",
) -> dict:
    return {
        "metric_id": metric_id,
        "name": name,
        "abbreviation": name[:6],
        "category": category,
        "is_driver_candidate": is_driver_candidate,
        "calculation_notes": calculation_notes,
    }


def _make_matrix(firms: list[dict]) -> dict:
    return {
        "metadata": {"firms": len(firms), "metrics": 4, "metrics_with_data": 2},
        "matrix": firms,
    }


def _make_firm(firm_id: str, ticker: str, metrics: dict) -> dict:
    return {"firm_id": firm_id, "ticker": ticker, "metrics": metrics}


def _make_cell(
    value,
    unit: str = "USD",
    missing_reason: str | None = None,
    as_of: str = "FY2024",
) -> dict:
    cell: dict = {"unit": unit}
    if value is not None:
        cell["value"] = value
        cell["as_of"] = as_of
    else:
        cell["value"] = None
        if missing_reason is not None:
            cell["missing_reason"] = missing_reason
    return cell


def _write_run(tmp_path: Path, taxonomy: dict, matrix: dict) -> Path:
    """Write synthetic run files under tmp_path and return the run_dir."""
    run_dir = tmp_path / "2026-03-09-synth"
    (run_dir / "1-universe").mkdir(parents=True)
    (run_dir / "3-analysis").mkdir(parents=True)

    (run_dir / "1-universe" / "metric_taxonomy.json").write_text(
        json.dumps(taxonomy), encoding="utf-8"
    )
    (run_dir / "3-analysis" / "standardized_matrix.json").write_text(
        json.dumps(matrix), encoding="utf-8"
    )
    return run_dir


def _make_driver_meta(category: str = "efficiency") -> dict:
    return {"is_driver": True, "category": category}


def _make_gap_record(
    gap_type: str = "never_attempted",
    high_impact: bool = False,
    derivable_from: list | None = None,
) -> dict:
    return {
        "gap_type": gap_type,
        "high_impact": high_impact,
        "derivable_from": derivable_from,
    }


def _make_coverage(
    metric_id: str,
    metric_name: str,
    firms_with_data: int,
    total_firms: int,
) -> dict:
    threshold = int(total_firms * COVERAGE_THRESHOLD_PCT)
    fill_pct = round(firms_with_data / total_firms * 100, 1) if total_firms else 0.0
    return {
        "metric_id": metric_id,
        "metric_name": metric_name,
        "firms_with_data": firms_with_data,
        "firms_total": total_firms,
        "coverage_pct": fill_pct,
        "above_correlation_threshold": firms_with_data >= threshold,
        "gap_to_threshold": max(0, threshold - firms_with_data),
    }


def _make_gap_for_metric(firm_id: str, metric_id: str, gap_type: str) -> dict:
    return {
        "firm_id": firm_id,
        "metric_id": metric_id,
        "gap_type": gap_type,
    }


# ---------------------------------------------------------------------------
# 1. Gap classification — each of the 4 types
# ---------------------------------------------------------------------------


class TestGapClassificationUnit(unittest.TestCase):
    """Unit tests for _classify_gap and its helper matchers."""

    def _all_null_cells(self) -> dict[str, dict[str, object]]:
        """Return a minimal firm_cells dict with nulls everywhere."""
        return {
            f"MET-VD-{i:03d}": {"value": None, "missing_reason": "not collected or not disclosed"}
            for i in range(1, 32)
        }

    def test_never_attempted_when_missing_reason_is_empty(self) -> None:
        cells: dict = {"MET-A": {"value": None}}
        gap_type, derivable = _classify_gap(
            metric_id="MET-A",
            missing_reason="",

            firm_id="FIRM-001",
            firm_cells=cells,
        )
        self.assertEqual(gap_type, "never_attempted")
        self.assertIsNone(derivable)

    def test_never_attempted_on_generic_not_collected_reason(self) -> None:
        cells = self._all_null_cells()
        gap_type, derivable = _classify_gap(
            metric_id="MET-VD-020",
            missing_reason="not collected or not disclosed",

            firm_id="FIRM-001",
            firm_cells=cells,
        )
        self.assertEqual(gap_type, "never_attempted")
        self.assertIsNone(derivable)

    def test_not_disclosed_on_known_reason_pattern(self) -> None:
        reason = next(iter(_NOT_DISCLOSED_PATTERNS))
        cells: dict = {"MET-A": {"value": None}}
        gap_type, derivable = _classify_gap(
            metric_id="MET-A",
            missing_reason=reason,

            firm_id="FIRM-001",
            firm_cells=cells,
        )
        self.assertEqual(gap_type, "not_disclosed")
        self.assertIsNone(derivable)

    def test_not_disclosed_on_gaap_eps_reason(self) -> None:
        cells = self._all_null_cells()
        gap_type, derivable = _classify_gap(
            metric_id="MET-VD-002",
            missing_reason="GAAP EPS not collected or not applicable",

            firm_id="FIRM-001",
            firm_cells=cells,
        )
        self.assertEqual(gap_type, "not_disclosed")

    def test_derivable_not_derived_when_components_present(self) -> None:
        # MET-VD-003 (DE growth 3yr) needs MET-VD-001 (DE/share) to be present.
        cells = self._all_null_cells()
        cells["MET-VD-001"] = {"value": 4.64, "unit": "USD", "as_of": "FY2024"}
        gap_type, derivable = _classify_gap(
            metric_id="MET-VD-003",
            missing_reason="insufficient DE/share history for 3-year CAGR",

            firm_id="FIRM-001",
            firm_cells=cells,
        )
        self.assertEqual(gap_type, "derivable_not_derived")
        self.assertIn("MET-VD-001", derivable)

    def test_not_disclosed_when_component_is_absent(self) -> None:
        # MET-VD-003 needs MET-VD-001, which is null → not derivable.
        cells = self._all_null_cells()
        # MET-VD-001 remains null from _all_null_cells
        gap_type, derivable = _classify_gap(
            metric_id="MET-VD-003",
            missing_reason="insufficient DE/share history for 3-year CAGR",

            firm_id="FIRM-001",
            firm_cells=cells,
        )
        self.assertEqual(gap_type, "not_disclosed")
        self.assertIsNone(derivable)

    def test_never_attempted_promoted_to_derivable_when_components_present(self) -> None:
        # No recognized missing_reason, but MET-VD-001 is present → derivable.
        cells = self._all_null_cells()
        cells["MET-VD-001"] = {"value": 3.5, "unit": "USD", "as_of": "FY2024"}
        gap_type, derivable = _classify_gap(
            metric_id="MET-VD-003",
            missing_reason="",

            firm_id="FIRM-001",
            firm_cells=cells,
        )
        self.assertEqual(gap_type, "derivable_not_derived")
        self.assertIn("MET-VD-001", derivable)

    def test_derivable_when_inverse_metric_present(self) -> None:
        """MET-VD-019 (FEAUM per Employee) is derivable when MET-VD-018 (Headcount/FEAUM) exists."""
        cells = self._all_null_cells()
        cells["MET-VD-018"] = {"value": 5.9, "unit": "per USD bn", "as_of": "FY2024"}
        gap_type, derivable = _classify_gap(
            metric_id="MET-VD-019",
            missing_reason="not collected or not disclosed",

            firm_id="FIRM-001",
            firm_cells=cells,
        )
        self.assertEqual(gap_type, "derivable_not_derived")
        self.assertIn("MET-VD-018", derivable)

    def test_not_derivable_when_component_missing(self) -> None:
        """MET-VD-019 is not derivable when MET-VD-018 is also null."""
        cells = self._all_null_cells()
        # MET-VD-018 remains null (from _all_null_cells).
        gap_type, derivable = _classify_gap(
            metric_id="MET-VD-019",
            missing_reason="not collected or not disclosed",

            firm_id="FIRM-001",
            firm_cells=cells,
        )
        # Should not be derivable when component is null.
        self.assertNotEqual(gap_type, "derivable_not_derived")


# ---------------------------------------------------------------------------
# 2. _matches_not_disclosed and _matches_never_attempted
# ---------------------------------------------------------------------------


class TestPatternMatchers(unittest.TestCase):
    def test_matches_not_disclosed_all_known_patterns(self) -> None:
        for reason in _NOT_DISCLOSED_PATTERNS:
            self.assertTrue(
                _matches_not_disclosed(reason),
                msg=f"Expected pattern to match: {reason!r}",
            )

    def test_matches_not_disclosed_case_insensitive(self) -> None:
        reason = "GAAP EPS NOT COLLECTED OR NOT APPLICABLE"
        self.assertTrue(_matches_not_disclosed(reason))

    def test_matches_not_disclosed_rejects_unknown_reason(self) -> None:
        self.assertFalse(_matches_not_disclosed("some other random reason"))

    def test_matches_never_attempted_canonical_patterns(self) -> None:
        self.assertTrue(_matches_never_attempted("not collected or not disclosed"))
        self.assertTrue(_matches_never_attempted("not calculated"))
        self.assertTrue(_matches_never_attempted("not disclosed or not calculable"))
        self.assertTrue(_matches_never_attempted("contextual metric not collected"))

    def test_matches_never_attempted_rejects_partial(self) -> None:
        # Exact-match only: "not collected" (subset) should not match.
        self.assertFalse(_matches_never_attempted("not collected"))

    def test_matches_never_attempted_case_insensitive(self) -> None:
        self.assertTrue(_matches_never_attempted("NOT CALCULATED"))


# ---------------------------------------------------------------------------
# 3. _check_derivable
# ---------------------------------------------------------------------------


class TestCheckDerivable(unittest.TestCase):
    def test_returns_components_when_all_present(self) -> None:
        # MET-VD-007 requires MET-VD-006.
        firm_cells = {"MET-VD-006": {"value": 0.12, "as_of": "FY2024"}}
        result = _check_derivable(metric_id="MET-VD-007", firm_cells=firm_cells)
        self.assertEqual(result, ["MET-VD-006"])

    def test_returns_none_when_component_null(self) -> None:
        firm_cells = {"MET-VD-006": {"value": None}}
        result = _check_derivable(metric_id="MET-VD-007", firm_cells=firm_cells)
        self.assertIsNone(result)

    def test_returns_none_when_component_absent_from_firm(self) -> None:
        firm_cells: dict = {}
        result = _check_derivable(metric_id="MET-VD-007", firm_cells=firm_cells)
        self.assertIsNone(result)

    def test_returns_none_for_metric_without_derivation_rule(self) -> None:
        # MET-VD-001 (DE/share) has no derivation components.
        self.assertNotIn("MET-VD-001", _DERIVATION_COMPONENTS)
        firm_cells: dict = {"MET-VD-001": {"value": None}}
        result = _check_derivable(metric_id="MET-VD-001", firm_cells=firm_cells)
        self.assertIsNone(result)

    def test_fre_margin_derivable_when_fre_growth_exists(self) -> None:
        """MET-VD-013 (FRE margin) requires MET-VD-014 (FRE growth) as proxy."""
        firm_cells = {"MET-VD-014": {"value": 13.6, "unit": "%", "as_of": "FY2024"}}
        result = _check_derivable(metric_id="MET-VD-013", firm_cells=firm_cells)
        self.assertIsNotNone(result)
        self.assertIn("MET-VD-014", result)

    def test_fre_margin_not_derivable_when_fre_growth_null(self) -> None:
        firm_cells: dict = {"MET-VD-014": {"value": None}}
        result = _check_derivable(metric_id="MET-VD-013", firm_cells=firm_cells)
        self.assertIsNone(result)


# ---------------------------------------------------------------------------
# 4. _parse_as_of_date
# ---------------------------------------------------------------------------


class TestParseAsOfDate(unittest.TestCase):
    def test_fy_year(self) -> None:
        self.assertEqual(_parse_as_of_date("FY2024"), date(2024, 12, 31))

    def test_fy_year_case_insensitive(self) -> None:
        self.assertEqual(_parse_as_of_date("fy2022"), date(2022, 12, 31))

    def test_quarter_with_space(self) -> None:
        self.assertEqual(_parse_as_of_date("Q3 2023"), date(2023, 9, 30))

    def test_quarter_with_slash(self) -> None:
        self.assertEqual(_parse_as_of_date("Q3/2023"), date(2023, 9, 30))

    def test_q1_and_q4(self) -> None:
        self.assertEqual(_parse_as_of_date("Q1/2024"), date(2024, 3, 31))
        self.assertEqual(_parse_as_of_date("Q4/2023"), date(2023, 12, 31))

    def test_iso_date(self) -> None:
        self.assertEqual(_parse_as_of_date("2024-06-30"), date(2024, 6, 30))

    def test_year_only(self) -> None:
        self.assertEqual(_parse_as_of_date("2021"), date(2021, 12, 31))

    def test_empty_returns_none(self) -> None:
        self.assertIsNone(_parse_as_of_date(""))

    def test_unrecognized_format_returns_none(self) -> None:
        self.assertIsNone(_parse_as_of_date("Q4/FY2024"))
        self.assertIsNone(_parse_as_of_date("March 2024"))


# ---------------------------------------------------------------------------
# 5. _is_stale
# ---------------------------------------------------------------------------


class TestIsStale(unittest.TestCase):
    def test_fy2020_is_stale_relative_to_2026_run(self) -> None:
        self.assertTrue(_is_stale("FY2020", date(2026, 3, 9)))

    def test_fy2024_is_stale_relative_to_2026_run(self) -> None:
        # FY2024 ends 2024-12-31, which is ~15 months before 2026-03-09 → stale.
        self.assertTrue(_is_stale("FY2024", date(2026, 3, 9)))

    def test_fy2025_is_not_stale_relative_to_2026_run(self) -> None:
        # FY2025 ends 2025-12-31, which is ~3 months before 2026-03-09 → not stale.
        self.assertFalse(_is_stale("FY2025", date(2026, 3, 9)))

    def test_empty_as_of_is_not_stale(self) -> None:
        self.assertFalse(_is_stale("", date(2026, 3, 9)))

    def test_unparseable_as_of_is_not_stale(self) -> None:
        self.assertFalse(_is_stale("unknown", date(2026, 3, 9)))


# ---------------------------------------------------------------------------
# 6. _assign_priority (backfill priority)
# ---------------------------------------------------------------------------


class TestBackfillPriority(unittest.TestCase):
    def test_market_structure_always_skip(self) -> None:
        meta = {"is_driver": False, "category": "market_structure"}
        record = _make_gap_record(high_impact=True)
        self.assertEqual(_assign_priority(record=record, meta=meta), "skip")

    def test_market_structure_driver_also_skip(self) -> None:
        meta = {"is_driver": True, "category": "market_structure"}
        record = _make_gap_record(gap_type="never_attempted", high_impact=True)
        self.assertEqual(_assign_priority(record=record, meta=meta), "skip")

    def test_non_driver_is_low(self) -> None:
        meta = {"is_driver": False, "category": "valuation_multiples"}
        record = _make_gap_record()
        self.assertEqual(_assign_priority(record=record, meta=meta), "low")

    def test_high_impact_never_attempted_is_critical(self) -> None:
        record = _make_gap_record(gap_type="never_attempted", high_impact=True)
        self.assertEqual(_assign_priority(record=record, meta=_make_driver_meta()), "critical")

    def test_high_impact_derivable_not_derived_is_critical(self) -> None:
        record = _make_gap_record(
            gap_type="derivable_not_derived",
            high_impact=True,
            derivable_from=["MET-VD-001"],
        )
        self.assertEqual(_assign_priority(record=record, meta=_make_driver_meta()), "critical")

    def test_high_impact_not_disclosed_is_high(self) -> None:
        record = _make_gap_record(gap_type="not_disclosed", high_impact=True)
        self.assertEqual(_assign_priority(record=record, meta=_make_driver_meta()), "high")

    def test_no_high_impact_never_attempted_is_high(self) -> None:
        record = _make_gap_record(gap_type="never_attempted", high_impact=False)
        self.assertEqual(_assign_priority(record=record, meta=_make_driver_meta()), "high")

    def test_no_high_impact_derivable_not_derived_is_high(self) -> None:
        record = _make_gap_record(
            gap_type="derivable_not_derived",
            high_impact=False,
            derivable_from=["MET-VD-004"],
        )
        self.assertEqual(_assign_priority(record=record, meta=_make_driver_meta()), "high")

    def test_not_disclosed_with_derivable_is_medium(self) -> None:
        record = _make_gap_record(
            gap_type="not_disclosed",
            high_impact=False,
            derivable_from=["MET-VD-001"],
        )
        self.assertEqual(_assign_priority(record=record, meta=_make_driver_meta()), "medium")

    def test_not_disclosed_without_derivable_is_low(self) -> None:
        record = _make_gap_record(gap_type="not_disclosed", high_impact=False, derivable_from=None)
        self.assertEqual(_assign_priority(record=record, meta=_make_driver_meta()), "low")


# ---------------------------------------------------------------------------
# 7. _build_high_impact_targets
# ---------------------------------------------------------------------------


class TestBuildHighImpactTargets(unittest.TestCase):
    def test_below_threshold_metric_with_actionable_gaps_is_included(self) -> None:
        # 4 firms, threshold = int(4 * 0.6) = 2. MET-X has 1/4 filled.
        total_firms = 4
        threshold = int(total_firms * COVERAGE_THRESHOLD_PCT)
        mc = [_make_coverage("MET-X", "X Metric", firms_with_data=1, total_firms=total_firms)]
        gaps = [
            _make_gap_for_metric("FIRM-002", "MET-X", "never_attempted"),
            _make_gap_for_metric("FIRM-003", "MET-X", "derivable_not_derived"),
        ]
        targets = _build_high_impact_targets(
            metric_coverage=mc,
            gap_records=gaps,
            coverage_threshold=threshold,
            driver_metric_ids=["MET-X"],
        )
        self.assertEqual(len(targets), 1)
        self.assertEqual(targets[0]["metric_id"], "MET-X")
        self.assertIn("FIRM-002", targets[0]["firms_to_backfill"])
        self.assertIn("FIRM-003", targets[0]["firms_to_backfill"])

    def test_above_threshold_with_actionable_gaps_still_included(self) -> None:
        total_firms = 4
        threshold = int(total_firms * COVERAGE_THRESHOLD_PCT)
        # 3 of 4 filled → above threshold.
        mc = [_make_coverage("MET-Y", "Y Metric", firms_with_data=3, total_firms=total_firms)]
        gaps = [_make_gap_for_metric("FIRM-004", "MET-Y", "never_attempted")]
        targets = _build_high_impact_targets(
            metric_coverage=mc,
            gap_records=gaps,
            coverage_threshold=threshold,
            driver_metric_ids=["MET-Y"],
        )
        self.assertEqual(len(targets), 1)
        self.assertTrue(targets[0]["already_above_threshold"])
        self.assertIn("FIRM-004", targets[0]["firms_to_backfill"])

    def test_metric_with_only_not_disclosed_gaps_is_excluded(self) -> None:
        total_firms = 4
        threshold = int(total_firms * COVERAGE_THRESHOLD_PCT)
        mc = [_make_coverage("MET-Z", "Z Metric", firms_with_data=1, total_firms=total_firms)]
        # Only not_disclosed — not actionable.
        gaps = [_make_gap_for_metric("FIRM-002", "MET-Z", "not_disclosed")]
        targets = _build_high_impact_targets(
            metric_coverage=mc,
            gap_records=gaps,
            coverage_threshold=threshold,
            driver_metric_ids=["MET-Z"],
        )
        self.assertEqual(targets, [])

    def test_fully_covered_metric_with_no_actionable_gaps_is_excluded(self) -> None:
        total_firms = 4
        threshold = int(total_firms * COVERAGE_THRESHOLD_PCT)
        mc = [_make_coverage("MET-W", "W Metric", firms_with_data=4, total_firms=total_firms)]
        targets = _build_high_impact_targets(
            metric_coverage=mc,
            gap_records=[],
            coverage_threshold=threshold,
            driver_metric_ids=["MET-W"],
        )
        self.assertEqual(targets, [])

    def test_empty_inputs_return_empty_list(self) -> None:
        targets = _build_high_impact_targets(
            metric_coverage=[],
            gap_records=[],
            coverage_threshold=2,
            driver_metric_ids=[],
        )
        self.assertEqual(targets, [])


# ---------------------------------------------------------------------------
# 8. _build_metrics_index
# ---------------------------------------------------------------------------


class TestBuildMetricsIndex(unittest.TestCase):
    def test_driver_candidate_indexed_as_driver(self) -> None:
        taxonomy = _make_taxonomy([
            _make_metric_entry("MET-001", "Earnings", is_driver_candidate=True),
        ])
        index = _build_metrics_index(taxonomy)
        self.assertIn("MET-001", index)
        self.assertTrue(index["MET-001"]["is_driver"])

    def test_non_driver_indexed_as_not_driver(self) -> None:
        taxonomy = _make_taxonomy([
            _make_metric_entry(
                "MET-002", "Multiple", category="valuation_multiples", is_driver_candidate=False
            ),
        ])
        index = _build_metrics_index(taxonomy)
        self.assertFalse(index["MET-002"]["is_driver"])

    def test_malformed_entries_are_skipped(self) -> None:
        taxonomy: dict = {"metrics": [None, "bad", 42]}
        index = _build_metrics_index(taxonomy)
        self.assertEqual(index, {})

    def test_empty_metric_id_is_skipped(self) -> None:
        taxonomy = {"metrics": [{"metric_id": "", "name": "No ID", "is_driver_candidate": True}]}
        index = _build_metrics_index(taxonomy)
        self.assertEqual(index, {})

    def test_category_and_name_are_preserved(self) -> None:
        taxonomy = _make_taxonomy([
            _make_metric_entry("MET-003", "FEAUM YoY", category="scale"),
        ])
        index = _build_metrics_index(taxonomy)
        self.assertEqual(index["MET-003"]["category"], "scale")
        self.assertEqual(index["MET-003"]["name"], "FEAUM YoY")


# ---------------------------------------------------------------------------
# 9. _parse_run_date
# ---------------------------------------------------------------------------


class TestParseRunDate(unittest.TestCase):
    def test_plain_date(self) -> None:
        self.assertEqual(_parse_run_date("2026-03-09"), date(2026, 3, 9))

    def test_date_with_run_suffix(self) -> None:
        self.assertEqual(_parse_run_date("2026-03-09-run2"), date(2026, 3, 9))

    def test_date_with_run3_suffix(self) -> None:
        self.assertEqual(_parse_run_date("2025-12-31-run3"), date(2025, 12, 31))

    def test_invalid_run_id_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            _parse_run_date("latest")


# ---------------------------------------------------------------------------
# 10. Full pipeline — synthetic 3 firms × 4 metrics integration tests
# ---------------------------------------------------------------------------


class TestAnalyzeDataGapsPipelineSynthetic(unittest.TestCase):
    """Integration tests using synthetic in-memory fixtures written to tmp_path via pytest."""

    def _base_taxonomy(self) -> dict:
        return _make_taxonomy([
            _make_metric_entry("MET-A", "Alpha Metric", is_driver_candidate=True),
            _make_metric_entry("MET-B", "Beta Metric", is_driver_candidate=True),
            _make_metric_entry("MET-C", "Gamma Metric", is_driver_candidate=True),
            _make_metric_entry(
                "MET-D",
                "Delta Multiple",
                category="valuation_multiples",
                is_driver_candidate=False,
            ),
        ])


class TestAllPopulated(TestAnalyzeDataGapsPipelineSynthetic):
    def test_all_populated(self, tmp_path: Path = None) -> None:
        # Use a real tmp dir since unittest doesn't have tmp_path.
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            taxonomy = self._base_taxonomy()
            matrix = _make_matrix([
                _make_firm("FIRM-001", "AA", {
                    "MET-A": _make_cell(1.0),
                    "MET-B": _make_cell(2.0),
                    "MET-C": _make_cell(3.0),
                    "MET-D": _make_cell(10.0),
                }),
                _make_firm("FIRM-002", "BB", {
                    "MET-A": _make_cell(1.5),
                    "MET-B": _make_cell(2.5),
                    "MET-C": _make_cell(3.5),
                    "MET-D": _make_cell(11.0),
                }),
                _make_firm("FIRM-003", "CC", {
                    "MET-A": _make_cell(2.0),
                    "MET-B": _make_cell(3.0),
                    "MET-C": _make_cell(4.0),
                    "MET-D": _make_cell(12.0),
                }),
            ])
            run_dir = _write_run(tmp, taxonomy, matrix)
            report = analyze_data_gaps(run_dir)

            # Only driver metrics (3) are counted; MET-D is not a driver candidate.
            self.assertEqual(report["metadata"]["total_driver_metrics"], 3)
            # All driver cells filled (3 firms × 3 metrics = 9), data is FY2024 → stale.
            self.assertEqual(report["metadata"]["filled_cells"], 9)
            self.assertEqual(report["metadata"]["null_cells"], 0)
            # No null gaps (stale gaps may exist but gap_type will be "stale").
            null_gaps = [g for g in report["gaps"] if g["gap_type"] != "stale"]
            self.assertEqual(null_gaps, [])

    def test_all_null(self, tmp_path: Path = None) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            taxonomy = self._base_taxonomy()
            matrix = _make_matrix([
                _make_firm("FIRM-001", "AA", {
                    "MET-A": _make_cell(None),
                    "MET-B": _make_cell(None),
                    "MET-C": _make_cell(None),
                    "MET-D": _make_cell(None),
                }),
                _make_firm("FIRM-002", "BB", {
                    "MET-A": _make_cell(None),
                    "MET-B": _make_cell(None),
                    "MET-C": _make_cell(None),
                    "MET-D": _make_cell(None),
                }),
                _make_firm("FIRM-003", "CC", {
                    "MET-A": _make_cell(None),
                    "MET-B": _make_cell(None),
                    "MET-C": _make_cell(None),
                    "MET-D": _make_cell(None),
                }),
            ])
            run_dir = _write_run(tmp, taxonomy, matrix)
            report = analyze_data_gaps(run_dir)

            self.assertEqual(report["metadata"]["filled_cells"], 0)
            # null_cells = 3 firms × 3 driver metrics = 9.
            self.assertEqual(report["metadata"]["null_cells"], 9)
            self.assertEqual(report["metadata"]["fill_rate_pct"], 0.0)
            gap_types = {g["gap_type"] for g in report["gaps"]}
            self.assertEqual(gap_types, {"never_attempted"})

    def test_empty_matrix(self, tmp_path: Path = None) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            taxonomy = self._base_taxonomy()
            matrix = _make_matrix([])
            run_dir = _write_run(tmp, taxonomy, matrix)
            report = analyze_data_gaps(run_dir)

            self.assertEqual(report["metadata"]["total_firms"], 0)
            self.assertEqual(report["metadata"]["total_cells"], 0)
            self.assertEqual(report["metadata"]["fill_rate_pct"], 0.0)
            self.assertEqual(report["gaps"], [])

    def test_mixed_filled_and_null(self, tmp_path: Path = None) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            taxonomy = self._base_taxonomy()
            matrix = _make_matrix([
                _make_firm("FIRM-001", "AA", {
                    "MET-A": _make_cell(1.0),
                    "MET-B": _make_cell(None, missing_reason="GAAP EPS not collected or not applicable"),
                    "MET-C": _make_cell(None),
                    "MET-D": _make_cell(8.0),
                }),
                _make_firm("FIRM-002", "BB", {
                    "MET-A": _make_cell(None),
                    "MET-B": _make_cell(2.5),
                    "MET-C": _make_cell(None),
                    "MET-D": _make_cell(None),
                }),
                _make_firm("FIRM-003", "CC", {
                    "MET-A": _make_cell(2.0),
                    "MET-B": _make_cell(None),
                    "MET-C": _make_cell(4.0),
                    "MET-D": _make_cell(None),
                }),
            ])
            run_dir = _write_run(tmp, taxonomy, matrix)
            report = analyze_data_gaps(run_dir)

            # Driver metrics: MET-A, MET-B, MET-C (3). 3 firms → 9 cells.
            self.assertEqual(report["metadata"]["total_cells"], 9)
            # MET-A: 2 filled (FIRM-001, FIRM-003)
            # MET-B: 1 filled (FIRM-002)
            # MET-C: 1 filled (FIRM-003)
            self.assertEqual(report["metadata"]["filled_cells"], 4)
            self.assertEqual(report["metadata"]["null_cells"], 5)

    def test_gap_types_assigned_correctly_in_pipeline(self, tmp_path: Path = None) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            taxonomy = self._base_taxonomy()
            matrix = _make_matrix([
                _make_firm("FIRM-001", "AA", {
                    "MET-A": _make_cell(None),  # no missing_reason → never_attempted
                    "MET-B": _make_cell(None, missing_reason="GAAP EPS not collected or not applicable"),
                    "MET-C": _make_cell(5.0),
                    "MET-D": _make_cell(8.0),
                }),
            ])
            run_dir = _write_run(tmp, taxonomy, matrix)
            report = analyze_data_gaps(run_dir)

            gaps_by_metric = {g["metric_id"]: g for g in report["gaps"]}
            self.assertEqual(gaps_by_metric["MET-A"]["gap_type"], "never_attempted")
            self.assertEqual(gaps_by_metric["MET-B"]["gap_type"], "not_disclosed")

    def test_report_can_be_written_to_json(self, tmp_path: Path = None) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            taxonomy = self._base_taxonomy()
            matrix = _make_matrix([
                _make_firm("FIRM-001", "AA", {
                    "MET-A": _make_cell(1.0),
                    "MET-B": _make_cell(None),
                    "MET-C": _make_cell(None),
                    "MET-D": _make_cell(10.0),
                }),
            ])
            run_dir = _write_run(tmp, taxonomy, matrix)
            report = analyze_data_gaps(run_dir)
            output_path = run_dir / "3-analysis" / "data_gaps.json"
            _write_json(output_path, report)

            self.assertTrue(output_path.exists())
            loaded = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertIn("metadata", loaded)
            self.assertIn("gaps", loaded)
            self.assertIn("metric_coverage", loaded)

    def test_summary_recommends_backfill_critical_on_zero_coverage(self, tmp_path: Path = None) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            taxonomy = self._base_taxonomy()
            # MET-A: 0/3 filled → triggers backfill_critical.
            matrix = _make_matrix([
                _make_firm("FIRM-001", "AA", {
                    "MET-A": _make_cell(None),
                    "MET-B": _make_cell(1.0),
                    "MET-C": _make_cell(1.0),
                    "MET-D": _make_cell(None),
                }),
                _make_firm("FIRM-002", "BB", {
                    "MET-A": _make_cell(None),
                    "MET-B": _make_cell(2.0),
                    "MET-C": _make_cell(2.0),
                    "MET-D": _make_cell(None),
                }),
                _make_firm("FIRM-003", "CC", {
                    "MET-A": _make_cell(None),
                    "MET-B": _make_cell(3.0),
                    "MET-C": _make_cell(3.0),
                    "MET-D": _make_cell(None),
                }),
            ])
            run_dir = _write_run(tmp, taxonomy, matrix)
            report = analyze_data_gaps(run_dir)
            self.assertEqual(report["summary"]["recommended_action"], "backfill_critical")
            self.assertEqual(report["summary"]["metrics_zero_coverage"], 1)

    def test_high_impact_targets_for_below_threshold_metrics(self, tmp_path: Path = None) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            taxonomy = self._base_taxonomy()
            # 3 firms, threshold = int(3 * 0.6) = 1. MET-A: 0/3 filled.
            matrix = _make_matrix([
                _make_firm("FIRM-001", "AA", {
                    "MET-A": _make_cell(None),
                    "MET-B": _make_cell(1.0),
                    "MET-C": _make_cell(1.0),
                    "MET-D": _make_cell(None),
                }),
                _make_firm("FIRM-002", "BB", {
                    "MET-A": _make_cell(None),
                    "MET-B": _make_cell(2.0),
                    "MET-C": _make_cell(2.0),
                    "MET-D": _make_cell(None),
                }),
                _make_firm("FIRM-003", "CC", {
                    "MET-A": _make_cell(None),
                    "MET-B": _make_cell(3.0),
                    "MET-C": _make_cell(3.0),
                    "MET-D": _make_cell(None),
                }),
            ])
            run_dir = _write_run(tmp, taxonomy, matrix)
            report = analyze_data_gaps(run_dir)

            targets_by_metric = {t["metric_id"]: t for t in report["high_impact_backfill_targets"]}
            self.assertIn("MET-A", targets_by_metric)
            met_a = targets_by_metric["MET-A"]
            self.assertEqual(met_a["current_coverage"], 0)
            self.assertEqual(len(met_a["firms_to_backfill"]), 3)


# ---------------------------------------------------------------------------
# 11. Integration tests against the real 2026-03-09-run2 dataset
# ---------------------------------------------------------------------------


RUN_DIR = Path("data/processed/pax/2026-03-09-run2")


class TestDataGapsRealDataIntegration(unittest.TestCase):
    """Smoke-tests against the actual run directory committed in the repo."""

    @classmethod
    def setUpClass(cls) -> None:
        if not RUN_DIR.exists():
            raise unittest.SkipTest(f"Run directory not found: {RUN_DIR}")
        cls.report = analyze_data_gaps(RUN_DIR)
        cls.meta = cls.report["metadata"]
        cls.summary = cls.report["summary"]
        cls.metric_coverage = cls.report["metric_coverage"]
        cls.gaps = cls.report["gaps"]
        cls.high_impact_targets = cls.report["high_impact_backfill_targets"]

    def test_total_cells_equals_firms_times_driver_metrics(self) -> None:
        meta = self.meta
        self.assertEqual(
            meta["total_cells"],
            meta["total_firms"] * meta["total_driver_metrics"],
        )

    def test_total_firms_is_23(self) -> None:
        self.assertEqual(self.meta["total_firms"], 23)

    def test_total_driver_metrics_is_25(self) -> None:
        self.assertEqual(self.meta["total_driver_metrics"], 25)

    def test_total_cells_is_575(self) -> None:
        self.assertEqual(self.meta["total_cells"], 575)

    def test_fill_rate_between_20_and_35_pct(self) -> None:
        fill_rate = self.meta["fill_rate_pct"]
        self.assertGreaterEqual(fill_rate, 20.0)
        self.assertLessEqual(fill_rate, 35.0)

    def test_filled_plus_null_equals_total(self) -> None:
        meta = self.meta
        self.assertEqual(
            meta["filled_cells"] + meta["null_cells"],
            meta["total_cells"],
        )

    def test_zero_coverage_metrics_exist(self) -> None:
        self.assertGreater(self.summary["metrics_zero_coverage"], 0)

    def test_zero_coverage_metrics_are_not_above_threshold(self) -> None:
        for mc in self.metric_coverage:
            if mc["firms_with_data"] == 0:
                self.assertFalse(mc["above_correlation_threshold"])

    def test_above_threshold_flag_consistent_with_count(self) -> None:
        total_firms = self.meta["total_firms"]
        threshold = int(total_firms * COVERAGE_THRESHOLD_PCT)
        for mc in self.metric_coverage:
            if mc["above_correlation_threshold"]:
                self.assertGreaterEqual(mc["firms_with_data"], threshold)
            else:
                self.assertLess(mc["firms_with_data"], threshold)

    def test_high_impact_targets_exist(self) -> None:
        self.assertGreater(len(self.high_impact_targets), 0)

    def test_high_impact_targets_have_required_fields(self) -> None:
        required = {
            "metric_id",
            "metric_name",
            "current_coverage",
            "target_coverage",
            "already_above_threshold",
            "firms_to_backfill",
            "reason",
        }
        for target in self.high_impact_targets:
            missing = required - set(target.keys())
            self.assertEqual(missing, set(), msg=f"Missing fields in target: {missing}")

    def test_all_gap_types_are_valid(self) -> None:
        valid = {"never_attempted", "not_disclosed", "derivable_not_derived", "stale"}
        for record in self.gaps:
            self.assertIn(record["gap_type"], valid)

    def test_all_backfill_priorities_are_valid(self) -> None:
        valid = {"critical", "high", "medium", "low", "skip"}
        for record in self.gaps:
            self.assertIn(record["backfill_priority"], valid)

    def test_gap_records_have_required_fields(self) -> None:
        required = {
            "firm_id",
            "ticker",
            "metric_id",
            "metric_name",
            "gap_type",
            "missing_reason",
            "high_impact",
            "derivable_from",
            "backfill_priority",
        }
        for record in self.gaps:
            missing = required - set(record.keys())
            self.assertEqual(missing, set(), msg=f"Gap record missing fields: {missing}")

    def test_recommended_action_is_backfill_critical(self) -> None:
        self.assertEqual(self.summary["recommended_action"], "backfill_critical")

    def test_metric_coverage_has_25_entries(self) -> None:
        self.assertEqual(len(self.metric_coverage), 25)

    def test_firm_coverage_has_23_entries(self) -> None:
        self.assertEqual(len(self.report["firm_coverage"]), 23)

    def test_pipeline_label_is_vda(self) -> None:
        self.assertEqual(self.meta["pipeline"], "VDA")

    def test_run_id_matches_directory_name(self) -> None:
        self.assertEqual(self.meta["run_id"], "2026-03-09-run2")


if __name__ == "__main__":
    unittest.main()
