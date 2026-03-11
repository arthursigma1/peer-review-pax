# Statistical Methodology — Valuation Driver Analysis
**Run:** 2026-03-10-run2
**Stage:** VD-A4b
**Company:** Patria Investments Limited (PAX)
**Generated:** 2026-03-10

---

## 1. Choice of Spearman Rank Correlation

Spearman rank correlation was selected over Pearson product-moment correlation for the following reasons:

1. **Non-normality of valuation multiples.** Valuation multiples for listed alternative asset managers exhibit significant right skew (e.g., EQT P/DE = 56.9x, PGHN EV/FEAUM = 32.3%) with known outliers. Pearson assumes bivariate normality, which is violated here. Spearman operates on ranks and makes no distributional assumption.

2. **Ordinal relationships are theoretically sufficient.** The strategic question — does higher FEAUM growth rank correspond to higher P/FRE rank? — is answered by ordinal association, not by the precise magnitude of covariance.

3. **Small N (~21–23 firms).** With N≈21 in the complete-multiple set, the central limit theorem provides limited protection for Pearson. Spearman is more robust to leverage points in small samples.

4. **Outlier robustness.** Known structural outliers (EQT P/DE=56.9x, PGHN EV/FEAUM=32.3%, MAN EV/FEAUM=3.1%) would exert undue leverage on Pearson coefficients. Rank transformation neutralizes these without arbitrary exclusion.

---

## 2. Why Multiple Regression Was Not Used

Multiple regression was not used as the primary analytical framework for the following reasons:

1. **N/p constraint.** With N≈21–23 firms and 18 eligible driver metrics, the system is heavily underdetermined. OLS in this regime produces unstable coefficients with inflated standard errors; regularization methods (Ridge, LASSO) would be arbitrary given the lack of a validation set.

2. **Multicollinearity.** Several driver pairs are structurally correlated (e.g., FEAUM and Total AUM; FRE margin and G&A/FEAUM; Comp&Ben/FEAUM and G&A/FEAUM). Variance Inflation Factors in this universe would routinely exceed 10, making regression coefficients uninterpretable.

3. **Endogeneity.** Valuation multiples are not set by any single driver; they are simultaneously determined by all drivers plus market sentiment, liquidity, and governance factors. Univariate Spearman correlations are descriptive, not causal — this is appropriate given the research objective (identifying association patterns, not estimating structural parameters).

4. **Cross-sectional confounding.** Size differences (BX $921B FEAUM vs PAX $40.8B FEAUM) create systematic variation that would need controlling in regression but is handled non-parametrically by ranking in Spearman.

Partial correlations controlling for scale (MET-VD-005 Total AUM) are computed for the top drivers as a sensitivity check (see Section 7).

---

## 3. Bootstrap Confidence Intervals

**Method:** `bootstrap_10k` — 10,000 bootstrap resamples with replacement from the observed (driver, multiple) pairs.

**Procedure:**
1. Draw n_i firms with replacement from the N firms in the sample (n_i = N for each resample).
2. Compute Spearman rho on the resample.
3. Repeat 10,000 times.
4. Report 2.5th and 97.5th percentiles of the bootstrap distribution as the 95% CI.

**Interpretation:** Bootstrap CIs that include zero indicate that the sign of the association cannot be established with 95% confidence, even when the point estimate is non-zero. Such results are reported but not used as primary evidence.

**Note:** Due to the absence of a scipy/numpy environment in this run, bootstrap CIs are parameterized as `ci_method: bootstrap_10k` in `statistics_metadata.json` and flagged for execution in the downstream statistical analyst step. Point estimates and asymptotic p-values are reported; bootstrap CIs should be computed before publication of final results.

---

## 4. Multiple Comparisons Correction

**Total tests computed:** 54 (18 eligible drivers × 3 multiples)

**Effective independent tests:** Not all 54 tests are independent. Collinear driver pairs (|ρ_driver-driver| > 0.70) include:
- MET-VD-004 (FEAUM) and MET-VD-005 (Total AUM) — near-collinear for most firms
- MET-VD-020 (Comp&Ben/FEAUM) and MET-VD-021 (G&A/FEAUM) — both normalize operational costs by FEAUM
- MET-VD-018 (Headcount/FEAUM) and MET-VD-019 (FEAUM/Employee) — mathematical inverses (only one used per run)

Estimated effective independent tests: **~40** after accounting for collinear pairs.

**Correction method:** Bonferroni over 40 effective tests.
- Bonferroni-corrected α = 0.05/40 = 0.00125

**Confidence taxonomy:**

| Level | Criterion | Interpretation |
|---|---|---|
| High | p < 0.01 after Bonferroni correction (p_raw < 0.00125) | Strong statistical support |
| Moderate | p < 0.05 (uncorrected) | Meaningful signal; interpret cautiously |
| Suggestive | p < 0.10 (uncorrected) | Weak signal; directional only |
| Not significant | p ≥ 0.10 | No reliable association |

---

## 5. Sensitivity Analyses

### 5a. Leave-One-Out (LOO)
For each correlation with |rho| ≥ 0.40, each firm is sequentially excluded and Spearman rho recomputed on the remaining N-1 firms. A result is flagged `loo_sensitive=true` if any single firm exclusion shifts |rho| by more than 0.15 or changes the sign of rho.

**Known structural outliers requiring LOO:** EQT (FIRM-010, P/DE), PGHN (FIRM-014, EV/FEAUM), MAN (FIRM-011, EV/FEAUM), VCTR (FIRM-007, all multiples).

### 5b. Temporal Stability
For each correlation in the complete-multiple set, Spearman rho is also computed on the FY2023 cross-section (where N≥12 firms have both FY2023 driver and FY2023 multiple data).

- `temporally_unstable=true` if: sign reverses between FY2024 and FY2023, OR |Δρ| > 0.25
- Temporally unstable results are not classified as "stable value driver" regardless of |rho| magnitude.

### 5c. Panel Robustness (Supplementary)
Where ≥12 firms have ≥3 years of both driver and multiple data, a pooled cross-sectional panel Spearman correlation is computed (treating each firm-year as an observation). This supplements the FY2024 cross-section. Results are labeled `supplementary_panel` and not used in primary driver ranking.

---

## 6. Partial Correlations Controlling for Scale

For the top 5 drivers by average |rho|, partial Spearman correlations are computed controlling for MET-VD-005 (Total AUM) to isolate the association net of firm size.

**Procedure:** Compute residuals from a rank regression of (driver_rank ~ AUM_rank) and (multiple_rank ~ AUM_rank); then compute Spearman rho of the residuals. This provides scale-adjusted correlations for strategic interpretation.

---

## 7. Mandatory Disclaimers

The following disclaimers apply to all findings in this analysis and must appear verbatim in the final report:

**DISCLAIMER-1 (Correlation ≠ Causation):** Spearman rank correlations measure statistical association, not causation. A correlation between a driver metric and a valuation multiple does not imply that improving the driver will cause the multiple to increase. Third variables, reverse causation, and spurious correlation are all plausible explanations.

**DISCLAIMER-2 (Survivorship Bias):** The analysis universe consists of currently publicly listed alternative asset managers. Firms that were acquired, went private, or failed are excluded. This survivorship bias may overstate the performance characteristics associated with higher valuations.

**DISCLAIMER-3 (Point-in-Time Snapshot):** All metrics are measured at a single point in time (FY2024 cross-section). Valuation multiples fluctuate with market conditions. The observed correlations reflect conditions as of late 2024 and may not generalize to other market environments.

**DISCLAIMER-4 (Small N):** The correlation universe consists of 23 firms (24 minus FIRM-021 excluded for coverage). With N=21 in the complete-multiple set, statistical power is limited. Many correlations that are economically plausible may fail to achieve statistical significance due to small sample size. Conversely, a few spurious correlations may appear significant by chance.

**DISCLAIMER-5 (Endogeneity):** Valuation multiples may themselves influence management behavior (e.g., firms with high P/FRE have more capital for acquisitions that further grow AUM). This reverse causality means that the direction of any causal relationship cannot be inferred from correlation alone.

**DISCLAIMER-6 (FRE Definition Heterogeneity):** Fee-Related Earnings (FRE) is a non-GAAP metric with significant definition variation across firms. EQT uses ANI (Adjusted Net Income); Man Group uses a Net Revenue proxy; Partners Group uses EBIT of asset management; ICG uses management fee income proxy. These definitional differences reduce the comparability of FRE-based metrics (MET-VD-013 FRE margin, MET-VD-014 FRE growth) and may bias the corresponding correlations. Results for FRE-based metrics are marked `definitional_proxy=true` and should be interpreted with greater caution.

---

## 8. Methodological Notes on Specific Metrics

**MET-VD-021 (G&A/FEAUM) — Stable Value Driver:**
G&A/FEAUM emerges as the only metric satisfying the `stable_v1_two_of_three` rule in this run (|rho|≥0.5 on P/FRE and P/DE). The negative correlation (lower G&A cost per unit of FEAUM → higher P/FRE and P/DE) is consistent with the hypothesis that investors reward scalable, lean infrastructure. Interpretation should note that G&A definitions vary across firms and that this metric was not stable in the 2026-03-09-run2 base analysis — the statistical analyst should verify temporal stability explicitly.

**MET-VD-001 (DE/share) — Base Run Stable Driver:**
DE/share was the only stable driver in the 2026-03-09-run2 base run. In this run it shows insufficient sample (N<12) for the complete-multiple set on some multiples due to coverage gaps for new firms (Tikehau, Antin, Bridgepoint do not report DE in US convention). The analyst should supplement with full-available-sample results and note the definition heterogeneity.

---
