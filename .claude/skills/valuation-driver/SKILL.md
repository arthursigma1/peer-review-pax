---
name: valuation-driver
description: Run the full Valuation Driver Analysis pipeline for any public company. Orchestrates 14 specialized agents across 5 steps to identify what drives valuation multiples and produce a strategic playbook. Usage: /valuation-driver TICKER [--auto] [--ui] [--sources /path/to/dir] [--base-run YYYY-MM-DD] [--style-ref /path/to/doc]
---

# Valuation Driver Analysis

Identify which operational and financial metrics drive valuation multiples across an industry peer universe, then synthesize a peer-derived strategic playbook.

## Usage

```
/valuation-driver TICKER                          # interactive CLI (pauses at quality gates)
/valuation-driver TICKER --auto                   # automatic CLI (gates validated by lead agent)
/valuation-driver TICKER --ui                     # launch Tauri desktop dashboard
/valuation-driver TICKER --sources /path/to/dir   # with supplemental proprietary data
/valuation-driver TICKER --auto --sources /path   # automatic + supplemental data
/valuation-driver TICKER --base-run 2026-03-06      # iterative: improve upon previous run
/valuation-driver TICKER --style-ref /path/to/doc   # match writing style of reference doc
```

## Step 0: Parse Arguments

Extract from the user's input:
- `TICKER` (required) — e.g., `PAX`, `BX`, `KKR`
- `--ui` flag (optional) — if present, launch the Tauri desktop dashboard instead of running in CLI mode
- `--auto` flag (optional) — if present, quality gates are validated automatically; otherwise interactive
- `--sources /path/to/dir` (optional) — path to a directory containing supplemental data files (PDFs, DOCX, PPTX)
- `--base-run YYYY-MM-DD` (optional) — date of a previous run to use as baseline. Agents receive previous outputs as context and are instructed to improve upon them.
- `--style-ref /path/to/doc` (optional) — path to a reference document whose writing style the report should match.

If no TICKER is provided, ask the user for one.

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
  "nuances": "Lead with evidence before conclusions. Every claim cites a source ID. Use Oxford commas. Qualify correlation-based findings with statistical confidence. Avoid marketing language — prefer 'the data suggest' over 'clearly demonstrates'. Section headers are descriptive, not clever. Footnotes for methodological caveats."
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

## Step 7: Step 1 of 5 — "Map the Industry" (Parallel)

Spawn three agents in parallel:

### Agent: universe-scout

Spawn with Agent tool (subagent_type: general-purpose, name: "universe-scout", team_name: "vda-{TICKER_LOWER}"):

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

Spawn with Agent tool (subagent_type: general-purpose, name: "source-mapper", team_name: "vda-{TICKER_LOWER}"):

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

Spawn with Agent tool (subagent_type: general-purpose, name: "metric-architect", team_name: "vda-{TICKER_LOWER}"):

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

## Step 8: Step 2 of 5 — "Gather Data" (Parallel)

Spawn two agents in parallel:

### Agent: data-collector

**CRITICAL: Split into 3 parallel tiers of ~9 firms each. Never assign 25+ firms to one agent — this will cause timeouts and incomplete output.**

Spawn three sub-instances of the data-collector, each covering a tier of firms:

**Tier 1 (top firms by AUM — approximately first 9):**

Spawn with Agent tool (subagent_type: general-purpose, name: "data-collector-t1", team_name: "vda-{TICKER_LOWER}"):

Instructions:
> You are data-collector-t1 for the Valuation Driver Analysis pipeline.
>
> **Your task:** Execute Stage VD-A2 — Data Collection for Tier 1 firms.
>
> Read `data/processed/{TICKER}/{DATE}/1-universe/peer_universe.json` to get the full firm list.
> Read `data/processed/{TICKER}/{DATE}/1-universe/metric_taxonomy.json` to get the metric taxonomy.
>
> **Cover firms ranked 1–9 by AUM** (the largest firms in the universe).
>
> For each firm and each metric, extract the most recent completed fiscal year (FY1), prior fiscal year (FY2), and three-year historical data where available.
>
> Primary sources: earnings releases, annual reports (20-F / 10-K), investor day presentations, earnings supplements, filesystem at `data/raw/{TICKER}/{DATE}/supplemental/` (check manifest.json — supplemental data takes priority over web search).
>
> For each data point record: firm_id, metric_id, value, period (FY1/FY2/FY3), currency, source_id, bias_tag, confidence (high/medium/low), extraction_notes.
>
> Missing data: record as `null` with explicit `missing_reason`. No estimation or interpolation.
>
> **Output:** `data/processed/{TICKER}/{DATE}/2-data/quantitative_tier1.json`

**Tier 2 (mid-tier firms — approximately firms 10–18):**

Spawn with Agent tool (subagent_type: general-purpose, name: "data-collector-t2", team_name: "vda-{TICKER_LOWER}"):

Instructions:
> You are data-collector-t2 for the Valuation Driver Analysis pipeline.
>
> **Your task:** Execute Stage VD-A2 — Data Collection for Tier 2 firms.
>
> Read `data/processed/{TICKER}/{DATE}/1-universe/peer_universe.json` to get the full firm list.
> Read `data/processed/{TICKER}/{DATE}/1-universe/metric_taxonomy.json` to get the metric taxonomy.
>
> **Cover firms ranked 10–18 by AUM** (mid-tier firms in the universe).
>
> For each firm and each metric, extract FY1, FY2, and three-year historical data where available.
>
> Primary sources: earnings releases, annual reports (20-F / 10-K), investor day presentations, earnings supplements. Check `data/raw/{TICKER}/{DATE}/supplemental/manifest.json` — supplemental data takes priority.
>
> For each data point record: firm_id, metric_id, value, period, currency, source_id, bias_tag, confidence, extraction_notes. Missing data → `null` with `missing_reason`.
>
> **Output:** `data/processed/{TICKER}/{DATE}/2-data/quantitative_tier2.json`

**Tier 3 (remaining firms — approximately firms 19–end):**

Spawn with Agent tool (subagent_type: general-purpose, name: "data-collector-t3", team_name: "vda-{TICKER_LOWER}"):

Instructions:
> You are data-collector-t3 for the Valuation Driver Analysis pipeline.
>
> **Your task:** Execute Stage VD-A2 — Data Collection for Tier 3 firms.
>
> Read `data/processed/{TICKER}/{DATE}/1-universe/peer_universe.json` to get the full firm list.
> Read `data/processed/{TICKER}/{DATE}/1-universe/metric_taxonomy.json` to get the metric taxonomy.
>
> **Cover firms ranked 19 through the end** (smaller firms in the universe).
>
> For each firm and each metric, extract FY1, FY2, and three-year historical data where available.
>
> Primary sources: earnings releases, annual reports (20-F / 10-K), investor day presentations, earnings supplements. Check `data/raw/{TICKER}/{DATE}/supplemental/manifest.json` — supplemental data takes priority.
>
> For each data point record: firm_id, metric_id, value, period, currency, source_id, bias_tag, confidence, extraction_notes. Missing data → `null` with `missing_reason`.
>
> **Output:** `data/processed/{TICKER}/{DATE}/2-data/quantitative_tier3.json`

After all three tiers complete, merge the outputs:

> Send to metric-architect (via SendMessage):
> Merge `2-data/quantitative_tier1.json`, `2-data/quantitative_tier2.json`, `2-data/quantitative_tier3.json` into a single `2-data/quantitative_data.json`. Deduplicate by firm_id + metric_id + period. Log any conflicts (same firm+metric+period with different values) to `2-data/merge_conflicts.md`.

### Agent: strategy-extractor

Spawn with Agent tool (subagent_type: general-purpose, name: "strategy-extractor", team_name: "vda-{TICKER_LOWER}"):

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
>
> For each firm in the qualitative peer set (BX, KKR, APO, ARES, BAM, OWL, TPG, CG, EQT, PGHN, STEP, HLN, BN, ICP, AMK), extract a standalone strategic profile across 10 dimensions:
> 1. Geographic reach (domestic / regional / global; primary markets)
> 2. Asset focus (core strategies by asset type)
> 3. Asset class mix (distribution of AUM across PE, credit, infra, real estate, solutions/multi-asset)
> 4. Origination model (proprietary vs. sponsor-to-sponsor vs. platform/operating companies)
> 5. Fund type emphasis (closed-end flagship vs. open-end / perpetual / evergreen vs. co-mingled SMAs)
> 6. Capital source (institutional LP vs. retail/wealth vs. insurance/corporate balance sheet)
> 7. Distribution strategy (direct institutional vs. third-party networks vs. wirehouse/RIA)
> 8. Client segment (sovereign wealth/large pensions vs. mid-market institutions vs. UHNW/family office vs. retail/DC)
> 9. Growth model (organic vs. geographic expansion vs. product adjacency vs. M&A/consolidation)
> 10. Stated strategic priorities (top 3–5 verbatim or closely paraphrased from most recent Investor Day or annual report)
>
> Profiles are self-contained — they do not reference {COMPANY} and do not compare firms against any external benchmark.
>
> **Output A:** `data/processed/{TICKER}/{DATE}/2-data/strategy_profiles.json`
>
> **Task B — Stage VD-B2:** Execute Action Cataloging for all firms in the qualitative peer set.
>
> For each firm, catalog concrete strategic actions taken in the prior 2–3 years. For each action record:
> - action_id (ACT-VD-NNN)
> - firm_id
> - action_type: `M&A`, `product-launch`, `geographic-expansion`, `distribution-shift`, `capital-structure-change`, `organizational-change`, `technology-operations`
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
> **Output B:** `data/processed/{TICKER}/{DATE}/2-data/strategic_actions.json`

### Quality Gate 2

After all four agents complete (three data-collector tiers + strategy-extractor), check:

**Criteria:**
- Data coverage: >= 60% of metrics are populated for >= 80% of universe firms
- All three valuation multiples (P/FRE, P/DE, EV/FEAUM) are populated for all firms
- Qualitative profiles have >= 2 concrete actions per firm (VD-B2)
- **Operational metrics coverage:** verify disclosure quality for Operational Feasibility & Scalable Infrastructure metrics — any metric with < 60% coverage is reclassified as `contextual-only` (excluded from VD-A4 correlation analysis but permitted in context tables and deep-dives)
- **FX methodology check:** verify that FX_MATERIAL flags are populated where applicable; confirm period-end rates used for stock metrics and period-average rates for flow metrics

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

## Step 9: Step 3 of 5 — "Find What Drives Value" (Sequential)

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
> Classification of results:
> - Stable value driver: ρ > 0.5 across all three multiples
> - Multiple-specific driver: ρ > 0.5 for exactly one multiple
> - Moderate signal: 0.3 ≤ ρ ≤ 0.5 for at least one multiple
> - Not a driver: ρ < 0.3 for all three multiples
>
> Following classification, test for multicollinearity among top-ranked stable drivers. Where two drivers exhibit ρ > 0.7 with each other, document the pair and flag the multicollinearity risk.
>
> For each correlation result record: correlation_id (COR-NNN), driver_metric_id, valuation_multiple, spearman_rho, classification, n_firms_included, notes.
>
> **Output:** `data/processed/{TICKER}/{DATE}/3-analysis/correlations.json`

### Send to metric-architect: VD-A4b Statistical Documentation

> **Stage VD-A4b — Statistical Documentation and Explainability.**
>
> Read `data/processed/{TICKER}/{DATE}/3-analysis/correlations.json`.
>
> Produce a standalone methodology document. Required contents:
>
> 1. **Methods and justification:** Document choice of Spearman over Pearson (robustness to non-normality, outlier resistance, monotonic relationships). Document explicitly why multiple regression was not used (insufficient degrees of freedom with N≈25, multicollinearity, overfitting risk, endogeneity).
>
> 2. **Bootstrap confidence intervals:** 1,000 bootstrap iterations per coefficient. Report 95% CIs. Flag CIs that include zero.
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
>    - Temporal stability: compare correlations on FY1 vs. FY2 data; flag unstable correlations
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

### Send to metric-architect: VD-C1 Convergence

After VD-A5 completes, spawn the convergence analyst:

Spawn with Agent tool (subagent_type: general-purpose, name: "convergence-analyst", team_name: "vda-{TICKER_LOWER}"):

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

Spawn two agents in parallel:

### Agent: platform-analyst

Spawn with Agent tool (subagent_type: general-purpose, name: "platform-analyst", team_name: "vda-{TICKER_LOWER}"):

Instructions:
> You are the platform-analyst for the Valuation Driver Analysis pipeline.
>
> **Your task:** Execute Stage VD-D1 — Platform-Level Deep-Dives.
>
> Read `data/processed/{TICKER}/{DATE}/3-analysis/final_peer_set.json` for the list of 9–12 firms.
> Read `data/processed/{TICKER}/{DATE}/3-analysis/driver_ranking.json` for stable driver rankings.
> Read `data/processed/{TICKER}/{DATE}/2-data/strategy_profiles.json` and `data/processed/{TICKER}/{DATE}/2-data/strategic_actions.json`.
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
>
> All profiles must be internally consistent. Transferable insights must be grounded in documented evidence from VD-B2, not inference.
>
> **Output:** `data/processed/{TICKER}/{DATE}/4-deep-dives/platform_profiles.json`

### Agent: vertical-analyst

Spawn with Agent tool (subagent_type: general-purpose, name: "vertical-analyst", team_name: "vda-{TICKER_LOWER}"):

Instructions:
> You are the vertical-analyst for the Valuation Driver Analysis pipeline.
>
> **Your task:** Execute Stage VD-D2 — Asset Class Deep-Dives.
>
> Read `data/processed/{TICKER}/{DATE}/3-analysis/driver_ranking.json` for which stable drivers are most salient.
> Read `data/processed/{TICKER}/{DATE}/2-data/strategic_actions.json` for peer actions.
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
2. Read evidence files: `3-analysis/correlations.json`, `3-analysis/driver_ranking.json`, `2-data/strategic_actions.json`, `2-data/strategy_profiles.json`
3. Send to claim-auditor via SendMessage:
   - Checkpoint: CP-2
   - Stage audited: VD-D1, VD-D2
   - Files audited: `4-deep-dives/platform_profiles.json`, `4-deep-dives/asset_class_analysis.json`
   - Audit focus: ALL (invalid_premises, misleading_context, sycophantic_fabrication, confidence_miscalibration) + operational_prerequisite_evidence (block any prerequisite based solely on job postings or vendor PRs)
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

### Agent: playbook-synthesizer

Spawn with Agent tool (subagent_type: general-purpose, name: "playbook-synthesizer", team_name: "vda-{TICKER_LOWER}"):

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
> **Entries missing any mandatory field will be blocked at CP-3.**
>
> **Output B:** `data/processed/{TICKER}/{DATE}/5-playbook/platform_playbook.json`
>
> **Task C — Stage VD-P3: Asset Class Playbooks**
>
> Read `data/processed/{TICKER}/{DATE}/4-deep-dives/asset_class_analysis.json`.
>
> Produce a parallel strategic menu at the vertical level, organized by value driver within each vertical. Same structure as VD-P2 — every PLAY-NNN and ANTI-NNN must include ALL mandatory fields (What_Was_Done, Observed_Metric_Impact, Prerequisites, Operational_And_Tech_Prerequisites, Execution_Burden, Failure_Modes_And_Margin_Destroyers, Transferability_Constraints, Evidence_Strength). Evidence citations to specific peer actions (ACT-VD-NNN). Cover all 5 verticals: Credit, Private Equity, Infrastructure, Real Estate, GP-Led Solutions/Secondaries.
>
> Within each vertical, organize plays by **strategy sub-type** (from VD-D2) where applicable, so readers can identify plays relevant to their specific sub-type.
>
> **Entries missing any mandatory field will be blocked at CP-3.**
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
   - Audit focus: sycophantic_fabrication, confidence_miscalibration, mandatory_field_completeness (block any PLAY-NNN or ANTI-NNN lacking Operational_And_Tech_Prerequisites, Failure_Modes_And_Margin_Destroyers, or Evidence_Strength)
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

Then spawn the report-builder and target-lens agents **in parallel** (they share the same inputs and have no dependency on each other):

### Agent: report-builder

Spawn with Agent tool (subagent_type: general-purpose, name: "report-builder", team_name: "vda-{TICKER_LOWER}"):

Instructions:
> You are the report-builder for the Valuation Driver Analysis pipeline.
>
> **Your task:** Execute Stage VD-P4 — Final Navigable HTML Report.
>
> Read all pipeline outputs in `data/processed/{TICKER}/{DATE}/`:
> - `5-playbook/value_principles.md`
> - `5-playbook/platform_playbook.json`
> - `5-playbook/asset_class_playbooks.json`
> - `4-deep-dives/platform_profiles.json`
> - `4-deep-dives/asset_class_analysis.json`
> - `3-analysis/statistical_methodology.md`
> - `3-analysis/driver_ranking.json`
>
> Produce a single self-contained HTML file with two addressable layers:
>
> **Layer 1 (Platform):**
> - Executive summary
> - Methodology and statistical appendix (reproduce verbatim disclaimers from VD-A4b)
> - Industry value driver findings (stable drivers with full statistical documentation)
> - Firm-level strategies and actions (platform deep-dives)
> - Platform strategic menu (organized by driver)
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
>
> **Style matching:**
> - If `data/processed/{TICKER}/{DATE}/style_guide.json` exists, adapt the report's tone, terminology, and structure to match the style guide while preserving all analytical rigor and mandatory disclaimers
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

Spawn with Agent tool (subagent_type: general-purpose, name: "target-lens", team_name: "vda-{TICKER_LOWER}"):

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
>
> For each PLAY-NNN in the platform and asset class playbooks, assess applicability to {COMPANY}:
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
> - `implementation_pathway`: concrete steps {COMPANY} could take, in what sequence, with what prerequisites
>
> **Additionally, produce a "Strategic Guidance" section structured for governance cascading:**
>
> **For PHL/Board level** (top-down strategic guidelines):
> - Top 5 value-creating principles relevant to {COMPANY}
> - Portfolio-level strategic priorities (which asset classes to grow, which capabilities to build)
> - 3-year directional targets linked to stable value drivers
>
> **For CEO/Management Committee** (operational translation):
> - Priority initiatives mapped to value drivers
> - Resource allocation implications
> - Quick wins vs. structural investments
>
> **Per Business Unit** (asset class specific):
> - For each of {COMPANY}'s business segments: top 3 applicable plays with implementation pathway
> - Competitive positioning vs. peers in that asset class
> - Do's and Don'ts grounded in peer evidence
>
> **Output:** `data/processed/{TICKER}/{DATE}/5-playbook/target_company_lens.json`

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
- Same sensitivity-check definitions (leave-one-out, temporal stability)

Low-coverage operational metrics (< 60% coverage) from the Operational Feasibility category may appear in context tables and deep-dives but must be labeled `contextual-only` and never cited as evidence of driver status.

### Statistical Methodology Improvements (from peer review)
The Statistical Analyst agent (VD-A4/A4b) must additionally:
1. **Run all correlations on a consistent sub-sample** of firms for which all three valuation multiples are available. Present supplementary results for the full sample separately.
2. **Flag metrics with N<10** as "insufficient data for evaluation" rather than classifying them as "not a driver."
3. **Compute partial correlations** for the top drivers, controlling for scale (mgmt_fee_rev), to test for confounded signals.
4. **Use 1,000-iteration bootstrap CIs** as specified. If Fisher z is used as a substitute, document the rationale explicitly.
5. **Execute temporal stability check** comparing FY1 vs FY2 correlations when data is available.
6. **Estimate effective independent tests** for multiple comparison correction (accounting for collinear pairs) rather than applying Bonferroni over all raw tests.

### Data Provenance Requirements (from peer review)
The Data Collector agents must:
1. **Record market cap reference date** per firm (not just the value).
2. **Document source and methodology** for computed metrics (organic growth, asset class HHI).
3. **Flag firms with non-calendar fiscal years** and specify the exact period covered.

### Iterative Run Support
When `--base-run` is provided:
1. All agents receive the path to the previous run's outputs as additional context
2. Agents are instructed to: review previous findings, identify gaps or weak points, incorporate any new supplemental sources, and produce improved outputs
3. The convergence analyst explicitly compares the new peer set against the previous run's peer set and documents changes
4. The report-builder includes a "Changes from Previous Analysis" appendix if base_run outputs exist
5. Quality gates compare coverage metrics against the base run — new run should not regress on coverage

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
