"""Crawl VDA source catalogs and extract analysis-ready signals."""

from __future__ import annotations

import argparse
import asyncio
import base64
import hashlib
import hmac
import json
import os
import re
import shutil
import time
import warnings
from dataclasses import asdict
from datetime import timedelta
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urljoin, urlparse
from urllib.request import Request as UrlRequest, urlopen

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from crawlee import Request
from crawlee.crawlers import HttpCrawler

from src.analyzer._shared import utcnow_iso
from .source_catalog import SourceRecord, find_latest_catalog_file, load_catalog, load_sources

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover - optional at runtime
    PdfReader = None

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

VDA_KEYWORDS = (
    "aum",
    "assets under management",
    "feaum",
    "fpaum",
    "fee earning",
    "fee-bearing",
    "fee bearing",
    "fre",
    "fee-related earnings",
    "distributable earnings",
    "management fees",
    "fundraising",
    "capital raised",
    "deployment",
    "realizations",
    "carry",
    "credit",
    "insurance",
    "wealth",
    "perpetual capital",
    "gpms",
    "margin",
    "dividend",
    "revenue",
)
FOLLOW_LINK_HINTS = (
    "10-k",
    "20-f",
    "annual",
    "results",
    "earnings",
    "presentation",
    "supplement",
    "transcript",
    "investor",
    "shareholder",
    "credit",
    "fund",
)
TEXT_EXTENSIONS = {".htm", ".html", ".xhtml", ".xml", ".txt"}
PDF_EXTENSIONS = {".pdf"}
CONTENT_ROOT_SELECTORS = (
    "main",
    "article",
    "[role='main']",
    "#main",
    "#content",
    "#main-content",
    ".main",
    ".main-content",
    ".content",
    ".content-body",
    ".article",
    ".article-body",
    ".article-content",
    ".entry-content",
    ".post-content",
    ".story-body",
    ".transcript",
    ".news-release",
    ".press-release",
    ".filing",
)
NOISE_HINTS = (
    "nav",
    "menu",
    "header",
    "footer",
    "breadcrumb",
    "cookie",
    "popup",
    "modal",
    "share",
    "social",
    "sidebar",
    "masthead",
    "newsletter",
    "subscribe",
    "advert",
    "ad-",
    "search",
    "toolbar",
    "dropdown",
)
NOISE_CONTAINER_TAGS = {"div", "section", "ul", "ol", "aside", "header", "footer", "nav"}
GENERIC_LINK_TEXT = {
    "home",
    "learn more",
    "read more",
    "view all",
    "overview",
    "menu",
}
BOILERPLATE_PHRASES = (
    "menu column",
    "the firm menu",
    "our clients institutional investors",
    "financial advisors family offices",
    "stock information overview dividends analyst coverage faq",
    "private wealth at",
    "view all press releases",
    "market movers tech stock news",
    "best credit cards compare credit cards",
)
NUMERIC_SIGNAL_RE = re.compile(r"(\$?\d[\d,.\-]*\s?(?:%|x|bn|billion|million|m|bps)?)", re.IGNORECASE)
EMBEDDED_DOCUMENT_QUERY_KEYS = ("src", "file", "pdf", "document", "download")
SEC_FORM_PRIORITY = {
    "10-k": 18,
    "20-f": 18,
    "annual report": 16,
    "10-q": 14,
    "quarterly report": 12,
    "8-k": 10,
    "6-k": 10,
    "def 14a": 8,
    "earnings": 6,
    "presentation": 4,
    "supplement": 4,
    "4": -8,
    "3": -8,
    "5": -8,
}
FIRM_TOKEN_STOPWORDS = {
    "and",
    "asset",
    "assets",
    "capital",
    "co",
    "company",
    "corp",
    "corporation",
    "global",
    "group",
    "holding",
    "holdings",
    "inc",
    "incorporated",
    "limited",
    "ltd",
    "management",
    "partners",
    "plc",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Crawlee over PAX VDA source catalogs.")
    parser.add_argument(
        "--processed-root",
        default="data/processed/pax",
        help="Root directory containing processed PAX outputs.",
    )
    parser.add_argument(
        "--catalog",
        help="Explicit source catalog file to crawl. Defaults to the latest run-level source_catalog.json.",
    )
    parser.add_argument(
        "--output-dir",
        help="Directory to write crawl artifacts. Defaults to <run>/1-universe/crawl/.",
    )
    parser.add_argument(
        "--raw-dir",
        help="Directory to write extracted raw text files. Defaults to data/raw/pax/crawled/<run-name>/.",
    )
    parser.add_argument("--max-seeds", type=int, help="Limit the number of seed source URLs.")
    parser.add_argument(
        "--max-links-per-page",
        type=int,
        default=2,
        help="Maximum number of relevant follow-up links to enqueue per HTML page.",
    )
    parser.add_argument(
        "--max-crawl-depth",
        type=int,
        default=1,
        help="Maximum follow-up depth. Seed URLs start at depth 0.",
    )
    parser.add_argument(
        "--max-requests",
        type=int,
        default=150,
        help="Hard cap on total requests for the crawl.",
    )
    parser.add_argument(
        "--respect-robots-txt",
        action="store_true",
        help="Respect robots.txt rules while crawling.",
    )
    return parser


async def crawl_sources(args: argparse.Namespace) -> dict[str, object]:
    processed_root = Path(args.processed_root)
    catalog_path = Path(args.catalog) if args.catalog else find_latest_catalog_file(processed_root)
    if catalog_path is None:
        raise FileNotFoundError(f"No source catalog found under {processed_root}")

    if args.catalog:
        sources = load_catalog(catalog_path)
    else:
        sources = load_sources(processed_root, latest_only=True)
    if args.max_seeds:
        sources = sources[: args.max_seeds]

    run_name = _derive_run_name(catalog_path)
    output_dir = Path(args.output_dir) if args.output_dir else catalog_path.parent / "crawl"
    raw_dir = Path(args.raw_dir) if args.raw_dir else Path("data/raw/pax/crawled") / run_name
    storage_dir = output_dir / "_crawlee_storage"
    if output_dir.exists():
        shutil.rmtree(output_dir)
    if raw_dir.exists():
        shutil.rmtree(raw_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    os.environ["CRAWLEE_STORAGE_DIR"] = str(storage_dir)

    results: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []
    visited_urls: set[str] = set()

    crawler = HttpCrawler(
        max_requests_per_crawl=args.max_requests,
        max_request_retries=2,
        max_crawl_depth=args.max_crawl_depth,
        request_handler_timeout=timedelta(seconds=75),
        respect_robots_txt_file=args.respect_robots_txt,
        retry_on_blocked=False,
    )

    @crawler.router.default_handler
    async def handle_request(context) -> None:
        body = context.parsed_content
        loaded_url = context.request.loaded_url or context.request.url
        if loaded_url in visited_urls:
            return
        visited_urls.add(loaded_url)

        user_data = dict(context.request.user_data)
        source = _source_from_user_data(user_data)
        content_type = str(context.http_response.headers.get("content-type", "")).lower()
        is_pdf = _is_pdf_url(loaded_url) or "application/pdf" in content_type

        if is_pdf:
            text, metadata = _extract_pdf_text(body)
            relevant_snippets = _collect_relevant_snippets(text.splitlines(), limit=10)
            raw_text_path = _write_text_artifact(raw_dir, source, loaded_url, text)
            item = {
                "source_id": source.source_id,
                "firm": source.firm,
                "seed_url": source.url,
                "loaded_url": loaded_url,
                "title": source.title,
                "document_type": source.document_type,
                "bias_tag": source.bias_tag,
                "depth": user_data.get("depth", 0),
                "content_type": content_type or "application/pdf",
                "text_path": str(raw_text_path),
                "text_length": len(text),
                "relevant_snippets": relevant_snippets,
                "pdf_metadata": metadata,
            }
            results.append(item)
            await context.push_data(item)
            return

        html = body.decode("utf-8", errors="ignore")
        soup = BeautifulSoup(html, features="xml" if "xml" in content_type else "lxml")
        page_title = soup.title.string.strip() if soup.title and soup.title.string else source.title
        extraction_modes: list[str] = []
        candidate_links: list[str] = []

        if _looks_like_xml_feed(content_type, loaded_url):
            blocks, feed_links = _extract_feed_blocks(soup=soup, base_url=loaded_url)
            candidate_links.extend(feed_links)
            extraction_modes.append("xml_feed")
        else:
            blocks = _extract_text_blocks(soup)

            harvested_blocks, harvested_links = _harvest_document_links(
                soup=soup,
                base_url=loaded_url,
                seed_source=source,
                limit=max(args.max_links_per_page * 4, 8),
            )
            if harvested_blocks:
                blocks.extend(harvested_blocks)
                candidate_links.extend(harvested_links)
                extraction_modes.append("document_links")

            embedded_links = _extract_embedded_document_links(loaded_url, soup)
            if embedded_links:
                candidate_links.extend(embedded_links)
                extraction_modes.append("embedded_document")

            if _should_fetch_structured_sec_hub(
                loaded_url=loaded_url,
                title=page_title,
                blocks=blocks,
            ):
                structured_blocks, structured_links, extraction_mode = await asyncio.to_thread(
                    _extract_structured_sec_hub_payload,
                    html,
                    loaded_url,
                    source,
                )
                if structured_blocks:
                    blocks.extend(structured_blocks)
                if structured_links:
                    candidate_links.extend(structured_links)
                if extraction_mode:
                    extraction_modes.append(extraction_mode)

        blocks = _dedupe_preserve_order(blocks)
        candidate_links = _dedupe_preserve_order(candidate_links)
        relevant_snippets = _collect_relevant_snippets(blocks, limit=10)
        text = "\n\n".join(blocks)
        raw_text_path = _write_text_artifact(raw_dir, source, loaded_url, text)

        item = {
            "source_id": source.source_id,
            "firm": source.firm,
            "seed_url": source.url,
            "loaded_url": loaded_url,
            "title": page_title,
            "document_type": source.document_type,
            "bias_tag": source.bias_tag,
            "depth": user_data.get("depth", 0),
            "content_type": content_type or "text/html",
            "text_path": str(raw_text_path),
            "text_length": len(text),
            "relevant_snippets": relevant_snippets,
            "extraction_modes": _dedupe_preserve_order(extraction_modes),
        }
        results.append(item)
        await context.push_data(item)

        depth = int(user_data.get("depth", 0))
        if depth >= args.max_crawl_depth:
            return

        candidates = candidate_links + _find_candidate_links(
            soup=soup,
            base_url=loaded_url,
            seed_source=source,
            limit=args.max_links_per_page,
        )
        candidates = _dedupe_preserve_order(candidates)[: args.max_links_per_page]
        if not candidates:
            return

        next_requests = [
            Request(
                url=url,
                uniqueKey=f"{source.source_id}:{depth + 1}:{url}",
                userData={**user_data, "depth": depth + 1, "source": asdict(source)},
            )
            for url in candidates
        ]
        await context.add_requests(next_requests)

    @crawler.failed_request_handler
    async def handle_failure(context, error: Exception) -> None:
        user_data = dict(context.request.user_data)
        source = _source_from_user_data(user_data)
        failure = {
            "source_id": source.source_id,
            "firm": source.firm,
            "url": context.request.url,
            "loaded_url": context.request.loaded_url,
            "depth": user_data.get("depth", 0),
            "error": str(error),
        }
        failures.append(failure)

    seed_requests = [
        Request(
            url=source.url,
            uniqueKey=f"{source.source_id}:{source.url}",
            userData={"depth": 0, "source": asdict(source)},
        )
        for source in sources
    ]
    stats = await crawler.run(seed_requests)

    summary = {
        "catalog_path": str(catalog_path),
        "run_name": run_name,
        "source_count": len(sources),
        "result_count": len(results),
        "failure_count": len(failures),
        "visited_url_count": len(visited_urls),
        "finished_at": utcnow_iso(),
        "stats": _stats_to_dict(stats),
    }

    _write_json(output_dir / "crawl_input_sources.json", [asdict(source) for source in sources])
    _write_json(output_dir / "crawl_results.json", results)
    _write_json(output_dir / "crawl_failures.json", failures)
    _write_json(output_dir / "crawl_summary.json", summary)

    return summary


def _source_from_user_data(user_data: dict[str, object]) -> SourceRecord:
    source = user_data.get("source", {})
    if not isinstance(source, dict):
        raise TypeError("Invalid source metadata in request user_data")
    return SourceRecord(**source)


def _derive_run_name(catalog_path: Path) -> str:
    if catalog_path.name == "source_catalog.json":
        return catalog_path.parent.parent.name
    return catalog_path.parent.name or "legacy"


def _looks_like_xml_feed(content_type: str, loaded_url: str) -> bool:
    lower = content_type.lower()
    return "xml" in lower or "output=atom" in loaded_url.lower()


def _extract_feed_blocks(*, soup: BeautifulSoup, base_url: str) -> tuple[list[str], list[str]]:
    blocks: list[str] = []
    links: list[str] = []
    entries = soup.find_all(lambda tag: getattr(tag, "name", None) and tag.name.lower().split(":")[-1] in {"entry", "item"})
    for entry in entries:
        title = _find_feed_value(entry, ("title",))
        summary = _find_feed_value(entry, ("summary", "description"))
        updated = _find_feed_value(entry, ("updated", "published", "pubdate"))
        link = _find_feed_link(entry)
        block = " ".join(part for part in (updated, title, summary) if part)
        block = " ".join(block.split())
        if len(block) >= 25:
            blocks.append(block)
        if link:
            links.append(urljoin(base_url, link))
    return _dedupe_preserve_order(blocks), _dedupe_preserve_order(links)


def _find_feed_value(node, names: tuple[str, ...]) -> str:
    for child in node.find_all(True):
        name = child.name.lower().split(":")[-1]
        if name in names:
            text = " ".join(child.get_text(" ", strip=True).split())
            if text:
                return text
    return ""


def _find_feed_link(node) -> str:
    for child in node.find_all(True):
        name = child.name.lower().split(":")[-1]
        if name != "link":
            continue
        href = child.get("href")
        if href:
            return str(href)
        text = " ".join(child.get_text(" ", strip=True).split())
        if text.startswith("http"):
            return text
    return ""


def _harvest_document_links(
    *,
    soup: BeautifulSoup,
    base_url: str,
    seed_source: SourceRecord,
    limit: int,
) -> tuple[list[str], list[str]]:
    candidates: list[tuple[int, str, str]] = []
    doc_extensions = PDF_EXTENSIONS | TEXT_EXTENSIONS | {".xls", ".xlsx", ".doc", ".docx", ".ppt", ".pptx"}

    for anchor in soup.find_all("a", href=True):
        href = urljoin(base_url, anchor["href"])
        parsed = urlparse(href)
        if parsed.scheme not in {"http", "https"}:
            continue

        text = " ".join(anchor.get_text(" ", strip=True).split())
        if not text:
            text = str(anchor.get("title") or anchor.get("aria-label") or "").strip()
        context = _extract_anchor_context(anchor)
        suffix = Path(parsed.path).suffix.lower()

        score = _score_link(href, text, seed_source)
        if suffix in doc_extensions:
            score += 3
        if _looks_like_document_label(text):
            score += 2
        if context:
            score += min(_score_text_block(context), 12)
        if text.lower() in GENERIC_LINK_TEXT:
            score -= 4
        if score <= 2:
            continue
        if suffix not in doc_extensions and not context and not _looks_like_document_label(text):
            continue

        summary = context or text
        summary = " ".join(summary.split())
        if text and len(text) > 8 and text not in summary:
            summary = f"{text} {summary}"
        if len(summary) < 25 and suffix not in doc_extensions:
            continue
        if _is_boilerplate_block(summary):
            continue
        candidates.append((score, href, summary))

    seen_urls: set[str] = set()
    blocks: list[str] = []
    links: list[str] = []
    for _score, href, summary in sorted(candidates, key=lambda item: item[0], reverse=True):
        if href in seen_urls:
            continue
        seen_urls.add(href)
        blocks.append(summary)
        links.append(href)
        if len(links) >= limit:
            break
    return blocks, links


def _extract_anchor_context(anchor) -> str:
    for ancestor in anchor.parents:
        if getattr(ancestor, "name", None) not in {"tr", "li", "article", "section", "div"}:
            continue
        text = " ".join(ancestor.get_text(" ", strip=True).split())
        if 40 <= len(text) <= 600 and not _is_boilerplate_block(text):
            return text
    return ""


def _looks_like_document_label(text: str) -> bool:
    lower = text.lower()
    return any(token in lower for token in FOLLOW_LINK_HINTS) or bool(re.search(r"\b(q[1-4]|fy20\d{2}|20\d{2})\b", lower))


def _extract_embedded_document_links(loaded_url: str, soup: BeautifulSoup) -> list[str]:
    links: list[str] = []
    parsed = urlparse(loaded_url)
    for key in EMBEDDED_DOCUMENT_QUERY_KEYS:
        for value in parse_qs(parsed.query).get(key, []):
            candidate = urljoin(loaded_url, value)
            if Path(urlparse(candidate).path).suffix.lower() in PDF_EXTENSIONS | TEXT_EXTENSIONS:
                links.append(candidate)

    for tag_name, attr_name in (("iframe", "src"), ("embed", "src"), ("object", "data")):
        for tag in soup.find_all(tag_name):
            target = tag.get(attr_name)
            if not target:
                continue
            candidate = urljoin(loaded_url, str(target))
            if Path(urlparse(candidate).path).suffix.lower() in PDF_EXTENSIONS | TEXT_EXTENSIONS:
                links.append(candidate)

    return _dedupe_preserve_order(links)


def _should_fetch_structured_sec_hub(*, loaded_url: str, title: str, blocks: list[str]) -> bool:
    haystack = f"{loaded_url} {title}".lower()
    if "sec-fil" not in haystack and "edgar" not in haystack:
        return False
    strong_block_count = sum(1 for block in blocks[:8] if _score_text_block(block) >= 8)
    return strong_block_count == 0


def _extract_structured_sec_hub_payload(
    html: str,
    loaded_url: str,
    source: SourceRecord,
) -> tuple[list[str], list[str], str | None]:
    q4_config = _parse_q4_sec_config(html)
    if q4_config:
        blocks, links = _fetch_q4_sec_filings(q4_config=q4_config, loaded_url=loaded_url)
        if blocks or links:
            return blocks, links, "q4_sec_feed"

    eqs_config = _parse_eqs_site_config(html=html, loaded_url=loaded_url)
    if eqs_config:
        blocks, links = _fetch_eqs_sec_filings(
            eqs_config=eqs_config,
            loaded_url=loaded_url,
            source=source,
        )
        if blocks or links:
            return blocks, links, "eqs_sec_api"

    return [], [], None


def _parse_q4_sec_config(html: str) -> dict[str, str] | None:
    if ".sec({" not in html and "q4MultiSecFilings" not in html:
        return None
    api_key_match = re.search(r"Q4ApiKey\s*=\s*['\"]([^'\"]+)['\"]", html)
    exchange_match = re.search(r"exchange\s*:\s*['\"]([^'\"]+)['\"]", html)
    symbol_match = re.search(r"symbol\s*:\s*['\"]([^'\"]+)['\"]", html)
    if not api_key_match or not exchange_match or not symbol_match:
        return None
    return {
        "api_key": api_key_match.group(1),
        "exchange": exchange_match.group(1),
        "symbol": symbol_match.group(1),
    }


def _fetch_q4_sec_filings(*, q4_config: dict[str, str], loaded_url: str) -> tuple[list[str], list[str]]:
    payload = _http_get_json(
        urljoin(loaded_url, "/feed/SECFiling.svc/GetEdgarFilingList"),
        params={
            "apiKey": q4_config["api_key"],
            "exchange": q4_config["exchange"],
            "symbol": q4_config["symbol"],
            "excludeNoDocuments": "true",
            "includeHtmlDocument": "false",
            "pageSize": "25",
            "pageNumber": "0",
            "year": "-1",
        },
    )
    items = payload.get("GetEdgarFilingListResult", []) if isinstance(payload, dict) else []
    return _build_q4_filing_payload(items=items, loaded_url=loaded_url)


def _build_q4_filing_payload(*, items: list[object], loaded_url: str) -> tuple[list[str], list[str]]:
    ranked: list[tuple[int, str, str]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        form_type = str(item.get("FilingTypeMnemonic", ""))
        description = str(item.get("FilingDescription", ""))
        score = _score_sec_filing_candidate(form_type=form_type, description=description)
        docs = item.get("DocumentList") or []
        doc_url = _best_q4_doc_url(docs, loaded_url=loaded_url)
        detail_url = urljoin(loaded_url, str(item.get("LinkToDetailPage", "")))
        summary = _format_q4_filing_block(item)
        ranked.append((score, doc_url or detail_url, summary))

    ranked.sort(key=lambda item: item[0], reverse=True)
    if not any(score > 0 for score, _, _ in ranked):
        ranked = ranked[:6]
    else:
        ranked = [item for item in ranked if item[0] > 0][:8]

    blocks = [summary for _score, _href, summary in ranked if summary]
    links = [href for _score, href, _summary in ranked if href]
    return _dedupe_preserve_order(blocks), _dedupe_preserve_order(links)


def _best_q4_doc_url(docs: object, *, loaded_url: str) -> str:
    if not isinstance(docs, list):
        return ""
    preferences = ("HTML", "XBRL_HTML", "CONVPDF", "CONVTEXT", "ORIG", "XLS")
    for preferred_type in preferences:
        for doc in docs:
            if not isinstance(doc, dict):
                continue
            if str(doc.get("DocumentType", "")) != preferred_type:
                continue
            url = str(doc.get("Url", "")).strip()
            if url:
                return urljoin(loaded_url, url)
    return ""


def _format_q4_filing_block(item: dict[str, object]) -> str:
    filing_date = str(item.get("FilingDate", "")).split(" ")[0]
    form_type = str(item.get("FilingTypeMnemonic", "")).strip()
    description = str(item.get("FilingDescription", "")).strip()
    doc_types = [
        str(doc.get("DocumentType", "")).lower()
        for doc in item.get("DocumentList", [])
        if isinstance(doc, dict) and doc.get("Url")
    ]
    doc_label = f" Documents: {', '.join(doc_types[:4])}" if doc_types else ""
    return " ".join(part for part in (filing_date, form_type, description) if part) + doc_label


def _parse_eqs_site_config(*, html: str, loaded_url: str) -> dict[str, str] | None:
    if "/_app/immutable/" not in html:
        return None
    for chunk_url in _extract_eqs_chunk_urls(html, loaded_url):
        chunk_text = _http_get_text(chunk_url)
        if "https://tools.cms-eqs.com" not in chunk_text:
            continue
        config = _parse_eqs_config_chunk(chunk_text)
        if config:
            return config
    return None


def _extract_eqs_chunk_urls(html: str, loaded_url: str) -> list[str]:
    matches = re.findall(r'href=["\']([^"\']*/_app/immutable/chunks/[^"\']+\.js)["\']', html)
    return _dedupe_preserve_order([urljoin(loaded_url, match) for match in matches[:8]])


def _parse_eqs_config_chunk(chunk_text: str) -> dict[str, str] | None:
    assignments = {
        match.group(1): match.group(3)
        for match in re.finditer(r"\b([A-Za-z_$][A-Za-z0-9_$]*)=(['\"])(.*?)\2", chunk_text)
    }
    export_match = re.search(r"export\{([^}]+)\}", chunk_text)
    if export_match is None:
        return None

    exports: dict[str, str] = {}
    for part in export_match.group(1).split(","):
        match = re.match(r"\s*([A-Za-z_$][A-Za-z0-9_$]*)\s+as\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*", part)
        if match:
            exports[match.group(2)] = match.group(1)

    api_base = assignments.get(exports.get("b", ""), "")
    site_id = assignments.get(exports.get("a", ""), "")
    secret = assignments.get(exports.get("q", ""), "")
    key = assignments.get(exports.get("r", ""), "")
    if not api_base or not api_base.startswith("https://tools.cms-eqs.com"):
        api_base = next((value for value in assignments.values() if value.startswith("https://tools.cms-eqs.com")), "")
    if not re.fullmatch(r"[a-f0-9]{6}", site_id):
        site_match = re.search(r'https://tools\.cms-eqs\.com["\'],[A-Za-z_$][A-Za-z0-9_$]*=(["\'])([a-f0-9]{6})\1', chunk_text)
        if site_match:
            site_id = site_match.group(2)
    if not re.fullmatch(r"[a-f0-9]{40}", key):
        key = next((value for value in assignments.values() if re.fullmatch(r"[a-f0-9]{40}", value)), "")
    if not re.fullmatch(r"[A-Za-z0-9]{24,40}", secret) or secret.startswith("6Lc") or secret == key:
        secret = next(
            (
                value
                for value in assignments.values()
                if re.fullmatch(r"[A-Za-z0-9]{24,40}", value)
                and value != key
                and not value.startswith("6Lc")
                and not value.islower()
            ),
            "",
        )
    if not api_base or not site_id or not key or not secret:
        return None
    return {
        "api_base": api_base,
        "site_id": site_id,
        "key": key,
        "secret": secret,
    }


def _fetch_eqs_sec_filings(
    *,
    eqs_config: dict[str, str],
    loaded_url: str,
    source: SourceRecord,
) -> tuple[list[str], list[str]]:
    token = _build_eqs_jwt(key=eqs_config["key"], secret=eqs_config["secret"])
    auth_headers = {"Authorization": f"Bearer {token}"}
    payload = _http_get_json(
        _join_url(eqs_config["api_base"], eqs_config["site_id"], "us/sec_filings_search"),
        headers=auth_headers,
        params={"limit": "25", "page": "1"},
    )
    items = payload.get("hydra:member", []) if isinstance(payload, dict) else []
    filtered_items = [item for item in items if isinstance(item, dict) and _matches_firm(source.firm, item)]
    if filtered_items:
        items = filtered_items
    return _build_eqs_filing_payload(
        items=items,
        loaded_url=loaded_url,
        eqs_config=eqs_config,
        auth_headers=auth_headers,
    )


def _build_eqs_filing_payload(
    *,
    items: list[object],
    loaded_url: str,
    eqs_config: dict[str, str],
    auth_headers: dict[str, str],
) -> tuple[list[str], list[str]]:
    ranked: list[tuple[int, dict[str, object], str]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        form = str((item.get("formType") or {}).get("mnemonic", ""))
        description = str((item.get("formType") or {}).get("shortDesc", ""))
        score = _score_sec_filing_candidate(form_type=form, description=description)
        summary = _format_eqs_filing_block(item)
        ranked.append((score, item, summary))

    ranked.sort(key=lambda item: item[0], reverse=True)
    if not any(score > 0 for score, _, _ in ranked):
        ranked = ranked[:6]
    else:
        ranked = [item for item in ranked if item[0] > 0][:8]

    blocks = [summary for _score, _item, summary in ranked if summary]
    for _score, item, _summary in ranked[:1]:
        blocks.extend(
            _fetch_eqs_filing_document_blocks(
                eqs_config=eqs_config,
                item=item,
                auth_headers=auth_headers,
                loaded_url=loaded_url,
            )
        )
    return _dedupe_preserve_order(blocks), []


def _best_eqs_doc_url(resources: object, *, loaded_url: str) -> str:
    if not isinstance(resources, dict):
        return ""
    origin = _url_origin(loaded_url)
    for key in ("HTML", "CONVTEXT", "RTF", "CONVPDF", "ORIG", "XLS"):
        value = str(resources.get(key, "")).strip()
        if value:
            return urljoin(origin, value)
    return ""


def _best_eqs_doc_format(resources: object) -> str:
    if not isinstance(resources, dict):
        return ""
    for key in ("HTML", "CONVTEXT", "RTF"):
        if resources.get(key):
            return key
    return ""


def _fetch_eqs_filing_document_blocks(
    *,
    eqs_config: dict[str, str],
    item: dict[str, object],
    auth_headers: dict[str, str],
    loaded_url: str,
) -> list[str]:
    filing_id = str(item.get("id", "")).strip()
    doc_format = _best_eqs_doc_format(item.get("resources") or {})
    if not filing_id or not doc_format:
        return []

    payload = _http_get_text(
        _join_url(eqs_config["api_base"], eqs_config["site_id"], "us/sec_filings", filing_id, doc_format),
        headers=auth_headers,
    )
    if not payload:
        return []
    if doc_format == "HTML":
        soup = BeautifulSoup(payload, "lxml")
        blocks = _extract_text_blocks(soup)
    else:
        blocks = [line.strip() for line in payload.splitlines() if len(line.strip()) >= 40]
    if not blocks:
        return []
    return _collect_relevant_snippets(blocks, limit=8) or blocks[:8]


def _format_eqs_filing_block(item: dict[str, object]) -> str:
    filed_date = str(item.get("filedDate", "")).split("T")[0]
    form = str((item.get("formType") or {}).get("mnemonic", "")).strip()
    description = str((item.get("formType") or {}).get("shortDesc", "")).strip()
    company = str((item.get("subjectCompany") or {}).get("name", "")).strip()
    return " ".join(part for part in (filed_date, company, form, description) if part)


def _build_eqs_jwt(*, key: str, secret: str) -> str:
    header = _b64url_json({"alg": "HS256", "typ": "JWT"})
    payload = _b64url_json({"iss": key, "exp": int(time.time()) + 20})
    signature = hmac.new(secret.encode("utf-8"), f"{header}.{payload}".encode("utf-8"), hashlib.sha256).digest()
    return f"{header}.{payload}.{base64.urlsafe_b64encode(signature).decode('utf-8').rstrip('=')}"


def _b64url_json(payload: dict[str, object]) -> str:
    raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def _matches_firm(firm: str, item: dict[str, object]) -> bool:
    tokens = _firm_tokens(firm)
    if not tokens:
        return False
    haystack = " ".join(
        str(value).lower()
        for value in (
            (item.get("subjectCompany") or {}).get("name", ""),
            (item.get("filedby") or {}).get("name", ""),
            (item.get("ticker") or ""),
        )
    )
    return any(token in haystack for token in tokens)


def _firm_tokens(firm: str) -> list[str]:
    tokens = []
    for token in re.findall(r"[a-z0-9]+", firm.lower()):
        if len(token) <= 2 or token in FIRM_TOKEN_STOPWORDS:
            continue
        tokens.append(token)
    return tokens


def _score_sec_filing_candidate(*, form_type: str, description: str) -> int:
    haystack = f"{form_type} {description}".lower()
    score = 0
    for needle, value in SEC_FORM_PRIORITY.items():
        if needle in haystack:
            score += value
    if any(token in haystack for token in VDA_KEYWORDS):
        score += 4
    if re.search(r"\b(20\d{2}|q[1-4]|fy20\d{2})\b", haystack):
        score += 1
    return score


def _http_get_text(url: str, *, headers: dict[str, str] | None = None) -> str:
    payload = _http_get(url, headers=headers)
    return payload.decode("utf-8", errors="ignore") if payload else ""


def _http_get_json(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    params: dict[str, str] | None = None,
) -> dict[str, object] | None:
    if params:
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}{urlencode(params, doseq=True)}"
    text = _http_get_text(url, headers=headers)
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _http_get(url: str, *, headers: dict[str, str] | None = None) -> bytes:
    request_headers = {"User-Agent": "Mozilla/5.0"}
    if headers:
        request_headers.update(headers)
    request = UrlRequest(url, headers=request_headers)
    try:
        with urlopen(request, timeout=15) as response:
            return response.read()
    except (HTTPError, URLError, TimeoutError, ValueError):
        return b""


def _join_url(*parts: str) -> str:
    clean = [part.strip("/") for part in parts if part]
    if not clean:
        return ""
    first, *rest = clean
    return "/".join([first] + rest)


def _url_origin(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}/"


def _extract_text_blocks(soup: BeautifulSoup) -> list[str]:
    _prune_noise(soup)
    root = _select_content_root(soup)

    blocks: list[str] = []
    for element in root.find_all(["h1", "h2", "h3", "h4", "p", "li", "td", "th", "tr"]):
        text = " ".join(element.get_text(" ", strip=True).split())
        if _is_viable_block(text):
            blocks.append(text)
    return _dedupe_preserve_order(blocks)


def _collect_relevant_snippets(blocks: list[str], *, limit: int) -> list[str]:
    ranked_blocks: list[tuple[int, str]] = []
    for block in blocks:
        score = _score_text_block(block)
        if score <= 0:
            continue
        ranked_blocks.append((score, block))
    snippets: list[str] = []
    for _score, block in sorted(ranked_blocks, key=lambda item: item[0], reverse=True):
        if block in snippets:
            continue
        snippets.append(block)
        if len(snippets) >= limit:
            break
    return snippets


def _prune_noise(soup: BeautifulSoup) -> None:
    for tag_name in ("script", "style", "noscript", "svg", "header", "footer", "nav", "aside"):
        for tag in soup.find_all(tag_name):
            tag.decompose()

    for tag in soup.find_all(True):
        if getattr(tag, "attrs", None) is None:
            continue
        if tag.name not in NOISE_CONTAINER_TAGS:
            continue
        attr_parts = []
        tag_id = tag.get("id")
        if tag_id:
            attr_parts.append(str(tag_id).lower())
        classes = tag.get("class") or []
        attr_parts.extend(str(value).lower() for value in classes)
        role = tag.get("role")
        if role:
            attr_parts.append(str(role).lower())
        attrs = " ".join(attr_parts)
        if attrs and any(hint in attrs for hint in NOISE_HINTS):
            tag.decompose()


def _select_content_root(soup: BeautifulSoup):
    for selector in CONTENT_ROOT_SELECTORS:
        node = soup.select_one(selector)
        if node is None:
            continue
        text = " ".join(node.get_text(" ", strip=True).split())
        if len(text) >= 300:
            return node
    return soup.body or soup


def _is_viable_block(text: str) -> bool:
    if len(text) < 40:
        return False
    if _is_boilerplate_block(text):
        return False
    return True


def _is_boilerplate_block(text: str) -> bool:
    lower = text.lower()
    if any(phrase in lower for phrase in BOILERPLATE_PHRASES):
        return True
    if lower.count("menu") >= 2:
        return True
    if ("overview" in lower or "view all" in lower) and _score_text_block(text) <= 2:
        return True
    return False


def _score_text_block(text: str) -> int:
    lower = text.lower()
    keyword_hits = sum(1 for keyword in VDA_KEYWORDS if keyword in lower)
    numeric_hits = len(NUMERIC_SIGNAL_RE.findall(text))
    score = keyword_hits * 4 + min(numeric_hits, 4) * 2
    if "$" in text:
        score += 2
    if "%" in text:
        score += 2
    if any(token in lower for token in ("q1", "q2", "q3", "q4", "fy2024", "fy2025", "fy2026", "2024", "2025", "2026")):
        score += 1
    if _is_boilerplate_block_candidate(lower):
        score -= 6
    return score


def _is_boilerplate_block_candidate(lower: str) -> bool:
    return any(phrase in lower for phrase in BOILERPLATE_PHRASES) or lower.count("menu") >= 2


def _find_candidate_links(
    *,
    soup: BeautifulSoup,
    base_url: str,
    seed_source: SourceRecord,
    limit: int,
) -> list[str]:
    base_host = urlparse(base_url).hostname or ""
    base_domain = ".".join(base_host.split(".")[-2:]) if base_host else ""
    candidates: list[tuple[int, str]] = []

    for anchor in soup.find_all("a", href=True):
        href = urljoin(base_url, anchor["href"])
        parsed = urlparse(href)
        if parsed.scheme not in {"http", "https"}:
            continue
        if parsed.path in {"", "/"} and not parsed.query:
            continue

        link_host = parsed.hostname or ""
        link_domain = ".".join(link_host.split(".")[-2:]) if link_host else ""
        if base_domain and link_domain and link_domain != base_domain and "sec.gov" not in link_host:
            continue

        text = " ".join(anchor.get_text(" ", strip=True).split())
        if text.lower() in GENERIC_LINK_TEXT:
            continue
        score = _score_link(href, text, seed_source)
        if score > 0:
            candidates.append((score, href))

    ordered_urls = [url for _score, url in sorted(candidates, reverse=True)]
    return _dedupe_preserve_order(ordered_urls)[:limit]


def _score_link(url: str, text: str, seed_source: SourceRecord) -> int:
    haystack = f"{url} {text}".lower()
    score = 0
    for keyword in FOLLOW_LINK_HINTS:
        if keyword in haystack:
            score += 1
    if score == 0:
        return 0
    path = urlparse(url).path.lower()
    suffix = Path(path).suffix.lower()
    if suffix in PDF_EXTENSIONS:
        score += 3
    elif suffix in TEXT_EXTENSIONS:
        score += 1
    if "sec.gov" in urlparse(url).netloc:
        score += 2
    if seed_source.document_type.lower() in haystack:
        score += 1
    return score


def _is_pdf_url(url: str) -> bool:
    return Path(urlparse(url).path).suffix.lower() in PDF_EXTENSIONS


def _extract_pdf_text(body: bytes) -> tuple[str, dict[str, object]]:
    if PdfReader is None:
        return "", {"pages": 0, "extractor": "unavailable"}

    with NamedTemporaryFile(suffix=".pdf") as handle:
        handle.write(body)
        handle.flush()
        reader = PdfReader(handle.name)
        pages = [page.extract_text() or "" for page in reader.pages]
        metadata = {
            "pages": len(reader.pages),
            "extractor": "pypdf",
            "title": getattr(reader.metadata, "title", None) if reader.metadata else None,
        }
        return "\n\n".join(pages), metadata


def _write_text_artifact(raw_dir: Path, source: SourceRecord, loaded_url: str, text: str) -> Path:
    slug = _slugify(source.title or source.source_id or loaded_url)
    url_hash = hashlib.sha1(loaded_url.encode("utf-8")).hexdigest()[:8]
    target = raw_dir / f"{source.source_id}_{slug}_{url_hash}.txt"
    header = [
        f"Source ID: {source.source_id}",
        f"Firm: {source.firm}",
        f"Title: {source.title}",
        f"Document Type: {source.document_type}",
        f"Bias Tag: {source.bias_tag}",
        f"Seed URL: {source.url}",
        f"Loaded URL: {loaded_url}",
        "",
    ]
    target.write_text("\n".join(header) + text, encoding="utf-8")
    return target


def _slugify(value: str) -> str:
    lowered = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return lowered[:80] or "source"


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped


def _stats_to_dict(stats: object) -> dict[str, object]:
    summary: dict[str, object] = {}
    for attr in ("requests_finished", "requests_failed", "requests_total", "retry_histogram"):
        if hasattr(stats, attr):
            summary[attr] = getattr(stats, attr)
    return summary


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    summary = asyncio.run(crawl_sources(args))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
