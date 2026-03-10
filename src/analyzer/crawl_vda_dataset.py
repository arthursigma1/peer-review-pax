"""Build a VDA-friendly dataset from crawl outputs."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


SIGNAL_DEFINITIONS = (
    {
        "signal_id": "aum",
        "label": "AUM",
        "metric_ids": ["MET-VD-005"],
        "keywords": ("assets under management", "aum"),
        "core": True,
    },
    {
        "signal_id": "feaum",
        "label": "Fee-Earning AUM",
        "metric_ids": ["MET-VD-004", "MET-VD-006", "MET-VD-007", "MET-VD-008"],
        "keywords": (
            "feaum",
            "fee-earning aum",
            "fee earning aum",
            "fee-bearing capital",
            "fee bearing capital",
            "fee-paying aum",
            "fee paying aum",
            "fee-generating aum",
        ),
        "core": True,
    },
    {
        "signal_id": "fre",
        "label": "Fee-Related Earnings",
        "metric_ids": ["MET-VD-013", "MET-VD-014"],
        "keywords": (
            "fee-related earnings",
            "fee related earnings",
            "fre margin",
            "fre",
            "distributable earnings",
            "de per share",
            "management fee revenue",
        ),
        "core": True,
    },
    {
        "signal_id": "fundraising",
        "label": "Fundraising",
        "metric_ids": ["MET-VD-008", "MET-VD-009"],
        "keywords": (
            "fundraising",
            "capital raised",
            "capital raising",
            "new capital raised",
            "gross inflows",
            "inflows",
            "capital formation",
        ),
        "core": True,
    },
    {
        "signal_id": "margin",
        "label": "Margin / Efficiency",
        "metric_ids": ["MET-VD-013", "MET-VD-015", "MET-VD-021", "MET-VD-022"],
        "keywords": (
            "margin",
            "operating leverage",
            "efficiency",
            "cost discipline",
            "compensation ratio",
            "g&a",
        ),
        "core": True,
    },
    {
        "signal_id": "deployment",
        "label": "Deployment",
        "metric_ids": [],
        "keywords": (
            "deployment",
            "capital deployed",
            "invested capital",
            "deployed",
            "originations",
        ),
        "core": False,
    },
    {
        "signal_id": "realizations",
        "label": "Realizations",
        "metric_ids": [],
        "keywords": (
            "realizations",
            "realized",
            "harvest",
            "exits",
            "monetization",
            "realized carry",
        ),
        "core": False,
    },
    {
        "signal_id": "carry",
        "label": "Carry / Performance Fees",
        "metric_ids": ["MET-VD-017"],
        "keywords": (
            "carried interest",
            "carry",
            "performance fees",
            "incentive fees",
            "performance revenues",
            "net realizations",
        ),
        "core": False,
    },
    {
        "signal_id": "perpetual_capital",
        "label": "Perpetual Capital",
        "metric_ids": ["MET-VD-011"],
        "keywords": (
            "perpetual capital",
            "evergreen",
            "permanent capital",
            "insurance capital",
            "annuity",
        ),
        "core": False,
    },
    {
        "signal_id": "credit",
        "label": "Credit Mix",
        "metric_ids": ["MET-VD-012"],
        "keywords": (
            "credit",
            "direct lending",
            "private credit",
            "asset based",
            "asset-backed",
            "clo",
        ),
        "core": False,
    },
    {
        "signal_id": "insurance",
        "label": "Insurance",
        "metric_ids": [],
        "keywords": (
            "insurance",
            "retirement services",
            "annuity",
            "athene",
            "balance sheet capital",
        ),
        "core": False,
    },
    {
        "signal_id": "wealth",
        "label": "Wealth Channel",
        "metric_ids": [],
        "keywords": (
            "wealth",
            "private wealth",
            "global wealth",
            "individual investor",
            "retail",
            "advisor",
        ),
        "core": False,
    },
)

SIGNAL_LOOKUP = {definition["signal_id"]: definition for definition in SIGNAL_DEFINITIONS}
CORE_SIGNAL_IDS = [definition["signal_id"] for definition in SIGNAL_DEFINITIONS if definition["core"]]
DEFAULT_SOURCE_BUCKETS = {"core": 14, "supporting": 8}
NUMERIC_RE = re.compile(r"\$?\d[\d,.\-]*\s?(?:%|x|bn|billion|million|m|bps)?", re.IGNORECASE)
XBRL_NOISE_PATTERNS = (
    "namespace prefix",
    "xbrl.org/2003/role",
    "dei_",
    "document and entity information",
    "taxonomy",
)
MARKET_NOISE_PATTERNS = (
    "s&p 500",
    "nasdaq",
    "bitcoin",
    "dow jones",
    "market movers",
    "stock market news",
)


@dataclass(frozen=True)
class PeerRecord:
    firm_id: str
    firm_name: str
    ticker: str


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Transform crawl outputs into a VDA-ready signal dataset.")
    parser.add_argument(
        "--processed-root",
        default="data/processed/pax",
        help="Root directory containing processed PAX outputs.",
    )
    parser.add_argument(
        "--crawl-results",
        help="Explicit crawl_results.json path. Defaults to the latest run-level crawl output.",
    )
    parser.add_argument(
        "--peer-universe",
        help="Explicit peer_universe.json path. Defaults to the peer universe for the crawl run.",
    )
    parser.add_argument(
        "--output-dir",
        help="Output directory. Defaults to <run>/2-data/.",
    )
    return parser


def build_crawl_dataset(args: argparse.Namespace) -> dict[str, object]:
    crawl_results_path = Path(args.crawl_results) if args.crawl_results else find_latest_crawl_results_file(args.processed_root)
    if crawl_results_path is None or not crawl_results_path.exists():
        raise FileNotFoundError(f"No crawl_results.json found under {args.processed_root}")

    run_root = crawl_results_path.parents[2]
    peer_universe_path = Path(args.peer_universe) if args.peer_universe else run_root / "1-universe" / "peer_universe.json"
    output_dir = Path(args.output_dir) if args.output_dir else run_root / "2-data"
    output_dir.mkdir(parents=True, exist_ok=True)

    crawl_results = _load_json(crawl_results_path)
    peer_lookup = build_peer_lookup(peer_universe_path)

    source_records = build_source_records(crawl_results, peer_lookup)
    firm_summaries = build_firm_summaries(source_records)

    dataset = {
        "metadata": {
            "pipeline": "VDA",
            "stage": "VD-A2X",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "crawl_results_path": str(crawl_results_path),
            "peer_universe_path": str(peer_universe_path),
            "source_count": len(source_records),
            "firm_count": len(firm_summaries),
            "shortlisted_source_count": sum(1 for record in source_records if record["include_in_vda_shortlist"]),
            "signal_definitions": [
                {
                    "signal_id": definition["signal_id"],
                    "label": definition["label"],
                    "metric_ids": definition["metric_ids"],
                    "core": definition["core"],
                }
                for definition in SIGNAL_DEFINITIONS
            ],
            "thresholds": {
                "core_source_score": DEFAULT_SOURCE_BUCKETS["core"],
                "supporting_source_score": DEFAULT_SOURCE_BUCKETS["supporting"],
                "max_shortlist_per_firm": 6,
            },
        },
        "source_records": source_records,
        "firm_summaries": firm_summaries,
    }

    dataset_path = output_dir / "crawl_vda_dataset.json"
    source_csv_path = output_dir / "crawl_vda_sources.csv"
    firm_summary_path = output_dir / "crawl_vda_firm_summary.json"

    _write_json(dataset_path, dataset)
    _write_source_csv(source_csv_path, source_records)
    _write_json(firm_summary_path, {"firms": firm_summaries})
    return {
        "dataset_path": str(dataset_path),
        "source_csv_path": str(source_csv_path),
        "firm_summary_path": str(firm_summary_path),
        "source_count": len(source_records),
        "firm_count": len(firm_summaries),
    }


def find_latest_crawl_results_file(processed_root: str | Path) -> Path | None:
    candidates = sorted(Path(processed_root).glob("*/1-universe/crawl/crawl_results.json"))
    return candidates[-1] if candidates else None


def build_peer_lookup(path: str | Path) -> dict[str, PeerRecord]:
    payload = _load_json(path)
    lookup: dict[str, PeerRecord] = {}
    for item in payload.get("universe", []):
        record = PeerRecord(
            firm_id=str(item.get("firm_id", "")).strip(),
            firm_name=str(item.get("firm_name", "")).strip(),
            ticker=str(item.get("ticker", "")).strip(),
        )
        keys = {
            normalize_firm_name(record.firm_name),
            normalize_firm_name(record.ticker),
        }
        for key in keys:
            if key:
                lookup[key] = record
    return lookup


def build_source_records(crawl_results: list[object], peer_lookup: dict[str, PeerRecord]) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for item in crawl_results:
        if not isinstance(item, dict):
            continue

        peer = resolve_peer_record(item.get("firm", ""), peer_lookup)
        text = _read_text_payload(item.get("text_path", ""))
        signal_mentions = count_signal_mentions(text)
        signal_snippets = prune_noise_snippets(
            item=item,
            signal_snippets=rank_signal_snippets(item.get("relevant_snippets", [])),
        )
        noise_flags = detect_noise_flags(item=item, text=text, signal_mentions=signal_mentions)
        utility_score = score_source_record(
            item=item,
            signal_mentions=signal_mentions,
            signal_snippets=signal_snippets,
            noise_flags=noise_flags,
        )

        records.append(
            {
                "firm_id": peer.firm_id if peer else None,
                "firm_name": peer.firm_name if peer else item.get("firm"),
                "ticker": peer.ticker if peer else None,
                "source_id": item.get("source_id"),
                "title": item.get("title"),
                "document_type": item.get("document_type"),
                "bias_tag": item.get("bias_tag"),
                "seed_url": item.get("seed_url"),
                "loaded_url": item.get("loaded_url"),
                "text_path": item.get("text_path"),
                "text_length": item.get("text_length", 0),
                "extraction_modes": item.get("extraction_modes", []),
                "signal_mentions": signal_mentions,
                "matched_metric_ids": matched_metric_ids(signal_mentions),
                "ranked_snippets": signal_snippets[:5],
                "utility_score": utility_score,
                "noise_flags": noise_flags,
                "include_in_vda_shortlist": False,
                "shortlist_bucket": "discard",
                "shortlist_rank": None,
                "top_signal_ids": unique_signal_ids(signal_snippets),
            }
        )

    assign_shortlists(records)
    return sorted(records, key=lambda record: (record["firm_name"] or "", -record["utility_score"], -(record["text_length"] or 0)))


def resolve_peer_record(firm_name: str, peer_lookup: dict[str, PeerRecord]) -> PeerRecord | None:
    normalized = normalize_firm_name(firm_name)
    if normalized in peer_lookup:
        return peer_lookup[normalized]
    for key, record in peer_lookup.items():
        if key and (key in normalized or normalized in key):
            return record
    return None


def normalize_firm_name(value: str | None) -> str:
    if not value:
        return ""
    lowered = re.sub(r"[^a-z0-9]+", " ", value.lower())
    tokens = [token for token in lowered.split() if token not in {"inc", "corp", "corporation", "ltd", "limited", "co", "management", "global"}]
    return " ".join(tokens)


def count_signal_mentions(text: str) -> dict[str, int]:
    lowered = text.lower()
    counts: dict[str, int] = {}
    for definition in SIGNAL_DEFINITIONS:
        total = 0
        for keyword in definition["keywords"]:
            pattern = keyword if " " in keyword else rf"\b{re.escape(keyword)}\b"
            total += len(re.findall(pattern, lowered))
        counts[definition["signal_id"]] = total
    return counts


def rank_signal_snippets(snippets: list[object]) -> list[dict[str, object]]:
    ranked: list[dict[str, object]] = []
    for raw_snippet in snippets:
        if not isinstance(raw_snippet, str):
            continue
        snippet = " ".join(raw_snippet.split())
        signal_id, score, matched_metrics = score_snippet(snippet)
        ranked.append(
            {
                "signal_id": signal_id,
                "score": score,
                "matched_metric_ids": matched_metrics,
                "snippet": snippet,
            }
        )
    ranked.sort(key=lambda item: item["score"], reverse=True)
    return ranked


def score_snippet(snippet: str) -> tuple[str | None, int, list[str]]:
    lowered = snippet.lower()
    numeric_hits = len(NUMERIC_RE.findall(snippet))
    best_signal_id: str | None = None
    best_score = 0
    best_metrics: list[str] = []
    for definition in SIGNAL_DEFINITIONS:
        keyword_hits = 0
        for keyword in definition["keywords"]:
            pattern = keyword if " " in keyword else rf"\b{re.escape(keyword)}\b"
            keyword_hits += len(re.findall(pattern, lowered))
        if keyword_hits == 0:
            continue
        score = keyword_hits * 4 + min(numeric_hits, 4) * 2
        if definition["core"]:
            score += 2
        if score > best_score:
            best_signal_id = definition["signal_id"]
            best_score = score
            best_metrics = list(definition["metric_ids"])
    return best_signal_id, best_score, best_metrics


def prune_noise_snippets(
    *,
    item: dict[str, object],
    signal_snippets: list[dict[str, object]],
) -> list[dict[str, object]]:
    return [snippet for snippet in signal_snippets if not is_noise_snippet(item=item, snippet=snippet["snippet"])]


def is_noise_snippet(*, item: dict[str, object], snippet: str) -> bool:
    lowered_snippet = snippet.lower()
    loaded_url = str(item.get("loaded_url", "")).lower()
    title = str(item.get("title", "")).lower()
    path = urlparse(loaded_url).path.lower()
    is_sec_exhibit_page = "sec.gov" in loaded_url and "ex-" in path
    return (
        "/symbol/" in loaded_url
        or "stock price, quote, news & analysis" in title
        or "globenewswire.com/en/search" in loaded_url
        or ("edgar search results" in title)
        or (is_sec_exhibit_page and str(item.get("document_type", "")).lower() in {"annual_report", "10-k annual report", "10-q quarterly report"})
        or (title == "document" and "sec.gov" in loaded_url)
        or "author/sa-transcripts" in loaded_url
        or "stock price" in lowered_snippet
        or "quote, news & analysis" in lowered_snippet
        or "search results" in lowered_snippet
    )


def is_sec_filings_hub_page(*, item: dict[str, object]) -> bool:
    loaded_url = str(item.get("loaded_url", "")).lower()
    title = str(item.get("title", "")).lower()
    path = urlparse(loaded_url).path.lower()
    return (
        "sec filings" in title
        and (
            path.endswith("/sec-filings")
            or path.endswith("/sec-filings/default.aspx")
            or path.endswith("/sec-filings-annual-letters/sec-filings")
        )
    )


def detect_noise_flags(
    *,
    item: dict[str, object],
    text: str,
    signal_mentions: dict[str, int],
) -> dict[str, bool]:
    lowered = text.lower()
    loaded_url = str(item.get("loaded_url", "")).lower()
    path = urlparse(loaded_url).path.lower()
    top_snippet = " ".join(str(snippet) for snippet in item.get("relevant_snippets", [])[:2]).lower()
    text_length = int(item.get("text_length", 0) or 0)
    total_signal_mentions = sum(signal_mentions.values())
    return {
        "is_empty": text_length == 0,
        "is_short": text_length < 500,
        "is_xbrl_reference_noise": text_length < 25000 and any(pattern in lowered or pattern in top_snippet for pattern in XBRL_NOISE_PATTERNS),
        "is_market_noise": any(pattern in lowered or pattern in top_snippet for pattern in MARKET_NOISE_PATTERNS),
        "is_sec_index_page": "browse-edgar?action=getcompany" in loaded_url or loaded_url.endswith("-index.htm"),
        "is_symbol_hub": "/symbol/" in loaded_url,
        "is_sec_filings_hub": is_sec_filings_hub_page(item=item),
        "is_quote_page": "stock price, quote, news & analysis" in str(item.get("title", "")).lower() or "/symbol/" in loaded_url,
        "is_press_release_search_page": "globenewswire.com/en/search" in loaded_url,
        "is_sec_exhibit_page": ("sec.gov" in loaded_url and "ex-" in path) or str(item.get("title", "")).strip().lower() == "document",
        "is_low_signal": total_signal_mentions == 0,
    }


def score_source_record(
    *,
    item: dict[str, object],
    signal_mentions: dict[str, int],
    signal_snippets: list[dict[str, object]],
    noise_flags: dict[str, bool],
) -> int:
    total_signal_mentions = sum(min(count, 6) for count in signal_mentions.values())
    unique_signals = sum(1 for count in signal_mentions.values() if count > 0)
    top_snippet_score = sum(int(snippet["score"]) for snippet in signal_snippets[:3])
    text_length = int(item.get("text_length", 0) or 0)
    length_score = min(6, int(math.log10(text_length + 1) * 2)) if text_length > 0 else 0
    bias_bonus = {"regulatory-filing": 6, "third-party-analyst": 4, "company-produced": 3}.get(str(item.get("bias_tag", "")), 1)
    doc_bonus = {
        "annual_report": 6,
        "earnings_supplement": 5,
        "earnings_call_transcript": 5,
        "investor_presentation": 4,
        "investor_day": 4,
        "shareholder_letter": 4,
        "press_release": 2,
    }.get(str(item.get("document_type", "")), 1)
    score = total_signal_mentions + unique_signals * 3 + top_snippet_score + length_score + bias_bonus + doc_bonus
    if noise_flags["is_xbrl_reference_noise"]:
        score -= 12
    if noise_flags["is_market_noise"]:
        score -= 10
    if noise_flags["is_symbol_hub"]:
        score -= 8
    if noise_flags["is_quote_page"]:
        score -= 24
    if noise_flags["is_press_release_search_page"]:
        score -= 18
    if noise_flags["is_sec_exhibit_page"]:
        score -= 20
    if noise_flags["is_sec_index_page"]:
        score -= 3
    if noise_flags["is_empty"]:
        score -= 12
    if noise_flags["is_low_signal"]:
        score -= 8
    return max(score, 0)


def matched_metric_ids(signal_mentions: dict[str, int]) -> list[str]:
    metric_ids: list[str] = []
    for signal_id, count in signal_mentions.items():
        if count <= 0:
            continue
        metric_ids.extend(SIGNAL_LOOKUP[signal_id]["metric_ids"])
    deduped: list[str] = []
    seen: set[str] = set()
    for metric_id in metric_ids:
        if metric_id in seen:
            continue
        seen.add(metric_id)
        deduped.append(metric_id)
    return deduped


def unique_signal_ids(signal_snippets: list[dict[str, object]], limit: int = 3) -> list[str]:
    ordered_signal_ids: list[str] = []
    seen: set[str] = set()
    for snippet in signal_snippets:
        signal_id = snippet.get("signal_id")
        if not signal_id or signal_id in seen:
            continue
        seen.add(signal_id)
        ordered_signal_ids.append(signal_id)
        if len(ordered_signal_ids) >= limit:
            break
    return ordered_signal_ids


def assign_shortlists(records: list[dict[str, object]]) -> None:
    records_by_firm: dict[tuple[str | None, str | None], list[dict[str, object]]] = defaultdict(list)
    for record in records:
        key = (record["firm_id"], record["firm_name"])
        records_by_firm[key].append(record)

    for _key, firm_records in records_by_firm.items():
        sorted_records = sorted(
            firm_records,
            key=lambda record: (
                -record["utility_score"],
                -sum(record["signal_mentions"].values()),
                -(record["text_length"] or 0),
            ),
        )
        has_non_hub_candidate = any(
            is_shortlist_candidate(record, exclude_sec_filings_hubs=True)
            for record in sorted_records
        )
        shortlist_candidates = [
            record
            for record in sorted_records
            if is_shortlist_candidate(record, exclude_sec_filings_hubs=has_non_hub_candidate)
        ]
        shortlist = shortlist_candidates[:6]
        if not shortlist:
            shortlist = [
                record
                for record in sorted_records
                if is_shortlist_fallback_candidate(record, exclude_sec_filings_hubs=has_non_hub_candidate)
            ][:3]
        for rank, record in enumerate(shortlist, start=1):
            record["include_in_vda_shortlist"] = True
            record["shortlist_rank"] = rank
            record["shortlist_bucket"] = "core" if record["utility_score"] >= DEFAULT_SOURCE_BUCKETS["core"] else "supporting"


def is_shortlist_candidate(record: dict[str, object], *, exclude_sec_filings_hubs: bool) -> bool:
    noise_flags = record["noise_flags"]
    return (
        record["utility_score"] >= DEFAULT_SOURCE_BUCKETS["supporting"]
        and not noise_flags.get("is_empty", False)
        and not noise_flags.get("is_low_signal", False)
        and not noise_flags.get("is_quote_page", False)
        and not noise_flags.get("is_press_release_search_page", False)
        and not noise_flags.get("is_sec_exhibit_page", False)
        and not (exclude_sec_filings_hubs and noise_flags.get("is_sec_filings_hub", False))
    )


def is_shortlist_fallback_candidate(record: dict[str, object], *, exclude_sec_filings_hubs: bool) -> bool:
    noise_flags = record["noise_flags"]
    return (
        not noise_flags.get("is_empty", False)
        and sum(record["signal_mentions"].values()) > 0
        and not noise_flags.get("is_quote_page", False)
        and not noise_flags.get("is_press_release_search_page", False)
        and not noise_flags.get("is_sec_exhibit_page", False)
        and not (exclude_sec_filings_hubs and noise_flags.get("is_sec_filings_hub", False))
    )


def build_firm_summaries(source_records: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str | None, str | None, str | None], list[dict[str, object]]] = defaultdict(list)
    for record in source_records:
        key = (record["firm_id"], record["firm_name"], record["ticker"])
        grouped[key].append(record)

    summaries: list[dict[str, object]] = []
    for (firm_id, firm_name, ticker), records in grouped.items():
        aggregate_signal_mentions = dict(sum_counters(record["signal_mentions"] for record in records))
        top_sources = [
            {
                "source_id": record["source_id"],
                "title": record["title"],
                "loaded_url": record["loaded_url"],
                "document_type": record["document_type"],
                "bias_tag": record["bias_tag"],
                "utility_score": record["utility_score"],
                "shortlist_bucket": record["shortlist_bucket"],
            }
            for record in sorted(records, key=lambda record: (-record["utility_score"], -(record["text_length"] or 0)))[:5]
        ]
        evidence_by_signal = {}
        for signal_id in SIGNAL_LOOKUP:
            evidence = []
            for record in records:
                for snippet in record["ranked_snippets"]:
                    if snippet["signal_id"] != signal_id:
                        continue
                    evidence.append(
                        {
                            "score": snippet["score"],
                            "snippet": snippet["snippet"],
                            "source_id": record["source_id"],
                            "loaded_url": record["loaded_url"],
                            "document_type": record["document_type"],
                            "bias_tag": record["bias_tag"],
                            "utility_score": record["utility_score"],
                        }
                    )
            evidence.sort(key=lambda item: (item["score"], item["utility_score"]), reverse=True)
            evidence_by_signal[signal_id] = evidence[:3]

        summaries.append(
            {
                "firm_id": firm_id,
                "firm_name": firm_name,
                "ticker": ticker,
                "source_count": len(records),
                "shortlisted_source_count": sum(1 for record in records if record["include_in_vda_shortlist"]),
                "aggregate_signal_mentions": aggregate_signal_mentions,
                "coverage_gaps": [signal_id for signal_id in CORE_SIGNAL_IDS if aggregate_signal_mentions.get(signal_id, 0) == 0],
                "top_sources": top_sources,
                "evidence_by_signal": evidence_by_signal,
            }
        )
    return sorted(summaries, key=lambda summary: summary["firm_name"] or "")


def sum_counters(counters: list[dict[str, int]] | tuple[dict[str, int], ...] | object) -> Counter:
    total: Counter = Counter()
    for counter in counters:
        total.update(counter)
    return total


def _read_text_payload(path_str: str | None) -> str:
    if not path_str:
        return ""
    path = Path(path_str)
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="ignore")
    _, _, body = text.partition("\n\n")
    return body


def _load_json(path: str | Path) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _write_source_csv(path: Path, records: list[dict[str, object]]) -> None:
    fieldnames = [
        "firm_id",
        "ticker",
        "firm_name",
        "source_id",
        "title",
        "document_type",
        "bias_tag",
        "loaded_url",
        "text_length",
        "utility_score",
        "shortlist_bucket",
        "include_in_vda_shortlist",
        "top_signal_ids",
        "matched_metric_ids",
        "aum_mentions",
        "feaum_mentions",
        "fre_mentions",
        "fundraising_mentions",
        "margin_mentions",
        "carry_mentions",
        "credit_mentions",
        "insurance_mentions",
        "wealth_mentions",
        "perpetual_capital_mentions",
        "top_snippet",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "firm_id": record["firm_id"],
                    "ticker": record["ticker"],
                    "firm_name": record["firm_name"],
                    "source_id": record["source_id"],
                    "title": record["title"],
                    "document_type": record["document_type"],
                    "bias_tag": record["bias_tag"],
                    "loaded_url": record["loaded_url"],
                    "text_length": record["text_length"],
                    "utility_score": record["utility_score"],
                    "shortlist_bucket": record["shortlist_bucket"],
                    "include_in_vda_shortlist": record["include_in_vda_shortlist"],
                    "top_signal_ids": ",".join(record["top_signal_ids"]),
                    "matched_metric_ids": ",".join(record["matched_metric_ids"]),
                    "aum_mentions": record["signal_mentions"]["aum"],
                    "feaum_mentions": record["signal_mentions"]["feaum"],
                    "fre_mentions": record["signal_mentions"]["fre"],
                    "fundraising_mentions": record["signal_mentions"]["fundraising"],
                    "margin_mentions": record["signal_mentions"]["margin"],
                    "carry_mentions": record["signal_mentions"]["carry"],
                    "credit_mentions": record["signal_mentions"]["credit"],
                    "insurance_mentions": record["signal_mentions"]["insurance"],
                    "wealth_mentions": record["signal_mentions"]["wealth"],
                    "perpetual_capital_mentions": record["signal_mentions"]["perpetual_capital"],
                    "top_snippet": record["ranked_snippets"][0]["snippet"] if record["ranked_snippets"] else "",
                }
            )


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    summary = build_crawl_dataset(args)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
