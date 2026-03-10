import unittest
from pathlib import Path

from src.ingestion.source_catalog import (
    SourceRecord,
    discover_catalog_files,
    find_latest_catalog_file,
    load_sources,
)


class SourceCatalogTest(unittest.TestCase):
    def setUp(self) -> None:
        self.processed_root = Path("data/processed/pax")

    def test_find_latest_catalog_file(self) -> None:
        latest = find_latest_catalog_file(self.processed_root)
        self.assertIsNotNone(latest)
        self.assertTrue(str(latest).endswith("2026-03-09-run2/1-universe/source_catalog.json"))

    def test_discover_catalog_files_includes_legacy_markdown(self) -> None:
        catalogs = discover_catalog_files(self.processed_root)
        self.assertIn(self.processed_root / "stage_0_sources.md", catalogs)
        self.assertIn(self.processed_root / "peer_p0_sources.md", catalogs)

    def test_load_sources_from_latest_catalog(self) -> None:
        sources = load_sources(self.processed_root, latest_only=True)
        self.assertGreater(len(sources), 50)
        self.assertTrue(all(isinstance(source, SourceRecord) for source in sources))
        self.assertTrue(all(source.url.startswith("http") for source in sources))

    def test_load_sources_from_legacy_markdown(self) -> None:
        sources = load_sources(self.processed_root, latest_only=False)
        ids = {source.source_id for source in sources}
        self.assertIn("S-001", ids)
        self.assertIn("PS-006", ids)


if __name__ == "__main__":
    unittest.main()
