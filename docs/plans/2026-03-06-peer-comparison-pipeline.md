# Peer Comparison Pipeline — Agent Team Execution Plan

> **For Claude:** Execute this plan using `TeamCreate` and the `Agent` tool to spawn and coordinate a team of specialized agents.

**Goal:** Evaluate Patria Investments Limited's (NASDAQ: PAX) competitive positioning against industry peers in alternative asset management — using only public information, executed entirely through a coordinated agent team in Claude Code.

**Prerequisite:** The Strategy Drift pipeline must have been run first. At minimum, `data/processed/pax/stage_2_pillars.json` must exist before Stage P4 can execute.

**Architecture:** Eight sequential stages (P0, P0b, P0c, P1, P2, P3, P4, P5) executed across 4 waves by 6 specialized agents plus a team lead. Each agent produces structured artifacts in `data/processed/pax/`. Prompts live in `prompts/peer/`. No custom software — the system IS the agent team.

---

## Cross-Cutting Principles

Embedded in every prompt and every agent's instructions:

| ID | Principle | Implementation |
|----|-----------|----------------|
| **A** | **Bias Qualification** | Every source gets a bias tag: `company-produced`, `regulatory-filing`, `third-party-analyst`, `journalist`, `industry-report`, `peer-disclosure`. Analysis explicitly weighs source bias. |
| **B** | **Methodological Rigor** | Each stage declares: Inputs, Method, Outputs, Limitations. No conclusions without justification. |
| **C** | **Academic Language** | Formal analytical prose. No marketing language, no casual summaries. |
| **D** | **Source Sufficiency** | Before analysis stages: verify sufficient independent, diverse sources. Minimum 3 sources per peer before analysis. Flag gaps. |

---

## Agent Team Architecture

### Team: `peer-analyzer`

```
                        ┌─────────────────────┐
                        │     TEAM LEAD        │
                        │  (orchestrator)      │
                        │  Creates tasks,      │
                        │  reviews outputs,    │
                        │  quality gates       │
                        └──────────┬──────────┘
                                   │
       ┌──────────┬────────────────┼────────────────┬──────────┬──────────┐
       ▼          ▼                ▼                ▼          ▼          ▼
┌──────────┐┌──────────┐    ┌──────────┐    ┌──────────┐┌──────────┐┌──────────┐
│  peer-   ││ metric-  │    │  source- │    │  data-   ││  bench-  ││  peer-   │
│  mapper  ││ analyst  │    │  scout   │    │ collector││ analyst  ││ reporter │
│          ││          │    │          │    │          ││          ││          │
│ Identify ││ Define   │    │ Catalog  │    │ Collect  ││Comparative│ Final   │
│ peer     ││ industry ││    │ sources  │    │ quant    ││ analysis ││ peer     │
│ group +  ││ metrics, ││    │ for PAX  │    │ data per ││ + strat. ││ report + │
│ selection││ normalize││    │ + peers  │    │ company  ││ context  ││ QA review│
│ criteria ││ data     │    │          │    │ + metric ││          ││          │
└──────────┘└──────────┘    └──────────┘    └──────────┘└──────────┘└──────────┘
```

### Agent Definitions

| Agent Name | Type | Role | Capabilities Needed |
|---|---|---|---|
| **`peer-mapper`** | `general-purpose` | Identify peer group, selection criteria | Web search, file write |
| **`metric-analyst`** | `general-purpose` | Define industry metrics, normalize data | Web search, file read/write |
| **`source-scout`** | `general-purpose` | Catalog sources for PAX + all peers | Web search, file write |
| **`data-collector`** | `general-purpose` | Collect quantitative data per company per metric | Web search, web fetch, file read/write |
| **`bench-analyst`** | `general-purpose` | Comparative analysis + strategic contextualization | File read/write (analytical) |
| **`peer-reporter`** | `general-purpose` | Final peer report + QA review | File read/write |

---

## Execution Strategy: 4 Waves

```
Wave P1 (parallel)         Wave P2 (parallel)     Wave P3 (sequential)     Wave P4 (sequential)
──────────────────         ──────────────────     ────────────────────     ────────────────────

peer-mapper ───────┐       data-collector ───┐    metric-analyst ─────┐    bench-analyst
  Task: Stage P0   │         Task: Stage P1  │      Task: Stage P2    │      Task: Stage P4
  Identify peers   │         Collect data    │      Standardize data  │      Strategic
                   │         for PAX + each  │                        │      context
metric-analyst ────┤         peer            │      bench-analyst ────┤
  Task: Stage P0b  │                         │        Task: Stage P3  │          │
  Define metrics   │                         │        Comparative     │          ▼
                   │                         │        analysis        │    peer-reporter
source-scout ──────┤                         │                        │      Task: Stage P5
  Task: Stage P0c  │                         │                        │      Peer report
  Map sources      │                         │                        │          │
                   ▼                         ▼                        ▼          ▼
             ┌──────────┐             ┌──────────┐             ┌──────────┐┌──────────┐
             │LEAD GATE │             │LEAD GATE │             │LEAD GATE ││QA REVIEW │
             │Peers OK? │             │Data      │             │Analysis  ││peer-     │
             │Metrics?  │             │complete? │             │quality?  ││reporter  │
             │Sources?  │             └──────────┘             └──────────┘└──────────┘
             └──────────┘
```

---

## Wave P1 — Foundation (Parallel)

### Task P1.1: Stage P0 — Peer Identification
**Agent:** `peer-mapper`
**Blocked by:** Nothing — starts immediately

Identify 5–7 peers for PAX in alternative asset management using the following criteria:

- **Primary criteria:** same sector (alternative asset management), publicly listed, comparable AUM scale
- **Secondary criteria:** geographic overlap, similar asset class mix (private equity, private credit, infrastructure, real assets)
- Separate **"scale peers"** (similar AUM) from **"strategy peers"** (similar asset class or geographic mix)

Expected peers to validate against (not prescriptive):
- BAM — Brookfield Asset Management (TSX/NYSE)
- ARES — Ares Management Corporation (NYSE)
- OWL — Blue Owl Capital (NYSE)
- HLNE — Hamilton Lane (NASDAQ)
- STEP — StepStone Group (NASDAQ)
- VINP — Vinci Partners Investments (NASDAQ)

For each peer, record:
- **PEER-NNN** ID (e.g., PEER-001)
- Full legal name, ticker, exchange
- Latest reported AUM (USD)
- Primary asset class strategies
- Peer type: `scale-peer` | `strategy-peer` | `both`
- Selection rationale (2–3 sentences)
- Any notable comparability limitations

**Output:** `data/processed/pax/peer_p0_identification.json`
**Commit:** `feat: stage P0 — peer group identification for PAX`

### Task P1.2: Stage P0b — Metric Definition
**Agent:** `metric-analyst`
**Blocked by:** Nothing — starts immediately

Define 15–20 industry metrics with **MET-NNN** IDs covering the following categories:

| Category | Metrics |
|---|---|
| **Scale** | AUM (total), Fee-Earning AUM (FEAUM), fundraising (LTM capital raised) |
| **Profitability** | Fee-Related Earnings (FRE), FRE margin, Distributable Earnings (DE) |
| **Growth** | AUM growth (YoY %), revenue growth (YoY %) |
| **Fee Quality** | Management fee rate (bps on FEAUM), performance fee share (% of total revenue) |
| **Capital Deployment** | Dry powder ratio (dry powder / total AUM), deployment pace (LTM) |
| **Fundraising** | Capital raised (LTM), fund size progression (latest flagship vs. prior) |
| **Returns** | Net IRR (where disclosed), MOIC (where disclosed) |
| **Valuation** | P/DE multiple, P/FRE multiple, EV/FEAUM |

For each metric, record:
- **MET-NNN** ID
- Full name, abbreviation, unit (USD, %, bps, x)
- Definition and calculation method
- Data source type (filing, supplement, earnings transcript)
- IFRS vs. GAAP note (PAX files 20-F under IFRS; US peers file 10-K under GAAP)
- Expected availability (High/Medium/Low per peer type)

**Output:** `data/processed/pax/peer_p0_metrics.json`
**Commit:** `feat: stage P0b — industry metric definitions for peer comparison`

### Task P1.3: Stage P0c — Source Mapping
**Agent:** `source-scout`
**Blocked by:** Nothing — starts immediately

Catalog sources for PAX and all peers identified in P0. Assign **PS-NNN** IDs.

**Source types per company:**

| Company Type | Expected Sources |
|---|---|
| PAX (foreign private issuer) | 20-F annual report, 6-K quarterly reports, earnings transcripts, investor day presentations, IR website supplements |
| US peers (domestic issuers) | 10-K, 10-Q, earnings transcripts, investor presentations, earnings supplements |
| Industry | Preqin Global Alternatives Report, PitchBook private markets data, Bain & Company Global Private Equity Report, industry association publications |

For each source, record:
- **PS-NNN** ID
- Company (PAX or PEER-NNN)
- Title, date, document type
- Bias tag: `company-produced` | `regulatory-filing` | `third-party-analyst` | `journalist` | `industry-report` | `peer-disclosure`
- URL / EDGAR reference
- Relevance note (which MET-NNN metrics it can populate)
- Reliability assessment (High/Medium/Low)

Run sufficiency check per company:
- [ ] >= 3 sources per peer (minimum threshold)
- [ ] >= 1 regulatory filing per company
- [ ] >= 1 earnings transcript per company (last 2 quarters)
- [ ] >= 2 industry-level sources for benchmarking context
- [ ] No single company has > 80% company-produced sources
- [ ] PAX sources span >= 12 months

**Output:** `data/processed/pax/peer_p0_sources.md`
**Commit:** `feat: stage P0c — source map for PAX peer comparison`

### Wave P1 Gate (Team Lead)
Review all three Wave P1 outputs. Verify:
1. Peer group is coherent — peers are genuinely comparable to PAX; selection rationale is sound
2. Metric set is comprehensive — covers scale, profitability, growth, and valuation dimensions
3. Sources are sufficient per company — minimum thresholds met; flag any peer with < 3 sources

**If gaps exist:** message the relevant agent to fill them before Wave P2 starts.

---

## Wave P2 — Data Collection (Parallel)

### Task P2.1: Stage P1 — Gather Quantitative Data
**Agent:** `data-collector`
**Blocked by:** Tasks P1.1, P1.2, P1.3

For PAX and each PEER-NNN identified in Stage P0:

1. Fetch source documents listed in `peer_p0_sources.md`
2. Save raw text to `data/raw/pax/` using naming convention:
   - PAX sources: `pax_{document_type}_{ps_id}.txt`
   - Peer sources: `peer_{ticker}_{document_type}_{ps_id}.txt`
3. Extract the value for each MET-NNN metric from the relevant source
4. Record each data point as a **BENCH-NNN** entry

Schema for each BENCH-NNN entry:

```json
{
  "id": "BENCH-001",
  "company_id": "PAX",
  "metric_id": "MET-003",
  "value": 42.1,
  "period": "FY2024",
  "currency": "USD",
  "source_id": "PS-005",
  "source_bias": "regulatory-filing",
  "confidence": "High",
  "notes": "Extracted from 20-F p. 47; converted from BRL at Dec 2024 rate"
}
```

For missing data points:
- Mark as `null` with a `missing_reason` field
- Flag metric/peer combinations where data is unavailable
- Do not estimate or interpolate; only record directly sourced values

**Output:** `data/raw/pax/pax_*.txt` + `data/raw/pax/peer_*.txt` + `data/processed/pax/peer_p1_data.json`
**Commit:** `feat: stage P1 — quantitative data collected for PAX and peers`

### Wave P2 Gate (Team Lead)
Review data completeness. Evaluate:
1. Data coverage per company: what % of MET-NNN metrics are populated per company?
2. Flag any peer with < 50% metric coverage — assess whether peer should be excluded or noted as data-limited
3. Confirm period alignment: are most values on the same fiscal year or TTM basis?
4. Confirm currency: are all values recorded in USD or flagged for conversion?

Write `data/processed/pax/peer_data_completeness.md` with findings per company.
**Commit:** `feat: data completeness gate — P1 coverage assessed`

**If critical gaps:** message `data-collector` to gather additional data before Wave P3 starts.

---

## Wave P3 — Analysis (Sequential)

### Task P3.1: Stage P2 — Standardize Data
**Agent:** `metric-analyst`
**Blocked by:** Wave P2 Gate

Using `peer_p1_data.json`, standardize all data for cross-company comparability:

1. **Currency conversion:** convert all values to USD using period-end or average exchange rates (document the rate and source)
2. **Period alignment:** align to TTM or calendar year 2024; note any company with a non-calendar fiscal year
3. **IFRS vs. GAAP reconciliation:** document any known definitional differences between PAX (IFRS) and US peers (GAAP) that affect specific MET-NNN metrics
4. **Completeness flagging:** mark any metric where fewer than 4 of the 7 peers report — note this limits ranking reliability
5. **Outlier identification:** flag statistical outliers (> 2 standard deviations) for manual review

**Output:** `data/processed/pax/peer_p2_standardized.json`
**Commit:** `feat: stage P2 — data standardized for peer comparison`

### Task P3.2: Stage P3 — Comparative Analysis
**Agent:** `bench-analyst`
**Blocked by:** Task P3.1

Using `peer_p2_standardized.json`, conduct systematic comparative analysis:

1. **Rankings:** for each MET-NNN, rank all companies 1–N (1 = best); assign **RANK-NNN** IDs
2. **Descriptive statistics:** compute median, mean, and range of the peer group per metric
3. **PAX positioning:** calculate PAX vs. median (% above/below) and PAX vs. best-in-class per metric
4. **Trend analysis:** where multi-year data exists, compute YoY change for PAX and each peer
5. **Competitive positioning summary:** for each major category (scale, profitability, growth, fee quality), characterize PAX's position as: `above-median` | `at-median` | `below-median` | `insufficient-data`
6. **Strengths and weaknesses:** identify top 3 metrics where PAX outperforms peers; top 3 where PAX underperforms
7. **Differentiation factors:** identify any dimensions where PAX's profile is structurally distinct from peers (e.g., EM focus, fee structure, geographic concentration)

**Output:** `data/processed/pax/peer_p3_comparison.json`
**Commit:** `feat: stage P3 — comparative analysis of PAX vs peers`

### Wave P3 Gate (Team Lead)
Quick review: are rankings internally consistent? Do trends appear plausible given known industry context? Any data errors visible in the comparison? Confirm no metric is over-interpreted where peer coverage is low.

---

## Wave P4 — Synthesis (Sequential)

### Task P4.1: Stage P4 — Strategic Contextualization
**Agent:** `bench-analyst`
**Blocked by:** Task P3.2 + `data/processed/pax/stage_2_pillars.json` (from drift pipeline)

Read the PIL-* pillar definitions from the Strategy Drift pipeline output. For each strategic pillar:

1. Identify the relevant MET-NNN metrics that would be expected to reflect execution of that pillar
2. Assess whether PAX's peer-relative performance on those metrics supports or contradicts stated strategic priorities
3. Where competitive underperformance exists on a pillar-relevant metric, flag as a **competitive gap**
4. Where drift was identified in the drift pipeline, assess whether it correlates with peer-relative weakness — this is evidence of strategic drift having real competitive consequences
5. Identify any pillars where PAX appears competitively differentiated — above-median on relevant metrics — regardless of drift status

Produce a structured assessment per pillar:
- Pillar ID (PIL-NNN) and name
- Relevant metrics (MET-NNN list)
- PAX positioning on each (RANK-NNN)
- Competitive assessment: `differentiated` | `competitive` | `lagging` | `insufficient-data`
- Connection to drift findings (if any)
- Summary narrative (2–4 sentences)

**Output:** `data/processed/pax/peer_p4_contextualization.json`
**Commit:** `feat: stage P4 — strategic contextualization of peer comparison`

### Task P4.2: Stage P5 — Peer Comparison Report
**Agent:** `peer-reporter`
**Blocked by:** Task P4.1

Using ALL outputs from Stages P0–P4, generate a comprehensive peer comparison report of 3,000–5,000 words.

Report structure:

1. **Executive Summary** (300 words) — headline competitive positioning finding, top 3 competitive strengths, top 3 competitive gaps, confidence level
2. **Methodology** — peer selection criteria, metric framework rationale, data sources table with bias tags, standardization approach, limitations
3. **Peer Group Profile** — profiles of each PEER-NNN, comparability assessment, scale vs. strategy peer classification
4. **Industry Metrics Framework** — MET-NNN definitions, rationale for inclusion, coverage and availability notes
5. **Comparative Performance Analysis** — results per metric category (scale, profitability, growth, fee quality, valuation); ranking tables; PAX vs. median analysis; trend observations
6. **Strategic Contextualization** — pillar-by-pillar competitive assessment; where drift correlates with competitive weakness; differentiation factors
7. **Conclusions** — overall competitive positioning verdict, most important findings, limitations and confidence, recommendations for further analysis

Requirements:
- All academic prose; no marketing language
- Every quantitative claim cites a BENCH-NNN or RANK-NNN ID
- Every source cited by PS-NNN ID
- Peers referenced by PEER-NNN ID; pillars by PIL-NNN ID; metrics by MET-NNN ID
- Bias and limitations explicitly acknowledged per section
- Confidence levels stated for comparative claims

**Output:** `data/processed/pax/peer_report.md`
**Commit:** `feat: stage P5 — peer comparison report for PAX`

### Task P4.3: Quality Review
**Agent:** `peer-reporter`
**Blocked by:** Task P4.2

Review `peer_report.md` against the following checklist:

- [ ] Academic language throughout (no marketing speak, no casual phrasing)
- [ ] Every quantitative claim has a citation (BENCH-NNN, RANK-NNN, PS-NNN)
- [ ] All peers referenced by PEER-NNN IDs
- [ ] All metrics referenced by MET-NNN IDs
- [ ] All pillars from drift pipeline referenced by PIL-NNN IDs
- [ ] Bias acknowledgments present per section
- [ ] Limitations of data (IFRS/GAAP differences, period misalignment, missing data) explicitly stated
- [ ] Competitive assessments qualified by data confidence level
- [ ] No unsourced claims about peer companies
- [ ] Conclusions follow logically from the evidence presented

Write `data/processed/pax/peer_qa_review.md` with pass/fail per checklist item and notes. If issues found, message `peer-reporter` to revise the relevant sections.

**Output:** `data/processed/pax/peer_qa_review.md`
**Commit:** `feat: quality review of peer comparison report`

---

## Task & Dependency Summary

```
WAVE P1 (parallel)
├── Task P1.1: peer-mapper → Identify peers (Stage P0)
├── Task P1.2: metric-analyst → Define metrics (Stage P0b)
├── Task P1.3: source-scout → Map sources (Stage P0c)
└── GATE: Lead reviews peer group + metrics + sources
         │
WAVE P2 (parallel)
├── Task P2.1: data-collector → Gather data (Stage P1)
└── GATE: Lead reviews data completeness
         │
WAVE P3 (sequential)
├── Task P3.1: metric-analyst → Standardize data (Stage P2)
├── Task P3.2: bench-analyst → Comparative analysis (Stage P3)
└── GATE: Lead reviews analysis quality
         │
WAVE P4 (sequential)
├── Task P4.1: bench-analyst → Strategic context (Stage P4)
├── Task P4.2: peer-reporter → Peer report (Stage P5)
└── Task P4.3: peer-reporter → Quality review
```

---

## File Outputs per Stage

| Stage | File | Format |
|---|---|---|
| P0 | `data/processed/pax/peer_p0_identification.json` | Structured JSON |
| P0b | `data/processed/pax/peer_p0_metrics.json` | Structured JSON |
| P0c | `data/processed/pax/peer_p0_sources.md` | Markdown table |
| Gate | `data/processed/pax/peer_data_completeness.md` | Markdown |
| P1 | `data/processed/pax/peer_p1_data.json` | Structured JSON |
| P2 | `data/processed/pax/peer_p2_standardized.json` | Structured JSON |
| P3 | `data/processed/pax/peer_p3_comparison.json` | Structured JSON |
| P4 | `data/processed/pax/peer_p4_contextualization.json` | Structured JSON |
| P5 | `data/processed/pax/peer_report.md` | Academic markdown |
| QA | `data/processed/pax/peer_qa_review.md` | Markdown checklist |

---

## How to Execute This Plan

```bash
# 1. Create the team
TeamCreate → team_name: "peer-analyzer"

# 2. Create all tasks in the task list
TaskCreate → one per task above, with dependencies set via addBlockedBy

# 3. Spawn Wave P1 agents (parallel)
Agent → name: "peer-mapper", team_name: "peer-analyzer"
Agent → name: "metric-analyst", team_name: "peer-analyzer"
Agent → name: "source-scout", team_name: "peer-analyzer"

# 4. After Wave P1 gate passes, spawn Wave P2
Agent → name: "data-collector", team_name: "peer-analyzer"

# 5. After Wave P2 gate passes, reassign metric-analyst for Stage P2
SendMessage → metric-analyst: "proceed to Stage P2 standardization"

# 6. After standardization, spawn bench-analyst for Stage P3
Agent → name: "bench-analyst", team_name: "peer-analyzer"

# 7. After Stage P3 gate, direct bench-analyst to Stage P4
SendMessage → bench-analyst: "proceed to Stage P4 strategic contextualization"

# 8. After Stage P4, spawn peer-reporter for Stage P5 + QA
Agent → name: "peer-reporter", team_name: "peer-analyzer"
```
