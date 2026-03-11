"""Tests for src/analyzer/claim_indexer.py — claim collection, chain resolution, scoring."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.analyzer._shared import CLAIM_TYPE_CEILINGS, CLM_ID_PATTERN
from src.analyzer.claim_indexer import collect_claims_from_dir, validate_claim


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


from src.analyzer.claim_indexer import generate_matrix_claims, resolve_chains


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
            "CLM-A-01": {
                "id": "CLM-A-01", "type": "factual",
                "evidence": ["CLM-B-01"], "score": 2, "layer": "3-analysis",
            },
            "CLM-B-01": {
                "id": "CLM-B-01", "type": "factual",
                "evidence": ["CLM-A-01"], "score": 2, "layer": "3-analysis",
            },
        }
        # Should not hang — returns whatever it resolved without looping
        result = resolve_chains(claims)
        assert "CLM-A-01" in result
        assert "CLM-B-01" in result

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
