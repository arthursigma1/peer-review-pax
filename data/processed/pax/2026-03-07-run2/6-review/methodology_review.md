# Methodology Review

## Summary

The statistical methodology is thorough in its design -- Spearman rank correlation is well-justified, bootstrap confidence intervals are computed, BH FDR correction is applied, and mandatory disclaimers are present verbatim. However, the analysis suffers from three material issues: (1) several firms in the final deep-dive set have zero valuation multiples or zero metric data, making them ineligible for the correlation analysis that justified their inclusion; (2) the "stable value driver" classification is applied to metrics that do not meet the stated criterion (rho > 0.5 across all three multiples), because one or two multiples have insufficient data (N < 10); and (3) the temporal stability analysis is acknowledged as infeasible but this limitation is insufficiently reflected in the confidence classifications, where all four BH-significant findings are presented at "moderate confidence" despite having no temporal validation.

## Critical Issues

### C1. ARES and HLNE have no valuation multiples -- cannot participate in any correlation

`2-data/quantitative_data.json`: ARES (FIRM-005) has an empty `valuation_multiples` object `{}`. HLNE (FIRM-012) has an empty `valuation_multiples` object `{}`. These firms cannot appear in any correlation computation because correlations require paired (driver, multiple) data. Yet ARES is included in the final peer set at `3-analysis/final_peer_set.json` with the rationale "Q1 on DVR-001 (FEAUM $384.9B)" -- a ranking that itself depends on correlations computed without ARES's own valuation data. HLNE is similarly included with "Q1 on DVR-002 (EPS $4.35)." The claimed metric coverage percentages (ARES 58.8%, HLNE 52.9%) do not disclose the absence of multiples, which is a more fundamental gap than missing driver metrics.

**Impact:** These two firms contribute no statistical evidence to the correlation analysis. Their inclusion in the final deep-dive set is not incorrect per se (deep-dives are qualitative), but the Q1 driver rankings cited as inclusion rationale are rankings on driver values, not on correlation strength, and this distinction is not made clear. The reader may misunderstand that ARES and HLNE "drive" the statistical findings when in fact they are absent from them.

### C2. "Stable value driver" classification applied inconsistently with stated criteria

The classification criteria in `3-analysis/correlations.json` metadata state: `"stable_value_driver": "abs(rho) > 0.5 across all three multiples"`. However:

- **EPS (MET-VD-002)** is classified as `stable_value_driver` with P/FRE rho=0.665 (N=13), P/DE rho=0.771 (N=6, classified `insufficient_data`), EV/FEAUM rho=0.750 (N=14, BH-significant). The P/DE multiple has only N=6, falling below the N=10 threshold for reliable classification. The criterion "rho > 0.5 across all three multiples" is not met because P/DE is insufficient_data.

- **Total AUM (MET-VD-005)** is classified as `stable_value_driver` with P/FRE rho=0.690 (N=19, BH-significant), P/DE rho=0.527 (N=10, not BH-significant), EV/FEAUM rho=0.552 (N=18, not BH-significant). Only one of three multiples is BH-significant. Moreover, the partial correlation analysis in `3-analysis/statistical_methodology.md` Section 6 shows that Total AUM's signal collapses to near zero after controlling for FEAUM (partial rho = +0.118 for P/FRE, +0.149 for EV/FEAUM), demonstrating it is a confounded proxy for FEAUM, not an independent driver. The report labels this finding but still classifies Total AUM as a stable value driver in the driver ranking.

**Impact:** The driver ranking in the correlations file and the final peer set selection both treat these as confirmed stable drivers. If EPS's P/DE is insufficient_data and Total AUM is confounded, the number of genuinely independent stable drivers may be only one (FEAUM), with EPS as a strong candidate pending P/DE confirmation and FRE Margin as a multiple-specific driver. This materially affects the final peer set auto-include logic, which requires "Q1 on 2+ of 3 confirmed independent stable value drivers."

### C3. STEP and HLNE quantitative data stored under non-standard period keys

`2-data/quantitative_data.json`: STEP and HLNE (March 31 fiscal year firms) have all 17 driver metrics present as keys but with `fy2025.value = null` for every metric. Their actual data is stored under non-standard keys like `q3fy2026(quarterendeddec2025)`. This means:

- The raw data file reports 0/17 metrics with `fy2025` values for these firms.
- The `3-analysis/standardized_data.json` did partially recover some values (STEP: 10/17, HLNE: 9/17), but several of these are single-quarter figures being used as if they were full-year values. For example, STEP's DE/share of $0.65 (`standardized_data.json`) is a single-quarter figure (Q3 FY2026), not annualized. HLNE's DE/share of $4.41 is similarly a single-quarter figure with a note stating "this is a single-quarter figure, not annualized."

**Impact:** Using quarterly earnings as if they were annual figures systematically inflates per-share metrics for these firms. HLNE's claimed EPS of $4.35 (which placed it Q1 on DVR-002) may actually be a quarterly figure -- if the annual EPS is roughly 4x lower, HLNE's Q1 ranking on EPS would be incorrect. This affects both the correlation analysis (HLNE appears as a high-EPS firm when it may not be) and the peer selection rationale.

## Significant Gaps

### S1. P/DE multiple has very low coverage (N=10 in full sample, N=6-9 in most correlations)

`3-analysis/correlations.json`: The P/DE multiple has N=10 in the full sample (vs N=19 for P/FRE and N=18 for EV/FEAUM). Only 10 of 25 firms have a P/DE value. In the consistent sub-sample, P/DE has N=7-9. This means that the "across all three multiples" criterion in the stable_value_driver classification is structurally impossible to satisfy rigorously -- one-third of the classification basis has insufficient statistical power. The methodology document (`statistical_methodology.md`) does not flag this asymmetry or discuss its implications for the classification scheme.

### S2. Market cap reference dates span 3 months across tiers

`2-data/quantitative_data.json` metadata: Tier 1 uses Dec 31, 2025 market caps; Tier 2 uses Feb 28, 2026; Tier 3 uses Mar 6, 2026. This creates a 2+ month spread in the denominator of valuation multiples. If the alt-asset-management sector experienced meaningful price movements between December 2025 and March 2026, cross-firm multiple comparisons are contaminated by timing differences. The methodology document acknowledges this ("valuation multiples should be interpreted with awareness") but does not quantify the potential impact or test sensitivity to a common reference date.

### S3. Metric coverage below 60% for several final-set firms without adequate flagging

The final peer set selection criteria (`3-analysis/final_peer_set.json` metadata) state `"metric_coverage_minimum": "At least 60% metric coverage in standardized data"`. In the standardized data:

| Firm | Standardized Coverage | Final Set? | Threshold Met? |
|------|----------------------|------------|----------------|
| APO | 47.1% (8/17) | Yes (auto-include) | No |
| BAM | 47.1% (8/17) | Yes (auto-include) | No |
| OWL | 52.9% (9/17) | Yes | No |
| STEP | 58.8% (10/17) | Yes (cautionary) | No |
| HLNE | 52.9% (9/17) | Yes | No |
| CG | 58.8% (10/17) | Yes | No |

Six of twelve final-set firms fall below the stated 60% coverage threshold. The `flagged_gaps` section in `final_peer_set.json` mentions APO and BAM but frames the issue as "below the 60% threshold but auto-included due to Q1 on 2+ independent drivers." The other four firms below threshold are not flagged. If the 60% rule is soft (overridable), this should be documented explicitly with a revised threshold or waiver rationale.

### S4. No bootstrap confidence intervals for non-BH-significant correlations with rho > 0.5

`3-analysis/statistical_methodology.md` Section 2: Bootstrap CIs are reported for the 4 BH-significant correlations and 7 additional "notable" correlations. But several full-sample correlations with |rho| > 0.5 that are classified as `stable_value_driver` or `multiple_specific_driver` do not have bootstrap CIs reported (e.g., Total AUM vs EV/FEAUM, rho=0.552, N=18; DE/share vs EV/FEAUM, rho=0.833, N=8). Without bootstrap CIs, the reader cannot assess whether these non-significant-but-classified correlations have CIs that include zero, which would undermine their classification.

### S5. Multicollinearity documented but not integrated into driver ranking

`3-analysis/correlations.json` multicollinearity section: 26 driver pairs with |rho| > 0.7 are identified, including FEAUM vs Total AUM (rho=0.96) and FRE margin vs Comp ratio (rho=-1.0). The partial correlation analysis in `statistical_methodology.md` Section 6 demonstrates that Total AUM and Credit % are confounded by FEAUM. However, the `full_sample_driver_ranking` in `correlations.json` still lists Total AUM as a `stable_value_driver` (rank 3) and Credit % as a `moderate_signal` (rank 6) without any annotation that these signals are not independent of FEAUM. The partial correlation findings should be reflected directly in the driver ranking, either by demoting confounded drivers or by adding an "independence" flag.

### S6. PGHN metric coverage discrepancy between raw and standardized data

`2-data/quantitative_data.json`: PGHN has only 4/17 metrics with `fy2025` values populated (24% coverage). Several additional metrics are stored under non-standard keys (`dec2025`, `h1fy2025`, `h1fy2025vsh1fy2024`). The `3-analysis/standardized_data.json` resolved some of these to 11/17 (65%), but the `final_peer_set.json` claims 64.7% coverage. This indicates the standardization step silently promoted non-`fy2025` data without documenting the period mismatches. For PGHN specifically, FRE margin and FRE growth are H1 2025 figures being compared to full-year 2025 data from other firms, introducing a temporal comparability issue.

## Minor Observations

### M1. Correlation count discrepancy

The metadata in `correlations.json` states `"total_correlations_computed": 102` (51 consistent + 51 full sample). The metric taxonomy (`1-universe/metric_taxonomy.json`) states `"approximate_tests": 42` (14 drivers x 3 multiples). The actual count of 51 full-sample correlations (17 drivers x 3 multiples) uses all 17 metrics including market structure metrics. However, the metric taxonomy explicitly states that market structure metrics (MET-VD-021/022/023) are `"is_driver_candidate": false` and should be "excluded from correlation analysis." It appears that 3 market-structure metrics were not correlated (since 14 x 3 = 42, not 51), but the actual count of 51 = 17 x 3 suggests either (a) all 17 were correlated or (b) the comp ratio metric (MET-VD-015) and two others not marked as driver candidates were included. The count of 51 should be reconciled with the 14 driver candidates.

### M2. EPS currency conversion for PGHN

`3-analysis/standardized_data.json`: PGHN's EPS is reported as 48.832 USD. The raw data shows CHF 43.6 with a CHF/USD rate of 1.12, yielding 43.6 x 1.12 = 48.832 USD. This conversion is correct and documented. However, PGHN's EPS is orders of magnitude larger than peers (e.g., PAX $0.54, BX $3.87) because PGHN shares trade at ~CHF 1,200. The Spearman rank correlation handles this correctly (it uses ranks, not values), but it is worth noting that the per-share metric scale differences are extreme and would invalidate any Pearson-based analysis.

### M3. Appendix B classification inconsistency

`3-analysis/statistical_methodology.md` Appendix B: Total AUM is listed with "Independent of Scale? No (confounded by FEAUM)" yet its Classification is "Stable driver." These two characterizations are in tension. A confounded metric is not an independent driver. The appendix would benefit from a clearer distinction between "stable correlation" and "independent driver."

### M4. BH FDR applied at q=0.10 but confidence tiers use 0.01/0.05/0.10 thresholds

The BH correction at q=0.10 means up to 10% of discoveries may be false. The confidence classification then places all four BH-significant results at "moderate confidence" (adjusted p < 0.05). This is reasonable but somewhat confusing -- the FDR threshold is 0.10 but the confidence cutoff is 0.05. A brief explanation of why the confidence tiers use stricter thresholds than the FDR cutoff would improve clarity.

## Recommended Actions

1. **[Critical] Annualize or exclude quarterly earnings data for STEP and HLNE.** Review every metric value for these firms in `standardized_data.json` and confirm whether it represents a full-year or single-quarter figure. Annualize quarterly figures where appropriate (with a seasonality caveat) or exclude them from the correlation analysis. Re-run the EPS driver ranking after correction -- HLNE's Q1 placement may be incorrect.

2. **[Critical] Revise the "stable value driver" classification to require N >= 10 for all three multiples.** EPS and Total AUM should be reclassified: EPS to "multiple-specific driver" (confirmed for EV/FEAUM, directionally supportive but insufficient for P/DE), and Total AUM to "confounded proxy for FEAUM" (per the partial correlation analysis). Update the `full_sample_driver_ranking` in `correlations.json` accordingly.

3. **[Critical] Add "independence" annotations to the driver ranking.** Flag Total AUM and Credit % as "confounded by FEAUM" directly in the driver ranking array, not just in the separate partial correlation section. This prevents downstream agents and readers from treating these as independent signals.

4. **[Significant] Document the 60% coverage threshold as soft with explicit waiver criteria.** Either enforce the threshold (which would remove APO, BAM, OWL, STEP, HLNE, and CG from the final set -- undesirable) or revise it to state: "60% target; firms below threshold included when they are Q1 on independent drivers or serve as instructive cautionary cases, with coverage gaps documented."

5. **[Significant] Add valuation multiple coverage to the final peer set table.** The current `metric_coverage_pct` field is misleading because it counts only driver metrics, not multiples. Add a `multiples_available` field (e.g., `["p_fre", "ev_feaum"]`) so that readers can immediately see which firms participate in which correlation.

6. **[Significant] Harmonize market cap reference dates or test sensitivity.** Either re-estimate all multiples at a common date or compute the sensitivity of the top 4 BH-significant correlations to a +/- 10% shift in Tier 2/3 market caps. If the LOO analysis already shows robustness to single-firm perturbation, a brief note explaining why dating differences do not materially affect rank-order correlations would suffice.

7. **[Significant] Report bootstrap CIs for all correlations classified as "stable_value_driver" or "multiple_specific_driver" in the full sample, not only for BH-significant ones.** Several classified drivers lack CIs, leaving their reliability unassessed.

8. **[Minor] Reconcile the 51-correlation count with the 14 driver candidates.** Clarify whether 17 or 14 metrics were correlated in the full sample, and if 17, explain why market structure metrics were included contrary to the metric taxonomy.
