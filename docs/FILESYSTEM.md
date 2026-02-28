# Strategy Drift Detector — Filesystem Guide

## Project Structure

```
hackathon-1/
├── docs/
│   ├── FILESYSTEM.md                          ← YOU ARE HERE
│   ├── PRESENTATION-INSTRUCTIONS.md           ← Instructions for creating the presentation
│   ├── strategy-drift-methodology.md          ← Reusable methodology (apply to any company)
│   └── plans/
│       └── 2026-02-28-strategy-drift-detector.md  ← Full execution plan with agent team architecture
│
├── prompts/                                   ← Prompt templates (reusable for any company)
│   ├── 00_source_mapping.md                   ← Stage 0: Source identification & classification
│   ├── 01_gather_strategy.md                  ← Stage 1A: Strategy element extraction
│   ├── 01_gather_actions.md                   ← Stage 1B: Action/execution evidence extraction
│   ├── 01_gather_commitments.md               ← Stage 1C: Commitment/guidance extraction
│   ├── 02_map_pillars.md                      ← Stage 2: Strategic pillar synthesis & ranking
│   ├── 03_map_actions.md                      ← Stage 3: Action-to-pillar mapping
│   ├── 04_coherence_analysis.md               ← Stage 4: 5-dimension coherence scoring
│   └── 05_final_report.md                     ← Stage 5: Comprehensive report generation
│
├── data/
│   ├── raw/                                   ← Raw source documents (text extracted from web)
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
│   └── processed/                             ← Structured analysis outputs (the pipeline results)
│       ├── stage_0_sources.md                 ← 50 cataloged sources with bias tags
│       ├── stage_1a_strategy.json             ← 22 strategy elements (STR-001 to STR-022)
│       ├── stage_1b_actions.json              ← 18 actions (ACT-001 to ACT-018)
│       ├── stage_1c_commitments.json          ← 24 commitments (CMT-001 to CMT-024)
│       ├── source_sufficiency_assessment.md   ← Data completeness gate review
│       ├── stage_2_pillars.json               ← 6 strategic pillars (PIL-001 to PIL-006)
│       ├── stage_3_actions.json               ← Actions mapped to pillars + resource allocation
│       ├── stage_4_coherence.json             ← 5-dimension coherence scores per pillar
│       ├── final_report.md                    ← ★ THE FINAL REPORT (~3,800 words)
│       └── qa_review.md                       ← Quality review (PASS)
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
| **★★★** | `data/processed/final_report.md` | The complete analysis — use this as the primary source |
| **★★** | `data/processed/stage_4_coherence.json` | Raw coherence scores and shadow strategies (for charts) |
| **★★** | `data/processed/stage_2_pillars.json` | Pillar definitions and rankings (for the strategy map) |
| **★** | `data/processed/stage_0_sources.md` | Source catalog (for methodology credibility slide) |
| **★** | `docs/strategy-drift-methodology.md` | Methodology overview (for the "how we built it" slide) |

## Pipeline Flow

```
Stage 0 → Stage 1A/1B/1C → Stage 2 → Stage 3 → Stage 4 → Stage 5
Sources    Gather Info       Pillars   Map Actions  Score     Report
(50 sources) (22+18+24 elements) (6 pillars) (mapped)  (scored)  (3,800 words)
```
