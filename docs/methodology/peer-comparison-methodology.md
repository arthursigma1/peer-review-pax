# Peer Comparison Analysis — Reusable Methodology

## Overview
Prompt-driven analytical workflow to evaluate a public company's competitive positioning against industry peers. Contextualizes strategy drift findings with external benchmarks. No custom code — executed entirely through Claude Code agent teams. Designed as the "second derivative" of the Strategy Drift Detector.

## Pipeline (6 Stages)
- P0: **Peer Identification** — select peers by sector, scale (AUM), geography, strategy, listing status. Separate "scale peers" from "strategy peers"
- P0b: **Metric Definition** — define 15-20 industry-specific metrics across categories: Scale, Profitability, Growth, Fee Quality, Capital Deployment, Fundraising, Returns, Valuation
- P0c: **Source Mapping** — catalog sources for target company + all peers with bias tags, sufficiency check per company
- P1: **Data Gathering** — extract quantitative/qualitative data for each company on each metric
- P2: **Standardization** — normalize currencies (to USD), align fiscal years (TTM/calendar), reconcile IFRS vs GAAP, flag insufficient data
- P3: **Comparative Analysis** — rankings, percentiles, medians, PAX vs median %, trend analysis (YoY), competitive positioning
- P4: **Strategic Contextualization** — integrate with drift pipeline PIL-* pillars, map metrics to pillars, assess where drift translates to competitive weakness
- P5: **Peer Report** — 3,000–5,000 word academic report with 7 sections

## Cross-Cutting Principles
Same 4 as drift pipeline:
- A) Bias Qualification: every source tagged (company-produced, regulatory-filing, third-party-analyst, journalist, industry-report, peer-disclosure)
- B) Methodological Rigor: each stage declares Inputs, Method, Outputs, Limitations
- C) Academic Language: formal prose, no marketing speak
- D) Source Sufficiency: minimum thresholds per peer before analysis

## Agent Team Structure (6 agents + lead)
- `peer-mapper`: identifies peers, criteria selection
- `metric-analyst`: defines metrics, normalizes data
- `source-scout`: catalogs sources for all companies
- `data-collector`: collects quantitative data
- `bench-analyst`: comparative analysis + strategic contextualization
- `peer-reporter`: final report + QA

## Execution: 4 Waves
- Wave P1 (parallel): peer-mapper (P0) + metric-analyst (P0b) + source-scout (P0c)
- Wave P2 (parallel): data-collector (P1) for each company
- Wave P3 (sequential): metric-analyst (P2) standardization → bench-analyst (P3) comparative analysis
- Wave P4 (sequential): bench-analyst (P4) strategic context → peer-reporter (P5) report + QA

## Peer Selection Framework
- Primary criteria: same sector/sub-sector, publicly listed, comparable scale
- Secondary criteria: geographic overlap, strategy similarity, asset class mix
- Exclusion: no public data, too small/large (10x AUM difference), different industry entirely

## Industry Metrics Framework
Categories with examples:
- Scale: AUM, FEAUM, fundraising
- Profitability: FRE, FRE margin, Distributable Earnings
- Growth: AUM growth, revenue growth
- Fee Quality: management fee rate, performance fee share
- Capital Deployment: dry powder ratio, deployment pace
- Fundraising: capital raised, fund size progression
- Returns: IRR, MOIC (where available)
- Valuation: P/DE, P/FRE, EV/FEAUM

## Data Normalization
- Currency: convert to USD at period-end rates
- Fiscal year: align to calendar year or TTM where needed
- Accounting: flag IFRS vs GAAP differences, note material impacts
- Minimum data: flag metrics with < 4 of 7 peers reporting

## Integration with Drift Analysis
Stage P4 reads PIL-* from the drift pipeline. For each pillar:
1. Identify relevant peer metrics
2. Assess whether company's execution on that pillar results in above/below-peer performance
3. Identify where internal drift correlates with competitive weakness (or strength)

## ID Conventions
- PEER-NNN: peer company identifiers
- MET-NNN: metric definitions
- BENCH-NNN: individual data points (company + metric + period)
- PS-NNN: peer source identifiers
- RANK-NNN: ranking entries

## Competitive Positioning Score
| Classification | Interpretation |
|---|---|
| Leader (top quartile) | Outperforming peers on this dimension |
| Above Average (2nd quartile) | Performing well, room for improvement |
| Below Average (3rd quartile) | Underperforming, warrants attention |
| Laggard (bottom quartile) | Significant competitive gap |

## Key Files
- Prompts: `prompts/peer/p0X_*.md`
- Raw data: `data/raw/{ticker}/`
- Structured outputs: `data/processed/{ticker}/peer_*.json`
- Plan: `docs/plans/YYYY-MM-DD-peer-comparison-pipeline.md`

## Reuse
To apply to a different company: replace {COMPANY} and {TICKER} in prompts, identify industry-specific peers and metrics, run the same pipeline. All prompts use placeholders.

## Dependency on Drift Pipeline
The peer comparison pipeline requires `stage_2_pillars.json` from the drift pipeline (at minimum). Run drift first, peer second. The peer report contextualizes drift findings with competitive benchmarks.
