# Valuation Driver Analysis — Design Document

**Version:** 1.0
**Date:** 2026-03-06
**Subject:** Patria Investments Limited (NASDAQ: PAX)
**Pipeline Identifier:** Valuation Driver Analysis (VD)
**Status:** Design — Not Yet Executed

---

## 1. Purpose and Research Question

This document specifies the full design of the Valuation Driver Analysis (VDA) pipeline for the alternative asset management industry, applied initially to Patria Investments Limited (PAX). The pipeline addresses three interrelated research questions:

1. Which operational and financial metrics exhibit statistically significant correlation with valuation multiples across the universe of publicly listed alternative asset managers?
2. What concrete strategic actions have peer firms executed to move those metrics?
3. What is the resulting menu of empirically grounded strategic plays, organized by value driver, that an alternative asset manager could evaluate for adoption?

The pipeline is designed to produce an analytically rigorous, peer-centric strategic playbook. It is explicitly **not** a performance evaluation of PAX, and it does not attempt to prescribe a course of action. PAX's current strategy enters the analysis only when leadership chooses to compare the playbook against their own trajectory.

---

## 2. Analytical Paradigm

### 2.1 Peer-Centric Framing

The fundamental analytical posture is peer-centric rather than PAX-centric. This distinction has material methodological consequences. A PAX-centric analysis would treat PAX's strategic priorities as the baseline and evaluate peers relative to those priorities — a design that introduces confirmation bias and limits the actionable insight surface. A peer-centric analysis studies what peers are doing on their own terms, synthesizes cross-sectional patterns, and produces a playbook that is independent of any one firm's prior commitments.

PAX's current strategy is explicitly withheld as a reference point during Phases 1 and 2. It becomes relevant, if at all, only in the consumer's own interpretation of the final playbook.

### 2.2 Rationale for a Hybrid Statistical-Qualitative Approach

The quantitative universe of publicly listed alternative asset managers comprises approximately 25 firms globally. This sample size is insufficient for reliable multiple regression analysis for the following reasons:

- **Degrees of freedom constraint.** With N ≈ 25 observations and 15+ candidate predictor variables, a conventional multiple regression would consume all available degrees of freedom and produce unstable estimates.
- **Multicollinearity.** Several candidate metrics are structurally correlated (e.g., fee-earning AUM growth and total AUM growth can be expected to exhibit ρ > 0.8), rendering coefficient estimates unreliable and confidence intervals uninformative.
- **Overfitting risk.** In small samples, a model with many predictors will fit idiosyncratic noise rather than systematic patterns.
- **Endogeneity.** Valuation multiples affect capital-raising capacity, which affects AUM growth — simultaneity that OLS cannot address without instrumental variables unavailable in this context.

The hybrid approach adopted here resolves these constraints by separating the analysis into two methodologically distinct tracks:

- **Quantitative layer (Track A):** Spearman rank correlation analysis applied to each driver metric against three valuation multiples. Spearman is non-parametric, robust to outliers and non-normality, and appropriate for ordinal rankings when N is small. It produces interpretable, defensible correlation coefficients without requiring the distributional assumptions that make regression unreliable at this sample size.
- **Qualitative layer (Track B):** Deep-dive strategy research per firm, mapping the causal chain from strategic actions to metric movements to valuation impact.

The quantitative layer identifies **what matters** — which metrics correlate with higher valuation. The qualitative layer identifies **how to move it** — which strategic actions peers have demonstrated to be effective at shifting those metrics. Neither layer is analytically sufficient alone; their combination produces conclusions that are simultaneously data-anchored and causally interpretable.

### 2.3 Independence from the Strategy Drift Pipeline

This pipeline operates independently of the existing Strategy Drift Detection pipeline. It does not require `stage_2_pillars.json` or any drift pipeline output as a prerequisite. PIL-* pillar identifiers are not referenced within this pipeline. This independence is deliberate: the playbook should be constructed from peer evidence alone, without being shaped by PAX's declared strategic architecture.

---

## 3. Pipeline Architecture

The pipeline is organized into three phases and five stages with two parallel tracks in Phase 1.

```
Phase 1: Screen
┌─────────────────────────────────────────────────────────────────────┐
│  Track A (Quantitative)              Track B (Qualitative)          │
│  VD-A0 Universe Identification       VD-B0 Source Mapping           │
│  VD-A1 Metric Taxonomy               VD-B1 Strategy Extraction      │
│  VD-A2 Data Collection               VD-B2 Action Cataloging        │
│  VD-A3 Standardization                                              │
│  VD-A4 Correlation Analysis                                         │
│  VD-A4b Statistical Documentation                                   │
│  VD-A5 Value Driver Ranking                                         │
└─────────────────────────────────────────────────────────────────────┘
                            │
                       VD-C1: Convergence
                   (Final Peer Set Selection)
                            │
Phase 2: Deep-Dives
┌─────────────────────────────────────────────────────────────────────┐
│  VD-D1 Platform-Level Deep-Dives (per firm, 9–12 peers)             │
│  VD-D2 Asset Class Deep-Dives (per vertical)                        │
└─────────────────────────────────────────────────────────────────────┘
                            │
Phase 3: Playbook
┌─────────────────────────────────────────────────────────────────────┐
│  VD-P1 Value Creation Principles                                    │
│  VD-P2 Platform Strategic Menu                                      │
│  VD-P3 Asset Class Playbooks                                        │
│  VD-P4 Final Navigable Report (HTML)                                │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. Phase 1 — Screen

### 4.1 Track A: Quantitative

#### Stage VD-A0: Peer Universe Identification

Catalog all publicly listed alternative asset managers globally. The target universe is approximately 25 firms. Classification is by business model composition:

| Class | Definition |
|---|---|
| `pure-play-alt` | >= 90% of revenue from alternative asset management |
| `majority-alt` | 60–89% of revenue from alternative asset management |
| `partial-alt` | Meaningful alternative segment but majority of revenue from other activities |

Expected universe (indicative, not prescriptive):

| Region | Tickers |
|---|---|
| United States | BX, KKR, APO, ARES, BAM, OWL, TPG, CG, BN, STEP, HLN, AMK, VCTR |
| Europe | EQT, PGHN (Partners Group), ICP (Intermediate Capital), MAN (Man Group) |
| Latin America | PAX (Patria Investments) |
| Other | Additional firms surfaced during research |

For each firm, record: full legal name, ticker, exchange, classification, latest AUM (USD), primary asset classes, inclusion/exclusion rationale.

**Output:** `peer_vd_a0_universe.json`

#### Stage VD-A1: Metric Taxonomy

Define all metrics organized by category. Metrics are divided into **driver candidates** (independent variables) and **valuation multiples** (dependent variables). Market structure metrics are collected as contextual data only and are explicitly excluded from the correlation analysis.

**Earnings Metrics**

| Metric | Abbreviation | Unit |
|---|---|---|
| Distributable Earnings per share | DE/share | USD |
| Earnings per share (GAAP) | EPS | USD |
| DE/share growth, 3-year CAGR | DE growth | % |

**Scale Metrics**

| Metric | Abbreviation | Unit |
|---|---|---|
| Fee-Earning AUM | FEAUM | USD bn |
| Total AUM | AUM | USD bn |
| FEAUM growth, year-over-year | FEAUM YoY | % |
| FEAUM growth, 3-year CAGR | FEAUM CAGR | % |

**Organic Growth Metrics**

| Metric | Abbreviation | Unit |
|---|---|---|
| Net organic FEAUM growth | Organic growth | % |
| Fundraising as % of AUM | Fundraising ratio | % |

**Mix and Diversification Metrics**

| Metric | Abbreviation | Unit |
|---|---|---|
| Asset class Herfindahl-Hirschman Index | Asset class HHI | 0–10,000 |
| Percentage of permanent capital | Perm capital % | % |
| Percentage of AUM in credit strategies | Credit % | % |

The asset class HHI is calculated as the sum of squared market share proportions across asset classes, multiplied by 10,000. A higher HHI indicates greater concentration. This metric is preferred over a simple count of asset classes because it captures relative weight, not merely presence.

**Efficiency Metrics**

| Metric | Abbreviation | Unit |
|---|---|---|
| Fee-Related Earnings margin | FRE margin | % |
| FRE growth, year-over-year | FRE growth | % |
| Compensation-to-revenue ratio | Comp ratio | % |

**Fee Quality Metrics**

| Metric | Abbreviation | Unit |
|---|---|---|
| Management fee rate (FRE/FEAUM) | Mgmt fee rate | bps |
| Performance fee share of total revenue | Perf fee share | % |

**Valuation Multiples (Dependent Variables)**

| Metric | Abbreviation | Unit |
|---|---|---|
| Price-to-Fee-Related Earnings | P/FRE | x |
| Price-to-Distributable Earnings | P/DE | x |
| Enterprise Value-to-Fee-Earning AUM | EV/FEAUM | % |

Using three valuation multiples rather than one is deliberate. A metric that exhibits correlation with all three multiples is classified as a **stable value driver** — its relationship with valuation is robust across the different ways the market prices these businesses. A metric that correlates strongly with only one multiple is classified as a **multiple-specific driver** — meaningful but less conclusive.

**Market Structure Metrics (Contextual Only — Not in Correlation Analysis)**

| Metric | Rationale for Exclusion |
|---|---|
| Average daily trading volume | Consequence of investor demand, not an actionable driver |
| Passive ownership percentage | Consequence of index inclusion decisions, not actionable by management |
| Free float percentage | Structural / founding shareholder artifact |

**Output:** `peer_vd_a1_metrics.json`

#### Stage VD-A2: Data Collection

Extract quantitative data for all firms in the VD-A0 universe across all VD-A1 driver metrics and valuation multiples. Time coverage: most recent completed fiscal year (FY1), prior fiscal year (FY2), and three-year historical data where available.

Primary sources: earnings releases, annual reports (20-F / 10-K), investor day presentations, earnings supplements, and a filesystem drop zone for proprietary or subscriber data (sell-side research, Preqin exports, internal databases).

For each data point, record: firm ID, metric ID, value, period, currency, source ID, source bias tag, confidence rating, and extraction notes.

Missing data is recorded as `null` with an explicit `missing_reason`. Estimation and interpolation are prohibited; only directly sourced values are recorded.

**Output:** `peer_vd_a2_raw_data.json`

#### Stage VD-A3: Standardization

Normalize VD-A2 data for cross-sectional comparability:

1. **Currency conversion:** convert all values to USD using period-end exchange rates. Document rate, date, and source for each conversion.
2. **Fiscal year alignment:** align to trailing twelve months (TTM) or calendar year basis. Flag firms with non-calendar fiscal years.
3. **FRE definition reconciliation:** FRE definitions vary materially across firms (some exclude depreciation and amortization; some include or exclude certain compensation components). Document each firm's disclosed FRE definition and flag metrics where definitional heterogeneity is material enough to affect cross-firm comparisons.
4. **Coverage flagging:** mark any metric for which fewer than 15 of approximately 25 firms report as "low coverage." Low-coverage metrics may still be analyzed but findings are qualified accordingly.
5. **Outlier flagging:** values exceeding two standard deviations from the cross-sectional mean are flagged for manual review before inclusion in correlation analysis.

**Output:** `peer_vd_a3_standardized.json`

#### Stage VD-A4: Correlation Analysis

Compute Spearman rank correlation coefficients for each driver metric against each of the three valuation multiples, yielding approximately 45 pairwise correlations.

**Classification of results:**

| Class | Criterion |
|---|---|
| Stable value driver | ρ > 0.5 across all three multiples |
| Multiple-specific driver | ρ > 0.5 for exactly one multiple |
| Moderate signal | 0.3 ≤ ρ ≤ 0.5 for at least one multiple |
| Not a driver | ρ < 0.3 for all three multiples |

Following classification, test for multicollinearity among the top-ranked stable drivers. Where two drivers exhibit ρ > 0.7 with each other, document the pair, assess which has stronger theoretical grounding as a causal antecedent of valuation, and flag the risk of attributing independent explanatory power to collinear variables.

**Output:** `peer_vd_a4_correlations.json`

#### Stage VD-A4b: Statistical Documentation and Explainability

This is a critical stage. All statistical choices must be explicitly justified, all limitations must be disclosed, and all confidence intervals must be reported. This stage produces a standalone methodology document that accompanies the final output.

**Methods and justification:**
- Document the choice of Spearman over Pearson rank correlation (robustness to non-normality, monotonic but not necessarily linear relationships, resistance to outlier influence)
- Document explicitly why multiple regression was not employed (insufficient degrees of freedom, high multicollinearity, overfitting risk, endogeneity — see Section 2.2)

**Bootstrap confidence intervals:**
- 1,000 bootstrap iterations per correlation coefficient
- Report 95% confidence intervals for each ρ estimate
- Confidence intervals that include zero are flagged regardless of point estimate magnitude

**Multiple comparisons correction:**
- Apply Bonferroni correction to the family of approximately 45 hypothesis tests
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
- Temporal stability check: compute correlations on FY1 data and FY2 data separately; flag correlations that are present in one year but not the other

**Mandatory disclaimers (reproduced verbatim in the final report):**
- Correlation does not imply causation. A positive correlation between a metric and a valuation multiple may reflect reverse causation (premium-valued firms can afford to invest in the activities that improve the metric), common-cause confounding, or chance.
- Survivorship bias. The universe consists of currently listed firms. Firms that were delisted, acquired, or failed are excluded, potentially skewing the analysis toward characteristics associated with survival rather than value creation per se.
- Point-in-time limitation. The analysis reflects conditions as of the most recent data collection period. Correlations may not be stable across market cycles.
- Small-N limitation. With approximately 25 observations, statistical power is limited. Findings should be treated as generating hypotheses for further investigation, not as definitive causal claims.
- Endogeneity. Several candidate drivers (e.g., AUM growth, FRE margin) may be simultaneously caused by and causally related to valuation multiples. No instrumental variable analysis is conducted.
- FRE definition heterogeneity. Fee-Related Earnings is not a GAAP or IFRS measure. Firm-specific definitions vary. Correlations involving FRE-based metrics are subject to measurement error arising from definitional inconsistency.

**Output:** `peer_vd_a4b_methodology.md`

#### Stage VD-A5: Value Driver Ranking

Rank the top five to six stable drivers by average absolute Spearman coefficient across the three valuation multiples. For each top-ranked driver:

- Provide a per-driver ranking of all firms in the universe (creating a quartile map)
- Identify firms in the top quartile (potential role models for that driver)
- Identify non-obvious peers — firms that did not appear in the expected peer list (VD-B0) but surface in the top quartile on two or more stable drivers
- Flag these non-obvious peers for possible inclusion in the qualitative deep-dive set

**Output:** `peer_vd_a5_driver_ranking.json`

---

### 4.2 Track B: Qualitative

Track B runs in parallel with Track A. The qualitative fieldwork does not wait for quantitative results; it begins at the same time as Track A, which ensures that by the time the Convergence stage (VD-C1) is reached, rich qualitative profiles already exist for the likely deep-dive candidates.

#### Stage VD-B0: Source Mapping

Catalog sources for the initial qualitative peer set, which comprises approximately 12–15 firms identified as the most strategically instructive. The expected list:

**Primary qualitative peers:** BX (Blackstone), KKR, APO (Apollo), ARES, BAM (Brookfield Asset Management), OWL (Blue Owl), TPG, CG (Carlyle), EQT, PGHN (Partners Group), STEP (StepStone), HLN (Hamilton Lane), BN (Brookfield Corporation), ICP (Intermediate Capital), AMK (AssetMark)

**Source types by category:**

| Category | Source Types |
|---|---|
| Primary public filings | 20-F / 10-K, 6-K / 10-Q, proxy statements |
| Management communications | Investor Day presentations, earnings call transcripts, earnings supplements, CEO letters to shareholders |
| Third-party sources | Industry reports (Preqin, Bain & Company Global Private Equity Report, McKinsey Global Private Markets Review), sell-side equity research |
| M&A and strategic announcements | Press releases, merger proxy filings, deal tombstones |
| Non-obvious sources | State pension fund board documents (CalPERS, CalSTRS, CPPIB board materials — these contain independent assessments of manager strategy and positioning), job posting data (reveals organizational priorities and capability build-out), patent and trademark filings (reveals product development directions), conference speaker slot assignments (reveals positioning and brand strategy) |

Assign **PS-VD-NNN** IDs to all sources. For each source, record: firm, title, date, document type, bias tag, URL or filing reference, and relevance notes.

**Bias tags:** `company-produced`, `regulatory-filing`, `third-party-analyst`, `journalist`, `industry-report`, `peer-disclosure`

**Output:** `peer_vd_b0_sources.json`

#### Stage VD-B1: Strategy Extraction

For each firm in the qualitative peer set, extract a standalone strategic profile. Profiles classify firms along ten dimensions derived from the Strategy Outline framework. Profiles are self-contained; they do not reference PAX, do not compare firms against PAX, and do not evaluate firms against any external benchmark.

**Ten classification dimensions:**

| Dimension | Description |
|---|---|
| Geographic reach | Domestic / regional / global; primary markets |
| Asset focus | Core strategies by asset type |
| Asset class mix | Distribution of AUM across private equity, credit, infrastructure, real estate, solutions/multi-asset |
| Origination model | Proprietary deal flow vs. sponsor-to-sponsor vs. platform/operating companies |
| Fund type emphasis | Closed-end flagship vs. open-end / perpetual / evergreen vs. co-mingled SMAs |
| Capital source | Institutional LP base vs. retail / wealth channel vs. insurance / corporate balance sheet |
| Distribution strategy | Direct institutional vs. third-party distribution networks vs. wire house / RIA platforms |
| Client segment | Sovereign wealth / large pensions vs. mid-market institutions vs. UHNW / family office vs. retail/defined contribution |
| Growth model | Organic / same-strategy growth vs. geographic expansion vs. product adjacency vs. M&A / consolidation |
| Stated strategic priorities | Top three to five verbatim or closely paraphrased strategic priorities from most recent Investor Day or annual report |

**Output:** `peer_vd_b1_strategies.json`

#### Stage VD-B2: Action Cataloging

For each firm in the qualitative peer set, catalog concrete strategic actions taken in the prior two to three years. For each action, record:

- Action type: `M&A`, `product-launch`, `geographic-expansion`, `distribution-shift`, `capital-structure-change`, `organizational-change`, `technology-operations`
- Description of the action
- Stated rationale (from management communications)
- Observable metric impact where disclosed (quantitative or directional)
- Timeline (announced, closed, operational)
- Source citation (PS-VD-NNN)

**Output:** `peer_vd_b2_actions.json`

---

### 4.3 Convergence: Stage VD-C1

The convergence stage merges the outputs of Track A and Track B to determine the final peer set for Phase 2 deep-dives. The target size is 9–12 firms.

**Scoring criteria for each candidate peer:**

| Criterion | Description |
|---|---|
| Quantitative relevance | Quartile position on two or more stable value drivers from VD-A5 |
| Qualitative relevance | Strategic instructiveness of the actions documented in VD-B2; diversity of strategic approaches represented |
| User priority | Any peers specifically nominated by the commissioning team |

**Inclusion rules:**

- Auto-include: any firm in the top quartile on two or more stable drivers
- Include as cautionary case: any firm in the bottom quartile that nonetheless has well-documented strategic actions — negative examples are instructive
- Flag for review: any non-obvious peer surfaced by VD-A5 that does not appear in the VD-B0 initial list
- Minimum coverage requirement: at least two sources per included firm before deep-dive begins

**Output:** `peer_vd_c1_final_set.json` — includes each firm's ID, inclusion rationale, exclusion rationale for omitted candidates, and any flagged gaps requiring additional source collection before Phase 2.

---

## 5. Phase 2 — Deep-Dives

### 5.1 Stage VD-D1: Platform-Level Deep-Dives

For each of the 9–12 firms in the final set, produce a structured platform-level profile. Each profile contains six sections:

1. **Identity and scale** — current AUM, FEAUM, geography, asset class mix, public listing history, ownership structure
2. **Strategic agenda** — top three to five stated priorities, sourced from most recent Investor Day or annual report
3. **Key actions (two to three year horizon)** — full catalog from VD-B2, with source citations; organized by action type
4. **Performance on stable value drivers** — scores on the top five to six drivers from VD-A5, with cross-sectional quartile position and brief context
5. **Value creation narrative** — an analytical account of what makes this firm trade at its current premium or discount relative to the peer group; the aim is to articulate the causal theory that connects strategy to valuation
6. **Transferable insights** — three to five specific lessons that a different alternative asset manager could consider, stated independently of PAX

**Output:** `peer_vd_d1_platform_deepdives.json`

### 5.2 Stage VD-D2: Asset Class Deep-Dives

Parallel to platform-level deep-dives, conduct vertical-specific deep-dives for the asset classes relevant to PAX's business. Each vertical deep-dive identifies the best-in-class practitioners within that vertical, analyzes their winning strategies, and documents vertical-specific metric drivers and emerging trends.

**Verticals and reference firms:**

| Vertical | Best-in-Class Reference Firms | Key Questions |
|---|---|---|
| **Credit** | ARES, OWL, HLN | Direct lending vs. CLO vs. mezzanine; origination model (bank-originated vs. proprietary); scale advantages in origination platforms; regulatory capital arbitrage dynamics |
| **Private Equity** | KKR, APO, CG, TPG | Mid-market vs. mega-cap; sector specialization vs. generalist; co-investment programs; GP-led secondaries as a product line |
| **Infrastructure** | BAM, EQT | Core vs. value-added risk profile; energy transition positioning; digital infrastructure (towers, fiber, data centers); regulatory environments across geographies |
| **Real Estate** | BX, BAM | Private equity real estate vs. core/core-plus; credit-oriented real estate; BREIT-style perpetual vehicles; retail investor access |
| **GP-Led Solutions / Secondaries** | STEP, HLN, PGHN | Primary vs. secondaries vs. co-investment; portfolio construction role; fee model differences vs. direct strategies |

For each vertical, the deep-dive produces:
- Profiles of the best-in-class practitioners and the basis for that classification
- Documentation of winning strategies and the evidence for their effectiveness
- Vertical-specific metric drivers (which of the stable drivers from VD-A5 are most salient within this vertical)
- Emerging trends and structural changes affecting the vertical

**Output:** `peer_vd_d2_asset_class_deepdives.json`

---

## 6. Phase 3 — Playbook

### 6.1 Stage VD-P1: Value Creation Principles

Synthesize the five to six stable value drivers from VD-A5 into a set of industry-level principles. For each driver:

- Restate the statistical finding in plain language, accompanied by the full statistical documentation from VD-A4b
- Explain the underlying economic mechanism: why should this metric correlate with valuation in this industry?
- Identify which firms illustrate the principle most clearly (from VD-D1 findings)
- Note the limitations and boundary conditions on the principle

This section functions as the evidentiary foundation for the strategic menus that follow.

**Output:** `peer_vd_p1_value_principles.md`

### 6.2 Stage VD-P2: Platform Strategic Menu

Organize the findings from Phase 2 into a strategic menu at the platform level. The organization is by value driver, not by peer firm. For each stable value driver:

- Enumerate the proven strategic plays that peers have executed to improve performance on that driver
- For each play: which firms executed it, what specifically was done, what metric impact was observed, what prerequisites or enabling conditions were present, what risks or limitations are documented

The structure ensures that a reader who identifies a target value driver can immediately find the full menu of proven approaches. The structure explicitly does not prioritize or recommend specific plays; it presents evidence and leaves strategic choice to the reader.

**Output:** `peer_vd_p2_platform_playbook.json`

### 6.3 Stage VD-P3: Asset Class Playbooks

Produce a parallel strategic menu at the vertical level, drawing on VD-D2 findings. Same structure as VD-P2 — organized by value driver within each vertical, with evidence citations to specific peer actions.

**Output:** `peer_vd_p3_asset_class_playbooks.json`

### 6.4 Stage VD-P4: Final Navigable Report

Produce an HTML report with sidebar navigation and two distinct layers addressable independently by different consumer groups.

**Layer 1 (Platform):**
- Executive summary
- Methodology and statistical appendix
- Industry value driver findings
- Firm-level strategies and actions
- Platform strategic menu

**Layer 2 (Asset Class):**
- Per-vertical sections, each self-contained
- Vertical-specific metric drivers
- Vertical strategic menu

**Technical requirements:**
- Sidebar navigation linking to all major sections
- Collapsible sections for supporting evidence and data tables
- Data tables with sortable columns for cross-firm comparisons
- Statistical appendix presenting correlation coefficients, confidence intervals, and corrected p-values
- Mandatory disclaimers section (reproduced verbatim from VD-A4b)

**Consumer design:**

| Consumer Group | Primary Layer | Entry Point |
|---|---|---|
| C-suite, Investor Relations, Corporate Strategy | Layer 1 | Executive summary → Platform strategic menu |
| Credit BU leadership | Layer 2 | Credit vertical section |
| Private Equity BU leadership | Layer 2 | Private Equity vertical section |
| Infrastructure BU leadership | Layer 2 | Infrastructure vertical section |
| Real Estate BU leadership | Layer 2 | Real Estate vertical section |
| GP-Led Solutions BU leadership | Layer 2 | Solutions/Secondaries vertical section |

**Output:** `final_report.html`

---

## 7. Agent Architecture

### 7.1 Agent Roster

| Agent | Pipeline Stages | Track / Phase |
|---|---|---|
| `universe-scout` | VD-A0 | Track A |
| `metric-architect` | VD-A1, VD-A3, VD-A4, VD-A4b, VD-A5 | Track A |
| `data-collector` | VD-A2 | Track A |
| `source-mapper` | VD-B0 | Track B |
| `strategy-extractor` | VD-B1, VD-B2 | Track B |
| `convergence-analyst` | VD-C1 | Convergence |
| `deep-dive-analyst` | VD-D1, VD-D2 | Phase 2 |
| `playbook-synthesizer` | VD-P1, VD-P2, VD-P3 | Phase 3 |
| `report-builder` | VD-P4 | Phase 3 |

### 7.2 Execution Waves

```
Wave 1 (parallel)
├── universe-scout      → VD-A0: identify all listed alt managers
├── source-mapper       → VD-B0: catalog sources for qual peers
└── metric-architect    → VD-A1: define metric taxonomy

Wave 2 (parallel, after Wave 1 outputs available)
├── data-collector      → VD-A2: extract quantitative data (needs A0 + A1)
└── strategy-extractor  → VD-B1 + VD-B2: extract strategies and actions (needs B0)

Wave 3 (sequential, after Wave 2 data collection complete)
├── metric-architect    → VD-A3: standardization
├── metric-architect    → VD-A4: correlation analysis
├── metric-architect    → VD-A4b: statistical documentation
├── metric-architect    → VD-A5: value driver ranking
└── convergence-analyst → VD-C1: merge quant + qual, finalize peer set

Wave 4 (parallel, after VD-C1 final set confirmed)
├── deep-dive-analyst   → VD-D1: platform-level deep-dives (9–12 firms)
└── deep-dive-analyst   → VD-D2: asset class deep-dives (5 verticals)

Wave 5 (sequential, after Phase 2 deep-dives complete)
├── playbook-synthesizer → VD-P1: value creation principles
├── playbook-synthesizer → VD-P2: platform strategic menu
├── playbook-synthesizer → VD-P3: asset class playbooks
└── report-builder       → VD-P4: final HTML report
```

### 7.3 Quality Gates

Quality gates occur between each wave. The team lead reviews outputs against explicit criteria before authorizing the subsequent wave.

| Gate | After | Criteria |
|---|---|---|
| Gate 1 | Wave 1 | Universe is comprehensive (>= 20 firms identified); metric taxonomy is internally consistent; source catalog meets minimum coverage (>= 3 sources per qualitative peer) |
| Gate 2 | Wave 2 data collection | Coverage >= 60% of metrics for >= 80% of universe firms; all three valuation multiples are populated for all firms; VD-B1/B2 profiles are substantive (>= 2 concrete actions per firm) |
| Gate 3 | Wave 3 VD-C1 | Final peer set is 9–12 firms with documented rationale; non-obvious peers flagged by Track A are resolved; all stable drivers pass the statistical documentation review in VD-A4b |
| Gate 4 | Wave 4 deep-dives | Platform and asset class deep-dives are internally consistent; transferable insights are grounded in documented evidence, not inference |

---

## 8. Data Model

### 8.1 File Outputs

| File | Stage | Format | Location |
|---|---|---|---|
| `peer_vd_a0_universe.json` | VD-A0 | JSON | `data/processed/pax/` |
| `peer_vd_a1_metrics.json` | VD-A1 | JSON | `data/processed/pax/` |
| `peer_vd_a2_raw_data.json` | VD-A2 | JSON | `data/processed/pax/` |
| `peer_vd_a3_standardized.json` | VD-A3 | JSON | `data/processed/pax/` |
| `peer_vd_a4_correlations.json` | VD-A4 | JSON | `data/processed/pax/` |
| `peer_vd_a4b_methodology.md` | VD-A4b | Markdown | `data/processed/pax/` |
| `peer_vd_a5_driver_ranking.json` | VD-A5 | JSON | `data/processed/pax/` |
| `peer_vd_b0_sources.json` | VD-B0 | JSON | `data/processed/pax/` |
| `peer_vd_b1_strategies.json` | VD-B1 | JSON | `data/processed/pax/` |
| `peer_vd_b2_actions.json` | VD-B2 | JSON | `data/processed/pax/` |
| `peer_vd_c1_final_set.json` | VD-C1 | JSON | `data/processed/pax/` |
| `peer_vd_d1_platform_deepdives.json` | VD-D1 | JSON | `data/processed/pax/` |
| `peer_vd_d2_asset_class_deepdives.json` | VD-D2 | JSON | `data/processed/pax/` |
| `peer_vd_p1_value_principles.md` | VD-P1 | Markdown | `data/processed/pax/` |
| `peer_vd_p2_platform_playbook.json` | VD-P2 | JSON | `data/processed/pax/` |
| `peer_vd_p3_asset_class_playbooks.json` | VD-P3 | JSON | `data/processed/pax/` |
| `final_report.html` | VD-P4 | HTML | `data/processed/pax/` |

### 8.2 Identifier Scheme

| Identifier | Entity | Example |
|---|---|---|
| `FIRM-NNN` | Firm in the VD-A0 universe | FIRM-001 (Blackstone) |
| `MET-VD-NNN` | Metric in the VD-A1 taxonomy | MET-VD-001 (FEAUM) |
| `DP-NNN` | Raw data point in VD-A2 | DP-0042 |
| `COR-NNN` | Correlation result in VD-A4 | COR-007 (FEAUM CAGR × P/FRE) |
| `DVR-NNN` | Stable value driver in VD-A5 | DVR-001 (FRE margin) |
| `PS-VD-NNN` | Source in VD-B0 | PS-VD-015 |
| `ACT-VD-NNN` | Peer action in VD-B2 | ACT-VD-033 |
| `PLAY-NNN` | Strategic play in VD-P2/P3 | PLAY-007 |

---

## 9. Source Strategy

### 9.1 Primary Public Sources

All analysis is conducted using publicly available information by default. A filesystem drop zone at `data/raw/pax/` accommodates proprietary or subscriber-gated data (sell-side research reports, Preqin data exports, Bloomberg terminal extracts) when available.

| Source Type | Examples | Bias Tag |
|---|---|---|
| Annual reports | 20-F, 10-K | `regulatory-filing` |
| Periodic reports | 6-K, 10-Q | `regulatory-filing` |
| Investor Day / analyst day materials | Slides, prepared remarks | `company-produced` |
| Earnings call transcripts | Q&A and prepared remarks | `company-produced` |
| Earnings supplements / fact books | Quarterly supplement PDFs | `company-produced` |
| Press releases | M&A, fund closes, management changes | `company-produced` |
| CEO interviews | Financial media, conference panels | `company-produced` |
| Industry reports | Preqin, Bain, McKinsey, BCG | `industry-report` |
| Sell-side equity research | Initiating coverage, thematic reports | `third-party-analyst` |
| Journalistic coverage | FT, WSJ, Bloomberg deep-dives | `journalist` |

### 9.2 Non-Obvious Sources

Several source types provide independent, non-management-filtered perspectives on alternative manager strategy and positioning:

- **Pension fund board documents.** CalPERS, CalSTRS, CPPIB, and similar large LPs publish board meeting materials that include independent assessments of GP strategy, fee terms, and positioning. These carry a `third-party-analyst` or `peer-disclosure` bias tag and provide perspectives not available in GP-controlled communications.
- **Job postings.** Active recruitment data reveals organizational priorities, capability gaps, and strategic initiatives before they are publicly announced. Treated as `company-produced` but with lower evidentiary weight on specific strategic claims.
- **Patent and trademark filings.** Product development directions and branding strategy for new fund vehicles.
- **Conference speaker slot assignments.** Presence at Milken, IPEM, SuperReturn, and similar events signals positioning and brand strategy ambitions.

### 9.3 Bias Mitigation

For every firm profile and every strategic claim, the analyst is required to identify whether the claim rests predominantly on company-produced sources, regulatory filings, or independent third-party sources. Claims resting solely on company-produced sources are explicitly qualified. No strategic claim is treated as established fact unless corroborated by at least one source outside the `company-produced` category.

---

## 10. Key Design Decisions and Rationale

| Decision | Rationale |
|---|---|
| Hybrid approach over pure regression | Small N (≈25) makes multiple regression statistically unreliable due to degrees of freedom constraints, multicollinearity, and overfitting risk. Spearman correlation combined with qualitative deep-dives is more robust and produces more interpretable output for a strategic audience. |
| Three valuation multiples (P/FRE, P/DE, EV/FEAUM) | "Stable drivers" must be robust across multiple ways the market prices these businesses. A correlation that appears in all three multiples is a more reliable signal than one confined to a single metric; each multiple captures a different facet of value (earnings power, distributable cash, AUM quality). |
| Peer-centric framing | Studying peers on their own terms avoids confirmation bias and ensures the playbook is constructed from evidence rather than PAX's prior strategic commitments. |
| Two-tier peer structure (≈25 quant, 9–12 qual) | The wide quantitative universe provides statistical validity (N as large as feasible in this sector). The narrow qualitative set allows depth of research that would be impractical across 25 firms. Track A's findings refine the qualitative set at the convergence stage. |
| Parallel tracks in Phase 1 | Qualitative fieldwork does not wait for quantitative findings. Running both tracks simultaneously reduces elapsed time and ensures qualitative profiles exist for the likely deep-dive candidates before VD-C1 is reached. |
| Market structure metrics excluded from correlation | Trading volume, passive ownership, and free float are consequences of investor behavior, not actions management can take. Including them would identify correlations with no actionable implications. |
| Asset class HHI for diversification | HHI captures relative weight across asset classes, not merely presence. A firm with a dominant credit business and a token infrastructure allocation has a very different diversification profile from a firm with balanced exposure — a count of asset classes would not distinguish them. |
| Percentage of permanent capital as driver candidate | Perpetual and open-end capital reduces the fundraising treadmill, smooths earnings, and reduces valuation discount from AUM rollover risk. Market pricing has increasingly rewarded permanent capital structures, making this a theoretically grounded candidate for a stable driver. |
| Independence from the Strategy Drift pipeline | The valuation driver analysis is designed to produce a standalone, peer-derived playbook. Anchoring it to PIL-* pillars would constrain the output to PAX's existing strategic frame — precisely the bias the peer-centric design is intended to avoid. |

---

## 11. Limitations and Scope Boundaries

The following limitations are acknowledged at the design stage and must be disclosed in the final output:

1. **Universe completeness.** Privately held alternative managers (e.g., Vista Equity Partners, Silver Lake) are excluded by definition. The analysis is limited to the listed universe, which may not be representative of the full competitive landscape.

2. **Data standardization limits.** FRE is a non-GAAP measure with firm-specific definitions. Despite the standardization procedures in VD-A3, residual measurement error in FRE-based metrics cannot be fully eliminated.

3. **Single time period.** The primary analysis uses the most recent fiscal year. Cross-sectional correlations may not reflect conditions across market cycles. The temporal stability check in VD-A4b is a partial mitigation.

4. **Causal inference.** The quantitative layer identifies statistical associations; it cannot establish causation. The qualitative layer provides the causal narrative, but that narrative is interpretive and cannot be independently verified without controlled experiments.

5. **Geographic and accounting heterogeneity.** The universe spans US GAAP filers, IFRS filers, and Swiss GAAP filers (Partners Group). Currency conversion and accounting standard reconciliation reduce but do not eliminate comparability constraints.

6. **Playbook transferability.** Strategic plays documented for large US-listed managers may face structural barriers to transfer to a firm with different scale, capital structure, LP base, or regulatory environment. The playbook presents evidence; it does not assess transferability to any specific firm.

---

*End of document.*
