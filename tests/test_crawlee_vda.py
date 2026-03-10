import unittest

from bs4 import BeautifulSoup

from src.ingestion.crawlee_vda import (
    _collect_relevant_snippets,
    _extract_feed_blocks,
    _harvest_document_links,
    _parse_eqs_config_chunk,
    _parse_q4_sec_config,
    _score_sec_filing_candidate,
    _score_text_block,
)
from src.ingestion.source_catalog import SourceRecord


class CrawleeVdaHeuristicsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.source = SourceRecord(
            source_id="PS-VD-001",
            firm="Blackstone",
            title="Blackstone SEC Filings",
            date="2025-12-31",
            document_type="annual_report",
            bias_tag="regulatory-filing",
            url="https://ir.blackstone.com/sec-filings/default.aspx",
            notes="",
            catalog_path="data/processed/pax/2026-03-09-run2/1-universe/source_catalog.json",
        )

    def test_financial_snippet_beats_menu_noise(self) -> None:
        blocks = [
            "The Firm Menu Column Our Clients Institutional Investors Financial Advisors Family Offices Insurance",
            "Distributable earnings (DE) were $2.2 billion in Q4 2025 and fee-related earnings margin expanded 20%.",
            "Stock Information Overview Dividends Analyst Coverage FAQ",
        ]
        snippets = _collect_relevant_snippets(blocks, limit=2)
        self.assertEqual(
            snippets[0],
            "Distributable earnings (DE) were $2.2 billion in Q4 2025 and fee-related earnings margin expanded 20%.",
        )

    def test_menu_block_scores_below_financial_block(self) -> None:
        menu_score = _score_text_block(
            "The Firm Menu Column Our Clients Institutional Investors Financial Advisors Family Offices Insurance"
        )
        financial_score = _score_text_block(
            "AUM reached $52.6 billion, FRE rose 19%, and fundraising totaled $7.7 billion in FY2025."
        )
        self.assertLess(menu_score, financial_score)

    def test_document_link_harvest_uses_table_context(self) -> None:
        soup = BeautifulSoup(
            """
            <html><body>
              <table>
                <tr>
                  <td>02/27/2026</td>
                  <td>10-K</td>
                  <td>Annual report with fee-related earnings and AUM discussion</td>
                  <td><a href="/docs/blackstone-10k-2026.html">View filing</a></td>
                </tr>
              </table>
            </body></html>
            """,
            "lxml",
        )
        blocks, links = _harvest_document_links(
            soup=soup,
            base_url="https://ir.blackstone.com/sec-filings/default.aspx",
            seed_source=self.source,
            limit=3,
        )
        self.assertEqual(links[0], "https://ir.blackstone.com/docs/blackstone-10k-2026.html")
        self.assertIn("Annual report", blocks[0])

    def test_atom_feed_entries_become_blocks_and_links(self) -> None:
        soup = BeautifulSoup(
            """
            <feed>
              <entry>
                <title>10-K - Annual report</title>
                <updated>2026-02-27T16:00:00-05:00</updated>
                <summary>Blackstone filed its annual report with updated AUM disclosures.</summary>
                <link href="https://www.sec.gov/Archives/edgar/data/example/index.htm" />
              </entry>
            </feed>
            """,
            "xml",
        )
        blocks, links = _extract_feed_blocks(soup=soup, base_url="https://www.sec.gov/feed")
        self.assertIn("10-K - Annual report", blocks[0])
        self.assertEqual(links[0], "https://www.sec.gov/Archives/edgar/data/example/index.htm")

    def test_parse_q4_sec_config(self) -> None:
        config = _parse_q4_sec_config(
            """
            <script>
            var Q4ApiKey = 'API-KEY-123';
            $('.module-sec--widget').sec({
                apiKey: Q4ApiKey,
                exchange: 'CIK',
                symbol: '0001393818',
                excludeNoDocuments: true
            });
            </script>
            """
        )
        self.assertEqual(
            config,
            {
                "api_key": "API-KEY-123",
                "exchange": "CIK",
                "symbol": "0001393818",
            },
        )

    def test_parse_eqs_config_chunk(self) -> None:
        config = _parse_eqs_config_chunk(
            'const a="https://tools.cms-eqs.com",E="fcf5b4",r="AbCd1234EfGh5678IjKl9012MnOp3456",R="81b388fe59ae7a7d96801e604f0eb6ace797726e";'
            'export{E as a,a as b,r as q,R as r};'
        )
        self.assertEqual(
            config,
            {
                "api_base": "https://tools.cms-eqs.com",
                "site_id": "fcf5b4",
                "key": "81b388fe59ae7a7d96801e604f0eb6ace797726e",
                "secret": "AbCd1234EfGh5678IjKl9012MnOp3456",
            },
        )

    def test_10k_scores_above_form4(self) -> None:
        self.assertGreater(
            _score_sec_filing_candidate(
                form_type="10-K",
                description="Annual report with AUM and fee-related earnings detail",
            ),
            _score_sec_filing_candidate(
                form_type="4",
                description="Statement of changes in beneficial ownership",
            ),
        )


if __name__ == "__main__":
    unittest.main()
