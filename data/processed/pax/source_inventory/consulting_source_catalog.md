# Consulting Sources

Base session: `2026-03-09-run2`

Separate consulting catalog:
- `/Users/arthurhrk/Documents/GitHub/peer-review-pax/data/processed/pax/source_inventory/consulting_source_catalog.json`

Combined catalog ready for Crawlee:
- `/Users/arthurhrk/Documents/GitHub/peer-review-pax/data/processed/pax/2026-03-09-run2/1-universe/source_catalog_with_consulting.json`

Catalog counts:
- `15` consulting sources in the separate catalog
- `83` sources in the combined catalog
- `13` net-new sources beyond the base run

Added consulting sources beyond the base run:
- `PS-VD-902` | Bain | `Private Equity Outlook 2026: Gaining Traction`
- `PS-VD-903` | Bain | `Private Equity's Reality Check: The GP Outlook for 2026`
- `PS-VD-905` | McKinsey | `Winning in alternatives: The asset manager's guide to raising capital in wealth`
- `PS-VD-906` | BCG | `Global Asset Management Industry Hit New Record High in 2024 and a Critical Turning Point`
- `PS-VD-907` | BCG | `Capturing Wealth Management's $3 Trillion Private Market Opportunity`
- `PS-VD-908` | Deloitte / Casey Quirk | `Asset Managers Pivot to Private Markets: Casey Quirk Results`
- `PS-VD-909` | PwC | `PwC's 2026 Private Capital Outlook`
- `PS-VD-910` | PwC | `Insights on capturing the retail alternatives market`
- `PS-VD-911` | Mercer | `Private Markets in Motion`
- `PS-VD-912` | Mercer | `The State of Alternative Investments in Wealth Management 2025`
- `PS-VD-913` | Cerulli | `Private Markets Investments Provide Advisors with Practice Differentiation, High Net Worth Client Asset Gathering and Retention Opportunities`
- `PS-VD-914` | Oliver Wyman | `Competing For Growth`
- `PS-VD-915` | Oliver Wyman | `Mergers & Acquisitions Trends In Wealth And Asset Management`

Already present in the base run and therefore de-duplicated in the combined catalog:
- `PS-VD-901` | Bain | `Global Private Equity Report 2026`
- `PS-VD-904` | McKinsey | `Global Private Markets Report 2026`

Suggested crawl command:

```bash
cd /Users/arthurhrk/Documents/GitHub/peer-review-pax
source .venv/bin/activate
python -m src.ingestion.crawlee_vda \
  --catalog data/processed/pax/2026-03-09-run2/1-universe/source_catalog_with_consulting.json \
  --output-dir data/processed/pax/2026-03-09-run2/1-universe/crawl-with-consulting \
  --raw-dir data/raw/pax/crawled/2026-03-09-run2-with-consulting \
  --max-links-per-page 2 \
  --max-requests 280
```
