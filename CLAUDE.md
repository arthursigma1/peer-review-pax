# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Strategy Drift Detector + Peer Comparison — an AI agent system that (1) evaluates whether a public company's actions align with its stated strategic priorities and (2) benchmarks the company's competitive positioning against industry peers. Currently applied to **Block, Inc.** (drift) and **Patria Investments Limited (PAX)** (drift + peer comparison). The system is prompt-driven with no custom application code; the `src/` and `tests/` directories are scaffolded but empty (only `__init__.py` files and `llm_client.py`).

## Architecture

This is a **prompt-driven analytical pipeline**, not a traditional software project. Analysis is executed entirely through Claude Code agent teams coordinated via `TeamCreate`/`Agent`/`SendMessage` tools.

### Pipeline (6 Stages)

```
Stage 0 → Stage 1A/1B/1C → Stage 2 → Stage 3 → Stage 4 → Stage 5
Sources    Gather Info       Pillars   Map Actions  Score     Report
```

- **Stage 0** — Source mapping: catalog public sources with bias tags
- **Stage 1A/1B/1C** — Parallel information gathering: strategy elements, actions, commitments
- **Stage 2** — Pillar synthesis: cluster strategy elements into ranked pillars
- **Stage 3** — Action mapping: classify actions to pillars, track commitment fulfillment
- **Stage 4** — Coherence analysis: 5-dimension weighted scoring (Resource 30%, Action 25%, Commitment 20%, Temporal 15%, Contradiction 10%)
- **Stage 5** — Final report generation

### Agent Team (5 agents + lead)

Executed in 4 waves with quality gates between each:
- `prompt-engineer` — writes prompts, QA reviews final output
- `source-scout` — maps and validates public sources
- `strategy-intel` — gathers strategy docs, maps pillars
- `execution-intel` — gathers actions & commitments, maps to pillars
- `drift-analyst` — coherence scoring, final report

### Peer Comparison Pipeline (8 Stages)

```
Stage P0/P0b/P0c → Stage P1 → Stage P2 → Stage P3 → Stage P4 → Stage P5
Identify Peers     Gather      Standardize  Compare    Strategic   Report
Define Metrics     Data                     Rankings   Context
Map Sources
```

- **Stage P0** — Peer identification: select 5-7 peers by sector, scale, strategy
- **Stage P0b** — Metric definition: 15-20 industry-specific metrics across 8 categories
- **Stage P0c** — Source mapping: catalog sources for target + all peers
- **Stage P1** — Data gathering: extract quantitative data per company per metric
- **Stage P2** — Standardization: normalize currency, fiscal year, accounting standards
- **Stage P3** — Comparative analysis: rankings, percentiles, trends, positioning
- **Stage P4** — Strategic contextualization: integrate with drift pipeline PIL-* pillars
- **Stage P5** — Peer report generation

**Dependency:** Peer pipeline requires `stage_2_pillars.json` from drift pipeline (run drift first).

### Key Directories

- `prompts/` — Drift pipeline prompt templates (`0X_*.md`), version-controlled. Never hardcode prompts in Python.
- `prompts/peer/` — Peer comparison pipeline prompt templates (`p0X_*.md`)
- `data/raw/` — Raw source documents for Block, Inc. (`block_{type}_{source_id}.txt`)
- `data/raw/pax/` — Raw source documents for PAX (`pax_*.txt`, `peer_{ticker}_*.txt`)
- `data/processed/` — Block, Inc. pipeline outputs: `stage_*.json`, `final_report.md`, `qa_review.md`
- `data/processed/pax/` — PAX pipeline outputs: drift (`stage_*.json`) + peer (`peer_*.json`, `peer_report.md`)
- `docs/plans/` — Execution plans with agent team architecture
- `docs/strategy-drift-methodology.md` — Reusable drift methodology (apply to any company)
- `docs/peer-comparison-methodology.md` — Reusable peer comparison methodology

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the analysis pipeline (scaffolded, not yet implemented)
python -m src.api.pipeline

# Start the API (scaffolded)
uvicorn src.api.main:app --reload

# Launch the UI (scaffolded)
streamlit run src/ui/app.py
```

## Skills (Slash Commands)

### `/analyze-drift TICKER [--auto]`

Run the full Strategy Drift Detection pipeline for any public company.

- `TICKER` — stock ticker symbol (e.g., `SQ`, `PAX`, `AAPL`)
- `--auto` — optional flag for fire-and-forget mode (quality gates validated automatically)
- Without `--auto` — interactive mode, pauses at each quality gate for user approval

Output: `data/processed/{TICKER}/{YYYY-MM-DD}/final_report.md` + `final_report.html`

## Conventions

- **Python 3.11+** with type hints
- **Anthropic SDK** via shared wrapper at `src/llm_client.py` — all LLM calls go through `llm_client.ask()`
- Default model: `claude-sonnet-4-20250514`
- API key via `ANTHROPIC_API_KEY` env var (`.env` file, never committed)
- Prompts use `{COMPANY}` placeholder for reuse across companies
- Every source gets a bias tag: `company-produced`, `regulatory-filing`, `third-party-analyst`, `journalist`, `industry-report`, `c-level-social`, `peer-disclosure`
- Academic language throughout — no marketing speak
- Every claim in drift reports must cite source IDs (S-*, STR-*, ACT-*, CMT-*, PIL-*)
- Every claim in peer reports must cite source IDs (PS-*, PEER-*, MET-*, BENCH-*, RANK-*, PIL-*)
- Per-company directory convention: `data/processed/{ticker}/`, `data/raw/{ticker}/`

## Scoring Framework

| Classification | Score Range |
|---|---|
| Aligned | >= 4.0 |
| Minor Drift | 3.0–3.9 |
| Significant Drift | 2.0–2.9 |
| Strategic Disconnect | < 2.0 |

## Reuse for Another Company

Replace "Block, Inc." in prompts, update source-scout search targets, and re-run the pipeline. All prompts are designed with `{COMPANY}` and `{TICKER}` placeholders. For peer comparison, also identify industry-specific peers and metrics appropriate to the target company's sector.
