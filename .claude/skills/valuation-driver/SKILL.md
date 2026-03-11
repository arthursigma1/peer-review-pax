---
name: valuation-driver
description: Run the full Valuation Driver Analysis pipeline for any public company. Orchestrates 14 specialized agents across 5 steps to identify what drives valuation multiples and produce a strategic playbook. Usage: /valuation-driver TICKER [--auto] [--ui] [--sources /path/to/dir] [--base-run YYYY-MM-DD] [--evidence-mode legacy|incremental] [--style-ref /path/to/doc] [--from-step N] [--to-step N]
---

# Valuation Driver Analysis

Identify which operational and financial metrics drive valuation multiples across an industry peer universe, then synthesize a peer-derived strategic playbook.

## Usage

```
/valuation-driver TICKER                              # interactive CLI (pauses at quality gates)
/valuation-driver TICKER --auto                       # automatic CLI (gates validated by lead agent)
/valuation-driver TICKER --ui                         # launch Tauri desktop dashboard
/valuation-driver TICKER --sources /path/to/dir       # with supplemental proprietary data
/valuation-driver TICKER --auto --sources /path       # automatic + supplemental data
/valuation-driver TICKER --base-run 2026-03-06        # iterative: improve upon previous run
/valuation-driver TICKER --evidence-mode incremental  # reuse canonical evidence store + plan recrawls only for gaps
/valuation-driver TICKER --style-ref /path/to/doc     # match writing style of reference doc
/valuation-driver TICKER --from-step 2                # start from step 2 (skip step 1)
/valuation-driver TICKER --to-step 3                  # stop after step 3
/valuation-driver TICKER --from-step 2 --to-step 4    # run steps 2–4 only
```

## Step 0: Parse Arguments

Extract from the user's input:
- `TICKER` (required) — e.g., `PAX`, `BX`, `KKR`
- `--ui` flag (optional) — if present, launch the Tauri desktop dashboard instead of running in CLI mode
- `--auto` flag (optional) — if present, quality gates are validated automatically; otherwise interactive
- `--sources /path/to/dir` (optional) — path to a directory containing supplemental data files (PDFs, DOCX, PPTX)
- `--base-run YYYY-MM-DD` (optional) — date of a previous run to use as baseline. Agents receive previous outputs as context and are instructed to improve upon them.
- `--evidence-mode legacy|incremental` (optional) — defaults to `legacy`. `incremental` keeps the run-local contracts unchanged but resolves sources against the global `source_inventory/` control plane and the canonical evidence store.
- `--style-ref /path/to/doc` (optional) — path to a reference document whose writing style the report should match.
- `--from-step N` (optional) — start execution from pipeline step N (1-indexed: 1=Map the Industry, 2=Gather Data, 3=Find What Drives Value, 4=Deep-Dive Peers, 5=Build the Playbook, 6=Review Analysis). Steps before N are skipped; their outputs are read from the most recent existing run in `data/processed/{TICKER}/`.
- `--to-step N` (optional) — stop execution after pipeline step N (inclusive, same 1-indexed scale). Steps after N are not executed.

Set `FROM_STEP` to the value of `--from-step` (default: 1).
Set `TO_STEP` to the value of `--to-step` (default: 6).
Set `EVIDENCE_MODE` to the value of `--evidence-mode` (default: `legacy`).

If no TICKER is provided, ask the user for one.

### Step Range Behavior

When `FROM_STEP > 1`:
- Locate the most recent existing output directory for this ticker: find the latest `data/processed/{TICKER}/YYYY-MM-DD*/` that contains relevant output files for steps before `FROM_STEP`.
- All agents in skipped steps read their inputs from that directory. The current run's output directory is still created fresh.
- Display to the user: "Starting from Step {FROM_STEP}. Using existing outputs from `data/processed/{TICKER}/{prior_date}/` for steps 1–{FROM_STEP - 1}."
- **Important:** If no prior outputs are found for a required skipped step, warn the user and ask whether to run from Step 1 instead.

When `TO_STEP < 6`:
- After completing Step `TO_STEP`, display: "Stopped after Step {TO_STEP} as requested. Run with `--from-step {TO_STEP + 1}` to continue."
- Do not execute any quality gates or agents for steps after `TO_STEP`.

### If `--ui` is present:

Launch the Tauri desktop dashboard pre-configured with the given TICKER:

1. Check that dependencies are installed:
   ```bash
   cd src/tauri && npm install
   ```
2. Launch the dashboard in development mode:
   ```bash
   cd src/tauri && npm run tauri dev
   ```
3. The dashboard opens with the Home screen. The user controls the pipeline from the UI (start, quality gate approvals, results browsing).
4. **Stop here** — do not proceed with CLI pipeline steps below. The UI handles everything.

### If `--ui` is NOT present (default CLI mode):

Set `DATE` to today's date in `YYYY-MM-DD` format.
Set `TICKER_LOWER` to the lowercase version of `TICKER`.

## Step 1: Create Directory Structure

Check if `data/processed/{TICKER}/{DATE}/` already exists. If it does, find the highest existing run suffix:

```bash
# Look for {DATE}, {DATE}-run2, {DATE}-run3, etc.
ls -d data/processed/{TICKER}/{DATE}* 2>/dev/null
```

- If `{DATE}/` does not exist → use `{DATE}` as-is
- If `{DATE}/` exists but `{DATE}-run2/` does not → set `DATE` to `{DATE}-run2`
- If `{DATE}-run2/` exists → set `DATE` to `{DATE}-run3`, and so on

After resolving, create the directories:

```
data/processed/{TICKER}/{DATE}/
data/raw/{TICKER}/{DATE}/
```

Display to the user: "Output directory: `data/processed/{TICKER}/{DATE}/`" (so they know which run this is).

## Step 2: Company Context Discovery

Before spawning agents, research the company and create `data/processed/{TICKER}/{DATE}/company_context.json`.

Use WebSearch to find:
- Full legal company name
- Stock exchange
- CEO and CFO names
- Primary sector and industry classification
- Major business segments / asset classes managed
- Investor relations URL
- SEC CIK number or local equivalent (for non-US filers)
- Any recent name changes or corporate restructuring

Also determine the sector automatically. For alternative asset managers, set `SECTOR` to `alt-asset-management`. For other sectors, set based on GICS or equivalent classification.

Save as JSON:

```json
{
  "company_name": "...",
  "ticker": "TICKER",
  "exchange": "...",
  "sector": "...",
  "ceo": "...",
  "cfo": "...",
  "business_segments": ["...", "..."],
  "primary_asset_classes": ["...", "..."],
  "ir_url": "...",
  "sec_cik": "...",
  "recent_name_changes": "...",
  "supplemental_sources_dir": null
}
```

If `--sources` was provided, set `supplemental_sources_dir` to that path.

If `--base-run` was provided:
- Set `base_run_date` to the provided date
- Verify `data/processed/{TICKER}/{base_run_date}/` exists and contains outputs
- Add `"base_run": "YYYY-MM-DD"` to company_context.json
- All subsequent agents receive additional instruction: "Previous analysis outputs are available at `data/processed/{TICKER}/{base_run_date}/`. Review them as context. Your goal is to IMPROVE upon these findings — fill data gaps, strengthen weak conclusions, incorporate new sources. Do not simply repeat previous findings."

If `--style-ref` was provided:
- Read the reference document
- Extract key style characteristics (tone, structure, terminology, level of detail)
- Store as `data/processed/{TICKER}/{DATE}/style_guide.json` with fields: `tone`, `formality`, `terminology_examples`, `structure_notes`
- The report-builder agent receives this as additional context

### Tone Profile

If a tone profile was provided (via `--style-ref` or the Tauri UI's tone capture), write it to `data/processed/{TICKER}/{DATE}/style_guide.json`.

If no tone profile was provided, write the default tone profile:

```json
{
  "source": "default",
  "reference_files": [],
  "formality": "academic",
  "voice": "active",
  "sentence_style": "concise",
  "hedging": "explicit",
  "data_presentation": "tables-first",
  "terminology": "technical",
  "nuances": "Lead with the answer before the evidence (Pyramid Principle). Section headers are action titles that state a conclusion, not topic labels (e.g., 'Scale is the dominant valuation driver, but not all scale is equal' not 'Industry Value Drivers'). Every claim cites a numbered footnote linking to source title, date, and bias tag. Use Oxford commas. Qualify correlation-based findings with statistical confidence. Avoid marketing language. Statistical methodology details belong in the Appendix, not inline. Plays are framed as observed peer mechanisms, not recommendations. Reference: docs/sigma-final-report-guide.md"
}
```

The report-builder agent already reads `style_guide.json` if it exists.

Display the discovered context to the user and confirm before proceeding.

## Step 3: Peer Validation (if reference list provided)

If the user provides a reference peer list (e.g., in the initial message or as a file), cross-reference it against the auto-generated universe that will be built in Step 5.

**Note:** This is a forward-looking step. At this point, store any user-provided reference list in `data/processed/{TICKER}/{DATE}/user_peer_list.json`. After Step 5 (universe-scout output), revisit this file and:
- Surface peers in the user list that the scout did not include (notable omissions)
- Surface peers the scout included that the user did not list (additions)
- Ask: "Your reference list differs from the auto-generated universe in the following ways. Approve, modify, or override?"

In `--auto` mode, skip this gate and proceed automatically, but log the diff to `data/processed/{TICKER}/{DATE}/peer_list_diff.md`.

## Step 4: Process Supplemental Sources (if --sources provided)

If `--sources` was provided, use `src/document_converter.py` to convert all files in the directory:

```python
# Convert all PDFs, DOCX, PPTX in supplemental directory
python src/document_converter.py --input {sources_dir} --output data/raw/{TICKER}/{DATE}/supplemental/
```

Tag each converted file with the appropriate bias type based on filename and content:
- Sell-side research → `third-party-analyst`
- Investor day slides → `company-produced`
- Industry reports (Preqin, Bain, McKinsey) → `industry-report`
- Internal databases / Preqin exports → `third-party-analyst`

Store a manifest at `data/raw/{TICKER}/{DATE}/supplemental/manifest.json` listing each file, its bias tag, and the firm(s) it covers.

Each source in `manifest.json` also gets a `track_affinity` field:
- `"quantitative"` — sell-side research, analyst models, financial databases → prioritized by data-collector agents
- `"qualitative"` — consulting reports (McKinsey, BCG, Bain), strategy presentations, Investor Day decks → prioritized by strategy-extractor agent
- `"both"` — earnings call transcripts, annual reports (contain both quant data and strategic commentary)

Agents should check `track_affinity` and prioritize sources matching their track.

Make the supplemental manifest path available to all agents in subsequent steps.

## Step 5: Placeholder Resolution Reference

When agents use prompts from `prompts/`, they must replace these placeholders with values from `company_context.json`:

| Placeholder | Source |
|-------------|--------|
| `{COMPANY}` | `company_name` |
| `{TICKER}` | `ticker` |
| `{TICKER_LOWER}` | lowercase `ticker` |
| `{EXCHANGE}` | `exchange` |
| `{CEO}` | `ceo` |
| `{CFO}` | `cfo` |
| `{SEGMENTS}` | `business_segments` (comma-separated) |
| `{SECTOR}` | `sector` |
| `{DATE}` | today's date (YYYY-MM-DD) |

All output file paths use: `data/processed/{TICKER}/{DATE}/` and `data/raw/{TICKER}/{DATE}/`

## Step 5b: Load Agent Configuration

Before spawning any agent, check if a custom agent configuration exists:

1. Read `.claude/agent_config.json` using the Read tool (path: `{PROJECT_ROOT}/.claude/agent_config.json` where `{PROJECT_ROOT}` is the repository root).
2. If the file exists and parses as valid JSON, use it as the **agent config**. For each agent being spawned, find the matching entry by `id` in the config's `agents` array.
3. If the file does not exist, use the default values specified in each agent section below.

**Overridable parameters from agent config:**
- `model` → pass as the `model` parameter to the Agent tool call (e.g., `model: "claude-sonnet-4-6"`)
- `temperature` → prepend to the agent's prompt: `"Temperature: {value}. "`
- `max_output_tokens` → prepend to the agent's prompt: `"Max output tokens: {value}. "`
- `tools` → the agent should only use tools listed in this array
- `instructions` → if present and non-empty, append to the base prompt as additional context: `"\n\nAdditional instructions from config:\n{instructions}"`
- `timeout_minutes` → use as the timeout for the Agent tool call (converted to milliseconds)

**Non-overridable (always from SKILL.md):**
- Full spawn prompt (the detailed Instructions block for each agent)
- Input/output file paths
- Pipeline step assignment and execution order
- Quality gate criteria

**Command-level overrides:** If the config has a `command` object:
- `command.auto_mode` → use as the auto/interactive mode flag (overrides `--auto` CLI flag)
- `command.tier_size` → use as the number of firms per data-collector tier
- `command.base_run` → use as the base run date (overrides `--base-run` CLI flag)
- `command.evidence_mode` → use as the evidence mode for this run (overrides `--evidence-mode`)
- `command.tone_profile` → pass to the report-builder agent as tone configuration

The Tauri dashboard's Agents tab saves this config file. Users can modify agent models, temperatures, tools, and other parameters through the UI, and the pipeline will respect those settings on the next run.

## Step 6: Create Agent Team

```
TeamCreate → team_name: "vda-{TICKER_LOWER}"
```

### Agent Roster

| Agent | User-Facing Name | Pipeline Step |
|---|---|---|
| universe-scout | Industry Scanner | Map the Industry |
| source-mapper | Source Cataloger | Map the Industry |
| metric-architect | Metrics Designer / Statistical Analyst | Map the Industry / Find What Drives Value |
| data-collector-t1/t2/t3 | Data Collector (3 tiers) | Gather Data |
| strategy-extractor | Strategy Researcher | Gather Data |
| convergence-analyst | Convergence Analyst | Find What Drives Value |
| platform-analyst | Platform Profiler | Deep-Dive Peers |
| vertical-analyst | Sector Specialist | Deep-Dive Peers |
| playbook-synthesizer | Insight Synthesizer | Build the Playbook |
| report-builder | Report Composer | Build the Playbook |
| target-lens | Target Company Lens | Build the Playbook |
| **claim-auditor** | **Fact Checker** | **CP-1 (post Gate 2), CP-2 (post Gate 4), CP-3 (pre report-builder)** |

- **claim-auditor** (Fact Checker): Verifies all claims against upstream evidence using 4-dimension over-compliance audit. Runs at checkpoints CP-1, CP-2, CP-3. Model: claude-opus-4-6. Temperature: 0.0. Max tokens: 32000. Tools: Read, Grep, Glob.

## General Output Conventions (All Agents)

**Trace metadata (OPTIONAL):** If you have access to session information, add a `_trace_metadata` field to your JSON output:

```json
{
  "_trace_metadata": {
    "agent_name": "<your-agent-name>",
    "session_id": "<claude-code-session-id-if-available>",
    "step": "<pipeline-step>",
    "started_at": "<ISO-8601>",
    "completed_at": "<ISO-8601>"
  }
}
```

This field is optional — if omitted, the claim indexer and Langfuse hooks will degrade gracefully.

## Step 7: Step 1 of 5 — "Map the Industry" (Parallel)

**Step range check:** If `FROM_STEP > 1`, skip this step entirely. Load existing outputs for this step from the prior run directory identified in the Step Range Behavior section above.

Spawn three agents in parallel:

### Agent: universe-scout

Spawn with Agent tool (subagent_type: general-purpose, name: "universe-scout", model: "claude-sonnet-4-6", team_name: "vda-{TICKER_LOWER}"):

Instructions:
> You are the universe-scout agent for the Valuation Driver Analysis pipeline.
>
> **Company:** {COMPANY} ({EXCHANGE}: {TICKER})
> **Sector:** {SECTOR}
> **Date:** {DATE}
>
> **Your task:** Execute Stage VD-A0 — Peer Universe Identification.
>
> Catalog all publicly listed alternative asset managers globally. The target universe is approximately 25 firms. Classification is by business model composition:
> - `pure-play-alt`: >= 90% of revenue from alternative asset management
> - `majority-alt`: 60–89% of revenue from alternative asset management
> - `partial-alt`: Meaningful alternative segment but majority of revenue from other activities
>
> Expected universe (indicative, not prescriptive):
> - United States: BX, KKR, APO, ARES, BAM, OWL, TPG, CG, BN, STEP, HLN, AMK, VCTR
> - Europe: EQT, PGHN (Partners Group), ICP (Intermediate Capital), MAN (Man Group)
> - Latin America: PAX (Patria Investments)
> - Search for any additional firms not on this list
>
> For each firm, record: full legal name, ticker, exchange, classification, latest AUM (USD billions), primary asset classes, inclusion/exclusion rationale.
>
> Use WebSearch extensively. Prioritize regulatory filings and factual data sources. Do not estimate or interpolate any values — record `null` with a `missing_reason` for unavailable data.
>
> **URL log:** Append every URL you visit to `data/raw/{TICKER}/{DATE}/urls_consumed_universe.jsonl` — one JSON object per line: `{"url": "...", "firm": "...", "timestamp": "...", "status": "ok|error|irrelevant"}`.
>
> **Output:** `data/processed/{TICKER}/{DATE}/1-universe/peer_universe.json`
>
> Schema per firm:
> ```json
> {
>   "firm_id": "FIRM-NNN",
>   "firm_name": "...",
>   "ticker": "...",
>   "exchange": "...",
>   "classification": "pure-play-alt | majority-alt | partial-alt",
>   "latest_aum_usd_bn": ...,
>   "primary_asset_classes": ["..."],
>   "inclusion_rationale": "...",
>   "exclusion_rationale": null
> }
> ```

### Agent: source-mapper

Spawn with Agent tool (subagent_type: general-purpose, name: "source-mapper", model: "claude-sonnet-4-6", team_name: "vda-{TICKER_LOWER}"):

Instructions:
> You are the source-mapper agent for the Valuation Driver Analysis pipeline.
>
> **Company:** {COMPANY} ({EXCHANGE}: {TICKER})
> **Date:** {DATE}
>
> **Your task:** Execute Stage VD-B0 — Source Mapping for qualitative peers.
>
> Catalog sources for the initial qualitative peer set (~12–15 firms): BX, KKR, APO, ARES, BAM, OWL, TPG, CG, EQT, PGHN, STEP, HLN, BN, ICP, AMK.
>
> **Source types to catalog:**
> - Primary public filings: 20-F / 10-K, 6-K / 10-Q, proxy statements
> - Management communications: Investor Day presentations, earnings call transcripts, earnings supplements, CEO letters
> - Third-party sources: Preqin reports, Bain Global PE Report, McKinsey Global Private Markets Review, sell-side research
> - M&A announcements: press releases, merger proxy filings
> - Non-obvious sources: pension fund board documents (CalPERS, CalSTRS, CPPIB), job postings, patent/trademark filings, conference speaker assignments
>
> **Check supplemental sources:** If `data/raw/{TICKER}/{DATE}/supplemental/manifest.json` exists, include those sources in the catalog with their pre-assigned bias tags.
>
> Assign **PS-VD-NNN** IDs to all sources. For each source record: firm, title, date, document type, bias tag, URL or filing reference, relevance notes.
>
> **Bias tags:** `company-produced`, `regulatory-filing`, `third-party-analyst`, `journalist`, `industry-report`, `peer-disclosure`
>
> **URL log:** Append every URL you visit to `data/raw/{TICKER}/{DATE}/urls_consumed_sources.jsonl` — one JSON object per line: `{"url": "...", "firm": "...", "timestamp": "...", "status": "ok|error|irrelevant"}`.
>
> **Output:** `data/processed/{TICKER}/{DATE}/1-universe/source_catalog.json`
>
> Schema per source:
> ```json
> {
>   "source_id": "PS-VD-NNN",
>   "firm": "...",
>   "title": "...",
>   "date": "YYYY-MM-DD",
>   "document_type": "...",
>   "bias_tag": "...",
>   "url_or_reference": "...",
>   "relevance_notes": "..."
> }
> ```

### Agent: metric-architect

Spawn with Agent tool (subagent_type: general-purpose, name: "metric-architect", model: "claude-sonnet-4-6", team_name: "vda-{TICKER_LOWER}"):

Instructions:
> You are the metric-architect agent for the Valuation Driver Analysis pipeline.
>
> **Company:** {COMPANY} ({EXCHANGE}: {TICKER})
> **Sector:** {SECTOR}
> **Date:** {DATE}
>
> **Your task:** Execute Stage VD-A1 — Metric Taxonomy Definition.
>
> Define all metrics organized by category. Metrics are divided into driver candidates (independent variables) and valuation multiples (dependent variables). Market structure metrics are collected as contextual data only — explicitly excluded from correlation analysis.
>
> **Required driver categories and metrics:**
>
> Earnings: DE/share, EPS (GAAP), DE/share growth 3-year CAGR
> Scale: Fee-Earning AUM (FEAUM), Total AUM, FEAUM YoY growth, FEAUM 3-year CAGR
> Organic Growth: Net organic FEAUM growth, Fundraising as % of AUM
> Mix and Diversification: Asset class HHI (Herfindahl-Hirschman Index), Permanent capital %, Credit % of AUM
> Efficiency: FRE margin, FRE growth YoY, Comp-to-revenue ratio
> Fee Quality: Management fee rate (FRE/FEAUM in bps), Performance fee share of total revenue
> Operational Feasibility & Scalable Infrastructure (alt-asset-manager overlay — include when `{SECTOR}` is `alt-asset-management`):
>   - Headcount_to_FEAUM (total headcount / FEAUM)
>   - FEAUM_per_Employee (FEAUM / total headcount)
>   - Compensation_and_Benefits_to_FEAUM (total comp & benefits / FEAUM, or nearest proxy such as comp-to-mgmt-fee-revenue)
>   - G&A_to_FEAUM (G&A expense / FEAUM)
>   - OpEx_Growth_minus_Fee_Revenue_Growth (trailing OpEx growth rate minus fee revenue growth rate)
>   - Constant_Currency_Revenue_Growth (revenue growth after removing FX translation effects)
>   - Integration_Costs_to_Revenue (integration/restructuring charges / total revenue — only when separately disclosed)
>   - CapEx_to_FEAUM (capex / FEAUM — only when technology/software capex is separately identifiable)
>   - Technology_Platform_Maturity (qualitative ordinal metric — collected for all firms regardless of capex disclosure. Values: 0 = standard vendor stack, 1 = proprietary internal platform, 2 = proprietary platform with ML/AI integration, 3 = commercialized technology product sold externally. Source from investor presentations, 20-F disclosures, and management commentary. This metric does NOT require disclosed technology capex — it is assessed from public evidence of technology capability.)
>
> **Coverage rule:** any Operational Feasibility metric with fewer than 60% of universe firms reporting is classified as `contextual-only` and excluded from correlation analysis in VD-A4. It may still appear in context tables and deep-dives.
>
> For non-alt-manager sectors, map this category to sector-specific "cost-to-scale" metrics (e.g., revenue per employee, SG&A-to-revenue). Do not force FEAUM-based metrics into non-alt-manager sectors.
>
> **Valuation multiples (dependent variables):**
> P/FRE, P/DE, EV/FEAUM
>
> **Market structure metrics (contextual only — exclude from correlation):**
> Average daily trading volume, Passive ownership %, Free float %
>
> For each metric, record: metric ID (MET-VD-NNN), name, abbreviation, unit, category, is_driver_candidate (boolean), calculation_notes.
>
> Note on Asset class HHI: calculated as sum of squared market share proportions across asset classes multiplied by 10,000. Higher = more concentrated.
>
> **Output:** `data/processed/{TICKER}/{DATE}/1-universe/metric_taxonomy.json`

### Quality Gate 1

After all three agents complete, check:

**Criteria:**
- Universe has >= 20 firms identified
- Metric taxonomy is internally consistent (no duplicate metric IDs, all required categories present)
- Source catalog meets minimum coverage: >= 3 sources per qualitative peer

**Interactive mode:** Display to user:
- Firm count in universe
- Metric count by category
- Source coverage summary (min/max/avg sources per firm)
- Ask: "Universe and metrics look good. Proceed to data gathering?"

**Auto mode:** Verify all three criteria. If universe < 20 firms, send message to universe-scout to expand search. If source coverage is insufficient, send message to source-mapper to fill gaps. Once criteria met, proceed automatically.

### Consulting Context Processing

If consulting crawl outputs exist at `data/processed/{TICKER}/{DATE}/1-universe/crawl-with-consulting/consulting_seed_results.json`:

1. Run the consulting context processor:
   ```bash
   python3 -m src.analyzer.consulting_context --seed-results data/processed/{TICKER}/{DATE}/1-universe/crawl-with-consulting/consulting_seed_results.json --output-dir data/processed/{TICKER}/{DATE}/2-data/
   ```
2. Verify output: `data/processed/{TICKER}/{DATE}/2-data/consulting_context.json`
3. Log: `[CONSULTING] Built consulting_context.json — {N} sources included, {M} excluded`

If no consulting crawl outputs exist, skip this step. The pipeline proceeds without consulting context.

### Incremental Evidence Bootstrap

If `EVIDENCE_MODE == incremental`:

1. Ensure the global control-plane artifacts exist under `data/processed/{TICKER}/source_inventory/`. If any are missing, build them in this order:
   ```bash
   python3 -m src.analyzer.carry_forward_registry --processed-root data/processed/{TICKER}/ --output-dir data/processed/{TICKER}/source_inventory/
   python3 -m src.analyzer.evidence_store --registry data/processed/{TICKER}/source_inventory/carry_forward_registry.json --canonical-root data/raw/{TICKER}/canonical --output-dir data/processed/{TICKER}/source_inventory/
   python3 -m src.analyzer.recrawl_resolution --registry data/processed/{TICKER}/source_inventory/carry_forward_registry.json --output-dir data/processed/{TICKER}/source_inventory/
   ```
2. Materialize the run-local manifests:
   ```bash
   python3 -m src.analyzer.incremental_bootstrap --run-dir data/processed/{TICKER}/{DATE}/ --registry data/processed/{TICKER}/source_inventory/carry_forward_registry.json --evidence-index data/processed/{TICKER}/source_inventory/evidence_store_index.json --recrawl-resolution data/processed/{TICKER}/source_inventory/recrawl_resolution.json
   ```
3. Verify the run-local artifacts:
   - `data/processed/{TICKER}/{DATE}/1-universe/source_resolution.json`
   - `data/processed/{TICKER}/{DATE}/1-universe/reuse_manifest.json`
   - `data/processed/{TICKER}/{DATE}/1-universe/recrawl_plan.json`
4. Log: `[INCREMENTAL] Evidence mode incremental enabled — reuse manifest and recrawl plan materialized for this run`

If `EVIDENCE_MODE == legacy`, skip this section entirely. Downstream steps keep consuming the same run-local contracts either way.

## Step 8: Step 2 of 5 — "Gather Data" (Parallel)

**Step range check:** If `FROM_STEP > 2`, skip this step and load existing outputs from the prior run. If `TO_STEP < 2`, stop here after completing Step 1 and display the stop message.

Spawn two agents in parallel:

### Agent: data-collector

**CRITICAL: Split into 3 parallel tiers of ~9 firms each. Never assign 25+ firms to one agent — this will cause timeouts and incomplete output.**

**Pre-dispatch: Generate metric checklist and (optionally) delta spec**

Before spawning data-collector agents, generate the metric checklist:

```bash
python3 -m src.analyzer.metric_checklist --run-dir data/processed/{TICKER}/{DATE}/
```

This creates `2-data/metric_checklist.json` with per-tier, per-firm collection priorities (critical/high/medium/low/skip).

If `--base-run` was provided, also generate the delta spec:

```bash
python3 -m src.analyzer.data_gaps --run-dir data/processed/{TICKER}/{base_run_date}/
python3 -m src.analyzer.delta_spec --base-run data/processed/{TICKER}/{base_run_date}/ --new-run-dir data/processed/{TICKER}/{DATE}/
```

This creates `2-data/delta_spec.json` with carry-forward data (never re-collected), skip list (confirmed non-disclosure), and targeted collection assignments per tier. **When delta_spec.json exists, data-collector agents collect ONLY cells listed in `collect.tierN.assignments` — no other metrics.**

**Pre-dispatch: Pre-slice context files for data-collector agents**

After generating checklist and delta_spec, run context_slicer to produce per-tier slices:

```bash
python3 -m src.analyzer.context_slicer --run-dir data/processed/{TICKER}/{DATE}/ --only consulting-slim,checklist-tiers,delta-tiers
```

This creates `consulting_context_slim.json`, `metric_checklist_tier{1,2,3}.json`, and `delta_spec_tier{1,2,3}.json` — reducing each data-collector's context load by ~45K tokens.

Spawn three sub-instances of the data-collector, each covering a tier of firms:

**Tier 1 (top firms by AUM — approximately first 9):**

Spawn with Agent tool (subagent_type: general-purpose, name: "data-collector-t1", model: "claude-sonnet-4-6", team_name: "vda-{TICKER_LOWER}"):

Instructions:
> You are data-collector-t1 for the Valuation Driver Analysis pipeline.
>
> **Your task:** Execute Stage VD-A2 — Data Collection for Tier 1 firms.
>
> Read `data/processed/{TICKER}/{DATE}/1-universe/peer_universe.json` to get the full firm list.
> Read `data/processed/{TICKER}/{DATE}/1-universe/metric_taxonomy.json` to get the metric taxonomy.
> Read `data/processed/{TICKER}/{DATE}/2-data/metric_checklist_tier1.json` for per-metric collection priorities (pre-sliced to your tier's firms only). Focus effort on `critical` and `high` priority metrics first. For `skip` priority metrics, do not attempt collection.
> If `data/processed/{TICKER}/{DATE}/2-data/delta_spec_tier1.json` exists, this is an incremental run. Read the delta spec and collect ONLY the metrics listed in `collect.tier1.assignments` for your tier's firms. Carry-forward data is already preserved — do NOT re-collect existing data points.
>
> **Cover firms ranked 1–9 by AUM** (the largest firms in the universe).
>
> For each firm and each metric, collect a **5-year panel**: FY T through FY T-4, where T is the most recent completed fiscal year (currently FY2024, so collect FY2020–FY2024). FY T and FY T-1 are mandatory; FY T-2 through FY T-4 are best-effort. For each data point, record the exact `period` (e.g., `FY2022`), `period_end_date`, and `fiscal_year_type` (calendar vs non-calendar with month).
>
> Primary sources: earnings releases, annual reports (20-F / 10-K), investor day presentations, earnings supplements, filesystem at `data/raw/{TICKER}/{DATE}/supplemental/` (check manifest.json — supplemental data takes priority over web search).
>
> For each data point record: firm_id, metric_id, value, period, currency, source_id, bias_tag, confidence (high/medium/low), extraction_notes.
>
> Missing data: record as `null` with explicit `missing_reason`. No estimation or interpolation. **However, when a target metric is not directly disclosed but its components are available, derive the ratio.** Tag derived values with `derivation_method` (formula), `component_sources` (source IDs for each input), and `derivation_confidence` (`high` if both components from same filing, `medium` if different filings, `low` if any component estimated). Common derivable metrics: Compensation_to_Revenue (comp / mgmt fee revenue), G&A_to_FEAUM (G&A / FEAUM), Headcount_to_FEAUM (employees / FEAUM). Derived metrics with confidence `low` are classified `contextual_only`.
>
> **URL log:** Append every URL you visit (WebSearch result pages, WebFetch targets, filing URLs) to `data/raw/{TICKER}/{DATE}/urls_consumed_tier1.jsonl` — one JSON object per line: `{"url": "...", "firm": "...", "timestamp": "...", "status": "ok|error|irrelevant"}`. Write this log incrementally as you work, not just at the end.
>
> **Output:** `data/processed/{TICKER}/{DATE}/2-data/quantitative_tier1.json`

**Tier 2 (mid-tier firms — approximately firms 10–18):**

Spawn with Agent tool (subagent_type: general-purpose, name: "data-collector-t2", model: "claude-sonnet-4-6", team_name: "vda-{TICKER_LOWER}"):

Instructions:
> You are data-collector-t2 for the Valuation Driver Analysis pipeline.
>
> **Your task:** Execute Stage VD-A2 — Data Collection for Tier 2 firms.
>
> Read `data/processed/{TICKER}/{DATE}/1-universe/peer_universe.json` to get the full firm list.
> Read `data/processed/{TICKER}/{DATE}/1-universe/metric_taxonomy.json` to get the metric taxonomy.
> Read `data/processed/{TICKER}/{DATE}/2-data/metric_checklist_tier2.json` for per-metric collection priorities (pre-sliced to your tier's firms only). Focus effort on `critical` and `high` priority metrics first. For `skip` priority metrics, do not attempt collection.
> If `data/processed/{TICKER}/{DATE}/2-data/delta_spec_tier2.json` exists, this is an incremental run. Read the delta spec and collect ONLY the metrics listed in `collect.tier2.assignments` for your tier's firms. Carry-forward data is already preserved — do NOT re-collect existing data points.
>
> **Cover firms ranked 10–18 by AUM** (mid-tier firms in the universe).
>
> For each firm and each metric, collect a **5-year panel**: FY T through FY T-4, where T is the most recent completed fiscal year (currently FY2024, so collect FY2020–FY2024). FY T and FY T-1 are mandatory; FY T-2 through FY T-4 are best-effort. For each data point, record the exact `period` (e.g., `FY2022`), `period_end_date`, and `fiscal_year_type` (calendar vs non-calendar with month).
>
> Primary sources: earnings releases, annual reports (20-F / 10-K), investor day presentations, earnings supplements. Check `data/raw/{TICKER}/{DATE}/supplemental/manifest.json` — supplemental data takes priority.
>
> For each data point record: firm_id, metric_id, value, period, currency, source_id, bias_tag, confidence, extraction_notes. Missing data → `null` with `missing_reason`. **However, when a target metric is not directly disclosed but its components are available, derive the ratio.** Tag derived values with `derivation_method` (formula), `component_sources` (source IDs), and `derivation_confidence` (`high`/`medium`/`low`). Common derivable metrics: Compensation_to_Revenue, G&A_to_FEAUM, Headcount_to_FEAUM. Derived metrics with confidence `low` are `contextual_only`.
>
> **URL log:** Append every URL you visit to `data/raw/{TICKER}/{DATE}/urls_consumed_tier2.jsonl` — one JSON object per line: `{"url": "...", "firm": "...", "timestamp": "...", "status": "ok|error|irrelevant"}`.
>
> **Output:** `data/processed/{TICKER}/{DATE}/2-data/quantitative_tier2.json`

**Tier 3 (remaining firms — approximately firms 19–end):**

Spawn with Agent tool (subagent_type: general-purpose, name: "data-collector-t3", model: "claude-sonnet-4-6", team_name: "vda-{TICKER_LOWER}"):

Instructions:
> You are data-collector-t3 for the Valuation Driver Analysis pipeline.
>
> **Your task:** Execute Stage VD-A2 — Data Collection for Tier 3 firms.
>
> Read `data/processed/{TICKER}/{DATE}/1-universe/peer_universe.json` to get the full firm list.
> Read `data/processed/{TICKER}/{DATE}/1-universe/metric_taxonomy.json` to get the metric taxonomy.
> Read `data/processed/{TICKER}/{DATE}/2-data/metric_checklist_tier3.json` for per-metric collection priorities (pre-sliced to your tier's firms only). Focus effort on `critical` and `high` priority metrics first. For `skip` priority metrics, do not attempt collection.
> If `data/processed/{TICKER}/{DATE}/2-data/delta_spec_tier3.json` exists, this is an incremental run. Read the delta spec and collect ONLY the metrics listed in `collect.tier3.assignments` for your tier's firms. Carry-forward data is already preserved — do NOT re-collect existing data points.
>
> **Cover firms ranked 19 through the end** (smaller firms in the universe).
>
> For each firm and each metric, collect a **5-year panel**: FY T through FY T-4, where T is the most recent completed fiscal year (currently FY2024, so collect FY2020–FY2024). FY T and FY T-1 are mandatory; FY T-2 through FY T-4 are best-effort. For each data point, record the exact `period` (e.g., `FY2022`), `period_end_date`, and `fiscal_year_type` (calendar vs non-calendar with month).
>
> Primary sources: earnings releases, annual reports (20-F / 10-K), investor day presentations, earnings supplements. Check `data/raw/{TICKER}/{DATE}/supplemental/manifest.json` — supplemental data takes priority.
>
> For each data point record: firm_id, metric_id, value, period, currency, source_id, bias_tag, confidence, extraction_notes. Missing data → `null` with `missing_reason`. **However, when a target metric is not directly disclosed but its components are available, derive the ratio.** Tag derived values with `derivation_method` (formula), `component_sources` (source IDs), and `derivation_confidence` (`high`/`medium`/`low`). Common derivable metrics: Compensation_to_Revenue, G&A_to_FEAUM, Headcount_to_FEAUM. Derived metrics with confidence `low` are `contextual_only`.
>
> **URL log:** Append every URL you visit to `data/raw/{TICKER}/{DATE}/urls_consumed_tier3.jsonl` — one JSON object per line: `{"url": "...", "firm": "...", "timestamp": "...", "status": "ok|error|irrelevant"}`.
>
> **Output:** `data/processed/{TICKER}/{DATE}/2-data/quantitative_tier3.json`

After all three tiers complete:

**If `--base-run` was provided:** Merge carry-forward data into the tier files before proceeding. This injects base-run data points that were NOT re-collected into the tier files so the standardization step sees the full dataset:

```bash
python3 -m src.analyzer.delta_spec --merge --new-run-dir data/processed/{TICKER}/{DATE}/
```

**Then** merge tier outputs into a single file:

> Send to metric-architect (via SendMessage):
> Merge `2-data/quantitative_tier1.json`, `2-data/quantitative_tier2.json`, `2-data/quantitative_tier3.json` into a single `2-data/quantitative_data.json`. Deduplicate by firm_id + metric_id + period. Log any conflicts (same firm+metric+period with different values) to `2-data/merge_conflicts.md`.

### Agent: strategy-extractor

Spawn with Agent tool (subagent_type: general-purpose, name: "strategy-extractor", model: "claude-opus-4-6", team_name: "vda-{TICKER_LOWER}"):

Instructions:
> You are the strategy-extractor agent for the Valuation Driver Analysis pipeline.
>
> **Company context:** {COMPANY} ({EXCHANGE}: {TICKER}) — but note: this pipeline is peer-centric. Do NOT treat {COMPANY} as the baseline or reference point. Study peers on their own terms.
>
> **Your tasks (sequential):**
>
> **Task A — Stage VD-B1:** Execute Strategy Extraction for all firms in the qualitative peer set.
>
> Read `data/processed/{TICKER}/{DATE}/1-universe/source_catalog.json` for sources.
> Read `docs/pax-peer-strategy-ontology.md` for the minimum business-model decomposition grid.
> Read `docs/pax-peer-assessment-framework.md` for business context.
> Read `data/processed/{TICKER}/{DATE}/2-data/consulting_context_slim.json` if it exists — use it ONLY to enrich `contextual_market_factors` and to frame industry trends (retailization, wealth-channel expansion, fee pressure, fundraising conditions, operating-model demands). Do NOT use consulting sources to assert a peer strategic action or stated priority unless peer/company evidence also supports it.
>
> **CONSULTING RULE:** consulting_context_slim.json is market context only. Never use it as primary evidence for firm-specific metrics, actions, or causal claims. If consulting conflicts with peer evidence, peer evidence wins.
>
> For each firm in the qualitative peer set (read the list from `1-universe/peer_universe.json`), extract a standalone strategic profile by mapping the peer across the full ontology grid:
> - Geographical reach
> - Business focus
> - Asset focus
> - Asset class and investment strategies (with sub-strategies per vertical: PE, Credit, Infrastructure, Real Estate, Natural Resources)
> - Sector orientation
> - Origination engine
> - Fund type
> - Capital source
> - Distribution strategy
> - Client segment
> - Growth agenda
> - Share class
> - Stated strategic priorities (top 3–5 verbatim or closely paraphrased from most recent Investor Day or annual report)
>
> Also capture contextual market factors (TAM, market share, governance, regulation) separately from the business-model grid — these are market-context data, not strategic choices.
>
> Use `null` plus `missing_reason` for dimensions without adequate evidence. Do not force-fit. Add new categories only when repeated evidence requires it. The ontology is a minimum baseline, not a ceiling.
>
> Profiles are self-contained — they do not reference {COMPANY} and do not compare firms against any external benchmark.
>
> **URL log:** Append every URL you visit to `data/raw/{TICKER}/{DATE}/urls_consumed_strategy.jsonl` — one JSON object per line: `{"url": "...", "firm": "...", "timestamp": "...", "status": "ok|error|irrelevant"}`.
>
> **Output A:** `data/processed/{TICKER}/{DATE}/2-data/strategy_profiles.json` (must conform to `schemas/vda/strategy_profile.schema.json`)
>
> **Task B — Stage VD-B2:** Execute Action Cataloging for all firms in the qualitative peer set.
>
> For each firm, catalog concrete strategic actions taken in the prior 2–3 years. For each action record:
> - action_id (ACT-VD-NNN)
> - firm_id
> - action_type: `M&A`, `product-launch`, `geographic-expansion`, `distribution-shift`, `capital-structure-change`, `organizational-change`, `technology-operations`, `technology-investment`
> - description
> - stated_rationale (from management communications)
> - observable_metric_impact (quantitative or directional, if disclosed)
> - timeline (announced, closed, operational)
> - source_citation (PS-VD-NNN)
>
> **Operational Prerequisites:** For every strategic action (M&A, fund launch, product launch, distribution expansion, technology initiative, operating platform acquisition), extract concurrent `operational_prerequisites` — the hidden infrastructure, systems, and organizational changes required to execute the action. Required subfields:
> - `systems_integration` — ERP, portfolio management, or front-office system consolidation
> - `data_reporting_stack` — data warehouse, LP reporting, regulatory reporting upgrades
> - `qa_controls_reconciliation` — QA, NAV reconciliation, operational control changes
> - `fund_admin_servicing` — fund administration, transfer agency, investor servicing changes
> - `compliance_risk_treasury` — compliance infrastructure, risk management, treasury ops
> - `hiring_org_redesign` — hiring waves, organizational restructuring, team integration
> - `geographic_integration` — cross-border operational complexity, local entity setup, regulatory licensing
>
> **Search priority (in order):**
> 1. Filings / annual reports / investor day materials — highest trust
> 2. Earnings transcripts and prepared remarks — moderate trust
> 3. Reputable media and analyst coverage — moderate trust
> 4. Job postings and vendor PRs — supporting evidence only; NEVER sufficient as sole basis for a GROUNDED verdict
>
> For each prerequisite, record: `source_bias_tag`, `evidence_class` (directly_documented / corroborated / inferred).
> If a prerequisite is inferred rather than directly documented, mark it `INFERRED` and require hedged language downstream ("the acquisition likely required…", "this expansion appears to have involved…").
> No operational prerequisite may be labeled GROUNDED if it relies only on job postings, vendor PRs, or management commentary without corroboration.
>
> **Technology and data platform actions (mandatory sweep):**
> For every firm, explicitly check for actions in these categories. If evidence exists, catalog them. If no evidence exists, record `no_tech_action_found: true` for the firm (so downstream agents know the absence is verified, not overlooked):
> - Proprietary technology platform build or acquisition (e.g., EQT Motherbrain, Hamilton Lane Cobalt, KKR Global Atlantic systems)
> - AI/ML integration into investment process or operations (e.g., Man Group systematic trading, Two Sigma quantitative models)
> - Commercialization of data/analytics products to external clients
> - Digital distribution platform launch or investment (e.g., iCapital partnership, direct-to-retail digital channels)
> - Operational automation or technology-driven headcount efficiency initiatives
> Use `action_type: technology-operations` for internal platforms and `action_type: technology-investment` for external-facing or commercialized products.
>
> **Output B:** `data/processed/{TICKER}/{DATE}/2-data/strategic_actions.json`

### Quality Gate 2

After all four agents complete (three data-collector tiers + strategy-extractor), check:

**Criteria:**
- Data coverage: >= 60% of metrics are populated for >= 80% of universe firms
- **Universe hygiene:** exclude firms with < 15% metric coverage or flagged as `model_incompatible` from the correlation universe. These firms remain in the qualitative peer set. Log `N_effective` (number of firms entering correlation analysis) — this must be >= 15
- All three valuation multiples (P/FRE, P/DE, EV/FEAUM) are populated for all firms
- Qualitative profiles have >= 2 concrete actions per firm (VD-B2)
- **Operational metrics coverage:** verify disclosure quality for Operational Feasibility & Scalable Infrastructure metrics — any metric with < 60% coverage is reclassified as `contextual-only` (excluded from VD-A4 correlation analysis but permitted in context tables and deep-dives)
- **FX methodology check:** verify that FX_MATERIAL flags are populated where applicable; confirm period-end rates used for stock metrics and period-average rates for flow metrics

**Data gaps analysis:** After validating coverage, generate the data gaps report:

```bash
python3 -m src.analyzer.data_gaps --run-dir data/processed/{TICKER}/{DATE}/
```

This creates `3-analysis/data_gaps.json` with gap classifications (never_attempted/not_disclosed/derivable_not_derived/stale), backfill priorities, and high-impact targets. Display the summary to the user:
- Fill rate: N% (X/Y driver metric cells populated)
- Metrics above 60% threshold: N | Below: N | Zero coverage: N
- High-impact backfill targets: list metrics where N more cells would cross the 60% threshold
- Recommended action: backfill_critical | proceed_with_warning | sufficient_coverage

If recommended action is `backfill_critical` in auto mode, dispatch targeted backfill agents for the top 5 high-impact metrics before proceeding.

**Timeout detection:** Check whether all three `2-data/quantitative_tier*.json` files exist and are non-empty. If a tier file is missing or empty after the agent completes, re-dispatch that tier's data-collector with a simpler prompt focused only on the most critical metrics (valuation multiples + FRE margin + FEAUM CAGR).

**Interactive mode:** Display:
- Metric coverage summary (% populated by firm and by metric)
- Valuation multiple coverage (count of firms with all three multiples)
- Operational Feasibility metrics coverage and contextual-only reclassifications
- Action count per qualitative peer
- Ask: "Data gathering complete. Proceed to statistical analysis?"

**Auto mode:** Verify all criteria. If coverage < 60%, identify the lowest-coverage metrics and send targeted message to the relevant data-collector tier to fill the gaps. Reclassify sub-threshold operational metrics as contextual-only and log the reclassification. Proceed once criteria are met.

### Checkpoint CP-1: Fact Checker (Data Verification)

Before proceeding to Step 3, dispatch the claim-auditor agent to verify data collection outputs:

1. Read the merged quantitative data file (`2-data/quantitative_data.json`)
2. Read evidence files: `1-universe/source_catalog.json`, `2-data/quantitative_tier1.json`, `2-data/quantitative_tier2.json`, `2-data/quantitative_tier3.json`
3. Send to claim-auditor via SendMessage:
   - Checkpoint: CP-1
   - Stage audited: VD-A2
   - File audited: `2-data/quantitative_data.json`
   - Audit focus: invalid_premises, misleading_context
4. Wait for claim-auditor response
5. Parse the audit JSON:
   - If verdict is `PASSED` → save `audit_cp1_data.json` to the output directory, proceed to Step 3
   - If verdict is `BLOCKED`:
     a. Send the `blocked_claims` back to the relevant data-collector agent with revision instructions
     b. Wait for revised output
     c. Re-dispatch claim-auditor (max 2 retries)
     d. If still blocked after 2 retries → forcibly downgrade blocked claims to INFERRED, save audit file with caveats, proceed
6. Log: `[CLAIM-AUDIT] CP-1 PASSED (N/N claims)` or `[CLAIM-AUDIT] CP-1 BLOCKED (N ungrounded, N fabricated)`
7. **Consulting source enforcement:** If `consulting_context.json` exists, verify that no quantitative tier data cites PS-VD-9xx sources as the primary basis for any firm-specific metric value.

## Step 9: Step 3 of 5 — "Find What Drives Value" (Sequential)

**Step range check:** If `FROM_STEP > 3`, skip this step and load existing outputs from the prior run. If `TO_STEP < 3`, stop here after completing Step 2 and display the stop message.

Send all subsequent steps in this phase to metric-architect via SendMessage, waiting for each to complete before sending the next.

### Send to metric-architect: VD-A3 Standardization

> **Stage VD-A3 — Standardization.**
>
> Read `data/processed/{TICKER}/{DATE}/2-data/quantitative_data.json`.
>
> Normalize for cross-sectional comparability:
> 1. **Currency conversion and FX handling:**
>    - **Point-in-time metrics** (stock prices, balance-sheet items, AUM snapshots): convert to USD using **period-end exchange rates**.
>    - **Flow metrics** (revenue, expenses, earnings, cash flows): convert using **period-average exchange rates**.
>    - **Growth metrics**: calculate growth in the firm's **local reporting currency first**, then compute:
>      - `reported_USD_growth` — growth rate from USD-translated figures
>      - `local_currency_growth` — growth rate in reporting currency before translation
>      - `constant_currency_growth` — growth rate excluding FX effects (use firm-disclosed CC figures when available)
>      - `fx_delta = reported_USD_growth − local_currency_growth`
>    - **FX materiality flag (`FX_MATERIAL`):** flag when `abs(fx_delta)` exceeds the greater of 500 bps or 30% of absolute reported growth magnitude.
>    - **Document** for every conversion: FX rate, rate type (period-end / period-average), rate date, rate source, translation method (average-rate / fixed-base).
>    - **Cross-border per-share note:** when currency mismatch, share-count changes, and accounting-basis differences coexist, append a comparability caveat.
> 2. **Fiscal year alignment:** align to TTM or calendar year basis. Flag non-calendar fiscal year firms and specify exact period covered.
> 3. **FRE definition reconciliation:** FRE is non-GAAP and varies by firm. Document each firm's disclosed FRE definition and flag metrics where definitional heterogeneity is material.
> 4. **Coverage flagging:** mark any metric with fewer than 15 of ~25 firms reporting as "low coverage." Operational Feasibility metrics with < 60% coverage are classified as `contextual-only` — excluded from VD-A4 correlation analysis but may appear in context tables and deep-dives.
> 5. **Outlier flagging:** values exceeding 2 standard deviations from the cross-sectional mean are flagged for review.
>
> **Output:** `data/processed/{TICKER}/{DATE}/3-analysis/standardized_data.json`

### Send to metric-architect: VD-A4 Correlation Analysis

> **Stage VD-A4 — Correlation Analysis.**
>
> Read `data/processed/{TICKER}/{DATE}/3-analysis/standardized_data.json`.
>
> Compute Spearman rank correlation coefficients for each driver metric against each of the three valuation multiples (P/FRE, P/DE, EV/FEAUM), yielding ~45 pairwise correlations.
>
> **Minimum sample rule:** Only compute correlations where N >= 12 firms have non-null values for both the driver and the multiple. Correlations with N < 12 are classified as `insufficient_sample` and excluded from the ranking. Correlations with N < 8 are not reported.
>
> **Temporal stability:** When at least 12 firms have data for FY T and FY T-1, compute Spearman correlations on BOTH years and compare. Flag any driver whose sign reverses or whose |Δρ| > 0.25 as `temporally_unstable`. Temporally unstable drivers cannot be classified as `stable_value_driver`.
>
> Classification of results:
> - Stable value driver: satisfies `stable_v1_two_of_three` rule AND not `temporally_unstable`
> - Multiple-specific driver: ρ > 0.5 for exactly one multiple
> - Moderate signal: 0.3 ≤ ρ ≤ 0.5 for at least one multiple
> - Insufficient sample: N < 12 — excluded from ranking
> - Not a driver: ρ < 0.3 for all three multiples
>
> Following classification, test for multicollinearity among top-ranked stable drivers. Where two drivers exhibit ρ > 0.7 with each other, document the pair and flag the multicollinearity risk.
>
> For each correlation result record: correlation_id (COR-NNN), driver_metric_id, valuation_multiple, spearman_rho, classification, n_firms_included, notes.
>
> **Output:** `data/processed/{TICKER}/{DATE}/3-analysis/correlations.json`
>
> **Claim emission (REQUIRED):** Add a top-level `_claims` array to `correlations.json`. For each correlation entry, emit one claim:
>
> ```json
> {
>   "_claims": [
>     {
>       "id": "CLM-COR-{NNN}-01",
>       "parent_id": "COR-{NNN}",
>       "type": "statistical",
>       "evidence": ["{driver_metric_id}", "{valuation_multiple_id}"],
>       "confidence": "grounded",
>       "score": 3,
>       "layer": "3-analysis"
>     }
>   ]
> }
> ```
>
> Rules:
> - One CLM per COR entry
> - `evidence` contains the two MET-VD-* IDs being correlated
> - Score is always 3 (computation is deterministic from input metrics)
> - `confidence` is always "grounded" for statistical claims backed by computation

### Send to metric-architect: VD-A4b Statistical Documentation

> **Stage VD-A4b — Statistical Documentation and Explainability.**
>
> Read `data/processed/{TICKER}/{DATE}/3-analysis/correlations.json`.
>
> Produce a standalone methodology document. Required contents:
>
> 1. **Methods and justification:** Document choice of Spearman over Pearson (robustness to non-normality, outlier resistance, monotonic relationships). Document explicitly why multiple regression was not used (insufficient degrees of freedom with N≈25, multicollinearity, overfitting risk, endogeneity).
>
> 2. **Bootstrap confidence intervals:** 10,000 bootstrap resamples per coefficient (preferred over asymptotic Fisher-z for N < 30). Report 95% CIs. Flag CIs that include zero. Record `ci_method: bootstrap_10k` in metadata.
>
> 3. **Multiple comparisons correction:** Apply Bonferroni correction to ~45 hypothesis tests. Report corrected and uncorrected p-values.
>
> 4. **Confidence classification:**
>    - High confidence: p < 0.01 after Bonferroni correction
>    - Moderate confidence: p < 0.05 after correction
>    - Suggestive: p < 0.10 after correction
>    - Not significant: p >= 0.10 after correction
>
> 5. **Sensitivity analyses:**
>    - Leave-one-out: recompute each significant correlation excluding each firm in turn; flag findings driven by a single influential observation
>    - Temporal stability: compare correlations on FY T vs. FY T-1 vs. FY T-2 (where available); flag drivers with sign reversal or |Δρ| > 0.25 as `temporally_unstable`
>    - **Panel robustness (supplementary):** construct a firm × year panel using all available years. Compute Spearman correlations on the panel. Report total observations, N firms, N periods. Note: panel results are supplementary only (within-firm autocorrelation violates independence) — they do not override the cross-sectional primary analysis
>
> 6. **Mandatory disclaimers (reproduce verbatim):**
>    - Correlation does not imply causation.
>    - Survivorship bias: universe consists of currently listed firms only.
>    - Point-in-time limitation: conditions as of most recent data collection period.
>    - Small-N limitation: N≈25 limits statistical power; findings generate hypotheses, not definitive causal claims.
>    - Endogeneity: several drivers may be simultaneously caused by and causally related to valuation multiples.
>    - FRE definition heterogeneity: FRE is non-GAAP; firm-specific definitions vary; measurement error is present.
>
> **Output:** `data/processed/{TICKER}/{DATE}/3-analysis/statistical_methodology.md`
>
> **Additionally produce:** `data/processed/{TICKER}/{DATE}/3-analysis/statistics_metadata.json` conforming to the `schemas/vda/statistics_metadata.schema.json` schema. Include `n_effective`, `temporal_depth` (object with `target_range`, `actual_years`, `firms_with_multi_year`), `ci_method`, and `minimum_sample_rule` fields.

### Send to metric-architect: VD-A5 Value Driver Ranking

> **Stage VD-A5 — Value Driver Ranking.**
>
> Read `data/processed/{TICKER}/{DATE}/3-analysis/correlations.json`.
> Read `data/processed/{TICKER}/{DATE}/3-analysis/statistical_methodology.md`.
>
> Rank the top 5–6 stable drivers by average absolute Spearman coefficient across the three valuation multiples.
>
> For each top-ranked driver:
> - driver_id (DVR-NNN)
> - driver_name
> - avg_abs_rho (across three multiples)
> - confidence_class (from VD-A4b)
> - per-firm quartile position (Q1/Q2/Q3/Q4 for all firms in universe)
> - top_quartile_firms (list of firm_ids in Q1)
> - bottom_quartile_firms (list of firm_ids in Q4)
> - non_obvious_peers: firms in top quartile on 2+ stable drivers that were NOT in the original VD-B0 qualitative peer list — flag these for possible inclusion in Phase 2
>
> **Output:** `data/processed/{TICKER}/{DATE}/3-analysis/driver_ranking.json`
>
> **Claim emission (REQUIRED):** Add a top-level `_claims` array to `driver_ranking.json`. For each driver entry, emit one claim:
>
> ```json
> {
>   "_claims": [
>     {
>       "id": "CLM-DVR-{NNN}-01",
>       "parent_id": "DVR-{NNN}",
>       "type": "statistical",
>       "evidence": ["COR-{X}", "COR-{Y}", "COR-{Z}"],
>       "confidence": "grounded",
>       "score": 3,
>       "layer": "3-analysis"
>     }
>   ]
> }
> ```
>
> Rules:
> - One CLM per DVR entry
> - `evidence` lists ALL COR-* IDs that were used to classify this driver
> - For `stable_value_driver`: evidence includes the 2+ COR-* entries with |rho| >= 0.5
> - For `multiple_specific_driver`: evidence includes the single qualifying COR-*
> - Score is 3 for stable/multiple_specific (backed by correlation data), 2 for contextual

### Send to metric-architect: VD-C1 Convergence

After VD-A5 completes, spawn the convergence analyst:

Spawn with Agent tool (subagent_type: general-purpose, name: "convergence-analyst", model: "claude-opus-4-6", team_name: "vda-{TICKER_LOWER}"):

Instructions:
> You are the convergence-analyst for the Valuation Driver Analysis pipeline.
>
> **Your task:** Execute Stage VD-C1 — Convergence and Final Peer Set Selection.
>
> Read:
> - `data/processed/{TICKER}/{DATE}/3-analysis/driver_ranking.json` (Track A results)
> - `data/processed/{TICKER}/{DATE}/2-data/strategic_actions.json` (Track B results)
> - `data/processed/{TICKER}/{DATE}/1-universe/source_catalog.json` (source coverage)
>
> The target final peer set for Phase 2 deep-dives is **9–12 firms**.
>
> **Scoring criteria:**
> - Quantitative relevance: top quartile on 2+ stable value drivers from VD-A5
> - Qualitative relevance: strategic instructiveness of VD-B2 actions; diversity of approaches represented
> - Source coverage: minimum 2 sources per firm before deep-dive begins
>
> **Inclusion rules:**
> - Auto-include: any firm in the top quartile on 2+ stable drivers
> - Include as cautionary case: any firm in the bottom quartile with well-documented strategic actions
> - Flag for review: any non-obvious peer surfaced by VD-A5 not in the VD-B0 initial list
> - Exclude: firms with < 2 sources or < 60% metric coverage in standardized data
>
> For each included firm, document the inclusion rationale. For each excluded candidate, document the exclusion rationale.
>
> **Output:** `data/processed/{TICKER}/{DATE}/3-analysis/final_peer_set.json`
>
> Schema:
> ```json
> {
>   "final_set": [
>     {
>       "firm_id": "FIRM-NNN",
>       "firm_name": "...",
>       "ticker": "...",
>       "inclusion_rationale": "...",
>       "cautionary_case": false,
>       "non_obvious_peer": false,
>       "source_count": ...,
>       "metric_coverage_pct": ...
>     }
>   ],
>   "excluded_candidates": [...],
>   "total_final_set_size": ...,
>   "flagged_gaps": ["..."]
> }
> ```

### Quality Gate 3

After VD-C1 completes, check:

**Criteria:**
- Final peer set is 9–12 firms with documented rationale for each
- Non-obvious peers surfaced by Track A are resolved (included with rationale or explicitly excluded)
- All stable drivers pass the statistical documentation review in VD-A4b (no CI that includes zero without explicit flag)

**Interactive mode:** Display:
- Final peer set list with inclusion rationale
- Non-obvious peers flagged and their resolution
- Top 3 stable drivers with their confidence classification
- Ask: "Statistical analysis complete. Proceed to deep-dives?"

**Auto mode:** Verify all criteria. If final set < 9 firms, send message to convergence-analyst to relax inclusion criteria (lower the top-quartile threshold to Q2). If any flagged gaps remain unresolved, log them and proceed. Once criteria met, proceed automatically.

## Step 10: Step 4 of 5 — "Deep-Dive Peers" (Parallel)

**Step range check:** If `FROM_STEP > 4`, skip this step and load existing outputs from the prior run. If `TO_STEP < 4`, stop here after completing Step 3 and display the stop message.

**Pre-dispatch: Pre-slice context files for deep-dive agents**

```bash
python3 -m src.analyzer.context_slicer --run-dir data/processed/{TICKER}/{DATE}/ --only actions-final,profiles-final
```

This creates `strategic_actions_final.json` and `strategy_profiles_final.json` in `4-deep-dives/`, filtered to the final peer set (~50% reduction each).

Spawn two agents in parallel:

### Agent: platform-analyst

Spawn with Agent tool (subagent_type: general-purpose, name: "platform-analyst", model: "claude-opus-4-6", team_name: "vda-{TICKER_LOWER}"):

Instructions:
> You are the platform-analyst for the Valuation Driver Analysis pipeline.
>
> **Your task:** Execute Stage VD-D1 — Platform-Level Deep-Dives.
>
> Read `data/processed/{TICKER}/{DATE}/3-analysis/final_peer_set.json` for the list of 9–12 firms.
> Read `data/processed/{TICKER}/{DATE}/3-analysis/driver_ranking.json` for stable driver rankings.
> Read `data/processed/{TICKER}/{DATE}/4-deep-dives/strategy_profiles_final.json` and `data/processed/{TICKER}/{DATE}/4-deep-dives/strategic_actions_final.json` (pre-sliced to final peer set firms only).
>
> For each firm in the final set, produce a structured platform-level profile with six sections:
>
> 1. **Identity and scale** — current AUM, FEAUM, geography, asset class mix, public listing history, ownership structure
> 2. **Strategic agenda** — top 3–5 stated priorities sourced from most recent Investor Day or annual report (cite source IDs)
> 3. **Key actions (2–3 year horizon)** — full catalog from VD-B2, organized by action type, with source citations (ACT-VD-NNN)
> 4. **Performance on stable value drivers** — scores on top 5–6 drivers from VD-A5 with cross-sectional quartile position and brief context
> 5. **Value creation narrative** — analytical account of what makes this firm trade at its current premium or discount relative to peer group; articulate the causal theory connecting strategy to valuation
> 6. **Transferable insights with implementation pathways** — For each of the 3–5 insights:
>    - The insight itself (grounded in documented evidence)
>    - **How they did it**: specific implementation sequence — what came first, what enabled what, what prerequisites were needed
>    - **Timeline**: how long the transformation took from announcement to measurable impact
>    - **Enabling conditions**: what organizational, capital, or market conditions made this possible
>    - Do NOT reference {COMPANY}; keep insights self-contained but operationally detailed
> 7. **Technology as enabler of value drivers** — For each firm, map documented technology investments (from `strategic_actions_final.json` where `action_type` is `technology-operations` or `technology-investment`) to the firm's performance on ranked value drivers. Answer:
>    - Which technology investment preceded or coincided with improvement on which ranked driver? (e.g., "operational automation → FRE margin expansion", "digital distribution platform → FEAUM growth acceleration")
>    - Is the technology investment a plausible mechanism for the observed driver performance, or merely coincidental?
>    - What was the sequence: tech investment → operational change → metric improvement? Document the causal chain where evidence supports it; flag as `INFERRED` where the link is plausible but not directly documented.
>    - If a firm has `no_tech_action_found: true` in strategic_actions_final.json, note this explicitly — the absence of documented tech investment is itself informative for the analysis.
>    - Use hedged language for all causal claims: "appears to have contributed to", "coincided with", "may have enabled". Never assert direct causation.
>
> All profiles must be internally consistent. Transferable insights must be grounded in documented evidence from VD-B2, not inference.
>
> **Output:** `data/processed/{TICKER}/{DATE}/4-deep-dives/platform_profiles.json`

### Agent: vertical-analyst

Spawn with Agent tool (subagent_type: general-purpose, name: "vertical-analyst", model: "claude-opus-4-6", team_name: "vda-{TICKER_LOWER}"):

Instructions:
> You are the vertical-analyst for the Valuation Driver Analysis pipeline.
>
> **Your task:** Execute Stage VD-D2 — Asset Class Deep-Dives.
>
> Read `data/processed/{TICKER}/{DATE}/3-analysis/driver_ranking.json` for which stable drivers are most salient.
> Read `data/processed/{TICKER}/{DATE}/4-deep-dives/strategic_actions_final.json` for peer actions (pre-sliced to final peer set firms only).
> Read `docs/pax-peer-strategy-ontology.md` for the minimum business-model decomposition grid.
> Read `docs/pax-peer-assessment-framework.md` for business context.
> Read `data/processed/{TICKER}/{DATE}/2-data/consulting_context_slim.json` if it exists — use it as formal input for vertical and sub-strategy context. It may support claims about market structure, private credit growth, wealth distribution, consolidation, democratization, and operating-model requirements. Keep all peer-specific examples grounded in peer evidence.
>
> **CONSULTING RULE:** consulting_context_slim.json is market context only. Never use it as primary evidence for firm-specific metrics, actions, or causal claims. If consulting conflicts with peer evidence, peer evidence wins.
>
> Conduct deep-dives for 5 verticals with their reference firms:
>
> | Vertical | Best-in-Class Reference Firms | Key Questions |
> |---|---|---|
> | Credit | ARES, OWL, HLN | Direct lending vs. CLO vs. mezzanine; origination model; scale advantages; regulatory capital dynamics |
> | Private Equity | KKR, APO, CG, TPG | Mid-market vs. mega-cap; sector specialization vs. generalist; co-investment programs; GP-led secondaries |
> | Infrastructure | BAM, EQT | Core vs. value-added risk profile; energy transition; digital infrastructure; regulatory environments |
> | Real Estate | BX, BAM | PERE vs. core/core-plus; credit-oriented real estate; BREIT-style perpetual vehicles; retail investor access |
> | GP-Led Solutions / Secondaries | STEP, HLN, PGHN | Primary vs. secondaries vs. co-investment; portfolio construction role; fee model differences |
>
> **Strategy Sub-Type Segmentation:** Do NOT stop at broad verticals. Within each vertical, segment by:
> - **Strategy Sub-Type** — specific investment approach or product variant
> - **Thematic Focus** — sector or structural theme targeted
> - **Economic Model** — fee structure, margin profile, capital intensity
>
> Illustrative sub-types:
> - PE: mid-market operational turnaround, large-cap buyout, sector-specialist growth equity, secondaries-led PE, GP-led continuation vehicles
> - Credit: direct lending, asset-backed finance, infrastructure debt, opportunistic credit, insurance-oriented credit, CLO management
> - Real Estate: logistics platforms, residential niches, data centers, real estate credit, core/core-plus perpetual vehicles
> - Infrastructure: core/super-core, value-added, energy transition, digital infrastructure, transport/logistics
> - Solutions: secondaries, GP-leds, bespoke mandates, advisory-heavy allocation solutions, co-investment programs
>
> For each sub-type, document:
> - Operational value-creation levers (what the GP does beyond capital allocation)
> - Fee model and margin structure (how fees differ from the flagship)
> - Talent model (team composition, key-person dependencies, compensation)
> - Data / reporting / technology requirements
> - Scaling constraints (deployment capacity, market depth, deal-flow limits)
> - Transferability barriers (regulatory, capability, brand, track-record requirements)
>
> For each vertical, produce:
> - Profiles of best-in-class practitioners and basis for classification
> - Documentation of winning strategies and evidence of effectiveness, **segmented by strategy sub-type**
> - Vertical-specific metric drivers (which stable drivers from VD-A5 are most salient within this vertical)
> - Emerging trends and structural changes affecting the vertical
> - Sub-type-level transferability analysis (which sub-types are accessible to new entrants vs. requiring established track records)
>
> **Output:** `data/processed/{TICKER}/{DATE}/4-deep-dives/asset_class_analysis.json`

### Quality Gate 4

After both deep-dive agents complete, check:

**Criteria:**
- Platform deep-dives are internally consistent (transferable insights grounded in documented evidence from VD-B2, not inference)
- Asset class deep-dives cover all 5 verticals with at least 2 reference firms each
- Value creation narratives cite specific source IDs, not general claims
- **Operational prerequisite verification:** block any claimed operational prerequisite that lacks source support or is based only on low-trust evidence (job postings or vendor PRs as sole source). All operational prerequisites must carry `evidence_class` tags (directly_documented / corroborated / inferred)
- **Strategy sub-type coverage:** verify that verticals are segmented by strategy sub-type, not treated as monolithic categories

**Interactive mode:** Display:
- Firms covered in platform deep-dives
- Verticals covered in asset class deep-dives
- Strategy sub-types identified per vertical
- Operational prerequisites with evidence quality summary
- Sample transferable insight from the highest-ranked firm
- Ask: "Deep-dives complete. Proceed to playbook synthesis?"

**Auto mode:** Verify criteria. If a deep-dive is missing a firm from the final set, send message to platform-analyst to fill the gap. If operational prerequisites lack evidence tags, send revision message to strategy-extractor. Proceed once criteria met.

### Checkpoint CP-2: Fact Checker (Deep-Dive Verification)

Before proceeding to Step 5, dispatch the claim-auditor agent to verify deep-dive outputs. This is the CRITICAL checkpoint — all 4 audit dimensions are active.

1. Read deep-dive outputs: `4-deep-dives/platform_profiles.json`, `4-deep-dives/asset_class_analysis.json`
2. Read evidence files: `3-analysis/correlations.json`, `3-analysis/driver_ranking.json`, `4-deep-dives/strategic_actions_final.json`, `4-deep-dives/strategy_profiles_final.json`
3. Send to claim-auditor via SendMessage:
   - Checkpoint: CP-2
   - Stage audited: VD-D1, VD-D2
   - Files audited: `4-deep-dives/platform_profiles.json`, `4-deep-dives/asset_class_analysis.json`
   - Audit focus: ALL (invalid_premises, misleading_context, sycophantic_fabrication, confidence_miscalibration) + operational_prerequisite_evidence (block any prerequisite based solely on job postings or vendor PRs)
   - Audit focus: sycophantic_fabrication, confidence_miscalibration, consulting_source_enforcement (block firm-specific claims solely backed by PS-VD-9xx sources)
4. Wait for claim-auditor response
5. Parse the audit JSON:
   - If verdict is `PASSED` → save `audit_cp2_deep_dives.json`, proceed to Step 5
   - If verdict is `BLOCKED`:
     a. Send blocked_claims to platform-analyst or vertical-analyst (whichever produced the flagged claims)
     b. Wait for revised output
     c. Re-dispatch claim-auditor (max 2 retries)
     d. If still blocked → forcibly downgrade, save audit file, proceed
6. Log: `[CLAIM-AUDIT] CP-2 PASSED (N/N claims)` or `[CLAIM-AUDIT] CP-2 BLOCKED (N ungrounded, N fabricated)`

## Step 11: Step 5 of 5 — "Build the Playbook" (Sequential)

**Step range check:** If `FROM_STEP > 5`, skip this step (no agents to skip in this skill — this would mean Review only). If `TO_STEP < 5`, stop here after completing Step 4 and display the stop message.

**Pre-dispatch: Pre-slice context files for playbook agents**

```bash
python3 -m src.analyzer.context_slicer --run-dir data/processed/{TICKER}/{DATE}/ --only action-lookup,footnote-registry
```

This creates `action_source_lookup.json` (~5KB vs 123KB, 96% reduction) and `footnote_registry.json` (~15KB vs 62KB, 76% reduction) in `5-playbook/` for the report-builder.

### Agent: playbook-synthesizer

Spawn with Agent tool (subagent_type: general-purpose, name: "playbook-synthesizer", model: "claude-opus-4-6", team_name: "vda-{TICKER_LOWER}"):

Instructions:
> You are the playbook-synthesizer for the Valuation Driver Analysis pipeline.
>
> **Your tasks (sequential — complete in order):**
>
> **Task A — Stage VD-P1: Value Creation Principles**
>
> Read `data/processed/{TICKER}/{DATE}/3-analysis/driver_ranking.json`.
> Read `data/processed/{TICKER}/{DATE}/3-analysis/statistical_methodology.md`.
> Read `data/processed/{TICKER}/{DATE}/4-deep-dives/platform_profiles.json`.
> Read `data/processed/{TICKER}/{DATE}/2-data/consulting_context_slim.json` if it exists — use it to explain WHY a theme matters now and WHY the market is moving in that direction. Do NOT let consulting sources replace peer evidence when describing what worked at a given firm.
>
> **CONSULTING RULE:** consulting_context_slim.json is market context only. Never use it as primary evidence for firm-specific metrics, actions, or causal claims. If consulting conflicts with peer evidence, peer evidence wins.
>
> For each of the 5–6 stable value drivers:
> - Restate the statistical finding in plain language, accompanied by the full statistical documentation (rho, CI, Bonferroni-corrected p-value, confidence class)
> - Explain the underlying economic mechanism: why should this metric correlate with valuation in this industry?
> - Identify which firms illustrate the principle most clearly (from VD-D1 findings)
> - Note limitations and boundary conditions on the principle
>
> **Output A:** `data/processed/{TICKER}/{DATE}/5-playbook/value_principles.md`
>
> **Task B — Stage VD-P2: Platform Strategic Menu**
>
> Read `data/processed/{TICKER}/{DATE}/4-deep-dives/platform_profiles.json`.
>
> Organize findings into a strategic menu at the platform level. Organize by value driver (not by firm). For each stable value driver:
> - Enumerate the proven strategic plays that peers have executed to improve performance on that driver
> - **Every PLAY-NNN must include ALL mandatory fields:**
>   - `What_Was_Done` — concrete description: who, what, when, at what scale
>   - `Observed_Metric_Impact` — quantitative or directional metric movement with time horizon and source citation
>   - `Prerequisites` — strategic and market prerequisites in place before execution
>   - `Operational_And_Tech_Prerequisites` — systems integration, data/reporting stack, compliance infrastructure, fund admin changes, hiring required (sourced from VD-B2 operational prerequisites)
>   - `Execution_Burden` — time horizon, capital required, organizational disruption, opportunity cost
>   - `Failure_Modes_And_Margin_Destroyers` — what could go wrong; specific mechanisms by which this play could destroy rather than create value
>   - `Transferability_Constraints` — scale, geography, regulatory, capability, or track-record barriers
>   - `Evidence_Strength` — `high` (multi-source, independent corroboration), `moderate` (single independent source or corroborated company disclosure), `low` (company-produced only or inferred)
>   - `source_citations` — array of PS-VD-NNN IDs grounding this play's evidence (resolved from action_citations' source_citation fields in `strategic_actions.json`)
>
> The menu presents evidence and does not prioritize or recommend specific plays. Cite ACT-VD-NNN and PS-VD-NNN identifiers throughout.
>
> **Additionally, for each stable value driver, include an "Anti-patterns" section:**
> - Enumerate strategic actions that peers executed which did NOT improve performance on this driver, or actively destroyed value
> - For each anti-pattern (ANTI-NNN), include the same mandatory fields as PLAY-NNN
> - For every anti-pattern, identify the **specific operational mechanism** of value destruction — not just that margin compression occurred, but why:
>   - Duplicated overhead from unintegrated acquisitions
>   - Fragmented country/entity platforms requiring parallel back-office infrastructure
>   - Reporting/control/reconciliation failures post-integration
>   - Insufficient systems integration leading to manual workarounds
>   - Headcount growth outrunning revenue/AUM growth
>   - Fee-rate dilution from channel or product mix shift
> - Frame as "Don'ts" — lessons from what did not work, not just what did
> - Cite ACT-VD-NNN and PS-VD-NNN identifiers throughout
>
> **Emerging Themes (mandatory section):**
> After the driver-organized plays and anti-patterns, include an "Emerging Themes" section for strategic actions that appear in `strategic_actions.json` but have no corresponding ranked driver (because the underlying metric had insufficient coverage for correlation analysis). These are well-documented peer initiatives that the statistical engine cannot yet validate but that governance audiences should monitor.
>
> For each emerging theme:
> - `theme_id`: THEME-NNN
> - `theme_name`: descriptive label (e.g., "Proprietary Technology Platforms", "AI-Integrated Investment Processes")
> - `actions`: array of ACT-VD-NNN IDs from strategic_actions.json that support this theme
> - `firms_involved`: which peers are executing on this theme
> - `What_Is_Observed`: factual description of what peers are doing — no causal claims
> - `Why_It_May_Matter`: economic mechanism by which this could affect valuation, stated as hypothesis
> - `Coverage_Gap`: which metric would need better coverage to test this statistically (e.g., "Technology_Platform_Maturity currently has N/24 firms — below 60% threshold")
> - `Evidence_Strength`: `observational` (multiple peers pursuing similar initiatives) or `anecdotal` (isolated examples)
> - `source_citations`: array of PS-VD-NNN IDs
>
> **Rules for Emerging Themes:**
> - NEVER claim causal impact on valuation — these are observed patterns, not validated drivers
> - Use hedged language throughout: "appears to", "peers are increasingly", "may contribute to"
> - Minimum 1 emerging theme required (technology/AI initiatives are nearly always present in alt-asset management)
> - Maximum 5 emerging themes to maintain focus
> - Each theme must cite at least 2 distinct peer actions from strategic_actions.json
>
> **Entries missing any mandatory field will be blocked at CP-3.**
>
> **Output B:** `data/processed/{TICKER}/{DATE}/5-playbook/platform_playbook.json`
>
> **Claim emission (REQUIRED):** Add a top-level `_claims` array to `platform_playbook.json`. For each PLAY-NNN and ANTI-NNN, emit 1-3 claims representing the key assertions:
>
> ```json
> {
>   "_claims": [
>     {
>       "id": "CLM-PLAY-{NNN}-01",
>       "parent_id": "PLAY-{NNN}",
>       "type": "factual",
>       "evidence": ["PS-VD-{X}", "ACT-VD-{Y}"],
>       "confidence": "grounded",
>       "score": 3,
>       "layer": "5-playbook"
>     },
>     {
>       "id": "CLM-PLAY-{NNN}-02",
>       "parent_id": "PLAY-{NNN}",
>       "type": "causal",
>       "evidence": ["CLM-PLAY-{NNN}-01", "CLM-DVR-{D}-01"],
>       "confidence": "partial",
>       "score": 2,
>       "layer": "5-playbook"
>     }
>   ]
> }
> ```
>
> Claim decomposition per play:
> 1. **Factual claim** (what the peer did): type=factual, evidence=[PS-VD-*, ACT-VD-*], score=3
> 2. **Causal claim** (why it worked — metric impact): type=causal, evidence=[factual CLM + DVR CLM], score=2 max
> 3. **Prescriptive claim** (generalizability — only if Transferability_Constraints allows): type=prescriptive, evidence=[causal CLM], score=2 max
>
> Anti-patterns (ANTI-NNN) follow the same structure with CLM-ANTI-{NNN}-{seq} IDs.
>
> Causal and prescriptive claims MUST use score <= 2. The claim_indexer enforces this ceiling.
>
> **Task C — Stage VD-P3: Asset Class Playbooks**
>
> Read `data/processed/{TICKER}/{DATE}/4-deep-dives/asset_class_analysis.json`.
>
> Produce a parallel strategic menu at the vertical level, organized by value driver within each vertical. Same structure as VD-P2 — every PLAY-NNN and ANTI-NNN must include ALL mandatory fields (What_Was_Done, Observed_Metric_Impact, Prerequisites, Operational_And_Tech_Prerequisites, Execution_Burden, Failure_Modes_And_Margin_Destroyers, Transferability_Constraints, Evidence_Strength, source_citations). Evidence citations to specific peer actions (ACT-VD-NNN). Cover all 5 verticals: Credit, Private Equity, Infrastructure, Real Estate, GP-Led Solutions/Secondaries.
>
> Within each vertical, organize plays by **strategy sub-type** (from VD-D2) where applicable, so readers can identify plays relevant to their specific sub-type.
>
> **Entries missing any mandatory field will be blocked at CP-3.**
>
> **Emerging Themes (per vertical):**
> Same structure as VD-P2 Emerging Themes, but scoped to each vertical. Include technology/data themes that are specific to the asset class (e.g., AI-driven credit underwriting in Credit, digital asset origination in PE, smart infrastructure monitoring in Infrastructure). At least 1 emerging theme per vertical where evidence exists.
>
> **Output C:** `data/processed/{TICKER}/{DATE}/5-playbook/asset_class_playbooks.json`

Wait for playbook-synthesizer to complete.

### Checkpoint CP-3: Fact Checker (Playbook Verification)

After playbook-synthesizer produces outputs and BEFORE report-builder generates the final HTML:

1. Read playbook outputs: `5-playbook/value_principles.md`, `5-playbook/platform_playbook.json`, `5-playbook/asset_class_playbooks.json`
2. Read evidence files: `4-deep-dives/platform_profiles.json`, `4-deep-dives/asset_class_analysis.json`, `3-analysis/driver_ranking.json`
3. Send to claim-auditor via SendMessage:
   - Checkpoint: CP-3
   - Stage audited: VD-P1, VD-P2, VD-P3
   - Files audited: `5-playbook/platform_playbook.json`, `5-playbook/asset_class_playbooks.json`
   - Audit focus: sycophantic_fabrication, confidence_miscalibration, mandatory_field_completeness (block any PLAY-NNN or ANTI-NNN lacking Operational_And_Tech_Prerequisites, Failure_Modes_And_Margin_Destroyers, or Evidence_Strength; block any THEME-NNN lacking theme_name, actions, firms_involved, What_Is_Observed, Why_It_May_Matter, Coverage_Gap, Evidence_Strength, or source_citations; block any THEME-NNN that asserts causal impact on valuation instead of using hedged language)
4. Wait for claim-auditor response
5. Parse the audit JSON:
   - If verdict is `PASSED` → save `audit_cp3_playbook.json`, proceed to report-builder
   - If verdict is `BLOCKED`:
     a. Send blocked_claims to playbook-synthesizer with revision instructions (include which mandatory fields are missing)
     b. Wait for revised output
     c. Re-dispatch claim-auditor (max 2 retries)
     d. If still blocked → forcibly downgrade, save audit file, proceed
6. Pass any INFERRED claims list to report-builder so it uses hedged language for those specific claims
7. Log: `[CLAIM-AUDIT] CP-3 PASSED (N/N claims)` or `[CLAIM-AUDIT] CP-3 BLOCKED (N ungrounded, N fabricated, N incomplete_fields)`
8. **Consulting source enforcement:** Verify that no PLAY-NNN or recommendation uses PS-VD-9xx as the sole evidence for a firm-specific claim. PS-VD-9xx may support "why this matters" context but not "what worked at firm X."

### Ghost Report Skeleton

Before spawning report-builder and target-lens, produce a narrative skeleton:

1. Read all playbook outputs: `5-playbook/value_principles.md`, `5-playbook/platform_playbook.json`, `5-playbook/asset_class_playbooks.json`
2. Read `3-analysis/driver_ranking.json` for headline findings
3. Write `5-playbook/ghost_report_skeleton.md` — a sequence of ~10 **action titles** (one per major report section) that form a coherent executive narrative arc when read top-to-bottom

Rules for action titles:
- Each title states a **conclusion or finding**, not a topic label
- The sequence reads as a coherent executive narrative top-to-bottom
- Titles follow the same hedging rules as body text (no causal language for moderate-signal correlations)
- Examples of strong titles:
  - "Scale drives valuation premiums more than any other factor, but only when converted into investable earnings quality"
  - "A small number of firms convert scale into premium through structurally advantaged business models"
  - "The most attractive near-term plays concentrate on replicable platform advantages, not prestige moves"
- Examples of weak titles (DO NOT use):
  - "Industry Value Drivers"
  - "Peer Profiles"
  - "Strategic Implications"
- Reference: `docs/sigma-final-report-guide.md` (Ghost Report section)

Output: `data/processed/{TICKER}/{DATE}/5-playbook/ghost_report_skeleton.md`

Then spawn the report-builder and target-lens agents **in parallel** (they share the same inputs and have no dependency on each other):

### Agent: report-builder

Spawn with Agent tool (subagent_type: general-purpose, name: "report-builder", model: "claude-opus-4-6", team_name: "vda-{TICKER_LOWER}"):

Instructions:
> You are the report-builder for the Valuation Driver Analysis pipeline.
>
> **Your task:** Execute Stage VD-P4 — Final Navigable HTML Report.
>
> Read all pipeline outputs in `data/processed/{TICKER}/{DATE}/`:
> - `5-playbook/value_principles.md`
> - `5-playbook/platform_playbook.json`
> - `5-playbook/asset_class_playbooks.json`
> - `5-playbook/ghost_report_skeleton.md` — use as H2 section headers
> - `4-deep-dives/platform_profiles.json`
> - `4-deep-dives/asset_class_analysis.json`
> - `3-analysis/statistical_methodology.md`
> - `3-analysis/driver_ranking.json`
> - `5-playbook/footnote_registry.json` — pre-built compact registry (source_id, firm, title, document_type, bias_tag only)
> - `5-playbook/action_source_lookup.json` — pre-built ACT-VD → PS-VD lookup (action_id, firm_id, source_citation only)
> - `2-data/consulting_context_slim.json` — for Industry Context section (if it exists, top_snippets removed)
>
> **CONSULTING RULE:** Add a short "Industry Context" section using consulting_context_slim.json. Keep it clearly labeled and separate from peer findings. Consulting sources (PS-VD-9xx) may only support market-level claims. Any firm-specific claim must cite peer PS-VD sources, not consulting sources.
>
> Also read the writing reference: `docs/sigma-final-report-guide.md`
>
> Produce a single self-contained HTML file with two addressable layers:
>
> **Layer 1 (Platform):**
> - Executive summary
> - Methodology brief (2-3 paragraphs: analytical framework, universe size, primary method, link to Statistical Appendix). Move all statistical parameters, confidence taxonomy, driver classification rules, and disclaimers to the Statistical Appendix at end of document.
> - Industry value driver findings (stable drivers with full statistical documentation)
> - Firm-level strategies and actions (platform deep-dives)
> - Platform strategic menu (organized by driver)
> - Sources & References (numbered footnote list before Appendix)
>
> **Layer 2 (Asset Class — 5 vertical sections, each self-contained):**
> - Credit, Private Equity, Infrastructure, Real Estate, GP-Led Solutions/Secondaries
> - Vertical-specific metric drivers
> - Vertical strategic menu
>
> **Governance-ready framing:**
> - If `data/processed/{TICKER}/{DATE}/5-playbook/target_company_lens.json` exists, incorporate the Strategic Guidance section as a dedicated chapter after the Executive Summary
> - Structure: "Strategic Implications for {COMPANY}" → PHL/Board Guidance → Management Priorities → Per-BU Recommendations
> - Include an "Anti-patterns & Cautionary Lessons" section after the Platform Strategic Menu
> - Include an "Emerging Themes" section after Anti-patterns — render THEME-NNN entries from `platform_playbook.json` and per-vertical emerging themes from `asset_class_playbooks.json`. Frame as "Themes to Monitor" with explicit disclaimers that these lack statistical validation. Use collapsible detail panels for each theme.
>
> **Style matching:**
> - If `data/processed/{TICKER}/{DATE}/style_guide.json` exists, adapt the report's tone, terminology, and structure to match the style guide while preserving all analytical rigor and mandatory disclaimers
>
> **Footnote generation system:**
> 1. Build a footnote registry: assign each PS-VD-NNN in `footnote_registry.json` a sequential number (1, 2, 3...)
> 2. Replace inline bare source IDs with superscript footnotes: `<sup class="fn"><a href="#fn-N">N</a></sup>`
> 3. Resolve ACT-VD-NNN → source_citation → PS-VD-NNN for play citations (using `action_source_lookup.json`)
> 4. Render a "Sources & References" ordered list section before the Appendix:
>    - Format: `[N] Title (Date). Bias: [tag]. URL`
>    - Each footnote anchored with `id="fn-N"` for navigation
>
> **Claim evidence layer (REQUIRED if claim_index.json exists):**
>
> 1. Read `claim_index.json` from the run root directory.
> 2. Embed it as `<script id="claim-data" type="application/json">` in the HTML `<head>`.
> 3. For each key assertion in the report text that corresponds to a CLM-* in the index, wrap it:
>    ```html
>    <span class="claim" data-claim="CLM-DVR-010-01">assertion text here</span>
>    ```
> 4. Add this CSS to the report stylesheet:
>    ```css
>    .claim { cursor: pointer; position: relative; }
>    .claim[data-score="2"] { text-decoration: underline; text-decoration-color: #d97706; text-underline-offset: 3px; }
>    .claim[data-score="1"] { text-decoration: underline; text-decoration-color: #d97706; text-underline-offset: 3px; }
>    .claim[data-score="1"]::after { content: " ⚠"; font-size: 0.7em; color: #d97706; }
>    .claim-tooltip { position: fixed; right: 20px; top: 80px; width: 360px; max-height: 80vh; overflow-y: auto; background: #1a1a2e; color: #e0e0e0; padding: 16px; border-radius: 8px; font-family: 'IBM Plex Mono', monospace; font-size: 12px; box-shadow: 0 4px 24px rgba(0,0,0,0.3); z-index: 1000; display: none; }
>    .claim-tooltip.visible { display: block; }
>    ```
> 5. Add this JavaScript at the end of `<body>`:
>    ```javascript
>    (function() {
>      const data = JSON.parse(document.getElementById('claim-data').textContent);
>      const tooltip = document.createElement('div');
>      tooltip.className = 'claim-tooltip';
>      document.body.appendChild(tooltip);
>
>      function renderChain(claimId, depth) {
>        const claim = data.claims[claimId];
>        if (!claim) return `<div style="padding-left:${depth*16}px">${claimId} (not found)</div>`;
>        let html = `<div style="padding-left:${depth*16}px">`;
>        html += `<strong>${claimId}</strong> · score ${claim.score}/3 · ${claim.type}<br>`;
>        (claim.evidence || []).forEach(ev => {
>          if (ev.startsWith('CLM-')) { html += renderChain(ev, depth+1); }
>          else { html += `<div style="padding-left:${(depth+1)*16}px; color:#90cdf4">↳ ${ev}</div>`; }
>        });
>        html += '</div>';
>        return html;
>      }
>
>      document.querySelectorAll('.claim').forEach(el => {
>        const cid = el.dataset.claim;
>        const claim = data.claims[cid];
>        if (claim) el.dataset.score = claim.score;
>        el.addEventListener('click', () => {
>          tooltip.innerHTML = renderChain(cid, 0);
>          tooltip.classList.toggle('visible');
>        });
>      });
>
>      document.addEventListener('click', e => {
>        if (!e.target.closest('.claim') && !e.target.closest('.claim-tooltip')) {
>          tooltip.classList.remove('visible');
>        }
>      });
>    })();
>    ```
>
> **Claim annotation guidelines:**
> - Annotate ALL statistical assertions (rho values, N counts, driver classifications)
> - Annotate ALL causal claims (X led to Y, X improved Z)
> - Annotate ALL prescriptive/comparative claims in the target company lens section
> - Do NOT annotate: section headings, methodology descriptions, general definitions
>
> **Writing principles (mandatory — reference: docs/sigma-final-report-guide.md):**
> - **Pyramid Principle:** Lead every section with the answer/conclusion, then support with evidence. The reader should understand the "so what" before seeing the proof.
> - **Action titles:** Use the action titles from `ghost_report_skeleton.md` as H2 headers. Each title states a conclusion, not a topic label.
> - **Bumper statements:** End major sections (Executive Summary, Driver Findings, Strategic Implications, Anti-patterns) with "Therefore: [implication for {COMPANY}]"
> - **Evidence → pattern → implication sequence:** Never skip directly to recommendation. Show the data, identify the pattern, then state the implication.
> - **Plays as observations:** Describe plays as "observed mechanisms" / "peer-demonstrated patterns", never as "recommendations" or "things to do"
> - **Methodology demotion:** Keep inline methodology to 2-3 paragraphs (framework, universe, method). All statistical parameters, confidence taxonomy, classification rules, sensitivity protocols, and disclaimers go in the Statistical Appendix at end of document.
>
> **Technical requirements:**
> - Sidebar navigation linking to all major sections
> - Collapsible sections for supporting evidence and data tables
> - Sortable data tables for cross-firm comparisons
> - Statistical appendix with correlation coefficients, confidence intervals, and corrected p-values
> - Mandatory disclaimers section (verbatim from VD-A4b)
> - Clean professional styling: DM Sans body font, IBM Plex Mono for data, light theme with #0068ff blue accent and white/gray surfaces, company name + date in header
> - "Anti-patterns & Cautionary Lessons" section with evidence citations
> - "Strategic Implications for {COMPANY}" chapter (if target lens available)
> - Style adaptation from style_guide.json (if available)
>
> **Consumer entry points:**
> - C-suite / IR / Corporate Strategy: Executive summary → Platform strategic menu
> - Credit BU: Credit vertical section
> - Private Equity BU: PE vertical section
> - Infrastructure BU: Infrastructure vertical section
> - Real Estate BU: Real Estate vertical section
> - GP-Led Solutions BU: Solutions/Secondaries vertical section
>
> **Output:** `data/processed/{TICKER}/{DATE}/5-playbook/final_report.html`

### Agent: target-lens

Spawn with Agent tool (subagent_type: general-purpose, name: "target-lens", model: "claude-opus-4-6", team_name: "vda-{TICKER_LOWER}"):

Instructions:
> You are the target-lens agent for the Valuation Driver Analysis pipeline.
>
> **Company:** {COMPANY} ({EXCHANGE}: {TICKER})
> **Sector:** {SECTOR}
> **Business Segments:** {SEGMENTS}
>
> **Your task:** Execute Stage VD-P5 — Target Company Strategic Lens.
>
> Read:
> - `data/processed/{TICKER}/{DATE}/company_context.json`
> - `data/processed/{TICKER}/{DATE}/5-playbook/platform_playbook.json`
> - `data/processed/{TICKER}/{DATE}/5-playbook/asset_class_playbooks.json`
> - `data/processed/{TICKER}/{DATE}/4-deep-dives/platform_profiles.json`
> - `data/processed/{TICKER}/{DATE}/3-analysis/driver_ranking.json`
> - `data/processed/{TICKER}/{DATE}/2-data/consulting_context_slim.json` (if it exists) — for market timing and structural relevance
>
> **CONSULTING RULE:** Use consulting_context_slim.json ONLY to strengthen `why_this_matters_for_pax`, market timing, and structural relevance. Do NOT use consulting evidence as the sole basis for a recommendation, implementation pathway, or claim that a peer has already validated a move. If consulting conflicts with peer evidence, peer evidence wins.
>
> For each PLAY-NNN in the platform and asset class playbooks, assess relevance to {COMPANY}.
>
> **Core posture: Extract transferable PRINCIPLES from peer evidence. Do NOT prescribe specific actions.**
>
> **Language rules (mandatory):**
> - NEVER use: "{COMPANY} should...", "{COMPANY} must...", imperative voice, prescriptive language
> - USE: "The peer evidence suggests...", "Firms that achieved [outcome] typically...", "An area worth exploring is...", "The data is consistent with..."
> - Plays are "observed mechanisms" — not "recommended actions"
> - Implementation pathways describe "what peers did" — not "what {COMPANY} should do"
> - Board guidance frames "principles the evidence supports" — not "decisions to make"
>
> **Classification:**
> - `directly_applicable` — {COMPANY} operates in the same geography/asset class AND has the prerequisites
> - `requires_adaptation` — relevant principle but execution path differs due to {COMPANY}'s scale, geography, or asset mix
> - `not_applicable` — geographic, regulatory, or structural mismatch makes this play irrelevant
>
> For each play, produce:
> - `play_id`: PLAY-NNN
> - `applicability`: directly_applicable | requires_adaptation | not_applicable
> - `rationale`: why this classification
> - `adaptation_notes`: if requires_adaptation, what would need to change
> - `priority`: high | medium | low (based on potential valuation impact for {COMPANY})
> - `implementation_pathway`: what peers did, in what sequence, with what prerequisites (descriptive, not prescriptive)
> - `transferability_score`: 1-5 (how transferable is this play to {COMPANY}'s context)
> - `adaptation_distance`: low | medium | high (how much adaptation would be needed)
> - `copycat_risk`: what could go wrong if copied without the peer's prerequisites, scale, or context
> - `principle_extracted`: the general principle this play illustrates (not the specific action)
>
> **Additionally, produce a "Strategic Guidance" section structured for governance cascading:**
>
> **For PHL/Board level** (principles the peer evidence supports):
> - Top 5 principles the peer evidence supports as value-creating for firms in {COMPANY}'s position
> - For each principle: evidence anchor, peer examples, boundary conditions
> - Framed as "The evidence suggests that..." not "The board should..."
>
> **For CEO/Management Committee** (areas the evidence suggests are worth exploring):
> - Areas the evidence suggests are worth exploring, mapped to value drivers
> - For each area: what peers did, what the evidence shows about outcomes, what prerequisites matter
> - Framed as exploration, not as priority initiatives
>
> **Per Business Unit** (patterns observed in each asset class):
> - For each of {COMPANY}'s business segments: top 3 relevant peer-demonstrated patterns
> - What peer evidence exists in this asset class
> - Observed mechanisms and their prerequisites — framed as "patterns observed" not "launch this by Q3"
>
> **Output:** `data/processed/{TICKER}/{DATE}/5-playbook/target_company_lens.json`
>
> **Claim emission (REQUIRED):** Add a top-level `_claims` array to `target_company_lens.json`. For each play assessment, emit one claim:
>
> ```json
> {
>   "_claims": [
>     {
>       "id": "CLM-TL-{NNN}-01",
>       "parent_id": "PLAY-{NNN}",
>       "type": "comparative",
>       "evidence": ["PS-VD-{target_co_source}", "CLM-PLAY-{NNN}-01"],
>       "confidence": "partial",
>       "score": 2,
>       "layer": "5-playbook"
>     }
>   ]
> }
> ```
>
> Rules:
> - One CLM per play assessment
> - `evidence` includes (a) source for the target company data point and (b) the corresponding play's factual claim
> - Type is `comparative` (comparing peer play to target company context)
> - Score is max 2 (analogy-based, not direct evidence). Use score 1 if applicability is "not_applicable"
> - Language reminder: "suggests", "appears to", "data is consistent with" — never imperative

### Quality Gate 5 (always shown, regardless of mode)

Display final report review to user:
- Top 3 stable value drivers with their ρ values and confidence class
- Firm count in final peer set
- Asset classes covered
- Any flagged statistical limitations from VD-A4b
- HTML report path

Ask: "Final report generated. Are the findings acceptable, or do any sections need revision?"

If the user requests revision, identify which agent produced the relevant section and send a targeted revision message.

## Architecture Safeguards

These safeguards apply to ALL agent dispatches above:

### Timeout Detection
The orchestrator checks for output files at 5-minute intervals after agent dispatch. If an agent has produced no output file after 15 minutes:
1. Send a status check message to the agent
2. If no response after 5 more minutes, kill and re-dispatch with a simplified prompt (fewer firms, narrower scope)
3. Log the timeout in `data/processed/{TICKER}/{DATE}/pipeline_log.md`

### Progressive Prompts
Start agents with focused, concise prompts. Only add complexity if a quality gate fails:
- **First attempt:** Core instructions only
- **On quality gate failure:** Re-dispatch with specific feedback about what failed and additional guidance
- **Never:** Add all possible edge cases to the initial prompt

### Source-Aware Priority
Agents that receive supplemental data (from the `--sources` flag, converted by marker-pdf):
- Check `data/raw/{TICKER}/{DATE}/supplemental/manifest.json` FIRST
- Use supplemental data as the primary source for any topic it covers
- Fall back to web search only for topics not covered by supplemental data
- In source citations, supplemental sources are marked with `[SUPP]` prefix

### Statistical Governance Consistency
The methodology document, VD-A4b statistical documentation, and the final report must use the SAME statistical rulebook throughout. No downstream output may silently switch methods. Specifically:
- Same multiple-testing correction method (Bonferroni or effective-independent-tests variant)
- Same confidence taxonomy thresholds (High / Moderate / Suggestive / Not significant)
- Same driver classification rules (Stable / Multiple-specific / Moderate signal / Not a driver)
- Same sensitivity-check definitions (leave-one-out, temporal stability, panel robustness)
- Same minimum sample rule (N >= 12 for formal ranking, N < 8 not reported)
- Same N_effective across all statistical outputs

Low-coverage operational metrics (< 60% coverage) from the Operational Feasibility category may appear in context tables and deep-dives but must be labeled `contextual-only` and never cited as evidence of driver status.

### Statistical Methodology Improvements (from peer review)
The Statistical Analyst agent (VD-A4/A4b) must additionally:
1. **Run all correlations on a consistent sub-sample** of firms for which all three valuation multiples are available. Present supplementary results for the full sample separately.
2. **Flag metrics with N<10** as "insufficient data for evaluation" rather than classifying them as "not a driver."
3. **Compute partial correlations** for the top drivers, controlling for scale (mgmt_fee_rev), to test for confounded signals.
4. **Use 10,000-resample bootstrap CIs** (`bootstrap_10k`). If Fisher z is used as a substitute, document the rationale explicitly and record `ci_method: fisher_z_with_disclosure`.
5. **Execute temporal stability check** comparing FY T vs FY T-1 vs FY T-2 (where available); flag drivers with sign reversal or |Δρ| > 0.25 as `temporally_unstable`.
6. **Estimate effective independent tests** for multiple comparison correction (accounting for collinear pairs) rather than applying Bonferroni over all raw tests.

### Data Provenance Requirements (from peer review)
The Data Collector agents must:
1. **Record market cap reference date** per firm (not just the value).
2. **Document source and methodology** for computed metrics (organic growth, asset class HHI).
3. **Flag firms with non-calendar fiscal years** and specify the exact period covered.

### Iterative Run Support

When `--base-run` is provided:
1. Before data collection, generate the delta spec (see data-collector pre-dispatch above). The delta spec ensures agents collect ONLY complementary data — existing data is carried forward, confirmed non-disclosures are skipped.
2. Data-collector agents read `2-data/delta_spec.json` and follow its `collect.tierN.assignments` — they do NOT re-collect carry-forward data.
3. The convergence analyst explicitly compares the new peer set against the previous run's peer set and documents changes.
4. The report-builder includes a "Changes from Previous Analysis" appendix if base_run outputs exist.
5. Quality gates compare coverage metrics against the base run — new run should not regress on coverage.
6. After QG2, the data gaps report shows improvement: compare `fill_rate_pct` and `metrics_above_threshold` against the base run's `data_gaps.json`.

## Step 12: Cleanup and Report

Display final summary:
- Company analyzed: {COMPANY} ({TICKER})
- Sector: {SECTOR}
- Universe size: N firms
- Final peer set: M firms
- Top stable value driver: [driver name] (ρ = X.XX across all three multiples)
- Report path: `data/processed/{TICKER}/{DATE}/5-playbook/final_report.html`

Clean up: `TeamDelete → team_name: "vda-{TICKER_LOWER}"`

Offer to commit:
```
git add data/processed/{TICKER}/{DATE}/ data/raw/{TICKER}/{DATE}/
git commit -m "feat: valuation driver analysis for {COMPANY} ({TICKER})"
```
