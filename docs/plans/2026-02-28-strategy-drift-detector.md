# Strategy Drift Detector — Agent Team Execution Plan

> **For Claude:** Execute this plan using `TeamCreate` and the `Agent` tool to spawn and coordinate a team of specialized agents.

**Goal:** Evaluate whether Block, Inc.'s actions and execution are coherent with its stated strategic pillars — using only public information, executed entirely through a coordinated agent team in Claude Code.

**Architecture:** Six sequential stages (0–5) executed across 4 waves by 5 specialized agents plus a team lead. Each agent produces structured artifacts in `data/`. Prompts live in `prompts/`. No custom software — the system IS the agent team.

---

## Cross-Cutting Principles

Embedded in every prompt and every agent's instructions:

| ID | Principle | Implementation |
|----|-----------|----------------|
| **A** | **Bias Qualification** | Every source gets a bias tag: `company-produced`, `regulatory-filing`, `third-party-analyst`, `journalist`, `industry-report`, `c-level-social`. Analysis explicitly weighs source bias. |
| **B** | **Methodological Rigor** | Each stage declares: Inputs, Method, Outputs, Limitations. No conclusions without justification. |
| **C** | **Academic Language** | Formal analytical prose. No marketing language, no casual summaries. |
| **D** | **Source Sufficiency** | Before analysis stages: verify sufficient independent, diverse sources. Minimum 2 per pillar, 3 for actions. Flag gaps. |

---

## Extended Source Categories (Wave 2.5)

Before advancing to synthesis (Waves 3-4), the source catalog is expanded with independent sources to reduce company-produced bias concentration:

| Category | Examples | Bias Tag |
|----------|----------|----------|
| **Reliable news & newsletters** | Bloomberg deep-dives, FT, fintech newsletters (Stratechery, Not Boring, The Generalist) | `journalist` |
| **C-level social media** | Jack Dorsey LinkedIn/X posts, Amrita Ahuja (CFO) public statements | `c-level-social` |
| **C-level appearances** | Conference keynotes, podcast interviews, panel discussions | `c-level-social` |
| **Specialized analyst research** | Bernstein, Jefferies, Goldman, JP Morgan — publicly available summaries and rating actions | `third-party-analyst` |
| **Industry reports** | Fintech market analyses, BNPL comparisons, Bitcoin mining industry reports | `industry-report` |
| **Competitive context** | Block vs PayPal/Stripe/Toast positioning articles | `journalist` or `industry-report` |

**Goal:** Reduce company-produced share to <50% of total sources for stronger analytical independence.

---

## Agent Team Architecture

### Team: `drift-detector`

```
                        ┌─────────────────────┐
                        │     TEAM LEAD        │
                        │  (orchestrator)      │
                        │  Creates tasks,      │
                        │  reviews outputs,    │
                        │  quality gates       │
                        └──────────┬──────────┘
                                   │
           ┌───────────┬───────────┼───────────┬───────────┐
           ▼           ▼           ▼           ▼           ▼
    ┌────────────┐┌────────────┐┌────────────┐┌────────────┐┌────────────┐
    │ prompt-    ││ source-    ││ strategy-  ││ execution- ││ drift-     │
    │ engineer   ││ scout      ││ intel      ││ intel      ││ analyst    │
    │            ││            ││            ││            ││            │
    │ Writes all ││ Maps &     ││ Gathers    ││ Gathers    ││ Coherence  │
    │ prompts,   ││ validates  ││ strategy   ││ actions &  ││ analysis + │
    │ then QA    ││ sources    ││ docs, maps ││ commitments││ final      │
    │ review     ││            ││ pillars    ││ maps to    ││ report     │
    │            ││            ││            ││ pillars    ││            │
    └────────────┘└────────────┘└────────────┘└────────────┘└────────────┘
```

### Agent Definitions

| Agent Name | Type | Role | Capabilities Needed |
|------------|------|------|---------------------|
| **`prompt-engineer`** | `general-purpose` | Write all prompt templates; quality-review the final report | File write, read existing plan |
| **`source-scout`** | `general-purpose` | Find and catalog Block, Inc. public sources; validate sufficiency | Web search, file write |
| **`strategy-intel`** | `general-purpose` | Gather strategy docs (Stage 1A); synthesize strategic pillars (Stage 2) | Web search, web fetch, file read/write |
| **`execution-intel`** | `general-purpose` | Gather actions (Stage 1B) and commitments (Stage 1C); map actions to pillars (Stage 3) | Web search, web fetch, file read/write |
| **`drift-analyst`** | `general-purpose` | Run coherence analysis (Stage 4); write final report (Stage 5) | File read/write (analytical, no web needed) |

---

## Execution Strategy: 4 Waves

```
Wave 1 (parallel)     Wave 2 (parallel)        Wave 3 (parallel)     Wave 4 (sequential)
─────────────────     ──────────────────        ─────────────────     ──────────────────

prompt-engineer ──┐   strategy-intel ────┐      strategy-intel ──┐    drift-analyst
  Task: Write     │     Task: Stage 1A   │        Task: Stage 2  │      Task: Stage 4
  all prompts     │     Gather strategy  │        Map pillars    │      Coherence
                  │                      │                       │      analysis
source-scout ─────┤   execution-intel ───┤      execution-intel──┤          │
  Task: Stage 0   │     Task: Stage 1B   │        Task: Stage 3  │          ▼
  Map sources     │     + Stage 1C       │        Map actions    │    drift-analyst
                  │     Gather actions   │                       │      Task: Stage 5
                  │     & commitments    │                       │      Final report
                  │                      │                       │          │
                  ▼                      ▼                       ▼          ▼
            ┌──────────┐          ┌──────────┐            ┌──────────┐┌──────────┐
            │LEAD GATE │          │LEAD GATE │            │LEAD GATE ││QA REVIEW │
            │Sufficiency│         │Data check│            │Pre-anal. ││prompt-eng│
            └──────────┘          └──────────┘            └──────────┘└──────────┘
```

---

## Wave 1 — Foundation (Parallel)

### Task 1.1: Write All Prompt Templates
**Agent:** `prompt-engineer`
**Blocked by:** Nothing — starts immediately

Write the following prompt files, each containing: Objective, Method, Output Format, Bias Awareness section:

| File | Stage | Purpose |
|------|-------|---------|
| `prompts/00_source_mapping.md` | 0 | Source identification and classification |
| `prompts/01_gather_strategy.md` | 1A | Strategy element extraction |
| `prompts/01_gather_actions.md` | 1B | Action/execution evidence extraction |
| `prompts/01_gather_commitments.md` | 1C | Commitment/guidance extraction |
| `prompts/02_map_pillars.md` | 2 | Strategic pillar synthesis and ranking |
| `prompts/03_map_actions.md` | 3 | Action-to-pillar mapping |
| `prompts/04_coherence_analysis.md` | 4 | 5-dimension coherence scoring |
| `prompts/05_final_report.md` | 5 | Comprehensive report generation |

**Output:** 8 markdown files in `prompts/`
**Commit:** `feat: add prompt templates for all 6 analysis stages`

### Task 1.2: Stage 0 — Map & Validate Sources
**Agent:** `source-scout`
**Blocked by:** Nothing — starts immediately

Search the web for Block, Inc. public sources:
- Investor relations (investors.block.xyz)
- SEC EDGAR filings (10-K, 10-Q)
- Earnings call transcripts (last 2-4 quarters)
- Jack Dorsey shareholder letters
- Block newsroom press releases
- Third-party analyst coverage

For each source, catalog:
- Source ID (S-001, S-002, ...)
- Title, Date, Type (`strategy` | `action` | `external-validation`)
- Bias classification (`company-produced` | `regulatory-filing` | `third-party-analyst` | `journalist`)
- URL/reference, Relevance note, Reliability assessment (High/Medium/Low)

Run sufficiency check:
- [ ] >= 2 strategy-defining documents
- [ ] >= 2 quarters of earnings transcripts
- [ ] >= 3 action/commitment sources
- [ ] >= 1 external validation source
- [ ] Sources span >= 12 months
- [ ] No single bias category > 60%

**Output:** `data/processed/stage_0_sources.md`
**Commit:** `feat: stage 0 — source map for Block Inc`

### Wave 1 Gate (Team Lead)
Review both outputs. Verify:
1. Prompts are complete and have proper output schemas
2. Source list passes sufficiency criteria
3. No critical gaps before proceeding

**If gaps exist:** message the relevant agent to fill them before Wave 2 starts.

---

## Wave 2 — Information Gathering (Parallel)

### Task 2.1: Stage 1A — Gather Strategy Information
**Agent:** `strategy-intel`
**Blocked by:** Tasks 1.1 and 1.2

Using the source list from `data/processed/stage_0_sources.md` (filtered to `type: strategy`), fetch and analyze each strategy document.

For each document:
1. Retrieve content via web fetch/search
2. Save raw text to `data/raw/block_strategy_{source_id}.txt`
3. Apply `prompts/01_gather_strategy.md` to extract:
   - Stated Mission/Vision
   - Strategic Pillars (explicitly named priorities)
   - Quantitative Targets
   - Resource Allocation Signals
   - C-Level Framing

Output as structured JSON with bias tags and confidence scores.

**Output:** `data/raw/block_strategy_*.txt` + `data/processed/stage_1a_strategy.json`
**Commit:** `feat: stage 1A — strategy elements for Block Inc`

### Task 2.2: Stage 1B — Gather Actions & Execution Evidence
**Agent:** `execution-intel`
**Blocked by:** Tasks 1.1 and 1.2

Using source list (filtered to `type: action`), fetch and analyze each action/execution document.

For each document:
1. Retrieve content via web fetch/search
2. Save raw text to `data/raw/block_actions_{source_id}.txt`
3. Apply `prompts/01_gather_actions.md` to extract:
   - Capital Allocation (spending, capex, acquisitions)
   - Organizational Decisions (restructurings, leadership)
   - Product/Service Launches
   - Discontinued Initiatives
   - Segment Financial Results

Output as structured JSON with bias tags and confidence scores.

**Output:** `data/raw/block_actions_*.txt` + `data/processed/stage_1b_actions.json`
**Commit:** `feat: stage 1B — action evidence for Block Inc`

### Task 2.3: Stage 1C — Gather Public Commitments
**Agent:** `execution-intel` (sequential, after Task 2.2)
**Blocked by:** Task 2.2

Using source list (filtered to earnings transcripts and press releases), extract forward-looking commitments.

Apply `prompts/01_gather_commitments.md` to extract:
- Guidance Statements
- Verbal Commitments ("We will...", "We are committed to...")
- Timeline Promises
- Comparative Framing

Distinguish between prepared remarks (curated) and Q&A responses (more candid). Weight Q&A higher for candor.

**Output:** `data/raw/block_commitments_*.txt` + `data/processed/stage_1c_commitments.json`
**Commit:** `feat: stage 1C — commitments and guidance for Block Inc`

### Wave 2 Gate (Team Lead)
Review all Stage 1 outputs. Evaluate:
1. Sufficient data points per expected pillar area (minimum 2)
2. Actions cover multiple strategic areas
3. No critical blind spots in evidence
4. Bias distribution across sources is acceptable

Write `data/processed/source_sufficiency_assessment.md` with findings.
**Commit:** `feat: source sufficiency gate — data completeness assessed`

**If gaps are critical:** message the relevant researcher agent to gather more.
**If acceptable:** proceed to Wave 3.

---

## Wave 3 — Analysis (Parallel)

### Task 3.1: Stage 2 — Map Strategic Pillars & Priorities
**Agent:** `strategy-intel`
**Blocked by:** Wave 2 Gate

Using `prompts/02_map_pillars.md`, synthesize `stage_1a_strategy.json` and `stage_1c_commitments.json` into Block's strategic pillar map.

Method:
1. Cluster strategy elements (STR-*) into distinct pillars
2. Rank by priority using: order of mention, C-level airtime, attached targets, resource signals
3. Track temporal evolution (stable/rising/declining/new/deprecated)

Expected pillars to validate against (not prescriptive):
- Bitcoin / decentralized financial infrastructure
- Cash App ecosystem growth
- Square / Seller ecosystem
- Operational efficiency / cost discipline

Include confidence scores, bias notes, methodology notes, and limitations.

**Output:** `data/processed/stage_2_pillars.json`
**Commit:** `feat: stage 2 — strategic pillars mapped for Block Inc`

### Task 3.2: Stage 3 — Map Actions & Commitments to Pillars
**Agent:** `execution-intel`
**Blocked by:** Wave 2 Gate + Task 3.1

Using `prompts/03_map_actions.md`, map every ACT-* and CMT-* to:
- A specific pillar (PIL-*) if clearly aligned
- "Unaligned" if no pillar match
- "Ambiguous" if multiple pillars

Then:
1. Estimate resource allocation percentages per pillar
2. Track commitment fulfillment: `fulfilled` | `in_progress` | `contradicted` | `silently_abandoned`
3. Identify unaligned actions and assess their significance

**Output:** `data/processed/stage_3_actions.json`
**Commit:** `feat: stage 3 — actions mapped to pillars for Block Inc`

### Wave 3 Gate (Team Lead)
Quick review: are pillar definitions clean? Are action mappings justified? Any obvious misclassifications?

---

## Wave 4 — Synthesis (Sequential)

### Task 4.1: Stage 4 — Coherence Analysis
**Agent:** `drift-analyst`
**Blocked by:** Tasks 3.1 and 3.2

Using `prompts/04_coherence_analysis.md`, score each pillar across 5 dimensions:

| Dimension | Weight | Question |
|-----------|--------|----------|
| Resource Alignment | 30% | Does capital allocation match stated priority? |
| Action Consistency | 25% | Do concrete actions advance this pillar? |
| Commitment Fulfillment | 20% | Are promises being kept? |
| Temporal Consistency | 15% | Is emphasis stable over time? |
| Absence of Contradiction | 10% | Are there undermining actions? |

Classify each pillar: `Aligned` (>=4.0) | `Minor Drift` (3.0-3.9) | `Significant Drift` (2.0-2.9) | `Strategic Disconnect` (<2.0)

Identify shadow strategies: resource-heavy areas NOT named as pillars.

**Output:** `data/processed/stage_4_coherence.json`
**Commit:** `feat: stage 4 — coherence analysis with drift scores`

### Task 4.2: Stage 5 — Final Report
**Agent:** `drift-analyst` (sequential, after Task 4.1)
**Blocked by:** Task 4.1

Using `prompts/05_final_report.md` and ALL outputs from Stages 0-4, generate comprehensive report.

Report structure:
1. **Executive Summary** (300 words max) — headline finding, top 3 drift flags, confidence
2. **Methodology** — framework, sources table with bias tags, scoring system, limitations
3. **Strategic Pillar Mapping** — pillars, rankings, temporal evolution
4. **Execution Evidence** — actions by area, commitment fulfillment, unaligned actions
5. **Coherence Analysis** — per-pillar scores, drift indicators, shadow strategies
6. **Key Findings & Drift Flags** — observation, evidence, classification, implication, confidence, bias consideration
7. **Conclusions** — overall assessment, strongest alignment, greatest concern, further analysis recommendations

All in academic prose. Every claim cites source IDs.

**Output:** `data/processed/final_report.md`
**Commit:** `feat: stage 5 — final strategy drift report for Block Inc`

### Task 4.3: Quality Review
**Agent:** `prompt-engineer`
**Blocked by:** Task 4.2

Review `final_report.md` for:
- [ ] Academic language throughout (no marketing speak)
- [ ] Every claim has source citation (S-*, STR-*, ACT-*, CMT-*)
- [ ] Bias acknowledgments present per finding
- [ ] Limitations honestly stated
- [ ] Scoring methodology consistently applied
- [ ] Shadow strategies identified (if any)

Write `data/processed/qa_review.md` with findings. If issues found, message `drift-analyst` to revise.

**Output:** `data/processed/qa_review.md`
**Commit:** `feat: quality review of final report`

---

## Task & Dependency Summary

```
WAVE 1 (parallel)
├── Task 1.1: prompt-engineer → Write prompts
├── Task 1.2: source-scout → Map sources (Stage 0)
└── GATE: Lead reviews sufficiency
         │
WAVE 2 (parallel)
├── Task 2.1: strategy-intel → Gather strategy (Stage 1A)
├── Task 2.2: execution-intel → Gather actions (Stage 1B)
├── Task 2.3: execution-intel → Gather commitments (Stage 1C)
└── GATE: Lead reviews data completeness
         │
WAVE 3 (parallel)
├── Task 3.1: strategy-intel → Map pillars (Stage 2)
├── Task 3.2: execution-intel → Map actions to pillars (Stage 3)
└── GATE: Lead quick review
         │
WAVE 4 (sequential)
├── Task 4.1: drift-analyst → Coherence analysis (Stage 4)
├── Task 4.2: drift-analyst → Final report (Stage 5)
└── Task 4.3: prompt-engineer → Quality review
```

---

## File Outputs per Stage

| Stage | File | Format |
|-------|------|--------|
| 0 | `data/processed/stage_0_sources.md` | Markdown table |
| 1A | `data/processed/stage_1a_strategy.json` | Structured JSON |
| 1B | `data/processed/stage_1b_actions.json` | Structured JSON |
| 1C | `data/processed/stage_1c_commitments.json` | Structured JSON |
| Gate | `data/processed/source_sufficiency_assessment.md` | Markdown |
| 2 | `data/processed/stage_2_pillars.json` | Structured JSON |
| 3 | `data/processed/stage_3_actions.json` | Structured JSON |
| 4 | `data/processed/stage_4_coherence.json` | Structured JSON |
| 5 | `data/processed/final_report.md` | Academic markdown |
| QA | `data/processed/qa_review.md` | Markdown checklist |

---

## How to Execute This Plan

```bash
# In Claude Code, the team lead runs:
# 1. Create the team
TeamCreate → team_name: "drift-detector"

# 2. Create all tasks in the task list
TaskCreate → one per task above, with dependencies set via addBlockedBy

# 3. Spawn Wave 1 agents (parallel)
Agent → name: "prompt-engineer", team_name: "drift-detector"
Agent → name: "source-scout", team_name: "drift-detector"

# 4. After Wave 1 completes + gate passes, spawn Wave 2
Agent → name: "strategy-intel", team_name: "drift-detector"
Agent → name: "execution-intel", team_name: "drift-detector"

# 5. After Wave 2 gate, reassign agents to Wave 3 tasks
SendMessage → strategy-intel: "proceed to Stage 2"
SendMessage → execution-intel: "proceed to Stage 3"

# 6. After Wave 3 gate, spawn Wave 4
Agent → name: "drift-analyst", team_name: "drift-detector"

# 7. After report, reassign prompt-engineer for QA
SendMessage → prompt-engineer: "review final report"
```
