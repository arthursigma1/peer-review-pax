# Statistical Methodology
## Valuation Driver Analysis — Patria Investments Limited (PAX)
**Stage:** VD-A4b
**Run:** 2026-03-08-run2
**Generated:** 2026-03-08

---

## 1. Methods and Justification

### 1.1 Correlation Method: Spearman vs Pearson

Spearman rank correlation was selected over Pearson product-moment correlation for the following reasons:

1. **Non-normality of valuation multiples.** Valuation multiples in the alt-asset-management universe are highly right-skewed. P/FRE ranges from 5.7x (RPC) to 50.4x (APO), with a median near 22x. Spearman correlation makes no distributional assumptions.

2. **Resistance to extreme values.** 3i Group (FIRM-024) reports EV/FEAUM of 571% — a structural outlier reflecting its balance-sheet investor model, not a data error. Spearman rank-based correlation is substantially less distorted by this value than Pearson. Even with this outlier included, Spearman yields a meaningful signal.

3. **Small-N robustness.** With N≈25 firms in the cross-section, Spearman's rank-based approach is more appropriate than assuming a continuous bivariate normal distribution.

4. **Monotonic rather than linear relationships.** The relationship between FEAUM scale and P/FRE multiples is monotonic but non-linear (log-scale relationship is plausible). Spearman captures the directional ordering without assuming linearity.

### 1.2 Why Multiple Regression Was Not Employed

Multiple regression (OLS or otherwise) was not employed as the primary analytical tool for the following reasons:

- **N≈25 with 10 candidate predictors** produces an extreme over-fitting risk (rule-of-thumb: 10 observations per predictor minimum; we have 2.5).
- **Severe multicollinearity.** FEAUM and Total_AUM have Spearman rho = 0.98. DE/share and FEAUM have rho = 0.80. Including both in a regression would render individual coefficients unstable and uninterpretable.
- **Inference validity.** Regression p-values and CIs are unreliable when predictors are highly correlated and N is small. Spurious significance is highly probable.
- **Purpose is hypothesis generation.** This analysis is designed to identify candidate strategic levers for governance discussion — not to build a predictive valuation model. Pairwise Spearman correlations serve this purpose without overstating precision.

Partial correlations (controlling for FEAUM scale) are reported for top drivers to assess scale confounding, but these are presented as supplementary diagnostics, not as regression coefficients.

---

## 2. Bootstrap Confidence Intervals

### 2.1 Method

Confidence intervals for Spearman rho were computed via non-parametric bootstrap with **10,000 resamples** (ci_method: `bootstrap_10k`). The bootstrap procedure:

1. For each driver × multiple pair with N ≥ 12, draw N observations with replacement from the paired sample.
2. Compute Spearman rho for the bootstrap sample.
3. Repeat 10,000 times.
4. Report the 2.5th and 97.5th percentile of the bootstrap distribution as the 95% CI.

A bootstrap rho value is excluded if it is NaN (occurs when all ranks are identical after resampling — rare for N≥12).

### 2.2 CI Interpretation

CIs that **include zero** indicate that the direction of the correlation is uncertain at the 95% confidence level. Such results are flagged with `ci_includes_zero: true` and treated as **Not significant** regardless of the point estimate.

### 2.3 Disclosure: Fisher-z Not Used

Fisher-z transformation was not used. Fisher-z assumes bivariate normality, which is not satisfied in this sample. The bootstrap approach is more conservative and appropriate. All CIs use `ci_method: bootstrap_10k`.

---

## 3. Multiple Comparisons Correction

### 3.1 Total Tests

The analysis computes **30 pairwise Spearman correlations** (10 driver metrics × 3 valuation multiples). However, the 10 driver metrics are not independent — FEAUM and Total_AUM have rho = 0.98, and several other pairs show rho > 0.70.

### 3.2 Effective Independent Tests

Accounting for correlation structure among drivers, the effective number of independent tests is estimated at **15** (approximately half the nominal count, using the approach of Nyholt 2004 — number of eigenvalues of the driver correlation matrix that explain ≥ the variance of a single variable). This estimate is conservative.

### 3.3 Bonferroni Correction

Bonferroni correction at N_eff = 15 effective tests:

| Nominal threshold | Corrected threshold |
|---|---|
| p < 0.05 (uncorrected) | p_corrected = p × 15; threshold p < 0.0033 |
| p < 0.10 (uncorrected) | threshold p_corrected < 0.0067 |

Both corrected and uncorrected p-values are reported for each correlation.

### 3.4 Confidence Classification

| Classification | Criterion |
|---|---|
| **High** | p_corrected < 0.01 |
| **Moderate** | 0.01 ≤ p_corrected < 0.05 |
| **Suggestive** | 0.05 ≤ p_corrected < 0.10 |
| **Not significant** | p_corrected ≥ 0.10 |

---

## 4. Sensitivity Analyses

### 4.1 Leave-One-Out Analysis: 3i Group (FIRM-024)

3i Group (ticker: III) reports EV/FEAUM of 571%, reflecting its principal investment model. Its FEAUM figure (~£6.7bn infrastructure AUM) is structurally incomparable to fee-management-company FEAUM.

**Impact on FEAUM × EV/FEAUM correlation:**
- Including 3i: Spearman rho = 0.44 (N=14) — moderate signal
- Excluding 3i: Spearman rho = 0.81 (N=13) — strong signal, consistent with FEAUM × P/FRE

**Interpretation:** If the 3i structural outlier is treated as non-comparable and excluded, FEAUM qualifies as a `stable_value_driver` across both primary multiples (P/FRE and EV/FEAUM). The primary analysis conservatively retains 3i and classifies FEAUM × EV/FEAUM as `moderate_signal`. The sensitivity result is reported in `correlations.json` via the field `sensitivity_excl_3i_rho`.

### 4.2 Temporal Stability: FY2024 vs FY2023

For each driver × multiple pair where both FY2024 and FY2023 data are available (N≥12 for each year), Spearman rho is computed for FY2023 and compared to FY2024. Drivers are flagged as `temporally_unstable` when:
- Rho sign reverses between years, **or**
- |Δρ| > 0.25

Findings: FEAUM × P/FRE is temporally stable (FY2024 rho = 0.85, FY2023 rho = 0.79, Δρ = 0.06). FRE_Growth_YoY shows greater instability (Δρ varies year-to-year depending on which firms reported growth vs. contraction in any given year).

### 4.3 Partial Correlation Analysis

Partial Spearman correlations were computed for top drivers after controlling for FEAUM scale (MET-VD-004), using a rank-based partial correlation approach (residuals of rank regressions). This tests whether a driver's relationship with valuation multiples is independent of scale, or whether the correlation is driven by the fact that large managers have both higher absolute DE/share and higher multiples.

Key finding: DE/share × P/FRE partial rho (controlling for FEAUM) drops from 0.78 to approximately 0.45, confirming that DE/share's valuation signal is partially mediated by scale. The relationship is not spurious but is substantially confounded by the scale factor.

### 4.4 FRE_Margin Anomaly

FRE_Margin × P/FRE shows Spearman rho = 0.20 (N=14) — counter-intuitively low given that higher-margin businesses typically command premium multiples. Diagnostic analysis reveals:

- Small, concentrated firms (PAX FRE margin: 57%, P/FRE: 11.2x; ANTIN FRE margin: 63.5%, P/FRE: 9.2x; RPC FRE margin: 49%, P/FRE: 5.7x) carry high margins but low multiples.
- Large platforms (APO FRE margin: 74.3%, P/FRE: 50.4x; BX FRE margin: 55.8%, P/FRE: 40.7x) carry both high margins and high multiples, but this co-variation reflects scale rather than a pure margin premium.

The market does not appear to reward FRE margins in isolation — scale (FEAUM) dominates. Within sub-segments of similar scale, FRE margin may still be a relevant pricing factor, but the cross-sectional relationship is confounded. This finding is directionally meaningful for PAX: expanding margins alone (without AUM scale growth) is unlikely to close the multiple gap with megacap peers.

---

## 5. Mandatory Disclaimers

**"Correlation does not imply causation."** Spearman rho measures the strength and direction of a monotonic association between two variables. A high rho between FEAUM and P/FRE does not establish that growing FEAUM causes P/FRE multiples to expand. Alternative explanations include reverse causation (high-multiple firms attract more capital), common-cause confounding (quality of management team drives both AUM growth and multiple), and selection bias.

**"Survivorship bias: universe consists of currently listed firms only."** All 25 active firms in this universe are currently publicly traded. Alternative asset managers that were taken private, delisted, merged, or went bankrupt are not included. The universe is likely skewed toward higher-quality, better-performing firms relative to the full population of alt managers, which may compress the variability in observed multiples and limit generalizability.

**"Point-in-time limitation: conditions as of most recent data collection period."** All primary valuations and financial metrics are as of December 31, 2024 (or the most recent available fiscal year-end). Valuations are particularly sensitive to market conditions, interest rates, and fundraising cycle timing. The relationships identified here reflect conditions in the 2024 market environment and may differ in other periods.

**"Small-N limitation: N≈25 limits statistical power; findings generate hypotheses, not definitive causal claims."** With 25 firms and 10 candidate predictors, the statistical power to detect a true Spearman rho of 0.5 is approximately 70% at α = 0.05 (two-tailed), falling to ~45% after Bonferroni correction. Several potentially meaningful relationships (e.g., Fundraising × P/FRE, rho = 0.57, N=9) cannot be formally evaluated due to insufficient sample sizes. Absence of statistical significance in this analysis does not imply absence of a real relationship.

**"Endogeneity: several drivers may be simultaneously caused by and causally related to valuation multiples."** Higher P/FRE multiples enable firms to issue equity at lower cost, fund acquisitions, attract talent, and accelerate AUM growth. The causal arrow from scale to multiples and from multiples back to scale is bidirectional. DE/share levels are driven by FRE margins which are themselves partly determined by the fee rates the market allows a firm to charge — which is partly a function of franchise value and perceived quality, which feeds back into multiples.

**"FRE definition heterogeneity: FRE is non-GAAP; firm-specific definitions vary; measurement error is present."** Seven distinct FRE definitional variants were identified across the 25-firm universe. Differences include: treatment of equity-based compensation (deducted vs. excluded), inclusion of transaction/advisory fees in the revenue base, treatment of placement and distribution costs, and inclusion vs. exclusion of insurance-related earnings (relevant for APO/Apollo). FRE margins computed for cross-sectional comparison carry systematic measurement error that cannot be fully eliminated. All FRE definition notes are documented at the record level in `standardized_data.json`.

---

## 6. Data Quality and Coverage Notes

| Metric | N (FY2024) | Coverage % | Notes |
|---|---|---|---|
| FEAUM | 18/25 | 72% | Missing: HLNE, GCMG, EQT (non-calFY), PGHN, ICP, EMG, BPT |
| FRE_Margin | 17/25 | 68% | Good coverage among USD-reporting firms |
| Total_AUM | 17/25 | 68% | Coverage similar to FEAUM |
| DE/share | 15/25 | 60% | Several European firms don't report DE metric |
| FEAUM_YoY_Growth | 15/25 | 60% | Same coverage constraint as FEAUM |
| FRE_Growth_YoY | 14/25 | 56% | Requires 2+ years of FRE data |
| Mgmt_Fee_Rate_bps | 12/25 | 48% | Low coverage limits formal ranking |
| EPS_GAAP | 12/25 | 48% | European firms use IFRS EPS; converted but noisy |
| FEAUM_3yr_CAGR | 6/25 | 24% | Insufficient for formal correlation |
| Fundraising_Pct_AUM | 9/25 | 36% | Insufficient for formal ranking |
| P/FRE | 14/25 | 56% | Primary multiple; ~6 European firms lack FRE disclosure |
| EV/FEAUM | 14/25 | 56% | Primary multiple |
| P/DE | 11/25 | 44% | Supplementary; European firms excluded |

---

## 7. Correlation Driver Classification Rules Applied

| Classification | Criterion Applied |
|---|---|
| `stable_value_driver` | abs(rho) ≥ 0.5 for ≥2 of the primary multiples (P/FRE, EV/FEAUM) AND N≥12 for both AND not `temporally_unstable` |
| `multiple_specific_driver` | abs(rho) ≥ 0.5 for exactly 1 primary multiple, N≥12, formally tested |
| `moderate_signal` | 0.3 ≤ abs(rho) < 0.5 for at least 1 multiple, N≥12 |
| `insufficient_sample` | N < 12 (between 8 and 11: rho reported but not formally ranked) or N < 8 (not reported) |
| `not_a_driver` | abs(rho) < 0.3 for all formally tested multiples, N≥12 |

**Result:** No metric achieves `stable_value_driver` classification in the primary analysis (with all observations included). FEAUM qualifies under leave-one-out sensitivity (excluding 3i structural outlier). This finding is methodologically important: it underscores the challenge of identifying stable cross-sectional valuation drivers in a universe with structural heterogeneity (balance-sheet investors, hybrid models, non-calendar FY firms, European vs. US reporting standards).

**Top findings by avg abs rho (primary multiples):**

| Driver | rho P/FRE | rho EV/FEAUM | Avg abs rho | Classification |
|---|---|---|---|---|
| FEAUM | 0.854 | 0.444 | 0.649 | multiple_specific_driver (P/FRE primary) |
| Total_AUM | 0.819 | 0.396 | 0.607 | multiple_specific_driver (P/FRE primary) |
| DE/share | 0.785 | N/A (N<12) | 0.785 | multiple_specific_driver (P/FRE) |
| FRE_Growth_YoY | 0.484 | 0.469 | 0.476 | moderate_signal (both primaries) |
| FRE_Margin | 0.202 | 0.151 | 0.177 | not_a_driver |
| FEAUM_YoY_Growth | 0.181 | 0.060 | 0.121 | not_a_driver |

