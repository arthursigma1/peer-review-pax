# PAX-First Valuation Driver Analysis Methodology

Authoritative status: this markdown file is the source of truth for the VDA repository after the PAX-first upgrade. Generic reuse remains possible, but it is no longer the design center.

## 1. Design Center

The repository exists to answer a specific question for Patria Investments Limited (PAX):

1. What valuation drivers matter most for PAX inside alternative asset management?
2. Which peer actions provide credible evidence for those drivers?
3. Which actions are realistically transferable to PAX, at what burden, and with what margin risk?

The repository therefore defaults to a PAX decision memo, not a neutral play menu. Neutrality is preserved only in the peer-evidence stages.

### 1.1 PAX Business-Spec Inputs

For PAX-specific runs, two companion documents capture the commissioning team's
business framing:

- `docs/pax/pax-peer-assessment-framework.md`
- `docs/pax/pax-peer-strategy-ontology.md`

These documents are mandatory starting points for PAX work. They seed the
initial KPI hypotheses, deep-dive shape, and business-model ontology. They are
not closed rulebooks: agents may extend them, challenge them, or downgrade
their hypotheses when evidence requires it. Statistical governance, driver
classification, and report hard-fail rules remain governed by this methodology.

## 2. Architecture

The methodology is organized into three layers.

### Layer 1. Peer Evidence Layer

Purpose: collect and standardize peer evidence without forcing a PAX recommendation too early.

Outputs:
- `1-universe/peer_universe.json`
- `1-universe/source_catalog.json`
- `1-universe/metric_taxonomy.json`
- `2-data/quantitative_data.json`
- `2-data/strategy_profiles.json`
- `2-data/strategic_actions.json`
- `3-analysis/standardized_data.json`
- `3-analysis/correlations.json`
- `3-analysis/statistics_metadata.json`
- `3-analysis/driver_ranking.json`
- `3-analysis/final_peer_set.json`
- `4-deep-dives/platform_profiles.json`
- `4-deep-dives/asset_class_analysis.json`

Rules:
- Evidence-first
- Source-disciplined
- Comparability-aware
- No PAX recommendation language
- No hard-fact treatment of inferred operational prerequisites

### Layer 2. PAX Interpretation Layer

Purpose: translate peer evidence into PAX relevance and transferability.

Outputs:
- `5-playbook/value_principles.md`
- `5-playbook/platform_playbook.json`
- `5-playbook/asset_class_playbooks.json`
- `5-playbook/target_company_lens.json`

Rules:
- Every driver and play must include PAX relevance
- Mega-cap peers must be filtered through transferability controls
- Archetype-aware interpretation is mandatory
- Recommendations must address execution burden, tech/ops prerequisites, timing, and margin risk

### Layer 3. PAX Decision Layer

Purpose: convert interpreted evidence into a ranked, advisory PAX decision memo.

Outputs:
- `5-playbook/report_metadata.json`
- `5-playbook/final_report.html`

Rules:
- Default report mode is `pax_decision_memo`
- Final synthesis is explicitly advisory
- Peer evidence remains visible underneath the advisory layer
- No stable-driver claim may appear unless it satisfies the exact stable-driver rule below
- Target Company Lens extracts principles from peer evidence; does not prescribe specific actions. Language must be exploratory ("the evidence suggests", "peers that achieved [outcome] typically...") not prescriptive ("PAX should", "PAX must")
- Plays are framed as "observed mechanisms" and "peer-demonstrated patterns", never as "recommendations" or "action items"

## 3. Statistical Governance

The repository uses one statistical governance framework across methodology, prompts, schemas, metadata, and report text.

### 3.1 Discovery Standard

- Primary discovery framework: Benjamini-Hochberg FDR at `q = 0.10`
- Confirmatory badge: survives Bonferroni across the declared family of tests
- Primary p-value method for small-N rank correlations: permutation-based p-values where feasible
- Fallback p-value method: asymptotic t-approximation only when permutation is computationally infeasible; the fallback must be tagged explicitly in metadata

### 3.2 Confidence Taxonomy

Every tested relationship receives exactly one confidence label:

| Label | Required conditions |
|---|---|
| `high` | BH-significant, `abs(rho) >= 0.50`, CI excludes zero, leave-one-out robust, coverage adequate, comparability not poor |
| `moderate` | BH-significant or strong effect with one material limitation in CI width, coverage, or comparability |
| `directional` | Not BH-significant but effect is coherent enough for contextual interpretation; not suitable for strong strategic claims |
| `unsupported` | Weak, unstable, poorly covered, or materially non-comparable |

The confirmatory badge is additive. A relationship can be `high` plus `bonferroni_survivor`.

### 3.3 Stable-Driver Rule

`stable_driver_rule_id = stable_v1_two_of_three`

A driver may be called a `stable_value_driver` only if all of the following are true:

1. It is formal-ranking eligible on at least two valuation multiples.
2. `abs(rho) >= 0.50` on at least two valuation multiples.
3. At least one of those qualifying correlations survives BH correction.
4. The sign is directionally consistent across all evaluated multiples.
5. The best-supported qualifying multiple has a CI excluding zero and leave-one-out range `<= 0.15`.
6. Coverage is not flagged `poor`.
7. Comparability quality is not flagged `poor`.

If a third multiple is missing, low-coverage, or insufficiently comparable, the driver may still be `stable_value_driver` under this rule, but the missing support must be disclosed. If the driver fails any condition above, it may not be called stable anywhere in the repository.

### 3.4 Driver Classes

| Class | Rule |
|---|---|
| `stable_value_driver` | Satisfies `stable_v1_two_of_three` |
| `multiple_specific_driver` | `abs(rho) >= 0.50` on exactly one eligible multiple and does not satisfy stable rule |
| `contextual_driver` | Useful explanatory or decomposition signal, but not eligible for headline driver ranking |
| `unsupported` | Not defensible for strategic interpretation |

### 3.5 Required Statistical Flags

Every correlation and every ranked driver must carry:

- `coverage_quality`: `adequate`, `thin`, or `poor`
- `comparability_quality`: `good`, `mixed`, or `poor`
- `mechanical_overlap_flag`: `true` when the driver is partially algebraically coupled to the valuation multiple
- `independence_flag`: `independent`, `partially_confounded`, or `confounded`
- `p_value_method`: `permutation` or `asymptotic_t_with_disclosure`
- `confirmatory_badge`: `bonferroni_survivor` or `null`

Examples of `mechanical_overlap_flag = true`:
- EPS vs `P/DE`
- FRE vs `P/FRE`
- FEAUM vs `EV/FEAUM`

### 3.6 Sensitivity Protocol

All headline drivers must be assessed through the same protocol:

1. Leave-one-out stability
2. Matched-sample view for comparable firms
3. Archetype-stratified view
4. Coverage and comparability grading
5. Mechanical-overlap disclosure
6. Partial-correlation or confounding check where conceptually required

Temporal stability is mandatory when at least 12 firms have data for both FY T and FY T-1. When fewer than 12 firms have multi-year data, temporal stability is reported as a supplementary check with explicit N disclosure. The report must never silently compensate for missing temporal checks by upgrading confidence.

### 3.7 Minimum Sample Size Rule

A correlation may only be classified as `formal_ranking_eligible` if it is computed on N >= 12 firms with non-null values for both the driver metric and the valuation multiple.

Correlations computed on N < 12 are classified as `insufficient_sample` and excluded from headline driver ranking. They may appear in supplementary tables with explicit N disclosure.

Correlations computed on N < 8 are not reported.

### 3.8 Temporal Depth Requirement

Data collection targets a **5-year panel** (FY T-4 through FY T, where T is the most recent completed fiscal year). For the majority of the universe, FY T and FY T-1 are mandatory; FY T-2 through FY T-4 are collected on a best-effort basis.

Temporal depth serves two purposes:

1. **Temporal stability check:** correlations computed on FY T are compared against correlations on FY T-1 and FY T-2 (where available). A driver whose sign or magnitude changes materially across years receives a `temporally_unstable` flag and cannot be classified as `stable_value_driver`.
2. **Panel robustness (supplementary):** a firm × year panel may be constructed to increase the effective sample size. Panel-based correlations are reported as robustness checks only — they are not used for headline driver ranking due to within-firm autocorrelation. When reported, panel results must disclose: total observations, number of firms, number of periods, and clustering method (firm-clustered standard errors).

Required fields for temporal data:

- `period`: fiscal year label (e.g., `FY2020`, `FY2024`)
- `period_end_date`: exact fiscal year end date
- `fiscal_year_type`: `calendar` or `non_calendar` with month specified

### 3.9 Metric Derivation Rule

When a target metric is not directly disclosed but its component inputs are available in filings, the Data Collector must derive the ratio and tag it as `derived`.

Required fields for derived metrics:

- `derivation_method`: formula used (e.g., "total_compensation / management_fee_revenue")
- `component_sources`: list of source IDs for each input component
- `derivation_confidence`: `high` (both components from same filing), `medium` (components from different filings or periods), `low` (one or more components estimated)

Derived metrics with `derivation_confidence = high` are treated identically to directly disclosed metrics. Derived metrics with `derivation_confidence = low` are classified as `contextual_only`.

Common derivable metrics in alt-asset-management:

- `Compensation_to_Revenue` = total compensation and benefits / total management fee revenue (both disclosed in 10-K/20-F)
- `G&A_to_FEAUM` = general and administrative expense / fee-earning AUM (both typically disclosed)
- `Headcount_to_FEAUM` = total employees / FEAUM (employee count in 10-K, FEAUM in earnings supplement)
- `FEAUM_per_Employee` = FEAUM / total employees (inverse of above)

### 3.10 Universe Hygiene Rule

Firms are excluded from the correlation analysis universe when any of the following apply:

- Metric coverage below 15% of the taxonomy (fewer than 5 of ~31 metrics populated)
- Flagged as `model_incompatible` (e.g., principal investors or holding companies whose business model does not produce fee-based earnings)
- Zero valuation multiples available

Excluded firms remain in the peer universe for qualitative reference (strategy profiles, deep-dives) but do not contribute to Spearman rank correlations or driver rankings.

The effective correlation universe size (`N_effective`) must be disclosed in `statistics_metadata.json` and match the actual number of firms entering the correlation engine.

## 4. Peer Archetypes

Peers are not equally informative. Every firm in the deep-dive set must be assigned exactly one primary archetype and may have one secondary tag.

| Archetype | Definition | Use for PAX |
|---|---|---|
| `north_star_peer` | Mega-cap or structurally advantaged platform that shows the direction of travel | Inspiration only unless transferability controls are satisfied |
| `near_peer` | Similar enough to PAX on scale, geography, model, or client channel to inform near-term strategy | Highest practical relevance |
| `adjacent_peer` | Informative on one mechanism but not directly comparable overall | Use selectively and state the boundary |
| `anti_pattern_peer` | Useful mainly as a warning case | Use to stress-test PAX execution plans |

For every archetype assignment, the repository must document:

- what is informative
- what is not transferable
- what is inspiration only
- what is a warning

Matched-sample or stratified views are mandatory whenever north-star peers would otherwise dominate the conclusion.

## 5. Metric System

### 5.1 Driver Families

The metric taxonomy must include:

- Earnings and per-share economics
- Scale and fundraising
- Mix and diversification
- Efficiency and margin
- Operational Feasibility and Scalable Infrastructure
- Context-only market structure metrics

For PAX runs, the initial candidate set should be seeded from
`docs/pax/pax-peer-assessment-framework.md`. Metrics from that business spec may be
classified as `formal_ranking_eligible`, `contextual_only`, or `unsupported`,
but they may not be silently omitted without explanation.

### 5.2 Operational Feasibility and Scalable Infrastructure

For alternative asset managers, the taxonomy must attempt to collect:

- `Headcount_to_FEAUM`
- `FEAUM_per_Employee`
- `Compensation_and_Benefits_to_FEAUM`
- `G&A_to_FEAUM`
- `OpEx_Growth_minus_Fee_Revenue_Growth`
- `Constant_Currency_Revenue_Growth`
- `Integration_Costs_to_Revenue`
- `CapEx_to_FEAUM`
- technology / operations investment intensity
- reporting / control platform maturity indicators

Each metric must be classified as one of:

- `formal_ranking_eligible`
- `contextual_only`
- `unsupported`

Low-disclosure metrics may not be silently promoted into the ranking engine.

Low-disclosure metrics should be derived from component inputs when possible (see Section 3.9). A metric that achieves >= 60% coverage through derivation is promoted from `contextual_only` to `formal_ranking_eligible`.

### 5.3 FX Treatment

Cross-border standardization rules:

- Point-in-time balance sheet and valuation snapshot metrics use period-end FX
- Flow metrics use period-average FX unless fixed-base constant-currency disclosure is provided
- Growth metrics must be computed in local currency first

Required fields for cross-border growth metrics:

- `reported_usd_growth`
- `local_currency_growth`
- `constant_currency_growth`
- `fx_delta`
- `fx_material_flag`

`fx_material_flag = true` when FX explains a large enough share of observed growth variance to change interpretation.

Per-share metrics must carry a comparability note when multiple of the following coexist:

- currency translation
- share-count change
- accounting-basis difference
- material non-cash earnings distortion

## 6. Strategy Research Contract

Every strategic action record must include both the visible business action and the hidden execution work.

Required fields:

- action description
- timing
- scale
- strategy subtype
- thematic focus
- economic model
- business rationale
- observed metric impact
- operational prerequisites
- transferability constraints

Every operational prerequisite must carry:

- `evidence_class`
- `source_bias_tag`
- `confidence_level`
- `stated_or_inferred`

Source priority for operational prerequisites:

1. filings / annual reports / investor presentations
2. earnings transcripts / management commentary
3. reputable media / analyst coverage
4. job postings / vendor PRs as supporting evidence only

If an operational prerequisite is inferred, it must never be presented as hard fact.

## 7. Strategy Profile Contract

Each peer in `strategy_profiles.json` must map the business model across the
ontology grid and capture contextual market factors as a separate object. The
output is a JSON array of profile objects conforming to
`archive/schemas/vda/strategy_profile.schema.json` (archived; runtime validation
via `src/validation/vda_contracts.py`). Contextual market factors (TAM,
market share, governance, regulation) are market-context data, not
business-model choices, and must not be mixed into the ontology mapping.

## 8. Vertical and Sub-Type Analysis

Verticals must be broken into strategy sub-types. The repository may not treat `Private Equity`, `Credit`, `Infrastructure`, or `Solutions` as monoliths.

For PAX runs, the minimum business-model decomposition grid is defined in
`docs/pax/pax-peer-strategy-ontology.md`. Agents may add dimensions or values when
the evidence demands it, but they may not collapse the analysis below that
baseline without disclosure.

Minimum segmentation dimensions:

- `strategy_sub_type`
- `thematic_focus`
- `economic_model`

Each sub-type analysis must document:

- value-creation mechanics
- fee model
- operating model
- tech/data/reporting requirements
- scaling constraints
- margin sensitivities
- transferability barriers for PAX

## 9. Playbook Contract

Every `PLAY-*` entry must include:

- `What_Was_Done`
- `Observed_Metric_Impact`
- `Why_It_Worked`
- `PAX_Relevance`
- `Preconditions`
- `Operational_And_Tech_Prerequisites`
- `Execution_Burden`
- `Time_To_Build`
- `Margin_Risk`
- `Failure_Modes_And_Margin_Destroyers`
- `Transferability_Constraints`
- `Archetype_Relevance`
- `Evidence_Strength`
- `Recommendation_For_PAX`
- `source_citations` — array of PS-VD-NNN source IDs grounding the play's evidence

Every anti-pattern must identify the likely destruction mechanism, for example:

- duplicated overhead
- fragmented country platforms
- headcount growth outrunning AUM
- fee-rate dilution
- poor systems integration
- inadequate controls/reporting
- integration complexity
- channel mismatch
- overpaying for scale

## 10. PAX Evaluation Dimensions

Every driver and play must include explicit PAX evaluation on:

- scale fit
- geography fit
- client/distribution fit
- balance-sheet fit
- regulatory fit
- operating-model fit
- tech readiness
- data/reporting readiness
- time-to-build
- capital intensity
- margin risk
- execution complexity

Each play must end with:

- why this matters for PAX
- what would have to be true for PAX to execute it well
- why this may fail for PAX
- whether it is `near_term_feasible`, `medium_term_feasible`, or `aspirational`

## 11. Driver Decomposition for PAX

Headline drivers are not sufficient. The final report must include bridge logic for the drivers that matter most to PAX.

Required bridges:

### FEAUM growth bridge

- fundraising
- deployment
- M&A / acquired scale
- fee-rate dilution or uplift
- mix shift
- FX effects

### FRE margin bridge

- fee mix
- compensation ratio
- G&A leverage
- integration drag
- technology and operations spend
- temporary launch costs
- distribution costs

### EPS / per-share bridge

- operating earnings
- non-cash noise
- share count and SBC
- tax
- FX
- realization dependence

## 12. Report Contract

The final report defaults to a PAX decision memo with the following sections:

1. Decision summary for PAX
2. Methodology brief (analytical framework, universe size, primary method — link to Statistical Appendix)
3. What the peer evidence says
4. What is actually transferable to PAX
5. Ranked strategic implications for Patria
6. Driver decomposition bridges
7. Archetype-specific lessons
8. Margin-risk and execution-risk register
9. Governance cascade
10. Sources & References (numbered footnote list: title, date, bias tag, URL)
11. Statistical Appendix (full statistical parameters, confidence taxonomy, driver classification rules, sensitivity protocol, disclaimers)

Required report metadata:

- `report_mode = pax_decision_memo`
- `target_company`
- `target_ticker`
- `statistical_governance`
- `stable_driver_rule_id`
- `default_synthesis = pax_first`
- `peer_evidence_layer_present = true`
- `pax_interpretation_layer_present = true`
- `pax_decision_layer_present = true`

## 13. Validation and Hard Fail Rules

The repository must validate outputs against the JSON schemas under `archive/schemas/vda/` (archived; runtime validation via `src/validation/vda_contracts.py`) and the validator module under `src/validation/vda_contracts.py`.

Hard fail the run when:

- required fields are missing
- methodology metadata and report metadata disagree
- statistical method tags are inconsistent
- a play lacks PAX relevance
- a play lacks execution realism
- a stable-driver claim violates `stable_v1_two_of_three`

## 14. Artifact Contract Matrix

| Artifact | Layer | Purpose |
|---|---|---|
| `3-analysis/statistics_metadata.json` | Peer Evidence | Explicit statistical governance metadata |
| `4-deep-dives/platform_profiles.json` | Peer Evidence | Peer evidence by platform and archetype |
| `4-deep-dives/asset_class_analysis.json` | Peer Evidence | Strategy sub-type evidence and scaling constraints |
| `5-playbook/platform_playbook.json` | PAX Interpretation | PAX-scored plays and anti-patterns |
| `5-playbook/asset_class_playbooks.json` | PAX Interpretation | Vertical and sub-type implications for PAX |
| `5-playbook/target_company_lens.json` | PAX Decision | Ranked implications, feasibility, risk, governance cascade |
| `5-playbook/report_metadata.json` | PAX Decision | Contract metadata for report consistency checks |
| `5-playbook/final_report.html` | PAX Decision | Default final decision memo |

## 15. Generic Reuse

Generic reuse remains possible, but it is secondary. To adapt this methodology to another listed alternative asset manager:

1. swap `target_company` and `target_ticker`
2. keep the same peer-evidence engine
3. replace the PAX interpretation layer with the new target's transferability lens
4. preserve the same statistical governance and validation contract
