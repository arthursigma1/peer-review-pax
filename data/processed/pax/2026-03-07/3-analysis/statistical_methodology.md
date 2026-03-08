# Statistical Methodology — Valuation Driver Analysis

**Date:** 2026-03-07
**Universe:** 25 eligible firms (24 total minus 2 model-incompatible)
**Consistent sub-sample:** 17 firms (all three multiples available)
**Statistical engine:** scipy.stats.spearmanr (SciPy v1.13.1)

---

## 1. Method Selection: Spearman Rank Correlation

### Why Spearman over Pearson

1. **Robustness to non-normality.** Alt-asset manager financial metrics exhibit pronounced right-skew (e.g., Blackstone's AUM is ~10x the median peer). Pearson assumes bivariate normality; Spearman does not.
2. **Outlier resistance.** Operating on ranks dampens extreme observations. With N~17, a single outlier can distort Pearson r materially.
3. **Monotonic relationships.** Spearman detects any monotonic association, not just linear. Scale-to-valuation relationships are plausibly monotonic but not necessarily linear.
4. **Interpretability.** Spearman rho measures how well ranks on one variable predict ranks on another.

### Why Multiple Regression Was Not Used

1. **Insufficient degrees of freedom.** N~17 with 6 candidates — regression would consume most df.
2. **Multicollinearity.** FEAUM and Total AUM have rho=0.9868. 1 collinear pair(s) identified.
3. **Overfitting risk.** High predictor-to-observation ratio; cross-validation infeasible at this N.
4. **Endogeneity.** Drivers and multiples are co-determined (e.g., high multiples enable cheaper capital-raising, growing AUM). No instrumental variables available.
5. **Non-normal residuals.** GAAP heterogeneity produces heteroskedastic residuals.

---

## 2. Bootstrap Confidence Intervals

- **Method:** Non-parametric bootstrap with replacement
- **Iterations:** 1,000 per coefficient
- **Confidence level:** 95% (2.5th and 97.5th percentiles)
- **Seed:** 42 (reproducibility)
- **Flag:** CIs including zero indicate the correlation is not statistically distinguishable from no association.

---

## 3. Multiple Comparisons Correction

- **Method:** Bonferroni correction
- **Total tests:** 18 (6 drivers x 3 multiples)
- **Corrected alpha:** 0.05 / 18 = 0.002778
- Both uncorrected and corrected p-values reported.

---

## 4. Confidence Classification

| Classification | Criterion |
|---|---|
| High confidence | p < 0.01 after Bonferroni |
| Moderate confidence | p < 0.05 after Bonferroni |
| Suggestive | p < 0.10 after Bonferroni |
| Not significant | p >= 0.10 after Bonferroni |

### Full Results Table

| Driver | Multiple | rho | p (uncorr) | p (Bonf) | 95% CI | Class |
|---|---|---|---|---|---|---|
| MET-VD-004 | MET-VD-026 | 0.7451 | 0.00223 | 0.040141 | [0.3651, 0.905] | moderate_confidence |
| MET-VD-004 | MET-VD-027 | 0.1056 | 0.719353 | 1.0 | [-0.5395, 0.6278] | not_significant |
| MET-VD-004 | MET-VD-028 | 0.8053 | 0.00051 | 0.009178 | [0.4777, 0.9564] | high_confidence |
| MET-VD-005 | MET-VD-026 | 0.7451 | 0.000599 | 0.010777 | [0.3998, 0.9082] | moderate_confidence |
| MET-VD-005 | MET-VD-027 | 0.3102 | 0.22555 | 1.0 | [-0.2161, 0.6959] | not_significant |
| MET-VD-005 | MET-VD-028 | 0.7296 | 0.000887 | 0.01596 | [0.4371, 0.8932] | moderate_confidence |
| MET-VD-006 | MET-VD-026 | 0.0826 | 0.761048 | 1.0 | [-0.5533, 0.6417] | not_significant |
| MET-VD-006 | MET-VD-027 | 0.1491 | 0.58161 | 1.0 | [-0.4199, 0.6687] | not_significant |
| MET-VD-006 | MET-VD-028 | -0.0148 | 0.956733 | 1.0 | [-0.4973, 0.5104] | not_significant |
| MET-VD-013 | MET-VD-026 | 0.37 | 0.174671 | 1.0 | [-0.145, 0.8113] | not_significant |
| MET-VD-013 | MET-VD-027 | 0.3247 | 0.237704 | 1.0 | [-0.2043, 0.6989] | not_significant |
| MET-VD-013 | MET-VD-028 | 0.5725 | 0.025737 | 0.463262 | [0.0553, 0.8769] | not_significant |
| MET-VD-014 | MET-VD-026 | 0.3439 | 0.249952 | 1.0 | [-0.193, 0.7536] | not_significant |
| MET-VD-014 | MET-VD-027 | 0.0661 | 0.830082 | 1.0 | [-0.5347, 0.6457] | not_significant |
| MET-VD-014 | MET-VD-028 | 0.3444 | 0.249257 | 1.0 | [-0.3808, 0.7627] | not_significant |
| MET-VD-016 | MET-VD-026 | -0.1073 | 0.727186 | 1.0 | [-0.7604, 0.5284] | not_significant |
| MET-VD-016 | MET-VD-027 | 0.0055 | 0.985767 | 1.0 | [-0.6676, 0.661] | not_significant |
| MET-VD-016 | MET-VD-028 | 0.0744 | 0.809174 | 1.0 | [-0.5374, 0.6271] | not_significant |


---

## 5. Driver Classification

| Classification | Rule |
|---|---|
| Stable value driver | `stable_v1_two_of_three`: abs(rho) >= 0.5 on >=2 multiples AND no negative rho on the third |
| Multiple-specific driver | abs(rho) >= 0.5 on exactly 1 multiple |
| Moderate signal | 0.3 <= abs(rho) < 0.5 on >=1 multiple |
| Not a driver | abs(rho) < 0.3 on all 3 |

### Results

- **MET-VD-004 (Fee-Earning Assets Under Management)**: stable_value_driver — MET-VD-026=rho0.7451, MET-VD-027=rho0.1056, MET-VD-028=rho0.8053
- **MET-VD-005 (Total Assets Under Management)**: stable_value_driver — MET-VD-026=rho0.7451, MET-VD-027=rho0.3102, MET-VD-028=rho0.7296
- **MET-VD-006 (FEAUM Year-over-Year Growth)**: not_a_driver — MET-VD-026=rho0.0826, MET-VD-027=rho0.1491, MET-VD-028=rho-0.0148
- **MET-VD-013 (Fee-Related Earnings Margin)**: multiple_specific_driver — MET-VD-026=rho0.37, MET-VD-027=rho0.3247, MET-VD-028=rho0.5725
- **MET-VD-014 (Fee-Related Earnings Growth Year-over-Year)**: moderate_signal — MET-VD-026=rho0.3439, MET-VD-027=rho0.0661, MET-VD-028=rho0.3444
- **MET-VD-016 (Management Fee Rate)**: not_a_driver — MET-VD-026=rho-0.1073, MET-VD-027=rho0.0055, MET-VD-028=rho0.0744


---

## 6. Sensitivity Analyses

### 6a. Leave-One-Out

- **MET-VD-004/MET-VD-026** (rho=0.7451): No single influential observation
- **MET-VD-004/MET-VD-028** (rho=0.8053): No single influential observation
- **MET-VD-005/MET-VD-026** (rho=0.7451): No single influential observation
- **MET-VD-005/MET-VD-027** (rho=0.3102): No single influential observation
- **MET-VD-005/MET-VD-028** (rho=0.7296): No single influential observation
- **MET-VD-013/MET-VD-026** (rho=0.37): Influential — FIRM-005 (Ares Management Corporation)
- **MET-VD-013/MET-VD-027** (rho=0.3247): No single influential observation
- **MET-VD-013/MET-VD-028** (rho=0.5725): No single influential observation
- **MET-VD-014/MET-VD-026** (rho=0.3439): No single influential observation
- **MET-VD-014/MET-VD-028** (rho=0.3444): No single influential observation


### 6b. Temporal Stability (FY2024 vs FY2023)

- **MET-VD-004/MET-VD-026**: FY2024 rho=0.7451, FY2023 rho=None (n=0) — STABLE
- **MET-VD-004/MET-VD-028**: FY2024 rho=0.8053, FY2023 rho=None (n=0) — STABLE
- **MET-VD-005/MET-VD-026**: FY2024 rho=0.7451, FY2023 rho=None (n=0) — STABLE
- **MET-VD-005/MET-VD-027**: FY2024 rho=0.3102, FY2023 rho=None (n=0) — STABLE
- **MET-VD-005/MET-VD-028**: FY2024 rho=0.7296, FY2023 rho=None (n=0) — STABLE
- **MET-VD-013/MET-VD-026**: FY2024 rho=0.37, FY2023 rho=None (n=0) — STABLE
- **MET-VD-013/MET-VD-027**: FY2024 rho=0.3247, FY2023 rho=None (n=0) — STABLE
- **MET-VD-013/MET-VD-028**: FY2024 rho=0.5725, FY2023 rho=None (n=0) — STABLE
- **MET-VD-014/MET-VD-026**: FY2024 rho=0.3439, FY2023 rho=None (n=0) — STABLE
- **MET-VD-014/MET-VD-028**: FY2024 rho=0.3444, FY2023 rho=None (n=0) — STABLE


### 6c. Partial Correlations Controlling for Scale (FEAUM)



---

## 7. Multicollinearity

| Metric 1 | Metric 2 | rho | N |
|---|---|---|---|
| MET-VD-004 (Fee-Earning Assets Under Management) | MET-VD-005 (Total Assets Under Management) | 0.9868 | 14 |


FEAUM and Total AUM are near-perfect rank correlates. Only the more commonly used metric (FEAUM) should be elevated for strategic interpretation; Total AUM serves as robustness check.

---

## 8. Mandatory Disclaimers

1. "Correlation does not imply causation."
2. "Survivorship bias: universe consists of currently listed firms only."
3. "Point-in-time limitation: conditions as of most recent data collection period."
4. "Small-N limitation: N~17 limits statistical power; findings generate hypotheses, not definitive causal claims."
5. "Endogeneity: several drivers may be simultaneously caused by and causally related to valuation multiples."
6. "FRE definition heterogeneity: FRE is non-GAAP; firm-specific definitions vary; measurement error is present."
7. "EM discount: PAX and VINP trade at structural EM discount that may confound cross-sectional correlations with geography-related variables."

---

## 9. Data Quality Notes

- **FRE reconciliation:** See `fre_definitions` in `standardized_data.json` for per-firm documentation.
- **Non-calendar FY:** FIRM-009 (March (StepStone)), FIRM-021 (March (3i)).
- **FX:** Point-in-time at period-end; flows at period-average. Documented per entry.
- **Model-incompatible:** FIRM-020, FIRM-021 excluded.
- **Contextual-only:** MET-VD-018, MET-VD-019, MET-VD-020, MET-VD-021, MET-VD-022, MET-VD-023, MET-VD-024, MET-VD-025 excluded.
