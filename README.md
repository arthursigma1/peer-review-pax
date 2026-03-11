# Strategy Intelligence System

AI agent system that identifies what drives valuation multiples across a peer universe and produces governance-ready strategic playbooks — with built-in anti-hallucination safeguards. Designed for board-level and C-suite executives making high-stakes strategic decisions.

Currently applied to **Patria Investments Limited (PAX)** in alternative asset management.

---

## What It Does

The system runs three analytical pipelines, each orchestrated by specialized AI agent teams through Claude Code:

| Pipeline | Purpose | Output |
|---|---|---|
| **Valuation Driver Analysis** | Identify which metrics drive valuation multiples across ~25 peers, produce a strategic playbook | HTML decision memo with plays, anti-patterns, and governance cascade |
| **Strategy Drift Detection** | Evaluate whether a company's actions align with its stated strategic priorities | Scored drift report with 5-dimension weighted assessment |
| **Peer Comparison** | Benchmark competitive positioning against industry peers | Comparative rankings with strategic context |

The **Valuation Driver Analysis (VDA)** is the flagship pipeline. It maps an industry's peer universe, collects quantitative and qualitative data, runs statistical analysis to identify value drivers, deep-dives the most informative peers, and synthesizes everything into a PAX-first decision memo with three visible layers:

- **Peer evidence layer** — what the cross-peer data actually supports
- **Interpretation layer** — transferability scoring, archetype relevance, execution realism
- **Decision layer** — ranked strategic implications, margin-risk, and governance cascade (PHL/Board → Management → per-BU)

---

## VDA Pipeline

14 specialized agents work across five steps:

```
Map the Industry → Gather Data → Find What Drives Value → Deep-Dive Peers → Build the Playbook
  (3 agents)        (4 agents)    (2 agents)                (2 agents)       (3 agents)
```

| Step | What Happens | Agents | Key Outputs |
|---|---|---|---|
| **Map the Industry** | Identify ~25 listed peers, catalog sources, define metric taxonomy | Industry Scanner, Source Cataloger, Metrics Designer | `peer_universe.json`, `source_catalog.json`, `metric_taxonomy.json` |
| **Gather Data** | Collect quantitative data (3 parallel tiers of ~9 firms) and extract strategy profiles | Data Collector (x3), Strategy Researcher | `quantitative_tier1/2/3.json`, `strategy_profiles.json`, `strategic_actions.json` |
| **Find What Drives Value** | Standardize data, compute Spearman correlations, rank drivers | Statistical Analyst, Convergence Analyst | `standardized_matrix.json`, `correlation_results.json`, `driver_ranking.json` |
| **Deep-Dive Peers** | Platform-level profiles and sector-specific analysis for 9-12 firms | Platform Profiler, Sector Specialist | `platform_profiles.json`, `asset_class_analysis.json` |
| **Build the Playbook** | Synthesize insights, generate HTML report, contextualize for target company | Insight Synthesizer, Report Composer, Target Company Lens | `playbook.json`, `target_lens.json`, `final_report.html` |

The playbook includes both proven plays (PLAY-NNN) and documented anti-patterns (ANTI-NNN). Every recommendation addresses transferability, operational prerequisites, time-to-build, capital intensity, and margin-risk.

### Fact Checker

LLM agents tend to produce plausible-sounding but unsupported claims — particularly when constructing causal narratives from correlational data. A **Fact Checker** agent runs at three checkpoints, auditing every claim against upstream evidence:

| Dimension | What It Catches |
|---|---|
| **Invalid premises** | Claims building on weak upstream outputs (e.g., treating a moderate correlation as a "stable driver") |
| **Misleading context** | Management narratives adopted as objective fact without independent corroboration |
| **Sycophantic fabrication** | Insights generated to fill gaps, with no upstream evidence |
| **Confidence miscalibration** | Causal language ("drives", "demonstrates") for correlational or single-sourced evidence |

Claims receive structured verdicts: **Grounded**, **Inferred** (requires hedged language), **Weak-Evidence** (annotated caveat), **Ungrounded** (hard block), or **Fabricated** (hard block). Blocked claims must be revised before the pipeline proceeds.

### Statistical Methodology

The quantitative layer uses **Spearman rank correlation** (not regression — the ~25-firm universe lacks sufficient degrees of freedom for reliable multiple regression):

- Primary discovery: Benjamini-Hochberg FDR `q = 0.10`
- Confirmatory badge: survives Bonferroni correction
- Leave-one-out, matched-sample, archetype-stratified, coverage, comparability, and confounding checks
- Explicit `mechanical_overlap_flag` where a driver is algebraically coupled to the valuation multiple
- A metric qualifies as a **stable value driver** only under `stable_v1_two_of_three`

### Source Controls

Every source is tagged with a bias classification (`regulatory-filing`, `company-produced`, `third-party-analyst`, `journalist`, `industry-report`, `peer-disclosure`). Claims resting solely on company-produced sources are explicitly qualified. Every claim must cite structured identifiers (PS-VD-\*, FIRM-\*, COR-\*, PLAY-\*, ANTI-\*).

---

## Desktop Dashboard

A **Tauri desktop app** provides a GUI for the VDA pipeline:

- **Pipeline Monitor** — real-time step progression with agent status cards and checkpoint verification
- **Embedded Terminal** — fully interactive Claude Code CLI session via PTY (portable-pty + xterm.js)
- **Agents Org** — configure all 14 agents (model, temperature, tools, timeout, instructions)
- **Results Browser** — browse output files by step folder
- **Run Digest** — summary statistics and quality metrics per run

```bash
cd src/tauri && npm install && npm run tauri dev
```

---

## Architecture

```
prompts/
  ├── drift/            Drift pipeline templates (6 stages)
  ├── peer/             Peer comparison templates (8 stages)
  └── vda/              VDA pipeline templates (claim auditor)

data/
  ├── raw/{ticker}/     Source documents per company
  │   ├── drift/          Drift-era raw extractions
  │   ├── canonical/      Crawled canonical documents
  │   └── crawled/        Web crawler outputs by run
  └── processed/{ticker}/
      ├── drift/          Drift + peer comparison outputs
      └── {YYYY-MM-DD}/   VDA run outputs
          ├── 1-universe/    Peer universe, sources, metrics
          ├── 2-data/        Quantitative data, strategy profiles
          ├── 3-analysis/    Correlations, driver rankings
          ├── 4-deep-dives/  Platform and sector profiles
          ├── 5-playbook/    Final report, playbooks, target lens
          └── 6-review/      Post-analysis review

src/
  ├── analyzer/         Data quality tools (10+ modules)
  │   ├── metric_checklist.py     Per-tier metric checklist
  │   ├── data_gaps.py            Gap analysis of standardized matrix
  │   ├── delta_spec.py           Incremental collection specs
  │   ├── context_slicer.py       Pre-slice context for agents
  │   ├── evidence_store.py       Evidence persistence layer
  │   ├── carry_forward_registry.py  Base-run data carryforward
  │   ├── consulting_context.py   Build context from consulting crawls
  │   └── crawl_vda_dataset.py    Transform crawl output to VDA dataset
  ├── ingestion/        Web crawlers
  │   ├── crawlee_vda.py          Crawlee-based source enrichment
  │   └── source_catalog.py       Source catalog utilities
  ├── report/           Report system
  │   ├── style_guide.html        Visual style reference
  │   ├── report_schema.json      Report structure contract
  │   └── report_validator.py     Post-generation validation
  ├── validation/       Schema validation
  │   └── vda_contracts.py        Runtime output validation
  ├── tauri/            Desktop dashboard
  │   ├── src-tauri/src/lib.rs    Rust backend (PTY, file watcher, IPC)
  │   └── src/                    React frontend
  ├── llm_client.py     Shared Anthropic SDK wrapper
  └── document_converter.py  PDF/DOCX/PPTX converter (marker-pdf)

docs/
  ├── methodology/      Reusable methodology docs
  ├── vda/              VDA reference docs
  ├── pax/              PAX-specific docs
  └── plans/            Execution plans

archive/                Legacy files (not deleted, just moved)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Agent orchestration** | Claude Code (`TeamCreate` / `Agent` / `SendMessage`) |
| **LLM** | Claude Opus 4.6 (reasoning), Claude Sonnet 4.6 (extraction, pipeline agents) |
| **LLM wrapper** | `src/llm_client.py` — Anthropic SDK with Langfuse tracing |
| **Web crawling** | Crawlee + BeautifulSoup, Scrapling, Playwright |
| **Desktop app** | Tauri 2.0 (Rust backend, WebView frontend) |
| **Terminal emulation** | portable-pty (Rust) + xterm.js (browser) |
| **Frontend** | React 19, TypeScript 5.9, Tailwind CSS 4 |
| **Document conversion** | marker-pdf (PDF/DOCX/PPTX → text) |
| **Data validation** | Pydantic 2, custom contract validators |
| **Statistical method** | Spearman rank correlation, BH FDR q=0.10, Bonferroni confirmatory |
| **Reports** | Self-contained HTML with sidebar navigation, sortable tables, collapsible sections |
| **Prompts** | Markdown templates with `{COMPANY}` / `{TICKER}` / `{SECTOR}` placeholders |

---

## Usage

### Running Pipelines

All pipelines run through Claude Code slash commands:

```bash
# Valuation Driver Analysis
/valuation-driver PAX                           # interactive CLI
/valuation-driver PAX --auto                    # fire-and-forget
/valuation-driver PAX --ui                      # launch desktop dashboard
/valuation-driver PAX --sources /path/to/docs   # with supplemental data
/valuation-driver PAX --base-run 2026-03-09     # iterative refinement on prior run
/valuation-driver PAX --style-ref /path/to/doc  # match reference writing style
/valuation-driver PAX --from-step 3 --to-step 5 # partial pipeline run

# Strategy Drift Detection
/analyze-drift PAX              # interactive (pauses at quality gates)
/analyze-drift PAX --auto       # automatic

# Post-Analysis Review
/review-analysis PAX            # deploy review agents on completed analysis
```

### Web Crawling

```bash
# Crawl sources from latest VDA source catalog
python -m src.ingestion.crawlee_vda --max-seeds 10

# Crawl from specific catalog
python -m src.ingestion.crawlee_vda --catalog data/processed/pax/2026-03-09-run2/1-universe/source_catalog.json

# Convert crawl output to VDA dataset
python -m src.analyzer.crawl_vda_dataset --crawl-results data/processed/pax/2026-03-09-run2/1-universe/crawl/crawl_results.json
```

### Data Quality Tools

```bash
# Metric checklist — per-tier collection priority
python3 -m src.analyzer.metric_checklist --run-dir data/processed/pax/2026-03-09-run2/

# Gap analysis — classify and prioritize data gaps
python3 -m src.analyzer.data_gaps --run-dir data/processed/pax/2026-03-09-run2/

# Delta spec — incremental collection plan from base run
python3 -m src.analyzer.delta_spec --base-run data/processed/pax/2026-03-09-run2/ --new-run-dir data/processed/pax/2026-03-10/

# Context slicer — reduce agent context load by 40-96%
python3 -m src.analyzer.context_slicer --run-dir data/processed/pax/2026-03-10-run2/

# Report validation
python3 -m src.report.report_validator --html data/processed/pax/2026-03-10-run2/5-playbook/final_report.html
```

### Prerequisites

- [Claude Code](https://claude.ai/code) CLI
- Python 3.11+ with `pip install -r requirements.txt`
- `ANTHROPIC_API_KEY` in `.env`
- For dashboard: Node.js 18+, Rust toolchain, [Tauri prerequisites](https://v2.tauri.app/start/prerequisites/)

---

## Reuse for Another Company

Replace the ticker. All prompts use `{COMPANY}`, `{TICKER}`, and `{SECTOR}` placeholders. The VDA pipeline auto-detects sector and identifies peers:

```bash
/valuation-driver KKR --auto
/valuation-driver AAPL --auto
/analyze-drift MSFT --auto
```

---

## Methodology

Detailed methodology documents in `docs/methodology/`:

- **[Strategy Drift](docs/methodology/strategy-drift-methodology.md)** — 5-dimension weighted scoring, source bias controls
- **[Peer Comparison](docs/methodology/peer-comparison-methodology.md)** — standardized benchmarking framework
- **[PAX-First VDA](docs/methodology/pax-first-valuation-driver-methodology.md)** — authoritative methodology, statistical governance, report contract

VDA reference docs in `docs/vda/`:

- **[Correlation Classification](docs/vda/vda-correlation-classification.md)** — stable / multiple-specific / contextual / unsupported
- **[Consulting Evidence Hierarchy](docs/vda/vda-consulting-evidence-hierarchy.md)** — PS-VD-9xx rules, agent routing
- **[Agent Orchestration](docs/vda/vda-agent-orchestration.md)** — 1-agent-per-firm, gap-fill, stall detection

---

## Project Status

**Active development.** The VDA pipeline is the primary focus, with PAX (Patria Investments) as the initial target company. The system is designed for reuse across any public company and sector.
