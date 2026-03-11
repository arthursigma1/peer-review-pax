"""Tests for src/analyzer/claim_indexer.py — claim collection, chain resolution, scoring."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.analyzer._shared import CLAIM_TYPE_CEILINGS, CLM_ID_PATTERN
from src.analyzer.claim_indexer import validate_claim


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
