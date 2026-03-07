# Stage P0b — Industry Metrics Definition

## Objective

Define a comprehensive set of 15-20 industry-specific metrics for benchmarking {COMPANY} ({TICKER}) against its peer group in alternative asset management. Metrics must cover multiple dimensions of business performance and be measurable using publicly available data.

## Inputs

- Company identity: {COMPANY} ({TICKER})
- Industry: Alternative asset management
- Peer group: `data/processed/{ticker}/peer_p0_identification.json`

## Method

### Step 1: Metric Category Framework

Define metrics across 8 categories:

**A. Scale Metrics**
- Total AUM (Assets Under Management)
- Fee-Earning AUM (FEAUM)
- Total fundraising (trailing 12 months)

**B. Profitability Metrics**
- Fee-Related Earnings (FRE)
- FRE Margin (FRE / Management Fees)
- Distributable Earnings (DE)
- DE per share

**C. Growth Metrics**
- AUM growth (YoY %)
- Revenue growth (YoY %)
- FRE growth (YoY %)

**D. Fee Quality Metrics**
- Management fee rate (management fees / average AUM)
- Performance/incentive fee share (% of total revenue)
- Fee-related revenue stability (mgmt fees / total fees)

**E. Capital Deployment Metrics**
- Dry powder ratio (uninvested capital / AUM)
- Deployment pace (capital deployed / dry powder, TTM)

**F. Fundraising Metrics**
- Capital raised (TTM)
- Fund size progression (latest flagship vs prior vintage)
- Fundraising yield (capital raised / AUM)

**G. Returns Metrics (where publicly available)**
- Net IRR (flagship strategies)
- MOIC (flagship strategies)

**H. Valuation Metrics**
- P/DE (Price / Distributable Earnings)
- P/FRE (Price / Fee-Related Earnings)
- EV/FEAUM (Enterprise Value / Fee-Earning AUM)

### Step 2: Metric Definition

For each metric, specify:

| Field | Description |
|-------|-------------|
| `id` | Unique identifier: `MET-001`, `MET-002`, etc. |
| `name` | Short descriptive name |
| `category` | One of the 8 categories above |
| `unit` | Unit of measurement (e.g., USD billions, %, x) |
| `definition` | Precise plain-English definition |
| `calculation` | Exact formula referencing line items |
| `data_sources` | Which filing sections or source types supply this metric |
| `relevance` | Why this metric matters for competitive positioning |
| `comparability_issues` | Known cross-firm differences (IFRS vs GAAP, fiscal year, AUM definition) |
| `priority` | `high` \| `medium` \| `low` |

### Step 3: Prioritization

Rank metrics by the following criteria, in order:

1. **Data availability** across the peer group — metrics unavailable for more than half the peers are deprioritized.
2. **Analytical value** for competitive positioning — metrics that distinguish business model quality over scale receive higher weight.
3. **Comparability** — metrics requiring minimal cross-firm adjustment receive higher priority than those heavily sensitive to definitional differences.

## Output Format

JSON file `data/processed/{ticker}/peer_p0_metrics.json`:

```json
{
  "metadata": {
    "stage": "P0b",
    "company": "{COMPANY}",
    "ticker": "{TICKER}",
    "analysis_date": "YYYY-MM-DD",
    "total_metrics_defined": 18
  },
  "metrics": [
    {
      "id": "MET-001",
      "name": "Total AUM",
      "category": "Scale",
      "unit": "USD billions",
      "definition": "Total assets under management including...",
      "calculation": "Sum of all fund AUM + co-investment vehicles",
      "data_sources": ["20-F/10-K business overview", "earnings presentations"],
      "relevance": "Primary scale indicator for alternative asset managers",
      "comparability_issues": "AUM definitions vary; some include advisory assets, others do not",
      "priority": "high"
    }
  ]
}
```

## Limitations

- Some metrics (IRR, MOIC) may not be publicly disclosed by all peers.
- AUM definitions vary across firms — not perfectly standardized.
- Fiscal years differ, requiring TTM approximations for cross-period comparison.
- IFRS vs GAAP can affect FRE and DE calculations in material ways.
- Valuation metrics are market-dependent and should be treated as point-in-time estimates.

## Bias Awareness

This stage is susceptible to selection bias in which metrics are defined and prioritized. Mitigations:

1. **Metric selection bias**: Define metrics across all 8 categories before applying the prioritization filter; avoid building the framework around metrics that favor {COMPANY}'s business model.
2. **Availability bias**: Metrics are constrained by what is publicly disclosed — acknowledge that selectively disclosed metrics (IRR, fund returns) may systematically favor firms with better performance.
3. **Definitional variance**: Flag every metric where the same name may mean different things across firms; do not assume standardization.
4. **Recency bias**: Current-period metrics may not represent normalized performance; where possible include multi-year averages alongside point-in-time figures.
