from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.analyzer.consulting_context import (
    build_context_payload,
    classify_claim_scope,
    classify_utility,
    detect_context_themes,
    extract_claims,
    find_latest_consulting_seed_results_file,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_seed(
    source_id: str,
    *,
    title: str = "Some Report",
    text_length: int = 10_000,
    snippets: list[str] | None = None,
    firm: str = "Industry-wide",
    loaded_url: str = "https://example.com/report",
    seed_url: str = "https://example.com/report",
) -> dict:
    return {
        "source_id": source_id,
        "firm": firm,
        "title": title,
        "document_type": "industry_report",
        "bias_tag": "industry-report",
        "seed_url": seed_url,
        "loaded_url": loaded_url,
        "text_length": text_length,
        "relevant_snippets": snippets if snippets is not None else [
            "Private capital broadly raised $1.3 trillion last year while buyout fundraising dropped 16%.",
            "Global dry powder sits at $3.2 trillion, putting pressure on GPs to deploy capital efficiently.",
            "Fee compression across the asset management industry has intensified over the past five years.",
        ],
    }


def _make_audit(
    source_id: str,
    *,
    status: str = "ok",
    off_domain: int = 0,
    seed_url: str = "https://example.com/report",
) -> dict:
    return {
        "source_id": source_id,
        "title": "Some Report",
        "seed_url": seed_url,
        "status": status,
        "off_domain_followup_count": off_domain,
    }


# ---------------------------------------------------------------------------
# detect_context_themes
# ---------------------------------------------------------------------------

class TestDetectContextThemes(unittest.TestCase):

    def test_themes_wealth_distribution(self) -> None:
        themes = detect_context_themes("Wealth managers are expanding access to private markets.")
        self.assertIn("wealth_distribution", themes)

    def test_themes_fundraising_lp_demand(self) -> None:
        themes = detect_context_themes("Global dry powder remains elevated heading into 2026.")
        self.assertIn("fundraising_lp_demand", themes)

    def test_themes_private_credit(self) -> None:
        themes = detect_context_themes("Private credit has become a key asset class for institutional allocators.")
        self.assertIn("private_credit", themes)

    def test_themes_margin_operating_model(self) -> None:
        themes = detect_context_themes("Intensifying fee compression is forcing firms to reconsider their operating models.")
        self.assertIn("margin_operating_model", themes)

    def test_themes_mna_consolidation(self) -> None:
        themes = detect_context_themes("A wave of acquisitions is reshaping the alternative asset management landscape.")
        self.assertIn("mna_consolidation", themes)

    def test_themes_democratization(self) -> None:
        themes = detect_context_themes("New semi-liquid vehicles are opening private markets to retail investors.")
        self.assertIn("democratization", themes)

    def test_themes_other_when_no_match(self) -> None:
        themes = detect_context_themes("The weather is sunny and the quarterly earnings call went smoothly.")
        self.assertEqual(themes, ["other"])

    def test_themes_multiple_detected(self) -> None:
        text = (
            "Wealth managers are adopting semi-liquid vehicles while dry powder reaches record highs "
            "and private credit continues to attract allocations."
        )
        themes = detect_context_themes(text)
        self.assertIn("wealth_distribution", themes)
        self.assertIn("democratization", themes)
        self.assertIn("fundraising_lp_demand", themes)
        self.assertIn("private_credit", themes)
        self.assertNotIn("other", themes)

    def test_themes_case_insensitive(self) -> None:
        themes = detect_context_themes("WEALTH MANAGERS CONTINUE TO EMBRACE SEMI-LIQUID VEHICLES.")
        self.assertIn("wealth_distribution", themes)
        self.assertIn("democratization", themes)

    # Retain the original combined test so the class name stays compatible
    def test_detect_context_themes_finds_wealth_and_democratization(self) -> None:
        text = (
            "Wealth managers are expanding retail access to semi-liquid private market vehicles "
            "for individual investors."
        )
        themes = detect_context_themes(text)
        self.assertIn("wealth_distribution", themes)
        self.assertIn("democratization", themes)


# ---------------------------------------------------------------------------
# extract_claims
# ---------------------------------------------------------------------------

class TestExtractClaims(unittest.TestCase):

    def test_claims_prefers_numeric(self) -> None:
        claims = extract_claims(
            title="Private Markets in Motion",
            snippets=[
                "Private market assets under management have been growing at over 10% a year.",
                "Investor demand, product innovation, and regulatory change should lead to continued growth.",
                "Contact us for more information.",
            ],
        )
        self.assertGreaterEqual(len(claims), 2)
        self.assertTrue(any("10%" in c for c in claims))
        self.assertFalse(any("Contact us" in c for c in claims))

    def test_claims_filters_contact_info(self) -> None:
        claims = extract_claims(
            title="Report",
            snippets=[
                "Contact us at support@example.com for pricing details and subscription options.",
                "Alternative assets reached $13 trillion in AUM globally last year, up 12% annually.",
            ],
        )
        self.assertFalse(any("contact" in c.lower() for c in claims))

    def test_claims_filters_short_sentences(self) -> None:
        claims = extract_claims(
            title="Report",
            snippets=[
                "Short.",
                "Also brief text here.",
                "Alternative assets reached $13 trillion in AUM globally last year, growing over 12% annually.",
            ],
        )
        # Only the long sentence with a number qualifies
        self.assertTrue(all(len(c) >= 40 for c in claims))
        self.assertTrue(any("$13 trillion" in c for c in claims))

    def test_claims_deduplicates(self) -> None:
        sentence = "Global dry powder sits at $3.2 trillion, putting pressure on GPs to deploy capital."
        claims = extract_claims(
            title="Report",
            snippets=[sentence, sentence],
        )
        matching = [c for c in claims if "$3.2 trillion" in c]
        self.assertEqual(len(matching), 1)

    def test_claims_empty_snippets(self) -> None:
        claims = extract_claims(title="Report", snippets=[])
        self.assertEqual(claims, [])

    def test_claims_max_claims_limit(self) -> None:
        snippets = [
            f"Alternative assets reached ${i} trillion in AUM globally last year, up {i}% annually."
            for i in range(1, 20)
        ]
        claims = extract_claims(title="Report", snippets=snippets, max_claims=3)
        self.assertLessEqual(len(claims), 3)

    def test_claims_title_included_if_relevant(self) -> None:
        # Title contains a theme keyword ("fundraising") and is not low-value
        claims = extract_claims(
            title="Global Fundraising Trends 2026",
            snippets=[],
        )
        self.assertTrue(any("fundraising" in c.lower() for c in claims))

    def test_claims_title_excluded_if_low_value(self) -> None:
        claims = extract_claims(
            title="LinkedIn | Global Fundraising Trends for Alternative Assets",
            snippets=[],
        )
        self.assertEqual(claims, [])

    def test_claims_strips_whitespace(self) -> None:
        claims = extract_claims(
            title="Report",
            snippets=["  Global dry powder sits at $3.2 trillion,   putting pressure on GPs.  "],
        )
        for c in claims:
            self.assertEqual(c, c.strip())
            self.assertNotIn("  ", c)  # no double spaces


# ---------------------------------------------------------------------------
# classify_claim_scope (NEW)
# ---------------------------------------------------------------------------

class TestClassifyClaimScope(unittest.TestCase):

    def test_scope_market_global_keyword(self) -> None:
        claim = "Global dry powder sits at $1.3 trillion across the alternatives universe."
        self.assertEqual(classify_claim_scope(claim), "market")

    def test_scope_market_industry_keyword(self) -> None:
        claim = "Industry-wide fee compression has accelerated over the past decade."
        self.assertEqual(classify_claim_scope(claim), "market")

    def test_scope_single_firm_possessive(self) -> None:
        claim = "Apollo's $500 billion AUM reflects its diversified platform strategy."
        self.assertEqual(classify_claim_scope(claim), "single_firm")

    def test_scope_single_firm_the_firm(self) -> None:
        claim = "The firm oversaw around $811 billion in assets as of year-end 2025."
        self.assertEqual(classify_claim_scope(claim), "single_firm")

    def test_scope_multi_firm_multiple_possessives(self) -> None:
        claim = "BlackRock's $40 billion infrastructure sale was followed by Macquarie's $40 billion raise."
        self.assertEqual(classify_claim_scope(claim), "multi_firm")

    def test_scope_segment_default(self) -> None:
        claim = "Private credit has grown rapidly in recent years driven by bank retrenchment."
        self.assertEqual(classify_claim_scope(claim), "segment")

    def test_scope_possessive_with_market_stays_market(self) -> None:
        # One possessive + market keyword: possessives is truthy but has_market is also true.
        # Logic: has_the_firm=False, len(possessives)<2, possessives AND has_market → skips single_firm branch,
        # falls to has_market → "market"
        claim = "ECP's $5 billion strategy targets opportunities in the global energy market."
        self.assertEqual(classify_claim_scope(claim), "market")

    def test_scope_the_company_pattern(self) -> None:
        claim = "The company reported $2.5 billion in fee-related earnings last quarter."
        self.assertEqual(classify_claim_scope(claim), "single_firm")


# ---------------------------------------------------------------------------
# classify_utility
# ---------------------------------------------------------------------------

class TestClassifyUtility(unittest.TestCase):

    def test_utility_low_when_status_not_ok(self) -> None:
        result = classify_utility(
            text_length=50_000,
            status="failed",
            title="Excellent Report",
            claims=["Global dry powder sits at $3.2 trillion."],
            themes=["fundraising_lp_demand"],
        )
        self.assertEqual(result, "low")

    def test_utility_low_when_title_linkedin(self) -> None:
        result = classify_utility(
            text_length=50_000,
            status="ok",
            title="LinkedIn | Private Markets Outlook 2026",
            claims=["Global dry powder sits at $3.2 trillion."],
            themes=["fundraising_lp_demand"],
        )
        self.assertEqual(result, "low")

    def test_utility_high_large_text_many_claims(self) -> None:
        result = classify_utility(
            text_length=10_000,
            status="ok",
            title="Private Markets Outlook",
            claims=[
                "Global dry powder sits at $3.2 trillion.",
                "Fee compression has accelerated across all segments.",
                "Private credit reached $1.7 trillion in AUM globally.",
            ],
            themes=["other"],
        )
        self.assertEqual(result, "high")

    def test_utility_high_medium_text_themed(self) -> None:
        result = classify_utility(
            text_length=5_000,
            status="ok",
            title="Private Markets Report",
            claims=[
                "Global dry powder sits at $3.2 trillion.",
                "Fee compression has accelerated across all segments.",
            ],
            themes=["fundraising_lp_demand"],
        )
        self.assertEqual(result, "high")

    def test_utility_medium_moderate_text(self) -> None:
        result = classify_utility(
            text_length=2_500,
            status="ok",
            title="Brief Market Note",
            claims=["Fee compression has intensified across the alternatives sector."],
            themes=["margin_operating_model"],
        )
        self.assertEqual(result, "medium")

    def test_utility_low_small_text(self) -> None:
        result = classify_utility(
            text_length=500,
            status="ok",
            title="Snippet",
            claims=["Global dry powder sits at $3.2 trillion."],
            themes=["fundraising_lp_demand"],
        )
        self.assertEqual(result, "low")

    def test_utility_low_no_claims(self) -> None:
        result = classify_utility(
            text_length=50_000,
            status="ok",
            title="Large Report With No Extractable Claims",
            claims=[],
            themes=["other"],
        )
        self.assertEqual(result, "low")

    def test_utility_high_requires_themed_at_5k(self) -> None:
        # 5000 chars, 2 claims but themes=["other"] → does NOT meet second "high" branch
        # Checks next branch: 5000 >= 2500 AND 2 claims → "medium"
        result = classify_utility(
            text_length=5_000,
            status="ok",
            title="Thematic Report",
            claims=[
                "Global dry powder sits at $3.2 trillion.",
                "Fee compression has accelerated across all segments.",
            ],
            themes=["other"],
        )
        self.assertEqual(result, "medium")


# ---------------------------------------------------------------------------
# build_context_payload
# ---------------------------------------------------------------------------

class TestBuildContextPayload(unittest.TestCase):

    # ------- exclusion rules -------

    def test_payload_excludes_deduped_in_base(self) -> None:
        seed_rows = [_make_seed("PS-VD-901")]
        audit_rows = [_make_audit("PS-VD-901", status="deduped_in_base")]
        payload = build_context_payload(seed_rows=seed_rows, audit_rows=audit_rows)
        self.assertEqual(payload["metadata"]["included_source_count"], 0)
        self.assertEqual(payload["metadata"]["excluded_source_count"], 1)

    def test_payload_excludes_failed(self) -> None:
        seed_rows = [_make_seed("PS-VD-901")]
        audit_rows = [_make_audit("PS-VD-901", status="failed")]
        payload = build_context_payload(seed_rows=seed_rows, audit_rows=audit_rows)
        self.assertEqual(payload["metadata"]["included_source_count"], 0)

    def test_payload_excludes_zero_text(self) -> None:
        seed_rows = [_make_seed("PS-VD-901", text_length=0, snippets=[])]
        audit_rows = [_make_audit("PS-VD-901", status="zero_text")]
        payload = build_context_payload(seed_rows=seed_rows, audit_rows=audit_rows)
        self.assertEqual(payload["metadata"]["included_source_count"], 0)

    def test_payload_excludes_missing_seed_result(self) -> None:
        # audit_row with no matching seed
        audit_rows = [_make_audit("PS-VD-999", status="missing_seed_result")]
        payload = build_context_payload(seed_rows=[], audit_rows=audit_rows)
        self.assertEqual(payload["metadata"]["included_source_count"], 0)
        self.assertEqual(payload["metadata"]["excluded_source_count"], 1)

    # ------- inclusion -------

    def test_payload_includes_ok_high_utility(self) -> None:
        seed_rows = [_make_seed("PS-VD-901")]
        audit_rows = [_make_audit("PS-VD-901", status="ok")]
        payload = build_context_payload(seed_rows=seed_rows, audit_rows=audit_rows)
        self.assertEqual(payload["metadata"]["included_source_count"], 1)
        self.assertEqual(payload["sources"][0]["source_id"], "PS-VD-901")

    # ------- metadata counts -------

    def test_payload_metadata_counts_correct(self) -> None:
        seed_rows = [
            _make_seed("PS-VD-901"),
            _make_seed("PS-VD-902", text_length=0, snippets=[]),
        ]
        audit_rows = [
            _make_audit("PS-VD-901", status="ok"),
            _make_audit("PS-VD-902", status="zero_text"),
        ]
        payload = build_context_payload(seed_rows=seed_rows, audit_rows=audit_rows)
        meta = payload["metadata"]
        self.assertEqual(meta["consulting_catalog_count"], 2)
        self.assertEqual(meta["seed_result_count"], 2)
        self.assertEqual(meta["included_source_count"] + meta["excluded_source_count"], 2)

    # ------- theme aggregation -------

    def test_payload_theme_counts_aggregated(self) -> None:
        seed_rows = [
            _make_seed(
                "PS-VD-901",
                snippets=[
                    "Private capital broadly raised $1.3 trillion last year while buyout fundraising dropped 16%.",
                    "Global dry powder sits at $3.2 trillion, putting pressure on GPs to deploy capital efficiently.",
                    "Fee compression across the asset management industry has intensified over five years.",
                ],
            ),
        ]
        audit_rows = [_make_audit("PS-VD-901", status="ok")]
        payload = build_context_payload(seed_rows=seed_rows, audit_rows=audit_rows)
        theme_counts = payload["metadata"]["theme_counts"]
        # At least one theme must be detected (fundraising from "dry powder")
        self.assertGreater(sum(theme_counts.values()), 0)
        # "other" should NOT be in theme_counts if real themes matched
        self.assertNotIn("other", theme_counts)

    # ------- claim shape -------

    def test_payload_claims_have_scope(self) -> None:
        seed_rows = [_make_seed("PS-VD-901")]
        audit_rows = [_make_audit("PS-VD-901", status="ok")]
        payload = build_context_payload(seed_rows=seed_rows, audit_rows=audit_rows)
        claims = payload["sources"][0]["claims"]
        self.assertGreater(len(claims), 0)
        for claim in claims:
            self.assertIsInstance(claim, dict)
            self.assertIn("text", claim)
            self.assertIn("scope", claim)
            self.assertIsInstance(claim["text"], str)
            self.assertIsInstance(claim["scope"], str)
            self.assertIn(claim["scope"], {"market", "segment", "multi_firm", "single_firm"})

    # ------- sort order -------

    def test_payload_sorted_by_source_id(self) -> None:
        seed_rows = [
            _make_seed("PS-VD-910"),
            _make_seed("PS-VD-902"),
            _make_seed("PS-VD-907"),
        ]
        audit_rows = [
            _make_audit("PS-VD-910", status="ok"),
            _make_audit("PS-VD-902", status="ok"),
            _make_audit("PS-VD-907", status="ok"),
        ]
        payload = build_context_payload(seed_rows=seed_rows, audit_rows=audit_rows)
        source_ids = [s["source_id"] for s in payload["sources"]]
        self.assertEqual(source_ids, sorted(source_ids))

    # ------- empty inputs -------

    def test_payload_empty_inputs(self) -> None:
        payload = build_context_payload(seed_rows=[], audit_rows=[])
        self.assertEqual(payload["sources"], [])
        self.assertEqual(payload["metadata"]["included_source_count"], 0)
        self.assertEqual(payload["metadata"]["excluded_source_count"], 0)

    # ------- seed without audit match is not iterated -------

    def test_payload_seed_without_audit_skipped(self) -> None:
        # seed_rows has PS-VD-901 but audit_rows has only PS-VD-902
        seed_rows = [_make_seed("PS-VD-901")]
        audit_rows = [_make_audit("PS-VD-902", status="ok")]
        payload = build_context_payload(seed_rows=seed_rows, audit_rows=audit_rows)
        # PS-VD-901 seed has no audit row → never iterated → not included
        ids = [s["source_id"] for s in payload["sources"]]
        self.assertNotIn("PS-VD-901", ids)

    # ------- domain extraction -------

    def test_payload_domain_extracted(self) -> None:
        seed_rows = [_make_seed("PS-VD-901", loaded_url="https://www.bain.com/insights/private-equity/")]
        audit_rows = [_make_audit("PS-VD-901", status="ok")]
        payload = build_context_payload(seed_rows=seed_rows, audit_rows=audit_rows)
        self.assertEqual(payload["sources"][0]["domain"], "www.bain.com")

    # ------- snippets capped at 5 -------

    def test_payload_snippets_capped_at_5(self) -> None:
        six_snippets = [
            f"Alternative assets reached ${i} trillion in AUM globally, growing {i}% per year."
            for i in range(1, 8)
        ]
        seed_rows = [_make_seed("PS-VD-901", snippets=six_snippets)]
        audit_rows = [_make_audit("PS-VD-901", status="ok")]
        payload = build_context_payload(seed_rows=seed_rows, audit_rows=audit_rows)
        self.assertLessEqual(len(payload["sources"][0]["top_snippets"]), 5)

    # Retain original combined test
    def test_build_context_payload_excludes_zero_text_and_failed_sources(self) -> None:
        seed_rows = [
            {
                "source_id": "PS-VD-902",
                "firm": "Industry-wide (Bain)",
                "title": "Private Equity Outlook 2026",
                "document_type": "industry_report",
                "bias_tag": "industry-report",
                "seed_url": "https://example.com/bain",
                "loaded_url": "https://example.com/bain",
                "text_length": 12000,
                "relevant_snippets": [
                    "Private capital broadly raised $1.3 trillion last year while buyout fundraising dropped 16%.",
                    "Global dry powder sits at $1.3 trillion, putting pressure on GPs to deploy capital.",
                ],
            },
            {
                "source_id": "PS-VD-908",
                "firm": "Industry-wide (Casey Quirk)",
                "title": "Asset Managers Pivot to Private Markets",
                "document_type": "industry_report",
                "bias_tag": "industry-report",
                "seed_url": "https://example.com/casey-quirk",
                "loaded_url": "https://example.com/casey-quirk",
                "text_length": 0,
                "relevant_snippets": [],
            },
        ]
        audit_rows = [
            {
                "source_id": "PS-VD-902",
                "title": "Private Equity Outlook 2026",
                "seed_url": "https://example.com/bain",
                "status": "ok",
                "off_domain_followup_count": 0,
            },
            {
                "source_id": "PS-VD-908",
                "title": "Asset Managers Pivot to Private Markets",
                "seed_url": "https://example.com/casey-quirk",
                "status": "zero_text",
                "off_domain_followup_count": 0,
            },
            {
                "source_id": "PS-VD-905",
                "title": "Winning in alternatives",
                "seed_url": "https://example.com/mckinsey",
                "status": "failed",
                "off_domain_followup_count": 0,
            },
        ]
        payload = build_context_payload(seed_rows=seed_rows, audit_rows=audit_rows)
        self.assertEqual(payload["metadata"]["included_source_count"], 1)
        self.assertEqual(payload["metadata"]["excluded_source_count"], 2)
        self.assertEqual(payload["sources"][0]["source_id"], "PS-VD-902")
        self.assertGreaterEqual(len(payload["sources"][0]["claims"]), 1)
        excluded_ids = {row["source_id"] for row in payload["metadata"]["excluded_sources"]}
        self.assertEqual(excluded_ids, {"PS-VD-905", "PS-VD-908"})


# ---------------------------------------------------------------------------
# find_latest_consulting_seed_results_file
# ---------------------------------------------------------------------------

class TestFindLatestConsultingSeedResultsFile(unittest.TestCase):

    def test_find_latest_no_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = find_latest_consulting_seed_results_file(tmpdir)
            self.assertIsNone(result)

    def test_find_latest_single_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            p = (
                Path(tmpdir)
                / "2026-01-01"
                / "1-universe"
                / "crawl-with-consulting"
            )
            p.mkdir(parents=True)
            target = p / "consulting_seed_results.json"
            target.write_text("[]")
            result = find_latest_consulting_seed_results_file(tmpdir)
            self.assertEqual(result, target)

    def test_find_latest_multiple_picks_last(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            for date in ["2026-01-01", "2026-02-15", "2026-03-09"]:
                p = (
                    Path(tmpdir)
                    / date
                    / "1-universe"
                    / "crawl-with-consulting"
                )
                p.mkdir(parents=True)
                (p / "consulting_seed_results.json").write_text("[]")

            result = find_latest_consulting_seed_results_file(tmpdir)
            self.assertIsNotNone(result)
            assert result is not None
            self.assertIn("2026-03-09", str(result))


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases(unittest.TestCase):

    def test_text_length_none_treated_as_zero(self) -> None:
        seed_rows = [
            {
                "source_id": "PS-VD-901",
                "firm": "Bain",
                "title": "Outlook",
                "document_type": "industry_report",
                "bias_tag": "industry-report",
                "seed_url": "https://example.com",
                "loaded_url": "https://example.com",
                "text_length": None,
                "relevant_snippets": [],
            }
        ]
        audit_rows = [_make_audit("PS-VD-901", status="ok")]
        # Should not raise; text_length=None coerced to 0 → utility=low → excluded
        payload = build_context_payload(seed_rows=seed_rows, audit_rows=audit_rows)
        self.assertEqual(payload["metadata"]["included_source_count"], 0)

    def test_relevant_snippets_none(self) -> None:
        seed_rows = [
            {
                "source_id": "PS-VD-901",
                "firm": "Bain",
                "title": "Outlook",
                "document_type": "industry_report",
                "bias_tag": "industry-report",
                "seed_url": "https://example.com",
                "loaded_url": "https://example.com",
                "text_length": 0,
                "relevant_snippets": None,
            }
        ]
        audit_rows = [_make_audit("PS-VD-901", status="ok")]
        # Should not raise; None snippets treated as empty
        payload = build_context_payload(seed_rows=seed_rows, audit_rows=audit_rows)
        self.assertIsNotNone(payload)

    def test_source_id_whitespace_stripped(self) -> None:
        seed_rows = [_make_seed("  PS-VD-901  ")]
        # audit row uses the same padded id; build_context_payload strips both
        audit_rows = [
            {
                "source_id": "  PS-VD-901  ",
                "title": "Some Report",
                "seed_url": "https://example.com/report",
                "status": "ok",
                "off_domain_followup_count": 0,
            }
        ]
        payload = build_context_payload(seed_rows=seed_rows, audit_rows=audit_rows)
        if payload["sources"]:
            self.assertEqual(payload["sources"][0]["source_id"], "PS-VD-901")


if __name__ == "__main__":
    unittest.main()
