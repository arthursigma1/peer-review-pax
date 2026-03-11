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
