# Crawl VDA Summary

Run: `data/processed/pax/2026-03-09-run2`
Generated from: `2-data/crawl_vda_dataset.json` and `2-data/crawl_vda_firm_summary.json`

## Snapshot

- `113` crawl-derived source records
- `16` firms
- `53` shortlisted records
- `0` shortlist for Blue Owl and Victory Capital

## Per-Firm Coverage

| Firm | Shortlisted | Core Gaps | Best Source |
|------|-------------|-----------|-------------|
| Apollo Global Management | 6/10 | - | `apo-20251231` |
| Ares Management | 6/8 | `feaum` | `ares-20241231` |
| Ashmore Group | 4/5 | `feaum` | `Ashmore Group Annual Report FY2025` |
| Blackstone | 1/10 | `feaum`, `fundraising` | `Blackstone IR SEC Filings Page` |
| Blue Owl Capital | 0/4 | `aum`, `feaum`, `fre`, `fundraising`, `margin` | no usable shortlist |
| Brookfield Asset Management | 6/11 | - | `Brookfield Corporation Annual Reports Page` |
| EQT | 3/6 | `fre` | `EQT AB (publ) Year-end Report 2025` |
| Hamilton Lane | 1/3 | - | `Hamilton Lane Annual Report FY2025 (SEC PDF)` |
| Industry-wide | 6/12 | `feaum`, `fre` | `Private Equity Outlook 2026: Gaining Traction \| Bain & Company` |
| Intermediate Capital Group | 6/6 | - | `ICG Annual Report FY2025` |
| KKR | 2/9 | `feaum`, `fre`, `margin` | `KKR IR SEC Filings Page` |
| Partners Group | 4/6 | `fre` | `Partners Group Interim Report H1 2025` |
| StepStone Group | 4/5 | `feaum`, `fundraising` | `EX-10.1` |
| TPG | 2/9 | - | `tpg-20241231` |
| The Carlyle Group | 2/6 | - | `Carlyle Group 10-K FY2025 (SEC PDF)` |
| Victory Capital | 0/3 | `aum`, `feaum`, `fre`, `fundraising`, `margin` | no usable shortlist |

## Best Evidence

### Apollo

- Best source: `apo-20251231`
- Signals: `aum`, `fre`, `credit`
- Evidence: "Assets Under Management, or AUM ... capital commitments ... gross assets plus capital commitments ..."

### Ares

- Best source: `ares-20241231`
- Signals: `credit`, `carry`
- Evidence: "Primarily from five direct lending funds ... $36.2 billion of IGAUM generating returns in excess of their hurdle rates ..."

### Brookfield

- Best source: `Brookfield Corporation Annual Reports Page`
- Signals: `fre`, `deployment`, `wealth`
- Evidence: "The margin on our fee-related earnings was 57% in the current period ..."

### ICG

- Best source: `ICG Annual Report FY2025`
- Signals: `aum`, `fundraising`, `credit`
- Evidence: "At 31 March 2025, AUM stood at $112bn and fee-earning AUM at $75bn ..."

### Carlyle

- Best source: `Carlyle Group 10-K FY2025 (SEC PDF)`
- Signals: `aum`, `carry`
- Evidence: "As of December 31, 2025, our total AUM and Fee-earning AUM included $115.4 billion and $110.9 billion ..."

## Watchlist

- Blackstone has one very strong filing result, but breadth is still thin.
- KKR improved, but evidence is still weak on fee-earning AUM, FRE, and margin.
- Blue Owl and Victory Capital should be treated as targeted backfill cases, not as firms with usable coverage.

## Where To Inspect

- Full dataset: `2-data/crawl_vda_dataset.json`
- Firm summary: `2-data/crawl_vda_firm_summary.json`
- Table view: `2-data/crawl_vda_sources.csv`
- Process audit: `6-review/source_coverage_audit.md`
