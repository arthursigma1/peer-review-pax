"""Tests for src/analyzer/delta_spec.py."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from src.analyzer.delta_spec import (
    FirmRecord,
    MetricRecord,
    _build_hint,
    _build_metrics_index,
    _index_gap_detail,
    _index_matrix,
    _load_firms,
    _split_firms_into_tiers,
    build_delta_spec,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_PEER_UNIVERSE = {
    "universe": [
        {"firm_id": "FIRM-001", "firm_name": "Blackstone Inc.", "ticker": "BX", "latest_aum_usd_bn": 1127.2},
        {"firm_id": "FIRM-002", "firm_name": "Apollo Global", "ticker": "APO", "latest_aum_usd_bn": 651.0},
        {"firm_id": "FIRM-003", "firm_name": "Ares Management", "ticker": "ARES", "latest_aum_usd_bn": 428.0},
        {"firm_id": "FIRM-004", "firm_name": "Blue Owl Capital", "ticker": "OWL", "latest_aum_usd_bn": 174.0},
        {"firm_id": "FIRM-005", "firm_name": "Patria Investments", "ticker": "PAX", "latest_aum_usd_bn": 44.0},
    ]
}

_METRIC_TAXONOMY = {
    "metrics": [
        {
            "metric_id": "MET-VD-001",
            "name": "DE per Share",
            "abbreviation": "DE/share",
            "category": "earnings",
            "is_driver_candidate": True,
            "calculation_notes": "Distributable earnings divided by diluted share count",
        },
        {
            "metric_id": "MET-VD-002",
            "name": "GAAP EPS",
            "abbreviation": "EPS",
            "category": "earnings",
            "is_driver_candidate": True,
            "calculation_notes": "GAAP net income / diluted shares",
        },
        {
            "metric_id": "MET-VD-003",
            "name": "AUM Total",
            "abbreviation": "AUM",
            "category": "aum",
            "is_driver_candidate": True,
            "calculation_notes": "Total assets under management reported by the firm",
        },
    ]
}


def _make_matrix(overrides: dict[tuple[str, str], dict | None] | None = None) -> dict:
    """Build a minimal standardized_matrix where all cells default to non-null (4.0).

    overrides: {(firm_id, metric_id): cell_dict or None (null cell)}
    """
    overrides = overrides or {}
    firms = []
    for firm_entry in _PEER_UNIVERSE["universe"]:
        fid = firm_entry["firm_id"]
        metrics = {}
        for metric_entry in _METRIC_TAXONOMY["metrics"]:
            mid = metric_entry["metric_id"]
            key = (fid, mid)
            if key in overrides:
                cell = overrides[key]
                if cell is None:
                    metrics[mid] = {"value": None, "unit": "USD", "missing_reason": "not collected"}
                else:
                    metrics[mid] = cell
            else:
                metrics[mid] = {"value": 4.0, "unit": "USD", "source": "10-K", "as_of": "FY2024"}
        firms.append({"firm_id": fid, "ticker": firm_entry["ticker"], "metrics": metrics})
    return {"matrix": firms}


def _make_data_gaps(gap_rows: list[dict]) -> dict:
    """Build a minimal data_gaps.json with the given gap_detail rows."""
    return {
        "gap_detail": gap_rows,
        "gap_summary_by_metric": [],
        "high_impact_targets": [],
    }


def _write_inputs(
    tmp_path: Path,
    matrix: dict | None = None,
    data_gaps: dict | None = None,
) -> tuple[Path, Path]:
    """Write synthetic input files; return (base_run_dir, new_run_dir)."""
    base_run = tmp_path / "base-run"
    new_run = tmp_path / "new-run"

    (base_run / "1-universe").mkdir(parents=True)
    (base_run / "3-analysis").mkdir(parents=True)

    (base_run / "1-universe" / "peer_universe.json").write_text(
        json.dumps(_PEER_UNIVERSE), encoding="utf-8"
    )
    (base_run / "1-universe" / "metric_taxonomy.json").write_text(
        json.dumps(_METRIC_TAXONOMY), encoding="utf-8"
    )
    (base_run / "3-analysis" / "standardized_matrix.json").write_text(
        json.dumps(matrix or _make_matrix()), encoding="utf-8"
    )
    (base_run / "3-analysis" / "data_gaps.json").write_text(
        json.dumps(data_gaps or _make_data_gaps([])), encoding="utf-8"
    )

    return base_run, new_run


def _collect_keys(spec: dict) -> set[tuple[str, str]]:
    """Extract (firm_id, metric_id) pairs from all collect tier assignments."""
    keys: set[tuple[str, str]] = set()
    for tier in ("tier1", "tier2", "tier3"):
        for assignment in spec["collect"][tier]["assignments"]:
            firm_id = assignment["firm_id"]
            for metric in assignment["metrics_to_collect"]:
                keys.add((firm_id, metric["metric_id"]))
    return keys


def _make_args(base_run: Path, new_run: Path) -> object:
    """Return a minimal argparse.Namespace-like object for build_delta_spec."""
    import argparse

    ns = argparse.Namespace()
    ns.base_run = str(base_run)
    ns.new_run_dir = str(new_run)
    ns.data_gaps = None
    ns.peer_universe = None
    ns.metric_taxonomy = None
    ns.standardized_matrix = None
    return ns


def _run_delta_spec(tmp_path: Path, matrix: dict | None = None, data_gaps: dict | None = None) -> dict:
    """Run build_delta_spec with synthetic inputs and return the parsed output."""
    base_run, new_run = _write_inputs(tmp_path, matrix=matrix, data_gaps=data_gaps)
    args = _make_args(base_run, new_run)
    summary = build_delta_spec(args)
    spec_path = Path(summary["delta_spec_path"])
    return json.loads(spec_path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# 1. Carry-forward logic
# ---------------------------------------------------------------------------


class TestCarryForward(unittest.TestCase):
    def test_cells_with_data_appear_in_carry_forward(self, tmp_path: Path | None = None) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            spec = _run_delta_spec(Path(td))
            # All cells have value=4.0 by default — all should be carry_forward.
            carry = spec["carry_forward"]["cells"]
            # 5 firms × 3 metrics = 15 cells
            self.assertEqual(len(carry), 15)

    def test_cells_with_data_never_appear_in_collect(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            spec = _run_delta_spec(Path(td))
            collect_cells: list[dict] = []
            for tier in ("tier1", "tier2", "tier3"):
                for assignment in spec["collect"][tier]["assignments"]:
                    collect_cells.extend(assignment["metrics_to_collect"])
            self.assertEqual(len(collect_cells), 0)

    def test_carry_forward_preserves_value_and_source(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            spec = _run_delta_spec(Path(td))
            carry = spec["carry_forward"]["cells"]
            first = carry[0]
            self.assertEqual(first["value"], 4.0)
            self.assertEqual(first["source"], "10-K")
            self.assertEqual(first["as_of"], "FY2024")


# ---------------------------------------------------------------------------
# 2. Skip logic
# ---------------------------------------------------------------------------


class TestSkipLogic(unittest.TestCase):
    def test_not_disclosed_cells_are_skipped(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            # FIRM-002 / MET-VD-002 is not_disclosed
            matrix = _make_matrix(overrides={("FIRM-002", "MET-VD-002"): None})
            data_gaps = _make_data_gaps(
                [
                    {
                        "firm_id": "FIRM-002",
                        "ticker": "APO",
                        "metric_id": "MET-VD-002",
                        "gap_type": "not_disclosed",
                        "backfill_priority": "low",
                    }
                ]
            )
            spec = _run_delta_spec(Path(td), matrix=matrix, data_gaps=data_gaps)
            skip_ids = {(c["firm_id"], c["metric_id"]) for c in spec["skip"]["cells"]}
            self.assertIn(("FIRM-002", "MET-VD-002"), skip_ids)

    def test_not_disclosed_cells_absent_from_collect(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            matrix = _make_matrix(overrides={("FIRM-002", "MET-VD-002"): None})
            data_gaps = _make_data_gaps(
                [
                    {
                        "firm_id": "FIRM-002",
                        "ticker": "APO",
                        "metric_id": "MET-VD-002",
                        "gap_type": "not_disclosed",
                        "backfill_priority": "low",
                    }
                ]
            )
            spec = _run_delta_spec(Path(td), matrix=matrix, data_gaps=data_gaps)
            collect_keys = _collect_keys(spec)
            self.assertNotIn(("FIRM-002", "MET-VD-002"), collect_keys)


# ---------------------------------------------------------------------------
# 3. Collection logic — never_attempted + critical/high/medium
# ---------------------------------------------------------------------------


class TestCollectionLogic(unittest.TestCase):
    def test_never_attempted_critical_goes_to_collect(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            matrix = _make_matrix(overrides={("FIRM-003", "MET-VD-001"): None})
            data_gaps = _make_data_gaps(
                [
                    {
                        "firm_id": "FIRM-003",
                        "ticker": "ARES",
                        "metric_id": "MET-VD-001",
                        "gap_type": "never_attempted",
                        "backfill_priority": "critical",
                    }
                ]
            )
            spec = _run_delta_spec(Path(td), matrix=matrix, data_gaps=data_gaps)
            collect_keys = _collect_keys(spec)
            self.assertIn(("FIRM-003", "MET-VD-001"), collect_keys)

    def test_never_attempted_high_goes_to_collect(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            matrix = _make_matrix(overrides={("FIRM-001", "MET-VD-002"): None})
            data_gaps = _make_data_gaps(
                [
                    {
                        "firm_id": "FIRM-001",
                        "ticker": "BX",
                        "metric_id": "MET-VD-002",
                        "gap_type": "never_attempted",
                        "backfill_priority": "high",
                    }
                ]
            )
            spec = _run_delta_spec(Path(td), matrix=matrix, data_gaps=data_gaps)
            collect_keys = _collect_keys(spec)
            self.assertIn(("FIRM-001", "MET-VD-002"), collect_keys)

    def test_never_attempted_medium_goes_to_collect(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            matrix = _make_matrix(overrides={("FIRM-004", "MET-VD-003"): None})
            data_gaps = _make_data_gaps(
                [
                    {
                        "firm_id": "FIRM-004",
                        "ticker": "OWL",
                        "metric_id": "MET-VD-003",
                        "gap_type": "never_attempted",
                        "backfill_priority": "medium",
                    }
                ]
            )
            spec = _run_delta_spec(Path(td), matrix=matrix, data_gaps=data_gaps)
            collect_keys = _collect_keys(spec)
            self.assertIn(("FIRM-004", "MET-VD-003"), collect_keys)

    def test_priority_breakdown_counts_critical(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            matrix = _make_matrix(overrides={("FIRM-003", "MET-VD-001"): None})
            data_gaps = _make_data_gaps(
                [
                    {
                        "firm_id": "FIRM-003",
                        "ticker": "ARES",
                        "metric_id": "MET-VD-001",
                        "gap_type": "never_attempted",
                        "backfill_priority": "critical",
                    }
                ]
            )
            spec = _run_delta_spec(Path(td), matrix=matrix, data_gaps=data_gaps)
            self.assertEqual(spec["metadata"]["priority_breakdown"]["critical"], 1)


# ---------------------------------------------------------------------------
# 4. Derivable collection
# ---------------------------------------------------------------------------


class TestDerivableCollection(unittest.TestCase):
    def test_derivable_not_derived_high_goes_to_collect(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            matrix = _make_matrix(overrides={("FIRM-005", "MET-VD-002"): None})
            data_gaps = _make_data_gaps(
                [
                    {
                        "firm_id": "FIRM-005",
                        "ticker": "PAX",
                        "metric_id": "MET-VD-002",
                        "gap_type": "derivable_not_derived",
                        "backfill_priority": "high",
                        "derivable_from": ["MET-VD-001"],
                    }
                ]
            )
            spec = _run_delta_spec(Path(td), matrix=matrix, data_gaps=data_gaps)
            collect_keys = _collect_keys(spec)
            self.assertIn(("FIRM-005", "MET-VD-002"), collect_keys)

    def test_derivable_not_derived_critical_goes_to_collect(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            matrix = _make_matrix(overrides={("FIRM-001", "MET-VD-003"): None})
            data_gaps = _make_data_gaps(
                [
                    {
                        "firm_id": "FIRM-001",
                        "ticker": "BX",
                        "metric_id": "MET-VD-003",
                        "gap_type": "derivable_not_derived",
                        "backfill_priority": "critical",
                        "derivable_from": ["MET-VD-001"],
                    }
                ]
            )
            spec = _run_delta_spec(Path(td), matrix=matrix, data_gaps=data_gaps)
            collect_keys = _collect_keys(spec)
            self.assertIn(("FIRM-001", "MET-VD-003"), collect_keys)

    def test_hint_for_derivable_contains_calculation_notes(self) -> None:
        metric = MetricRecord(
            metric_id="MET-VD-002",
            name="GAAP EPS",
            abbreviation="EPS",
            calculation_notes="GAAP net income / diluted shares",
        )
        hint = _build_hint(
            gap_classification="derivable_not_derived",
            ticker="PAX",
            metric=metric,
            cell={},
        )
        self.assertIn("derivable", hint.lower())
        self.assertIn("GAAP net income / diluted shares", hint)


# ---------------------------------------------------------------------------
# 5. Low priority exclusion
# ---------------------------------------------------------------------------


class TestLowPriorityExclusion(unittest.TestCase):
    def test_never_attempted_low_not_collected(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            matrix = _make_matrix(overrides={("FIRM-002", "MET-VD-003"): None})
            data_gaps = _make_data_gaps(
                [
                    {
                        "firm_id": "FIRM-002",
                        "ticker": "APO",
                        "metric_id": "MET-VD-003",
                        "gap_type": "never_attempted",
                        "backfill_priority": "low",
                    }
                ]
            )
            spec = _run_delta_spec(Path(td), matrix=matrix, data_gaps=data_gaps)
            collect_keys = _collect_keys(spec)
            self.assertNotIn(("FIRM-002", "MET-VD-003"), collect_keys)

    def test_skip_priority_never_collected(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            matrix = _make_matrix(overrides={("FIRM-001", "MET-VD-001"): None})
            data_gaps = _make_data_gaps(
                [
                    {
                        "firm_id": "FIRM-001",
                        "ticker": "BX",
                        "metric_id": "MET-VD-001",
                        "gap_type": "never_attempted",
                        "backfill_priority": "skip",
                    }
                ]
            )
            spec = _run_delta_spec(Path(td), matrix=matrix, data_gaps=data_gaps)
            collect_keys = _collect_keys(spec)
            self.assertNotIn(("FIRM-001", "MET-VD-001"), collect_keys)


# ---------------------------------------------------------------------------
# 6. Tier splitting
# ---------------------------------------------------------------------------


class TestTierSplitting(unittest.TestCase):
    def test_tier_splitting_matches_metric_checklist_logic(self) -> None:
        from src.analyzer.metric_checklist import split_firms_into_tiers as mc_split

        # Build FirmRecord lists for both modules using the same input.
        from src.analyzer.delta_spec import FirmRecord as DeltaFirmRecord

        firms_delta = [
            DeltaFirmRecord("FIRM-001", "BX Inc", "BX", 1127.2),
            DeltaFirmRecord("FIRM-002", "APO Inc", "APO", 651.0),
            DeltaFirmRecord("FIRM-003", "ARES Inc", "ARES", 428.0),
            DeltaFirmRecord("FIRM-004", "OWL Inc", "OWL", 174.0),
            DeltaFirmRecord("FIRM-005", "PAX Inc", "PAX", 44.0),
        ]

        from src.analyzer.metric_checklist import FirmRecord as MCFirmRecord

        firms_mc = [
            MCFirmRecord("FIRM-001", "BX Inc", "BX", 1127.2),
            MCFirmRecord("FIRM-002", "APO Inc", "APO", 651.0),
            MCFirmRecord("FIRM-003", "ARES Inc", "ARES", 428.0),
            MCFirmRecord("FIRM-004", "OWL Inc", "OWL", 174.0),
            MCFirmRecord("FIRM-005", "PAX Inc", "PAX", 44.0),
        ]

        dt1, dt2, dt3 = _split_firms_into_tiers(firms_delta)
        mc1, mc2, mc3 = mc_split(firms_mc)

        self.assertEqual([f.firm_id for f in dt1], [f.firm_id for f in mc1])
        self.assertEqual([f.firm_id for f in dt2], [f.firm_id for f in mc2])
        self.assertEqual([f.firm_id for f in dt3], [f.firm_id for f in mc3])

    def test_tier_splitting_sizes_for_5_firms(self) -> None:
        firms = [
            FirmRecord(f"FIRM-{i:03d}", f"Firm {i}", f"F{i}", float(100 - i))
            for i in range(1, 6)
        ]
        t1, t2, t3 = _split_firms_into_tiers(firms)
        # n=5: tier_size=1, extra=2 → t1=2, t2=2, t3=1
        self.assertEqual(len(t1), 2)
        self.assertEqual(len(t2), 2)
        self.assertEqual(len(t3), 1)

    def test_tier_splitting_sizes_for_9_firms(self) -> None:
        firms = [
            FirmRecord(f"FIRM-{i:03d}", f"Firm {i}", f"F{i}", float(100 - i))
            for i in range(1, 10)
        ]
        t1, t2, t3 = _split_firms_into_tiers(firms)
        self.assertEqual(len(t1), 3)
        self.assertEqual(len(t2), 3)
        self.assertEqual(len(t3), 3)

    def test_collect_cells_assigned_to_correct_tier(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            # FIRM-005 (PAX, smallest AUM) has never_attempted critical gap.
            matrix = _make_matrix(overrides={("FIRM-005", "MET-VD-001"): None})
            data_gaps = _make_data_gaps(
                [
                    {
                        "firm_id": "FIRM-005",
                        "ticker": "PAX",
                        "metric_id": "MET-VD-001",
                        "gap_type": "never_attempted",
                        "backfill_priority": "critical",
                    }
                ]
            )
            spec = _run_delta_spec(Path(td), matrix=matrix, data_gaps=data_gaps)
            # Tier3 should contain FIRM-005 (smallest AUM in 5-firm universe).
            tier3_firm_ids = spec["collect"]["tier3"]["firms"]
            self.assertIn("FIRM-005", tier3_firm_ids)
            # The assignment should appear in tier3.
            tier3_assignments = spec["collect"]["tier3"]["assignments"]
            assignment_firm_ids = [a["firm_id"] for a in tier3_assignments]
            self.assertIn("FIRM-005", assignment_firm_ids)


# ---------------------------------------------------------------------------
# 7. Hint generation
# ---------------------------------------------------------------------------


class TestHintGeneration(unittest.TestCase):
    def _metric(self, notes: str = "") -> MetricRecord:
        return MetricRecord(
            metric_id="MET-VD-001",
            name="DE per Share",
            abbreviation="DE/share",
            calculation_notes=notes,
        )

    def test_hint_never_attempted_contains_ticker_and_metric_name(self) -> None:
        hint = _build_hint(
            gap_classification="never_attempted",
            ticker="BX",
            metric=self._metric(),
            cell={},
        )
        self.assertIn("BX", hint)
        self.assertIn("DE per Share", hint)

    def test_hint_never_attempted_references_10k(self) -> None:
        hint = _build_hint(
            gap_classification="never_attempted",
            ticker="BX",
            metric=self._metric(),
            cell={},
        )
        self.assertIn("10-K", hint)

    def test_hint_derivable_not_derived_references_component_inputs(self) -> None:
        metric = self._metric(notes="FRE / management fee revenue * 100")
        hint = _build_hint(
            gap_classification="derivable_not_derived",
            ticker="APO",
            metric=metric,
            cell={},
        )
        self.assertIn("component inputs", hint.lower())
        self.assertIn("FRE / management fee revenue * 100", hint)

    def test_hint_stale_references_base_run_as_of(self) -> None:
        hint = _build_hint(
            gap_classification="stale",
            ticker="ARES",
            metric=self._metric(),
            cell={"as_of": "FY2022"},
        )
        self.assertIn("FY2022", hint)
        self.assertIn("latest filings", hint.lower())

    def test_hint_stale_missing_as_of_falls_back_gracefully(self) -> None:
        hint = _build_hint(
            gap_classification="stale",
            ticker="OWL",
            metric=self._metric(),
            cell={},
        )
        self.assertIn("unknown", hint.lower())


# ---------------------------------------------------------------------------
# 8. Full pipeline with synthetic 5 firms × 3 metrics
# ---------------------------------------------------------------------------


class TestFullPipeline(unittest.TestCase):
    def test_full_pipeline_metadata_counts(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            # Mix: FIRM-001/MET-VD-002 → never_attempted/high (collect)
            #       FIRM-002/MET-VD-003 → not_disclosed/low (skip)
            #       All others → filled (carry_forward)
            matrix = _make_matrix(
                overrides={
                    ("FIRM-001", "MET-VD-002"): None,
                    ("FIRM-002", "MET-VD-003"): None,
                }
            )
            data_gaps = _make_data_gaps(
                [
                    {
                        "firm_id": "FIRM-001",
                        "ticker": "BX",
                        "metric_id": "MET-VD-002",
                        "gap_type": "never_attempted",
                        "backfill_priority": "high",
                    },
                    {
                        "firm_id": "FIRM-002",
                        "ticker": "APO",
                        "metric_id": "MET-VD-003",
                        "gap_type": "not_disclosed",
                        "backfill_priority": "low",
                    },
                ]
            )
            spec = _run_delta_spec(Path(td), matrix=matrix, data_gaps=data_gaps)
            meta = spec["metadata"]

            # 15 total cells: 13 filled, 1 collect, 1 skip
            self.assertEqual(meta["total_cells_existing"], 13)
            self.assertEqual(meta["total_cells_to_collect"], 1)
            self.assertEqual(meta["total_cells_skipped_not_disclosed"], 1)

    def test_full_pipeline_output_file_written(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            base_run, new_run = _write_inputs(Path(td))
            args = _make_args(base_run, new_run)
            summary = build_delta_spec(args)
            spec_path = Path(summary["delta_spec_path"])
            self.assertTrue(spec_path.exists())
            self.assertEqual(spec_path.name, "delta_spec.json")

    def test_full_pipeline_structure_has_required_keys(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            spec = _run_delta_spec(Path(td))
            self.assertIn("metadata", spec)
            self.assertIn("carry_forward", spec)
            self.assertIn("skip", spec)
            self.assertIn("collect", spec)
            self.assertIn("tier1", spec["collect"])
            self.assertIn("tier2", spec["collect"])
            self.assertIn("tier3", spec["collect"])


# ---------------------------------------------------------------------------
# 9. Edge case: 100% fill rate → empty collect list
# ---------------------------------------------------------------------------


class TestFullFillRate(unittest.TestCase):
    def test_empty_collect_when_all_cells_filled(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            # Default matrix has all cells filled.
            spec = _run_delta_spec(Path(td))
            all_collect: list[dict] = []
            for tier in ("tier1", "tier2", "tier3"):
                for assignment in spec["collect"][tier]["assignments"]:
                    all_collect.extend(assignment["metrics_to_collect"])
            self.assertEqual(len(all_collect), 0)
            self.assertEqual(spec["metadata"]["total_cells_to_collect"], 0)

    def test_carry_forward_equals_total_cells_when_full(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            spec = _run_delta_spec(Path(td))
            # 5 firms × 3 metrics = 15
            self.assertEqual(spec["metadata"]["total_cells_existing"], 15)


# ---------------------------------------------------------------------------
# 10. Edge case: 0% fill rate → all cells in collect
# ---------------------------------------------------------------------------


class TestZeroFillRate(unittest.TestCase):
    def _make_all_null_matrix(self) -> dict:
        firms = []
        for firm_entry in _PEER_UNIVERSE["universe"]:
            fid = firm_entry["firm_id"]
            metrics = {}
            for metric_entry in _METRIC_TAXONOMY["metrics"]:
                mid = metric_entry["metric_id"]
                metrics[mid] = {"value": None, "unit": "USD", "missing_reason": "not collected"}
            firms.append({"firm_id": fid, "ticker": firm_entry["ticker"], "metrics": metrics})
        return {"matrix": firms}

    def _make_all_never_attempted_gaps(self) -> dict:
        rows = []
        for firm_entry in _PEER_UNIVERSE["universe"]:
            for metric_entry in _METRIC_TAXONOMY["metrics"]:
                rows.append(
                    {
                        "firm_id": firm_entry["firm_id"],
                        "ticker": firm_entry["ticker"],
                        "metric_id": metric_entry["metric_id"],
                        "gap_type": "never_attempted",
                        "backfill_priority": "high",
                    }
                )
        return _make_data_gaps(rows)

    def test_all_cells_collected_when_zero_fill(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            spec = _run_delta_spec(
                Path(td),
                matrix=self._make_all_null_matrix(),
                data_gaps=self._make_all_never_attempted_gaps(),
            )
            all_collect: list[dict] = []
            for tier in ("tier1", "tier2", "tier3"):
                for assignment in spec["collect"][tier]["assignments"]:
                    all_collect.extend(assignment["metrics_to_collect"])
            # 5 firms × 3 metrics = 15
            self.assertEqual(len(all_collect), 15)
            self.assertEqual(spec["metadata"]["total_cells_existing"], 0)

    def test_carry_forward_empty_when_zero_fill(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            spec = _run_delta_spec(
                Path(td),
                matrix=self._make_all_null_matrix(),
                data_gaps=self._make_all_never_attempted_gaps(),
            )
            self.assertEqual(len(spec["carry_forward"]["cells"]), 0)


# ---------------------------------------------------------------------------
# Unit tests for helper functions
# ---------------------------------------------------------------------------


class TestLoadFirms(unittest.TestCase):
    def test_firms_sorted_by_aum_descending(self) -> None:
        firms = _load_firms(_PEER_UNIVERSE)
        aums = [f.aum_usd_bn for f in firms]
        self.assertEqual(aums, sorted(aums, reverse=True))

    def test_all_firms_loaded(self) -> None:
        firms = _load_firms(_PEER_UNIVERSE)
        self.assertEqual(len(firms), 5)


class TestBuildMetricsIndex(unittest.TestCase):
    def test_index_contains_all_metric_ids(self) -> None:
        index = _build_metrics_index(_METRIC_TAXONOMY)
        self.assertIn("MET-VD-001", index)
        self.assertIn("MET-VD-002", index)
        self.assertIn("MET-VD-003", index)

    def test_metric_record_has_correct_name(self) -> None:
        index = _build_metrics_index(_METRIC_TAXONOMY)
        self.assertEqual(index["MET-VD-001"].name, "DE per Share")


class TestIndexMatrix(unittest.TestCase):
    def test_index_key_lookup(self) -> None:
        matrix = _make_matrix()
        index = _index_matrix(matrix)
        cell = index.get(("FIRM-001", "MET-VD-001"))
        self.assertIsNotNone(cell)
        self.assertEqual(cell["value"], 4.0)

    def test_null_cell_indexed(self) -> None:
        matrix = _make_matrix(overrides={("FIRM-002", "MET-VD-002"): None})
        index = _index_matrix(matrix)
        cell = index.get(("FIRM-002", "MET-VD-002"))
        self.assertIsNotNone(cell)
        self.assertIsNone(cell["value"])


class TestIndexGapDetail(unittest.TestCase):
    def test_gap_detail_key_lookup(self) -> None:
        data_gaps = _make_data_gaps(
            [
                {
                    "firm_id": "FIRM-001",
                    "ticker": "BX",
                    "metric_id": "MET-VD-002",
                    "gap_type": "never_attempted",
                    "backfill_priority": "critical",
                }
            ]
        )
        index = _index_gap_detail(data_gaps)
        gap = index.get(("FIRM-001", "MET-VD-002"))
        self.assertIsNotNone(gap)
        self.assertEqual(gap["gap_type"], "never_attempted")

    def test_gaps_key_also_accepted(self) -> None:
        """data_gaps.py uses 'gaps' key; spec documents 'gap_detail' — both should work."""
        data_gaps = {
            "gaps": [
                {
                    "firm_id": "FIRM-002",
                    "ticker": "APO",
                    "metric_id": "MET-VD-001",
                    "gap_type": "not_disclosed",
                    "backfill_priority": "low",
                }
            ]
        }
        index = _index_gap_detail(data_gaps)
        gap = index.get(("FIRM-002", "MET-VD-001"))
        self.assertIsNotNone(gap)
        self.assertEqual(gap["gap_type"], "not_disclosed")


# ---------------------------------------------------------------------------
# Merge carry-forward tests
# ---------------------------------------------------------------------------


class TestMergeCarryForward(unittest.TestCase):
    """Tests for merge_carry_forward() — injecting base-run data into tier files."""

    def test_carry_forward_injected_into_empty_tier_files(self) -> None:
        """When no tier files exist yet, merge creates them with carry-forward data."""
        import tempfile
        from src.analyzer.delta_spec import merge_carry_forward

        with tempfile.TemporaryDirectory() as td:
            new_run = Path(td) / "new-run"
            data_dir = new_run / "2-data"
            data_dir.mkdir(parents=True)

            # Write a delta_spec with carry-forward cells and tier info
            spec = {
                "carry_forward": {
                    "cells": [
                        {"firm_id": "FIRM-001", "ticker": "BX", "metric_id": "MET-VD-001", "value": 4.64, "unit": "USD", "source": "10-K", "as_of": "FY2024"},
                        {"firm_id": "FIRM-002", "ticker": "APO", "metric_id": "MET-VD-001", "value": 6.89, "unit": "USD", "source": "10-K", "as_of": "FY2024"},
                    ]
                },
                "collect": {
                    "tier1": {"firms": ["FIRM-001", "FIRM-002"], "assignments": []},
                    "tier2": {"firms": [], "assignments": []},
                    "tier3": {"firms": [], "assignments": []},
                },
            }
            (data_dir / "delta_spec.json").write_text(json.dumps(spec), encoding="utf-8")

            result = merge_carry_forward(new_run)

            self.assertTrue(result["merged"])
            self.assertEqual(result["carry_forward_cells"], 2)
            self.assertEqual(result["newly_injected"], 2)

            # Tier1 file should exist with 2 data points
            tier1 = json.loads((data_dir / "quantitative_tier1.json").read_text())
            self.assertEqual(len(tier1["data_points"]), 2)

    def test_newly_collected_data_not_overwritten(self) -> None:
        """If a tier file already has a data point, carry-forward does NOT replace it."""
        import tempfile
        from src.analyzer.delta_spec import merge_carry_forward

        with tempfile.TemporaryDirectory() as td:
            new_run = Path(td) / "new-run"
            data_dir = new_run / "2-data"
            data_dir.mkdir(parents=True)

            # Pre-existing tier file with a freshly collected data point
            tier1_data = {
                "metadata": {"tier": 1},
                "data_points": [
                    {"firm_id": "FIRM-001", "ticker": "BX", "metric_id": "MET-VD-001", "value": 5.00, "unit": "USD", "source": "NEW collection"},
                ]
            }
            (data_dir / "quantitative_tier1.json").write_text(json.dumps(tier1_data), encoding="utf-8")

            # Delta spec carries forward same cell with OLD value
            spec = {
                "carry_forward": {
                    "cells": [
                        {"firm_id": "FIRM-001", "ticker": "BX", "metric_id": "MET-VD-001", "value": 4.64, "unit": "USD", "source": "OLD base run"},
                    ]
                },
                "collect": {
                    "tier1": {"firms": ["FIRM-001"], "assignments": []},
                    "tier2": {"firms": [], "assignments": []},
                    "tier3": {"firms": [], "assignments": []},
                },
            }
            (data_dir / "delta_spec.json").write_text(json.dumps(spec), encoding="utf-8")

            result = merge_carry_forward(new_run)

            # Should NOT inject (already exists)
            self.assertEqual(result["newly_injected"], 0)
            tier1 = json.loads((data_dir / "quantitative_tier1.json").read_text())
            self.assertEqual(len(tier1["data_points"]), 1)
            self.assertEqual(tier1["data_points"][0]["value"], 5.00)  # kept NEW value

    def test_no_delta_spec_returns_error(self) -> None:
        """When delta_spec.json doesn't exist, merge returns error gracefully."""
        import tempfile
        from src.analyzer.delta_spec import merge_carry_forward

        with tempfile.TemporaryDirectory() as td:
            result = merge_carry_forward(Path(td))
            self.assertFalse(result.get("merged", True))
            self.assertIn("error", result)

    def test_empty_carry_forward(self) -> None:
        """When carry_forward has no cells, merge completes with 0 injected."""
        import tempfile
        from src.analyzer.delta_spec import merge_carry_forward

        with tempfile.TemporaryDirectory() as td:
            new_run = Path(td) / "new-run"
            data_dir = new_run / "2-data"
            data_dir.mkdir(parents=True)

            spec = {
                "carry_forward": {"cells": []},
                "collect": {
                    "tier1": {"firms": [], "assignments": []},
                    "tier2": {"firms": [], "assignments": []},
                    "tier3": {"firms": [], "assignments": []},
                },
            }
            (data_dir / "delta_spec.json").write_text(json.dumps(spec), encoding="utf-8")

            result = merge_carry_forward(new_run)
            self.assertTrue(result["merged"])
            self.assertEqual(result["carry_forward_cells"], 0)

    def test_multi_tier_distribution(self) -> None:
        """Carry-forward cells are distributed to the correct tiers."""
        import tempfile
        from src.analyzer.delta_spec import merge_carry_forward

        with tempfile.TemporaryDirectory() as td:
            new_run = Path(td) / "new-run"
            data_dir = new_run / "2-data"
            data_dir.mkdir(parents=True)

            spec = {
                "carry_forward": {
                    "cells": [
                        {"firm_id": "FIRM-001", "ticker": "BX", "metric_id": "MET-VD-001", "value": 4.64, "unit": "USD"},
                        {"firm_id": "FIRM-005", "ticker": "PAX", "metric_id": "MET-VD-001", "value": 1.20, "unit": "USD"},
                    ]
                },
                "collect": {
                    "tier1": {"firms": ["FIRM-001"], "assignments": []},
                    "tier2": {"firms": [], "assignments": []},
                    "tier3": {"firms": ["FIRM-005"], "assignments": []},
                },
            }
            (data_dir / "delta_spec.json").write_text(json.dumps(spec), encoding="utf-8")

            result = merge_carry_forward(new_run)

            self.assertEqual(result["newly_injected"], 2)
            tier1 = json.loads((data_dir / "quantitative_tier1.json").read_text())
            tier3 = json.loads((data_dir / "quantitative_tier3.json").read_text())
            self.assertEqual(len(tier1["data_points"]), 1)
            self.assertEqual(tier1["data_points"][0]["ticker"], "BX")
            self.assertEqual(len(tier3["data_points"]), 1)
            self.assertEqual(tier3["data_points"][0]["ticker"], "PAX")


if __name__ == "__main__":
    unittest.main()
