# Strategy Drift Detector — Reusable Methodology

## Overview
Prompt-driven analytical workflow to evaluate whether a public company's actions align with stated strategic pillars. No custom code — executed entirely through Claude Code agent teams.

## Pipeline (6 Stages)
0. **Source Mapping** — Catalog public sources with bias tags, run sufficiency check
1. **Information Gathering** (3 parallel tracks):
   - 1A: Strategy extraction (pillars, vision, targets, resource signals)
   - 1B: Action/execution evidence (capex, reorgs, launches, discontinuations)
   - 1C: Public commitments (guidance, verbal commitments, timeline promises)
2. **Pillar Mapping** — Cluster strategy elements into ranked pillars with temporal trends
3. **Action Mapping** — Classify actions to pillars, track commitment fulfillment
4. **Coherence Analysis** — 5-dimension weighted scoring (Resource 30%, Action 25%, Commitment 20%, Temporal 15%, Contradiction 10%)
5. **Final Report** — Academic-quality synthesis with evidence citations

## Cross-Cutting Principles
- A) Bias Qualification: every source tagged (company-produced, regulatory-filing, third-party-analyst, journalist)
- B) Methodological Rigor: each stage declares Inputs, Method, Outputs, Limitations
- C) Academic Language: formal prose, no marketing speak
- D) Source Sufficiency: minimum thresholds before analysis (2 per pillar, 3 for actions)

## Agent Team Structure (5 agents + lead)
- `prompt-engineer`: writes prompts, QA reviews final output
- `source-scout`: maps and validates public sources
- `strategy-intel`: gathers strategy docs → maps pillars
- `execution-intel`: gathers actions + commitments → maps to pillars
- `drift-analyst`: coherence scoring → final report

## Execution: 4 Waves
- Wave 1 (parallel): prompt-engineer + source-scout
- Wave 2 (parallel): strategy-intel + execution-intel
- Wave 3 (parallel): pillar mapping + action mapping
- Wave 4 (sequential): coherence analysis → report → QA

## Source Categories (expanded)
- Company-produced: shareholder letters, investor day, press releases, earnings calls
- Regulatory: 10-K, 10-Q, 8-K (SEC EDGAR)
- Third-party analyst: sell-side reports, rating actions
- Journalist: Bloomberg, CNBC, Reuters, WSJ, Fortune
- **Extended sources**: Industry newsletters, C-level LinkedIn posts, specialized analyst research, conference presentations, podcast appearances

## Key Files
- Prompts: `prompts/0X_*.md`
- Raw data: `data/raw/`
- Structured outputs: `data/processed/stage_*.json`
- Plan: `docs/plans/YYYY-MM-DD-strategy-drift-detector.md`

## Scoring Framework
| Classification | Score Range |
|---|---|
| Aligned | >= 4.0 |
| Minor Drift | 3.0–3.9 |
| Significant Drift | 2.0–2.9 |
| Strategic Disconnect | < 2.0 |

## Reuse
To apply to a different company: replace "Block, Inc." in prompts, update source-scout search targets, run the same pipeline. All prompts use {COMPANY} placeholder.
