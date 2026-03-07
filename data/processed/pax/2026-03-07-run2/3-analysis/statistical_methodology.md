# Statistical Methodology — Valuation Driver Analysis

**Pipeline:** Valuation Driver Analysis (VDA)
**Stage:** VD-A4b — Statistical Documentation and Explainability
**Company:** Patria Investments Limited (NASDAQ: PAX)
**Sector:** Alternative Asset Management
**Run:** 2026-03-07-run2
**Universe:** 25 publicly listed alternative asset managers (24 used in analysis after excluding BN)

---

## 1. Methods and Justification

### 1.1 Choice of Spearman Rank Correlation

This analysis employs **Spearman rank correlation** (rho) as the primary measure of association between driver metrics and valuation multiples. Spearman was selected over Pearson for the following reasons:

- **Robustness to non-normality.** Financial metrics (AUM, earnings, fee rates) are positively skewed and fat-tailed. Spearman operates on ranks rather than raw values, requiring no distributional assumptions. Pearson assumes bivariate normality, which is violated in this dataset.

- **Outlier resistance.** The dataset contains meaningful outliers (e.g., Blackstone FEAUM = $922B, 3x the next-largest peer; Antin HHI = 10,000, a pure-play infrastructure firm). Spearman's rank transformation bounds the influence of extreme values, whereas a single outlier can dominate Pearson's correlation.

- **Monotonic relationships.** Spearman detects any monotonic (not just linear) relationship between variables. The relationship between scale and valuation, for instance, may be concave (diminishing returns to size), which Spearman captures but Pearson may understate.

- **Small-sample appropriateness.** With N ranging from 10 to 19 per correlation, Spearman's distribution-free nature avoids the sensitivity of parametric methods to small-sample distributional violations.

### 1.2 Why Multiple Regression Was Not Used

Multiple regression was explicitly not used for this analysis. The reasons are:

1. **Insufficient degrees of freedom.** With N approximately equal to 25 and 14 candidate driver metrics, a regression model would have 14 predictors for approximately 19 observations (P/FRE sample). The rule of thumb of 10-15 observations per predictor is severely violated, yielding unreliable coefficient estimates and inflated R-squared.

2. **Multicollinearity.** 26 driver pairs exhibit Spearman |rho| > 0.7, including near-perfect correlations (FEAUM vs Total AUM: rho = 0.96; FRE margin vs Comp ratio: rho = -1.0). Multicollinearity inflates variance of regression coefficients, produces unstable sign estimates, and makes individual predictor significance uninterpretable.

3. **Overfitting risk.** With more parameters than can be reliably estimated, a regression model would fit noise in the training sample and fail to generalize. Cross-validation is not feasible at N approximately equal to 25.

4. **Endogeneity.** Several drivers are simultaneously caused by and causally related to valuation multiples. For example, high-valuation firms can raise capital more cheaply, boosting AUM growth, which in turn supports higher multiples. Regression coefficients would conflate causal and reverse-causal effects. Instrumental variable approaches are infeasible at this sample size.

5. **Interpretive clarity.** Pairwise Spearman correlations provide transparent, auditable signals that are directly interpretable by investment professionals. Regression coefficients require conditioning on all other variables simultaneously, obscuring individual driver effects in the presence of collinearity.

---

## 2. Bootstrap Confidence Intervals

1,000 bootstrap iterations were performed for each correlation with N >= 10 on the full sample. At each iteration, N observations were resampled with replacement and the Spearman rho recomputed. The 2.5th and 97.5th percentiles of the bootstrap distribution provide non-parametric 95% confidence intervals.

### 2.1 BH-Significant Correlations — Bootstrap Results

| Driver | Multiple | Observed rho | 95% CI Lower | 95% CI Upper | CI Includes Zero | N |
|--------|----------|-------------|-------------|-------------|-----------------|---|
| Fee-Earning AUM | P/FRE | +0.765 | +0.333 | +0.942 | No | 17 |
| Total AUM | P/FRE | +0.690 | +0.282 | +0.897 | No | 19 |
| EPS (GAAP) | EV/FEAUM | +0.750 | +0.283 | +0.911 | No | 14 |
| FRE Margin | EV/FEAUM | +0.708 | +0.277 | +0.955 | No | 17 |

All four BH-significant correlations have 95% CIs that exclude zero, confirming that the associations are not driven by sampling variability alone.

### 2.2 Other Notable Bootstrap Results

| Driver | Multiple | Observed rho | 95% CI Lower | 95% CI Upper | CI Includes Zero | N |
|--------|----------|-------------|-------------|-------------|-----------------|---|
| EPS (GAAP) | P/FRE | +0.665 | +0.232 | +0.927 | No | 13 |
| FEAUM | EV/FEAUM | +0.629 | +0.157 | +0.839 | No | 16 |
| Total AUM | EV/FEAUM | +0.552 | +0.016 | +0.813 | No | 18 |
| Total AUM | P/DE | +0.527 | -0.124 | +0.948 | **Yes** | 10 |
| FRE Margin | P/DE | +0.515 | -0.185 | +0.923 | **Yes** | 10 |
| Credit % | P/FRE | +0.476 | -0.017 | +0.836 | **Yes** | 18 |
| FRE Margin | P/FRE | +0.404 | -0.052 | +0.757 | **Yes** | 19 |

Correlations flagged with "CI Includes Zero" should be interpreted cautiously; they may not persist in a larger sample.

---

## 3. Multiple Comparisons Correction

### 3.1 Benjamini-Hochberg FDR

The Benjamini-Hochberg (BH) procedure was applied at q = 0.10 (false discovery rate of 10%) across all 51 full-sample correlations. BH controls the expected proportion of false discoveries among rejected hypotheses, providing a less conservative but more powerful alternative to Bonferroni for exploratory analyses.

### 3.2 Corrected and Uncorrected P-Values for BH-Significant Findings

| Correlation ID | Driver | Multiple | rho | Raw p-value | BH-adjusted p-value | BH Significant (q=0.10) |
|---------------|--------|----------|-----|------------|--------------------|-----------------------|
| COR-061 | Fee-Earning AUM | P/FRE | +0.765 | 0.0003 | 0.0255 | Yes |
| COR-064 | Total AUM | P/FRE | +0.690 | 0.0011 | 0.0374 | Yes |
| COR-090 | FRE Margin | EV/FEAUM | +0.708 | 0.0015 | 0.0382 | Yes |
| COR-057 | EPS (GAAP) | EV/FEAUM | +0.750 | 0.0020 | 0.0408 | Yes |

Four of 51 full-sample correlations survive BH correction. All four have raw p-values below 0.005.

---

## 4. Confidence Classification

Based on BH-adjusted p-values:

| Classification | Criterion | Correlations |
|---------------|-----------|--------------|
| **High confidence** | Adjusted p < 0.01 | None |
| **Moderate confidence** | Adjusted p < 0.05 | FEAUM vs P/FRE (0.026), Total AUM vs P/FRE (0.037), FRE Margin vs EV/FEAUM (0.038), EPS vs EV/FEAUM (0.041) |
| **Suggestive** | Adjusted p < 0.10 | None additional (the 4 above are all below 0.05) |
| **Not significant** | Adjusted p >= 0.10 | Remaining 47 correlations |

All four BH-significant correlations fall in the **moderate confidence** tier. No correlations achieve high confidence (adjusted p < 0.01), which is expected given the small sample sizes (N = 14-19) and the number of simultaneous tests.

---

## 5. Sensitivity Analyses

### 5.1 Leave-One-Out Analysis

For each BH-significant correlation, the Spearman rho was recomputed 16-19 times, each time excluding one firm from the sample. A finding is flagged as **fragile** if any single firm's removal changes the rho by more than 0.15.

| Driver | Multiple | Original rho | Min rho (LOO) | Max rho (LOO) | Range | Influential Firms | Verdict |
|--------|----------|-------------|---------------|---------------|-------|-------------------|---------|
| FEAUM | P/FRE | +0.765 | +0.718 | +0.829 | 0.112 | None | **Robust** |
| Total AUM | P/FRE | +0.690 | +0.635 | +0.750 | 0.116 | None | **Robust** |
| EPS (GAAP) | EV/FEAUM | +0.750 | +0.703 | +0.852 | 0.148 | None | **Robust** |
| FRE Margin | EV/FEAUM | +0.708 | +0.650 | +0.782 | 0.132 | None | **Robust** |

All four BH-significant correlations are robust to leave-one-out perturbation. No single firm drives any of the significant findings. The maximum LOO range is 0.148 (EPS vs EV/FEAUM), below the 0.15 threshold.

### 5.2 Temporal Stability

Temporal stability of correlations cannot be fully tested in this analysis. Valuation multiples are computed at a single point in time (FY2025 market capitalization against FY2025 earnings/AUM). FY2024 driver values are available for only a subset of firms (3-8 firms depending on the metric, sourced from tier 1 only), which is insufficient for meaningful re-estimation.

| Driver | FY2024 Data Points Available | Sufficient for Re-estimation |
|--------|-----------------------------|-----------------------------|
| EPS (GAAP) | 3 | No |
| FEAUM | 8 | No |
| Total AUM | 7 | No |
| FRE Margin | 3 | No |

**Recommendation:** Future iterations of this analysis should collect multi-year panel data (FY2022-FY2025) to enable temporal stability testing. A finding that persists across multiple cross-sections would substantially increase confidence.

---

## 6. Partial Correlations

Partial Spearman correlations were computed for top drivers, controlling for FEAUM (MET-VD-004), to test whether driver signals are confounded by scale. This is particularly important given the near-perfect correlation between FEAUM and Total AUM (rho = 0.96 on the consistent sub-sample).

### 6.1 Results

| Driver | Multiple | N | Raw rho | Partial rho (controlling FEAUM) | Attenuation | Verdict |
|--------|----------|---|---------|--------------------------------|-------------|---------|
| EPS (GAAP) | P/FRE | 12 | +0.706 | +0.665 | 0.041 | **Independent signal** |
| EPS (GAAP) | EV/FEAUM | 13 | +0.758 | +0.688 | 0.070 | **Independent signal** |
| Total AUM | P/FRE | 17 | +0.765 | +0.118 | 0.646 | **Confounded by FEAUM** |
| Total AUM | EV/FEAUM | 16 | +0.638 | +0.149 | 0.489 | **Confounded by FEAUM** |
| FRE Margin | EV/FEAUM | 15 | +0.611 | +0.414 | 0.197 | **Partially attenuated** |
| FRE Margin | P/FRE | 17 | +0.284 | -0.309 | N/A | **Sign reversal** — raw association driven entirely by scale confound |
| Credit % | P/FRE | 16 | +0.453 | -0.111 | 0.342 | **Confounded by FEAUM** |
| Credit % | EV/FEAUM | 15 | +0.356 | +0.077 | 0.279 | **Confounded by FEAUM** |

### 6.2 Interpretation

- **EPS (GAAP)** retains its signal after controlling for scale. The partial rho drops by only 0.04-0.07, indicating that EPS captures information about valuation independent of firm size. This is the most robust driver in the dataset.

- **Total AUM** is almost entirely confounded by FEAUM. After partialing out FEAUM, the Total AUM signal collapses to near zero. This confirms that Total AUM and FEAUM are measuring the same underlying factor (scale), and Total AUM adds no incremental explanatory power.

- **FRE Margin** shows partial attenuation. The EV/FEAUM signal drops from 0.61 to 0.41 after controlling for scale, suggesting that roughly one-third of the FRE margin signal is attributable to scale (larger firms tend to have higher margins due to operating leverage). The remaining 0.41 partial correlation indicates a genuine, independent efficiency signal.

- **Credit %** is confounded. The raw positive associations with P/FRE and EV/FEAUM disappear after controlling for scale, suggesting that credit-heavy firms tend to be larger rather than that credit exposure per se drives valuation.

---

## 7. Effective Independent Tests

### 7.1 Estimation Method

The 51 full-sample correlations are not independent because the 17 driver metrics are substantially correlated with each other (26 pairs with |rho| > 0.7). The effective number of independent tests was estimated by identifying driver clusters and counting independent dimensions:

**Driver clusters identified (based on pairwise |rho| > 0.7 on the consistent sub-sample):**

1. **Scale cluster:** FEAUM, Total AUM, DE growth 3yr, FEAUM CAGR 3yr, Performance fee share (~5 metrics collapsing to ~1-2 independent dimensions)
2. **Profitability cluster:** DE/share, FRE margin, Comp ratio (~3 metrics collapsing to ~1 dimension)
3. **Mix-growth cluster:** HHI, Credit %, FRE growth YoY (~3 metrics collapsing to ~1-2 dimensions)
4. **Approximately independent:** EPS, FEAUM YoY growth, Fundraising ratio, Organic growth, Perm capital %, Mgmt fee rate (~6 metrics, each ~1 dimension)

**Estimated effective independent drivers:** ~12 (reduced from 17)
**Estimated effective tests:** ~36 (= 12 drivers x 3 multiples), reduced from 51

### 7.2 Implications for Multiple Testing

| Correction Method | Threshold (alpha = 0.05) | Tests Assumed | Corrected Alpha |
|-------------------|-------------------------|---------------|-----------------|
| None (uncorrected) | 0.05 | 1 | 0.0500 |
| Bonferroni (raw) | 0.05 / 51 | 51 | 0.0010 |
| Bonferroni (effective) | 0.05 / 36 | 36 | 0.0014 |
| BH FDR q = 0.10 (used) | Adaptive | 51 | Adaptive |

Under the effective-test-adjusted Bonferroni, only COR-061 (FEAUM vs P/FRE, p = 0.0003) would survive. The BH FDR procedure, which was used as the primary correction, is better suited to this exploratory context because it controls the false discovery rate rather than the family-wise error rate, preserving more statistical power while still limiting false positives.

---

## 8. Mandatory Disclaimers

The following limitations apply to all findings in this analysis. They must be considered when interpreting results.

**Correlation does not imply causation.** The Spearman rank correlations reported in this analysis measure the strength and direction of monotonic association between driver metrics and valuation multiples. They do not establish causal relationships. A positive correlation between FEAUM and P/FRE, for example, could reflect that (a) larger AUM causes higher multiples, (b) higher multiples enable cheaper capital and faster AUM growth, (c) both are driven by an unobserved third factor (e.g., brand quality, founder reputation), or (d) some combination of these mechanisms.

**Survivorship bias: universe consists of currently listed firms only.** The universe of 25 firms includes only alternative asset managers that are publicly listed as of FY2025. Firms that were acquired (e.g., Sculptor/Rithm), delisted (e.g., Petershill Partners), or remained private are excluded. This creates survivorship bias: the observed correlations reflect the characteristics of firms that have survived as public entities, which may systematically differ from the full population of alt-asset managers.

**Point-in-time limitation: conditions as of most recent data collection period.** All data reflects conditions as of FY2025 (calendar year ended December 31, 2025, or nearest fiscal year equivalent). Valuation multiples are computed using market capitalizations from December 2025 through March 2026 (varying by tier). Market conditions, interest rates, and investor sentiment at this specific point in time influence both driver metrics and valuation multiples. Results may not generalize to different market regimes.

**Small-N limitation: N approximately equal to 25 limits statistical power; findings generate hypotheses, not definitive causal claims.** The largest full-sample correlation (P/FRE) includes N = 19 firms. The consistent sub-sample includes only N = 9 firms. At these sample sizes, statistical power is limited: even true correlations of moderate strength (rho = 0.4) may not achieve statistical significance, and apparent significant correlations may reflect sampling noise. The four BH-significant findings should be treated as well-supported hypotheses warranting further investigation, not as established facts.

**Endogeneity: several drivers may be simultaneously caused by and causally related to valuation multiples.** AUM growth, fundraising intensity, and fee-related earnings are all influenced by a firm's market valuation. High-multiple firms attract more investor capital (cheaper equity issuance, greater LP confidence), which mechanically increases AUM and earnings. This bidirectional causality means that observed correlations likely overstate the unidirectional effect of drivers on multiples. Instrumental variable or natural experiment approaches would be needed to estimate causal effects, but are infeasible at this sample size.

**FRE definition heterogeneity: FRE is non-GAAP; firm-specific definitions vary; measurement error is present.** Fee-Related Earnings is a non-GAAP metric with material definitional differences across firms. Key variations include: pre-tax vs. after-tax treatment; inclusion or exclusion of equity-based compensation; treatment of transaction, advisory, and monitoring fees; and European equivalents that use IFRS-based operating profit proxies (e.g., EQT's "Fee-related EBITDA," CVC's "Management Fee Earnings," Bridgepoint's "Underlying EBITDA"). These definitional differences introduce measurement error that attenuates correlations and may bias comparisons. The FRE definition reconciliation in the standardized data file documents each firm's specific definition.

---

## Appendix A: Software and Reproducibility

- **Correlation computation:** Custom Python implementation of Spearman rank correlation with tie-handling (average ranks). P-values computed using the t-distribution approximation: t = rho * sqrt((N-2) / (1-rho^2)), with degrees of freedom = N-2.
- **Bootstrap:** 1,000 iterations, resampling with replacement, seed = 42 for reproducibility. 95% CIs taken from the 2.5th and 97.5th percentiles of the bootstrap distribution.
- **BH FDR correction:** Standard Benjamini-Hochberg step-up procedure applied to all 51 full-sample p-values simultaneously at q = 0.10.
- **Partial correlations:** Computed by correlating the residuals of X and Y after removing the linear effect of Z (in rank space). Specifically: partial_rho(X,Y|Z) = (rho_XY - rho_XZ * rho_YZ) / sqrt((1 - rho_XZ^2) * (1 - rho_YZ^2)).
- **Leave-one-out:** Exhaustive recomputation excluding each firm in turn from the paired sample.

## Appendix B: Summary of Key Findings

| Rank | Driver | Avg |rho| | Classification | Survives BH? | Robust (LOO)? | Independent of Scale? |
|------|--------|-----------|----------------|--------------|---------------|----------------------|
| 1 | EPS (GAAP) | 0.729 | Stable driver | Yes (EV/FEAUM) | Yes | Yes |
| 2 | FEAUM | 0.695 | Stable driver | Yes (P/FRE) | Yes | N/A (is the scale variable) |
| 3 | Total AUM | 0.590 | Stable driver | Yes (P/FRE) | Yes | No (confounded by FEAUM) |
| 4 | DE/share | 0.550 | Moderate signal | No | N/A | Mixed |
| 5 | FRE Margin | 0.542 | Multiple-specific (EV/FEAUM) | Yes (EV/FEAUM) | Yes | Partially (attenuated but retains signal) |
| 6 | Credit % | 0.395 | Moderate signal | No | N/A | No (confounded by FEAUM) |
| 7 | FRE Growth YoY | 0.260 | Moderate signal | No | N/A | N/A |

The most defensible drivers of valuation in alt-asset management, based on this analysis, are:
1. **Scale (FEAUM)** — the dominant factor, with the strongest and most significant correlation with P/FRE.
2. **Earnings quality (EPS)** — retains its signal after controlling for scale, suggesting that the market rewards profitability independent of firm size.
3. **Operating efficiency (FRE Margin)** — shows an independent, partially attenuated signal for EV/FEAUM, indicating that the market places a premium on fee-based operating leverage beyond what scale alone explains.
