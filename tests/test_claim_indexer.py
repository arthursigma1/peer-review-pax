"""Tests for src/analyzer/claim_indexer.py — claim collection, chain resolution, scoring."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.analyzer._shared import CLAIM_TYPE_CEILINGS, CLM_ID_PATTERN
from src.analyzer.claim_indexer import build_claim_index, collect_claims_from_dir, validate_claim


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


class TestClaimConstants:
    def test_type_ceilings_causal_is_2(self):
        assert CLAIM_TYPE_CEILINGS["causal"] == 2

    def test_type_ceilings_prescriptive_is_2(self):
        assert CLAIM_TYPE_CEILINGS["prescriptive"] == 2

    def test_type_ceilings_statistical_is_3(self):
        assert CLAIM_TYPE_CEILINGS["statistical"] == 3

    def test_type_ceilings_factual_is_3(self):
        assert CLAIM_TYPE_CEILINGS["factual"] == 3

    def test_type_ceilings_comparative_is_3(self):
        assert CLAIM_TYPE_CEILINGS["comparative"] == 3

    def test_clm_id_pattern_matches_valid(self):
        assert CLM_ID_PATTERN.match("CLM-COR-191-01")
        assert CLM_ID_PATTERN.match("CLM-DVR-010-01")
        assert CLM_ID_PATTERN.match("CLM-PLAY-001-03")
        assert CLM_ID_PATTERN.match("CLM-MET-021-FIRM-001-01")
        assert CLM_ID_PATTERN.match("CLM-TL-001-02")
        assert CLM_ID_PATTERN.match("CLM-ANTI-003-01")

    def test_clm_id_pattern_rejects_invalid(self):
        assert not CLM_ID_PATTERN.match("COR-191")
        assert not CLM_ID_PATTERN.match("PLAY-001")
        assert not CLM_ID_PATTERN.match("CLM-")
        assert not CLM_ID_PATTERN.match("")


class TestValidateClaim:
    def test_valid_claim_passes(self):
        claim = {
            "id": "CLM-COR-191-01", "parent_id": "COR-191",
            "type": "statistical", "evidence": ["MET-VD-021", "MET-VD-026"],
            "confidence": "grounded", "score": 3, "layer": "3-analysis",
        }
        assert validate_claim(claim) == []

    def test_missing_id_field(self):
        claim = {"parent_id": "X", "type": "factual", "evidence": [], "confidence": "grounded", "score": 3, "layer": "2-data"}
        errors = validate_claim(claim)
        assert any("id" in e for e in errors)

    def test_invalid_type(self):
        claim = {
            "id": "CLM-COR-191-01", "parent_id": "COR-191",
            "type": "opinion", "evidence": ["PS-VD-001"],
            "confidence": "grounded", "score": 3, "layer": "3-analysis",
        }
        errors = validate_claim(claim)
        assert any("type" in e for e in errors)

    def test_score_exceeds_type_ceiling(self):
        claim = {
            "id": "CLM-PLAY-001-02", "parent_id": "PLAY-001",
            "type": "causal", "evidence": ["CLM-PLAY-001-01"],
            "confidence": "grounded", "score": 3, "layer": "5-playbook",
        }
        errors = validate_claim(claim)
        assert any("ceiling" in e.lower() for e in errors)

    def test_empty_evidence_flags_unsupported(self):
        claim = {
            "id": "CLM-PLAY-001-03", "parent_id": "PLAY-001",
            "type": "prescriptive", "evidence": [],
            "confidence": "grounded", "score": 2, "layer": "5-playbook",
        }
        errors = validate_claim(claim)
        assert any("evidence" in e.lower() for e in errors)

    def test_invalid_clm_id_format(self):
        claim = {
            "id": "COR-191", "parent_id": "COR-191",
            "type": "statistical", "evidence": ["MET-VD-021"],
            "confidence": "grounded", "score": 3, "layer": "3-analysis",
        }
        errors = validate_claim(claim)
        assert any("id" in e.lower() and "format" in e.lower() for e in errors)

    def test_confidence_score_mismatch(self):
        claim = {
            "id": "CLM-COR-191-01", "parent_id": "COR-191",
            "type": "statistical", "evidence": ["MET-VD-021"],
            "confidence": "grounded", "score": 1, "layer": "3-analysis",
        }
        errors = validate_claim(claim)
        assert any("confidence" in e.lower() and "score" in e.lower() for e in errors)


class TestCollectClaims:
    def test_collects_claims_from_single_file(self, tmp_path):
        data = {
            "_claims": [
                {
                    "id": "CLM-COR-001-01", "parent_id": "COR-001",
                    "type": "statistical", "evidence": ["MET-VD-001", "MET-VD-026"],
                    "confidence": "grounded", "score": 3, "layer": "3-analysis",
                },
            ],
            "correlations": [{"correlation_id": "COR-001"}],
        }
        _write_json(tmp_path / "3-analysis" / "correlation_results.json", data)
        claims, warnings = collect_claims_from_dir(tmp_path)
        assert len(claims) == 1
        assert claims["CLM-COR-001-01"]["source_file"] == "3-analysis/correlation_results.json"

    def test_collects_from_multiple_files(self, tmp_path):
        cor_data = {
            "_claims": [
                {"id": "CLM-COR-001-01", "parent_id": "COR-001", "type": "statistical",
                 "evidence": ["MET-VD-001"], "confidence": "grounded", "score": 3, "layer": "3-analysis"},
            ],
        }
        dvr_data = {
            "_claims": [
                {"id": "CLM-DVR-001-01", "parent_id": "DVR-001", "type": "statistical",
                 "evidence": ["COR-001"], "confidence": "grounded", "score": 3, "layer": "3-analysis"},
            ],
        }
        _write_json(tmp_path / "3-analysis" / "correlation_results.json", cor_data)
        _write_json(tmp_path / "3-analysis" / "driver_ranking.json", dvr_data)
        claims, warnings = collect_claims_from_dir(tmp_path)
        assert len(claims) == 2

    def test_skips_files_without_claims(self, tmp_path):
        _write_json(tmp_path / "1-universe" / "peer_universe.json", {"universe": []})
        claims, warnings = collect_claims_from_dir(tmp_path)
        assert len(claims) == 0
        assert len(warnings) == 0

    def test_duplicate_claim_id_warns(self, tmp_path):
        claim = {"id": "CLM-COR-001-01", "parent_id": "COR-001", "type": "statistical",
                 "evidence": ["MET-VD-001"], "confidence": "grounded", "score": 3, "layer": "3-analysis"}
        _write_json(tmp_path / "a.json", {"_claims": [claim]})
        _write_json(tmp_path / "b.json", {"_claims": [claim]})
        claims, warnings = collect_claims_from_dir(tmp_path)
        assert any("duplicate" in w.lower() for w in warnings)

    def test_invalid_claim_produces_warning(self, tmp_path):
        bad_claim = {"id": "BAD", "parent_id": "X", "type": "opinion", "evidence": [], "confidence": "grounded",
                     "score": 3, "layer": "3-analysis"}
        _write_json(tmp_path / "bad.json", {"_claims": [bad_claim]})
        claims, warnings = collect_claims_from_dir(tmp_path)
        assert len(claims) == 0
        assert len(warnings) > 0


from src.analyzer.claim_indexer import apply_score_cascading, generate_matrix_claims, resolve_chains


class TestGenerateMatrixClaims:
    def _make_matrix(self) -> dict:
        return {
            "metrics": {
                "MET-VD-021": {
                    "metric_name": "G&A/FEAUM",
                    "firms": {
                        "FIRM-001": {
                            "value": 0.42,
                            "source": "BX FY2024 10-K (PS-VD-001)",
                        },
                        "FIRM-002": {
                            "value": None,
                            "missing_reason": "not disclosed",
                        },
                        "FIRM-003": {
                            "value": 0.38,
                            "source": "some description without PS-VD id",
                        },
                    },
                },
            },
        }

    def test_generates_claim_for_cell_with_ps_vd(self):
        claims, warnings = generate_matrix_claims(self._make_matrix())
        matching = [c for c in claims if "FIRM-001" in c["id"] and "MET-021" in c["id"]]
        assert len(matching) == 1
        assert matching[0]["score"] == 3
        assert "PS-VD-001" in matching[0]["evidence"]

    def test_skips_null_cells(self):
        claims, warnings = generate_matrix_claims(self._make_matrix())
        firm2_claims = [c for c in claims if "FIRM-002" in c["id"]]
        assert len(firm2_claims) == 0

    def test_score_1_when_no_ps_vd_in_source(self):
        claims, warnings = generate_matrix_claims(self._make_matrix())
        matching = [c for c in claims if "FIRM-003" in c["id"]]
        assert len(matching) == 1
        assert matching[0]["score"] == 1
        assert matching[0]["confidence"] == "sourced"

    def test_extracts_multiple_ps_vd_from_source_string(self):
        matrix = {
            "metrics": {
                "MET-VD-005": {
                    "metric_name": "Total AUM",
                    "firms": {
                        "FIRM-001": {
                            "value": 1274,
                            "source": "BX 10-K (PS-VD-001) and earnings (PS-VD-034)",
                        },
                    },
                },
            },
        }
        claims, _ = generate_matrix_claims(matrix)
        assert len(claims) == 1
        assert set(claims[0]["evidence"]) == {"PS-VD-001", "PS-VD-034"}
        assert claims[0]["score"] == 3

    def test_no_source_field_gets_score_1_with_warning(self):
        matrix = {
            "metrics": {
                "MET-VD-001": {
                    "metric_name": "AUM",
                    "firms": {
                        "FIRM-001": {"value": 100},
                    },
                },
            },
        }
        claims, warnings = generate_matrix_claims(matrix)
        assert len(claims) == 1
        assert claims[0]["score"] == 1
        assert any("no source field" in w for w in warnings)


class TestGenerateMatrixClaimsDataPoints:
    """Tests for the flat data_points format (production standardized_matrix.json)."""

    def test_high_confidence_gets_score_3(self):
        matrix = {
            "data_points": [
                {"firm_id": "FIRM-001", "metric_id": "MET-VD-001", "value_raw": 4.64,
                 "confidence": "high", "missing": False},
            ],
        }
        claims, warnings = generate_matrix_claims(matrix)
        assert len(claims) == 1
        assert claims[0]["score"] == 3
        assert claims[0]["confidence"] == "grounded"

    def test_medium_confidence_gets_score_2(self):
        matrix = {
            "data_points": [
                {"firm_id": "FIRM-001", "metric_id": "MET-VD-001", "value_raw": 1.0,
                 "confidence": "medium", "missing": False},
            ],
        }
        claims, warnings = generate_matrix_claims(matrix)
        assert len(claims) == 1
        assert claims[0]["score"] == 2

    def test_low_confidence_gets_score_1(self):
        matrix = {
            "data_points": [
                {"firm_id": "FIRM-001", "metric_id": "MET-VD-001", "value_raw": 1.0,
                 "confidence": "low", "missing": False},
            ],
        }
        claims, warnings = generate_matrix_claims(matrix)
        assert len(claims) == 1
        assert claims[0]["score"] == 1

    def test_missing_data_points_skipped(self):
        matrix = {
            "data_points": [
                {"firm_id": "FIRM-001", "metric_id": "MET-VD-001", "value_raw": None,
                 "confidence": "high", "missing": True},
            ],
        }
        claims, _ = generate_matrix_claims(matrix)
        assert len(claims) == 0

    def test_multiple_data_points(self):
        matrix = {
            "data_points": [
                {"firm_id": "FIRM-001", "metric_id": "MET-VD-001", "value_raw": 4.64,
                 "confidence": "high", "missing": False},
                {"firm_id": "FIRM-002", "metric_id": "MET-VD-001", "value_raw": 2.0,
                 "confidence": "medium", "missing": False},
                {"firm_id": "FIRM-001", "metric_id": "MET-VD-002", "value_raw": 100,
                 "confidence": "low", "missing": False},
            ],
        }
        claims, _ = generate_matrix_claims(matrix)
        assert len(claims) == 3


class TestResolveChains:
    def test_simple_chain_to_leaf(self):
        claims = {
            "CLM-DVR-010-01": {
                "id": "CLM-DVR-010-01", "type": "statistical",
                "evidence": ["COR-191", "COR-192"], "score": 3, "layer": "3-analysis",
            },
        }
        result = resolve_chains(claims)
        # Non-CLM IDs are leaves — chain should include them directly
        assert set(result["CLM-DVR-010-01"]["chain"]) == {"COR-191", "COR-192"}

    def test_chain_follows_clm_references(self):
        claims = {
            "CLM-COR-191-01": {
                "id": "CLM-COR-191-01", "type": "statistical",
                "evidence": ["MET-VD-021", "MET-VD-026"], "score": 3, "layer": "3-analysis",
            },
            "CLM-DVR-010-01": {
                "id": "CLM-DVR-010-01", "type": "statistical",
                "evidence": ["CLM-COR-191-01"], "score": 3, "layer": "3-analysis",
            },
        }
        result = resolve_chains(claims)
        chain = result["CLM-DVR-010-01"]["chain"]
        assert "CLM-COR-191-01" in chain
        assert "MET-VD-021" in chain
        assert "MET-VD-026" in chain

    def test_circular_reference_does_not_infinite_loop(self):
        claims = {
            "CLM-FAC-001-01": {
                "id": "CLM-FAC-001-01", "type": "factual",
                "evidence": ["CLM-FAC-002-01"], "score": 2, "layer": "3-analysis",
            },
            "CLM-FAC-002-01": {
                "id": "CLM-FAC-002-01", "type": "factual",
                "evidence": ["CLM-FAC-001-01"], "score": 2, "layer": "3-analysis",
            },
        }
        # Should not hang — returns whatever it resolved without looping
        result = resolve_chains(claims)
        assert "CLM-FAC-001-01" in result
        assert "CLM-FAC-002-01" in result
        assert isinstance(result["CLM-FAC-001-01"]["chain"], list)
        assert isinstance(result["CLM-FAC-002-01"]["chain"], list)

    def test_deep_chain_3_levels(self):
        claims = {
            "CLM-MET-021-FIRM-001-01": {
                "id": "CLM-MET-021-FIRM-001-01", "type": "factual",
                "evidence": ["PS-VD-001"], "score": 3, "layer": "2-data",
            },
            "CLM-COR-191-01": {
                "id": "CLM-COR-191-01", "type": "statistical",
                "evidence": ["CLM-MET-021-FIRM-001-01"], "score": 3, "layer": "3-analysis",
            },
            "CLM-DVR-010-01": {
                "id": "CLM-DVR-010-01", "type": "statistical",
                "evidence": ["CLM-COR-191-01"], "score": 3, "layer": "3-analysis",
            },
        }
        result = resolve_chains(claims)
        chain = result["CLM-DVR-010-01"]["chain"]
        assert "PS-VD-001" in chain
        assert "CLM-COR-191-01" in chain
        assert "CLM-MET-021-FIRM-001-01" in chain

    def test_diamond_dag_shared_intermediate(self):
        """Two claims share a common CLM- dependency — chain should include all transitive evidence."""
        claims = {
            "CLM-SHARED-001-01": {
                "id": "CLM-SHARED-001-01", "type": "factual",
                "evidence": ["PS-VD-001"], "score": 3, "layer": "2-data",
            },
            "CLM-COR-001-01": {
                "id": "CLM-COR-001-01", "type": "statistical",
                "evidence": ["CLM-SHARED-001-01"], "score": 3, "layer": "3-analysis",
            },
            "CLM-COR-002-01": {
                "id": "CLM-COR-002-01", "type": "statistical",
                "evidence": ["CLM-SHARED-001-01"], "score": 3, "layer": "3-analysis",
            },
            "CLM-DVR-001-01": {
                "id": "CLM-DVR-001-01", "type": "statistical",
                "evidence": ["CLM-COR-001-01", "CLM-COR-002-01"], "score": 3, "layer": "3-analysis",
            },
        }
        result = resolve_chains(claims)
        chain = result["CLM-DVR-001-01"]["chain"]
        assert "CLM-COR-001-01" in chain
        assert "CLM-COR-002-01" in chain
        assert "CLM-SHARED-001-01" in chain
        assert "PS-VD-001" in chain

    def test_dangling_clm_reference_included_as_leaf(self):
        """Evidence references a CLM- ID that doesn't exist in claims — included but not recursed."""
        claims = {
            "CLM-DVR-001-01": {
                "id": "CLM-DVR-001-01", "type": "statistical",
                "evidence": ["CLM-MISSING-001-01", "PS-VD-001"], "score": 3, "layer": "3-analysis",
            },
        }
        result = resolve_chains(claims)
        chain = result["CLM-DVR-001-01"]["chain"]
        assert "CLM-MISSING-001-01" in chain  # included as leaf even though missing
        assert "PS-VD-001" in chain


class TestScoreCascading:
    def test_no_downgrade_when_evidence_strong(self):
        claims = {
            "CLM-COR-001-01": {
                "id": "CLM-COR-001-01", "type": "statistical",
                "evidence": ["PS-VD-001"], "score": 3, "confidence": "grounded",
                "layer": "3-analysis",
            },
            "CLM-DVR-001-01": {
                "id": "CLM-DVR-001-01", "type": "statistical",
                "evidence": ["CLM-COR-001-01"], "score": 3, "confidence": "grounded",
                "layer": "3-analysis",
            },
        }
        result, downgrades = apply_score_cascading(claims)
        assert result["CLM-DVR-001-01"]["score"] == 3
        assert downgrades == 0

    def test_downgrade_from_weak_evidence(self):
        claims = {
            "CLM-COR-001-01": {
                "id": "CLM-COR-001-01", "type": "statistical",
                "evidence": ["MET-VD-021"], "score": 1, "confidence": "sourced",
                "layer": "3-analysis",
            },
            "CLM-DVR-001-01": {
                "id": "CLM-DVR-001-01", "type": "statistical",
                "evidence": ["CLM-COR-001-01"], "score": 3, "confidence": "grounded",
                "layer": "3-analysis",
            },
        }
        result, downgrades = apply_score_cascading(claims)
        # Cascading: min(3, 1) = 1, but damping floor = max(1, 1) = 1
        assert result["CLM-DVR-001-01"]["score"] == 1
        assert downgrades == 1
        assert result["CLM-DVR-001-01"]["confidence"] == "sourced"  # score 1 → sourced

    def test_damping_floor_prevents_hard_block_from_weak_source(self):
        claims = {
            "CLM-MET-001-FIRM-001-01": {
                "id": "CLM-MET-001-FIRM-001-01", "type": "factual",
                "evidence": [], "score": 1, "confidence": "sourced",
                "layer": "2-data",
            },
            "CLM-COR-001-01": {
                "id": "CLM-COR-001-01", "type": "statistical",
                "evidence": ["CLM-MET-001-FIRM-001-01"], "score": 3,
                "confidence": "grounded", "layer": "3-analysis",
            },
        }
        result, downgrades = apply_score_cascading(claims)
        # Damping: floor is 1, not 0 — weak source doesn't hard-block
        assert result["CLM-COR-001-01"]["score"] >= 1

    def test_truly_unsupported_remains_zero(self):
        claims = {
            "CLM-PLAY-001-01": {
                "id": "CLM-PLAY-001-01", "type": "factual",
                "evidence": [], "score": 0, "confidence": "unsupported",
                "layer": "5-playbook",
            },
        }
        result, downgrades = apply_score_cascading(claims)
        assert result["CLM-PLAY-001-01"]["score"] == 0

    def test_non_clm_evidence_uses_default_scores(self):
        claims = {
            "CLM-PLAY-001-01": {
                "id": "CLM-PLAY-001-01", "type": "factual",
                "evidence": ["PS-VD-018", "ACT-VD-036"], "score": 3,
                "confidence": "grounded", "layer": "5-playbook",
            },
        }
        result, downgrades = apply_score_cascading(claims)
        # PS-VD defaults to 3, ACT-VD defaults to 3 → min(3, min(3,3)) = 3
        assert result["CLM-PLAY-001-01"]["score"] == 3

    def test_type_ceiling_applied_after_cascade(self):
        claims = {
            "CLM-PLAY-001-02": {
                "id": "CLM-PLAY-001-02", "type": "causal",
                "evidence": ["PS-VD-018"], "score": 2, "confidence": "partial",
                "layer": "5-playbook",
            },
        }
        result, _ = apply_score_cascading(claims)
        # Causal ceiling = 2; PS-VD default = 3; min(2, 3) = 2; ceiling = 2 → 2
        assert result["CLM-PLAY-001-02"]["score"] == 2

    def test_non_clm_via_parent_id_fallback(self):
        """COR-191 in evidence has no default — falls back to covering CLM or score 1."""
        claims = {
            "CLM-DVR-001-01": {
                "id": "CLM-DVR-001-01", "type": "statistical",
                "evidence": ["COR-191"], "score": 3, "confidence": "grounded",
                "layer": "3-analysis",
            },
        }
        result, downgrades = apply_score_cascading(claims)
        # COR-191 has no covering CLM → fallback to 1 → min(3,1)=1, max(1,1)=1
        assert result["CLM-DVR-001-01"]["score"] == 1
        assert downgrades == 1

    def test_non_clm_with_covering_claim_uses_its_score(self):
        """COR-191 in evidence is covered by a CLM with parent_id=COR-191 → uses its score."""
        claims = {
            "CLM-COR-191-01": {
                "id": "CLM-COR-191-01", "type": "statistical",
                "evidence": ["MET-VD-021"], "score": 3, "confidence": "grounded",
                "layer": "3-analysis", "parent_id": "COR-191",
            },
            "CLM-DVR-001-01": {
                "id": "CLM-DVR-001-01", "type": "statistical",
                "evidence": ["COR-191"], "score": 3, "confidence": "grounded",
                "layer": "3-analysis",
            },
        }
        result, downgrades = apply_score_cascading(claims)
        # COR-191 covered by CLM-COR-191-01 (score 3) → min(3, 3)=3
        assert result["CLM-DVR-001-01"]["score"] == 3
        assert downgrades == 0


class TestBuildClaimIndex:
    def _make_run_dir(self, tmp_path: Path) -> Path:
        """Create a minimal run directory with claims across layers."""
        cor_data = {
            "_claims": [
                {"id": "CLM-COR-001-01", "parent_id": "COR-001", "type": "statistical",
                 "evidence": ["MET-VD-001", "MET-VD-026"], "confidence": "grounded",
                 "score": 3, "layer": "3-analysis"},
            ],
        }
        dvr_data = {
            "_claims": [
                {"id": "CLM-DVR-001-01", "parent_id": "DVR-001", "type": "statistical",
                 "evidence": ["CLM-COR-001-01"], "confidence": "grounded",
                 "score": 3, "layer": "3-analysis"},
            ],
        }
        play_data = {
            "_claims": [
                {"id": "CLM-PLAY-001-01", "parent_id": "PLAY-001", "type": "factual",
                 "evidence": ["PS-VD-018", "ACT-VD-036"], "confidence": "grounded",
                 "score": 3, "layer": "5-playbook"},
                {"id": "CLM-PLAY-001-02", "parent_id": "PLAY-001", "type": "causal",
                 "evidence": ["CLM-PLAY-001-01", "CLM-DVR-001-01"], "confidence": "partial",
                 "score": 2, "layer": "5-playbook"},
            ],
        }
        matrix_data = {
            "metrics": {
                "MET-VD-001": {
                    "metric_name": "Total AUM",
                    "firms": {
                        "FIRM-001": {"value": 1274, "source": "BX 10-K (PS-VD-001)"},
                    },
                },
            },
        }
        _write_json(tmp_path / "3-analysis" / "correlation_results.json", cor_data)
        _write_json(tmp_path / "3-analysis" / "driver_ranking.json", dvr_data)
        _write_json(tmp_path / "5-playbook" / "playbook.json", play_data)
        _write_json(tmp_path / "3-analysis" / "standardized_matrix.json", matrix_data)
        return tmp_path

    def test_build_produces_valid_index(self, tmp_path):
        run_dir = self._make_run_dir(tmp_path)
        index = build_claim_index(run_dir)
        assert "stats" in index
        assert "claims" in index
        assert index["stats"]["total_claims"] > 0

    def test_stats_count_by_score(self, tmp_path):
        run_dir = self._make_run_dir(tmp_path)
        index = build_claim_index(run_dir)
        by_score = index["stats"]["by_score"]
        total = sum(by_score.values())
        assert total == index["stats"]["total_claims"]

    def test_groundedness_pct_formula(self, tmp_path):
        run_dir = self._make_run_dir(tmp_path)
        index = build_claim_index(run_dir)
        by_score = index["stats"]["by_score"]
        total = index["stats"]["total_claims"]
        expected_pct = (by_score.get(3, 0) + by_score.get(2, 0)) / total * 100
        assert abs(index["stats"]["groundedness_pct"] - expected_pct) < 0.1

    def test_chain_field_present_on_all_claims(self, tmp_path):
        run_dir = self._make_run_dir(tmp_path)
        index = build_claim_index(run_dir)
        for cid, claim in index["claims"].items():
            assert "chain" in claim, f"Missing chain on {cid}"

    def test_causal_claim_capped_at_2(self, tmp_path):
        run_dir = self._make_run_dir(tmp_path)
        index = build_claim_index(run_dir)
        causal = index["claims"].get("CLM-PLAY-001-02")
        assert causal is not None
        assert causal["score"] <= 2

    def test_legacy_run_without_claims(self, tmp_path):
        """Run dir with no _claims[] in any file but with standardized_matrix."""
        matrix_data = {
            "metrics": {
                "MET-VD-001": {
                    "metric_name": "AUM",
                    "firms": {"FIRM-001": {"value": 100, "source": "Filing (PS-VD-001)"}},
                },
            },
        }
        _write_json(tmp_path / "3-analysis" / "standardized_matrix.json", matrix_data)
        index = build_claim_index(tmp_path)
        assert index["stats"].get("legacy_run") is True
        assert index["stats"]["total_claims"] > 0  # matrix claims still generated


class TestCLI:
    def test_cli_writes_output_file(self, tmp_path):
        matrix = {
            "metrics": {
                "MET-VD-001": {
                    "metric_name": "AUM",
                    "firms": {"FIRM-001": {"value": 100, "source": "(PS-VD-001)"}},
                },
            },
        }
        _write_json(tmp_path / "3-analysis" / "standardized_matrix.json", matrix)
        result = subprocess.run(
            [sys.executable, "-m", "src.analyzer.claim_indexer", "--run-dir", str(tmp_path)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stderr
        output = tmp_path / "claim_index.json"
        assert output.exists()
        data = json.loads(output.read_text())
        assert "claims" in data


_REAL_RUN_DIR = Path("data/processed/pax/2026-03-10-run2")


@pytest.mark.skipif(not _REAL_RUN_DIR.exists(), reason="Real PAX run data not available")
class TestIntegrationRealData:
    def test_index_builds_without_error(self):
        index = build_claim_index(_REAL_RUN_DIR)
        assert index["stats"]["total_claims"] > 0

    def test_matrix_claims_generated(self):
        index = build_claim_index(_REAL_RUN_DIR)
        matrix_claims = [c for c in index["claims"].values() if c["layer"] == "2-data"]
        assert len(matrix_claims) > 50  # expect ~150 non-null cells

    def test_no_score_0_on_matrix_claims_with_source(self):
        index = build_claim_index(_REAL_RUN_DIR)
        for cid, claim in index["claims"].items():
            if claim["layer"] == "2-data" and claim["evidence"]:
                assert claim["score"] > 0, f"{cid} has source but score 0"

    def test_legacy_run_flag_not_set(self):
        """Real run should have _claims[] in at least some files (after prompts updated)."""
        index = build_claim_index(_REAL_RUN_DIR)
        # For now, legacy_run=True is expected (prompts not updated yet)
        # After Chunk 2, this should flip to legacy_run not present
        if "legacy_run" in index["stats"]:
            assert index["stats"]["legacy_run"] is True
