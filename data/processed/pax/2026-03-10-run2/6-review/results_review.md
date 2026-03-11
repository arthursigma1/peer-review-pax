# Results Review

## Summary

The 2026-03-10-run2 VDA analysis is analytically rigorous, with a coherent narrative anchored by the G&A/FEAUM stable driver finding and a well-developed Scale-Efficiency Paradox framework. The target company lens appropriately uses exploratory language and provides a three-tier governance cascade (PHL/Board, Management Committee, Per-BU). However, several critical issues weaken the statistical foundation, notable peer evidence from VD-B2 is absent from the playbook, and two significant analytical angles remain unexplored: the temporal dimension of driver improvement and the relationship between growth model type (organic vs. M&A) and valuation premium.

## Critical Issues

### 1. DVR-010 (G&A/FEAUM) Does Not Actually Satisfy the `stable_v1_two_of_three` Rule as Described

**File:** `driver_ranking.json`, `value_principles.md` (line 28-29)

The `stable_v1_two_of_three` rule requires |rho| >= 0.5 on at least two of three multiples. DVR-010 shows:
- P/FRE: rho = -0.6061 (passes)
- P/DE: rho = -0.5053 (passes)
- EV/FEAUM: rho = -0.0228 (fails)

This appears to satisfy the rule (2 of 3). However, the `avg_abs_rho` is 0.3781, which is lower than DVR-002 (FRE Growth YoY) at `avg_abs_rho` = 0.487. DVR-002 shows |rho| >= 0.5 on only P/DE (rho = -0.5463), failing on P/FRE (rho = -0.4765) and EV/FEAUM (rho = -0.4382). Yet DVR-002's average absolute rho across all three multiples is substantially higher than DVR-010's. The report does not address this tension: how can a driver with a lower average signal strength rank above a driver with higher average signal strength? The answer lies in the stable rule's threshold mechanism, but this should be disclosed explicitly because a board-level reader could misinterpret DVR-010 as the "strongest" signal when by average magnitude it is not.

Additionally, the EV/FEAUM correlation for DVR-010 (rho = -0.0228, p = 0.0196) has a suspiciously low p-value for such a weak correlation. With N=19, a Spearman rho of -0.0228 should have p >> 0.05. This suggests either a data error in the p-value or an unusual distributional artifact that the report does not explain.

### 2. FRE Growth (DVR-002) Negative Correlation Is Insufficiently Explained

**File:** `value_principles.md` (lines 137-143), `driver_ranking.json` (rank 2)

The report acknowledges the counterintuitive negative correlation between FRE Growth and valuation multiples but explains it only as a "denominator effect" or market discounting of unsustainable growth. This is a critical finding that undermines any narrative claim that improving FRE growth will improve valuation multiples. The report then proceeds to treat FRE growth as a positive signal throughout the playbook (e.g., Principle 4 in the final report states "FRE growth and G&A efficiency must be pursued simultaneously"). If the statistical evidence says higher FRE growth is associated with *lower* multiples, the playbook cannot logically recommend pursuing FRE growth for multiple expansion without a rigorous explanation of why the correlation sign reversal does not apply to PAX's situation. The current "denominator effect" hypothesis is plausible but untested; no partial correlation controlling for FRE level is presented.

### 3. Bootstrap Confidence Intervals Not Computed

**File:** `final_report.html` (lines 1291-1292)

The statistical appendix states: "Due to the absence of a scipy/numpy runtime environment, bootstrap CIs are parameterized but not computed in this run." This means the 10,000-resample bootstrap CIs that the methodology specifies are absent. The analysis relies entirely on asymptotic p-values from a sample of N=19-21, where asymptotic approximations are known to perform poorly. For a board-level deliverable, the absence of bootstrap CIs for the primary stable driver finding is a methodological gap that should be flagged as a limitation, not buried in the appendix.

### 4. DVR-001 (DE/share) Classification Inconsistency Across Documents

**File:** `driver_ranking.json` (line 541-554), `value_principles.md` (lines 82-128), `final_report.html` (line 1277-1289)

In `driver_ranking.json`, DE/share (MET-VD-001) is classified as `not_a_driver` with avg_abs_rho of 0.198, showing rho values of 0.138, 0.209, and 0.247 on the three multiples -- none exceeding 0.3. Yet `value_principles.md` devotes an entire section (Principle 2) to DE/share as a "Cross-Run Stable" driver, citing base-run evidence (rho = 0.857 on EV/FEAUM). The final report treats it as a co-equal pillar alongside DVR-010. The change-from-base-run section in `driver_ranking.json` provides appropriate context ("coverage gap is definitional"), but the prominence given to a metric that is `not_a_driver` in the current run's data creates a methodological tension: the analysis is selectively carrying forward a prior run's finding while not carrying forward the prior run's evidence for other metrics. The criteria for when base-run carryforward overrides current-run classification are not stated.

## Missed Insights

### 1. Partners Group Evergreen Model Not Surfaced as a Distinct Play

**File:** `strategic_actions.json` (ACT-VD-043, ACT-VD-044, ACT-VD-058), `platform_playbook.json`

Partners Group (FIRM-014) has the most developed evergreen product suite in the peer set: ~$55B in evergreen AUM (32% of total), 200,000+ wealth-channel clients, ELTIF-compliant European structures, and a new private markets royalties asset class. These actions (ACT-VD-043, ACT-VD-044, ACT-VD-058) represent a distinct playbook for wealth-channel distribution that is more transferable to PAX than BAM's infrastructure-centric permanent capital model. Yet the platform playbook does not contain a dedicated play for the Partners Group evergreen/wealth-channel model. PLAY-001 references OWL's permanent capital, and PLAY-006 references BAM's open-end vehicles, but the Partners Group model -- combining evergreen funds with technology-enabled distribution and ELTIF structures -- is absent as a standalone play despite strong evidence in VD-B2.

### 2. ICG-Amundi Distribution Partnership Not Analyzed

**File:** `strategic_actions.json` (ACT-VD-028), `platform_playbook.json`, `target_lens.json`

ICG's strategic partnership with Amundi (ACT-VD-028) -- where Amundi acquired a ~6-7% minority stake in ICG to distribute private markets products through its 2,000+ distribution partner network reaching 100 million end clients -- is a structurally novel distribution model that is highly relevant to PAX. PAX's identified weakness is international distribution infrastructure for open-end products. A similar partnership with a large LatAm or global distributor could address this gap without PAX building proprietary distribution. This action is mentioned nowhere in the platform playbook, asset class playbooks, or target company lens.

### 3. Cross-Firm Pattern: Post-IPO Expansion Phase Not Synthesized

**File:** `strategic_actions.json` (ACT-VD-049/TPG, ACT-VD-060/CVC, ACT-VD-062/CVC)

Three firms -- TPG (IPO Jan 2022), CVC (IPO Apr 2024), and PAX (IPO Jan 2021) -- share a common pattern: IPO followed by rapid credit platform scaling and distribution channel expansion. TPG acquired Angelo Gordon ($73B credit AUM) 18 months post-IPO. CVC scaled credit from EUR 25B to EUR 40B+ within 3 years of listing. PAX grew credit from $2B to $5B+ in the same timeframe. This "post-IPO credit acceleration" pattern is not synthesized as a cross-firm theme despite strong evidence across three firms. The pattern suggests that public company status unlocks distribution channels (insurance, wealth) that structurally accelerate credit platform growth.

### 4. Hamilton Lane Technology Moat (Cobalt Platform) Under-Explored

**File:** `strategic_actions.json` (ACT-VD-027), `platform_profiles.json` (STEP profile references Cobalt)

Hamilton Lane's Cobalt data platform (50,000+ private markets funds) and StepStone's data analytics represent a technology-driven efficiency model. The value_principles.md mentions STEP's Cobalt in passing (line 63) but does not develop the insight that technology platforms are a mechanism for achieving G&A efficiency independent of permanent capital. The driver_ranking shows Revenue/Employee (MET-VD-022) and FEAUM/Employee (MET-VD-019) as `not_a_driver`, which may explain the omission -- but the economic mechanism (technology reducing headcount per FEAUM dollar) is distinct from the permanent-capital mechanism and deserves at least a paragraph.

### 5. Blackstone's AI Infrastructure Theme ($70B+) Not Connected to Infrastructure Vertical Playbook

**File:** `strategic_actions.json` (ACT-VD-015), `asset_class_playbooks.json`

Blackstone's $70B+ commitment to AI infrastructure (data centers, CoreWeave) represents a structural shift in infrastructure deal flow toward digital infrastructure. This is directly relevant to PAX's infrastructure franchise, which is described as the "crown jewel" but whose sub-sector composition is characterized as traditional LatAm infrastructure (energy, transport, logistics). The asset class analysis identifies "Digital Infrastructure" as a sub-type but does not connect Blackstone's action (ACT-VD-015) to the question of whether PAX's infrastructure franchise should develop digital infrastructure origination in LatAm.

## Analytical Gaps

### 1. No Temporal Analysis of Driver Improvement and Valuation Re-Rating

**File:** `driver_ranking.json`, `value_principles.md`

The report's temporal stability section (`final_report.html`, line 1300) compares FY2023 vs. FY2024 correlations but does not analyze whether firms that improved on a stable driver over multiple years experienced valuation re-rating. For example: did CVC, which went from private to public (and improved G&A transparency) between 2023-2025, see its implied multiple converge toward peers? Did Carlyle's efficiency improvements under Schwartz (2023-2025) correlate with multiple recovery? This longitudinal question is the most decision-relevant for PAX (which is on a trajectory to improve G&A/FEAUM), yet the analysis is purely cross-sectional. The disclaimer acknowledges the point-in-time limitation (DISCLAIMER-3) but does not attempt even a qualitative assessment of whether improvement trajectories matter.

### 2. Organic vs. M&A Growth Model Not Analyzed as a Driver

**File:** `driver_ranking.json`, `strategic_actions.json`

The strategic_actions.json catalog contains explicit `action_type` classifications (M&A, organic_expansion, fundraise, product-launch, etc.). Firms in the peer set follow markedly different growth strategies: Apollo and KKR grew insurance AUM through M&A (Athene, Global Atlantic); Blue Owl was formed through a three-way SPAC combination; Ares grew European direct lending organically; PAX grew credit organically but acquired iGah3. The question of whether organic-growth-dominant firms command different multiples than M&A-dominant firms is not analyzed, despite the data being available. This is particularly relevant for PAX, which relies primarily on organic fundraising ($7.7B in 2025) and could inform whether acquisitive vs. organic scaling is more valued by the market.

### 3. Thin Coverage for Several Firms in the Universe

**File:** `platform_profiles.json`, `strategic_actions.json`

The deep-dive set covers 12 of 23 firms. The 11 firms not profiled include: Blackstone (FIRM-001), EQT (FIRM-010), TPG (FIRM-009), Partners Group (FIRM-014), Hamilton Lane (FIRM-015), ICG (FIRM-016), Tikehau (FIRM-020), Bridgepoint, Victory Capital, and Man Group (FIRM-011). Some of these have rich action catalogs (Partners Group: 4 actions; Hamilton Lane: 4 actions; ICG: 3 actions; Man Group: 3 actions; TPG: 4 actions) that are not reflected in platform profiles. Notably, Blackstone -- the largest firm in the universe with 5 actions including the $70B AI infrastructure commitment -- is excluded from platform profiles entirely. The exclusion criteria are stated as "final peer set" convergence, but the report does not acknowledge the information loss from excluding the largest firm in alternatives.

### 4. DVR-015 (Permanent Capital %) Treated as a Moderate Signal but Given Disproportionate Playbook Weight

**File:** `driver_ranking.json` (rank 6, classification: moderate_signal), `platform_playbook.json`, `target_lens.json`

Permanent Capital % (DVR-015) is classified as a `moderate_signal` with rho values of 0.40/0.41/0.21 -- none exceeding the 0.5 threshold for multiple-specific classification. Yet the playbook and target lens devote extensive attention to permanent capital strategies (PLAY-001, PLAY-006, PLAY-007, PLAY-008, PLAY-AC-005, PLAY-AC-006, PLAY-AC-008, PLAY-AC-009). At least eight plays reference permanent capital as a mechanism. The report does not reconcile this emphasis with the statistical evidence that Permanent Capital % is at best a moderate signal. The economic reasoning for permanent capital is sound, but the gap between statistical evidence (moderate) and strategic emphasis (central) should be acknowledged.

### 5. Consulting Source Hierarchy Compliance Not Fully Verifiable

**File:** `final_report.html`, `target_lens.json`

The methodology mandates that PS-VD-9xx consulting sources serve only as market context and cannot be the sole basis for firm-specific claims. The final report references four consulting sources (fn-47 through fn-50: BCG and Bain reports). The target_lens.json metadata states: "No consulting source is the sole basis for any recommendation or firm-specific claim." The report's usage appears compliant -- consulting citations appear alongside peer evidence in "market timing" contexts. However, the assertion in the target lens Principle 5 that "the $50-60B threshold is achievable within 2-3 years" (line 1026 of final_report.html) references only fn-8 (Patria's own filings) and is not framed as market context. This is acceptable per the hierarchy rules, but the precision of the "$50-60B" threshold is not grounded in any specific peer evidence or statistical analysis -- it appears to be an inference from PAX's current growth rate, which should be hedged with language like "suggests" rather than the current direct framing.

## Suggested Additions

### 1. Add a Sensitivity Table Showing PAX's Blended G&A/FEAUM Under Different GPMS Scaling Scenarios

The analysis repeatedly states that GPMS scaling is the "highest-impact efficiency vector" but never quantifies the impact. A simple table showing: (a) PAX's current blended G&A/FEAUM at $40.8B FEAUM, (b) the blended ratio at $50B FEAUM (with $10B incremental from GPMS), (c) the blended ratio at $60B FEAUM -- would make the strategic argument concrete and decision-relevant for the board. The data required (PAX's current G&A expense, GPMS marginal G&A cost) is available from PS-VD-057/058.

### 2. Add a "Driver Improvement Trajectory" Section for PAX

Rather than relying solely on cross-sectional quartile positions, provide an estimated 2-3 year trajectory for PAX's position on each ranked driver, given stated strategic actions. This would answer the board's implicit question: "If we execute the GPMS and infrastructure vehicle strategies, when do we move from Q4 to Q3 or Q2 on efficiency drivers?" Even a directional assessment (with appropriate hedging) would be more actionable than the current static quartile positioning.

### 3. Explicitly Address Whether the FRE Growth Negative Correlation Undermines the Growth-Efficiency Narrative

The Carlyle cautionary case (efficiency without growth = value trap) is persuasive qualitatively, but the statistical evidence says the *opposite* of what the narrative implies: higher FRE growth correlates with *lower* multiples. Either provide a rigorous reconciliation (partial correlation, subsample analysis excluding outliers, or level-vs-growth decomposition) or add a disclaimer that the growth argument is based on qualitative peer evidence, not the statistical correlation.

### 4. Include a Distribution Partnership Play Modeled on ICG-Amundi

The ICG-Amundi partnership (ACT-VD-028) is the most structurally novel distribution mechanism in the action catalog and directly addresses PAX's identified distribution gap for open-end products. A dedicated play analyzing whether PAX could establish a similar partnership with a global or regional distributor (e.g., a large Latin American bank or insurance group) would strengthen the open-end infrastructure vehicle recommendation.

### 5. Include Partners Group Evergreen/Wealth Channel Model as a Reference Case

Partners Group's 32% evergreen AUM, 200,000+ wealth clients, and ELTIF structures (ACT-VD-043, ACT-VD-044) represent the most developed wealth-channel playbook in the peer set. Given that PAX's governance cascade identifies international distribution as the key prerequisite for open-end vehicle success, the Partners Group model deserves explicit treatment as a reference for how a mid-scale manager (PGHN at $185B is closer to PAX's trajectory than BAM at $1T+) built wealth distribution.
