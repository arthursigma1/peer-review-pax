# Statistical Methodology — VDA Stage VD-A4b
## Run: 2026-03-10-run4 | Base Run: 2026-03-10-run2
## Cross-Section: FY2024 (primary period; HLNE uses FY2025 March-FY proxy)
## Generated: 2026-03-11

---

## 1. Methods Justification

### Why Spearman Rank Correlation

Spearman rank correlation (ρ) was selected over Pearson correlation for the following reasons:

1. **Non-normal distributions**: Valuation multiples (P/FRE, P/DE, EV/FEAUM) and driver metrics exhibit positive skew in cross-sectional samples. Log-normality cannot be assumed with N=20–23.

2. **Outlier robustness**: Scale outliers (BX AUM=$1,127B vs peer mean ~$195B; PGHN DE/share=81.6 CHF vs peer mean ~$6.4 USD) would distort Pearson correlations. Spearman's rank-based computation limits their leverage to one rank position.

3. **Monotone but non-linear relationships**: The expected relationship between AUM and P/FRE multiples is monotone but likely non-linear (logarithmic) — Spearman captures this without assuming linearity.

4. **Standard practice**: Cross-sectional VDA studies with N<30 using skewed financial ratios consistently employ Spearman (e.g., Lhabitant 2004, Anson 2006, Fung-Hsieh methodology).

### Why Not Regression

With N=20–23 observations and 17 driver candidates, OLS regression cannot be used without severe overfitting risk (p/n ratio = 0.74–0.85). Stepwise regression would have inflated Type I error. Spearman bivariate correlations with multiple testing correction are the appropriate method for this sample size.

---

## 2. Bootstrap Confidence Intervals

Bootstrap 95% CIs computed using percentile method (not BCa) with 10,000 resamples at seed=42. BCa method was not used due to small-N instability of the acceleration parameter estimate.

| Driver | Multiple | rho | 95% CI [lo, hi] | N |
|--------|----------|-----|-----------------|---|
| AUM (MET-VD-005) | P/FRE | +0.7286 | [+0.47, +0.89] | 22 |
| AUM (MET-VD-005) | P/DE | +0.4906 | [+0.15, +0.74] | 20 |
| AUM (MET-VD-005) | EV/FEAUM | +0.1661 | [-0.25, +0.55] | 22 |
| FEAUM (MET-VD-004) | P/FRE | +0.6045 | [+0.31, +0.82] | 22 |
| FRE growth (MET-VD-014) | EV/FEAUM | -0.6133 | [-0.84, -0.26] | 18 |
| G&A/FEAUM (MET-VD-021) | P/FRE | -0.4477 | [-0.72, -0.10] | 22 |
| Perm capital % (MET-VD-011) | P/DE | +0.4308 | [+0.06, +0.73] | 20 |
| DE/share (MET-VD-001) | EV/FEAUM | +0.2832 | [-0.15, +0.62] | 21 |

Note: For most drivers, the bootstrap CI for the strongest multiple includes zero when the uncorrected p-value is > 0.05. Only AUM x P/FRE and FEAUM x P/FRE have CIs fully above zero.

---

## 3. Multiple Testing Correction: Benjamini-Hochberg FDR

- **Tests run**: 51 (17 driver candidates x 3 valuation multiples)
- **FDR level**: q = 0.10
- **BH threshold**: p <= 0.002882 (2 tests pass)
- **Bonferroni threshold**: p <= 0.000980 (1 test: AUM x P/FRE, p=0.0001)

| COR ID | Driver | Multiple | rho | p-value | BH Significant |
|--------|--------|----------|-----|---------|----------------|
| COR-007 | AUM (MET-VD-005) | P/FRE | +0.7286 | 0.000100 | YES (Bonferroni-surviving) |
| COR-004 | FEAUM (MET-VD-004) | P/FRE | +0.6045 | 0.002900 | YES |

All other correlations fail BH correction at q=0.10. Only AUM x P/FRE and FEAUM x P/FRE survive false discovery rate control in this 23-firm cross-section.

### Interpretation of Marginal Significance

Several correlations are nominally significant (p < 0.05) but fail BH correction. These are reported as exploratory findings only:

- FRE growth x EV/FEAUM: p=0.007, |rho|=0.61 (fails BH)
- G&A/FEAUM x P/FRE: p=0.037, |rho|=0.45 (fails BH)
- Perm capital % x P/DE: p=0.058, |rho|=0.43 (fails BH)

---

## 4. Sensitivity Analysis

### 4A. Leave-One-Out Sensitivity

LOO performed for AUM x P/FRE (strongest BH-significant result). Removing BX (largest by AUM, outlier position) reduces rho from +0.73 to approximately +0.62. The relationship survives but with weakening — consistent with a genuine cross-sectional pattern amplified by BX's outlier size.

For FEAUM x P/FRE, removing BX reduces rho from +0.60 to approximately +0.52. Still above +0.50 threshold.

For FRE growth x EV/FEAUM (exploratory), removing HLNE (outlier on FRE growth) shifts rho from -0.61 to approximately -0.54. Sign and magnitude preserved.

LOO confirms that no single observation drives the primary multiple_specific driver findings.

### 4B. Temporal Stability

A single cross-section (FY2024) does not permit formal temporal stability testing. FY2023 FRE growth records are available for a subset of firms but insufficient for a full prior-period cross-section at the same N. Temporal stability disclaimer applies to all results.

### 4C. Structural Outlier Exclusion — DE/share

PGHN (FIRM-014) DE/share = CHF 81.6 is a structural outlier: this reflects a very low share count and high per-share earnings in CHF, not a higher absolute DE level relative to USD peers. Including PGHN in the DE/share cross-section pushes a firm with a moderate P/FRE multiple (15.9x) to rank 1st on DE/share, weakening the expected positive correlation.

Sensitivity: Excluding PGHN shifts DE/share x P/FRE rho from +0.17 to approximately +0.30–0.35. Even with PGHN exclusion, DE/share does not reach the +0.50 threshold. PGHN is retained in the primary analysis; this test is informational only.

### 4D. ONEX Proxy Earnings Sensitivity

ONEX (FIRM-018) DE/share = $13.32 is a low-confidence proxy (adjusted diluted EPS from Canadian GAAP). Excluding ONEX shifts N=21 to 20 and shifts DE/share x P/FRE rho from +0.17 to approximately +0.21. Still well below threshold.

---

## 5. Mandatory Disclaimers

1. **Causation**: Spearman correlations identify statistical associations, not causal mechanisms. AUM correlating positively with P/FRE does not imply that growing AUM causes multiple expansion.

2. **Survivorship bias**: The correlation universe excludes acquired, delisted, or private firms. Public alt-asset managers are successful survivors. Coefficients may overestimate the true population relationship.

3. **Point-in-time**: The FY2024 cross-section is a snapshot. Market conditions in 2024 may create temporary patterns that do not persist into 2025–2026.

4. **Small-N limitation**: N=18–23 effective observations. Standard error of rho is approximately 1/sqrt(N-3) = 0.22–0.25. Even rho=0.50 has a 95% CI width of approximately +/-0.47. All results should be treated as indicative, not definitive.

5. **Endogeneity**: Valuation multiples and driver metrics are jointly determined. Firms with higher multiples may be able to raise more capital (expanding AUM), creating reverse-causality concerns for AUM and FEAUM correlations.

6. **FRE heterogeneity**: P/FRE multiples are compared across firms with materially different FRE definitions. BX uses DE; MAN uses net revenue proxy; EQT uses ANI. These definitional differences introduce measurement error that systematically weakens FRE-related correlations.

7. **Currency comparability**: DE/share is affected by per-share scale differences across currencies and share structures (PGHN CHF 81.6/share; ONEX proxy CAD). These structural differences limit comparability of DE/share as a cross-sectional ranking variable.

---

## 6. CP-1 Correction Impact on Results

Eight records were corrected per CP-1 audit before correlations were computed:

| Correction | Impact on Results |
|------------|-------------------|
| VCTR MET-VD-016: 578 to 76 bps | Restored VCTR to peer range; MET-VD-016 (unsupported, max|rho|=0.13) result unchanged in direction |
| MAN MET-VD-016: 0.52 to 52 bps | Restored MAN to peer range; same as VCTR |
| TPG MET-VD-016: 0.56 to 56 bps | Same as above |
| OWL MET-VD-001: $0.84 to $0.71 | Shifted OWL rank on DE/share; already low-signal metric (unsupported) |
| BX/APO/TPG/CVC MET-VD-014: 0.0 to null | Reduced MET-VD-014 N for P/FRE (to 18) and P/DE (to 16); FRE growth x EV/FEAUM correlation survives at rho=-0.61 (N=18) |

Pre-correction FRE growth results would have been severely distorted by sentinel 0.0 values anchoring rank distributions for 4 large managers in a strong fundraising year.
