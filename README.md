# Strategy Intelligence System

AI-powered analytical pipelines that evaluate corporate strategy alignment, benchmark competitive positioning, and identify what drives valuation multiples across a peer universe — producing governance-ready strategic playbooks with built-in anti-hallucination safeguards.

Currently applied to **Block, Inc.** (strategy drift) and **Patria Investments Limited** (drift + peer comparison + valuation driver analysis).

---

## What It Does

The system runs three complementary analytical pipelines, each orchestrated by specialized AI agent teams:

### 1. Strategy Drift Detection

Evaluates whether a company's **actions** align with its **stated strategic priorities**.

Sources are cataloged and bias-tagged, strategy elements are clustered into ranked pillars, concrete actions and public commitments are mapped to those pillars, and a five-dimension weighted score quantifies coherence. The output is a scored drift report with full source citations.

```
Sources → Gather Info → Synthesize Pillars → Map Actions → Score Coherence → Report
           (parallel)                                      (5 dimensions)
```

**Scoring:** Aligned (>= 4.0) · Minor Drift (3.0-3.9) · Significant Drift (2.0-2.9) · Strategic Disconnect (< 2.0)

### 2. Peer Comparison

Benchmarks competitive positioning against industry peers across standardized metrics with strategic context.

Requires a completed drift analysis (uses pillar structure as the comparison framework).

### 3. Valuation Driver Analysis

The flagship pipeline. Identifies **which operational and financial metrics matter for valuation in alternative asset management**, then converts peer evidence into a PAX-first decision memo with explicit transferability, execution burden, and margin-risk controls.

```
Map the Industry → Gather Data → Find What Drives Value → Deep-Dive Peers → Build the Playbook
  (3 agents)       (4 agents)     (2 agents)               (2 agents)        (3 agents)
```

14 specialized agents work across five steps:

| Step | What Happens | Agents |
|---|---|---|
| **Map the Industry** | Identify ~25 listed peers, catalog sources, define metric taxonomy | Industry Scanner, Source Cataloger, Metrics Designer |
| **Gather Data** | Collect quantitative data (3 parallel tiers) and extract strategy profiles | Data Collector (x3), Strategy Researcher |
| **Find What Drives Value** | Standardize data, compute Spearman correlations, rank value drivers | Statistical Analyst, Convergence Analyst |
| **Deep-Dive Peers** | Platform-level profiles and sector-specific analysis for 9-12 firms | Platform Profiler, Sector Specialist |
| **Build the Playbook** | Synthesize insights, produce HTML report, contextualize for target company | Insight Synthesizer, Report Composer, Target Company Lens |

The final output is a navigable HTML **PAX decision memo** with three visible layers:
- **Peer evidence layer** — what the cross-peer data and deep-dives actually support
- **PAX interpretation layer** — transferability scoring, archetype relevance, and execution realism
- **PAX decision layer** — ranked strategic implications, margin-risk, and governance cascade

The playbook includes both proven plays (PLAY-NNN) and documented anti-patterns (ANTI-NNN). Every final recommendation must address transferability to PAX, operational and tech prerequisites, time-to-build, capital intensity, and margin-risk.

---

## Anti-Hallucination: Fact Checker

LLM agents tend to produce plausible-sounding but unsupported claims — particularly when constructing causal narratives from correlational data. The pipeline embeds a **Fact Checker** agent that runs at three checkpoints, auditing every claim against upstream evidence across four dimensions:

| Dimension | What It Catches |
|---|---|
| **Invalid premises** | Claims building on weak upstream outputs (e.g., treating a moderate correlation as a "stable driver") |
| **Misleading context** | Management narratives adopted as objective fact without independent corroboration |
| **Sycophantic fabrication** | Insights or recommendations generated to fill gaps, with no upstream evidence |
| **Confidence miscalibration** | Causal language ("drives", "demonstrates") for correlational or single-sourced evidence |

Claims receive structured verdicts: **Grounded**, **Inferred** (requires hedged language downstream), **Weak-Evidence** (annotated caveat), **Ungrounded** (hard block), or **Fabricated** (hard block). Blocked claims must be revised before the pipeline proceeds — with a maximum of two retries before forced downgrade.

The framework is grounded in the H-Neurons paper (Gao et al., 2025) on over-compliance in large language models.

---

## Architecture

This is a **prompt-driven analytical system**, not a traditional software project. There is no application server, no database, and no API. Analysis is executed entirely through Claude Code agent teams coordinated via prompt templates and structured handoffs.

```
prompts/               Version-controlled prompt templates
  ├── 0X_*.md            Drift pipeline (6 stages)
  ├── peer/p0X_*.md      Peer comparison (8 stages)
  └── vda/               VDA pipeline (claim auditor)

data/
  ├── raw/{ticker}/      Source documents per company
  └── processed/{ticker}/{date}/
        ├── 1-universe/    Peer universe, sources, metrics
        ├── 2-data/        Quantitative data, strategy profiles
        ├── 3-analysis/    Correlations, driver rankings
        ├── 4-deep-dives/  Platform and sector profiles
        ├── 5-playbook/    Final report, playbooks
        └── 6-review/      Post-analysis review

docs/
  ├── strategy-drift-methodology.md
  ├── peer-comparison-methodology.md
  ├── valuation-driver-methodology.md
  └── valuation-driver-methodology.html

src/
  ├── llm_client.py        Shared Anthropic SDK wrapper
  ├── document_converter.py PDF/DOCX/PPTX converter
  └── tauri/               Desktop dashboard (React + TypeScript + Tailwind + Rust)
```

### Statistical Methodology

The quantitative layer uses **Spearman rank correlation** (not regression — the ~25-firm universe lacks sufficient degrees of freedom for reliable multiple regression). Statistical governance is unified across the repo:
- Primary discovery framework: BH FDR `q = 0.10`
- Confirmatory badge: survives Bonferroni
- Primary inference for small-N rank tests: permutation-based p-values where feasible
- Leave-one-out, matched-sample, archetype-stratified, coverage, comparability, and confounding checks
- Explicit `mechanical_overlap_flag` where a driver is algebraically coupled to the valuation multiple

A metric may be called a **stable value driver** only if it satisfies the repository rule `stable_v1_two_of_three`.

### Source Controls

Every source is tagged with a bias classification (`regulatory-filing`, `company-produced`, `third-party-analyst`, `journalist`, `industry-report`, `peer-disclosure`). Claims resting solely on company-produced sources are explicitly qualified. Every claim must cite structured identifiers (PS-VD-\*, FIRM-\*, COR-\*, ACT-VD-\*, PLAY-\*, ANTI-\*).

---

## Desktop Dashboard

A **Tauri desktop app** provides a GUI for the VDA pipeline with:

- **Pipeline Monitor** — real-time step progression, agent status, checkpoint verification bars
- **Agents Org** — configure all 14 agents (model, temperature, tools, timeout, instructions)
- **Results Browser** — browse output files by step folder
- **Source Upload** — drag-and-drop supplemental documents (PDFs, DOCX, PPTX)

```bash
cd src/tauri && npm install && npm run tauri dev
```

---

## Running the Pipelines

All pipelines run through Claude Code slash commands:

```bash
# Strategy Drift Detection
/analyze-drift PAX              # interactive (pauses at quality gates)
/analyze-drift PAX --auto       # automatic (gates validated by lead agent)

# Valuation Driver Analysis
/valuation-driver PAX                           # interactive CLI
/valuation-driver PAX --auto                    # automatic
/valuation-driver PAX --ui                      # launch desktop dashboard
/valuation-driver PAX --sources /path/to/docs   # with supplemental data
/valuation-driver PAX --base-run 2026-03-06     # iterative refinement
/valuation-driver PAX --style-ref /path/to/doc  # match writing style

# Post-Analysis Review
/review-analysis PAX            # deploy review agents on completed analysis
```

### Prerequisites

- [Claude Code](https://claude.ai/code) CLI
- Python 3.11+ with `pip install -r requirements.txt`
- `ANTHROPIC_API_KEY` in `.env`
- For dashboard: Node.js 18+, Rust toolchain, Tauri prerequisites
- Optional contract validation: `python -m src.validation.vda_contracts /path/to/data/processed/pax/YYYY-MM-DD-runN`

### Crawlee Source Enrichment

The repo now includes a Crawlee-based enrichment step for VDA source catalogs. It reads the latest
`data/processed/pax/*/1-universe/source_catalog.json`, crawls the seeded URLs, follows a small number
of relevant links (earnings pages, SEC filings, investor presentations), and writes:

- structured crawl outputs to `data/processed/pax/<run>/1-universe/crawl/`
- extracted raw text files to `data/raw/pax/crawled/<run>/`

Run it with Python 3.11:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m src.ingestion.crawlee_vda --max-seeds 10
```

Useful flags:

```bash
python -m src.ingestion.crawlee_vda --catalog data/processed/pax/2026-03-09-run2/1-universe/source_catalog.json
python -m src.ingestion.crawlee_vda --max-seeds 25 --max-links-per-page 3 --max-requests 120
python -m src.ingestion.crawlee_vda --respect-robots-txt
```

To convert crawl output into a VDA-friendly dataset with per-source utility scores, signal counts,
ranked snippets, and firm-level evidence summaries:

```bash
python -m src.analyzer.crawl_vda_dataset --crawl-results data/processed/pax/2026-03-09-run2/1-universe/crawl/crawl_results.json
```

This writes `crawl_vda_dataset.json`, `crawl_vda_firm_summary.json`, and `crawl_vda_sources.csv`
to `data/processed/pax/<run>/2-data/`.

### Reuse for Another Company

Replace the ticker. All prompts use `{COMPANY}`, `{TICKER}`, and `{SECTOR}` placeholders. The VDA pipeline auto-detects sector and identifies peers:

```bash
/valuation-driver KKR --auto
/valuation-driver AAPL --auto
/analyze-drift MSFT --auto
```

---

## Methodology

Detailed methodology documents are available in `docs/`:

- **[Strategy Drift Methodology](docs/strategy-drift-methodology.md)** — 5-dimension weighted scoring, source bias controls
- **[Peer Comparison Methodology](docs/peer-comparison-methodology.md)** — standardized benchmarking framework
- **[PAX-First Valuation Driver Methodology](docs/pax-first-valuation-driver-methodology.md)** — authoritative PAX-first methodology, statistical governance, report contract, and validation rules
- **[Repository Drift Audit](docs/vda-repository-drift-audit.md)** — mismatch log, patch plan, and upgrade changelog
- **[Legacy Reusable VDA Methodology](docs/valuation-driver-methodology.md)** — archived neutral-spec snapshot retained for historical reference only

---

## Tech Stack

| Component | Technology |
|---|---|
| Agent orchestration | Claude Code (`TeamCreate` / `Agent` / `SendMessage`) |
| LLM | Claude Opus 4.6 (reasoning), Claude Sonnet 4.6 (extraction) |
| LLM wrapper | `src/llm_client.py` (Anthropic SDK) |
| Prompts | Markdown templates with `{COMPANY}` / `{TICKER}` / `{SECTOR}` placeholders |
| Desktop dashboard | Tauri 2.0 + React + TypeScript + Tailwind CSS |
| Document conversion | marker-pdf (PDF/DOCX/PPTX to text) |
| Statistical method | Spearman rank correlation with BH FDR q=0.10, Bonferroni confirmatory badge, and permutation-based inference where feasible |
| Reports | Self-contained HTML with sidebar navigation, sortable tables, collapsible sections |
