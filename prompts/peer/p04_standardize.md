# Stage P2 — Data Standardization

## Objective

Normalize all collected data points (BENCH-*) for comparability across {COMPANY} ({TICKER}) and its peer group. Address currency differences, fiscal year misalignment, and accounting standard variations to produce a standardized dataset suitable for quantitative comparison.

## Inputs

- Raw data: `data/processed/{ticker}/peer_p1_data.json`
- Metric definitions: `data/processed/{ticker}/peer_p0_metrics.json`
- Peer group: `data/processed/{ticker}/peer_p0_identification.json`

## Method

### Step 1: Currency Normalization

- Convert all monetary values to USD
- Use period-end exchange rates from public sources (ECB, Federal Reserve)
- Record original currency and conversion rate for audit trail
- Flag entries where currency conversion may materially affect comparability

### Step 2: Fiscal Year Alignment

- Identify fiscal year-end for each company
- For companies with non-December year-ends, calculate TTM (trailing twelve months) or use most recent available annual data
- Document alignment method per company
- Flag where alignment required estimation or interpolation

### Step 3: Accounting Standard Reconciliation

- Identify which companies report under IFRS vs US GAAP
- For key metrics (FRE, DE, revenue recognition), note material differences
- Do NOT adjust figures — instead, annotate the impact of standards differences
- Create a comparability notes section for each affected metric

### Step 4: Data Completeness Assessment

- For each metric: count how many of the peer group have valid data
- Flag metrics with coverage < 4 of 7 peers — these have limited benchmarking value
- Flag individual data points with quality concerns
- Calculate overall coverage rate

### Step 5: Outlier Detection

- For each metric, calculate mean and standard deviation across peer group
- Flag values > 2 standard deviations from mean as potential outliers
- Do NOT remove outliers — annotate for analyst review

## Output Format

JSON file `data/processed/{ticker}/peer_p2_standardized.json`:

```json
{
  "metadata": {
    "stage": "P2",
    "company": "{COMPANY}",
    "analysis_date": "YYYY-MM-DD",
    "normalization_methods": {
      "currency": "Period-end USD conversion",
      "fiscal_year": "TTM alignment where needed",
      "accounting": "Annotated, not adjusted"
    },
    "coverage_summary": {
      "total_metrics": 18,
      "fully_covered": 12,
      "partially_covered": 4,
      "insufficient_coverage": 2
    }
  },
  "standardized_data": [
    {
      "id": "BENCH-001",
      "company_id": "...",
      "metric_id": "MET-001",
      "original_value": 150.5,
      "original_currency": "BRL",
      "standardized_value": 28.3,
      "standardized_currency": "USD",
      "conversion_rate": 5.32,
      "conversion_date": "2025-12-31",
      "period": "FY2025",
      "aligned_period": "CY2025",
      "alignment_method": "fiscal_year_match",
      "accounting_standard": "IFRS",
      "comparability_notes": "...",
      "quality_flags": [],
      "outlier_flag": false
    }
  ],
  "metric_coverage": {
    "MET-001": {
      "companies_with_data": 7,
      "companies_total": 7,
      "coverage_rate": 1.0,
      "sufficient": true,
      "comparability_issues": "..."
    }
  },
  "company_notes": {
    "PAX": {
      "fiscal_year_end": "December 31",
      "accounting_standard": "IFRS",
      "reporting_currency": "USD",
      "alignment_notes": "..."
    }
  }
}
```

## Limitations

- Currency conversion introduces exchange rate sensitivity — results may differ with different rate sources.
- TTM calculations approximate true annual figures for non-December year-end companies.
- IFRS/GAAP differences are annotated but not adjusted, meaning some metrics remain imperfectly comparable.
- Point-in-time exchange rates do not capture intra-period volatility.
- Data completeness assessment depends on the thoroughness of source mapping completed in Stage P0c; gaps in the source catalog propagate directly into coverage rates.

## Bias Awareness

1. **Currency conversion timing**: choice of period-end vs average rate affects results; period-end rates are used here for auditability but may not reflect the economic period being compared.
2. **Alignment method choices**: TTM vs fiscal year may favor companies with strong recent quarters; document the method used per company and flag where the choice materially affects the result.
3. **Annotation vs adjustment**: not adjusting for GAAP/IFRS differences may disadvantage firms using the less favorable standard for a given metric; the annotation-only approach is a deliberate choice to preserve raw data integrity.
4. **Coverage-driven metric selection**: excluding low-coverage metrics in downstream stages may systematically favor larger, better-disclosed firms; flag this pattern explicitly if it emerges.
5. **Outlier retention**: retaining flagged outliers preserves data integrity but risks distorting mean and standard deviation calculations used in downstream ranking — downstream stages must account for outlier flags.
