import argparse
import json
import tempfile
import unittest
from pathlib import Path

from src.analyzer.pax_session_source_inventory import (
    build_inventory,
    discover_sessions,
    extract_source_ids,
    normalize_url,
)


class PaxSessionSourceInventoryTest(unittest.TestCase):
    def test_discover_sessions_filters_non_session_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "2026-03-07").mkdir()
            (root / "2026-03-09-run2").mkdir()
            (root / "source_inventory").mkdir()
            (root / "notes").mkdir()
            sessions = discover_sessions(root)
            self.assertEqual([session.name for session in sessions], ["2026-03-07", "2026-03-09-run2"])

    def test_extract_source_ids_dedupes_and_sorts(self) -> None:
        text = "PS-VD-010 PS-VD-002 PS-VD-010 ignored"
        self.assertEqual(extract_source_ids(text), ["PS-VD-002", "PS-VD-010"])

    def test_normalize_url_removes_scheme_query_and_trailing_slash(self) -> None:
        url = "https://Example.com/path/to/doc/?a=1"
        self.assertEqual(normalize_url(url), "example.com/path/to/doc")

    def test_build_inventory_tracks_baseline_and_historical_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            older = root / "2026-03-07"
            baseline = root / "2026-03-09-run2"
            for session_dir in (older, baseline):
                (session_dir / "1-universe").mkdir(parents=True)
                (session_dir / "2-data").mkdir(parents=True)
                (session_dir / "3-analysis").mkdir(parents=True)
                (session_dir / "4-deep-dives").mkdir(parents=True)
                (session_dir / "5-playbook").mkdir(parents=True)

            (older / "1-universe" / "source_catalog.json").write_text(
                json.dumps(
                    {
                        "sources": [
                            {
                                "source_id": "PS-VD-001",
                                "firm": "Firm A",
                                "title": "Older filing",
                                "date": "2025-01-01",
                                "document_type": "annual_report",
                                "bias_tag": "regulatory-filing",
                                "url_or_reference": "https://example.com/older-filing",
                            },
                            {
                                "source_id": "PS-VD-002",
                                "firm": "Firm B",
                                "title": "Historical only",
                                "date": "2025-02-01",
                                "document_type": "presentation",
                                "bias_tag": "company-produced",
                                "url_or_reference": "https://example.com/historical-only",
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )
            (baseline / "1-universe" / "source_catalog.json").write_text(
                json.dumps(
                    [
                        {
                            "source_id": "PS-VD-001",
                            "firm": "Firm A",
                            "title": "Baseline filing",
                            "date": "2026-01-01",
                            "document_type": "annual_report",
                            "bias_tag": "regulatory-filing",
                            "url": "https://example.com/baseline-filing",
                        },
                        {
                            "source_id": "PS-VD-003",
                            "firm": "Firm C",
                            "title": "Unused baseline source",
                            "date": "2026-01-02",
                            "document_type": "presentation",
                            "bias_tag": "company-produced",
                            "url": "https://example.com/unused-baseline",
                        },
                    ]
                ),
                encoding="utf-8",
            )
            (older / "2-data" / "strategy_profiles.json").write_text(
                '{"source_id": "PS-VD-001", "note": "older usage"}',
                encoding="utf-8",
            )
            (baseline / "2-data" / "strategy_profiles.json").write_text(
                '{"sources": ["PS-VD-001"]}',
                encoding="utf-8",
            )
            (baseline / "2-data" / "crawl_vda_dataset.json").write_text(
                '{"sources": ["PS-VD-003"]}',
                encoding="utf-8",
            )
            (baseline / "1-universe" / "crawl").mkdir(parents=True)
            (baseline / "1-universe" / "crawl" / "crawl_results.json").write_text(
                json.dumps(
                    [
                        {
                            "source_id": "PS-VD-001",
                            "seed_url": "https://example.com/baseline-filing",
                            "loaded_url": "https://example.com/baseline-filing",
                        }
                    ]
                ),
                encoding="utf-8",
            )

            summary = build_inventory(
                argparse.Namespace(
                    processed_root=str(root),
                    baseline_session="2026-03-09-run2",
                    output_dir=str(root / "source_inventory"),
                )
            )

            self.assertEqual(summary["session_count"], 2)

            inventory = json.loads((root / "source_inventory" / "session_source_inventory.json").read_text())
            self.assertEqual(inventory["metadata"]["baseline_session"], "2026-03-09-run2")
            self.assertIn("PS-VD-002", inventory["baseline_diff"]["source_ids_only_in_older_catalogs"])
            self.assertIn("PS-VD-003", inventory["baseline_diff"]["source_ids_in_baseline_catalog_not_used_original"])
            self.assertNotIn("PS-VD-003", inventory["baseline_diff"]["source_ids_in_baseline_catalog_not_used_augmented"])

            by_source = {row["source_id"]: row for row in inventory["sources"]}
            self.assertEqual(by_source["PS-VD-001"]["status_vs_baseline"], "baseline_used")
            self.assertEqual(by_source["PS-VD-003"]["status_vs_baseline"], "baseline_surfaced_by_crawl_vda")
            self.assertEqual(by_source["PS-VD-002"]["status_vs_baseline"], "historical_catalog_only")


if __name__ == "__main__":
    unittest.main()
