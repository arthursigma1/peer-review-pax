# Methodology Review

**Run:** 2026-03-10-run4
**Base Run:** 2026-03-10-run2
**Reviewer:** methodology-reviewer agent
**Date:** 2026-03-11

---

## Summary

The statistical methodology is substantively rigorous: Spearman rank correlation is correctly justified, Benjamini-Hochberg FDR correction is applied to all 51 hypothesis tests, bootstrap CIs are computed for all eight reported significant or near-significant correlations, and all seven mandatory disclaimers are present. The primary weakness is not in the methodology itself but in the downstream driver-labeling system, which introduces material confusion: `driver_ranking.json` uses DVR-IDs that do not map consistently to the MET-VD IDs documented in `final_peer_set.json` and `statistical_methodology.md`, and FIRM-ID annotation errors in the `non_obvious_peers` section propagate through to `final_peer_set.json`. Additionally, the absence of any stable value driver in this run — a regression from run2 — is adequately documented but its playbook implications are under-interpreted in the ranking file itself. Data coverage is adequate for the primary drivers (N=18–23) but two firms in the final peer set have coverage below 90%, and DE/share structural comparability issues limit its utility as a playbook anchor despite its prominence in `final_peer_set.json` selection logic.

---

## Critical Issues

### 1. DVR-ID to MET-VD-ID Mapping Inconsistency — `driver_ranking.json`

**Location:** `driver_ranking.json`, `ranked_drivers[]` entries; `final_peer_set.json`, `selection_methodology` field.

The DVR-IDs used in `driver_ranking.json` do not match the DVR-IDs referenced in `final_peer_set.json`'s peer selection logic. Specifically:

- `final_peer_set.json` (`selection_methodology` field) references `DVR-001` as **DE/share** and `DVR-010` as **G&A/FEAUM**.
- `driver_ranking.json` (`ranked_drivers[]`) assigns `DVR-001` = **Total AUM** (MET-VD-005) and `DVR-005` = **G&A/FEAUM** (MET-VD-021). DE/share (MET-VD-001) appears nowhere in `ranked_drivers[]` — it is flagged as `unsupported` per `change_from_base_run.key_changes[]`.
- `final_peer_set.json` inclusion rationales for FIRM-009 (TPG), FIRM-012 (STEP), FIRM-015 (HLNE), and FIRM-024 (ANTIN) all cite `DVR-001 (stable, DE/share)` as the qualifying criterion — a DVR-ID that in `driver_ranking.json` refers to a different metric entirely (AUM).

This is a cross-file labeling inconsistency, likely an artifact of the `final_peer_set.json` agent reading an older DVR-ID convention (from run2 where DE/share was DVR-001) while `driver_ranking.json` assigned fresh DVR-IDs based on run4 ranking order. The result: four firms in the 12-firm final peer set (TPG, STEP, HLNE, ANTIN) have their inclusion justified by a stable driver (DE/share) that `driver_ranking.json` classifies as `unsupported` in this run. This materially affects the validity of the peer selection rationale.

**Impact:** High. If DE/share is genuinely unsupported in run4 (as stated in `driver_ranking.json`), the qualifying criterion for four deep-dive peers is absent. The playbook must not present DE/share as a confirmed driver for this run's evidence base.

### 2. FIRM-ID Annotation Errors in `driver_ranking.json` — `non_obvious_peers` Field

**Location:** `driver_ranking.json`, `non_obvious_peers` field; `final_peer_set.json`, `driver_ranking_annotation_error` section.

`driver_ranking.json` contains `non_obvious_peers: []` (empty array) in the actual JSON, so there are no FIRM-ID label errors present in the output file itself. However, `final_peer_set.json` (`driver_ranking_annotation_error`) documents that the agent that produced `driver_ranking.json` introduced FIRM-ID label errors in earlier drafts (FIRM-018 labeled as "OWL", FIRM-025 referenced which does not exist in `peer_universe.json`). It is unclear whether these errors were corrected before the final file was written. The `non_obvious_peers: []` in the current `driver_ranking.json` suggests the section was emptied rather than corrected.

**Impact:** Medium. If `non_obvious_peers` was intentionally emptied to avoid propagating errors, it introduces a gap: TPG (FIRM-009), HLNE (FIRM-015), and ANTIN (FIRM-024) are flagged as `non_obvious_peer: true` in `final_peer_set.json` but have no corresponding entry in `driver_ranking.json`. The downstream report-builder has no source of truth in `driver_ranking.json` for these non-obvious designations.

### 3. No Stable Value Driver in Run4 — Interpretation Gap

**Location:** `driver_ranking.json`, `ranking_methodology.stable_driver_note`; `statistical_methodology.md` Section 3.

`driver_ranking.json` correctly documents that no stable value driver exists in run4 (the 23-firm cross-section reduces cross-sectional signal strength due to structural heterogeneity). However, the change_from_base_run notes state: "Run2 had G&A/FEAUM as stable" — yet `final_peer_set.json` (`selection_methodology`) continues to reference `DVR-010 (G&A/FEAUM)` as a "stable" driver for peer selection qualification. If G&A/FEAUM is not stable in run4, peer selection criteria referencing it as a stable driver are applying a classification that does not hold in the current evidence base.

**Impact:** High. The peer set was selected partly using stable-driver criteria that do not apply in run4. This does not invalidate the final peer set (other criteria also apply), but the rationale as written overstates the evidentiary basis.

---

## Significant Gaps

### 4. Bootstrap CIs Reported Only for Eight Correlations — Not All 51

**Location:** `statistical_methodology.md`, Section 2; `correlation_results.json`, `statistical_parameters`.

Bootstrap CIs are documented for eight correlations in `statistical_methodology.md` (the nominally significant or near-significant ones). `correlation_results.json` includes CI fields (`ci_95_lo`, `ci_95_hi`) for all correlations in `driver_ranking.json`'s `per_multiple` entries. The review of `driver_ranking.json` shows CI fields populated for all 10 ranked drivers × 3 multiples = 30 pairs. However, `statistical_methodology.md` narrative only discusses 8 CI estimates — the remaining 43 are computed but not documented. The methodology section should note that CIs were computed for all 51 pairs, with the 8 highlighted being those where nominal significance warranted closer inspection.

Additionally, the Bootstrap CI table in `statistical_methodology.md` (Section 2) shows `DE/share × EV/FEAUM` CI = `[-0.15, +0.62]` which includes zero — this is correctly noted. However, `AUM × P/DE` CI = `[+0.15, +0.74]` (also in the table) is listed but AUM × P/DE is **not** BH-significant (`bh_significant: false` per `driver_ranking.json` DVR-001). The methodology section does not comment on this apparent inconsistency — a CI excluding zero but p-value failing BH correction. The explanation (N=20 vs N=22 for P/FRE; different effective sample reduces test power in BH procedure) should be explicitly stated.

### 5. Multicollinearity Between AUM and FEAUM Not Resolved Before Ranking

**Location:** `driver_ranking.json`, DVR-001 (AUM) and DVR-003 (FEAUM) ranked separately; `driver_ranking.json` DVR-003 `interpretation` field: "Closely correlated with AUM (inter-rho ~0.90)".

AUM (DVR-001) and FEAUM (DVR-003) are reported as having inter-driver Spearman rho ≈ 0.90, exceeding the 0.70 multicollinearity threshold specified in the review methodology brief. Both are included in the ranked drivers list as if they are independent contributors. While the methodology correctly uses bivariate Spearman (not regression), presenting two nearly identical drivers as separately ranked risks misleading playbook consumers into treating them as additive signals. The methodology section (`statistical_methodology.md`) does not address this pair explicitly — it only mentions the MET-VD-018/MET-VD-019 (Headcount/FEAUM vs FEAUM/Employee) mathematical inverse pair.

**Recommended action:** Flag AUM and FEAUM as a collinear pair in `statistical_methodology.md` Section 2 or an added Section 7. Treat FEAUM as a constituent of the AUM signal, not a separate driver, in playbook framing. AUM is correctly ranked higher (lower p-value; rho=0.73 vs 0.60 on P/FRE).

### 6. LOO Sensitivity Incomplete — Only Performed for Two Drivers

**Location:** `statistical_methodology.md`, Section 4A.

Leave-one-out sensitivity is documented only for AUM × P/FRE (removing BX), FEAUM × P/FRE (removing BX), and FRE growth × EV/FEAUM (removing HLNE). LOO was not performed for G&A/FEAUM × P/FRE (DVR-005, rank 5), which has p=0.037 — the third nominally significant result. Given that PAX is Q4 on G&A/FEAUM (rank 22/23), this driver has the most direct strategic implication for PAX, and no sensitivity test documents whether this finding is driven by a single observation. Specifically, the MAN (FIRM-011) structural outlier on EV/FEAUM and VCTR (FIRM-007) partial-alt status are both potential leverage points on G&A/FEAUM × P/FRE.

### 7. Temporal Stability Check — Absent Beyond Disclaimer

**Location:** `statistical_methodology.md`, Section 4B.

The temporal stability disclaimer is correctly included. However, the methodology states "FY2023 FRE growth records are available for a subset of firms but insufficient for a full prior-period cross-section at the same N." No documentation is provided of what subset was available, what N was achievable for FY2023, or whether the FY2023 subset yielded directionally consistent results. For a cross-sectional study with N=18–23, even a partial temporal stability check (e.g., AUM × P/FRE and FEAUM × P/FRE for the 12–15 firms with FY2023 data) would materially strengthen the two BH-significant findings.

### 8. VCTR Partial-Alt Contamination Not Isolated in Sensitivity

**Location:** `metric_taxonomy.json` `comparability_flags.FIRM-007`; `driver_ranking.json` DVR-005 (G&A/FEAUM) top peers listing "MAN (7.0)".

VCTR (FIRM-007) is classified as `partial-alt` — the only such firm in the 23-firm correlation universe (VINP was excluded). Three multiples are flagged low-comparability for VCTR. The methodology does not include a sensitivity test removing VCTR from the correlation universe, which would confirm whether its partial-alt revenue mix distorts efficiency metric correlations (G&A/FEAUM, Comp&Ben/FEAUM). With max|rho| < 0.50 for both efficiency drivers, VCTR removal sensitivity is a low-cost test that would either confirm robustness or reveal a single-firm contamination problem.

### 9. FRE Growth Negative Coefficient Interpretation — Potential Reverse Causality Unaddressed

**Location:** `driver_ranking.json`, DVR-002, `interpretation` field.

The negative coefficient for FRE growth × EV/FEAUM (rho = -0.61, p = 0.007) is interpreted as either an "execution discount" or a size-confound (smaller FEAUM bases). Neither interpretation addresses the most likely mechanical explanation: EV/FEAUM is structurally lower for younger platforms precisely because they have lower absolute FEAUM (denominator effect), and younger platforms also exhibit higher FRE growth rates off smaller bases. This creates a spurious negative correlation that is an artifact of the metric construction (FEAUM appears in both the dependent variable denominator and is correlated with the driver variable). The methodology section should explicitly identify this as a potential mechanical artifact and note that the interpretation requires additional controls (not available at N=18) before causal inference.

---

## Minor Observations

### 10. DVR-004 (Perm capital %) — Empty Interpretation Field

**Location:** `driver_ranking.json`, DVR-004 `interpretation: ""`.

DVR-004 (Permanent Capital %, rank 4, moderate signal, strongest rho = 0.43 × P/DE) has an empty `interpretation` field. Given that the P/DE CI = [-0.04, +0.76] marginally includes zero and p = 0.058, this driver is on the boundary of the moderate/unsupported threshold. An interpretation noting the theoretical mechanism (predictable fee streams reduce re-fundraising risk, narrowing earnings discount) and the marginal statistical confidence would strengthen the document. Same gap applies to DVR-006, DVR-007, DVR-008, DVR-009, DVR-010 — all five have empty `interpretation` fields.

### 11. Minimum N Thresholds — `minimum_n_report: 8` Undocumented

**Location:** `correlation_results.json`, `statistical_parameters.minimum_n_compute: 12` and `minimum_n_report: 8`.

The `minimum_n_report` threshold of 8 is lower than `minimum_n_compute` of 12. This means correlations with N as low as 8 could appear in reports even though they cannot be computed. The distinction and its implications are not documented anywhere in `statistical_methodology.md`. With N=8, Spearman rho would need to exceed ~0.74 for p < 0.05 — effectively only the most extreme correlations would qualify. This threshold should be explained or the two fields should be reconciled.

### 12. BH vs. Bonferroni Threshold Discrepancy Not Explained

**Location:** `statistical_methodology.md`, Section 3.

The document states "BH threshold: p <= 0.002882 (2 tests pass)" and "Bonferroni threshold: p <= 0.000980 (1 test: AUM × P/FRE)." This correctly shows BH is less conservative than Bonferroni. However, the FEAUM × P/FRE p-value is listed as p = 0.002882 in `statistical_methodology.md` but as p = 0.002882 in `driver_ranking.json` DVR-003 MET-VD-026 — the values match but land exactly on the BH threshold. Whether "p <= 0.002882" is applied as a strict inequality (exclude) or weak inequality (include) determines whether FEAUM × P/FRE is BH-significant. The document should clarify the boundary convention (the current classification as BH-significant implies ≤ is applied as weak inequality).

### 13. Currency Standardization Note Missing From Standardized Matrix Documentation

**Location:** `metric_taxonomy.json` MET-VD-004 `calculation_notes`; `statistical_methodology.md` (no corresponding section).

The metric taxonomy notes that non-USD FEAUM figures should be "converted to USD at period-end exchange rates." `statistical_methodology.md` has no section confirming that this conversion was applied consistently for EUR-denominated firms (EQT, CVC, ANTIN, Eurazeo, Tikehau), GBP firms (MAN, ICP, Bridgepoint), CHF firms (PGHN), and CAD firms (ONEX). A brief confirmation note (or table of exchange rates applied) would close this documentation gap, particularly for EQT where a 1.09 EUR/USD rate is mentioned in `peer_universe.json` but not validated against the standardization step.

### 14. `statistical_methodology.md` Section 6 CP-1 Corrections — Incomplete Scope Description

**Location:** `statistical_methodology.md`, Section 6.

Section 6 documents 8 CP-1 corrections but groups them into 5 rows — the BX/APO/TPG/CVC MET-VD-014 sentinel nullification counts as 4 corrections (one per firm) in the total of 8. The table presentation could mislead a reader into counting only 5 corrections. The correction log should either list all 8 individual corrections (one row per firm) or add a note that the final row represents 4 separate single-firm corrections.

---

## Recommended Actions

1. **[Critical — Pre-Report]** Reconcile DVR-ID conventions between `driver_ranking.json` (run4 ranking-order assignment) and `final_peer_set.json` (run2 inherited DVR-IDs). Either: (a) update `final_peer_set.json` inclusion rationales to use run4 DVR-IDs (DVR-001=AUM, DVR-005=G&A/FEAUM), or (b) add a DVR-ID crosswalk table in `final_peer_set.json` mapping run2 IDs to run4 IDs. Report-builder must not use both DVR-ID conventions simultaneously.

2. **[Critical — Pre-Report]** Revise peer selection rationales for FIRM-009 (TPG), FIRM-012 (STEP), FIRM-015 (HLNE), and FIRM-024 (ANTIN) to remove references to DE/share as a "stable driver" qualifying criterion. In run4, DE/share is classified as `unsupported` per `driver_ranking.json`. Replace with the actual qualifying criterion (e.g., DE/share rank position, business model analog, diversity fill) without overstating statistical validation.

3. **[Critical — Pre-Report]** Remove or correct all references to "stable" value driver classification in `final_peer_set.json` that cite run2-derived stable status (G&A/FEAUM, DE/share). These are not confirmed stable in run4. The methodology note in `driver_ranking.json` (`stable_driver_note`) must be consistently reflected in all downstream files.

4. **[Significant — Pre-Report]** Add a multicollinearity flag for AUM (DVR-001) and FEAUM (DVR-003) in `statistical_methodology.md` Section 2 or a new Section 7. Document the inter-driver rho ≈ 0.90 and explain that these are treated as a collinear pair — AUM is the primary ranked driver, FEAUM is a confirming signal but should not be treated as additive. Update playbook framing accordingly.

5. **[Significant — Pre-Report]** Perform and document LOO sensitivity for G&A/FEAUM × P/FRE (removing MAN and VCTR separately). Given that PAX is Q4 on this driver and it has the most direct strategic implication, the absence of LOO sensitivity for this driver is the most consequential methodological gap for the playbook.

6. **[Significant — Pre-Report]** Add a mechanical-artifact note to the FRE growth × EV/FEAUM interpretation in `driver_ranking.json` DVR-002. Acknowledge that the negative correlation may be partly structural (smaller FEAUM denominator → lower EV/FEAUM, smaller platforms grow FRE faster) rather than solely an investor execution discount. Use hedged language ("appears to reflect," not "confirms").

7. **[Significant — Next Run]** Add a partial temporal stability check for the two BH-significant findings (AUM × P/FRE and FEAUM × P/FRE) using the available FY2023 subset. Document the N achieved, the subset composition, and the direction/magnitude of rho. Even if the subset is insufficient for formal significance testing, directional consistency would meaningfully strengthen the findings.

8. **[Moderate — Pre-Report]** Add interpretation text to `driver_ranking.json` for DVR-004 through DVR-010 (all currently have empty `interpretation` fields). Minimum: one sentence on the theoretical mechanism and a note on statistical confidence for each.

9. **[Moderate — Pre-Report]** Populate `driver_ranking.json` `non_obvious_peers` section with correct FIRM-ID entries for TPG (FIRM-009), HLNE (FIRM-015), and ANTIN (FIRM-024) — all flagged `non_obvious_peer: true` in `final_peer_set.json` but absent from `driver_ranking.json`.

10. **[Moderate — Next Run]** Add VCTR-exclusion sensitivity test for efficiency metric correlations (DVR-005 G&A/FEAUM, DVR-009 Comp&Ben/FEAUM). The partial-alt classification flags VCTR as a comparability concern; a sensitivity test documents whether its inclusion distorts efficiency driver results.

11. **[Minor — Pre-Report]** Clarify the `minimum_n_report: 8` threshold in `correlation_results.json` — document its meaning in `statistical_methodology.md` and confirm no correlations with N < 12 appear in any ranked or reported results.

12. **[Minor — Pre-Report]** Add a currency standardization confirmation note to `statistical_methodology.md` confirming which exchange rates were applied for EUR, GBP, CHF, and CAD firm metrics and that the conversion was applied consistently in the standardized matrix.

13. **[Minor — Pre-Report]** Expand CP-1 correction log in `statistical_methodology.md` Section 6 to show all 8 individual corrections as separate rows (one per firm), not 5 grouped rows.

14. **[Minor — Pre-Report]** Clarify the BH boundary convention (weak vs. strict inequality) where FEAUM × P/FRE p-value = 0.002882 equals the BH threshold exactly. State explicitly that the weak inequality (≤) is applied, confirming FEAUM × P/FRE as BH-significant.
