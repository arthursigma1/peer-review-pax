# VDA Methodology Review

**Reviewer:** Methodology Reviewer Agent
**Date:** 2026-03-06
**Pipeline:** Valuation Driver Analysis (VDA) for Patria Investments Limited (PAX)
**Files Reviewed:** All 16 pipeline output files (VD-A0 through VD-P3) + design document

---

## Executive Summary

- **The hybrid approach is sound**: separating quantitative (Track A) from qualitative (Track B) analysis is the correct response to a universe of N~25 firms, and the justification for rejecting multiple regression is rigorous and well-documented.
- **The dominant finding — scale dominance — rests on a methodologically fragile foundation**: all five "stable drivers" are multicollinear at rho > 0.91, meaning the analysis identifies one factor dressed in five costumes, not five independent drivers. The driver classification framework rewards this redundancy as if it were corroboration.
- **Critical data gaps undermine several candidate drivers**: organic growth (N=6), comp ratio (N=5–7), asset class HHI (N=6), and performance fee share (N=7–9) have sample sizes so small that "not a driver" classifications are almost certainly false negatives, not true nulls. These metrics cannot be scientifically evaluated at N<10.
- **The bootstrap CI methodology diverges from what was promised**: VD-A4b uses Fisher z-transformation rather than the 1,000-iteration bootstrap specified in the design document. This is a material deviation that should be disclosed and justified.
- **The valuation multiple selection contains a structural flaw**: including both P/FRE and EV/FEAUM when the numerators (market cap and enterprise value) differ only by net debt creates quasi-circular tests when FRE and FEAUM are themselves highly correlated.
- **Reproducibility is partially achieved**: the methodology is well-documented for the statistical choices made, but critical data extraction rules (e.g., how to compute organic growth, how to classify permanent capital) lack enough precision for an independent analyst to replicate the dataset without judgment calls.

---

## Statistical Methodology Assessment

### Strengths

**Spearman over Pearson is correct.** The right-skewed distribution of valuation multiples (P/FRE range: 6.4x–31.5x; EV/FEAUM: 3.2%–21.7%) and the extreme scale disparity across firms (BX $7.1B in fees vs. PX $291M) make Pearson correlation unsuitable. Spearman's rank-based approach is robust to both non-normality and outlier leverage. The justification in VD-A4b is thorough and cites all three relevant reasons (non-normality, outlier robustness, monotonic relationships).

**The regression rejection is well-argued.** Section 2.2 of the design document and Section 2 of VD-A4b correctly identify four independent reasons not to use multiple regression: degrees-of-freedom constraint, severe multicollinearity, overfitting risk, and endogeneity. This reasoning is consistent and reproducible.

**Multiple testing correction uses both methods.** Reporting both Bonferroni and Benjamini-Hochberg FDR provides transparency and lets readers apply their preferred conservatism level. The selection of BH-FDR at q=0.10 as the primary framework for an exploratory, hypothesis-generating analysis is defensible.

**Multicollinearity is documented.** The analysis explicitly identifies and documents 11 collinear pairs (all with rho > 0.89) in VD-A4. This is methodologically honest and prevents the reader from treating five correlated scale metrics as five independent pieces of evidence.

**Mandatory disclaimers are complete and well-calibrated.** All six design-specified disclaimers (causation, survivorship, point-in-time, small N, endogeneity, FRE heterogeneity) are reproduced faithfully in both VD-A4b and VD-P1. The VD-P1 principle documents correctly carry these caveats forward.

**Leave-one-out analysis is directionally appropriate.** For the three top stable drivers, LOO analysis is performed with specific estimated impact ranges (typically -0.03 to -0.05 per firm removed). The conclusion that no single firm drives the scale results is reasonable.

### Gaps and Recommendations

**Gap 1: Bootstrap CIs promised, Fisher z delivered.**
The design document (Section 4.1, VD-A4b) specifies "1,000 bootstrap iterations per correlation coefficient." VD-A4b instead uses Fisher z-transformation throughout. These two approaches should yield similar point estimates but can differ materially for small N and non-normal data — precisely the conditions present here. The deviation is undocumented. Either implement the bootstrap as specified and compare results, or explicitly note in VD-A4b that Fisher z was substituted and provide a rationale (e.g., "Fisher z provides adequate approximation for N>15; bootstrap was infeasible for N=5–9 cells").

**Gap 2: The "stable driver" classification conflates corroboration with redundancy.**
A metric classified as a "stable driver" requires rho > 0.5 across all three multiples. However, because P/FRE, P/DE, and EV/FEAUM are themselves highly correlated (a firm that ranks high on P/FRE will also rank high on P/DE and EV/FEAUM), the three-multiple criterion does not provide three independent tests — it provides approximately 1.5–2 independent pieces of evidence. The classification threshold should be accompanied by a note that the three multiples are not independent, and that "stable driver" means "correlated with all three positively" rather than "validated by three independent tests."

**Gap 3: Variable sample sizes across tests violate the comparability assumption.**
The correlations for mgmt_fee_rev vs. EV/FEAUM (N=21), vs. P/FRE (N=20), and vs. P/DE (N=15) are presented as three equivalent tests of the same metric. They are not: the N=15 test excludes 6 additional firms that are present in the N=21 test (firms that have EV/FEAUM but not P/DE). The sub-sample tested for P/DE may not be representative of the full universe, introducing sample selection bias. Recommended fix: conduct all correlation tests on a consistent sub-sample of firms for which all three multiples are available (approximately 15 firms), and separately report the full-sample results for P/FRE and EV/FEAUM.

**Gap 4: No correction for temporal autocorrelation or panel effects.**
The analysis uses FY2024 data (with March fiscal year observations from FY2025 for STEP, HLNE, ICP). These are not cleanly contemporaneous cross-sections — different reporting dates introduce up to 12 months of temporal drift. Formally this introduces heteroscedasticity in the error terms. Recommended fix: align all data to a single 12-month reference period (e.g., trailing twelve months ending December 2025) by interpolating or using the nearest available data point.

**Gap 5: The Bonferroni correction is computed over 55 tests, but the tests are highly non-independent.**
The 11 documented collinear pairs mean that approximately 20–25% of the 55 tests are near-duplicates. Bonferroni over 55 non-independent tests is overly conservative and inflates the Type II error rate. A structurally appropriate correction would: (a) identify the effective number of independent tests (approximately 35–40 given the collinearity structure), (b) apply Bonferroni over that reduced number, or (c) use a permutation-based correction that respects the correlation structure among test statistics.

**Gap 6: Sensitivity analyses are conceptual rather than computational.**
VD-A4b Section 5 describes LOO sensitivity analysis as "conceptual," with estimated rho ranges ("Estimated LOO rho ~ 0.58-0.61") rather than computed values. Because the data is fully tabulated in VD-A3, these LOO correlations could be computed exactly. The absence of computed LOO results means the stability claims cannot be independently verified. The temporal stability check (specified in the design as a comparison of FY1 vs. FY2 correlations) is entirely absent from the output.

**Gap 7: N<10 cells are reported as if they are informative.**
Six correlation results are computed on N=5–9 observations: perf_fee_share (N=7–9), comp_ratio (N=5–7), asset_class_hhi (N=6), organic_growth (N=6). A Spearman correlation on N=6 has minimum detectable rho of approximately 0.83 at alpha=0.05 (two-tailed). This means any true rho below 0.83 will be classified as "not a driver" or "moderate" with certainty at N=6, regardless of the true underlying relationship. These cells should be explicitly flagged as "insufficient data for evaluation" rather than as evidence of no relationship.

**Gap 8: No partial correlation analysis for the credit exposure driver.**
Credit exposure (rank 2 driver, rho=0.521 with P/FRE) is confounded with scale: APO ($938B AUM, 75% credit), ARES ($622B AUM, 70% credit), and OWL ($307B AUM, 55% credit) are all in Q1 on both scale and credit exposure. A partial correlation of credit_pct vs. P/FRE controlling for scale (mgmt_fee_rev or AUM) would test whether credit provides an independent valuation premium beyond what scale alone explains. Without this test, the credit premium claim rests on a confounded bivariate correlation.

**Gap 9: The three valuation multiples are not fully independent.**
P/FRE and EV/FEAUM both use enterprise value or market cap in the numerator. If FRE and FEAUM are highly correlated (and they are: rho=0.920 in the multicollinearity table), then a metric that correlates with P/FRE will mechanically also tend to correlate with EV/FEAUM through the shared scale of the numerator. This creates a subtle circularity in the "stable driver" classification that overstates the multi-multiple robustness. P/DE, which uses distributable earnings (inclusive of performance fees), is the most independent of the three multiples and should be weighted more heavily in classification decisions.

---

## Data Coverage Assessment

### Current Coverage

The actual metric coverage achieved in VD-A3 is as follows:

| Metric | Observations (N) | Coverage Rate (of N=22) | Assessment |
|--------|-----------------|------------------------|------------|
| P/FRE | 20 | 91% | Good |
| EV/FEAUM | 21 | 95% | Good |
| P/DE | 15–16 | 68–73% | Moderate |
| FEAUM (absolute) | 22 | 100% | Excellent |
| AUM (absolute) | 22 | 100% | Excellent |
| FEAUM YoY growth | 21 | 95% | Good |
| FRE (absolute) | 21 | 95% | Good |
| FRE margin | 20 | 91% | Good |
| Mgmt fee revenue | 22 | 100% | Excellent |
| DE (absolute) | 15 | 68% | Moderate |
| DE/share | 15 | 68% | Moderate |
| Perm capital % | 15 | 68% | Moderate |
| Credit % | 15 | 68% | Moderate |
| FRE growth YoY | 20 | 91% | Good |
| Mgmt fee growth | 14 | 64% | Moderate |
| Fundraising ratio | 13 | 59% | Marginal |
| Perf fee share | 9 | 41% | Poor — insufficient for evaluation |
| Organic growth | 6 | 27% | Poor — insufficient for evaluation |
| Comp ratio | 7 | 32% | Poor — insufficient for evaluation |
| Asset class HHI | 6 | 27% | Poor — insufficient for evaluation |
| DE growth 3yr CAGR | 5 | 23% | Poor — insufficient for evaluation |
| FEAUM 3yr CAGR | 7 | 32% | Poor — insufficient for evaluation |

**The design document specified a coverage threshold of 15 of approximately 25 firms as "low coverage."** By that criterion, 8 of 19 driver candidate metrics fall below threshold. The analysis correctly flags these as "low coverage" in VD-A3. However, the subsequent correlation analysis and driver ranking treat low-coverage and adequate-coverage metrics side by side without consistently distinguishing their evidentiary weight.

The five firms excluded from VD-A3 (Man Group, Partners Group, 3i, Rithm Capital, Onex) are correctly excluded based on structural incompatibility with the FRE/DE/FEAUM framework. However, their exclusion removes 19% of the universe and systematically eliminates two major European firms (Man Group, Partners Group) and two hybrid/balance-sheet models (3i, Onex) — potentially biasing the scale-valuation relationship toward US-listed pure-play alt managers.

### Critical Gaps

**Gap 1: P/DE coverage (N=15) is too low for a "stable driver" classification.**
The classification of Total AUM and Distributable Earnings as "stable drivers" (requiring rho > 0.5 across all three multiples) relies on P/DE tests run on only 15 firms. The 6 additional firms in the P/FRE and EV/FEAUM tests are missing from the P/DE test, introducing sample selection bias. The 15-firm sub-sample that reports P/DE is systematically different: it excludes STEP, ICP, TKO, ANTIN, RF, and GCMG — all smaller firms or European firms that don't report DE. Removing these firms from the P/DE correlation changes the sample composition in ways that may inflate the correlation.

**Gap 2: No disclosure of the actual data points used per firm.**
VD-A2 was too large to read fully (>25,000 tokens; read request failed), which prevents verification of individual data points. The standardized file (VD-A3) presents per-firm summaries but does not provide the primary source reference for each individual data point. A critical audit of VD-A2 against primary filings should be conducted before any investment decision is made based on this analysis.

**Gap 3: KKR's FEAUM is listed as `null` in VD-A0.**
KKR (FIRM-003, $638B AUM) has `latest_feaum_usd_bn: null`. The VD-A3 standardized dataset lists KKR FEAUM as $512B — this value appears to have been estimated or sourced without explicit disclosure of the source or methodology. Given KKR's size (rank 3 by AUM), this null at VD-A0 and the subsequent imputation in VD-A3 represents a data provenance gap that needs to be documented.

**Gap 4: Several European firms have incomplete metric profiles.**
ICP (FY2025, March fiscal year) has null values for P/FRE, P/DE, FRE margin, FRE, DE, and most driver metrics — it contributes only EV/FEAUM to the analysis. Man Group and Partners Group are excluded entirely. This means the 6 European firms in the universe contribute far less data density than US-listed firms, potentially understating the importance of European dynamics (geographic risk premiums, regulatory differences, different LP base preferences).

**Gap 5: FRE definition reconciliation is documented but not standardized.**
VD-A3 documents FRE definitions firm-by-firm (19 distinct definitions) but does not systematically adjust values to a common definition. For example, the choice of whether to include or exclude stock-based compensation from FRE can shift margins by 5–15 percentage points. Without normalization, FRE-based correlations (FRE margin, FRE growth, FRE absolute) are subject to measurement error that is directionally unpredictable.

---

## Metric Selection Assessment

### Current Taxonomy Strengths

The 25-metric taxonomy (19 driver candidates + 3 dependent variables + 3 contextual metrics) is well-structured and covers the primary dimensions on which alternative asset managers differentiate competitively. The decision to exclude market structure metrics (ADTV, passive ownership, free float) from the correlation analysis is correct: these are consequences of investor behavior, not actionable management levers.

The three-multiple dependent variable design (P/FRE, P/DE, EV/FEAUM) appropriately captures different facets of value: earnings power (P/FRE), distributable cash (P/DE), and AUM quality (EV/FEAUM). The "stable driver" criterion requiring all three to show rho > 0.5 is a conceptually sound way to screen for robust signals — subject to the independence caveat noted above.

The HHI for asset class diversification is methodologically superior to a simple asset class count, for the reasons stated in the design document.

### Missing Metrics

**Missing Metric 1: Return on Invested Capital (ROIC) on GP commitment capital.**
All major alt managers invest their own capital alongside LPs (GP commits range from 1% to 5% of fund size). The return earned on GP capital is a direct measure of alignment and investment quality. Firms with high ROIC on GP commits (e.g., BAM, where the Brookfield parent holds concentrated positions) may command premium multiples for demonstrated alignment. This metric is partially disclosed in annual reports and investor days but was not included in the taxonomy.

**Missing Metric 2: Revenue concentration (top 3 strategy share of total revenue).**
Highly concentrated revenue (e.g., ANTIN at 100% infrastructure, PX heavily PE/VC) vs. diversified revenue is related to but distinct from the asset class HHI metric. The HHI is currently computed on AUM, not revenue — but because fee rates vary dramatically by asset class (PE at 150–200bps vs. credit at 75–100bps), a revenue-based concentration metric would capture different information. This would allow a test of the hypothesis that revenue diversification (not just AUM diversification) predicts valuation multiples.

**Missing Metric 3: Track record / vintage fund performance (net IRR vs. benchmark).**
None of the 25 metrics in the taxonomy directly measures investment performance. This is a significant omission: the market presumably pays higher multiples to managers with better track records, but this relationship is untested. Fund-level net IRRs are disclosed in 10-K filings for US-listed managers (SEC Form 10-K Item 7) and could be aggregated as a "flagship fund vintage IRR" or "% of funds meeting hurdle" metric. The omission is understandable given data standardization challenges, but it means the analysis cannot distinguish between scale premiums and performance premiums.

**Missing Metric 4: Fundraising velocity (time to close flagship fund vs. target).**
Fundraising efficiency — how quickly a manager reaches the hard cap on a flagship fund — signals LP demand quality. A manager that closes a $10B fund in 6 months vs. one that takes 24 months demonstrates different levels of franchise strength, even if the ultimate AUM raised is identical. This information is partially available from press releases and PERE/Preqin data but was not extracted.

**Missing Metric 5: Insurance-linked AUM as % of total AUM.**
Given that the APO/Athene and KKR/Global Atlantic models are repeatedly cited as industry-defining strategic plays, the proportion of AUM linked to insurance liabilities deserves a dedicated metric. The current "permanent capital %" metric conflates insurance capital, publicly listed vehicles (BDCs, REITs), and long-duration drawdown funds — very different risk and permanence profiles.

**Missing Metric 6: Retail/private wealth AUM as % of total AUM.**
The private wealth channel is described as a primary growth lever for BX, KKR, and OWL. Whether firms have access to this channel (and what proportion of AUM comes from it) is a structurally important differentiator. This metric is partially available from Blackstone's disclosures ($300B) and would require estimation for other firms, but it tests an important hypothesis about the premium that retail channel access commands.

**Appropriate exclusions confirmed:** The three market structure metrics (ADTV, passive %, free float) are correctly excluded. The decision not to include leverage ratios (debt/FEAUM, interest coverage) as driver candidates is also defensible given that alt manager corporate leverage is modest and not obviously related to valuation multiples in this period.

---

## Peer Selection Assessment

### Universe Completeness

The 27-firm universe (VD-A0) is comprehensive for the publicly listed segment. The methodology notes correctly identify the key source databases (MarketVector MVAALT, BlueStar BUALT) and the verification process. The 15 documented exclusions (with reasons) are all justifiable. The known limitation — that the privately held universe (Permira, Warburg Pincus, General Atlantic, Vista, Thoma Bravo) is excluded — is appropriately disclosed.

**Potential gap: Intermediate Capital Group (ICP) is retained in VD-A0 and VD-C1 but contributes near-zero quantitative data.** ICP has null values for P/FRE, P/DE, FRE, DE, and all derived metrics. It contributes only EV/FEAUM and AUM/FEAUM to the analysis. Retaining ICP adds one observation to the EV/FEAUM correlation (marginal value) while creating false impressions of European coverage. It should either be excluded at VD-A3 (with Man Group and Partners Group) or explicitly labeled as "EV/FEAUM only" in all downstream analyses.

**Potential gap: Rithm Capital (RITM) and 3i Group (III) are excluded but their models are evolving.** Rithm's Sculptor acquisition ($37B AUM) is a relevant case study in fee-earnings model transition. 3i's Action superstore model generates significant proprietary capital returns. Including these as "special case" observations with appropriate flags rather than outright exclusions would add data points at the edges of the universe.

**Strong feature: The 2-tier structure (27 quantitative / 15 qualitative / 12 deep-dive) is well-calibrated.** The convergence mechanism (VD-C1) that winnows from 27 to 12 using both quantitative rankings and strategic instructiveness is an appropriate design choice. The 12-firm deep-dive set covers role models (8), cautionary cases (2), and non-obvious peers (2) — providing both aspirational benchmarks and instructive counter-examples.

### Convergence Logic

**The VD-C1 convergence logic is sound but incompletely documented.** The output correctly identifies inclusion rationale for each of the 12 firms and exclusion rationale for the remaining candidates. However, the quantitative criteria for VD-C1 state that the auto-include rule is "top quartile on 2+ stable drivers." In the actual VD-C1 output, several firms are included based on Q1 status on drivers that were classified as "not_a_driver" (FRE margin at 0.116 avg rho; FRE growth at 0.018 avg rho). This is a definitional inconsistency: including firms based on strong performance on metrics that the analysis finds to be non-value drivers dilutes the quantitative rationale for the convergence decision.

**Specific inconsistency:** CG (Carlyle) is included as a "cautionary case" and KKR is included as a "role model" partly because of Q1 performance on FRE growth (30% and 37% respectively). But FRE growth has avg |rho| = 0.018 — the weakest correlation of any metric tested. Including firms based on FRE growth as a qualifier contradicts the analysis's own conclusion that FRE growth is "not a driver." This should be explicitly reconciled: either acknowledge that the inclusion is based on strategic instructiveness (qualitative criterion) rather than quantitative relevance, or update the convergence methodology to only use statistically validated drivers as quantitative criteria.

**Non-obvious peer identification is a methodological strength.** The surfacing of BPT (Bridgepoint) and CVC as non-obvious peers through quantitative analysis — firms that did not appear in the initial B0 qualitative list but emerged from the Track A rankings — demonstrates the value of the hybrid approach. The BPT identification is particularly strong: BPT is the closest structural analog to PAX's M&A-driven growth strategy and provides a real-world outcome reference for what a recently public, mid-scale, acquisition-driven European alt manager looks like.

---

## Reproducibility Assessment

### What Is Reproducible

1. The design document provides sufficient detail to replicate the analysis structure, stage sequence, and quality gate criteria.
2. The statistical methodology (Spearman computation, p-value via t-test approximation, Fisher z CIs, Bonferroni and BH-FDR corrections) is fully documented and reproducible.
3. The universe identification methodology is documented with source databases and verification steps.
4. The FRE definition documentation (19 firm-specific notes in VD-A3) provides the most thorough cross-firm FRE reconciliation available in any published analysis of this universe.
5. The source catalog (VD-B0: 82 sources across 15 firms) provides traceable references.
6. Identifier schemes (FIRM-NNN, MET-VD-NNN, COR-NNN, DVR-NNN, PS-VD-NNN, ACT-VD-NNN, PLAY-NNN) enable cross-file traceability.

### What Is Not Reproducible

1. **Individual data points in VD-A2 are not separately verifiable** from VD-A3 (the raw data file was too large to read fully and data provenance is not provided per-cell in the standardized output).
2. **Organic growth estimates for 6 firms are not explained.** How was organic growth derived for PAX (12%), PX (8%), BN (15%), CVC (15%), RF (10%), ANTIN (7.3%)? No methodology or source citation is provided for these estimates in VD-A3.
3. **Asset class HHI calculations are not traceable.** The 6 firms with HHI values (PAX 2,200; PX 3,000; ANTIN 10,000; RF 2,500; BN 1,800; VCTR 2,000; CVC 2,000) were presumably computed from disclosed AUM breakdowns, but the underlying asset class shares are not documented in VD-A3.
4. **KKR FEAUM is listed as null in VD-A0 but populated in VD-A3.** The source and methodology for KKR's $512B FEAUM figure needs documentation.
5. **The temporal stability check is specified in the design but absent from outputs.** The comparison of FY1 vs. FY2 correlations is never executed or referenced in VD-A4 or VD-A4b.
6. **The LOO analysis is conceptual (estimated ranges) rather than computed.** The exact LOO rho values should be calculated from the tabulated data.
7. **Market cap reference dates are not uniformly disclosed.** The sample includes firms with different fiscal year-ends (March FY for STEP, HLNE, ICP; calendar FY for most others). The market cap dates used for P/FRE, P/DE, and EV/FEAUM calculations are not specified per firm in VD-A3 — a critical reproducibility gap since market cap can vary 10–20% within a fiscal year.

---

## Priority Improvements (Ranked)

### Priority 1: Implement Partial Correlation for Credit Exposure Driver
**Impact: High | Difficulty: Low**
The credit exposure driver (rank 2, rho=0.521 with P/FRE) is confounded with scale. Computing partial Spearman correlation of credit_pct vs. P/FRE controlling for mgmt_fee_rev_usd_mn would test whether credit provides an independent premium. If partial rho drops to near zero, the credit premium is entirely explained by scale. If partial rho remains significant, it establishes an independent credit premium thesis. This single analysis would materially change the strategic implications for PAX.

### Priority 2: Implement Temporal Stability Check (FY1 vs. FY2)
**Impact: High | Difficulty: Low**
The design document specified this check and it was never executed. Point-in-time cross-sectional correlations are sensitive to market conditions. A second-year check using FY2023 data for the same universe (requiring historical data extraction) would test whether the scale-dominance finding is stable across years or specific to the post-2022 rate environment. This is particularly important for the permanent capital non-finding (perm capital % may matter in different interest rate environments).

### Priority 3: Resolve the Bootstrap vs. Fisher z Discrepancy
**Impact: Medium | Difficulty: Low**
Either execute the 1,000-iteration bootstrap specified in the design document and compare CIs to the Fisher z approximation, or formally amend the methodology to use Fisher z with explicit justification. For the N=5–9 cells (perf fee share, comp ratio, organic growth, asset class HHI), the Fisher z approximation breaks down at small N, making bootstrapped CIs particularly important for those metrics.

### Priority 4: Establish a Consistent Sub-Sample for All Three-Multiple Tests
**Impact: High | Difficulty: Medium**
Run all 19 driver metrics against all three multiples on the common sub-sample of firms for which all three multiples are available (approximately 14–15 firms). Present these as the primary analysis. Separately present the larger-N tests for P/FRE (N=20) and EV/FEAUM (N=21) as supplementary analysis. This eliminates sample selection bias from the variable N across multiples.

### Priority 5: Add Performance Track Record Metrics to the Taxonomy
**Impact: High | Difficulty: High**
Fund-level net IRRs vs. benchmarks are disclosed in 10-K filings (Item 7) for US-listed managers. Extracting flagship fund vintage IRRs and computing a cross-sectional performance metric would test whether the valuation premium reflects performance quality or pure scale. This analysis would be novel in the literature and would significantly strengthen the analytical contribution.

### Priority 6: Add Insurance-Linked AUM % and Retail AUM % as Separate Metrics
**Impact: Medium | Difficulty: Medium**
Disaggregating the "permanent capital %" metric into (a) insurance-linked AUM, (b) retail/wealth channel AUM, and (c) long-duration drawdown AUM would test whether specific permanent capital types carry different valuation premia. The current composite metric confounds very different business models (APO/Athene's $292B insurance vs. PX's 85% permanent but lower-fee PE/VC solutions vehicles).

### Priority 7: Compute Exact LOO Values and Correct Effective N for Bonferroni
**Impact: Medium | Difficulty: Low**
The data is fully tabulated in VD-A3. Computing exact leave-one-out rho for each statistically significant result requires simple rank recomputation. Additionally, estimating the effective number of independent tests (accounting for the 11 documented collinear pairs) would allow a more calibrated multiple-testing correction — potentially recovering several "borderline significant" results that are currently lost to over-conservative Bonferroni.

### Priority 8: Document Data Provenance for Organic Growth and HHI Estimates
**Impact: Medium | Difficulty: Low**
Adding source citations and calculation methodology to the 6 organic growth estimates and 7 HHI values in VD-A3 would close the most significant reproducibility gaps without requiring any additional data collection.

---

## Summary Assessment Table

| Dimension | Rating | Primary Concern |
|-----------|--------|-----------------|
| Statistical methodology design | Strong | Bootstrap deviation, non-independent tests |
| Statistical execution | Moderate | LOO conceptual only, no temporal stability |
| Data coverage (P/FRE, EV/FEAUM) | Good | Variable N across tests |
| Data coverage (low-coverage metrics) | Weak | N<10 for 5 key metrics |
| FRE definition handling | Good | Documented, not standardized |
| Metric taxonomy | Moderate | Missing performance, insurance-linked, retail AUM |
| Peer universe | Strong | ICP edge case; no private universe |
| Convergence logic | Moderate | Includes non-driver metrics as Q1 criteria |
| Reproducibility | Moderate | Organic growth, HHI, market cap dates undocumented |
| Disclaimer completeness | Strong | All six disclaimers present and well-calibrated |
| Overall | Moderate-Strong | Findings are directionally credible but precision-limited |

---

*Review completed 2026-03-06. All assessments based on reading of design document and 16 pipeline output files. Raw data file VD-A2 could not be fully reviewed (exceeds 25,000 token limit) — a separate data audit of VD-A2 against primary filings is recommended before any decision-grade use of the outputs.*
