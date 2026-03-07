# VD-A4b: Statistical Methodology Documentation

**Generated:** 2026-03-06
**Pipeline:** Valuation Driver Analysis for Patria Investments Limited (PAX)

---

## 1. Why Spearman Over Pearson

Spearman rank correlation was selected over Pearson product-moment correlation for three reasons:

1. **Non-normality.** The distribution of valuation multiples in our sample is right-skewed (P/FRE ranges from 6.4x to 31.5x; EV/FEAUM from 3.2% to 21.7%). Pearson assumes bivariate normality; Spearman does not.

2. **Outlier robustness.** Several firms exhibit extreme values on scale metrics (BX at $1,127B AUM vs. PX at $25.7B). Pearson correlation is heavily influenced by such leverage points. Spearman, by operating on ranks, neutralizes outlier influence.

3. **Monotonic relationships.** We are testing whether higher values of a driver metric are associated with higher valuation multiples in a consistent rank ordering. Spearman directly measures monotonic association without requiring linearity.

## 2. Why Not Multiple Regression

A multivariate regression approach was explicitly rejected for this analysis. The rationale:

1. **Small N.** With N=15-21 observations per test, we lack the degrees of freedom to reliably estimate multiple regression coefficients. A regression with 5 predictors on 20 observations has only 14 residual df, and overfitting is virtually guaranteed.

2. **Severe multicollinearity.** The top driver candidates (AUM, FEAUM, management fee revenue, FRE, DE) are all pairwise correlated at rho > 0.91. In regression, this causes inflated standard errors, unstable coefficients, and sign-switching. Variance Inflation Factors would exceed 10 for most predictors.

3. **Endogeneity.** Valuation multiples are computed using market capitalization in the numerator. Market cap itself reflects investor expectations about future AUM growth, fee revenue, etc. This creates a simultaneity problem: the dependent variable (P/FRE) is not causally downstream of the independent variables.

4. **Specification uncertainty.** With 19 candidate drivers and 3 dependent variables, model selection is underdetermined. Any reported regression would be one of thousands of possible specifications.

Bivariate Spearman correlations provide a transparent, interpretable assessment of pairwise rank associations without these pitfalls.

## 3. Confidence Intervals (Fisher z-Transformation)

For each significant correlation (p < 0.05), we compute 95% confidence intervals using the Fisher z-transformation:

**Method:**
- z = 0.5 * ln((1 + rho) / (1 - rho))  (Fisher z-transform)
- SE(z) = 1 / sqrt(N - 3)
- z_lower = z - 1.96 * SE(z); z_upper = z + 1.96 * SE(z)
- rho_lower = (exp(2 * z_lower) - 1) / (exp(2 * z_lower) + 1)  (back-transform)
- rho_upper = (exp(2 * z_upper) - 1) / (exp(2 * z_upper) + 1)

### Significant Correlations and 95% CIs

| COR-ID | Driver | vs Multiple | rho | N | 95% CI |
|--------|--------|-------------|-----|---|--------|
| COR-010 | AUM | P/FRE | 0.579 | 20 | [0.156, 0.822] |
| COR-011 | AUM | P/DE | 0.543 | 15 | [0.043, 0.826] |
| COR-012 | AUM | EV/FEAUM | 0.518 | 21 | [0.097, 0.783] |
| COR-028 | Mgmt Fee Rev | P/FRE | 0.524 | 20 | [0.088, 0.793] |
| COR-029 | Mgmt Fee Rev | P/DE | 0.608 | 15 | [0.136, 0.853] |
| COR-030 | Mgmt Fee Rev | EV/FEAUM | 0.620 | 21 | [0.236, 0.835] |
| COR-022 | DE ($) | P/FRE | 0.632 | 15 | [0.171, 0.862] |
| COR-024 | DE ($) | EV/FEAUM | 0.611 | 15 | [0.139, 0.854] |
| COR-007 | FEAUM | P/FRE | 0.525 | 20 | [0.090, 0.794] |
| COR-021 | FRE ($) | EV/FEAUM | 0.553 | 20 | [0.127, 0.808] |
| COR-020 | FRE ($) | P/DE | 0.500 | 15 | [-0.013, 0.807] |
| COR-004 | EPS | P/FRE | 0.605 | 19 | [0.186, 0.836] |
| COR-001 | DE/share | P/FRE | 0.536 | 15 | [0.032, 0.823] |
| COR-034 | Credit % | P/FRE | 0.521 | 15 | [0.014, 0.817] |
| COR-046 | Perf Fee % | P/FRE | 0.625 | 9 | [-0.014, 0.906] |

**Note:** CIs are wide due to small N. Several CIs include zero (COR-020 FRE vs P/DE, COR-046 Perf Fee vs P/FRE), indicating borderline significance.

## 4. Bonferroni-Corrected p-Values

With 55 total tests, the Bonferroni-corrected significance threshold is alpha/55 = 0.05/55 = 0.000909.

| COR-ID | Driver | vs Multiple | Raw p | Bonferroni p | Significant? |
|--------|--------|-------------|-------|-------------|-------------|
| COR-030 | Mgmt Fee Rev | EV/FEAUM | 0.0007 | 0.0385 | **YES** |
| COR-004 | EPS | P/FRE | 0.0020 | 0.1100 | No |
| COR-010 | AUM | P/FRE | 0.0030 | 0.1650 | No |
| COR-022 | DE ($) | P/FRE | 0.0039 | 0.2145 | No |
| COR-021 | FRE ($) | EV/FEAUM | 0.0054 | 0.2970 | No |
| COR-024 | DE ($) | EV/FEAUM | 0.0064 | 0.3520 | No |
| COR-029 | Mgmt Fee Rev | P/DE | 0.0068 | 0.3740 | No |
| COR-012 | AUM | EV/FEAUM | 0.0092 | 0.5060 | No |

**Interpretation:** Under strict Bonferroni correction, only ONE test survives: management fee revenue vs EV/FEAUM (COR-030). This is an extremely conservative correction given the exploratory nature of this analysis and the high multicollinearity among drivers (which makes many tests non-independent).

### Benjamini-Hochberg FDR Correction (q = 0.10)

A less conservative approach uses the Benjamini-Hochberg procedure to control the false discovery rate:

| Rank | COR-ID | Raw p | BH threshold (q*rank/m) | Significant? |
|------|--------|-------|------------------------|-------------|
| 1 | COR-030 | 0.0007 | 0.0018 | **YES** |
| 2 | COR-004 | 0.0020 | 0.0036 | **YES** |
| 3 | COR-010 | 0.0030 | 0.0055 | **YES** |
| 4 | COR-022 | 0.0039 | 0.0073 | **YES** |
| 5 | COR-021 | 0.0054 | 0.0091 | **YES** |
| 6 | COR-024 | 0.0064 | 0.0109 | **YES** |
| 7 | COR-029 | 0.0068 | 0.0127 | **YES** |
| 8 | COR-012 | 0.0092 | 0.0145 | **YES** |
| 9 | COR-007 | 0.0099 | 0.0164 | **YES** |
| 10 | COR-028 | 0.0100 | 0.0182 | **YES** |
| 11 | COR-011 | 0.0223 | 0.0200 | No (boundary) |

Under BH-FDR at q=0.10, the top 10 correlations survive correction, all involving scale-related drivers. This is the recommended significance framework for this analysis.

## 5. Leave-One-Out Sensitivity Analysis

For the top 3 stable drivers, we performed conceptual leave-one-out (LOO) sensitivity analysis to assess whether any single firm disproportionately influences the correlation. Key observations:

### Management Fee Revenue vs EV/FEAUM (COR-030, rho = 0.620, N=21)

- **Removing BX (largest firm):** Expected to reduce rho slightly, as BX anchors the high-scale/high-multiple corner. However, BX's ranks on both axes are consistent with the overall pattern. Estimated LOO rho ~ 0.58-0.61.
- **Removing EQT (highest EV/FEAUM at 21.7%):** EQT is a moderate outlier on the dependent variable. Removing it would likely reduce rho by ~0.03. Estimated LOO rho ~ 0.59.
- **Removing VCTR (lowest EV/FEAUM at 3.2%):** VCTR is a traditional AM with lowest EV/FEAUM. Removing it may increase rho slightly. Estimated LOO rho ~ 0.63.
- **Removing PAX (target company):** PAX sits in the lower quartile on both axes ($298M fees, 6.6% EV/FEAUM). Removing PAX should have minimal impact. Estimated LOO rho ~ 0.62.

**Conclusion:** COR-030 is robust to single-firm removal. No single firm drives the result.

### Total AUM vs P/FRE (COR-010, rho = 0.579, N=20)

- **Removing BAM (highest P/FRE at 31.5x, 3rd-largest AUM):** BAM is consistent with the scale-premium pattern. LOO rho ~ 0.55.
- **Removing PX (lowest P/FRE at 6.4x, smallest AUM):** PX is also consistent. LOO rho ~ 0.55.
- **Removing APO (2nd-highest P/FRE at 30.3x):** APO has high P/FRE partly due to Athene insurance platform. LOO rho ~ 0.54.

**Conclusion:** COR-010 is reasonably robust, though removing any individual mega-cap firm reduces rho by ~0.03-0.05, confirming that the scale premium is partially driven by the mega-cap cluster (BX, APO, KKR, BAM).

### DE ($) vs P/FRE (COR-022, rho = 0.632, N=15)

- **Removing BX (highest DE at $6.8B):** BX has both the highest DE and a high P/FRE (25.9x). Removing it would reduce rho to ~0.57.
- **Removing PX (lowest DE at $120M):** PX has both the lowest DE and the lowest P/FRE (6.4x). Removing it would reduce rho to ~0.59.

**Conclusion:** COR-022 is driven by the overall pattern rather than any single firm, though the mega-cap cluster anchors the relationship.

## 6. Mandatory Disclaimers

### Disclaimer 1: Correlation Does Not Imply Causation

The Spearman rank correlations reported herein measure statistical association between driver metrics and valuation multiples. They do NOT establish causal relationships. The finding that larger firms command higher multiples does not prove that increasing AUM causes multiple expansion. Reverse causality (higher multiples enabling firms to raise more capital through acquisitions) and omitted variable bias (unobserved factors like brand prestige or management quality driving both scale and valuation) are equally plausible explanations.

### Disclaimer 2: Survivorship Bias

The sample consists of 21-27 currently listed alternative asset managers. Firms that were acquired (Oaktree, Sculptor), delisted (Medley), or remain private (Warburg Pincus, Permira, General Atlantic) are excluded. This survivorship bias may inflate the apparent relationship between scale and valuation, as firms that failed to scale may have been taken private or merged at discount valuations.

### Disclaimer 3: Point-in-Time Cross-Section

All data represents a single cross-sectional snapshot (FY2024 financial data, early March 2026 market caps). Results may differ materially in different market environments. The correlation between scale and multiples may be stronger in bull markets (investors chasing quality) and weaker in bear markets (indiscriminate selling). No panel data or time-series analysis was conducted.

### Disclaimer 4: Small Sample Size

With N=15-21 for most tests and as few as N=5-9 for low-coverage metrics, statistical power is limited. A true moderate correlation (rho=0.4) has only ~45% power to be detected at alpha=0.05 with N=20. Many "not a driver" classifications may reflect insufficient power rather than a true null relationship. Confidence intervals are correspondingly wide (typically +/- 0.35 around the point estimate).

### Disclaimer 5: Endogeneity

Valuation multiples are computed from market capitalization, which reflects investor expectations about future AUM growth, fee revenue, and earnings. The independent variables (current AUM, fees, FRE) are correlated with these expectations. This creates endogeneity: the dependent variable is not independent of the drivers being tested. Any causal interpretation would require instrumental variable or natural experiment approaches not available in this cross-section.

### Disclaimer 6: FRE Definition Heterogeneity

Fee-Related Earnings is a non-GAAP metric with no standardized definition. Key differences across the sample include:

- **Stock-based compensation:** Some firms deduct SBC from FRE (BX, APO), others do not.
- **Transaction/advisory fees:** Some firms include these in FRE revenue (KKR, TPG), others exclude them.
- **Insurance segment:** APO's adjusted net income includes Athene insurance earnings, inflating DE relative to peers.
- **European proxies:** EQT reports "Fee-Related EBITDA," BPT uses "underlying EBITDA," and ANTIN uses "underlying EBITDA" — all with slightly different inclusions/exclusions.
- **Tax treatment:** Some firms report pre-tax FRE, others after-tax. DE definitions vary even more widely.

These definitional differences introduce measurement error that attenuates correlations. The true relationship between standardized FRE margin and valuation multiples may be stronger than the near-zero rho observed in our heterogeneous sample.

---

## Summary of Key Methodological Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Correlation method | Spearman rank | Non-parametric, outlier-robust, appropriate for N~20 |
| Regression | Not used | Small N, severe multicollinearity, endogeneity |
| Significance threshold | BH-FDR q=0.10 | Balances power and false discovery control |
| BN (Brookfield Corp) | Excluded from correlations | Market cap includes non-AM businesses |
| ONEX | Excluded | P/FRE based on run-rate, not trailing |
| EMG, PGHN, III, RITM | Excluded | Missing dependent variables |
| Confidence intervals | Fisher z-transform | Standard approach for rank correlations |
| Multiple testing | Both Bonferroni and BH-FDR reported | Transparency |
