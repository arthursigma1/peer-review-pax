# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Strategy Drift Detector + Peer Comparison + Valuation Driver Analysis — an AI agent system that (1) evaluates whether a public company's actions align with its stated strategic priorities, (2) benchmarks the company's competitive positioning against industry peers, and (3) identifies what drives valuation multiples across a peer universe and produces a strategic playbook with a Target Company Lens for governance cascade. Currently applied to **Block, Inc.** (drift) and **Patria Investments Limited (PAX)** (drift + peer comparison + VDA). The system is prompt-driven; analysis executes through Claude Code agent teams. Supports iterative refinement via `--base-run`. A **Tauri desktop dashboard** provides a GUI for the VDA pipeline.

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
Map the Industry → Gather Data → Find What Drives Value → Deep-Dive Peers → Build the Playbook (+ Target Company Lens)
```

- **Map the Industry** — Identify peers, catalog sources, define metrics (3 parallel agents: Industry Scanner, Source Cataloger, Metrics Designer). Supplemental sources get `track_affinity` tags (`quantitative`, `qualitative`, or `both`) for agent-level source routing.
- **Gather Data** — Collect quantitative data and extract strategies (Data Collector splits into 3 tiers of ~9 firms; Strategy Researcher runs in parallel)
- **Find What Drives Value** — Standardize, correlate (Spearman), rank drivers (Statistical Analyst, sequential)
- **Deep-Dive Peers** — Platform profiles and asset class analysis (Platform Profiler + Sector Specialist, parallel)
- **Build the Playbook** — Synthesize insights and generate HTML report (Insight Synthesizer + Report Composer, sequential). Playbooks include Anti-patterns (ANTI-NNN) alongside proven plays (PLAY-NNN). Target Company Lens agent extracts transferable principles from peer evidence for governance cascade (PHL/Board → Management → per-BU) — language is exploratory, not prescriptive. A Ghost Report Skeleton (action titles) is produced before the final report to ensure narrative coherence. Supports `--base-run YYYY-MM-DD` for iterative refinement and `--style-ref /path/to/doc` for writing style matching. Writing reference: `docs/sigma-final-report-guide.md`.

**Independence:** VDA pipeline operates independently of the drift pipeline. No PIL-* pillar IDs are referenced.

**Claim Verification:** A Fact Checker agent runs at three checkpoints (CP-1 after data collection, CP-2 after deep-dives, CP-3 after playbook) to verify claims against upstream evidence using a 4-dimension over-compliance audit. Ungrounded or fabricated claims trigger a hard block requiring revision.

**Methodology:** `docs/pax-first-valuation-driver-methodology.md` — Authoritative PAX-first VDA methodology reference. The legacy reusable spec in `docs/valuation-driver-methodology.md` is archival only.

### Key Directories

- `prompts/` — Drift pipeline prompt templates (`0X_*.md`), version-controlled
- `prompts/peer/` — Peer comparison pipeline prompt templates (`p0X_*.md`)
- `data/raw/{ticker}/` — Raw source documents per company
- `data/processed/{ticker}/` — Pipeline outputs per company (drift, peer, VDA)
- `docs/plans/` — Execution plans with agent team architecture
- `docs/strategy-drift-methodology.md` — Reusable drift methodology
- `docs/peer-comparison-methodology.md` — Reusable peer comparison methodology
- `docs/pax-first-valuation-driver-methodology.md` — Authoritative PAX-first VDA methodology
- `docs/vda-repository-drift-audit.md` — Drift log and patch plan
- `docs/valuation-driver-methodology.md` — Legacy reusable VDA methodology kept for historical reference
- `docs/sigma-final-report-guide.md` — SIGMA writing guide for final report (Pyramid Principle, action titles, footnotes, bumper statements)
- `src/tauri/` — Tauri desktop dashboard (React + TypeScript + Tailwind + Rust)
- `src/analyzer/` — VDA data quality tools (metric_checklist, data_gaps, delta_spec, consulting_context)
- `src/report/` — Report consistency system (style_guide.html, report_schema.json, report_validator.py)
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

# VDA data quality tools
python3 -m src.analyzer.metric_checklist --run-dir data/processed/pax/2026-03-09-run2/
python3 -m src.analyzer.data_gaps --run-dir data/processed/pax/2026-03-09-run2/
python3 -m src.analyzer.delta_spec --base-run data/processed/pax/2026-03-09-run2/ --new-run-dir data/processed/pax/2026-03-10/
python3 -m src.analyzer.delta_spec --merge --new-run-dir data/processed/pax/2026-03-10/  # after delta collection

# Build consulting context from crawl outputs
python3 -m src.analyzer.consulting_context --seed-results data/processed/pax/2026-03-09-run2/1-universe/crawl-with-consulting/consulting_seed_results.json

# Validate a generated VDA report
python3 -m src.report.report_validator --html data/processed/pax/2026-03-10-run2/5-playbook/final_report.html

# Validate with regression check against a base run
python3 -m src.report.report_validator --html path/to/final_report.html --base-run data/processed/pax/2026-03-09-run2/
```

## Skills (Slash Commands)

### `/analyze-drift TICKER [--auto]`

Run the full Strategy Drift Detection pipeline for any public company.

- `TICKER` — stock ticker symbol (e.g., `SQ`, `PAX`, `AAPL`)
- `--auto` — optional flag for fire-and-forget mode (quality gates validated automatically)
- Without `--auto` — interactive mode, pauses at each quality gate for user approval

Output: `data/processed/{TICKER}/{YYYY-MM-DD}/final_report.md` + `final_report.html`

### `/valuation-driver TICKER [--auto] [--ui] [--sources /path/to/dir] [--base-run YYYY-MM-DD] [--style-ref /path/to/doc] [--from-step N] [--to-step N]`

Run the full Valuation Driver Analysis pipeline for any public company.

- `TICKER` — stock ticker symbol (e.g., `PAX`, `BX`, `KKR`)
- `--auto` — optional flag for fire-and-forget mode
- `--ui` — launch the Tauri desktop dashboard instead of CLI mode
- `--sources /path/to/dir` — optional path to supplemental data files (PDFs, DOCX, PPTX converted via marker-pdf)
- `--base-run YYYY-MM-DD` — optional date of a previous run; agents improve upon prior outputs rather than starting from scratch
- `--style-ref /path/to/doc` — optional reference document whose writing style the final report should match
- `--from-step N` — start from step N (1–6); prior step outputs are read from the most recent existing run
- `--to-step N` — stop after step N (1–6); steps after N are not executed

Steps: 1=Map the Industry, 2=Gather Data, 3=Find What Drives Value, 4=Deep-Dive Peers, 5=Build the Playbook, 6=Review Analysis

Output: `data/processed/{TICKER}/{YYYY-MM-DD}/5-playbook/final_report.html` + supporting JSON files organized in step folders

### `/review-analysis TICKER [--report path]`

Deploy review agents on any completed VDA analysis to identify improvement opportunities.

- `TICKER` — stock ticker of the analysis to review
- `--report path` — optional override for report location

Output: `data/processed/{TICKER}/{YYYY-MM-DD}/6-review/methodology_review.md` + `6-review/results_review.md`

### `/consistency-check`

Audit cross-cutting dependencies across pipeline agents, dashboard, CLAUDE.md, and report system. Read-only — flags mismatches across 6 domains:
- Canonical filenames (CLAUDE.md, SKILL.md, usePipeline.ts, lib.rs)
- Agent names (CLAUDE.md, SKILL.md, ptyParser.ts)
- Design tokens (theme.ts, index.css, style_guide.html)
- Report schema (report_schema.json, report_validator.py, style_guide.html)
- Pipeline flow (SKILL.md, usePipeline.ts, CLAUDE.md)
- Methodology (methodology doc, CLAUDE.md conventions)

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
| target-lens | Target Company Lens | Build the Playbook |
| claim-auditor | Fact Checker | Verify Claims (CP-1, CP-2, CP-3) |

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
- Every claim in VDA reports must cite source IDs (PS-VD-*, FIRM-*, MET-VD-*, COR-*, DVR-*, ACT-VD-*, PLAY-*, ANTI-*)
- Per-company directory convention: `data/processed/{ticker}/`, `data/raw/{ticker}/`
- Multiple runs per day use incremental suffix: `YYYY-MM-DD`, `YYYY-MM-DD-run2`, `YYYY-MM-DD-run3`
- VDA data collection always splits into 3 parallel tiers (~9 firms each)
- VDA output files use folder structure: `{ticker}/{date}/{step-folder}/` where step folders are: `1-universe`, `2-data`, `3-analysis`, `4-deep-dives`, `5-playbook`, `6-review`
- **VDA canonical output filenames** — Pipeline agents MUST use these exact names. The Tauri dashboard detects step completion and infers agent activity from filenames. Changing a filename without updating both the SKILL.md and the dashboard (`usePipeline.ts` STEP_COMPLETE_REQS + FILE_TO_AGENT, `lib.rs` detect_existing_session) will break the UI.

| Step | Folder | Canonical Files |
|---|---|---|
| 0 | 1-universe | `peer_universe.json`, `metric_taxonomy.json`, `source_catalog.json` |
| 1 | 2-data | `quantitative_tier1.json`, `quantitative_tier2.json`, `quantitative_tier3.json`, `strategy_profiles.json`, `strategic_actions.json`, `metric_checklist.json`, `delta_spec.json` (if `--base-run`), `consulting_context.json` (if consulting crawl exists) |
| 2 | 3-analysis | `standardized_matrix.json`, `correlation_results.json`, `driver_ranking.json`, `data_gaps.json` |
| 3 | 4-deep-dives | `platform_profiles.json`, `asset_class_analysis.json` |
| 4 | 5-playbook | `playbook.json`, `target_lens.json`, `final_report.html` |
| 5 | 6-review | `methodology_review.md`, `results_review.md` |
- VDA playbooks include Anti-patterns (ANTI-NNN) alongside proven plays (PLAY-NNN)
- VDA Fact Checker produces audit files per checkpoint: `audit_cp1_data.json`, `audit_cp2_deep_dives.json`, `audit_cp3_playbook.json`
- Claims marked `INFERRED` by Fact Checker require hedged language in final report ("suggests", "appears to", never "demonstrates" or "proves")
- VDA reports use a structured tone profile (`style_guide.json`) — default is academic/evidence-based; custom tone extracted from user-uploaded reference documents

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
| Stable value driver | Satisfies repository rule `stable_v1_two_of_three` |
| Multiple-specific driver | `abs(rho) >= 0.5` on exactly one eligible multiple and fails stable rule |
| Contextual driver | Useful for decomposition or interpretation but not headline ranking |
| Unsupported | Not defensible for strategic interpretation |

## VDA Consulting Evidence Hierarchy

Consulting and industry-report sources (PS-VD-9xx) are **market context only**. Peer evidence always wins.

| Rule | Detail |
|---|---|
| Peer evidence > consulting | If a consulting source conflicts with a filing, earnings deck, or investor presentation, the firm source wins |
| Consulting cannot solely sustain | firm-specific metrics, firm-specific actions, causal claims about a specific firm, or final recommendations |
| Allowed usage | `market_context`, `distribution_context`, `operating_model_context`, `supporting_context` |
| Disallowed usage | `firm_specific_fact`, `firm_specific_metric`, `firm_specific_action`, `sole_basis_for_recommendation` |
| Citation rule | PS-VD-9xx may cite market-level claims; firm-specific claims require peer PS-VD sources |
| claim-auditor enforcement | Any claim where PS-VD-9xx is the sole citation AND the claim is about a specific firm → BLOCK |

**Agents that consume `consulting_context.json`:** strategy-extractor, vertical-analyst, playbook-synthesizer, target-lens, report-builder, claim-auditor.
**Agents that do NOT receive it:** data-collector-t1, data-collector-t2, data-collector-t3.

**Claim scope classification:** Each claim in `consulting_context.json` has a `scope` field (`market`, `segment`, `multi_firm`, `single_firm`). Claims with `single_firm` scope must not be used as firm-specific evidence.

## VDA Agent Orchestration Best Practices

Learned from 2026-03-09-run2 (best run to date). These patterns prevent agent stalls and context overflow:

1. **1-agent-per-firm for qualitative tasks** — Never assign 15 firms to a single agent. Each agent handles 1 firm (profile + actions). ~27K tokens each, zero stalls. Dispatch all 15 in parallel.
2. **No WebSearch for qualitative data** — Strategy profiles and strategic actions of major public alt-asset managers are well-known. Use training data only. WebSearch is the #1 context consumer and primary cause of stalls.
3. **Incremental file writing** — Instruct agents to write partial results every 3 firms. If they stall at firm 12, you still have 9 firms saved.
4. **Gap-fill pattern** — When an agent completes partially (e.g., 4 of 8 profiles), dispatch a smaller agent to fill ONLY the gap. Read existing file → append → overwrite. Never redo completed work.
5. **Split read-heavy from write-heavy** — Separate "research + profile" from "research + actions" into two parallel agents per firm if needed.
6. **Simplified schemas for large outputs** — `operational_prerequisites` with 7 nested subfields causes stalls. Use `op_prereq_summary` (single string) instead. Expand in post-processing if needed.
7. **Merge pattern for parallel per-firm agents** — Each agent writes to `profiles/{TICKER}.json` and `actions/{TICKER}.json`. A merge script combines all fragments into the canonical `strategy_profiles.json` and `strategic_actions.json`.
8. **Context budget rule of thumb** — Agents that read >3 files AND do WebSearch will likely stall before writing. Keep total input under 50K tokens per agent.
9. **Stall detection** — Monitor URL log line count + output file existence. If URL log is frozen for >5 min with no new output file, the agent has stalled. Redispatch immediately.
10. **`bypassPermissions` mode** — Background agents with `settings.local.json` restrictions silently fail on Write/Bash. Use `mode: bypassPermissions` or ensure permissions include `Write(**)`, `Bash(*)`.

## Reuse for Another Company

Replace "Block, Inc." in prompts, update source-scout search targets, and re-run the pipeline. All prompts are designed with `{COMPANY}`, `{TICKER}`, and `{SECTOR}` placeholders. For peer comparison, also identify industry-specific peers and metrics appropriate to the target company's sector. For VDA, run `/valuation-driver TICKER` — the pipeline auto-detects sector and identifies peers.

## Design Context

### Users
Board-level and C-suite executives reviewing completed valuation driver analysis for governance decisions. They open this tool expecting clarity, authority, and confidence — not to tinker, but to understand and act. Every element must earn the trust of someone making high-stakes decisions.

### Brand Personality
**Authoritative, elegant, restrained.** The tool projects institutional weight. The interface is quiet — it never competes with the data for attention. Think McKinsey deliverable meets Bloomberg density.

### Aesthetic Direction
- **Reference**: Bloomberg Terminal — dense, functional, information hierarchy achieved through typography alone, every pixel justified
- **Theme**: Light mode only. White base, blue (#0068ff) accent, gray hierarchy
- **Typography**: DM Sans at varied weights (headings and body), IBM Plex Mono (tickers, data, logs). Self-hosted woff2 at `public/fonts/`
- **Shape language**: `rounded-md` containers, `rounded` inputs. Institutional, not playful
- **Color restraint**: Blue accent used sparingly for actions and focus. Status colors (emerald, red, amber) for pipeline state only. No decorative color
- **Terminal**: Dark island (`bg-gray-900`) inside light shell, `bg-gray-100` chrome as transition bridge
- **Anti-references**: Generic SaaS dashboards (Intercom/HubSpot), AI/ML demo apps (purple gradients, glow), hacker aesthetic (neon-on-dark), overdesigned Dribbble concepts (form over function)

### Design Principles
1. **Data speaks, UI recedes** — The interface is invisible infrastructure. No decoration, no personality injection. Typography and whitespace create hierarchy, not color or ornament.
2. **Earn every element** — If it doesn't inform a decision, remove it. No placeholder illustrations, no "Get Started!" energy, no marketing copy in a tool built for analysis.
3. **Density over simplicity** — Executives scan, they don't browse. Prefer information-rich layouts (tables, inline stats, compact cards) over spacious hero sections. Respect the user's time and screen real estate.
4. **Trust through craft** — Consistent spacing, aligned baselines, proper contrast ratios (WCAG AA minimum). Sloppy details erode confidence in the analysis itself.
5. **Convention over invention** — Terminals are dark. Buttons look like buttons. Navigation is where you expect it. Don't innovate on established patterns — execute them flawlessly.
