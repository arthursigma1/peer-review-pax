"""Tests for src/analyzer/metric_checklist.py.

Unit tests use tmp_path and synthetic JSON fixtures for isolation.
Integration tests (TestGenerateChecklistIntegration) use the real PAX run data
in data/processed/pax/2026-03-09-run2/ and are skipped when that directory is absent.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from src.analyzer.metric_checklist import (
    FirmRecord,
    MetricRecord,
    assign_collection_priority,
    build_firm_checklist,
    extract_derivable_formula,
    generate_checklist,
    load_firms,
    load_metrics,
    split_firms_into_tiers,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_metric(
    *,
    metric_id: str = "MET-VD-001",
    name: str = "test metric",
    abbreviation: str = "test",
    category: str = "driver",
    is_driver_candidate: bool = True,
    calculation_notes: str = "",
) -> MetricRecord:
    return MetricRecord(
        metric_id=metric_id,
        name=name,
        abbreviation=abbreviation,
        category=category,
        is_driver_candidate=is_driver_candidate,
        calculation_notes=calculation_notes,
    )


def _make_firm(
    *,
    firm_id: str = "FIRM-001",
    firm_name: str = "Test Co",
    ticker: str = "TST",
    aum_usd_bn: float = 100.0,
) -> FirmRecord:
    return FirmRecord(
        firm_id=firm_id,
        firm_name=firm_name,
        ticker=ticker,
        aum_usd_bn=aum_usd_bn,
    )


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


_PAX_RUN_DIR = Path("data/processed/pax/2026-03-09-run2")
_pax_data_available = _PAX_RUN_DIR.is_dir()


# ---------------------------------------------------------------------------
# assign_collection_priority — skip
# ---------------------------------------------------------------------------

class TestAssignCollectionPrioritySkip:
    def test_market_structure_category_returns_skip(self) -> None:
        metric = _make_metric(category="market_structure", is_driver_candidate=True)
        assert assign_collection_priority(metric) == "skip"

    def test_market_structure_overrides_driver_candidate_flag(self) -> None:
        # Even if is_driver_candidate is True, market_structure wins.
        metric = _make_metric(
            category="market_structure",
            is_driver_candidate=True,
            name="DE/share",
        )
        assert assign_collection_priority(metric) == "skip"

    def test_market_structure_driver_false_also_skip(self) -> None:
        metric = _make_metric(
            category="market_structure",
            is_driver_candidate=False,
            name="average daily trading volume",
            abbreviation="adtv",
        )
        assert assign_collection_priority(metric) == "skip"

    def test_non_driver_non_multiple_returns_skip(self) -> None:
        # calculation_notes must not contain the word "multiple" — that triggers critical.
        metric = _make_metric(
            category="contextual",
            is_driver_candidate=False,
            name="generic metric",
            abbreviation="gen",
            calculation_notes="disclosed in annual filings only",
        )
        assert assign_collection_priority(metric) == "skip"


# ---------------------------------------------------------------------------
# assign_collection_priority — critical
# ---------------------------------------------------------------------------

class TestAssignCollectionPriorityCritical:
    def test_valuation_multiples_category_returns_critical(self) -> None:
        metric = _make_metric(
            category="valuation_multiples",
            is_driver_candidate=False,
            name="P/FRE",
            abbreviation="P/FRE",
        )
        assert assign_collection_priority(metric) == "critical"

    def test_abbreviation_p_slash_returns_critical(self) -> None:
        metric = _make_metric(
            category="driver",
            is_driver_candidate=False,
            abbreviation="P/DE",
            name="price to distributable earnings",
        )
        assert assign_collection_priority(metric) == "critical"

    def test_abbreviation_ev_slash_returns_critical(self) -> None:
        metric = _make_metric(
            category="driver",
            is_driver_candidate=False,
            abbreviation="EV/EBITDA",
            name="enterprise value to ebitda",
        )
        assert assign_collection_priority(metric) == "critical"

    def test_name_p_slash_fre_returns_critical(self) -> None:
        metric = _make_metric(
            category="driver",
            is_driver_candidate=False,
            name="P/FRE valuation",
            abbreviation="pFRE",
        )
        assert assign_collection_priority(metric) == "critical"

    def test_name_p_slash_de_returns_critical(self) -> None:
        metric = _make_metric(
            category="driver",
            is_driver_candidate=False,
            name="P/DE ratio",
            abbreviation="pDE",
        )
        assert assign_collection_priority(metric) == "critical"

    def test_calculation_notes_contains_multiple_returns_critical(self) -> None:
        metric = _make_metric(
            category="driver",
            is_driver_candidate=False,
            name="some valuation",
            abbreviation="val",
            calculation_notes="this is a multiple of earnings",
        )
        assert assign_collection_priority(metric) == "critical"

    def test_valuation_multiples_category_generic_name(self) -> None:
        metric = _make_metric(
            category="valuation_multiples",
            is_driver_candidate=False,
            name="generic multiple",
            abbreviation="genmul",
        )
        assert assign_collection_priority(metric) == "critical"

    def test_ev_slash_feaum_abbreviation_returns_critical(self) -> None:
        metric = _make_metric(
            category="valuation_multiples",
            is_driver_candidate=False,
            abbreviation="EV/FEAUM",
            name="enterprise value to fee-earning aum",
        )
        assert assign_collection_priority(metric) == "critical"


# ---------------------------------------------------------------------------
# assign_collection_priority — high
# ---------------------------------------------------------------------------

class TestAssignCollectionPriorityHigh:
    @pytest.mark.parametrize("name,abbreviation", [
        ("distributable earnings per share", "de/share"),
        ("DE/share", "DE/share"),
        ("fee-earning AUM", "FEAUM"),
        ("total AUM", "AUM"),
        ("FRE margin", "fre margin"),
        ("fee-related earnings margin", "FRE margin"),
        ("management fee rate", "mgmt fee rate"),
        ("permanent capital", "perm capital"),
        ("credit percentage", "credit %"),
        ("compensation-to-revenue", "comp ratio"),
        ("performance fee share", "perf fee share"),
        ("EPS", "eps"),
        ("earnings per share", "EPS"),
    ])
    def test_high_priority_metric_name_patterns(self, name: str, abbreviation: str) -> None:
        metric = _make_metric(
            category="driver",
            is_driver_candidate=True,
            name=name,
            abbreviation=abbreviation,
        )
        assert assign_collection_priority(metric) == "high"

    def test_high_priority_matched_via_abbreviation_only(self) -> None:
        metric = _make_metric(
            category="driver",
            is_driver_candidate=True,
            name="something without trigger words",
            abbreviation="FEAUM",
        )
        assert assign_collection_priority(metric) == "high"

    def test_high_priority_not_demoted_by_formula_in_notes(self) -> None:
        # A high-priority metric must not be demoted to medium even if notes contain a formula.
        metric = _make_metric(
            category="driver",
            is_driver_candidate=True,
            name="AUM",
            abbreviation="AUM",
            calculation_notes="FRE / Revenue",
        )
        assert assign_collection_priority(metric) == "high"

    def test_perf_fee_share_matches_via_abbreviation(self) -> None:
        metric = _make_metric(
            category="driver",
            is_driver_candidate=True,
            name="performance economics split",
            abbreviation="perf fee share",
        )
        assert assign_collection_priority(metric) == "high"


# ---------------------------------------------------------------------------
# assign_collection_priority — medium
# ---------------------------------------------------------------------------

class TestAssignCollectionPriorityMedium:
    def test_formula_division_returns_medium(self) -> None:
        metric = _make_metric(
            category="driver",
            is_driver_candidate=True,
            name="some derived ratio",
            abbreviation="sdr",
            calculation_notes="FRE / Revenue",
        )
        assert assign_collection_priority(metric) == "medium"

    def test_formula_multiplication_returns_medium(self) -> None:
        metric = _make_metric(
            category="driver",
            is_driver_candidate=True,
            name="scaled metric",
            abbreviation="scl",
            calculation_notes="FEAUM * 10,000",
        )
        assert assign_collection_priority(metric) == "medium"

    def test_formula_addition_with_spaces_returns_medium(self) -> None:
        metric = _make_metric(
            category="driver",
            is_driver_candidate=True,
            name="total fees",
            abbreviation="tf",
            calculation_notes="mgmt fees + advisory fees",
        )
        assert assign_collection_priority(metric) == "medium"

    def test_driver_candidate_no_formula_no_name_match_returns_medium(self) -> None:
        # Remaining driver candidates that pass no other rules fall to medium.
        metric = _make_metric(
            category="driver",
            is_driver_candidate=True,
            name="some other driver metric",
            abbreviation="sod",
            calculation_notes="No arithmetic expression here.",
        )
        assert assign_collection_priority(metric) == "medium"

    def test_formula_in_parentheses_detected(self) -> None:
        metric = _make_metric(
            category="driver",
            is_driver_candidate=True,
            name="fre yoy growth",
            abbreviation="fre growth",
            calculation_notes="(FRE_t / FRE_t-1) - 1. Captures both revenue growth and margin.",
        )
        assert assign_collection_priority(metric) == "medium"


# ---------------------------------------------------------------------------
# assign_collection_priority — low
# ---------------------------------------------------------------------------

class TestAssignCollectionPriorityLow:
    @pytest.mark.parametrize("name,abbreviation", [
        ("integration costs to revenue", "integration/rev"),
        ("integration/rev ratio", "integration/rev"),
        ("capex to feaum", "capex/feaum"),
        ("capex/feaum ratio", "capex/feaum"),
        ("constant currency revenue growth", "cc rev growth"),
        ("cc rev growth", "cc rev growth"),
    ])
    def test_low_priority_metric_name_patterns(self, name: str, abbreviation: str) -> None:
        metric = _make_metric(
            category="driver",
            is_driver_candidate=True,
            name=name,
            abbreviation=abbreviation,
        )
        assert assign_collection_priority(metric) == "low"

    def test_low_priority_matched_via_name_only(self) -> None:
        metric = _make_metric(
            category="driver",
            is_driver_candidate=True,
            name="integration/rev",
            abbreviation="ir_custom",
        )
        assert assign_collection_priority(metric) == "low"

    def test_low_priority_matched_via_abbreviation_only(self) -> None:
        metric = _make_metric(
            category="driver",
            is_driver_candidate=True,
            name="capex efficiency",
            abbreviation="capex/feaum",
        )
        assert assign_collection_priority(metric) == "low"


# ---------------------------------------------------------------------------
# extract_derivable_formula
# ---------------------------------------------------------------------------

class TestExtractDerivableFormula:
    def test_division_formula_detected(self) -> None:
        result = extract_derivable_formula("FRE / Revenue")
        assert result is not None
        assert "/" in result

    def test_multiplication_formula_detected(self) -> None:
        # The regex requires at least one formula-like operand (uppercase, digit, or underscore).
        # "FEAUM * 10,000" satisfies this — FEAUM is uppercase, 10,000 has a digit.
        result = extract_derivable_formula("FEAUM * 10,000")
        assert result is not None
        assert "*" in result

    def test_addition_with_spaces_detected(self) -> None:
        result = extract_derivable_formula("mgmt fees + advisory fees")
        assert result is not None
        assert "+" in result

    def test_subtraction_with_spaces_detected(self) -> None:
        result = extract_derivable_formula("gross revenue - carried interest")
        assert result is not None
        assert "-" in result

    def test_hyphenated_compound_word_not_detected(self) -> None:
        result = extract_derivable_formula("fee-earning AUM is computed using")
        assert result is None

    def test_empty_string_returns_none(self) -> None:
        assert extract_derivable_formula("") is None

    def test_plain_prose_returns_none(self) -> None:
        assert extract_derivable_formula("Disclosed in annual reports.") is None

    def test_prose_slash_not_a_formula(self) -> None:
        # "real assets/infrastructure" should not trigger formula detection.
        notes = (
            "Standardize across firms using categories: "
            "private equity, credit, real assets/infrastructure, hedge fund."
        )
        assert extract_derivable_formula(notes) is None

    def test_formula_trimmed_at_sentence_boundary(self) -> None:
        notes = "FEAUM * 10,000. Then divide by number of shares."
        result = extract_derivable_formula(notes)
        assert result is not None
        # Result should not extend past the period.
        assert "Then divide" not in result

    def test_formula_embedded_in_prose(self) -> None:
        notes = "Calculated as FRE / Revenue for each reporting period."
        result = extract_derivable_formula(notes)
        assert result is not None
        assert "/" in result

    def test_uppercase_operands_in_division(self) -> None:
        result = extract_derivable_formula("EV / EBITDA is the primary ratio used.")
        assert result is not None

    def test_underscore_operand_in_division(self) -> None:
        result = extract_derivable_formula("FEAUM_t / FEAUM_t1 measures growth.")
        assert result is not None

    def test_formula_result_is_string_when_found(self) -> None:
        result = extract_derivable_formula("NET_INCOME / Revenue")
        assert isinstance(result, str)

    def test_feaum_division_contains_operand(self) -> None:
        notes = "(FEAUM_t / FEAUM_t-1) - 1. Use end-of-fiscal-year values."
        result = extract_derivable_formula(notes)
        assert result is not None
        assert "FEAUM_t" in result

    def test_pure_prose_divided_by_word_prose(self) -> None:
        # "divided by" in prose does not count as a formula operator.
        notes = "GAAP net income attributable to common shareholders divided by diluted share count."
        result = extract_derivable_formula(notes)
        assert result is None


# ---------------------------------------------------------------------------
# split_firms_into_tiers
# ---------------------------------------------------------------------------

class TestSplitFirmsIntoTiers:
    def _firms(self, n: int) -> list[FirmRecord]:
        return [
            _make_firm(firm_id=f"FIRM-{i:03d}", aum_usd_bn=float(100 - i))
            for i in range(n)
        ]

    def test_nine_firms_splits_3_3_3(self) -> None:
        t1, t2, t3 = split_firms_into_tiers(self._firms(9))
        assert len(t1) == 3
        assert len(t2) == 3
        assert len(t3) == 3

    def test_ten_firms_splits_4_3_3(self) -> None:
        t1, t2, t3 = split_firms_into_tiers(self._firms(10))
        assert len(t1) == 4
        assert len(t2) == 3
        assert len(t3) == 3

    def test_eleven_firms_splits_4_4_3(self) -> None:
        t1, t2, t3 = split_firms_into_tiers(self._firms(11))
        assert len(t1) == 4
        assert len(t2) == 4
        assert len(t3) == 3

    def test_twenty_three_firms_splits_8_8_7(self) -> None:
        t1, t2, t3 = split_firms_into_tiers(self._firms(23))
        assert len(t1) == 8
        assert len(t2) == 8
        assert len(t3) == 7

    def test_three_firms_splits_1_1_1(self) -> None:
        t1, t2, t3 = split_firms_into_tiers(self._firms(3))
        assert len(t1) == 1
        assert len(t2) == 1
        assert len(t3) == 1

    def test_one_firm_splits_1_0_0(self) -> None:
        t1, t2, t3 = split_firms_into_tiers(self._firms(1))
        assert len(t1) == 1
        assert len(t2) == 0
        assert len(t3) == 0

    def test_zero_firms_splits_0_0_0(self) -> None:
        t1, t2, t3 = split_firms_into_tiers(self._firms(0))
        assert len(t1) == 0
        assert len(t2) == 0
        assert len(t3) == 0

    @pytest.mark.parametrize("n", list(range(0, 30)))
    def test_total_firms_preserved_across_all_sizes(self, n: int) -> None:
        t1, t2, t3 = split_firms_into_tiers(self._firms(n))
        assert len(t1) + len(t2) + len(t3) == n

    def test_tiers_are_disjoint(self) -> None:
        t1, t2, t3 = split_firms_into_tiers(self._firms(23))
        all_ids = [f.firm_id for f in t1 + t2 + t3]
        assert len(all_ids) == len(set(all_ids))

    def test_tier1_receives_largest_aum_firms(self) -> None:
        firms = self._firms(9)  # aum = 100, 99, ..., 92
        t1, t2, t3 = split_firms_into_tiers(firms)
        assert min(f.aum_usd_bn for f in t1) > max(f.aum_usd_bn for f in t2)

    def test_tier_size_difference_at_most_one(self) -> None:
        for n in range(1, 25):
            sizes = [len(t) for t in split_firms_into_tiers(self._firms(n))]
            assert max(sizes) - min(sizes) <= 1, f"n={n}: sizes={sizes}"


# ---------------------------------------------------------------------------
# load_firms
# ---------------------------------------------------------------------------

class TestLoadFirms:
    def test_firms_sorted_by_aum_descending(self, tmp_path: Path) -> None:
        payload = {
            "universe": [
                {"firm_id": "FIRM-001", "firm_name": "Small Co", "ticker": "SML", "latest_aum_usd_bn": 10.0},
                {"firm_id": "FIRM-002", "firm_name": "Large Co", "ticker": "LRG", "latest_aum_usd_bn": 500.0},
                {"firm_id": "FIRM-003", "firm_name": "Mid Co", "ticker": "MID", "latest_aum_usd_bn": 100.0},
            ]
        }
        p = tmp_path / "peer_universe.json"
        _write_json(p, payload)
        firms = load_firms(p)
        assert firms[0].aum_usd_bn == 500.0
        assert firms[1].aum_usd_bn == 100.0
        assert firms[2].aum_usd_bn == 10.0

    def test_fields_extracted_correctly(self, tmp_path: Path) -> None:
        payload = {
            "universe": [
                {
                    "firm_id": "FIRM-042",
                    "firm_name": "Patria Investments Limited",
                    "ticker": "PAX",
                    "latest_aum_usd_bn": 42.5,
                }
            ]
        }
        p = tmp_path / "peer_universe.json"
        _write_json(p, payload)
        firms = load_firms(p)
        assert len(firms) == 1
        f = firms[0]
        assert f.firm_id == "FIRM-042"
        assert f.firm_name == "Patria Investments Limited"
        assert f.ticker == "PAX"
        assert f.aum_usd_bn == 42.5

    def test_empty_universe_returns_empty_list(self, tmp_path: Path) -> None:
        p = tmp_path / "peer_universe.json"
        _write_json(p, {"universe": []})
        assert load_firms(p) == []

    def test_missing_aum_defaults_to_zero(self, tmp_path: Path) -> None:
        payload = {
            "universe": [
                {"firm_id": "FIRM-001", "firm_name": "No AUM Co", "ticker": "NAC"}
            ]
        }
        p = tmp_path / "peer_universe.json"
        _write_json(p, payload)
        firms = load_firms(p)
        assert firms[0].aum_usd_bn == 0.0

    def test_firm_id_whitespace_stripped(self, tmp_path: Path) -> None:
        payload = {
            "universe": [
                {"firm_id": "  FIRM-001  ", "firm_name": "Test", "ticker": "TST", "latest_aum_usd_bn": 50.0}
            ]
        }
        p = tmp_path / "peer_universe.json"
        _write_json(p, payload)
        firms = load_firms(p)
        assert firms[0].firm_id == "FIRM-001"

    def test_returns_list_of_firm_records(self, tmp_path: Path) -> None:
        payload = {
            "universe": [
                {"firm_id": "FIRM-001", "firm_name": "Test Co", "ticker": "TST", "latest_aum_usd_bn": 100.0}
            ]
        }
        p = tmp_path / "peer_universe.json"
        _write_json(p, payload)
        firms = load_firms(p)
        assert all(isinstance(f, FirmRecord) for f in firms)

    def test_multiple_firms_all_loaded(self, tmp_path: Path) -> None:
        payload = {
            "universe": [
                {"firm_id": f"FIRM-{i:03d}", "firm_name": f"Co {i}", "ticker": f"C{i}", "latest_aum_usd_bn": float(i * 10)}
                for i in range(1, 6)
            ]
        }
        p = tmp_path / "peer_universe.json"
        _write_json(p, payload)
        firms = load_firms(p)
        assert len(firms) == 5


# ---------------------------------------------------------------------------
# load_metrics
# ---------------------------------------------------------------------------

class TestLoadMetrics:
    def test_metrics_loaded_correctly(self, tmp_path: Path) -> None:
        payload = {
            "metrics": [
                {
                    "metric_id": "MET-VD-001",
                    "name": "DE/share",
                    "abbreviation": "DE/share",
                    "category": "driver",
                    "is_driver_candidate": True,
                    "calculation_notes": "",
                }
            ]
        }
        p = tmp_path / "metric_taxonomy.json"
        _write_json(p, payload)
        metrics = load_metrics(p)
        assert len(metrics) == 1
        m = metrics[0]
        assert m.metric_id == "MET-VD-001"
        assert m.name == "DE/share"
        assert m.abbreviation == "DE/share"
        assert m.category == "driver"
        assert m.is_driver_candidate is True
        assert m.calculation_notes == ""

    def test_empty_metrics_list_returns_empty(self, tmp_path: Path) -> None:
        p = tmp_path / "metric_taxonomy.json"
        _write_json(p, {"metrics": []})
        assert load_metrics(p) == []

    def test_is_driver_candidate_false_loaded(self, tmp_path: Path) -> None:
        payload = {
            "metrics": [
                {
                    "metric_id": "MET-VD-002",
                    "name": "P/FRE",
                    "abbreviation": "P/FRE",
                    "category": "valuation_multiples",
                    "is_driver_candidate": False,
                    "calculation_notes": "",
                }
            ]
        }
        p = tmp_path / "metric_taxonomy.json"
        _write_json(p, payload)
        metrics = load_metrics(p)
        assert metrics[0].is_driver_candidate is False

    def test_missing_is_driver_candidate_defaults_false(self, tmp_path: Path) -> None:
        payload = {
            "metrics": [
                {
                    "metric_id": "MET-VD-003",
                    "name": "Some metric",
                    "abbreviation": "sm",
                    "category": "driver",
                    "calculation_notes": "",
                }
            ]
        }
        p = tmp_path / "metric_taxonomy.json"
        _write_json(p, payload)
        metrics = load_metrics(p)
        assert metrics[0].is_driver_candidate is False

    def test_returns_list_of_metric_records(self, tmp_path: Path) -> None:
        payload = {
            "metrics": [
                {
                    "metric_id": "MET-VD-001",
                    "name": "DE/share",
                    "abbreviation": "DE/share",
                    "category": "driver",
                    "is_driver_candidate": True,
                    "calculation_notes": "",
                }
            ]
        }
        p = tmp_path / "metric_taxonomy.json"
        _write_json(p, payload)
        metrics = load_metrics(p)
        assert all(isinstance(m, MetricRecord) for m in metrics)

    def test_calculation_notes_whitespace_stripped(self, tmp_path: Path) -> None:
        payload = {
            "metrics": [
                {
                    "metric_id": "MET-VD-001",
                    "name": "ratio",
                    "abbreviation": "r",
                    "category": "driver",
                    "is_driver_candidate": True,
                    "calculation_notes": "  FRE / Revenue  ",
                }
            ]
        }
        p = tmp_path / "metric_taxonomy.json"
        _write_json(p, payload)
        metrics = load_metrics(p)
        assert metrics[0].calculation_notes == "FRE / Revenue"

    def test_multiple_metrics_all_loaded(self, tmp_path: Path) -> None:
        payload = {
            "metrics": [
                {
                    "metric_id": f"MET-VD-{i:03d}",
                    "name": f"metric {i}",
                    "abbreviation": f"m{i}",
                    "category": "driver",
                    "is_driver_candidate": True,
                    "calculation_notes": "",
                }
                for i in range(1, 8)
            ]
        }
        p = tmp_path / "metric_taxonomy.json"
        _write_json(p, payload)
        metrics = load_metrics(p)
        assert len(metrics) == 7


# ---------------------------------------------------------------------------
# build_firm_checklist
# ---------------------------------------------------------------------------

class TestBuildFirmChecklist:
    def test_each_firm_has_entry_for_every_metric(self) -> None:
        firm = _make_firm()
        metrics = [
            _make_metric(metric_id=f"MET-VD-{i:03d}", name=f"metric {i}")
            for i in range(5)
        ]
        checklist = build_firm_checklist(firm, metrics)
        assert len(checklist["metrics"]) == 5

    def test_checklist_contains_correct_firm_fields(self) -> None:
        firm = _make_firm(firm_id="FIRM-007", ticker="BX")
        checklist = build_firm_checklist(firm, [_make_metric()])
        assert checklist["firm_id"] == "FIRM-007"
        assert checklist["ticker"] == "BX"

    def test_metric_entry_has_required_keys(self) -> None:
        checklist = build_firm_checklist(_make_firm(), [_make_metric()])
        entry = checklist["metrics"][0]
        for key in ("metric_id", "metric_name", "category", "collection_priority", "derivable_from", "status"):
            assert key in entry, f"Missing key: {key}"

    def test_status_is_pending(self) -> None:
        checklist = build_firm_checklist(_make_firm(), [_make_metric()])
        assert checklist["metrics"][0]["status"] == "pending"

    def test_metric_entry_ids_match_input(self) -> None:
        metric = _make_metric(metric_id="MET-VD-042", name="custom metric")
        checklist = build_firm_checklist(_make_firm(), [metric])
        entry = checklist["metrics"][0]
        assert entry["metric_id"] == "MET-VD-042"
        assert entry["metric_name"] == "custom metric"

    def test_priority_assigned_per_metric(self) -> None:
        metrics = [
            _make_metric(
                metric_id="MET-VD-001",
                name="DE/share",
                abbreviation="DE/share",
                category="driver",
                is_driver_candidate=True,
            ),
            _make_metric(
                metric_id="MET-VD-002",
                name="P/FRE",
                abbreviation="P/FRE",
                category="valuation_multiples",
                is_driver_candidate=False,
            ),
        ]
        checklist = build_firm_checklist(_make_firm(), metrics)
        priorities = {e["metric_id"]: e["collection_priority"] for e in checklist["metrics"]}
        assert priorities["MET-VD-001"] == "high"
        assert priorities["MET-VD-002"] == "critical"

    def test_derivable_from_populated_for_medium_priority(self) -> None:
        metric = _make_metric(
            name="custom ratio",
            abbreviation="cr",
            category="driver",
            is_driver_candidate=True,
            calculation_notes="FRE / Revenue",
        )
        checklist = build_firm_checklist(_make_firm(), [metric])
        entry = checklist["metrics"][0]
        assert entry["collection_priority"] == "medium"
        assert entry["derivable_from"] is not None

    def test_derivable_from_none_for_high_priority(self) -> None:
        # High-priority metric should have derivable_from=None even if notes contain a formula.
        metric = _make_metric(
            name="DE/share",
            abbreviation="DE/share",
            category="driver",
            is_driver_candidate=True,
            calculation_notes="FRE / Revenue",
        )
        checklist = build_firm_checklist(_make_firm(), [metric])
        entry = checklist["metrics"][0]
        assert entry["collection_priority"] == "high"
        assert entry["derivable_from"] is None

    def test_empty_metrics_list_produces_empty_checklist(self) -> None:
        checklist = build_firm_checklist(_make_firm(), [])
        assert checklist["metrics"] == []

    def test_all_entries_have_status_pending(self) -> None:
        metrics = [
            _make_metric(metric_id=f"MET-VD-{i:03d}", name=f"m{i}")
            for i in range(10)
        ]
        checklist = build_firm_checklist(_make_firm(), metrics)
        assert all(e["status"] == "pending" for e in checklist["metrics"])

    def test_category_field_carried_through(self) -> None:
        metric = _make_metric(category="valuation_multiples", is_driver_candidate=False, abbreviation="P/FRE")
        checklist = build_firm_checklist(_make_firm(), [metric])
        assert checklist["metrics"][0]["category"] == "valuation_multiples"


# ---------------------------------------------------------------------------
# generate_checklist (integration with synthetic tmp_path fixtures)
# ---------------------------------------------------------------------------

class TestGenerateChecklist:
    def _build_universe(self, n: int = 3) -> dict:
        return {
            "universe": [
                {
                    "firm_id": f"FIRM-{i:03d}",
                    "firm_name": f"Firm {i}",
                    "ticker": f"F{i:02d}",
                    "latest_aum_usd_bn": float(100 - i),
                }
                for i in range(1, n + 1)
            ]
        }

    def _build_taxonomy(self) -> dict:
        return {
            "metrics": [
                {
                    "metric_id": "MET-VD-001",
                    "name": "DE/share",
                    "abbreviation": "DE/share",
                    "category": "driver",
                    "is_driver_candidate": True,
                    "calculation_notes": "",
                },
                {
                    "metric_id": "MET-VD-002",
                    "name": "P/FRE",
                    "abbreviation": "P/FRE",
                    "category": "valuation_multiples",
                    "is_driver_candidate": False,
                    "calculation_notes": "",
                },
                {
                    "metric_id": "MET-VD-003",
                    "name": "market size",
                    "abbreviation": "mktsize",
                    "category": "market_structure",
                    "is_driver_candidate": False,
                    "calculation_notes": "",
                },
            ]
        }

    def _make_args(
        self,
        run_dir: Path,
        peer_universe_path: Path,
        taxonomy_path: Path,
        output_dir: Path,
    ) -> argparse.Namespace:
        return argparse.Namespace(
            run_dir=str(run_dir),
            peer_universe=str(peer_universe_path),
            metric_taxonomy=str(taxonomy_path),
            output_dir=str(output_dir),
        )

    def test_output_file_created(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "run"
        universe_path = tmp_path / "peer_universe.json"
        taxonomy_path = tmp_path / "metric_taxonomy.json"
        output_dir = tmp_path / "2-data"
        _write_json(universe_path, self._build_universe(3))
        _write_json(taxonomy_path, self._build_taxonomy())
        generate_checklist(self._make_args(run_dir, universe_path, taxonomy_path, output_dir))
        assert (output_dir / "metric_checklist.json").exists()

    def test_metadata_firm_and_metric_counts(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "run"
        universe_path = tmp_path / "peer_universe.json"
        taxonomy_path = tmp_path / "metric_taxonomy.json"
        output_dir = tmp_path / "2-data"
        _write_json(universe_path, self._build_universe(9))
        _write_json(taxonomy_path, self._build_taxonomy())
        generate_checklist(self._make_args(run_dir, universe_path, taxonomy_path, output_dir))
        checklist = json.loads((output_dir / "metric_checklist.json").read_text())
        assert checklist["metadata"]["total_firms"] == 9
        assert checklist["metadata"]["total_metrics"] == 3
        # Only DE/share is a driver candidate.
        assert checklist["metadata"]["driver_metrics"] == 1

    def test_tier_sizes_recorded_in_metadata(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "run"
        universe_path = tmp_path / "peer_universe.json"
        taxonomy_path = tmp_path / "metric_taxonomy.json"
        output_dir = tmp_path / "2-data"
        _write_json(universe_path, self._build_universe(9))
        _write_json(taxonomy_path, self._build_taxonomy())
        generate_checklist(self._make_args(run_dir, universe_path, taxonomy_path, output_dir))
        checklist = json.loads((output_dir / "metric_checklist.json").read_text())
        tiers = checklist["metadata"]["tiers"]
        assert tiers["tier1"] == 3
        assert tiers["tier2"] == 3
        assert tiers["tier3"] == 3

    def test_tiers_contain_all_firms(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "run"
        universe_path = tmp_path / "peer_universe.json"
        taxonomy_path = tmp_path / "metric_taxonomy.json"
        output_dir = tmp_path / "2-data"
        _write_json(universe_path, self._build_universe(9))
        _write_json(taxonomy_path, self._build_taxonomy())
        generate_checklist(self._make_args(run_dir, universe_path, taxonomy_path, output_dir))
        checklist = json.loads((output_dir / "metric_checklist.json").read_text())
        all_firm_ids: list[str] = []
        for tier_key in ("tier1", "tier2", "tier3"):
            all_firm_ids.extend(checklist["tiers"][tier_key]["firms"])
        assert len(all_firm_ids) == 9
        assert len(set(all_firm_ids)) == 9

    def test_each_firm_checklist_has_all_metrics(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "run"
        universe_path = tmp_path / "peer_universe.json"
        taxonomy_path = tmp_path / "metric_taxonomy.json"
        output_dir = tmp_path / "2-data"
        _write_json(universe_path, self._build_universe(3))
        _write_json(taxonomy_path, self._build_taxonomy())
        generate_checklist(self._make_args(run_dir, universe_path, taxonomy_path, output_dir))
        checklist = json.loads((output_dir / "metric_checklist.json").read_text())
        for tier_key in ("tier1", "tier2", "tier3"):
            for firm_entry in checklist["tiers"][tier_key]["checklist"]:
                assert len(firm_entry["metrics"]) == 3

    def test_priority_rules_section_present(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "run"
        universe_path = tmp_path / "peer_universe.json"
        taxonomy_path = tmp_path / "metric_taxonomy.json"
        output_dir = tmp_path / "2-data"
        _write_json(universe_path, self._build_universe(3))
        _write_json(taxonomy_path, self._build_taxonomy())
        generate_checklist(self._make_args(run_dir, universe_path, taxonomy_path, output_dir))
        checklist = json.loads((output_dir / "metric_checklist.json").read_text())
        assert "priority_rules" in checklist
        for key in ("critical", "high", "medium", "low", "skip"):
            assert key in checklist["priority_rules"]

    def test_return_value_contains_checklist_path_and_counts(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "run"
        universe_path = tmp_path / "peer_universe.json"
        taxonomy_path = tmp_path / "metric_taxonomy.json"
        output_dir = tmp_path / "2-data"
        _write_json(universe_path, self._build_universe(3))
        _write_json(taxonomy_path, self._build_taxonomy())
        result = generate_checklist(self._make_args(run_dir, universe_path, taxonomy_path, output_dir))
        assert "checklist_path" in result
        assert result["total_firms"] == 3
        assert result["total_metrics"] == 3

    def test_default_paths_from_run_dir(self, tmp_path: Path) -> None:
        # When peer_universe and metric_taxonomy are None, paths default to
        # <run_dir>/1-universe/*.json and output to <run_dir>/2-data/.
        run_dir = tmp_path / "run"
        _write_json(run_dir / "1-universe" / "peer_universe.json", self._build_universe(3))
        _write_json(run_dir / "1-universe" / "metric_taxonomy.json", self._build_taxonomy())
        args = argparse.Namespace(
            run_dir=str(run_dir),
            peer_universe=None,
            metric_taxonomy=None,
            output_dir=None,
        )
        generate_checklist(args)
        assert (run_dir / "2-data" / "metric_checklist.json").exists()

    def test_pax_universe_size_23_firms_tier_split(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "run"
        universe_path = tmp_path / "peer_universe.json"
        taxonomy_path = tmp_path / "metric_taxonomy.json"
        output_dir = tmp_path / "2-data"
        _write_json(universe_path, self._build_universe(23))
        _write_json(taxonomy_path, self._build_taxonomy())
        generate_checklist(self._make_args(run_dir, universe_path, taxonomy_path, output_dir))
        checklist = json.loads((output_dir / "metric_checklist.json").read_text())
        tiers = checklist["metadata"]["tiers"]
        assert tiers["tier1"] == 8
        assert tiers["tier2"] == 8
        assert tiers["tier3"] == 7

    def test_critical_skip_and_high_priorities_in_output(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "run"
        universe_path = tmp_path / "peer_universe.json"
        taxonomy_path = tmp_path / "metric_taxonomy.json"
        output_dir = tmp_path / "2-data"
        _write_json(universe_path, self._build_universe(3))
        _write_json(taxonomy_path, self._build_taxonomy())
        generate_checklist(self._make_args(run_dir, universe_path, taxonomy_path, output_dir))
        checklist = json.loads((output_dir / "metric_checklist.json").read_text())
        metrics_by_id = {
            e["metric_id"]: e["collection_priority"]
            for e in checklist["tiers"]["tier1"]["checklist"][0]["metrics"]
        }
        assert metrics_by_id["MET-VD-001"] == "high"       # DE/share
        assert metrics_by_id["MET-VD-002"] == "critical"   # P/FRE (valuation_multiples)
        assert metrics_by_id["MET-VD-003"] == "skip"       # market_structure

    def test_all_entries_have_pending_status(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "run"
        universe_path = tmp_path / "peer_universe.json"
        taxonomy_path = tmp_path / "metric_taxonomy.json"
        output_dir = tmp_path / "2-data"
        _write_json(universe_path, self._build_universe(6))
        _write_json(taxonomy_path, self._build_taxonomy())
        generate_checklist(self._make_args(run_dir, universe_path, taxonomy_path, output_dir))
        checklist = json.loads((output_dir / "metric_checklist.json").read_text())
        for tier_key in ("tier1", "tier2", "tier3"):
            for firm_entry in checklist["tiers"][tier_key]["checklist"]:
                for entry in firm_entry["metrics"]:
                    assert entry["status"] == "pending"

    def test_derivable_from_non_empty_string_when_set(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "run"
        universe_path = tmp_path / "peer_universe.json"
        taxonomy_path = tmp_path / "metric_taxonomy.json"
        output_dir = tmp_path / "2-data"
        taxonomy = {
            "metrics": [
                {
                    "metric_id": "MET-VD-001",
                    "name": "fre yoy",
                    "abbreviation": "fre yoy",
                    "category": "driver",
                    "is_driver_candidate": True,
                    "calculation_notes": "FRE_t / FRE_t1 - 1",
                }
            ]
        }
        _write_json(universe_path, self._build_universe(3))
        _write_json(taxonomy_path, taxonomy)
        generate_checklist(self._make_args(run_dir, universe_path, taxonomy_path, output_dir))
        checklist = json.loads((output_dir / "metric_checklist.json").read_text())
        entry = checklist["tiers"]["tier1"]["checklist"][0]["metrics"][0]
        assert entry["collection_priority"] == "medium"
        assert isinstance(entry["derivable_from"], str)
        assert len(entry["derivable_from"]) > 0


# ---------------------------------------------------------------------------
# Integration tests against real PAX data (skipped when data is absent)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _pax_data_available, reason="PAX run data not available")
class TestGenerateChecklistWithRealData:
    """End-to-end tests using the actual 2026-03-09-run2 data fixtures."""

    @pytest.fixture(scope="class")
    def checklist(self, tmp_path_factory: pytest.TempPathFactory) -> dict:
        out = tmp_path_factory.mktemp("pax_checklist")
        args = argparse.Namespace(
            run_dir=str(_PAX_RUN_DIR),
            peer_universe=None,
            metric_taxonomy=None,
            output_dir=str(out),
        )
        generate_checklist(args)
        return json.loads((out / "metric_checklist.json").read_text())

    def test_total_firms_is_23(self, checklist: dict) -> None:
        assert checklist["metadata"]["total_firms"] == 23

    def test_total_metrics_is_31(self, checklist: dict) -> None:
        assert checklist["metadata"]["total_metrics"] == 31

    def test_driver_metrics_is_25(self, checklist: dict) -> None:
        assert checklist["metadata"]["driver_metrics"] == 25

    def test_tier_splits_are_8_8_7(self, checklist: dict) -> None:
        tiers = checklist["metadata"]["tiers"]
        assert tiers["tier1"] == 8
        assert tiers["tier2"] == 8
        assert tiers["tier3"] == 7

    def test_each_firm_has_31_metrics(self, checklist: dict) -> None:
        for tier_key in ("tier1", "tier2", "tier3"):
            for firm_entry in checklist["tiers"][tier_key]["checklist"]:
                assert len(firm_entry["metrics"]) == 31, f"Firm {firm_entry['firm_id']} in {tier_key}"

    def test_all_priority_values_valid(self, checklist: dict) -> None:
        valid = {"critical", "high", "medium", "low", "skip"}
        for tier_key in ("tier1", "tier2", "tier3"):
            for firm_entry in checklist["tiers"][tier_key]["checklist"]:
                for entry in firm_entry["metrics"]:
                    assert entry["collection_priority"] in valid

    def test_all_entries_pending(self, checklist: dict) -> None:
        for tier_key in ("tier1", "tier2", "tier3"):
            for firm_entry in checklist["tiers"][tier_key]["checklist"]:
                for entry in firm_entry["metrics"]:
                    assert entry["status"] == "pending"

    def test_each_firm_in_exactly_one_tier(self, checklist: dict) -> None:
        all_ids: list[str] = []
        for tier_key in ("tier1", "tier2", "tier3"):
            all_ids.extend(checklist["tiers"][tier_key]["firms"])
        assert len(all_ids) == 23
        assert len(set(all_ids)) == 23

    def test_bx_in_tier1(self, checklist: dict) -> None:
        assert "FIRM-001" in checklist["tiers"]["tier1"]["firms"]

    def test_pax_in_exactly_one_tier(self, checklist: dict) -> None:
        hits = sum(
            1 for t in ("tier1", "tier2", "tier3")
            if "FIRM-019" in checklist["tiers"][t]["firms"]
        )
        assert hits == 1

    def test_derivable_from_never_empty_string(self, checklist: dict) -> None:
        for tier_key in ("tier1", "tier2", "tier3"):
            for firm_entry in checklist["tiers"][tier_key]["checklist"]:
                for entry in firm_entry["metrics"]:
                    df = entry.get("derivable_from")
                    if df is not None:
                        assert isinstance(df, str) and len(df) > 0


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
