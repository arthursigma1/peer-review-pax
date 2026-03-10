"""Build a cleaned consulting-context dataset from consulting crawl outputs."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

from src.analyzer._shared import utcnow_iso
from src.validation.vda_contracts import (
    VALID_ALLOWED_USAGE,
    VALID_CLAIM_SCOPES,
    VALID_DISALLOWED_USAGE,
)


THEME_KEYWORDS = {
    "wealth_distribution": (
        "wealth",
        "advisor",
        "retail",
        "high net worth",
        "private market opportunity",
        "distribution",
    ),
    "fundraising_lp_demand": (
        "fundraising",
        "fund-raising",
        "capital raised",
        "allocator",
        "allocation",
        "lp",
        "dry powder",
    ),
    "private_credit": (
        "private credit",
        "credit",
        "direct lending",
        "asset-backed",
        "asset based",
    ),
    "margin_operating_model": (
        "margin",
        "operating model",
        "efficiency",
        "cost",
        "operating leverage",
        "fee compression",
    ),
    "mna_consolidation": (
        "m&a",
        "mergers",
        "acquisitions",
        "consolidation",
        "inorganic",
        "strategic partnerships",
    ),
    "democratization": (
        "democratization",
        "semi-liquid",
        "evergreen",
        "individual investor",
        "product innovation",
        "eltif",
    ),
}
NUMERIC_SIGNAL_RE = re.compile(r"\$?\d[\d,.\-]*\s?(?:%|x|bn|billion|million|m|bps|tn)?", re.IGNORECASE)
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
LOW_VALUE_TITLE_HINTS = ("linkedin", "home |", "corporate", "podcast", "webcasts", "webinars")
CONTACT_HINTS = ("@", "mobile", "phone", "communications", "contact us", "subscribe")
DEFAULT_ALLOWED_USAGE = sorted(VALID_ALLOWED_USAGE)
DEFAULT_DISALLOWED_USAGE = sorted(VALID_DISALLOWED_USAGE)
EXCLUDED_STATUSES = {"deduped_in_base", "failed", "zero_text", "missing_seed_result"}


# Heuristics for claim scope detection
_FIRM_POSSESSIVE_RE = re.compile(r"[A-Z][a-zA-Z&]+(?:\u2019s|'s)\s+\$[\d,.]")
_THE_FIRM_RE = re.compile(
    r"\bthe (?:firm|company)\b.*?\b(?:managed|oversaw|reported|generated|raised|earned|had)\b",
    re.IGNORECASE,
)
_MARKET_SCOPE_RE = re.compile(
    r"\b(?:global(?:ly)?|industry[-\s]wide|market\b|sector\b|overall\b|worldwide)\b",
    re.IGNORECASE,
)

def classify_claim_scope(claim: str) -> str:
    """Classify whether a claim is market-level, multi-firm, or firm-specific.

    Priority: single_firm (the-firm pattern) > multi_firm > single_firm (possessive) > market > segment.
    """
    if _THE_FIRM_RE.search(claim):
        return "single_firm"
    possessives = _FIRM_POSSESSIVE_RE.findall(claim)
    if len(possessives) >= 2:
        return "multi_firm"
    has_market = bool(_MARKET_SCOPE_RE.search(claim))
    if possessives and not has_market:
        return "single_firm"
    if has_market:
        return "market"
    return "segment"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build consulting_context.json from consulting crawl outputs.")
    parser.add_argument(
        "--processed-root",
        default="data/processed/pax",
        help="Root directory containing processed PAX outputs.",
    )
    parser.add_argument(
        "--seed-results",
        help="Explicit consulting_seed_results.json path. Defaults to the latest consulting crawl output.",
    )
    parser.add_argument(
        "--audit",
        help="Explicit consulting_seed_audit.json path. Defaults to the audit alongside the seed results.",
    )
    parser.add_argument(
        "--output-dir",
        help="Output directory. Defaults to <run>/2-data/.",
    )
    return parser


def find_latest_consulting_seed_results_file(processed_root: str | Path) -> Path | None:
    candidates = sorted(Path(processed_root).glob("*/1-universe/crawl-with-consulting/consulting_seed_results.json"))
    return candidates[-1] if candidates else None


def detect_context_themes(text: str) -> list[str]:
    lowered = text.lower()
    matches = [
        theme
        for theme, keywords in THEME_KEYWORDS.items()
        if any(keyword in lowered for keyword in keywords)
    ]
    return matches or ["other"]


def extract_claims(*, title: str, snippets: list[str], max_claims: int = 5) -> list[str]:
    candidates: list[tuple[int, str]] = []
    seen: set[str] = set()

    for snippet in snippets:
        for sentence in SENTENCE_SPLIT_RE.split(_clean_text(snippet)):
            sentence = sentence.strip(" -")
            if len(sentence) < 40:
                continue
            normalized = sentence.lower()
            if normalized in seen:
                continue
            if any(hint in normalized for hint in CONTACT_HINTS):
                continue

            numeric_bonus = 2 if NUMERIC_SIGNAL_RE.search(sentence) else 0
            theme_bonus = sum(
                1
                for keywords in THEME_KEYWORDS.values()
                if any(keyword in normalized for keyword in keywords)
            )
            length_bonus = 1 if 60 <= len(sentence) <= 280 else 0
            score = numeric_bonus + theme_bonus + length_bonus
            if score <= 0:
                continue

            seen.add(normalized)
            candidates.append((score, sentence))

    if title and not any(title.lower().startswith(prefix) for prefix in LOW_VALUE_TITLE_HINTS):
        title_text = _clean_text(title)
        if any(keyword in title_text.lower() for keywords in THEME_KEYWORDS.values() for keyword in keywords):
            candidates.append((1, title_text))

    candidates.sort(key=lambda item: (-item[0], -len(item[1]), item[1]))
    return [claim for _, claim in candidates[:max_claims]]


def classify_utility(*, text_length: int, status: str, title: str, claims: list[str], themes: list[str]) -> str:
    lowered_title = title.lower()
    if status != "ok":
        return "low"
    if any(hint in lowered_title for hint in LOW_VALUE_TITLE_HINTS):
        return "low"
    if text_length >= 10_000 and len(claims) >= 3:
        return "high"
    if text_length >= 5_000 and len(claims) >= 2 and themes != ["other"]:
        return "high"
    if text_length >= 2_500 and claims:
        return "medium"
    return "low"


def build_context_payload(seed_rows: list[dict[str, object]], audit_rows: list[dict[str, object]]) -> dict[str, object]:
    seed_by_id = {str(row.get("source_id", "")).strip(): row for row in seed_rows}
    sources: list[dict[str, object]] = []
    excluded: list[dict[str, object]] = []

    for audit_row in sorted(audit_rows, key=lambda row: str(row.get("source_id", ""))):
        source_id = str(audit_row.get("source_id", "")).strip()
        status = str(audit_row.get("status", "missing_seed_result")).strip() or "missing_seed_result"
        seed_row = seed_by_id.get(source_id, {})

        title = str(seed_row.get("title") or audit_row.get("title") or "").strip()
        snippets = [
            _clean_text(str(snippet))
            for snippet in (seed_row.get("relevant_snippets") or [])
            if str(snippet).strip()
        ]
        claims = extract_claims(title=title, snippets=snippets)
        themes = detect_context_themes(" ".join([title, *claims, *snippets[:5]]))
        text_length = int(seed_row.get("text_length") or 0)
        utility = classify_utility(
            text_length=text_length,
            status=status,
            title=title,
            claims=claims,
            themes=themes,
        )

        record = {
            "source_id": source_id,
            "firm": str(seed_row.get("firm") or "").strip(),
            "title": title,
            "document_type": str(seed_row.get("document_type") or "").strip(),
            "bias_tag": str(seed_row.get("bias_tag") or "").strip(),
            "seed_url": str(seed_row.get("seed_url") or audit_row.get("seed_url") or "").strip(),
            "loaded_url": str(seed_row.get("loaded_url") or "").strip(),
            "domain": urlparse(str(seed_row.get("loaded_url") or seed_row.get("seed_url") or "")).netloc.lower(),
            "text_length": text_length,
            "status": status,
            "utility_for_agents": utility,
            "allowed_usage": list(DEFAULT_ALLOWED_USAGE),
            "disallowed_usage": list(DEFAULT_DISALLOWED_USAGE),
            "context_themes": themes,
            "claims": [{"text": c, "scope": classify_claim_scope(c)} for c in claims],
            "top_snippets": snippets[:5],
            "off_domain_followup_count": int(audit_row.get("off_domain_followup_count") or 0),
        }

        if status in EXCLUDED_STATUSES or utility == "low":
            excluded.append(
                {
                    "source_id": source_id,
                    "title": title,
                    "status": status,
                    "utility_for_agents": utility,
                }
            )
            continue

        sources.append(record)

    metadata = {
        "pipeline": "VDA",
        "stage": "VD-A2C",
        "generated_at": utcnow_iso(),
        "consulting_catalog_count": len(audit_rows),
        "seed_result_count": len(seed_rows),
        "included_source_count": len(sources),
        "excluded_source_count": len(excluded),
        "included_status_counts": dict(Counter(source["status"] for source in sources)),
        "theme_counts": dict(Counter(theme for source in sources for theme in source["context_themes"])),
        "excluded_sources": excluded,
    }
    return {"metadata": metadata, "sources": sources}


def build_consulting_context(args: argparse.Namespace) -> dict[str, object]:
    seed_results_path = Path(args.seed_results) if args.seed_results else find_latest_consulting_seed_results_file(args.processed_root)
    if seed_results_path is None or not seed_results_path.exists():
        raise FileNotFoundError(f"No consulting_seed_results.json found under {args.processed_root}")

    audit_path = Path(args.audit) if args.audit else seed_results_path.with_name("consulting_seed_audit.json")
    if not audit_path.exists():
        raise FileNotFoundError(f"consulting_seed_audit.json was not found next to {seed_results_path}")

    run_root = seed_results_path.parents[2]
    output_dir = Path(args.output_dir) if args.output_dir else run_root / "2-data"
    output_dir.mkdir(parents=True, exist_ok=True)

    seed_rows = _load_json(seed_results_path)
    audit_rows = _load_json(audit_path)
    payload = build_context_payload(seed_rows=seed_rows, audit_rows=audit_rows)
    payload["metadata"]["seed_results_path"] = str(seed_results_path)
    payload["metadata"]["audit_path"] = str(audit_path)

    _write_json(output_dir / "consulting_context.json", payload)
    return payload


def _load_json(path: Path) -> list[dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"Expected a list in {path}")
    return payload


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    payload = build_consulting_context(args)
    print(
        json.dumps(
            {
                "included_source_count": payload["metadata"]["included_source_count"],
                "excluded_source_count": payload["metadata"]["excluded_source_count"],
                "theme_counts": payload["metadata"]["theme_counts"],
            },
            indent=2,
            ensure_ascii=True,
        )
    )


if __name__ == "__main__":
    main()
