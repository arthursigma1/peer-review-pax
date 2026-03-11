# Source Coverage Audit

Analysis date: 2026-03-09
Run audited: `data/processed/pax/2026-03-09-run2`

## 1. Crawl VDA Summary

- Crawl-derived VDA dataset: `113` source records across `16` firms.
- Shortlisted for VDA use: `53` records.
- Firms with strongest coverage after crawl enrichment: Apollo, Ares, Brookfield, ICG, Carlyle.
- Firms still weak after crawl enrichment: Blue Owl (`0` shortlisted), Victory Capital (`0` shortlisted), KKR (missing `feaum`, `fre`, `margin`), Blackstone (missing `feaum`, `fundraising`).

Best current source stacks:

- Apollo: `6/10` shortlisted, no core signal gaps.
- Ares: `6/8` shortlisted, only `feaum` gap.
- Brookfield: `6/11` shortlisted, no core signal gaps.
- ICG: `6/6` shortlisted, no core signal gaps.

Weak current source stacks:

- Blue Owl: `0/4` shortlisted, no usable VDA evidence surfaced from current crawl.
- Victory Capital: `0/3` shortlisted, no usable VDA evidence surfaced from current crawl.
- KKR: `2/9` shortlisted, still light on fee-centric evidence.
- Blackstone: `1/10` shortlisted, strong filing evidence but shallow breadth.

## 2. Did The Best Run Actually Use The Sources?

The current run-level source catalog contains `70` cataloged sources.

Before adding the new crawl-derived VDA dataset:

- Original run outputs cited `41/70` catalog sources.
- `29/70` catalog sources were not propagated into downstream artifacts.

After adding `crawl_vda_dataset.json` and `crawl_vda_firm_summary.json`:

- Referenced coverage rose to `63/70` catalog sources.
- Only `7/70` catalog sources remain unused in outputs.

This means the main issue was not only source discovery. A large part of the issue was propagation of source evidence into downstream artifacts.

Unused in original outputs were concentrated in:

- Industry-wide: `7`
- Ashmore Group: `4`
- Carlyle Group: `4`
- Victory Capital: `4`
- Intermediate Capital Group: `3`
- Hamilton Lane: `2`
- Brookfield Corporation: `1`
- EQT: `1`
- Partners Group: `1`
- TPG: `1`
- Blue Owl Capital: `1`

## 3. Cross-Run Catalog Overlap

Structured source catalogs compared:

- `2026-03-07`: `71` sources, `69` unique URLs
- `2026-03-07-run2`: `65` sources, `63` unique URLs
- `2026-03-08-run2`: `65` sources, `63` unique URLs
- `2026-03-09-run2`: `70` sources, `67` unique URLs

Comparing `2026-03-09-run2` against the union of older structured catalogs:

- Latest unique URLs: `67`
- Older unique URLs: `69`
- Overlap: `52`
- Latest-only: `15`
- Older-only: `17`

Important nuance:

- Older-only does not always mean missing evidence.
- Some older URLs are just older seed entry points for documents now reached through smarter hub pages.
- Blindly merging all historical source URLs would create duplication and low-yield reruns.

## 4. Historical URLs Still Not Covered By The Latest Crawl

After checking older-only URLs against the latest crawl outputs, `15` historical URLs remain truly uncovered by the `2026-03-09-run2` crawl.

Highest-value uncovered candidates:

- Brookfield 2024 10-K direct PDF (`PS-VD-017`)
- Blue Owl Q3 2025 10-Q (`PS-VD-020`)
- Carlyle Q3 2025 results (`PS-VD-057`)
- EQT Q3 2025 announcement (`PS-VD-058`)
- Partners Group corporate governance report 2024 (`PS-VD-059`)
- Ares Q1 2025 10-Q (`PS-VD-060`)
- KKR Q2 2025 10-Q (`PS-VD-064`)

Special-case uncovered candidates:

- Patria-only sources (`PS-VD-066` through `PS-VD-071`) are absent from the latest peer crawl because the latest run focused on peers, not the target itself.

Low-confidence or suspect historical entries:

- StepStone `PS-VD-035` points to a Hamilton Lane URL and should be treated as catalog hygiene debt, not a crawl gap.

## 5. Recommendation

Yes: consolidate the sources.

No: do not rerun everything from every historical run.

Recommended operating model:

1. Build a canonical source registry across runs.
   Store one normalized record per URL with provenance: `source_id`, firm, first_seen_run, seen_in_runs, catalog_paths, bias tag, document type.

2. Keep `2026-03-09-run2` as the base crawl universe.
   It is the best structured starting point and already covers most of the useful peer evidence.

3. Add a targeted backfill queue from historical runs.
   Prioritize uncovered quarterly filings and direct documents, not hub pages.

4. Separate registry from crawl cache.
   A source registry answers "what exists"; a crawl cache answers "what text have we already extracted." They should not be the same artifact.

5. Rerun only where the latest VDA dataset is weak.
   First priority firms: Blue Owl, Victory Capital, KKR, Blackstone.
   Second priority firms: Ares for `feaum`; StepStone for fundraising; Partners Group for `fre`.

## 6. Practical Next Step

Best next move:

- Create a master source registry under `data/processed/pax/`.
- Seed it with all structured catalogs plus the legacy markdown catalogs.
- Mark each source as one of:
  - `covered_by_latest_crawl`
  - `uncovered_high_value`
  - `duplicate_entry_point`
  - `catalog_hygiene_issue`
- Then generate a small targeted crawl input from only `uncovered_high_value` records.

If the goal is to improve the current run rather than rebuild the process, the shortest path is:

- keep `2026-03-09-run2` as the base;
- backfill the `7` high-value uncovered peer URLs listed above;
- rerun only those firms with weak VDA shortlist coverage.
