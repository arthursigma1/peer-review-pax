# Strategy Drift Detector + Peer Comparison — Filesystem Guide

## Project Structure

```
peer-review-pax/
├── docs/
│   ├── FILESYSTEM.md                          ← YOU ARE HERE
│   ├── PRESENTATION-INSTRUCTIONS.md           ← Instructions for creating the presentation
│   ├── strategy-drift-methodology.md          ← Reusable drift methodology (any company)
│   ├── peer-comparison-methodology.md         ← Reusable peer comparison methodology (any company)
│   └── plans/
│       ├── 2026-02-28-strategy-drift-detector.md  ← Drift pipeline execution plan (Block, Inc.)
│       └── 2026-03-06-peer-comparison-pipeline.md ← Peer pipeline execution plan (PAX)
│
├── prompts/                                   ← Drift pipeline prompt templates (reusable)
│   ├── 00_source_mapping.md                   ← Stage 0: Source identification & classification
│   ├── 01_gather_strategy.md                  ← Stage 1A: Strategy element extraction
│   ├── 01_gather_actions.md                   ← Stage 1B: Action/execution evidence extraction
│   ├── 01_gather_commitments.md               ← Stage 1C: Commitment/guidance extraction
│   ├── 02_map_pillars.md                      ← Stage 2: Strategic pillar synthesis & ranking
│   ├── 03_map_actions.md                      ← Stage 3: Action-to-pillar mapping
│   ├── 04_coherence_analysis.md               ← Stage 4: 5-dimension coherence scoring
│   └── 05_final_report.md                     ← Stage 5: Comprehensive report generation
│
├── prompts/peer/                              ← Peer comparison pipeline prompt templates (reusable)
│   ├── p00_peer_identification.md             ← Stage P0: Peer group selection
│   ├── p01_define_metrics.md                  ← Stage P0b: Industry metric definitions
│   ├── p02_source_mapping.md                  ← Stage P0c: Multi-company source mapping
│   ├── p03_gather_data.md                     ← Stage P1: Quantitative data extraction
│   ├── p04_standardize.md                     ← Stage P2: Currency/FY/GAAP normalization
│   ├── p05_comparative_analysis.md            ← Stage P3: Rankings, percentiles, trends
│   ├── p06_strategic_context.md               ← Stage P4: Integration with drift pillars
│   └── p07_peer_report.md                     ← Stage P5: Peer comparison report
│
├── data/
│   ├── raw/                                   ← Raw source documents — Block, Inc.
│   │   ├── block_strategy_S-001.txt           ← Q4 2025 Shareholder Letter
│   │   ├── block_strategy_S-002.txt           ← Investor Day 2025
│   │   ├── block_strategy_S-004.txt           ← Q3 2025 Shareholder Letter
│   │   ├── block_strategy_S-005.txt           ← Q1 2025 Shareholder Letter
│   │   ├── block_strategy_S-006.txt           ← 10-K FY 2025
│   │   ├── block_strategy_S-007.txt           ← 10-K FY 2024
│   │   ├── block_strategy_S-015.txt           ← Q3 2025 Investor Presentation
│   │   ├── block_strategy_S-016.txt           ← Q2 2025 Investor Presentation
│   │   ├── block_actions_*.txt                ← Earnings transcripts, press releases, filings
│   │   └── block_commitments_*.txt            ← Forward-looking statements, guidance
│   │
│   ├── raw/pax/                               ← Raw source documents — PAX + peers
│   │   ├── pax_strategy_S-*.txt               ← PAX strategy sources (20-F, 6-K, IR)
│   │   ├── pax_actions_S-*.txt                ← PAX action/execution sources
│   │   ├── pax_commitments_S-*.txt            ← PAX commitment sources
│   │   ├── pax_peer_PS-*.txt                  ← PAX peer analysis sources
│   │   └── peer_{ticker}_PS-*.txt             ← Peer company sources
│   │
│   ├── processed/                             ← Block, Inc. pipeline outputs
│   │   ├── stage_0_sources.md                 ← 50 cataloged sources with bias tags
│   │   ├── stage_1a_strategy.json             ← 22 strategy elements (STR-001 to STR-022)
│   │   ├── stage_1b_actions.json              ← 18 actions (ACT-001 to ACT-018)
│   │   ├── stage_1c_commitments.json          ← 24 commitments (CMT-001 to CMT-024)
│   │   ├── source_sufficiency_assessment.md   ← Data completeness gate review
│   │   ├── stage_2_pillars.json               ← 6 strategic pillars (PIL-001 to PIL-006)
│   │   ├── stage_3_actions.json               ← Actions mapped to pillars + resource allocation
│   │   ├── stage_4_coherence.json             ← 5-dimension coherence scores per pillar
│   │   ├── final_report.md                    ← ★ THE FINAL REPORT (~3,800 words)
│   │   └── qa_review.md                       ← Quality review (PASS)
│   │
│   └── processed/pax/                         ← PAX pipeline outputs (drift + peer)
│       ├── stage_0_sources.md                 ← PAX drift: source catalog
│       ├── stage_1a_strategy.json             ← PAX drift: strategy elements (STR-*)
│       ├── stage_1b_actions.json              ← PAX drift: actions (ACT-*)
│       ├── stage_1c_commitments.json          ← PAX drift: commitments (CMT-*)
│       ├── source_sufficiency_assessment.md   ← PAX drift: sufficiency gate
│       ├── stage_2_pillars.json               ← PAX drift: strategic pillars (PIL-*)
│       ├── stage_3_actions.json               ← PAX drift: action-to-pillar mapping
│       ├── stage_4_coherence.json             ← PAX drift: coherence scores
│       ├── final_report.md                    ← PAX drift: final report
│       ├── peer_p0_identification.json        ← PAX peer: peer group (PEER-*)
│       ├── peer_p0_metrics.json               ← PAX peer: metric definitions (MET-*)
│       ├── peer_p0_sources.md                 ← PAX peer: source catalog (PS-*)
│       ├── peer_p1_data.json                  ← PAX peer: raw data (BENCH-*)
│       ├── peer_p2_standardized.json          ← PAX peer: normalized data
│       ├── peer_p3_comparison.json            ← PAX peer: rankings (RANK-*)
│       ├── peer_p4_contextualization.json     ← PAX peer: drift-competition integration
│       ├── peer_report.md                     ← ★ PAX PEER COMPARISON REPORT
│       └── peer_qa_review.md                  ← PAX peer: quality review
│
├── src/                                       ← (Scaffolded, not used — no code in this project)
├── tests/                                     ← (Scaffolded, not used)
├── PLAN.md                                    ← Original hackathon plan (superseded by docs/plans/)
├── README.md                                  ← Project README
├── requirements.txt                           ← Python dependencies (for future code extensions)
├── .env.example                               ← API key template
└── .gitignore                                 ← Git ignore rules
```

## Key Files for Presentation

| Priority | File | What It Contains |
|----------|------|------------------|
| **★★★** | `data/processed/final_report.md` | Block, Inc. drift analysis — primary source |
| **★★★** | `data/processed/pax/peer_report.md` | PAX peer comparison report |
| **★★★** | `data/processed/pax/final_report.md` | PAX drift analysis report |
| **★★** | `data/processed/stage_4_coherence.json` | Block coherence scores (for charts) |
| **★★** | `data/processed/pax/peer_p3_comparison.json` | PAX peer rankings and positioning |
| **★★** | `data/processed/pax/peer_p4_contextualization.json` | PAX drift-competition integration |
| **★★** | `data/processed/stage_2_pillars.json` | Block pillar definitions and rankings |
| **★** | `data/processed/stage_0_sources.md` | Block source catalog |
| **★** | `docs/strategy-drift-methodology.md` | Drift methodology overview |
| **★** | `docs/peer-comparison-methodology.md` | Peer comparison methodology overview |

## Pipeline Flows

### Drift Pipeline (per company)
```
Stage 0 → Stage 1A/1B/1C → Stage 2 → Stage 3 → Stage 4 → Stage 5
Sources    Gather Info       Pillars   Map Actions  Score     Report
```

### Peer Comparison Pipeline (depends on drift)
```
Stage P0/P0b/P0c → Stage P1 → Stage P2 → Stage P3 → Stage P4 → Stage P5
Identify Peers     Gather      Standardize  Compare    Strategic   Report
Define Metrics     Data                     Rankings   Context
Map Sources
```

**Dependency:** Peer P4 reads PIL-* from drift Stage 2. Run drift first.
