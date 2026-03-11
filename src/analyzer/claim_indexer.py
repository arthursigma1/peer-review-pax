"""Claim indexer: collect, validate, resolve, and score claims across VDA pipeline outputs."""

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
    for field in _REQUIRED_FIELDS:
        if field not in claim:
            errors.append(f"Missing required field: {field}")
    if errors:
        return errors

    if not CLM_ID_PATTERN.match(claim["id"]):
        errors.append(f"Invalid id format: {claim['id']} — must match CLM-{{PREFIX}}-{{ID}}-{{SEQ}}")

    if claim["type"] not in VALID_CLAIM_TYPES:
        errors.append(f"Invalid type: {claim['type']} — must be one of {sorted(VALID_CLAIM_TYPES)}")

    if claim["type"] in CLAIM_TYPE_CEILINGS:
        ceiling = CLAIM_TYPE_CEILINGS[claim["type"]]
        if claim["score"] > ceiling:
            errors.append(f"Score {claim['score']} exceeds ceiling {ceiling} for type '{claim['type']}'")

    if claim["confidence"] not in VALID_CONFIDENCE_LABELS:
        errors.append(f"Invalid confidence: {claim['confidence']}")

    if claim["confidence"] in _CONFIDENCE_TO_SCORE:
        expected_score = _CONFIDENCE_TO_SCORE[claim["confidence"]]
        if claim["score"] != expected_score:
            errors.append(f"Confidence '{claim['confidence']}' implies score {expected_score}, got score {claim['score']}")

    if not claim["evidence"] and claim["score"] > 0:
        errors.append("Empty evidence[] on claim with score > 0")

    return errors


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

    json_files: list[Path] = []
    for rel in _CLAIM_BEARING_FILES:
        p = run_dir / rel
        if p.exists():
            json_files.append(p)
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
