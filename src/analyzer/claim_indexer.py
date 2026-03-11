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
    "5-playbook/playbook.json",
    "5-playbook/target_lens.json",
    "5-playbook/platform_playbook.json",
    "5-playbook/asset_class_playbooks.json",
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


# Maps production data_points confidence labels to VDA confidence labels
_DATA_POINTS_CONFIDENCE = {"high": "grounded", "medium": "partial", "low": "sourced"}


def _make_matrix_claim(met_id: str, firm_id: str, score: int, confidence: str, evidence: list[str]) -> dict:
    """Build a single matrix claim dict."""
    met_short = met_id.replace("MET-VD-", "MET-")
    return {
        "id": f"CLM-{met_short}-{firm_id}-01",
        "parent_id": met_id,
        "type": "factual",
        "evidence": evidence,
        "confidence": confidence,
        "score": score,
        "layer": "2-data",
    }


def generate_matrix_claims(matrix: dict) -> tuple[list[dict], list[str]]:
    """Auto-generate factual claims from standardized_matrix.json.

    Supports two formats:
    - Nested format: {"metrics": {"MET-VD-021": {"firms": {"FIRM-001": {"value": ..., "source": "..."}}}}}
    - Flat format: {"data_points": [{"firm_id": "FIRM-001", "metric_id": "MET-VD-001", "value_raw": ..., "confidence": "high"}]}

    For nested format, extracts PS-VD-* IDs from source strings.
    For flat format, maps confidence (high→grounded, medium→partial, low→sourced).
    """
    if not isinstance(matrix, dict):
        return [], ["standardized_matrix.json root is not a dict"]

    if "data_points" in matrix:
        return _generate_claims_from_data_points(matrix["data_points"])

    return _generate_claims_from_metrics(matrix.get("metrics", {}))


def _generate_claims_from_data_points(data_points: list) -> tuple[list[dict], list[str]]:
    """Generate claims from flat data_points list format."""
    claims: list[dict] = []
    warnings: list[str] = []

    for dp in data_points:
        if not isinstance(dp, dict):
            continue
        if dp.get("missing", False):
            continue

        firm_id = dp.get("firm_id", "")
        met_id = dp.get("metric_id", "")
        if not firm_id or not met_id:
            continue

        confidence = _DATA_POINTS_CONFIDENCE.get(dp.get("confidence", "low"), "sourced")
        score = _CONFIDENCE_TO_SCORE[confidence]
        claims.append(_make_matrix_claim(met_id, firm_id, score, confidence, []))

    return claims, warnings


def _generate_claims_from_metrics(metrics: dict) -> tuple[list[dict], list[str]]:
    """Generate claims from nested metrics dict format."""
    claims: list[dict] = []
    warnings: list[str] = []

    for met_id, met_data in metrics.items():
        if not isinstance(met_data, dict):
            continue
        firms = met_data.get("firms", {})
        for firm_id, cell in firms.items():
            if not isinstance(cell, dict):
                continue
            if cell.get("value") is None:
                continue

            source_str = cell.get("source", "")
            ps_vd_ids = _PS_VD_PATTERN.findall(source_str) if source_str else []

            if ps_vd_ids:
                score, confidence, evidence = 3, "grounded", sorted(set(ps_vd_ids))
            elif source_str:
                score, confidence, evidence = 1, "sourced", []
                warnings.append(f"Matrix cell {met_id}/{firm_id}: source text present but no PS-VD-* ID parseable")
            else:
                score, confidence, evidence = 1, "sourced", []
                warnings.append(f"Matrix cell {met_id}/{firm_id}: no source field")

            claims.append(_make_matrix_claim(met_id, firm_id, score, confidence, evidence))

    return claims, warnings


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


def _evidence_score(ev_id: str, claims: dict[str, dict], parent_index: dict[str, list[str]]) -> int:
    """Return the score of an evidence item. CLM-* returns claim score, others use defaults."""
    if ev_id.startswith("CLM-") and ev_id in claims:
        return claims[ev_id]["score"]
    for prefix, default in NON_CLM_DEFAULT_SCORES.items():
        if ev_id.startswith(prefix):
            return default
    # Non-CLM without prefix match → check covering CLM via parent_index (O(1) lookup)
    covering_ids = parent_index.get(ev_id, [])
    if covering_ids:
        return min(claims[cid]["score"] for cid in covering_ids if cid in claims)
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
    downgraded_ids: set[str] = set()

    # Build parent_id → [claim_ids] index once for O(1) evidence lookups
    parent_index: dict[str, list[str]] = {}
    for cid, c in result.items():
        pid = c.get("parent_id")
        if pid:
            parent_index.setdefault(pid, []).append(cid)

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

            ev_scores = [_evidence_score(ev_id, result, parent_index) for ev_id in evidence]
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
                    downgraded_ids.add(cid)

    return result, len(downgraded_ids)


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
    has_agent_claims = any(c.get("layer") != "2-data" for c in claims.values())
    legacy_run = not has_agent_claims and len(matrix_claims_list) > 0

    # 3. Resolve chains
    claims = resolve_chains(claims)

    # 4. Score cascading
    claims, downgrade_count = apply_score_cascading(claims)

    # 5. Compute stats
    by_score: dict[int, int] = {0: 0, 1: 0, 2: 0, 3: 0}
    by_type: dict[str, int] = {}
    for c in claims.values():
        by_score[c["score"]] += 1
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
