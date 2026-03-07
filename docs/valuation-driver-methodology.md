# Valuation Driver Analysis — Reusable Methodology

## Overview

Prompt-driven analytical workflow to identify which operational and financial metrics correlate with valuation multiples across a publicly listed peer universe, catalog the strategic actions peers have executed to move those metrics, and synthesize findings into an empirically grounded strategic playbook. No custom code — executed entirely through Claude Code agent teams.

The pipeline is organized into three phases — **Map the Industry**, **Gather Data**, and **Find What Drives Value** (Phase 1); **Deep-Dive Peers** (Phase 2); and **Build the Playbook** (Phase 3) — with two parallel tracks running throughout Phase 1. The output is a navigable HTML playbook organized by value driver, not by peer firm.

## Research Questions

Applied to any subject company `{COMPANY}` (`{TICKER}`) in `{SECTOR}`, the pipeline addresses three interrelated questions:

1. Which operational and financial metrics exhibit statistically significant correlation with valuation multiples across the universe of publicly listed `{SECTOR}` firms?
2. What concrete strategic actions have peer firms executed to move those metrics?
3. What is the resulting menu of empirically grounded strategic plays, organized by value driver, that a firm in this sector could evaluate for adoption?

The pipeline produces an analytically rigorous, peer-centric strategic playbook. It is explicitly **not** a performance evaluation of `{COMPANY}`, and it does not prescribe a course of action. `{COMPANY}`'s current strategy enters the analysis only if leadership chooses to compare the playbook against their own trajectory.

## Analytical Paradigm

### Peer-Centric Framing

The fundamental analytical posture is peer-centric rather than `{COMPANY}`-centric. A `{COMPANY}`-centric analysis would treat `{COMPANY}`'s strategic priorities as the baseline and evaluate peers relative to those priorities — a design that introduces confirmation bias and limits the actionable insight surface. A peer-centric analysis studies what peers are doing on their own terms, synthesizes cross-sectional patterns, and produces a playbook independent of any one firm's prior commitments.

`{COMPANY}`'s current strategy is explicitly withheld as a reference point during Phase 1. It becomes relevant, if at all, only in the consumer's own interpretation of the final playbook.

### Hybrid Statistical-Qualitative Approach

The quantitative universe of publicly listed firms in most specialized sectors comprises approximately 20–30 firms globally. This sample size is insufficient for reliable multiple regression analysis for the following reasons:

- **Degrees of freedom constraint.** With N ≈ 25 observations and 15+ candidate predictor variables, a conventional multiple regression consumes all available degrees of freedom and produces unstable estimates.
- **Multicollinearity.** Several candidate metrics are structurally correlated (e.g., FEAUM growth and total AUM growth can be expected to exhibit ρ > 0.8), rendering coefficient estimates unreliable and confidence intervals uninformative.
- **Overfitting risk.** In small samples, a model with many predictors fits idiosyncratic noise rather than systematic patterns.
- **Endogeneity.** Valuation multiples affect capital-raising capacity, which affects AUM growth — simultaneity that OLS cannot address without instrumental variables unavailable in this context.

The hybrid approach resolves these constraints by separating the analysis into two methodologically distinct tracks:

- **Quantitative layer (Track A):** Spearman rank correlation analysis applied to each driver metric against three valuation multiples. Spearman is non-parametric, robust to outliers and non-normality, and appropriate for ordinal rankings when N is small. It produces interpretable, defensible correlation coefficients without requiring distributional assumptions that make regression unreliable at this sample size.
- **Qualitative layer (Track B):** Deep-dive strategy research per firm, mapping the causal chain from strategic actions to metric movements to valuation impact.

The quantitative layer identifies **what matters** — which metrics correlate with higher valuation. The qualitative layer identifies **how to move it** — which strategic actions peers have demonstrated to be effective at shifting those metrics. Neither layer is analytically sufficient alone; their combination produces conclusions that are simultaneously data-anchored and causally interpretable.

### Independence from the Strategy Drift Pipeline

The Valuation Driver Analysis operates independently of the Strategy Drift Detection pipeline. It does not require `stage_2_pillars.json` or any drift pipeline output as a prerequisite. PIL-* pillar identifiers are not referenced within this pipeline. This independence is deliberate: the playbook should be constructed from peer evidence alone, without being shaped by `{COMPANY}`'s declared strategic architecture.

## Pipeline Architecture

Three phases, five steps (with two parallel tracks in Phase 1):

```
Phase 1: Map the Industry + Gather Data + Find What Drives Value
┌─────────────────────────────────────────────────────────────────────┐
│  Track A (Quantitative)              Track B (Qualitative)          │
│  Step 1: Map the Industry (VD-A0)    Step 1: Map Sources (VD-B0)   │
│  Step 1: Define Metrics (VD-A1)      Step 2: Extract Strategies     │
│  Step 2: Collect Data (VD-A2)                 (VD-B1)              │
│  Step 3: Standardize (VD-A3)         Step 2: Catalog Actions        │
│  Step 3: Correlate (VD-A4)                    (VD-B2)              │
│  Step 3: Document Stats (VD-A4b)                                    │
│  Step 3: Rank Drivers (VD-A5)                                       │
└─────────────────────────────────────────────────────────────────────┘
                            │
                   Step 3: Convergence (VD-C1)
               (Final Peer Set Selection)
                            │
Phase 2: Deep-Dive Peers
┌─────────────────────────────────────────────────────────────────────┐
│  Step 4: Platform Deep-Dives (VD-D1)                                │
│  Step 4: Asset Class Deep-Dives (VD-D2)                             │
└─────────────────────────────────────────────────────────────────────┘
                            │
Phase 3: Build the Playbook
┌─────────────────────────────────────────────────────────────────────┐
│  Step 5: Value Creation Principles (VD-P1)                          │
│  Step 5: Platform Strategic Menu (VD-P2)                            │
│  Step 5: Asset Class Playbooks (VD-P3)                              │
│  Step 5: Final Navigable Report (VD-P4)                             │
└─────────────────────────────────────────────────────────────────────┘
```

## Phase 1: Map the Industry + Gather Data + Find What Drives Value

### Track A — Quantitative

#### Stage VD-A0: Map the Industry (Universe Identification)

**Agent:** Industry Scanner

Catalog all publicly listed firms in `{SECTOR}` globally. The target universe is approximately 20–30 firms. Classify each firm by business model composition:

| Class | Definition |
|---|---|
| `pure-play` | >= 90% of revenue from the target sector activity |
| `majority-sector` | 60–89% of revenue from target sector activity |
| `partial-sector` | Meaningful sector segment but majority revenue from other activities |

For each firm, record: full legal name, ticker, exchange, classification, latest relevant scale metric (e.g., AUM in USD for asset managers), primary product lines or strategies, inclusion rationale, and exclusion rationale for omitted candidates.

**Output:** `1-universe/peer_universe.json`

#### Stage VD-A1: Define Metrics (Metric Taxonomy)

**Agent:** Metrics Designer

Define all metrics organized by category. Metrics divide into two roles:

- **Driver candidates** (independent variables): operational and financial metrics that management can, in principle, influence
- **Valuation multiples** (dependent variables): the market pricing metrics against which drivers are tested

A third category — **market structure metrics** — is collected as contextual data only and is explicitly excluded from the correlation analysis. Market structure metrics (e.g., trading volume, passive ownership percentage, free float) are consequences of investor behavior, not actions management can take. Including them would identify correlations with no actionable implications.

**Driver candidate categories:** Earnings, Scale, Organic Growth, Mix and Diversification, Efficiency, Fee Quality, Operational Feasibility & Scalable Infrastructure (adapt categories to `{SECTOR}`)

**Sector overlay — Operational Feasibility & Scalable Infrastructure:**

This category captures whether a firm's operating model can absorb growth without proportional cost escalation. The specific metrics depend on the sector:

- **Alternative asset managers:** preferred metrics (when disclosed):
  - `Headcount_to_FEAUM` — total headcount divided by fee-earning AUM
  - `FEAUM_per_Employee` — fee-earning AUM per full-time employee
  - `Compensation_and_Benefits_to_FEAUM` — total compensation and benefits expense as a percentage of FEAUM (or nearest disclosed proxy such as comp-to-management-fee-revenue)
  - `G&A_to_FEAUM` — general and administrative expense as a percentage of FEAUM
  - `OpEx_Growth_minus_Fee_Revenue_Growth` — trailing difference between operating expense growth rate and fee revenue growth rate; positive values indicate cost outpacing revenue
  - `Constant_Currency_Revenue_Growth` — revenue growth rate after removing FX translation effects (see VD-A3 FX methodology)
  - `Integration_Costs_to_Revenue` — integration and restructuring charges as a percentage of total revenue (only when separately disclosed in filings)
  - `CapEx_to_FEAUM` — capital expenditure as a percentage of FEAUM (only when technology or software capex is separately identifiable in filings)
- **Other sectors:** map this category to the closest sector-specific "cost-to-scale" metrics (e.g., revenue per employee, SG&A-to-revenue, integration cost ratios). Do not force FEAUM-based metrics into non-alt-manager sectors.

**Coverage rule:** any metric in this category with fewer than 60% of universe firms reporting is classified as `contextual-only` and excluded from the formal driver-ranking correlation engine (VD-A4). It may still appear in context tables and deep-dive narratives.

**Valuation multiples:** Select three multiples that capture different facets of how the market prices businesses in `{SECTOR}`. Using three rather than one is deliberate — a metric that correlates with all three is classified as a **stable driver**; a metric correlating with only one is a **multiple-specific driver**.

For each metric, record: full name, abbreviation, unit of measure, calculation method, and any known definitional heterogeneity across firms.

**Output:** `1-universe/metric_taxonomy.json`

#### Stage VD-A2: Collect Data (Data Collection)

**Agent:** Data Collector

Extract quantitative data for all firms in the VD-A0 universe across all VD-A1 driver metrics and valuation multiples. Time coverage: most recent completed fiscal year (FY1), prior fiscal year (FY2), and three-year historical data where available.

Primary sources: earnings releases, annual reports (20-F / 10-K / equivalent), investor day presentations, earnings supplements, and a filesystem drop zone for proprietary or subscriber-gated data.

For each data point, record: firm ID, metric ID, value, period, currency, source ID, source bias tag, confidence rating, and extraction notes.

Missing data is recorded as `null` with an explicit `missing_reason`. Estimation and interpolation are prohibited; only directly sourced values are recorded.

**Output:** `2-data/quantitative_data.json`

#### Stage VD-A3: Standardize (Data Standardization)

**Agent:** Metrics Designer

Normalize VD-A2 data for cross-sectional comparability:

1. **Currency conversion and FX handling:**
   - **Point-in-time metrics** (stock prices, balance-sheet items, AUM snapshots): convert to USD using **period-end exchange rates**.
   - **Flow metrics** (revenue, expenses, earnings, cash flows): convert using **period-average exchange rates** unless the firm reports a fixed-base constant-currency figure.
   - **Growth metrics**: calculate growth in the firm's **local reporting currency first**, then compute:
     - `reported_USD_growth` — growth rate computed from USD-translated figures
     - `local_currency_growth` — growth rate computed in the firm's reporting currency before translation
     - `constant_currency_growth` — growth rate excluding FX translation effects (use firm-disclosed constant-currency figures when available; otherwise approximate using prior-period average rates applied to current-period local-currency figures)
     - `fx_delta = reported_USD_growth − local_currency_growth`
   - **FX materiality flag (`FX_MATERIAL`):** flag a metric when `abs(fx_delta)` exceeds the greater of:
     - 500 basis points, **or**
     - 30% of the absolute reported growth magnitude (i.e., `abs(fx_delta) > 0.30 × abs(reported_USD_growth)`)
   - **Documentation:** for every currency conversion, record: FX rate used, rate type (period-end or period-average), rate date, rate source, and whether average-rate or fixed-base translation was applied.
   - **Cross-border per-share comparability note:** when currency mismatch, share-count changes, and accounting-basis differences coexist for a per-share metric, append a comparability caveat to that data point.
2. **Fiscal year alignment:** align to trailing twelve months (TTM) or calendar year basis. Flag firms with non-calendar fiscal years and specify the exact period covered.
3. **Accounting definition reconciliation:** non-GAAP and non-IFRS metrics vary materially in definition across firms. Document each firm's disclosed definition and flag metrics where definitional heterogeneity is material enough to affect cross-firm comparisons.
4. **Coverage flagging:** mark any metric for which fewer than 60% of universe firms report as "low coverage." Low-coverage metrics may still appear in context tables and deep-dive narratives but are excluded from the formal driver-ranking engine (VD-A4) unless explicitly approved for statistical testing.
5. **Outlier flagging:** values exceeding two standard deviations from the cross-sectional mean are flagged for manual review before inclusion in correlation analysis.

**Output:** `3-analysis/standardized_data.json`

#### Stage VD-A4: Find What Drives Value (Correlation Analysis)

**Agent:** Statistical Analyst

Compute Spearman rank correlation coefficients for each driver metric against each valuation multiple, yielding approximately N × M pairwise correlations (where N is the number of driver candidates and M is the number of valuation multiples, typically 3).

**Classification of results:**

| Class | Criterion |
|---|---|
| Stable value driver | ρ > 0.5 across all three valuation multiples |
| Multiple-specific driver | ρ > 0.5 for exactly one multiple |
| Moderate signal | 0.3 ≤ ρ ≤ 0.5 for at least one multiple |
| Not a driver | ρ < 0.3 for all three multiples |

Following classification, test for multicollinearity among the top-ranked stable drivers. Where two drivers exhibit ρ > 0.7 with each other, document the pair, assess which has stronger theoretical grounding as a causal antecedent of valuation, and flag the risk of attributing independent explanatory power to collinear variables.

**Output:** `3-analysis/correlations.json`

#### Stage VD-A4b: Document Statistics (Statistical Documentation)

**Agent:** Statistical Analyst

All statistical choices must be explicitly justified, all limitations must be disclosed, and all confidence intervals must be reported. This stage produces a standalone methodology document that accompanies the final output.

**Methods and justification:**
- Document the choice of Spearman over Pearson rank correlation: robustness to non-normality, monotonic but not necessarily linear relationships, resistance to outlier influence
- Document explicitly why multiple regression was not employed: insufficient degrees of freedom, high multicollinearity, overfitting risk, endogeneity (see Analytical Paradigm section above)

**Bootstrap confidence intervals:**
- 1,000 bootstrap iterations per correlation coefficient
- Report 95% confidence intervals for each ρ estimate
- Confidence intervals that include zero are flagged regardless of point estimate magnitude

**Multiple comparisons correction:**
- Apply Bonferroni correction to the full family of hypothesis tests
- Report corrected p-values alongside uncorrected p-values

**Confidence classification:**

| Class | Criterion |
|---|---|
| High confidence | p < 0.01 after Bonferroni correction |
| Moderate confidence | p < 0.05 after correction |
| Suggestive | p < 0.10 after correction |
| Not significant | p >= 0.10 after correction |

**Sensitivity analyses:**
- Leave-one-out analysis: recompute each significant correlation excluding each firm in turn; report whether the finding is robust or driven by a single influential observation
- Temporal stability check: compute correlations on FY1 data and FY2 data separately; flag correlations present in one year but absent in the other

**Mandatory disclaimers (reproduced verbatim in the final report):**
- *Correlation does not imply causation.* A positive correlation between a metric and a valuation multiple may reflect reverse causation, common-cause confounding, or chance.
- *Survivorship bias.* The universe consists of currently listed firms. Firms that were delisted, acquired, or failed are excluded, potentially skewing the analysis toward characteristics associated with survival rather than value creation per se.
- *Point-in-time limitation.* The analysis reflects conditions as of the most recent data collection period. Correlations may not be stable across market cycles.
- *Small-N limitation.* With approximately 20–30 observations, statistical power is limited. Findings should be treated as hypothesis-generating, not as definitive causal claims.
- *Endogeneity.* Several candidate drivers may be simultaneously caused by and causally related to valuation multiples. No instrumental variable analysis is conducted.
- *Definition heterogeneity.* Non-GAAP metrics are not standardized across firms. Correlations involving such metrics are subject to measurement error arising from definitional inconsistency.

**Output:** `3-analysis/statistical_methodology.md`

#### Stage VD-A5: Rank Drivers (Value Driver Ranking)

**Agent:** Statistical Analyst

Rank the top five to six stable drivers by average absolute Spearman coefficient across the three valuation multiples. For each top-ranked driver:

- Provide a per-driver ranking of all firms in the universe (creating a quartile map)
- Identify firms in the top quartile as potential role models for that driver
- Identify **non-obvious peers** — firms that did not appear in the initial qualitative peer list (VD-B0) but surface in the top quartile on two or more stable drivers
- Flag non-obvious peers for possible inclusion in the qualitative deep-dive set

**Output:** `3-analysis/driver_ranking.json`

---

### Track B — Qualitative

Track B runs in parallel with Track A. The qualitative fieldwork does not wait for quantitative results; it begins simultaneously with Track A, ensuring that rich qualitative profiles already exist for the likely deep-dive candidates before the Convergence stage is reached.

#### Stage VD-B0: Map Sources (Source Mapping)

**Agent:** Source Cataloger

Catalog sources for the initial qualitative peer set, which comprises approximately 12–15 firms identified as the most strategically instructive candidates. These are drawn from the broader quantitative universe but selected for strategic depth and public information availability.

Assign **PS-VD-NNN** IDs to all sources. For each source, record: firm, title, date, document type, bias tag, URL or filing reference, and relevance notes.

**Bias tags:** `company-produced`, `regulatory-filing`, `third-party-analyst`, `journalist`, `industry-report`, `peer-disclosure`

**Non-obvious sources** that provide independent, non-management-filtered perspectives should be actively sought:
- **Large LP board documents.** Major institutional investors publish board meeting materials that include independent assessments of GP strategy, fee terms, and positioning
- **Job postings.** Active recruitment data reveals organizational priorities, capability gaps, and strategic initiatives before public announcement
- **Patent and trademark filings.** Product development directions and branding strategy
- **Conference speaker assignments.** Presence at major sector events signals positioning and brand strategy ambitions

**Output:** `1-universe/source_catalog.json`

#### Stage VD-B1: Extract Strategies (Strategy Extraction)

**Agent:** Strategy Researcher

For each firm in the qualitative peer set, extract a standalone strategic profile. Profiles classify firms along ten dimensions. Profiles are self-contained; they do not reference `{COMPANY}`, do not compare firms against `{COMPANY}`, and do not evaluate firms against any external benchmark.

**Ten classification dimensions** (adapt dimension labels to `{SECTOR}`):

| Dimension | Description |
|---|---|
| Geographic reach | Domestic / regional / global; primary markets |
| Product / strategy focus | Core offerings by product or strategy type |
| Product mix | Distribution of revenue or AUM across product lines |
| Origination model | Proprietary vs. intermediated deal or client flow |
| Vehicle type emphasis | Closed-end / fixed-term vs. open-end / perpetual vs. other |
| Capital source | Institutional vs. retail / wealth channel vs. corporate |
| Distribution strategy | Direct vs. third-party networks vs. platform arrangements |
| Client segment | Sovereign / large institutional vs. mid-market vs. retail |
| Growth model | Organic / same-strategy vs. geographic expansion vs. product adjacency vs. M&A |
| Stated strategic priorities | Top three to five verbatim or closely paraphrased priorities from the most recent Investor Day or annual report |

**Output:** `2-data/strategy_profiles.json`

#### Stage VD-B2: Catalog Actions (Action Cataloging)

**Agent:** Strategy Researcher

For each firm in the qualitative peer set, catalog concrete strategic actions taken in the prior two to three years. For each action, record:

- Action type: `M&A`, `product-launch`, `geographic-expansion`, `distribution-shift`, `capital-structure-change`, `organizational-change`, `technology-operations`
- Description of the action
- Stated rationale from management communications
- Observable metric impact where disclosed (quantitative or directional)
- Timeline: announced, closed, operational
- Source citation (PS-VD-NNN)

**Operational Prerequisites Extraction:**

For every strategic action identified (M&A, fund launch, product launch, distribution expansion, technology initiative, operating platform acquisition), extract concurrent `Operational_Prerequisites` — the hidden infrastructure, systems, and organizational changes required to execute the action. Required subfields:

| Subfield | Description |
|---|---|
| `systems_integration` | ERP, portfolio management, or front-office system consolidation |
| `data_reporting_stack` | Data warehouse, LP reporting, regulatory reporting upgrades |
| `qa_controls_reconciliation` | Quality assurance, NAV reconciliation, operational control changes |
| `fund_admin_servicing` | Fund administration, transfer agency, or investor servicing changes |
| `compliance_risk_treasury` | Compliance infrastructure, risk management frameworks, treasury operations |
| `hiring_org_redesign` | Hiring waves, organizational restructuring, team integration |
| `geographic_integration` | Cross-border operational complexity, local entity setup, regulatory licensing |

**Search priority for prerequisites (in order):**
1. Filings, annual reports, investor day materials — highest trust
2. Earnings transcripts and prepared remarks — moderate trust
3. Reputable media and analyst coverage — moderate trust
4. Job postings and vendor press releases — supporting evidence only; **never** sufficient as the sole basis for a `GROUNDED` verdict

**Evidence standards:**
- Record `source_bias_tag` and `evidence_class` (directly documented / corroborated / inferred) for every prerequisite.
- If a prerequisite is inferred from circumstantial evidence rather than directly documented, mark it `INFERRED` and require hedged language in all downstream outputs ("the acquisition likely required…", "this expansion appears to have involved…").
- No operational prerequisite may be labeled `GROUNDED` if it relies only on job postings, vendor press releases, or management commentary without corroboration from at least one filing or independent source.

**Output:** `2-data/strategic_actions.json`

---

### Convergence: Stage VD-C1

**Agent:** Insight Synthesizer

The Convergence stage merges the outputs of Track A and Track B to determine the final peer set for Phase 2 deep-dives. The target size is 9–12 firms.

**Scoring criteria for each candidate peer:**

| Criterion | Description |
|---|---|
| Quantitative relevance | Quartile position on two or more stable value drivers from VD-A5 |
| Qualitative relevance | Strategic instructiveness of actions in VD-B2; diversity of approaches represented |
| Commissioning priority | Any peers specifically nominated by the commissioning team |

**Inclusion rules:**
- Auto-include: any firm in the top quartile on two or more stable drivers
- Include as cautionary case: any firm in the bottom quartile with well-documented strategic actions — negative examples are instructive
- Flag for review: any non-obvious peer surfaced by VD-A5 that does not appear in the VD-B0 initial list
- Minimum coverage requirement: at least two sources per included firm before deep-dive begins

**Output:** `3-analysis/final_peer_set.json` — includes each firm's ID, inclusion rationale, exclusion rationale for omitted candidates, and any flagged source gaps requiring additional collection before Phase 2.

## Phase 2: Deep-Dive Peers

### Stage VD-D1: Platform-Level Deep-Dives

**Agent:** Platform Profiler

For each of the 9–12 firms in the final set, produce a structured platform-level profile containing six sections:

1. **Identity and scale** — key scale metrics, geography, product mix, listing history, ownership structure
2. **Strategic agenda** — top three to five stated priorities, sourced from the most recent Investor Day or annual report
3. **Key actions (two to three year horizon)** — full catalog from VD-B2, with source citations, organized by action type
4. **Performance on stable value drivers** — scores on the top five to six drivers from VD-A5, with cross-sectional quartile position and brief context
5. **Value creation narrative** — an analytical account of what makes this firm trade at its current premium or discount relative to peers; the aim is to articulate the causal theory connecting strategy to valuation
6. **Transferable insights** — three to five specific lessons that a different firm in `{SECTOR}` could consider, stated independently of `{COMPANY}`

**Output:** `4-deep-dives/platform_profiles.json`

### Stage VD-D2: Vertical-Level Deep-Dives

**Agent:** Sector Specialist

Parallel to platform-level deep-dives, conduct vertical-specific deep-dives for the product verticals or business lines relevant to `{COMPANY}`'s business. Each vertical deep-dive identifies the best-in-class practitioners within that vertical, analyzes their winning strategies, and documents vertical-specific metric drivers and emerging trends.

**Strategy Sub-Type Segmentation:**

Do not stop at broad verticals such as "Private Equity" or "Credit." Within each vertical, segment by:
- **Strategy Sub-Type** — the specific investment approach or product variant
- **Thematic Focus** — the sector or structural theme the strategy targets
- **Economic Model** — the fee structure, margin profile, and capital intensity

For alternative asset managers, illustrative sub-types include (adapt to `{SECTOR}` for non-alt-manager universes):

| Vertical | Sub-Types |
|---|---|
| Private Equity | Mid-market operational turnaround, large-cap buyout, sector-specialist growth equity, secondaries-led PE, GP-led continuation vehicles |
| Credit | Direct lending, asset-backed finance, infrastructure debt, opportunistic credit, insurance-oriented credit, CLO management |
| Real Estate | Logistics platforms, residential niches, data centers, real estate credit, core/core-plus perpetual vehicles |
| Infrastructure | Core/super-core, value-added, energy transition, digital infrastructure, transport/logistics |
| Solutions | Secondaries, GP-leds, bespoke mandates, advisory-heavy allocation solutions, co-investment programs |

For each sub-type, document:
- **Operational value-creation levers** — what the GP does to generate returns beyond capital allocation (e.g., procurement optimization, add-on acquisition playbooks, operational improvement teams)
- **Fee model and margin structure** — management fee rates, performance fee mechanics, catch-up provisions, and how they differ from the vertical's flagship structure
- **Talent model** — team composition, key-person dependencies, compensation structure, recruiting pipeline
- **Data, reporting, and technology requirements** — portfolio monitoring, LP reporting, regulatory compliance, valuation methodology
- **Scaling constraints** — deployment capacity, fundraising cycle, market depth, deal-flow limitations
- **Transferability barriers** — what prevents a firm from entering this sub-type (regulatory, capability, brand, track-record requirements)

For each vertical, the deep-dive produces:
- Profiles of the best-in-class practitioners and the basis for that classification
- Documentation of winning strategies and evidence for their effectiveness, segmented by strategy sub-type
- Vertical-specific metric drivers (which of the stable drivers from VD-A5 are most salient within this vertical)
- Emerging trends and structural changes affecting the vertical
- Sub-type-level transferability analysis (which sub-types are accessible to new entrants vs. requiring established track records)

**Output:** `4-deep-dives/asset_class_analysis.json`

## Phase 3: Build the Playbook

### Stage VD-P1: Value Creation Principles

**Agent:** Insight Synthesizer

Synthesize the five to six stable value drivers from VD-A5 into a set of industry-level principles. For each driver:

- Restate the statistical finding in plain language, accompanied by the full statistical documentation from VD-A4b
- Explain the underlying economic mechanism: why should this metric correlate with valuation in this industry?
- Identify which firms illustrate the principle most clearly (from VD-D1 findings)
- Note the limitations and boundary conditions on the principle

This section functions as the evidentiary foundation for the strategic menus that follow.

**Output:** `5-playbook/value_principles.md`

### Stage VD-P2: Platform Strategic Menu

**Agent:** Report Composer

Organize the findings from Phase 2 into a strategic menu at the platform level. The organization is **by value driver, not by peer firm**. For each stable value driver:

- Enumerate the proven strategic plays that peers have executed to improve performance on that driver
- For each play, include all mandatory fields (see below)

**Mandatory fields for every PLAY-NNN:**

| Field | Description |
|---|---|
| `What_Was_Done` | Concrete description of the action: who, what, when, at what scale |
| `Observed_Metric_Impact` | Quantitative or directional metric movement with time horizon and source citation |
| `Prerequisites` | Strategic and market prerequisites that were in place before execution |
| `Operational_And_Tech_Prerequisites` | Systems integration, data/reporting stack, compliance infrastructure, fund admin changes, and hiring that were required (sourced from VD-B2 operational prerequisites) |
| `Execution_Burden` | Estimated resource intensity: time horizon, capital required, organizational disruption, opportunity cost |
| `Failure_Modes_And_Margin_Destroyers` | What could go wrong; specific mechanisms by which this play could destroy rather than create value |
| `Transferability_Constraints` | Scale, geography, regulatory, capability, or track-record barriers that limit which firms can execute this play |
| `Evidence_Strength` | Confidence classification: `high` (multi-source, independent corroboration), `moderate` (single independent source or corroborated company disclosure), `low` (company-produced only or inferred) |

**Anti-patterns (ANTI-NNN):**

For each stable value driver, include an "Anti-patterns" section enumerating strategic actions that peers executed which did NOT improve performance or actively destroyed value. For every anti-pattern, identify not just that margin compression or value destruction occurred, but the **likely operational mechanism**:
- Duplicated overhead from unintegrated acquisitions
- Fragmented country or entity platforms requiring parallel back-office infrastructure
- Reporting, control, or reconciliation failures post-integration
- Insufficient systems integration leading to manual workarounds and error propagation
- Headcount growth outrunning revenue or AUM growth
- Fee-rate dilution from channel or product mix shift

**Neutral playbook / Target lens separation:**

The core playbook output is neutral — it presents evidence and does not prioritize or recommend specific plays. Strategic prioritization is left to the reader. If `{TARGET_LENS}` is enabled, a separate target-company overlay is generated (see VD-P5) that evaluates which plays are more or less feasible for `{COMPANY}` and why. The overlay is a distinct output file; it does not modify the neutral playbook.

**Output:** `5-playbook/platform_playbook.json`

### Stage VD-P3: Vertical Strategic Menus

**Agent:** Report Composer

Produce a parallel strategic menu at the vertical level, drawing on VD-D2 findings. Same structure as VD-P2 — organized by value driver within each vertical, with evidence citations to specific peer actions.

Every PLAY-NNN and ANTI-NNN entry must include the same mandatory fields defined in VD-P2 (`What_Was_Done`, `Observed_Metric_Impact`, `Prerequisites`, `Operational_And_Tech_Prerequisites`, `Execution_Burden`, `Failure_Modes_And_Margin_Destroyers`, `Transferability_Constraints`, `Evidence_Strength`). Entries that omit any mandatory field will be blocked at CP-3.

Within each vertical, organize plays by strategy sub-type (from VD-D2) where applicable, so that readers can identify plays relevant to their specific sub-type rather than only at the broad vertical level.

**Output:** `5-playbook/asset_class_playbooks.json`

### Stage VD-P4: Final Navigable Report

**Agent:** Report Composer

Produce an HTML report with sidebar navigation and two distinct layers addressable independently by different consumer groups:

**Layer 1 (Platform):**
- Executive summary
- Methodology and statistical appendix
- Industry value driver findings
- Firm-level strategies and actions
- Platform strategic menu

**Layer 2 (Vertical):**
- Per-vertical sections, each self-contained
- Vertical-specific metric drivers
- Vertical strategic menu

**Technical requirements:**
- Sidebar navigation linking to all major sections
- Collapsible sections for supporting evidence and data tables
- Data tables with sortable columns for cross-firm comparisons
- Statistical appendix presenting correlation coefficients, confidence intervals, and corrected p-values
- Mandatory disclaimers section (reproduced verbatim from VD-A4b)

**Output:** `final_report.html`

## Agent Team

| Agent Name | Pipeline Stages | Phase |
|---|---|---|
| Industry Scanner | VD-A0 | Phase 1, Track A |
| Metrics Designer | VD-A1, VD-A3 | Phase 1, Track A |
| Data Collector | VD-A2 | Phase 1, Track A |
| Statistical Analyst | VD-A4, VD-A4b, VD-A5 | Phase 1, Track A |
| Source Cataloger | VD-B0 | Phase 1, Track B |
| Strategy Researcher | VD-B1, VD-B2 | Phase 1, Track B |
| Insight Synthesizer | VD-C1, VD-P1 | Convergence + Phase 3 |
| Platform Profiler | VD-D1 | Phase 2 |
| Sector Specialist | VD-D2 | Phase 2 |
| Report Composer | VD-P2, VD-P3, VD-P4 | Phase 3 |
| Fact Checker | CP-1, CP-2, CP-3 | Verification |

## Execution: 5 Waves

```
Wave 1 (parallel)
├── Industry Scanner    → VD-A0: identify all listed sector firms
├── Source Cataloger    → VD-B0: catalog sources for qualitative peers
└── Metrics Designer    → VD-A1: define metric taxonomy

Wave 2 (parallel, after Wave 1 outputs available)
├── Data Collector      → VD-A2: extract quantitative data (needs A0 + A1)
└── Strategy Researcher → VD-B1 + VD-B2: extract strategies and actions (needs B0)

Wave 3 (sequential, after Wave 2 data collection complete)
├── Metrics Designer    → VD-A3: standardization
├── Statistical Analyst → VD-A4: correlation analysis
├── Statistical Analyst → VD-A4b: statistical documentation
├── Statistical Analyst → VD-A5: value driver ranking
└── Insight Synthesizer → VD-C1: merge quant + qual, finalize peer set

Wave 4 (parallel, after VD-C1 final set confirmed)
├── Platform Profiler   → VD-D1: platform-level deep-dives (9–12 firms)
└── Sector Specialist   → VD-D2: vertical deep-dives

Wave 5 (sequential, after Phase 2 deep-dives complete)
├── Insight Synthesizer → VD-P1: value creation principles
├── Report Composer     → VD-P2: platform strategic menu
├── Report Composer     → VD-P3: vertical strategic menus
└── Report Composer     → VD-P4: final HTML report
```

## Quality Gates

Quality gates occur between each wave. The team lead reviews outputs against explicit criteria before authorizing the next wave.

| Gate | After | Criteria |
|---|---|---|
| Gate 1 | Wave 1 | Universe is comprehensive (>= 20 firms identified); metric taxonomy is internally consistent and includes the Operational Feasibility & Scalable Infrastructure category; source catalog meets minimum coverage (>= 3 sources per qualitative peer) |
| Gate 2 | Wave 2 data collection | Coverage >= 60% of metrics for >= 80% of universe firms; all valuation multiples are populated for all firms; VD-B1/B2 profiles are substantive (>= 2 concrete actions per firm); **operational metrics coverage:** verify disclosure quality for Operational Feasibility metrics — metrics with < 60% coverage are reclassified as `contextual-only`; FX methodology applied correctly (FX_MATERIAL flags populated where applicable) |
| Gate 3 | Wave 3 convergence | Final peer set is 9–12 firms with documented rationale; non-obvious peers flagged by Track A are resolved; all stable drivers pass statistical documentation review in VD-A4b |
| Gate 4 | Wave 4 deep-dives | Platform and vertical deep-dives are internally consistent; transferable insights are grounded in documented evidence, not inference; **operational prerequisite verification:** block any claimed operational prerequisite that lacks source support or is based only on low-trust evidence (job postings or vendor PRs as sole source); all operational prerequisites carry `evidence_class` tags |
| Gate 5 | Wave 5 playbook | **Playbook field completeness:** block any PLAY-NNN or ANTI-NNN entry that lacks `Operational_And_Tech_Prerequisites`, `Failure_Modes_And_Margin_Destroyers`, or `Evidence_Strength`; all anti-pattern entries identify the specific operational mechanism of value destruction |

## Claim Verification

The pipeline incorporates inline claim verification at three checkpoints to prevent over-compliance hallucination — the tendency for LLM agents to produce plausible-sounding but unsupported claims, particularly in Tier 3 outputs (causal narratives, transferable insights, playbook recommendations). The verification framework draws on findings from Gao et al. (2025, arXiv:2512.01797v2) regarding over-compliance neurons in large language models.

### Theoretical Foundation

H-Neurons research demonstrates that hallucination in LLMs stems from over-compliance: the model prioritizes producing plausible answers over acknowledging uncertainty. This manifests in the VDA pipeline as confident-sounding causal narratives, fabricated transferable insights, and confidence-miscalibrated language — particularly in Phase 2 and Phase 3 outputs where agents construct interpretive claims from correlational evidence.

Structural enforcement via hard gates at verification checkpoints is the prompt-level analog of neuron suppression: it forces the producing agent to acknowledge uncertainty rather than fabricate plausible content.

### 4-Dimension Audit Matrix

Each claim is checked against four over-compliance dimensions:

| Dimension | Audit Question | Primary Targets |
|---|---|---|
| Invalid premises | Does this claim rest on an upstream output that was itself weak or flagged? | Causal narratives building on moderate-signal correlations, driver rankings |
| Misleading context | Is the sole source `company-produced` or `c-level-social`? If so, is it corroborated? | Strategy profiles, `stated_rationale` fields, management commentary |
| Sycophantic fabrication | Does this claim exist in upstream evidence, or was it generated to fill a gap? | Transferable insights, anti-patterns, PLAY-* recommendations |
| Confidence miscalibration | Does the language match evidence strength? (Causal language for correlational evidence?) | Value principles, playbook narratives, statistical methodology propagation |

### Checkpoints

Three verification checkpoints are embedded within the pipeline:

| Checkpoint | After Stage | Verifies | Evidence Files | Primary Dimensions |
|---|---|---|---|---|
| CP-1 | VD-A2 merge (Gate 2) | Metric values, source_ids, confidence levels | `source_catalog.json`, tier files | Invalid premises, misleading context |
| CP-2 | VD-D1/D2 (Gate 4) | Causal narratives, transferable insights, value creation stories, operational prerequisite claims | `correlations.json`, `driver_ranking.json`, `strategic_actions.json` | All 4 (critical gate) — additionally: block any claimed operational prerequisite that lacks source support or is based only on job postings / vendor PRs without corroboration |
| CP-3 | VD-P2/P3 (pre-Gate 5) | PLAY-* recommendations, anti-patterns, target company lens, mandatory field completeness | `platform_profiles.json`, `asset_class_analysis.json`, `driver_ranking.json` | Sycophantic fabrication, confidence miscalibration — additionally: block any PLAY-NNN or ANTI-NNN entry that lacks `Operational_And_Tech_Prerequisites`, `Failure_Modes_And_Margin_Destroyers`, or `Evidence_Strength` |

### Verdict Taxonomy

| Verdict | Definition | Action |
|---|---|---|
| `GROUNDED` | Cited evidence supports claim at stated confidence | Pass |
| `INFERRED` | Legitimate inference from evidence, but not directly observed | Pass — must be labeled with hedged language in downstream outputs |
| `WEAK-EVIDENCE` | Evidence exists but is thinner than claim implies | Annotated — flows through with caveat |
| `UNGROUNDED` | No evidence found in upstream files | Hard block — revision required |
| `FABRICATED` | Claim contradicts upstream evidence | Hard block — revision required |

### Enforcement and Retry Logic

1. On `UNGROUNDED` or `FABRICATED` verdict, the pipeline pauses.
2. The auditor produces a revision message specifying: which claims failed, why, what evidence is needed or what language downgrade is required.
3. The revision message is sent back to the producing agent.
4. The producing agent re-runs with revision instructions appended.
5. Maximum retries: 2. After two failed attempts, the claim is forcibly downgraded to `INFERRED` with an explicit caveat in the final report, and the pipeline continues.

### INFERRED Claim Handling

Claims marked `INFERRED` propagate with hedging requirements:
- Downstream agents receive the `INFERRED` label alongside the claim
- Final report must use hedged language: "the data suggests", "management attributes", "appears to correlate with" — never "demonstrates", "drives", "proves"
- The audit JSON file documents the labeling requirement per claim

### Output Files

| File | Checkpoint | Location |
|---|---|---|
| `audit_cp1_data.json` | CP-1 | `{step-folder}/` |
| `audit_cp2_deep_dives.json` | CP-2 | `{step-folder}/` |
| `audit_cp3_playbook.json` | CP-3 | `{step-folder}/` |

## Metric Taxonomy Framework

### Driver Candidate Categories

Adapt these categories to `{SECTOR}`. The categories below reflect an asset management context and should be relabeled or restructured for other sectors:

| Category | Purpose |
|---|---|
| Earnings | Profitability and earnings quality metrics |
| Scale | Absolute size and growth metrics |
| Organic Growth | Growth from existing strategies vs. inorganic expansion |
| Mix and Diversification | Concentration across product lines or asset classes |
| Efficiency | Margin and cost structure metrics |
| Fee or Revenue Quality | Revenue durability and predictability |
| Operational Feasibility & Scalable Infrastructure | Operating model scalability — whether growth can be absorbed without proportional cost escalation. Sector-specific metrics (see VD-A1 sector overlay). Metrics with < 60% coverage are `contextual-only` |

### Stable Driver vs. Multiple-Specific Driver

A metric is a **stable value driver** if ρ > 0.5 against all three valuation multiples. This criterion filters for robustness: the relationship with valuation holds regardless of which pricing convention the market applies. A metric that correlates strongly with only one multiple may reflect an artifact of that multiple's construction rather than a true driver of value.

### Market Structure Metrics (Excluded from Analysis)

Metrics that are consequences of investor behavior — trading volume, passive ownership percentage, free float — are collected as contextual data but excluded from the correlation analysis. Including them would produce correlations with no actionable implications for management.

## Peer Selection: Two-Tier Structure

The pipeline uses a two-tier peer structure:

- **Quantitative universe (~20–30 firms):** the widest defensible set of publicly listed firms in `{SECTOR}`. Breadth maximizes statistical validity.
- **Qualitative deep-dive set (9–12 firms):** a narrowed set allowing depth of research that would be impractical across 25+ firms. Selection is determined at the Convergence stage (VD-C1) by merging Track A quartile rankings with Track B strategic instructiveness assessments.

The two-tier structure ensures that Track A findings refine — rather than predetermine — the qualitative set. Non-obvious peers that emerge from the quantitative analysis are surfaced before Phase 2 begins.

**Inclusion logic at Convergence:**
- Auto-include firms in the top quartile on two or more stable drivers
- Include cautionary cases from the bottom quartile with well-documented strategic actions
- Require minimum source coverage (>= 2 sources) per included firm before Phase 2

## Spearman Correlation Approach

### Why Spearman Over Regression

Multiple regression is analytically inappropriate for a sector universe of ~25 firms (see Analytical Paradigm above). Spearman rank correlation is the appropriate substitute because:

- It is non-parametric: no distributional assumptions required
- It is robust to outliers and non-normality
- It captures monotonic but not necessarily linear relationships
- It produces interpretable coefficients at this sample size

### Bootstrap Confidence Intervals

Each correlation coefficient is accompanied by a 95% confidence interval computed from 1,000 bootstrap iterations. Coefficients whose confidence interval includes zero are flagged regardless of point estimate magnitude.

### Bonferroni Correction

With approximately 45 pairwise tests (15 driver metrics × 3 valuation multiples), the family-wise error rate without correction would be approximately 90% at α = 0.05. Bonferroni correction reduces this to 5%. Both corrected and uncorrected p-values are reported.

### Sensitivity Analyses

Two sensitivity analyses are mandatory:

1. **Leave-one-out:** remove each firm in turn and recompute the correlation. A finding that disappears when one firm is removed is classified as driven by a single influential observation and is downgraded.
2. **Temporal stability:** compute correlations on FY1 and FY2 separately. A finding that appears in only one year is flagged as potentially unstable.

## Source Strategy and Bias Mitigation

### Source Types

| Source Type | Bias Tag |
|---|---|
| Annual reports (20-F, 10-K, equivalent) | `regulatory-filing` |
| Periodic reports (10-Q, 6-K, equivalent) | `regulatory-filing` |
| Investor Day / analyst day materials | `company-produced` |
| Earnings call transcripts | `company-produced` |
| Earnings supplements / fact books | `company-produced` |
| Press releases | `company-produced` |
| CEO interviews and conference panels | `company-produced` |
| Industry reports (Preqin, Bain, McKinsey, etc.) | `industry-report` |
| Sell-side equity research | `third-party-analyst` |
| Journalistic coverage | `journalist` |
| LP / counterparty board materials | `peer-disclosure` |

### Bias Mitigation Requirement

For every firm profile and every strategic claim, the analyst is required to identify whether the claim rests predominantly on company-produced sources, regulatory filings, or independent third-party sources. Claims resting solely on company-produced sources are explicitly qualified. No strategic claim is treated as established fact unless corroborated by at least one source outside the `company-produced` category.

## Data Model

### File Outputs

| File | Stage | Format |
|---|---|---|
| `1-universe/peer_universe.json` | VD-A0 | JSON |
| `1-universe/metric_taxonomy.json` | VD-A1 | JSON |
| `1-universe/source_catalog.json` | VD-B0 | JSON |
| `2-data/quantitative_data.json` | VD-A2 | JSON |
| `2-data/quantitative_tier1.json` | VD-A2 (T1) | JSON |
| `2-data/quantitative_tier2.json` | VD-A2 (T2) | JSON |
| `2-data/quantitative_tier3.json` | VD-A2 (T3) | JSON |
| `2-data/strategy_profiles.json` | VD-B1 | JSON |
| `2-data/strategic_actions.json` | VD-B2 | JSON |
| `2-data/merge_conflicts.md` | VD-A2 | Markdown |
| `3-analysis/standardized_data.json` | VD-A3 | JSON |
| `3-analysis/correlations.json` | VD-A4 | JSON |
| `3-analysis/statistical_methodology.md` | VD-A4b | Markdown |
| `3-analysis/driver_ranking.json` | VD-A5 | JSON |
| `3-analysis/final_peer_set.json` | VD-C1 | JSON |
| `4-deep-dives/platform_profiles.json` | VD-D1 | JSON |
| `4-deep-dives/asset_class_analysis.json` | VD-D2 | JSON |
| `5-playbook/value_principles.md` | VD-P1 | Markdown |
| `5-playbook/platform_playbook.json` | VD-P2 | JSON |
| `5-playbook/asset_class_playbooks.json` | VD-P3 | JSON |
| `5-playbook/final_report.html` | VD-P4 | HTML |
| `6-review/methodology_review.md` | Review | Markdown |
| `6-review/results_review.md` | Review | Markdown |
| `audit_cp1_data.json` | CP-1 | JSON |
| `audit_cp2_deep_dives.json` | CP-2 | JSON |
| `audit_cp3_playbook.json` | CP-3 | JSON |

Default location: `data/processed/{ticker}/{date}/{step-folder}/`

### Identifier Scheme

| Identifier | Entity | Example |
|---|---|---|
| `FIRM-NNN` | Firm in the VD-A0 universe | FIRM-001 |
| `MET-VD-NNN` | Metric in the VD-A1 taxonomy | MET-VD-001 |
| `DP-NNN` | Raw data point in VD-A2 | DP-0042 |
| `COR-NNN` | Correlation result in VD-A4 | COR-007 |
| `DVR-NNN` | Stable value driver in VD-A5 | DVR-001 |
| `PS-VD-NNN` | Source in VD-B0 | PS-VD-015 |
| `ACT-VD-NNN` | Peer action in VD-B2 | ACT-VD-033 |
| `PLAY-NNN` | Strategic play in VD-P2/P3 | PLAY-007 |
| `ANTI-NNN` | Anti-pattern in VD-P2/P3 | ANTI-003 |

## Limitations and Scope Boundaries

The following limitations are acknowledged at design stage and must be disclosed in the final output:

1. **Universe completeness.** Privately held firms are excluded by definition. The analysis is limited to the listed universe, which may not represent the full competitive landscape.

2. **Data standardization limits.** Non-GAAP metrics are not standardized across firms. Despite the standardization procedures in VD-A3, residual measurement error from definitional inconsistency cannot be fully eliminated.

3. **Single time period.** The primary analysis uses the most recent fiscal year. Cross-sectional correlations may not reflect conditions across market cycles. The temporal stability check in VD-A4b is a partial mitigation.

4. **Causal inference.** The quantitative layer identifies statistical associations; it cannot establish causation. The qualitative layer provides the causal narrative, but that narrative is interpretive and cannot be independently verified without controlled experiments.

5. **Geographic, FX, and accounting heterogeneity.** A globally diverse universe may span US GAAP, IFRS, and other accounting standards. Currency conversion (using period-end rates for stock metrics and period-average rates for flow metrics) and accounting reconciliation reduce but do not eliminate comparability constraints. Growth metrics are computed in local currency first to isolate FX effects; metrics flagged as `FX_MATERIAL` require interpretive caution.

6. **Playbook transferability.** Strategic plays documented for large listed firms may face structural barriers to transfer to a firm with different scale, capital structure, client base, or regulatory environment. The playbook presents evidence; it does not assess transferability to any specific firm.

## Statistical Governance Consistency

The methodology document, the statistical documentation (VD-A4b), and the final report must use the **same** statistical rulebook throughout. No downstream output may silently switch methods. Specifically:

| Element | Governing Definition | Must Be Consistent Across |
|---|---|---|
| Multiple-testing correction method | Bonferroni correction (or effective-independent-tests variant) as defined in VD-A4b | VD-A4b, VD-P1, final report statistical appendix |
| Confidence taxonomy | High / Moderate / Suggestive / Not significant with thresholds defined in VD-A4b | VD-A4b, VD-A5, VD-P1, final report |
| Driver classification rules | Stable / Multiple-specific / Moderate signal / Not a driver with thresholds defined in VD-A4 | VD-A4, VD-A5, VD-D1, VD-P2, final report |
| Sensitivity-check definitions | Leave-one-out and temporal stability as defined in VD-A4b | VD-A4b, VD-P1, final report |

**Low-coverage operational metrics:** new metrics from the Operational Feasibility & Scalable Infrastructure category that have < 60% coverage may appear in context tables and deep-dive narratives even when excluded from the formal driver-ranking engine. They must be explicitly labeled as `contextual-only` in every appearance and must not be cited as evidence of driver status.

## Cross-Cutting Principles

- **A) Bias qualification.** Every source is tagged with a bias category. Claims resting solely on company-produced sources are explicitly qualified.
- **B) Methodological rigor.** Each stage declares its inputs, method, outputs, and limitations.
- **C) Academic language.** Formal prose throughout; no marketing speak, no hyperbole.
- **D) Source sufficiency.** Minimum thresholds are enforced before each phase advances: >= 3 sources per qualitative peer before Phase 1 concludes; >= 2 sources per firm before Phase 2 deep-dives begin.
- **E) Peer-centricity.** `{COMPANY}`'s strategy is withheld as a reference point throughout Phase 1 and Phase 2. The playbook is constructed from peer evidence alone.
- **F) Playbook neutrality.** The core playbook presents evidence and options; it does not rank or recommend specific plays. Strategic prioritization is left to the reader. If a `{TARGET_LENS}` overlay is enabled, feasibility assessment and prioritization are produced in a separate output file (VD-P5) that does not modify the neutral playbook.
- **G) Statistical governance.** A single statistical rulebook governs the entire pipeline. The same multiple-testing correction, confidence taxonomy, driver classification rules, and sensitivity-check definitions apply in every stage and in the final report. No downstream output may silently switch methods.

## Key Files

- Prompts: `prompts/vda/` (adapt naming convention to project)
- Raw data: `data/raw/{ticker}/`
- Structured outputs: `data/processed/{ticker}/{date}/{step-folder}/*.json`
- Statistical appendix: `data/processed/{ticker}/{date}/3-analysis/statistical_methodology.md`
- Final report: `data/processed/{ticker}/{date}/5-playbook/final_report.html`

## Reuse

To apply to a different company: replace `{COMPANY}`, `{TICKER}`, and `{SECTOR}` throughout prompts and configurations; identify the relevant publicly listed peer universe for that sector; define industry-appropriate driver metrics and valuation multiples; adapt the ten strategy dimensions in VD-B1 to the sector's strategic vocabulary; adapt asset class / vertical labels in VD-D2 to the firm's product lines. The pipeline structure, statistical methodology, and quality gates apply unchanged.

## Relationship to Other Pipelines

The Valuation Driver Analysis is designed to operate independently of the Strategy Drift Detection and Peer Comparison pipelines. It does not require any output from those pipelines as a prerequisite. It does not reference PIL-* pillar identifiers. The independence is deliberate: anchoring the playbook to `{COMPANY}`'s existing strategic frame would constrain the output to `{COMPANY}`'s prior commitments — precisely the bias the peer-centric design is intended to avoid.

However, the playbook output can serve as a complement to a drift analysis. A user who has run the drift pipeline can optionally compare the playbook's recommended value driver improvements against the company's current PIL-* pillars to identify alignment or divergence. This comparison is left to the user and is not automated within the pipeline.
