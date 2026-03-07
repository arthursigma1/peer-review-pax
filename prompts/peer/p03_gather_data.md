# Stage P1 — Peer Data Gathering

## Objective

Extract quantitative and qualitative data for {COMPANY} ({TICKER}) and each identified peer across all defined metrics (MET-*). Build the raw data foundation for standardization and comparative analysis in subsequent pipeline stages.

## Inputs

- Peer group: `data/processed/{ticker}/peer_p0_identification.json`
- Metric definitions: `data/processed/{ticker}/peer_p0_metrics.json`
- Source catalog: `data/processed/{ticker}/peer_p0_sources.md`
- This prompt template

## Method

### Step 1: Source Retrieval

For each company (target + peers):

1. Retrieve source documents listed in the PS-* catalog.
2. Save raw text to `data/raw/{ticker}/` using the following naming convention:
   - Target company: `pax_peer_PS-NNN.txt`
   - Peers: `peer_{peer_ticker}_PS-NNN.txt`
3. Record retrieval date and confirm file integrity before proceeding to extraction.

### Step 2: Data Extraction

For each company × metric combination identified in the coverage matrix:

1. Search source documents for metric data points.
2. Extract the following fields for each data point:
   - `value` — numeric figure as reported
   - `period` — fiscal year or quarter (e.g., FY2025, Q3 FY2025)
   - `period_end_date` — calendar date of period end (YYYY-MM-DD)
   - `currency` — currency after any conversion applied
   - `currency_original` — currency as reported in source
   - `source_id` — PS-NNN reference
   - `source_location` — specific page, table, or section
3. Record confidence level based on source directness:

| Confidence | Definition |
|------------|------------|
| `high` | Directly reported figure from regulatory filing or official presentation |
| `medium` | Calculated from two or more reported figures |
| `low` | Estimated from partial data, third-party sources, or cross-currency approximation |

### Step 3: Multi-Period Collection

Where available, collect data for the following periods for each company × metric:

- Most recent full fiscal year (primary period)
- Prior full fiscal year (required for YoY growth calculations)
- Most recent quarter (for timeliness assessment)

Document any gaps where prior-year data is unavailable or restated.

### Step 4: Data Quality Flags

Flag each data point where one or more of the following conditions apply:

| Flag | Condition |
|------|-----------|
| `secondary-source` | Data sourced from a third party, not the company's own filing |
| `definition-variance` | Metric definition may differ from the standard MET-* definition |
| `currency-converted` | Currency conversion was applied; state the rate and date used |
| `fiscal-year-mismatch` | Company's fiscal year does not align with calendar year; approximation applied |
| `restated` | Source data was subject to a restatement; clarify which version is used |

## Output Format

JSON file `data/processed/{ticker}/peer_p1_data.json`:

```json
{
  "metadata": {
    "stage": "P1",
    "company": "{COMPANY}",
    "ticker": "{TICKER}",
    "analysis_date": "YYYY-MM-DD",
    "peers_covered": ["PEER-001", "PEER-002"],
    "metrics_attempted": 18,
    "data_points_collected": 150,
    "coverage_rate": 0.85
  },
  "data_points": [
    {
      "id": "BENCH-001",
      "company_id": "PEER-001",
      "metric_id": "MET-001",
      "value": 150.5,
      "unit": "USD billions",
      "period": "FY2025",
      "period_end_date": "2025-12-31",
      "currency": "USD",
      "currency_original": "USD",
      "source_id": "PS-001",
      "source_bias": "regulatory-filing",
      "source_location": "10-K p.45, AUM table",
      "confidence": "high",
      "quality_flags": [],
      "notes": ""
    }
  ],
  "coverage_matrix": {
    "MET-001": {"{TICKER}": true, "PEER-001": true, "PEER-002": true},
    "MET-002": {"{TICKER}": true, "PEER-001": false, "PEER-002": true}
  }
}
```

## Limitations

- Data availability varies significantly across companies; some metric × company combinations will have no extractable data.
- Fiscal year-end dates differ across peers (December, March, June), complicating period alignment for YoY comparisons.
- Some metrics (IRR, MOIC) are selectively disclosed and may only be available for a subset of peers.
- Currency differences require conversion, introducing exchange rate sensitivity that should be documented.
- Historical data may be restated or reclassified; always use the most recently published version and flag the discrepancy.

## Bias Awareness

This stage is the primary point at which raw data enters the pipeline; biases introduced here propagate to all downstream analysis. Mitigations:

1. **Selective disclosure**: Companies report metrics that make their performance appear favorable — do not treat the presence of a metric in a company's filing as evidence that the metric is representative; note when disclosure appears selective.
2. **Source hierarchy**: Regulatory filings are most reliable; press releases are least — confidence levels must reflect this hierarchy.
3. **Definitional variance**: The same metric name may carry different calculations across firms — record the source definition verbatim alongside the extracted value, and flag `definition-variance` where differences are material.
4. **Coverage asymmetry**: More data is available for larger, US-listed peers — do not impute or estimate missing data points without flagging `low` confidence and documenting the estimation method.
5. **Point-in-time snapshot**: Market-dependent metrics (AUM, valuation multiples) fluctuate materially — record the exact date of the observation and caution against drawing trend conclusions from a single period.
