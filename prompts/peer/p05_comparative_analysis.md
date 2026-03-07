# Stage P3 — Comparative Performance Analysis

## Objective

Perform systematic quantitative benchmarking of {COMPANY} ({TICKER}) against its peer group across all standardized metrics. Produce rankings, percentile positions, trend analysis, and an overall assessment of competitive positioning within the alternative asset management industry.

## Inputs

- Standardized data: `data/processed/{ticker}/peer_p2_standardized.json`
- Metric definitions: `data/processed/{ticker}/peer_p0_metrics.json`
- Peer group: `data/processed/{ticker}/peer_p0_identification.json`

## Method

### Step 1: Per-Metric Rankings

For each metric with sufficient coverage (>= 4 peers):

1. Rank all companies (1 = best performer)
2. Calculate: {COMPANY}'s rank, peer group median, mean, min, max
3. Calculate {COMPANY} vs median (% above or below)
4. Assign RANK-NNN identifier to each ranking entry

Note: "best" depends on metric — for profitability metrics, higher is better; for leverage metrics, lower may be better. Define directionality per metric in the output, referencing the `direction` field from the metric definition.

**Evidence required:** Reference specific BENCH-* standardized data points and MET-* definitions for every ranking entry.

### Step 2: Percentile Analysis

For each metric:

- Calculate {COMPANY}'s percentile position within the peer group
- Classify position using the following thresholds:

| Classification | Percentile Range | Interpretation |
|----------------|-----------------|----------------|
| **Leader** | >= 75th percentile | Top quartile performance within peer group |
| **Above Average** | 50th–74th percentile | Second quartile; outperforms the median |
| **Below Average** | 25th–49th percentile | Third quartile; underperforms the median |
| **Laggard** | < 25th percentile | Bottom quartile; materially below the peer group |

**Evidence required:** Document the full ranked array used to derive each percentile calculation.

### Step 3: Trend Analysis

Where multi-period data exists:

- Calculate YoY change for {COMPANY} and each peer
- Compare {COMPANY}'s trajectory vs peer median trajectory
- Identify convergence (improving vs peers) or divergence (falling behind)
- Flag metrics where {COMPANY}'s trend diverges significantly from peer group

**Evidence required:** Reference the specific BENCH-* data points used for each period in the trend calculation, noting any alignment method differences between periods.

### Step 4: Category-Level Assessment

Aggregate findings by metric category (Scale, Profitability, Growth, Fee Quality, Capital Deployment, Fundraising, Returns, Valuation):

- Count of Leader / Above Average / Below Average / Laggard positions per category
- Category-level competitive assessment in 1-2 sentences
- Identify patterns: consistently strong or consistently weak categories
- Flag categories where data coverage is insufficient for reliable assessment

### Step 5: Overall Competitive Positioning

Synthesize per-metric and per-category findings:

- Top 3 competitive strengths: metrics or categories where {COMPANY} consistently leads
- Top 3 competitive weaknesses: metrics or categories where {COMPANY} consistently lags
- Key differentiators: what makes {COMPANY} quantitatively distinct from the peer group
- Overall positioning assessment using the four-tier classification (Leader / Above Average / Below Average / Laggard) at the aggregate level

## Output Format

JSON file `data/processed/{ticker}/peer_p3_comparison.json`:

```json
{
  "metadata": {
    "stage": "P3",
    "company": "{COMPANY}",
    "analysis_date": "YYYY-MM-DD",
    "peers_analyzed": 6,
    "metrics_analyzed": 16
  },
  "rankings": [
    {
      "id": "RANK-001",
      "metric_id": "MET-001",
      "metric_name": "Total AUM",
      "direction": "higher_is_better",
      "rankings": [
        {"company": "PEER-001", "value": 500.0, "rank": 1},
        {"company": "PEER-003", "value": 200.0, "rank": 2},
        {"company": "{TICKER}", "value": 30.0, "rank": 5}
      ],
      "target_rank": 5,
      "target_percentile": 28,
      "target_position": "Below Average",
      "peer_median": 150.0,
      "target_vs_median_pct": -80.0,
      "peer_mean": 180.0,
      "peer_min": 20.0,
      "peer_max": 500.0,
      "outlier_flags": [],
      "coverage_note": "..."
    }
  ],
  "trends": [
    {
      "metric_id": "MET-001",
      "target_yoy_change_pct": 15.0,
      "peer_median_yoy_change_pct": 10.0,
      "trajectory": "converging",
      "significance": "positive — growing faster than peers"
    }
  ],
  "category_summary": {
    "Scale": {
      "metrics_count": 3,
      "leader": 0,
      "above_average": 1,
      "below_average": 1,
      "laggard": 1,
      "assessment": "Below peers on absolute scale, competitive on growth"
    }
  },
  "competitive_positioning": {
    "strengths": ["..."],
    "weaknesses": ["..."],
    "differentiators": ["..."],
    "overall_classification": "Below Average",
    "overall_assessment": "..."
  }
}
```

## Limitations

- Rankings among small peer groups (5-7 companies) have limited statistical significance; percentile positions are approximate and sensitive to individual outliers.
- Trend analysis requires multi-period data, which may not be available for all metrics and peers; where trend data is missing, this must be flagged rather than inferred.
- "Best" direction for some metrics is context-dependent (e.g., dry powder may be desirable as a sign of fundraising strength or undesirable as a sign of deployment difficulty); directionality assumptions must be documented.
- Percentile calculations with fewer than 6 data points should be interpreted with caution.

## Bias Awareness

1. **Scale bias**: absolute metrics (AUM, revenue) naturally favor larger peers; ensure per-company and category-level assessments distinguish absolute scale from quality or efficiency metrics.
2. **Metric weighting**: treating all metrics equally in the category-level aggregation may not reflect their relative importance to competitive positioning; note where a single dominant metric drives the category assessment.
3. **Point-in-time snapshot**: rankings can shift significantly quarter to quarter; flag metrics where known seasonality or recent events may make the current period unrepresentative.
4. **Survivor bias**: the peer group includes only current public companies, excluding firms that were acquired, went private, or failed — this may create an upward bias in peer group benchmarks.
5. **Definition sensitivity**: small definitional differences inherited from Stage P2 can move rankings in a small peer group; the outlier_flags field in each ranking entry must carry forward any quality flags from standardized data.
