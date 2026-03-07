# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Strategy Drift Detector + Peer Comparison + Valuation Driver Analysis — an AI agent system that (1) evaluates whether a public company's actions align with its stated strategic priorities, (2) benchmarks the company's competitive positioning against industry peers, and (3) identifies what drives valuation multiples across a peer universe and produces a strategic playbook. Currently applied to **Block, Inc.** (drift) and **Patria Investments Limited (PAX)** (drift + peer comparison + VDA). The system is prompt-driven; analysis executes through Claude Code agent teams. A **Tauri desktop dashboard** provides a GUI for the VDA pipeline.

## Architecture

This is a **prompt-driven analytical pipeline**, not a traditional software project. Analysis is executed entirely through Claude Code agent teams coordinated via `TeamCreate`/`Agent`/`SendMessage` tools.

### Strategy Drift Pipeline (6 Stages)

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

### Peer Comparison Pipeline (8 Stages)

```
Stage P0/P0b/P0c → Stage P1 → Stage P2 → Stage P3 → Stage P4 → Stage P5
Identify Peers     Gather      Standardize  Compare    Strategic   Report
Define Metrics     Data                     Rankings   Context
Map Sources
```

**Dependency:** Peer pipeline requires `stage_2_pillars.json` from drift pipeline (run drift first).

### Valuation Driver Analysis Pipeline (5 Steps)

```
Map the Industry → Gather Data → Find What Drives Value → Deep-Dive Peers → Build the Playbook
```

- **Map the Industry** — Identify peers, catalog sources, define metrics (3 parallel agents: Industry Scanner, Source Cataloger, Metrics Designer)
- **Gather Data** — Collect quantitative data and extract strategies (Data Collector splits into 3 tiers of ~9 firms; Strategy Researcher runs in parallel)
- **Find What Drives Value** — Standardize, correlate (Spearman), rank drivers (Statistical Analyst, sequential)
- **Deep-Dive Peers** — Platform profiles and asset class analysis (Platform Profiler + Sector Specialist, parallel)
- **Build the Playbook** — Synthesize insights and generate HTML report (Insight Synthesizer + Report Composer, sequential)

**Independence:** VDA pipeline operates independently of the drift pipeline. No PIL-* pillar IDs are referenced.

**Methodology:** `docs/valuation-driver-methodology.md` — Reusable, company-agnostic VDA methodology reference.

### Key Directories

- `prompts/` — Drift pipeline prompt templates (`0X_*.md`), version-controlled
- `prompts/peer/` — Peer comparison pipeline prompt templates (`p0X_*.md`)
- `data/raw/{ticker}/` — Raw source documents per company
- `data/processed/{ticker}/` — Pipeline outputs per company (drift, peer, VDA)
- `docs/plans/` — Execution plans with agent team architecture
- `docs/strategy-drift-methodology.md` — Reusable drift methodology
- `docs/peer-comparison-methodology.md` — Reusable peer comparison methodology
- `docs/valuation-driver-methodology.md` — Reusable VDA methodology
- `src/tauri/` — Tauri desktop dashboard (React + TypeScript + Tailwind + Rust)
- `src/document_converter.py` — PDF/DOCX/PPTX to text converter using marker-pdf

## Commands

```bash
# Install Python dependencies
pip install -r requirements.txt

# Run the Tauri desktop dashboard (development mode)
cd src/tauri && npm run tauri dev

# Build the Tauri app for production
cd src/tauri && npm run tauri build

# Convert supplemental documents (PDF, DOCX, PPTX)
python -c "from src.document_converter import convert_directory; print(convert_directory('/path/to/dir'))"
```

## Skills (Slash Commands)

### `/analyze-drift TICKER [--auto]`

Run the full Strategy Drift Detection pipeline for any public company.

- `TICKER` — stock ticker symbol (e.g., `SQ`, `PAX`, `AAPL`)
- `--auto` — optional flag for fire-and-forget mode (quality gates validated automatically)
- Without `--auto` — interactive mode, pauses at each quality gate for user approval

Output: `data/processed/{TICKER}/{YYYY-MM-DD}/final_report.md` + `final_report.html`

### `/valuation-driver TICKER [--auto] [--sources /path/to/dir]`

Run the full Valuation Driver Analysis pipeline for any public company.

- `TICKER` — stock ticker symbol (e.g., `PAX`, `BX`, `KKR`)
- `--auto` — optional flag for fire-and-forget mode
- `--sources /path/to/dir` — optional path to supplemental data files (PDFs, DOCX, PPTX converted via marker-pdf)

Output: `data/processed/{TICKER}/{YYYY-MM-DD}/peer_vd_final_report.html` + supporting JSON files

### `/review-analysis TICKER [--report path]`

Deploy review agents on any completed VDA analysis to identify improvement opportunities.

- `TICKER` — stock ticker of the analysis to review
- `--report path` — optional override for report location

Output: `data/processed/{TICKER}/peer_vd_review_methodology.md` + `peer_vd_review_results.md`

## VDA Friendly Naming

| Internal Agent | User-Facing Name | Pipeline Step |
|---|---|---|
| universe-scout | Industry Scanner | Map the Industry |
| source-mapper | Source Cataloger | Map the Industry |
| metric-architect | Metrics Designer / Statistical Analyst | Map the Industry / Find What Drives Value |
| data-collector | Data Collector | Gather Data |
| strategy-extractor | Strategy Researcher | Gather Data |
| platform-analyst | Platform Profiler | Deep-Dive Peers |
| vertical-analyst | Sector Specialist | Deep-Dive Peers |
| playbook-synthesizer | Insight Synthesizer | Build the Playbook |
| report-builder | Report Composer | Build the Playbook |

## Conventions

- **Python 3.11+** with type hints
- **Anthropic SDK** via shared wrapper at `src/llm_client.py` — all LLM calls go through `llm_client.ask()`
- Default model: `claude-sonnet-4-20250514`
- API key via `ANTHROPIC_API_KEY` env var (`.env` file, never committed)
- Prompts use `{COMPANY}`, `{TICKER}`, `{SECTOR}` placeholders for reuse across companies
- Every source gets a bias tag: `company-produced`, `regulatory-filing`, `third-party-analyst`, `journalist`, `industry-report`, `c-level-social`, `peer-disclosure`
- Academic language throughout — no marketing speak
- Every claim in drift reports must cite source IDs (S-*, STR-*, ACT-*, CMT-*, PIL-*)
- Every claim in peer reports must cite source IDs (PS-*, PEER-*, MET-*, BENCH-*, RANK-*, PIL-*)
- Every claim in VDA reports must cite source IDs (PS-VD-*, FIRM-*, MET-VD-*, COR-*, DVR-*, ACT-VD-*, PLAY-*)
- Per-company directory convention: `data/processed/{ticker}/`, `data/raw/{ticker}/`
- VDA data collection always splits into 3 parallel tiers (~9 firms each)

## Scoring Framework (Drift)

| Classification | Score Range |
|---|---|
| Aligned | >= 4.0 |
| Minor Drift | 3.0–3.9 |
| Significant Drift | 2.0–2.9 |
| Strategic Disconnect | < 2.0 |

## VDA Correlation Classification

| Classification | Criterion |
|---|---|
| Stable value driver | rho > 0.5 across all three multiples |
| Multiple-specific driver | rho > 0.5 for exactly one multiple |
| Moderate signal | 0.3 <= rho <= 0.5 for at least one multiple |
| Not a driver | rho < 0.3 for all three multiples |

## Reuse for Another Company

Replace "Block, Inc." in prompts, update source-scout search targets, and re-run the pipeline. All prompts are designed with `{COMPANY}`, `{TICKER}`, and `{SECTOR}` placeholders. For peer comparison, also identify industry-specific peers and metrics appropriate to the target company's sector. For VDA, run `/valuation-driver TICKER` — the pipeline auto-detects sector and identifies peers.
