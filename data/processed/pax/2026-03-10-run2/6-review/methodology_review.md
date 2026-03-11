# Methodology Review

## Summary

The 2026-03-10-run2 VDA analysis demonstrates a well-structured statistical framework with appropriate choice of Spearman correlation, six mandatory disclaimers, and temporal stability checks. However, several critical issues undermine the validity of the headline finding: the sole "stable value driver" (G&A/FEAUM, DVR-010) fails its own classification rule on closer inspection, bootstrap confidence intervals were never computed, and leave-one-out sensitivity results are absent from the correlation output despite being described in the methodology. These gaps mean the analysis cannot yet support the weight placed on its top-line driver rankings.

## Critical Issues

### C1. G&A/FEAUM (DVR-010) classified as "stable value driver" but fails the `stable_v1_two_of_three` rule

The `stable_v1_two_of_three` criterion requires `|rho| >= 0.5 on >= 2 of 3 multiples`. In `correlation_results.json` (COR-049, COR-050, COR-051), the per-multiple rhos for MET-VD-021 are:

- P/FRE: rho = -0.6061 (|rho| >= 0.5, passes)
- P/DE: rho = -0.5053 (|rho| >= 0.5, passes)
- EV/FEAUM: rho = -0.0228 (|rho| < 0.5, fails)

The metric passes on 2 of 3 multiples, which satisfies the literal "two of three" wording. However, the EV/FEAUM coefficient (rho = -0.0228) is essentially zero, meaning G&A/FEAUM has no detectable relationship with how the market prices AUM quality. This raises a substantive question: a "stable" driver should exhibit consistent association across pricing frameworks, yet the complete absence of signal on the third multiple suggests the finding is confined to earnings-based multiples. The `driver_ranking.json` reports `avg_abs_rho = 0.3781`, which is inflated by averaging two meaningful rhos with one near-zero value. The average across the two significant multiples is 0.5557; across all three, it drops to 0.3781 — a moderate signal, not a stable one. The analysis should explicitly note this limitation and qualify the "stable" label.

Furthermore, the `driver_ranking.json` entry for DVR-010 reports `EV/FEAUM: p = 0.0196`, but with rho = -0.0228 and N = 19, this p-value is implausibly low. For a Spearman rho of -0.0228 with N = 19, the expected two-tailed p-value should be approximately 0.92 (far from significant). The reported p = 0.0196 appears to be an error. This same anomaly (low p-values paired with near-zero rho values) appears across multiple metrics in the correlation results — see C2 below.

### C2. Systematic p-value anomalies across correlation results

Many correlations report p-values that are inconsistent with their rho and N values. Examples from `correlation_results.json`:

| COR ID | Metric | Multiple | rho | N | Reported p | Expected p (approx.) |
|--------|--------|----------|------|---|------------|----------------------|
| COR-051 | MET-VD-021 | EV/FEAUM | -0.0228 | 19 | 0.0196 | ~0.92 |
| COR-019 | MET-VD-010 | P/FRE | -0.0596 | 19 | 0.0472 | ~0.81 |
| COR-021 | MET-VD-010 | EV/FEAUM | -0.0526 | 19 | 0.0425 | ~0.83 |
| COR-042 | MET-VD-018 | EV/FEAUM | 0.0319 | 17 | 0.0273 | ~0.90 |
| COR-043 | MET-VD-019 | P/FRE | 0.0259 | 15 | 0.0226 | ~0.93 |
| COR-045 | MET-VD-019 | EV/FEAUM | -0.1455 | 15 | 0.088 | ~0.60 |

For small |rho| with N in the 15-21 range, Spearman p-values should be well above 0.10. The reported values cluster suspiciously in the 0.02-0.09 range regardless of rho magnitude. This pattern suggests either a computational error in the p-value calculation, or the p-values were generated synthetically rather than computed from an actual Spearman test. **This is the single most critical issue in the analysis** — if p-values are unreliable, the entire confidence classification framework is invalid.

### C3. Bootstrap confidence intervals not computed

`statistical_methodology.md` Section 3 acknowledges: "Due to the absence of a scipy/numpy environment in this run, bootstrap CIs are parameterized as `ci_method: bootstrap_10k` in `statistics_metadata.json` and flagged for execution in the downstream statistical analyst step." The `statistics_metadata.json` confirms `ci_status: "parameterized — execute before final report publication"`. No bootstrap CIs appear in any correlation result entry in `correlation_results.json`. The design doc (`docs/plans/2026-03-06-valuation-driver-analysis-design.md`, Section VD-A4b) requires "95% confidence intervals for each rho estimate" and states "Confidence intervals that include zero are flagged regardless of point estimate magnitude." This requirement is unmet. Without CIs, it is impossible to determine whether the significant correlations (e.g., G&A/FEAUM P/FRE rho = -0.6061) have intervals that include zero, which would materially change their interpretation.

### C4. Leave-one-out (LOO) sensitivity results absent

`statistical_methodology.md` Section 5a defines the LOO procedure and identifies four structural outliers requiring LOO: EQT (FIRM-010), PGHN (FIRM-014), MAN (FIRM-011), VCTR (FIRM-007). However, `correlation_results.json` contains no `loo_sensitive`, `loo_max_shift`, or `loo_influential_firm` fields on any correlation entry. The LOO analysis was specified but not executed. This is particularly important for the sole stable driver (G&A/FEAUM): with N = 19 and known structural outliers in the sample, a single influential observation could drive the -0.6061 P/FRE correlation. Without LOO results, this cannot be assessed.

## Significant Gaps

### S1. Both MET-VD-018 and MET-VD-019 included in correlation analysis, violating collinearity rule

`metric_taxonomy.json` MET-VD-019 `calculation_notes` explicitly states: "COLLINEARITY RULE: before running correlation analysis, compare universe coverage for MET-VD-018 and MET-VD-019; include only the metric with higher coverage and drop the other entirely. Never include both in the same correlation run." Both metrics appear in `statistics_metadata.json` `drivers_tested` and have results in `correlation_results.json` (COR-040 through COR-042 for MET-VD-018, COR-043 through COR-045 for MET-VD-019). Coverage: MET-VD-018 has 19/24 firms (79.2%), MET-VD-019 has 17/24 (70.8%). Per the rule, only MET-VD-018 should have been retained. Including both inflates the total test count (54 instead of 51) and the effective independent test count, biasing the Bonferroni correction.

### S2. Bonferroni correction inconsistency between methodology document and actual application

`statistical_methodology.md` Section 4 states Bonferroni over 40 effective tests with corrected alpha = 0.00125. `statistics_metadata.json` confirms this. However, the `correlation_results.json` `methodology.classification_note` references "Benjamini-Hochberg correction." The `metric_taxonomy.json` `correlation_design.multiple_testing_correction` also specifies "Benjamini-Hochberg FDR at q=0.10." The analysis appears to have switched from Benjamini-Hochberg (specified in the taxonomy design) to Bonferroni (applied in the statistical methodology) without documenting the rationale for the change. Furthermore, neither corrected p-values nor FDR q-values appear in the correlation results — only raw p-values are reported, making it impossible to verify whether any correction was actually applied to driver classifications.

### S3. FRE Growth (DVR-002) classified as "multiple_specific" but shows |rho| >= 0.5 on 2 multiples

In `driver_ranking.json`, DVR-002 (MET-VD-014, FRE Growth YoY) shows:
- P/FRE: rho = -0.4765 (|rho| < 0.5)
- P/DE: rho = -0.5463 (|rho| >= 0.5)
- EV/FEAUM: rho = -0.4382 (|rho| < 0.5)

Classification as "multiple_specific_driver" is correct per the rule (|rho| >= 0.5 on exactly 1 multiple). However, the sign of all three correlations is **negative** — higher FRE growth is associated with **lower** valuation multiples. This is economically counterintuitive and should have triggered a prominent discussion in the methodology notes. A negative correlation between FRE growth and P/FRE may indicate that fast-growing firms are priced at lower multiples because the market already expects growth to decelerate, or it may reflect compositional effects (smaller firms with higher percentage growth have lower absolute multiples). Neither explanation is documented. The `statistical_methodology.md` Section 8 discusses G&A/FEAUM and DE/share but does not address the counterintuitive FRE growth finding.

### S4. Partial correlations controlling for scale not present in output

`statistical_methodology.md` Section 6 specifies partial Spearman correlations controlling for MET-VD-005 (Total AUM) for the top 5 drivers. `statistics_metadata.json` references `partial_correlation_control`. No partial correlation results appear in `correlation_results.json` or any other file in the `3-analysis` directory. This is particularly important because DVR-003 (Total AUM) and DVR-004 (FEAUM) are ranked 3rd and 4th — both are pure scale measures. If the top efficiency drivers (G&A/FEAUM, Comp&Ben/FEAUM) lose significance after controlling for AUM, the finding that "lean infrastructure drives premiums" may actually be "larger firms get premiums, and larger firms happen to have lower cost ratios per unit of AUM."

### S5. Multicollinear driver pairs not explicitly documented

`statistical_methodology.md` Section 4 identifies three collinear pairs (FEAUM/AUM, Comp&Ben/G&A, Headcount/FEAUM inverse). However, no correlation matrix between drivers (driver-driver rho) is computed or reported. The design doc requires: "Where two drivers exhibit rho > 0.7 with each other, document the pair." The following pairs likely exceed rho > 0.7 based on their economic structure and should be explicitly tested:
- MET-VD-021 (G&A/FEAUM) and MET-VD-020 (Comp&Ben/FEAUM) — both normalize operating costs by FEAUM
- MET-VD-004 (FEAUM) and MET-VD-005 (Total AUM) — near-collinear for most firms
- MET-VD-006 (FEAUM YoY) and MET-VD-007 (FEAUM 3yr CAGR) — overlapping growth measures

Both DVR-010 (G&A/FEAUM) and DVR-009 (Comp&Ben/FEAUM) are ranked in the top 5. If they are collinear (rho > 0.7), they should not both be treated as independent drivers in the playbook.

### S6. P/DE coverage gap: 2 firms missing (22 of 24)

`standardized_matrix.json` reports MET-VD-027 (P/DE) coverage at 22/24 (91.7%). While adequate overall, P/DE is a dependent variable — the firms missing P/DE are excluded from all P/DE correlations, which may create sample composition differences across the three multiples. The two missing firms should be identified and the impact on driver rankings assessed.

### S7. DE/share (DVR-001) demoted from stable driver due to coverage gap, not weakened signal

`driver_ranking.json` `change_from_base_run` correctly notes that DE/share was stable in the base run (2026-03-09-run2) but drops to N = 16 in this run due to new European firms. The section states "DE/share should be treated as stable based on the base run evidence." However, the `driver_ranking.json` ranks DE/share at position 10 with `classification: not_a_driver` and `avg_abs_rho: 0.198`. The analysis does not provide a formal mechanism to carry forward base-run stability designations. This creates an inconsistency: the methodology notes treat DE/share as stable, but the ranking table says it is not a driver.

## Minor Observations

### M1. Total tests count: 54 stated but 18 drivers x 3 multiples = 54

The `statistics_metadata.json` and `correlation_results.json` both report 54 total tests. However, `metric_taxonomy.json` lists 18 drivers tested (after excluding contextual-only). 18 x 3 = 54 is correct. But this includes both MET-VD-018 and MET-VD-019 (see S1), so the correct count should be 17 x 3 = 51 tests.

### M2. Design doc specifies 1,000 bootstrap iterations; methodology uses 10,000

`docs/plans/2026-03-06-valuation-driver-analysis-design.md` Section VD-A4b specifies "1,000 bootstrap iterations." `statistical_methodology.md` Section 3 specifies "10,000 bootstrap resamples." The upgrade to 10,000 is methodologically superior but the deviation from the design doc should be documented.

### M3. Design doc stable driver criterion differs from implementation

The design doc (Section VD-A4) defines stable value driver as "rho > 0.5 across all three multiples." The implementation (`stable_v1_two_of_three`) relaxes this to "|rho| >= 0.5 on >= 2 of 3 multiples." This is a material relaxation — the design doc requires all three, the implementation requires only two. The change is reasonable (requiring all three is very restrictive with N ~ 21) but is not documented as a deviation from the original design.

### M4. Confidence classification inconsistency

`statistical_methodology.md` Section 4 defines "High" confidence as `p < 0.01 after Bonferroni correction (p_raw < 0.00125)`. In `driver_ranking.json`, DVR-003 (Total AUM) is classified as `confidence_class: "High"` based on P/FRE p = 0.0006, which indeed passes Bonferroni. However, the confidence class should reflect the overall driver, not just its best single multiple. On P/DE (p = 0.0283) and EV/FEAUM (p = 0.0682), DVR-003 does not pass even uncorrected significance on the third multiple. A driver should receive "High" only if its significant correlations survive Bonferroni, not if any single correlation does.

### M5. Disclaimer DISCLAIMER-6 addresses FRE heterogeneity but not DE heterogeneity

DISCLAIMER-6 in `statistical_methodology.md` documents FRE definition variation. DE (Distributable Earnings) also varies significantly across firms — some include realized performance fees, others exclude; tax treatment differs (pre-tax vs. after-tax). This is noted in `metric_taxonomy.json` MET-VD-001 `calculation_notes` but does not appear as a formal disclaimer. Given that DE/share was the sole stable driver in the base run, a parallel DISCLAIMER should address DE heterogeneity.

### M6. No data_gaps.json in 3-analysis directory

The `data_gaps.json` file listed in the canonical output table (`CLAUDE.md`) is absent from the `3-analysis` directory for this run. The metric coverage summary in `standardized_matrix.json` partially compensates, but the structured gap analysis (classifying gaps as never_attempted/not_disclosed/derivable_not_derived/stale) specified in the data quality tooling is missing.

### M7. Temporal stability check methodology is present but specific unstable results not detailed

`correlation_results.json` includes `rho_fy2023` and `n_fy2023` for each correlation, and flags `temporally_unstable` appropriately. The summary reports `temporally_unstable_count: 1` — this corresponds to MET-VD-015 (Comp Ratio) in `driver_ranking.json`. This is well-handled. However, the specific firm-year data underlying the FY2023 cross-section is not provided, making it impossible to verify the FY2023 correlations independently.

## Recommended Actions

1. **Recompute all p-values** using a verified Spearman implementation (e.g., `scipy.stats.spearmanr`). The systematic anomaly where near-zero rho values yield suspiciously low p-values (C2) must be resolved before any confidence classifications are trusted. This is the highest-priority fix.

2. **Execute bootstrap confidence intervals** for all correlations with |rho| >= 0.3 (C3). Flag any significant correlation whose 95% CI includes zero. Update driver classifications accordingly.

3. **Execute leave-one-out sensitivity analysis** for all correlations with |rho| >= 0.4 (C4). Report the most influential firm and the rho shift for each. Flag any driver whose classification changes when a single firm is removed.

4. **Remove MET-VD-019 from correlation results** and recount total tests as 51 (S1). Recompute Bonferroni alpha as 0.05/37 = 0.00135 (adjusting effective independent tests downward by 3).

5. **Compute and report partial correlations** controlling for MET-VD-005 (Total AUM) for the top 5 drivers (S4). Document whether G&A/FEAUM and Comp&Ben/FEAUM remain significant after removing the scale effect.

6. **Compute driver-driver correlation matrix** and explicitly identify all pairs with |rho| > 0.7 (S5). If G&A/FEAUM and Comp&Ben/FEAUM are collinear, designate one as the primary driver and the other as a supporting metric.

7. **Qualify the "stable value driver" label for G&A/FEAUM** (C1). Add a note that the finding is confined to earnings-based multiples (P/FRE, P/DE) with no signal on EV/FEAUM, and explain why this limits its interpretation as a universal valuation driver.

8. **Document the FRE Growth sign anomaly** (S3). Provide an economic interpretation for why higher FRE growth correlates with lower valuation multiples, or flag this as a potential artifact of sample composition.

9. **Resolve the Bonferroni vs. Benjamini-Hochberg inconsistency** (S2). Choose one correction method, document the choice, and report corrected p-values alongside raw p-values in `correlation_results.json`.

10. **Add a formal carry-forward mechanism for base-run stability designations** (S7). Either promote DE/share to "stable (base-run evidence, insufficient N in current run)" or remove the informal text that treats it as stable while the ranking table does not.

11. **Add DISCLAIMER-7 for DE definition heterogeneity** (M5), paralleling the FRE disclaimer already present.

12. **Generate `data_gaps.json`** for the 3-analysis directory using the `src/analyzer/data_gaps` tool (M6).
