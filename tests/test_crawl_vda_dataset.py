import unittest

from src.analyzer.crawl_vda_dataset import (
    assign_shortlists,
    build_firm_summaries,
    count_signal_mentions,
    detect_noise_flags,
    prune_noise_snippets,
    rank_signal_snippets,
    score_source_record,
    unique_signal_ids,
)


class CrawlVdaDatasetTest(unittest.TestCase):
    def test_signal_mentions_capture_core_vda_terms(self) -> None:
        text = (
            "Assets under management reached $938 billion. Fee-earning AUM grew 18%. "
            "Fee-related earnings margin expanded to 54% and fundraising totaled $18 billion."
        )
        counts = count_signal_mentions(text)
        self.assertGreater(counts["aum"], 0)
        self.assertGreater(counts["feaum"], 0)
        self.assertGreater(counts["fre"], 0)
        self.assertGreater(counts["fundraising"], 0)
        self.assertGreater(counts["margin"], 0)

    def test_source_score_penalizes_xbrl_noise(self) -> None:
        useful_item = {
            "document_type": "annual_report",
            "bias_tag": "regulatory-filing",
            "text_length": 8000,
            "loaded_url": "https://example.com/10k.html",
            "relevant_snippets": [
                "AUM reached $120 billion, fee-related earnings margin was 48%, and fundraising totaled $12 billion."
            ],
        }
        useful_text = useful_item["relevant_snippets"][0]
        useful_mentions = count_signal_mentions(useful_text)
        useful_snippets = rank_signal_snippets(useful_item["relevant_snippets"])
        useful_flags = detect_noise_flags(item=useful_item, text=useful_text, signal_mentions=useful_mentions)
        useful_score = score_source_record(
            item=useful_item,
            signal_mentions=useful_mentions,
            signal_snippets=useful_snippets,
            noise_flags=useful_flags,
        )

        noisy_item = {
            "document_type": "annual_report",
            "bias_tag": "regulatory-filing",
            "text_length": 9000,
            "loaded_url": "https://example.com/xbrl.html",
            "relevant_snippets": [
                "Namespace Prefix: dei Data Type: dei:centralIndexKeyItemType Reference 1: http://www.xbrl.org/2003/role/presentationRef"
            ],
        }
        noisy_text = noisy_item["relevant_snippets"][0]
        noisy_mentions = count_signal_mentions(noisy_text)
        noisy_snippets = rank_signal_snippets(noisy_item["relevant_snippets"])
        noisy_flags = detect_noise_flags(item=noisy_item, text=noisy_text, signal_mentions=noisy_mentions)
        noisy_score = score_source_record(
            item=noisy_item,
            signal_mentions=noisy_mentions,
            signal_snippets=noisy_snippets,
            noise_flags=noisy_flags,
        )

        self.assertGreater(useful_score, noisy_score)

    def test_firm_summary_reports_coverage_gap(self) -> None:
        source_records = [
            {
                "firm_id": "FIRM-001",
                "firm_name": "Blackstone Inc.",
                "ticker": "BX",
                "source_id": "PS-VD-001",
                "title": "Blackstone 10-K",
                "loaded_url": "https://example.com/bx-10k",
                "document_type": "annual_report",
                "bias_tag": "regulatory-filing",
                "utility_score": 20,
                "text_length": 1000,
                "include_in_vda_shortlist": True,
                "shortlist_bucket": "core",
                "signal_mentions": {
                    "aum": 3,
                    "feaum": 2,
                    "fre": 2,
                    "fundraising": 0,
                    "margin": 1,
                    "deployment": 0,
                    "realizations": 0,
                    "carry": 0,
                    "perpetual_capital": 0,
                    "credit": 0,
                    "insurance": 0,
                    "wealth": 0,
                },
                "ranked_snippets": [
                    {
                        "signal_id": "aum",
                        "score": 12,
                        "snippet": "AUM reached $120 billion.",
                    }
                ],
            }
        ]
        summary = build_firm_summaries(source_records)[0]
        self.assertIn("fundraising", summary["coverage_gaps"])
        self.assertEqual(summary["shortlisted_source_count"], 1)

    def test_unique_signal_ids_dedupes_ranked_snippets(self) -> None:
        signal_ids = unique_signal_ids(
            [
                {"signal_id": "aum"},
                {"signal_id": "aum"},
                {"signal_id": "fre"},
                {"signal_id": "fundraising"},
            ]
        )
        self.assertEqual(signal_ids, ["aum", "fre", "fundraising"])

    def test_shortlist_excludes_low_signal_fallback_records(self) -> None:
        records = [
            {
                "firm_id": "FIRM-100",
                "firm_name": "Low Signal Co.",
                "ticker": "LSC",
                "utility_score": 10,
                "text_length": 1200,
                "signal_mentions": {
                    "aum": 0,
                    "feaum": 0,
                    "fre": 0,
                    "fundraising": 0,
                    "margin": 0,
                    "deployment": 0,
                    "realizations": 0,
                    "carry": 0,
                    "perpetual_capital": 0,
                    "credit": 0,
                    "insurance": 0,
                    "wealth": 0,
                },
                "noise_flags": {
                    "is_empty": False,
                    "is_short": False,
                    "is_xbrl_reference_noise": False,
                    "is_market_noise": False,
                    "is_sec_index_page": False,
                    "is_symbol_hub": False,
                    "is_low_signal": True,
                },
                "include_in_vda_shortlist": False,
                "shortlist_bucket": "discard",
                "shortlist_rank": None,
            }
        ]
        assign_shortlists(records)
        self.assertFalse(records[0]["include_in_vda_shortlist"])
        self.assertEqual(records[0]["shortlist_bucket"], "discard")

    def test_prune_noise_snippets_removes_symbol_page_summary(self) -> None:
        snippets = rank_signal_snippets(["Patria: Latam's Premier Asset Manager Logs $50bn In AUM"])
        pruned = prune_noise_snippets(
            item={
                "title": "Patria Investments Limited (PAX) Stock Price, Quote, News & Analysis | Seeking Alpha",
                "loaded_url": "https://seekingalpha.com/symbol/PAX",
                "document_type": "earnings_call_transcript",
            },
            signal_snippets=snippets,
        )
        self.assertEqual(pruned, [])

    def test_prune_noise_snippets_removes_sec_exhibit_page(self) -> None:
        snippets = rank_signal_snippets(
            [
                "Subject to the terms and conditions of this Agreement, the Total Commitments may be utilized "
                "in addition to the Loans provided for in Section 2.1."
            ]
        )
        pruned = prune_noise_snippets(
            item={
                "title": "Ares Management 10-K FY2024 (SEC Filing)",
                "loaded_url": "https://www.sec.gov/Archives/edgar/data/1176948/000104746914004247/a2219854zex-10_10.htm",
                "document_type": "annual_report",
            },
            signal_snippets=snippets,
        )
        self.assertEqual(pruned, [])

    def test_shortlist_excludes_quote_page_even_with_signal_mentions(self) -> None:
        records = [
            {
                "firm_id": "FIRM-200",
                "firm_name": "Quote Page Co.",
                "ticker": "QPC",
                "utility_score": 24,
                "text_length": 1600,
                "signal_mentions": {
                    "aum": 1,
                    "feaum": 0,
                    "fre": 0,
                    "fundraising": 1,
                    "margin": 0,
                    "deployment": 0,
                    "realizations": 0,
                    "carry": 0,
                    "perpetual_capital": 0,
                    "credit": 0,
                    "insurance": 0,
                    "wealth": 0,
                },
                "noise_flags": {
                    "is_empty": False,
                    "is_short": False,
                    "is_xbrl_reference_noise": False,
                    "is_market_noise": False,
                    "is_sec_index_page": False,
                    "is_symbol_hub": True,
                    "is_quote_page": True,
                    "is_press_release_search_page": False,
                    "is_sec_exhibit_page": False,
                    "is_low_signal": False,
                },
                "include_in_vda_shortlist": False,
                "shortlist_bucket": "discard",
                "shortlist_rank": None,
            }
        ]
        assign_shortlists(records)
        self.assertFalse(records[0]["include_in_vda_shortlist"])
        self.assertEqual(records[0]["shortlist_bucket"], "discard")

    def test_shortlist_prefers_direct_filing_over_sec_filings_hub(self) -> None:
        records = [
            {
                "firm_id": "FIRM-300",
                "firm_name": "Hub Co.",
                "ticker": "HUB",
                "utility_score": 120,
                "text_length": 4000,
                "signal_mentions": {
                    "aum": 3,
                    "feaum": 0,
                    "fre": 0,
                    "fundraising": 0,
                    "margin": 0,
                    "deployment": 0,
                    "realizations": 0,
                    "carry": 0,
                    "perpetual_capital": 0,
                    "credit": 2,
                    "insurance": 0,
                    "wealth": 0,
                },
                "noise_flags": {
                    "is_empty": False,
                    "is_low_signal": False,
                    "is_quote_page": False,
                    "is_press_release_search_page": False,
                    "is_sec_exhibit_page": False,
                    "is_sec_filings_hub": True,
                },
                "include_in_vda_shortlist": False,
                "shortlist_bucket": "discard",
                "shortlist_rank": None,
            },
            {
                "firm_id": "FIRM-300",
                "firm_name": "Hub Co.",
                "ticker": "HUB",
                "utility_score": 90,
                "text_length": 8000,
                "signal_mentions": {
                    "aum": 4,
                    "feaum": 1,
                    "fre": 1,
                    "fundraising": 1,
                    "margin": 0,
                    "deployment": 0,
                    "realizations": 0,
                    "carry": 0,
                    "perpetual_capital": 0,
                    "credit": 1,
                    "insurance": 0,
                    "wealth": 0,
                },
                "noise_flags": {
                    "is_empty": False,
                    "is_low_signal": False,
                    "is_quote_page": False,
                    "is_press_release_search_page": False,
                    "is_sec_exhibit_page": False,
                    "is_sec_filings_hub": False,
                },
                "include_in_vda_shortlist": False,
                "shortlist_bucket": "discard",
                "shortlist_rank": None,
            },
        ]
        assign_shortlists(records)
        self.assertFalse(records[0]["include_in_vda_shortlist"])
        self.assertTrue(records[1]["include_in_vda_shortlist"])


if __name__ == "__main__":
    unittest.main()
