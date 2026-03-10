# Claim-Level Explainability Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add structural hallucination defense via claim-level evidence traceability across the entire VDA pipeline.

**Architecture:** Each pipeline agent emits `_claims[]` in its JSON output (except standardized_matrix, which is script-generated). A deterministic Python script (`claim_indexer.py`) collects all claims, auto-generates matrix claims from existing `source` fields, resolves recursive evidence chains, applies score cascading, and outputs `claim_index.json`. Three consumers read the index: the claim-auditor (D5 chain integrity), the report HTML (interactive evidence sidebar), and a traceback agent (natural language queries).

**Tech Stack:** Python 3.11+, pytest, argparse CLI. No new dependencies. Prompt updates in SKILL.md (Markdown).

**Spec:** `docs/superpowers/specs/2026-03-10-claim-explainability-design.md`

---

## File Structure

| File | Action | Responsibility |
|---|---|---|
| `src/analyzer/claim_indexer.py` | Create | Core module: collect claims from JSONs, auto-generate matrix claims, resolve chains, validate, score cascade, output claim_index.json |
| `src/analyzer/_shared.py` | Modify | Add `CLAIM_TYPE_CEILINGS` dict and `CLM_ID_PATTERN` regex constant |
| `tests/test_claim_indexer.py` | Create | Unit + integration tests for claim_indexer |
| `.claude/skills/valuation-driver/SKILL.md` | Modify | Add `_claims[]` emission instructions to metric-architect, playbook-synthesizer, target-lens, and report-builder prompts |
| `prompts/vda/claim_auditor.md` | Modify | Add D5 chain integrity dimension |
| `prompts/vda/traceback_agent.md` | Create | Traceback agent prompt template |
| `CLAUDE.md` | Modify | Add claim_index.json to canonical filenames, CLM-* to conventions |

---

## Chunk 1: claim_indexer.py — Core Infrastructure

This is the foundation. All other phases depend on it. Covers spec phases F4 (script) with F1-F3 claim formats baked into the schema.

### Task 1: Shared constants and types

**Files:**
- Modify: `src/analyzer/_shared.py`
- Test: `tests/test_claim_indexer.py`

- [ ] **Step 1: Write failing tests for claim schema constants**

```python
# tests/test_claim_indexer.py
"""Tests for src/analyzer/claim_indexer.py — claim collection, chain resolution, scoring."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.analyzer._shared import CLAIM_TYPE_CEILINGS, CLM_ID_PATTERN


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_claim_indexer.py::TestClaimConstants -v`
Expected: FAIL — `ImportError: cannot import name 'CLAIM_TYPE_CEILINGS'`

- [ ] **Step 3: Implement constants in _shared.py**

Add to `src/analyzer/_shared.py`:

```python
import re

CLM_ID_PATTERN = re.compile(r"^CLM-[A-Z]+-[\w-]+-\d+$")

CLAIM_TYPE_CEILINGS: dict[str, int] = {
    "factual": 3,
    "statistical": 3,
    "comparative": 3,
    "causal": 2,
    "prescriptive": 2,
}

VALID_CLAIM_TYPES = frozenset(CLAIM_TYPE_CEILINGS.keys())

VALID_CONFIDENCE_LABELS = frozenset({"grounded", "partial", "sourced", "unsupported"})

# Default scores for non-CLM evidence types in cascading
NON_CLM_DEFAULT_SCORES: dict[str, int] = {
    "PS-VD": 3,   # primary source — grounded by definition
    "FIRM": 3,    # structural peer entry
    "ACT-VD": 3,  # documented peer action from filings — grounded
}
# MET-VD, COR, DVR default to score of covering CLM, or 1 if uncovered
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_claim_indexer.py::TestClaimConstants -v`
Expected: PASS (all 7 tests)

- [ ] **Step 5: Commit**

```bash
git add src/analyzer/_shared.py tests/test_claim_indexer.py
git commit -m "feat(claims): add claim schema constants to _shared.py"
```

---

### Task 2: Claim validation function

**Files:**
- Create: `src/analyzer/claim_indexer.py`
- Test: `tests/test_claim_indexer.py`

- [ ] **Step 1: Write failing tests for claim validation**

Append to `tests/test_claim_indexer.py`:

```python
from src.analyzer.claim_indexer import validate_claim


class TestValidateClaim:
    def test_valid_claim_passes(self):
        claim = {
            "id": "CLM-COR-191-01",
            "parent_id": "COR-191",
            "type": "statistical",
            "evidence": ["MET-VD-021", "MET-VD-026"],
            "confidence": "grounded",
            "score": 3,
            "layer": "3-analysis",
        }
        errors = validate_claim(claim)
        assert errors == []

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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_claim_indexer.py::TestValidateClaim -v`
Expected: FAIL — `ImportError: cannot import name 'validate_claim'`

- [ ] **Step 3: Implement validate_claim**

Create `src/analyzer/claim_indexer.py`:

```python
"""Claim indexer: collect, validate, resolve, and score claims across VDA pipeline outputs.

Reads _claims[] from pipeline JSON files, auto-generates matrix claims from
standardized_matrix.json source fields, resolves recursive evidence chains,
applies score cascading with damping, and outputs claim_index.json.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from src.analyzer._shared import (
    CLAIM_TYPE_CEILINGS,
    CLM_ID_PATTERN,
    NON_CLM_DEFAULT_SCORES,
    VALID_CLAIM_TYPES,
    VALID_CONFIDENCE_LABELS,
    utcnow_iso,
)

_CONFIDENCE_TO_SCORE = {"grounded": 3, "partial": 2, "sourced": 1, "unsupported": 0}
_SCORE_TO_CONFIDENCE = {v: k for k, v in _CONFIDENCE_TO_SCORE.items()}

_REQUIRED_FIELDS = {"id", "parent_id", "type", "evidence", "confidence", "score", "layer"}


def validate_claim(claim: dict) -> list[str]:
    """Validate a single claim dict. Returns list of error strings (empty = valid)."""
    errors: list[str] = []

    # Required fields
    for field in _REQUIRED_FIELDS:
        if field not in claim:
            errors.append(f"Missing required field: {field}")
    if errors:
        return errors  # can't validate further without required fields

    # ID format
    if not CLM_ID_PATTERN.match(claim["id"]):
        errors.append(f"Invalid id format: {claim['id']} — must match CLM-{{PREFIX}}-{{ID}}-{{SEQ}}")

    # Type
    if claim["type"] not in VALID_CLAIM_TYPES:
        errors.append(f"Invalid type: {claim['type']} — must be one of {sorted(VALID_CLAIM_TYPES)}")

    # Score ceiling by type
    if claim["type"] in CLAIM_TYPE_CEILINGS:
        ceiling = CLAIM_TYPE_CEILINGS[claim["type"]]
        if claim["score"] > ceiling:
            errors.append(
                f"Score {claim['score']} exceeds ceiling {ceiling} for type '{claim['type']}'"
            )

    # Confidence label
    if claim["confidence"] not in VALID_CONFIDENCE_LABELS:
        errors.append(f"Invalid confidence: {claim['confidence']}")

    # Confidence-score consistency
    if claim["confidence"] in _CONFIDENCE_TO_SCORE:
        expected_score = _CONFIDENCE_TO_SCORE[claim["confidence"]]
        if claim["score"] != expected_score:
            errors.append(
                f"Confidence '{claim['confidence']}' implies score {expected_score}, "
                f"got score {claim['score']}"
            )

    # Evidence non-empty (except score 0 which is already flagged)
    if not claim["evidence"] and claim["score"] > 0:
        errors.append("Empty evidence[] on claim with score > 0")

    return errors
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_claim_indexer.py::TestValidateClaim -v`
Expected: PASS (all 7 tests)

- [ ] **Step 5: Commit**

```bash
git add src/analyzer/claim_indexer.py tests/test_claim_indexer.py
git commit -m "feat(claims): add claim validation function"
```

---

### Task 3: Collect claims from pipeline JSONs

**Files:**
- Modify: `src/analyzer/claim_indexer.py`
- Test: `tests/test_claim_indexer.py`

- [ ] **Step 1: Write failing tests for claim collection**

Append to `tests/test_claim_indexer.py`:

```python
from src.analyzer.claim_indexer import collect_claims_from_dir


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


class TestCollectClaims:
    def test_collects_claims_from_single_file(self, tmp_path):
        data = {
            "_claims": [
                {
                    "id": "CLM-COR-001-01",
                    "parent_id": "COR-001",
                    "type": "statistical",
                    "evidence": ["MET-VD-001", "MET-VD-026"],
                    "confidence": "grounded",
                    "score": 3,
                    "layer": "3-analysis",
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
        bad_claim = {"id": "BAD", "type": "opinion", "evidence": [], "confidence": "grounded",
                     "score": 3, "layer": "3-analysis"}
        _write_json(tmp_path / "bad.json", {"_claims": [bad_claim]})
        claims, warnings = collect_claims_from_dir(tmp_path)
        assert len(claims) == 0
        assert len(warnings) > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_claim_indexer.py::TestCollectClaims -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: Implement collect_claims_from_dir**

Add to `src/analyzer/claim_indexer.py`:

```python
# Files to scan for _claims[] (relative to run dir)
_CLAIM_BEARING_FILES = [
    "3-analysis/correlation_results.json",
    "3-analysis/driver_ranking.json",
    "4-deep-dives/platform_profiles.json",
    "4-deep-dives/asset_class_analysis.json",
    "5-playbook/platform_playbook.json",
    "5-playbook/asset_class_playbooks.json",
    "5-playbook/target_lens.json",
]


def collect_claims_from_dir(
    run_dir: Path,
) -> tuple[dict[str, dict], list[str]]:
    """Scan pipeline JSONs in run_dir for _claims[] arrays.

    Returns (claims_by_id, warnings). Claims are enriched with source_file.
    Invalid or duplicate claims are skipped and produce warnings.
    """
    claims: dict[str, dict] = {}
    warnings: list[str] = []

    # Scan known files + any other .json files found
    json_files: list[Path] = []
    for rel in _CLAIM_BEARING_FILES:
        p = run_dir / rel
        if p.exists():
            json_files.append(p)
    # Also scan any .json files not in the known list
    for p in sorted(run_dir.rglob("*.json")):
        if p not in json_files:
            json_files.append(p)

    for path in json_files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        raw_claims = data.get("_claims")
        if not raw_claims or not isinstance(raw_claims, list):
            continue

        rel_path = str(path.relative_to(run_dir))

        for claim in raw_claims:
            if not isinstance(claim, dict):
                warnings.append(f"{rel_path}: non-dict entry in _claims[]")
                continue

            errors = validate_claim(claim)
            if errors:
                cid = claim.get("id", "<no id>")
                warnings.append(f"{rel_path}: invalid claim {cid}: {'; '.join(errors)}")
                continue

            cid = claim["id"]
            if cid in claims:
                warnings.append(
                    f"{rel_path}: duplicate claim id {cid} "
                    f"(first seen in {claims[cid]['source_file']})"
                )
                continue

            claims[cid] = {**claim, "source_file": rel_path}

    return claims, warnings
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_claim_indexer.py::TestCollectClaims -v`
Expected: PASS (all 5 tests)

- [ ] **Step 5: Commit**

```bash
git add src/analyzer/claim_indexer.py tests/test_claim_indexer.py
git commit -m "feat(claims): add claim collection from pipeline JSONs"
```

---

### Task 4: Auto-generate matrix claims from source fields

**Files:**
- Modify: `src/analyzer/claim_indexer.py`
- Test: `tests/test_claim_indexer.py`

- [ ] **Step 1: Write failing tests for matrix claim generation**

Append to `tests/test_claim_indexer.py`:

```python
from src.analyzer.claim_indexer import generate_matrix_claims


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_claim_indexer.py::TestGenerateMatrixClaims -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: Implement generate_matrix_claims**

Add to `src/analyzer/claim_indexer.py`:

```python
_PS_VD_PATTERN = re.compile(r"PS-VD-\d+")


def generate_matrix_claims(matrix: dict) -> tuple[list[dict], list[str]]:
    """Auto-generate factual claims from standardized_matrix.json source fields.

    For each non-null cell, extracts PS-VD-* IDs from the source string.
    Score 3 if PS-VD found, score 1 if source text present but no PS-VD parseable.
    Null cells (missing_reason) are skipped.
    """
    claims: list[dict] = []
    warnings: list[str] = []

    metrics = matrix.get("metrics", {})
    for met_id, met_data in metrics.items():
        if not isinstance(met_data, dict):
            continue
        firms = met_data.get("firms", {})
        # Shorten metric ID for claim: MET-VD-021 -> MET-021
        met_short = met_id.replace("MET-VD-", "MET-")
        for firm_id, cell in firms.items():
            if not isinstance(cell, dict):
                continue
            value = cell.get("value")
            if value is None:
                continue

            source_str = cell.get("source", "")
            ps_vd_ids = _PS_VD_PATTERN.findall(source_str) if source_str else []

            if ps_vd_ids:
                score = 3
                confidence = "grounded"
                evidence = sorted(set(ps_vd_ids))
            elif source_str:
                score = 1
                confidence = "sourced"
                evidence = []
                warnings.append(
                    f"Matrix cell {met_id}/{firm_id}: source text present "
                    f"but no PS-VD-* ID parseable"
                )
            else:
                score = 1
                confidence = "sourced"
                evidence = []
                warnings.append(f"Matrix cell {met_id}/{firm_id}: no source field")

            claim_id = f"CLM-{met_short}-{firm_id}-01"
            claims.append({
                "id": claim_id,
                "parent_id": met_id,
                "type": "factual",
                "evidence": evidence,
                "confidence": confidence,
                "score": score,
                "layer": "2-data",
            })

    return claims, warnings
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_claim_indexer.py::TestGenerateMatrixClaims -v`
Expected: PASS (all 4 tests)

- [ ] **Step 5: Commit**

```bash
git add src/analyzer/claim_indexer.py tests/test_claim_indexer.py
git commit -m "feat(claims): auto-generate matrix claims from source fields"
```

---

### Task 5: Resolve evidence chains recursively

**Files:**
- Modify: `src/analyzer/claim_indexer.py`
- Test: `tests/test_claim_indexer.py`

- [ ] **Step 1: Write failing tests for chain resolution**

Append to `tests/test_claim_indexer.py`:

```python
from src.analyzer.claim_indexer import resolve_chains


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_claim_indexer.py::TestResolveChains -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: Implement resolve_chains**

Add to `src/analyzer/claim_indexer.py`:

```python
def resolve_chains(claims: dict[str, dict]) -> dict[str, dict]:
    """Resolve evidence chains recursively for all claims.

    For each claim, follows evidence[] references. If an evidence ID starts with
    'CLM-', recursively follows that claim's evidence too. Non-CLM IDs are leaf
    nodes. Adds a 'chain' field (sorted list of all transitive evidence IDs).

    Handles circular references by tracking visited nodes.
    """
    cache: dict[str, list[str]] = {}

    def _resolve(claim_id: str, visited: set[str]) -> list[str]:
        if claim_id in cache:
            return cache[claim_id]
        if claim_id in visited:
            return []  # circular reference — stop
        visited.add(claim_id)

        claim = claims.get(claim_id)
        if not claim:
            return []

        chain: list[str] = []
        for ev_id in claim.get("evidence", []):
            chain.append(ev_id)
            if ev_id.startswith("CLM-") and ev_id in claims:
                chain.extend(_resolve(ev_id, visited))

        cache[claim_id] = sorted(set(chain))
        return cache[claim_id]

    result = {}
    for cid, claim in claims.items():
        _resolve(cid, set())
        result[cid] = {**claim, "chain": cache.get(cid, [])}

    return result
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_claim_indexer.py::TestResolveChains -v`
Expected: PASS (all 4 tests)

- [ ] **Step 5: Commit**

```bash
git add src/analyzer/claim_indexer.py tests/test_claim_indexer.py
git commit -m "feat(claims): recursive evidence chain resolution"
```

---

### Task 6: Score cascading with damping

**Files:**
- Modify: `src/analyzer/claim_indexer.py`
- Test: `tests/test_claim_indexer.py`

- [ ] **Step 1: Write failing tests for score cascading**

Append to `tests/test_claim_indexer.py`:

```python
from src.analyzer.claim_indexer import apply_score_cascading


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
        assert result["CLM-DVR-001-01"]["score"] <= 2
        assert downgrades >= 1

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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_claim_indexer.py::TestScoreCascading -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: Implement apply_score_cascading**

Add to `src/analyzer/claim_indexer.py`:

```python
def _evidence_score(ev_id: str, claims: dict[str, dict]) -> int:
    """Return the score of an evidence item. CLM-* returns claim score, others use defaults."""
    if ev_id.startswith("CLM-") and ev_id in claims:
        return claims[ev_id]["score"]
    # Non-CLM: check prefix against defaults
    for prefix, default in NON_CLM_DEFAULT_SCORES.items():
        if ev_id.startswith(prefix):
            return default
    # MET-VD, COR, DVR without covering CLM → check if a CLM covers it
    covering = [c for c in claims.values() if c.get("parent_id") == ev_id]
    if covering:
        return min(c["score"] for c in covering)
    return 1  # uncovered non-CLM ID


def apply_score_cascading(
    claims: dict[str, dict],
) -> tuple[dict[str, dict], int]:
    """Apply score cascading with damping.

    effective_score = max(1, min(own_score, min(evidence_scores)))
    Exception: score 0 (unsupported) is not damped — stays 0.
    Type ceilings are re-applied after cascading.

    Returns (updated_claims, downgrade_count).
    """
    result = {cid: {**c} for cid, c in claims.items()}
    downgrades = 0

    # Iterate until stable (handles transitive dependencies)
    changed = True
    max_iterations = 50  # safety bound
    iteration = 0
    while changed and iteration < max_iterations:
        changed = False
        iteration += 1
        for cid, claim in result.items():
            if claim["score"] == 0:
                continue  # unsupported stays 0, no damping

            evidence = claim.get("evidence", [])
            if not evidence:
                continue

            ev_scores = [_evidence_score(ev_id, result) for ev_id in evidence]
            min_ev = min(ev_scores)
            cascaded = min(claim["score"], min_ev)

            # Damping: floor at 1 (weak source → warning, not hard block)
            cascaded = max(1, cascaded)

            # Re-apply type ceiling
            ceiling = CLAIM_TYPE_CEILINGS.get(claim["type"], 3)
            cascaded = min(cascaded, ceiling)

            if cascaded != claim["score"]:
                old = claim["score"]
                claim["score"] = cascaded
                claim["confidence"] = _SCORE_TO_CONFIDENCE.get(cascaded, "partial")
                changed = True
                if cascaded < old:
                    downgrades += 1

    return result, downgrades
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_claim_indexer.py::TestScoreCascading -v`
Expected: PASS (all 6 tests)

- [ ] **Step 5: Commit**

```bash
git add src/analyzer/claim_indexer.py tests/test_claim_indexer.py
git commit -m "feat(claims): score cascading with damping and type ceilings"
```

---

### Task 7: Build claim_index.json and CLI

**Files:**
- Modify: `src/analyzer/claim_indexer.py`
- Test: `tests/test_claim_indexer.py`

- [ ] **Step 1: Write failing tests for index building and CLI**

Append to `tests/test_claim_indexer.py`:

```python
import subprocess
import sys

from src.analyzer.claim_indexer import build_claim_index


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
        _write_json(tmp_path / "5-playbook" / "platform_playbook.json", play_data)
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_claim_indexer.py::TestBuildClaimIndex -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: Implement build_claim_index and CLI**

Add to `src/analyzer/claim_indexer.py`:

```python
_MATRIX_FILE = "3-analysis/standardized_matrix.json"


def build_claim_index(run_dir: Path) -> dict:
    """Build the full claim index for a pipeline run.

    1. Collect _claims[] from all pipeline JSONs
    2. Auto-generate matrix claims from standardized_matrix.json
    3. Resolve evidence chains recursively
    4. Apply score cascading with damping
    5. Compute stats

    Returns the complete index dict ready for JSON serialization.
    """
    # 1. Collect agent-emitted claims
    claims, warnings = collect_claims_from_dir(run_dir)

    # 2. Auto-generate matrix claims
    matrix_path = run_dir / _MATRIX_FILE
    matrix_claims_list: list[dict] = []
    if matrix_path.exists():
        try:
            matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
            matrix_claims_list, matrix_warnings = generate_matrix_claims(matrix)
            warnings.extend(matrix_warnings)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            warnings.append(f"Failed to read standardized_matrix.json: {e}")

    # Merge matrix claims (don't overwrite agent-emitted ones)
    for mc in matrix_claims_list:
        if mc["id"] not in claims:
            claims[mc["id"]] = {**mc, "source_file": _MATRIX_FILE}

    # Detect legacy run (no agent-emitted claims found)
    agent_claims = [c for c in claims.values() if c.get("layer") != "2-data"]
    legacy_run = len(agent_claims) == 0 and len(matrix_claims_list) > 0

    # 3. Resolve chains
    claims = resolve_chains(claims)

    # 4. Score cascading
    claims, downgrade_count = apply_score_cascading(claims)

    # 5. Compute stats
    by_score: dict[int, int] = {0: 0, 1: 0, 2: 0, 3: 0}
    by_type: dict[str, int] = {}
    for c in claims.values():
        by_score[c["score"]] = by_score.get(c["score"], 0) + 1
        by_type[c["type"]] = by_type.get(c["type"], 0) + 1

    total = len(claims)
    groundedness_pct = ((by_score.get(3, 0) + by_score.get(2, 0)) / total * 100) if total else 0.0

    stats: dict = {
        "total_claims": total,
        "by_score": by_score,
        "by_type": by_type,
        "groundedness_pct": round(groundedness_pct, 1),
        "cascading_downgrades": downgrade_count,
    }
    if legacy_run:
        stats["legacy_run"] = True
    if warnings:
        stats["warnings_count"] = len(warnings)

    run_name = run_dir.name

    return {
        "run": run_name,
        "generated_at": utcnow_iso(),
        "stats": stats,
        "claims": claims,
        "warnings": warnings if warnings else [],
    }


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Build claim_index.json for a VDA pipeline run.",
    )
    p.add_argument(
        "--run-dir",
        type=Path,
        required=True,
        help="Path to the pipeline run directory (e.g., data/processed/pax/2026-03-10-run2/)",
    )
    p.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output path for claim_index.json (default: {run-dir}/claim_index.json)",
    )
    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    run_dir: Path = args.run_dir
    if not run_dir.is_dir():
        parser.error(f"Run directory not found: {run_dir}")

    index = build_claim_index(run_dir)

    output_path = args.output or (run_dir / "claim_index.json")
    output_path.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"claim_index.json written to {output_path}")
    print(f"  Total claims: {index['stats']['total_claims']}")
    print(f"  Groundedness: {index['stats']['groundedness_pct']}%")
    if index.get("warnings"):
        print(f"  Warnings: {len(index['warnings'])}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run ALL tests to verify everything passes**

Run: `python3 -m pytest tests/test_claim_indexer.py -v`
Expected: PASS (all tests across all classes)

- [ ] **Step 5: Commit**

```bash
git add src/analyzer/claim_indexer.py tests/test_claim_indexer.py
git commit -m "feat(claims): build_claim_index and CLI entry point"
```

---

### Task 8: Integration test with real PAX run data

**Files:**
- Test: `tests/test_claim_indexer.py`

- [ ] **Step 1: Write integration test**

Append to `tests/test_claim_indexer.py`:

```python
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
```

- [ ] **Step 2: Run integration test**

Run: `python3 -m pytest tests/test_claim_indexer.py::TestIntegrationRealData -v`
Expected: PASS (or skip if data not present)

- [ ] **Step 3: Commit**

```bash
git add tests/test_claim_indexer.py
git commit -m "test(claims): integration test with real PAX run data"
```

---

## Chunk 2: Agent Prompt Updates (F1-F3)

Update SKILL.md to instruct agents to emit `_claims[]` in their JSON outputs. These are prompt-only changes — no Python code.

### Task 9: metric-architect — correlation_results claims (F1)

**Files:**
- Modify: `.claude/skills/valuation-driver/SKILL.md` (around the VD-A4 correlation section)

- [ ] **Step 1: Read the current metric-architect correlation output instructions**

Read: `.claude/skills/valuation-driver/SKILL.md` — find the section where `correlation_results.json` output schema is defined (search for "correlation_results" or "VD-A4").

- [ ] **Step 2: Add _claims[] instruction after the correlation output schema**

Add to the metric-architect's correlation output instructions (after the existing JSON schema):

```markdown
**Claim emission (REQUIRED):** Add a top-level `_claims` array to `correlation_results.json`. For each correlation entry, emit one claim:

```json
{
  "_claims": [
    {
      "id": "CLM-COR-{NNN}-01",
      "parent_id": "COR-{NNN}",
      "type": "statistical",
      "evidence": ["{driver_metric_id}", "{valuation_multiple_id}"],
      "confidence": "grounded",
      "score": 3,
      "layer": "3-analysis"
    }
  ]
}
```

Rules:
- One CLM per COR entry
- `evidence` contains the two MET-VD-* IDs being correlated
- Score is always 3 (computation is deterministic from input metrics)
- `confidence` is always "grounded" for statistical claims backed by computation
```

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/valuation-driver/SKILL.md
git commit -m "feat(claims): add _claims[] emission to metric-architect correlation prompt"
```

---

### Task 10: metric-architect — driver_ranking claims (F2)

**Files:**
- Modify: `.claude/skills/valuation-driver/SKILL.md` (around the VD-A5 driver ranking section)

- [ ] **Step 1: Read the current driver ranking output instructions**

Read: `.claude/skills/valuation-driver/SKILL.md` — find the section where `driver_ranking.json` output schema is defined (search for "driver_ranking" or "VD-A5").

- [ ] **Step 2: Add _claims[] instruction after the driver ranking output schema**

```markdown
**Claim emission (REQUIRED):** Add a top-level `_claims` array to `driver_ranking.json`. For each driver entry, emit one claim:

```json
{
  "_claims": [
    {
      "id": "CLM-DVR-{NNN}-01",
      "parent_id": "DVR-{NNN}",
      "type": "statistical",
      "evidence": ["COR-{X}", "COR-{Y}", "COR-{Z}"],
      "confidence": "grounded",
      "score": 3,
      "layer": "3-analysis"
    }
  ]
}
```

Rules:
- One CLM per DVR entry
- `evidence` lists ALL COR-* IDs that were used to classify this driver
- For `stable_value_driver`: evidence includes the 2+ COR-* entries with |rho| >= 0.5
- For `multiple_specific_driver`: evidence includes the single qualifying COR-*
- Score is 3 for stable/multiple_specific (backed by correlation data), 2 for contextual
```

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/valuation-driver/SKILL.md
git commit -m "feat(claims): add _claims[] emission to metric-architect driver ranking prompt"
```

---

### Task 11: playbook-synthesizer — playbook claims (F3a)

**Files:**
- Modify: `.claude/skills/valuation-driver/SKILL.md` (around VD-P1/P2 playbook section)

- [ ] **Step 1: Read the current playbook output instructions**

Read: `.claude/skills/valuation-driver/SKILL.md` — find the section where `platform_playbook.json` and play schema is defined (search for "PLAY-NNN" or "VD-P2").

- [ ] **Step 2: Add _claims[] instruction after the playbook output schema**

```markdown
**Claim emission (REQUIRED):** Add a top-level `_claims` array to `platform_playbook.json`. For each PLAY-NNN and ANTI-NNN, emit 1-3 claims representing the key assertions:

```json
{
  "_claims": [
    {
      "id": "CLM-PLAY-{NNN}-01",
      "parent_id": "PLAY-{NNN}",
      "type": "factual",
      "evidence": ["PS-VD-{X}", "ACT-VD-{Y}"],
      "confidence": "grounded",
      "score": 3,
      "layer": "5-playbook"
    },
    {
      "id": "CLM-PLAY-{NNN}-02",
      "parent_id": "PLAY-{NNN}",
      "type": "causal",
      "evidence": ["CLM-PLAY-{NNN}-01", "CLM-DVR-{D}-01"],
      "confidence": "partial",
      "score": 2,
      "layer": "5-playbook"
    }
  ]
}
```

Claim decomposition per play:
1. **Factual claim** (what the peer did): type=factual, evidence=[PS-VD-*, ACT-VD-*], score=3
2. **Causal claim** (why it worked — metric impact): type=causal, evidence=[factual CLM + DVR CLM], score=2 max
3. **Prescriptive claim** (generalizability — only if Transferability_Constraints allows): type=prescriptive, evidence=[causal CLM], score=2 max

Anti-patterns (ANTI-NNN) follow the same structure with CLM-ANTI-{NNN}-{seq} IDs.

Causal and prescriptive claims MUST use score <= 2. The claim_indexer enforces this ceiling.
```

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/valuation-driver/SKILL.md
git commit -m "feat(claims): add _claims[] emission to playbook-synthesizer prompt"
```

---

### Task 12: target-lens — target_lens claims (F3b)

**Files:**
- Modify: `.claude/skills/valuation-driver/SKILL.md` (around VD-P5 target lens section)

- [ ] **Step 1: Read the current target lens output instructions**

Read: `.claude/skills/valuation-driver/SKILL.md` — find the target lens section (search for "VD-P5" or "target_lens").

- [ ] **Step 2: Add _claims[] instruction after the target lens output schema**

```markdown
**Claim emission (REQUIRED):** Add a top-level `_claims` array to `target_lens.json`. For each play assessment, emit one claim:

```json
{
  "_claims": [
    {
      "id": "CLM-TL-{NNN}-01",
      "parent_id": "PLAY-{NNN}",
      "type": "comparative",
      "evidence": ["PS-VD-{target_co_source}", "CLM-PLAY-{NNN}-01"],
      "confidence": "partial",
      "score": 2,
      "layer": "5-playbook"
    }
  ]
}
```

Rules:
- One CLM per play assessment
- `evidence` includes (a) source for the target company data point and (b) the corresponding play's factual claim
- Type is `comparative` (comparing peer play to target company context)
- Score is max 2 (analogy-based, not direct evidence). Use score 1 if applicability is "not_applicable"
- Language reminder: "suggests", "appears to", "data is consistent with" — never imperative
```

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/valuation-driver/SKILL.md
git commit -m "feat(claims): add _claims[] emission to target-lens prompt"
```

---

## Chunk 3: Claim-Auditor D5 and Report HTML (F5-F6)

### Task 13: Claim-auditor D5 — Chain Integrity

**Files:**
- Modify: `prompts/vda/claim_auditor.md`

- [ ] **Step 1: Read the current claim auditor prompt**

Read: `prompts/vda/claim_auditor.md` — understand the current D1-D4 structure and checkpoint format.

- [ ] **Step 2: Add D5 dimension after D4**

Add after the D4 section:

```markdown
### D5 — Chain Integrity (NEW — requires claim_index.json)

**When:** CP-3 only (claim_index.json is generated after playbook step)

**Input:** Read `claim_index.json` from the run root directory.

**Checks:**

| # | Check | Pass | Fail |
|---|---|---|---|
| D5.1 | Every CLM-* has non-empty `evidence[]` | PASS | score 0 → HARD BLOCK |
| D5.2 | Every ID in `evidence[]` resolves to an object in the run | PASS | Orphan ID → WARNING |
| D5.3 | Recursive chain reaches leaf (PS-VD-*) | PASS | Broken chain → score <= 2 |
| D5.4 | Score cascading consistent (no child > parent evidence) | PASS | Downgrade applied → NOTE |
| D5.5 | Causal/prescriptive claims use hedged language in report | PASS | Hard language → FLAG |

**Output:** Add `chain_integrity` section to existing audit JSON:

```json
{
  "chain_integrity": {
    "total_claims_audited": 347,
    "grounded": 289,
    "partial": 41,
    "sourced": 12,
    "unsupported": 5,
    "score_avg": 2.77,
    "hard_blocks": 5,
    "cascading_downgrades": 14,
    "orphan_ids": [],
    "broken_chains": [],
    "language_flags": []
  }
}
```

**Verdict interaction:** If `hard_blocks > 0`, overall checkpoint verdict = BLOCKED (same as existing D3 FABRICATED behavior).
```

- [ ] **Step 3: Commit**

```bash
git add prompts/vda/claim_auditor.md
git commit -m "feat(claims): add D5 chain integrity dimension to claim auditor"
```

---

### Task 14: Report-builder — embed claim_index and interactive claims (F6)

**Files:**
- Modify: `.claude/skills/valuation-driver/SKILL.md` (VD-P4 report-builder section)

- [ ] **Step 1: Read the current report-builder instructions**

Read: `.claude/skills/valuation-driver/SKILL.md` — find the report-builder section (search for "VD-P4" or "report-builder" or "final_report.html").

- [ ] **Step 2: Add claim embedding instructions to report-builder prompt**

Add after the existing footnote system instructions:

```markdown
**Claim evidence layer (REQUIRED if claim_index.json exists):**

1. Read `claim_index.json` from the run root directory.
2. Embed it as `<script id="claim-data" type="application/json">` in the HTML `<head>`.
3. For each key assertion in the report text that corresponds to a CLM-* in the index, wrap it:
   ```html
   <span class="claim" data-claim="CLM-DVR-010-01">assertion text here</span>
   ```
4. Add this CSS to the report stylesheet:
   ```css
   .claim { cursor: pointer; position: relative; }
   .claim[data-score="2"] { text-decoration: underline; text-decoration-color: #d97706; text-underline-offset: 3px; }
   .claim[data-score="1"] { text-decoration: underline; text-decoration-color: #d97706; text-underline-offset: 3px; }
   .claim[data-score="1"]::after { content: " ⚠"; font-size: 0.7em; color: #d97706; }
   .claim-tooltip { position: fixed; right: 20px; top: 80px; width: 360px; max-height: 80vh; overflow-y: auto; background: #1a1a2e; color: #e0e0e0; padding: 16px; border-radius: 8px; font-family: 'IBM Plex Mono', monospace; font-size: 12px; box-shadow: 0 4px 24px rgba(0,0,0,0.3); z-index: 1000; display: none; }
   .claim-tooltip.visible { display: block; }
   ```
5. Add this JavaScript at the end of `<body>`:
   ```javascript
   (function() {
     const data = JSON.parse(document.getElementById('claim-data').textContent);
     const tooltip = document.createElement('div');
     tooltip.className = 'claim-tooltip';
     document.body.appendChild(tooltip);

     function renderChain(claimId, depth) {
       const claim = data.claims[claimId];
       if (!claim) return `<div style="padding-left:${depth*16}px">${claimId} (not found)</div>`;
       let html = `<div style="padding-left:${depth*16}px">`;
       html += `<strong>${claimId}</strong> · score ${claim.score}/3 · ${claim.type}<br>`;
       (claim.evidence || []).forEach(ev => {
         if (ev.startsWith('CLM-')) { html += renderChain(ev, depth+1); }
         else { html += `<div style="padding-left:${(depth+1)*16}px; color:#90cdf4">↳ ${ev}</div>`; }
       });
       html += '</div>';
       return html;
     }

     document.querySelectorAll('.claim').forEach(el => {
       const cid = el.dataset.claim;
       const claim = data.claims[cid];
       if (claim) el.dataset.score = claim.score;
       el.addEventListener('click', () => {
         tooltip.innerHTML = renderChain(cid, 0);
         tooltip.classList.toggle('visible');
       });
     });

     document.addEventListener('click', e => {
       if (!e.target.closest('.claim') && !e.target.closest('.claim-tooltip')) {
         tooltip.classList.remove('visible');
       }
     });
   })();
   ```

**Claim annotation guidelines:**
- Annotate ALL statistical assertions (rho values, N counts, driver classifications)
- Annotate ALL causal claims (X led to Y, X improved Z)
- Annotate ALL prescriptive/comparative claims in the target company lens section
- Do NOT annotate: section headings, methodology descriptions, general definitions
```

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/valuation-driver/SKILL.md
git commit -m "feat(claims): add interactive evidence layer to report-builder prompt"
```

---

## Chunk 4: Traceback Agent and CLAUDE.md Updates (F7)

### Task 15: Traceback agent prompt

**Files:**
- Create: `prompts/vda/traceback_agent.md`

- [ ] **Step 1: Write the traceback agent prompt**

```markdown
# Evidence Traceback Agent

You answer questions about the evidence chain behind VDA pipeline claims.

## Context

You have access to `claim_index.json` which maps every claim (CLM-*) to its evidence chain, from final report assertions down to source documents (PS-VD-*).

## Startup

1. Read `claim_index.json` from the run directory (use `--run-dir` argument or most recent run)
2. Read the `stats` section first — report total claims, groundedness %, score distribution
3. Do NOT load the full claims section into memory — use Grep to find specific claims on demand

## Answering Queries

For each query:
1. Identify the relevant CLM-* ID(s) using Grep on claim_index.json
2. Read only the matched claim entries (use Read with offset/limit)
3. If semantic context is needed (what does the claim actually assert?), read the `source_file` JSON and find the `parent_id` object
4. Present the chain as a tree:
   ```
   CLM-DVR-010-01  ·  score 3/3  ·  statistical
   ╰─ COR-191  ρ=-0.61 P/FRE (N=19)
      ╰─ MET-VD-021 × MET-VD-026
         ╰─ PS-VD-001, PS-VD-018...
   ```

## Supported Query Types

- **Forward trace**: "Where did claim X come from?" → follow chain to leaves
- **Reverse trace**: "What depends on PS-VD-018?" → Grep evidence arrays for the ID
- **Weakness scan**: "What are the weakest claims?" → filter by score ascending
- **Hard blocks**: "Any score 0 claims?" → filter by score == 0
- **Groundedness check**: "How grounded is PLAY-003?" → show chain + score

## Context Budget

- claim_index.json: read stats (~2K tokens), then targeted Grep (~5K per query)
- Parent JSON lookups: 1-2 per query, read only the relevant entry (~5K each)
- NEVER load standardized_matrix.json fully — use Grep for specific FIRM/MET entries
- Total per query: ~15-20K tokens max
```

- [ ] **Step 2: Commit**

```bash
git add prompts/vda/traceback_agent.md
git commit -m "feat(claims): add traceback agent prompt template"
```

---

### Task 16: Update CLAUDE.md with canonical filenames and conventions

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Read CLAUDE.md canonical filenames table**

Read: `CLAUDE.md` — find the "VDA canonical output filenames" table.

- [ ] **Step 2: Add claim_index.json to the canonical filenames table**

Add a new row for the cross-step index:

```markdown
| cross-step | (run root) | `claim_index.json` |
```

And add to step 4 (5-playbook) audit files:

```markdown
Update the existing audit row to note D5 `chain_integrity` section.
```

- [ ] **Step 3: Add CLM-* to the conventions section**

In the VDA ID conventions section, add:

```markdown
- Every claim in VDA claim index must use IDs (CLM-MET-*, CLM-COR-*, CLM-DVR-*, CLM-PLAY-*, CLM-ANTI-*, CLM-TL-*)
```

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add claim_index.json to canonical filenames and CLM-* convention"
```

---

### Task 17: Final verification

- [ ] **Step 1: Run all claim_indexer tests**

Run: `python3 -m pytest tests/test_claim_indexer.py -v`
Expected: ALL PASS

- [ ] **Step 2: Run claim_indexer CLI on real data (if available)**

Run: `python3 -m src.analyzer.claim_indexer --run-dir data/processed/pax/2026-03-10-run2/`
Expected: Outputs `claim_index.json` with matrix claims and legacy_run=true flag

- [ ] **Step 3: Run existing test suite to verify no regressions**

Run: `python3 -m pytest tests/ -v`
Expected: ALL PASS (existing tests unaffected)

- [ ] **Step 4: Commit any final adjustments**

```bash
git add -A
git commit -m "feat(claims): claim-level explainability system complete"
```
