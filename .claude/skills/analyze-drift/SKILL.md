---
name: analyze-drift
description: Run the full Strategy Drift Detection pipeline for any public company. Orchestrates 5 specialized agents across 4 waves to evaluate whether a company's actions align with its stated strategic priorities. Usage: /analyze-drift TICKER [--auto]
---

# Strategy Drift Analysis

Analyze strategic coherence for any public company by ticker symbol.

## Usage

```
/analyze-drift TICKER           # interactive mode (pauses at quality gates)
/analyze-drift TICKER --auto    # automatic mode (gates validated by lead agent)
```

## Step 0: Parse Arguments

Extract from the user's input:
- `TICKER` (required) — e.g., `SQ`, `PAX`, `AAPL`
- `--auto` flag (optional) — if present, quality gates are automatic; otherwise interactive

If no TICKER is provided, ask the user for one.

Set `DATE` to today's date in `YYYY-MM-DD` format.
Set `TICKER_LOWER` to the lowercase version of `TICKER`.

## Step 1: Create Directory Structure

Check if `data/processed/{TICKER}/{DATE}/` already exists. If it does, find the highest existing run suffix:

```bash
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

Display to the user: "Output directory: `data/processed/{TICKER}/{DATE}/`"

## Step 2: Stage -1 — Company Context Discovery

Before spawning agents, research the company and create `data/processed/{TICKER}/{DATE}/company_context.json`.

Use WebSearch to find:
- Full legal company name
- Stock exchange
- CEO and CFO names
- Major business segments
- Investor relations URL
- SEC CIK number
- Any recent name changes

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
  "ir_url": "...",
  "sec_cik": "...",
  "recent_name_changes": "..."
}
```

Display the discovered context to the user and confirm before proceeding.

## Step 3: Placeholder Resolution Reference

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
| `{DATE}` | today's date (YYYY-MM-DD) |

All output file paths use: `data/processed/{TICKER}/{DATE}/` and `data/raw/{TICKER}/{DATE}/`

## Step 4: Create Agent Team

```
TeamCreate → team_name: "drift-{TICKER_LOWER}"
```

## Step 5: Wave 1 — Foundation (Parallel)

Spawn two agents in parallel:

### Agent: source-scout

Spawn with Agent tool (subagent_type: general-purpose, name: "source-scout", team_name: "drift-{TICKER_LOWER}"):

Instructions to include in the prompt:
> You are the source-scout agent for the Strategy Drift Detector.
>
> **Company:** {COMPANY} ({EXCHANGE}: {TICKER})
> **CEO:** {CEO} | **CFO:** {CFO}
> **Business Segments:** {SEGMENTS}
> **IR URL:** {IR_URL}
> **SEC CIK:** {SEC_CIK}
>
> **Your task:** Execute Stage 0 — Source Identification and Classification.
> Read the prompt at `prompts/drift/00_source_mapping.md` and follow it exactly.
> Replace all placeholders with the company values above.
>
> **Output path:** `data/processed/{TICKER}/{DATE}/stage_0_sources.md`
>
> Search the web for public sources about this company. Catalog each source with bias tags. Run the sufficiency assessment. Write the output file.

### Agent: prompt-reviewer

Spawn with Agent tool (subagent_type: general-purpose, name: "prompt-reviewer", team_name: "drift-{TICKER_LOWER}"):

Instructions:
> You are the prompt-reviewer agent. Review all prompt files in `prompts/` to verify:
> 1. No hardcoded company names remain (should use {COMPANY}, {TICKER}, etc.)
> 2. Placeholder usage is consistent
> 3. Output paths use {TICKER}/{DATE}/ format
>
> Report any issues found. In Wave 4, you will be recalled for QA review.

### Quality Gate 1

**Interactive mode:** Display to user:
- Source count and bias distribution from stage_0_sources.md
- Sufficiency verdict
- Ask: "Sources look good. Proceed to Wave 2?"

**Auto mode:** Read the sufficiency verdict from stage_0_sources.md. If INSUFFICIENT, send message to source-scout to fill gaps. If SUFFICIENT, proceed automatically.

## Step 6: Wave 2 — Information Gathering (Parallel)

Spawn two agents:

### Agent: strategy-intel

Spawn with Agent tool (subagent_type: general-purpose, name: "strategy-intel", team_name: "drift-{TICKER_LOWER}"):

Instructions:
> You are the strategy-intel agent for the Strategy Drift Detector.
>
> **Company:** {COMPANY} ({EXCHANGE}: {TICKER})
> **CEO:** {CEO} | **CFO:** {CFO}
> **Business Segments:** {SEGMENTS}
> **Company Context:** Read `data/processed/{TICKER}/{DATE}/company_context.json`
>
> **Your task:** Execute Stage 1A — Strategy Element Extraction.
> Read the prompt at `prompts/drift/01_gather_strategy.md` and follow it exactly.
> Use the source catalog at `data/processed/{TICKER}/{DATE}/stage_0_sources.md`.
> Replace all placeholders with company values.
>
> **Output paths:**
> - Raw texts: `data/raw/{TICKER}/{DATE}/{TICKER_LOWER}_strategy_{source_id}.txt`
> - Structured output: `data/processed/{TICKER}/{DATE}/stage_1a_strategy.json`

### Agent: execution-intel

Spawn with Agent tool (subagent_type: general-purpose, name: "execution-intel", team_name: "drift-{TICKER_LOWER}"):

Instructions:
> You are the execution-intel agent for the Strategy Drift Detector.
>
> **Company:** {COMPANY} ({EXCHANGE}: {TICKER})
> **CEO:** {CEO} | **CFO:** {CFO}
> **Business Segments:** {SEGMENTS}
> **Company Context:** Read `data/processed/{TICKER}/{DATE}/company_context.json`
>
> **Tasks (sequential):**
>
> **Task A — Stage 1B:** Execute Action and Execution Evidence Extraction.
> Read `prompts/drift/01_gather_actions.md`. Use source catalog at `data/processed/{TICKER}/{DATE}/stage_0_sources.md`.
> Output: `data/raw/{TICKER}/{DATE}/{TICKER_LOWER}_actions_{source_id}.txt` + `data/processed/{TICKER}/{DATE}/stage_1b_actions.json`
>
> **Task B — Stage 1C:** Execute Forward-Looking Commitment Extraction (after Task A).
> Read `prompts/drift/01_gather_commitments.md`.
> Output: `data/raw/{TICKER}/{DATE}/{TICKER_LOWER}_commitments_{source_id}.txt` + `data/processed/{TICKER}/{DATE}/stage_1c_commitments.json`

### Quality Gate 2

**Interactive mode:** Display:
- Count of STR-*, ACT-*, CMT-* elements extracted
- Ask: "Data gathering complete. Proceed to Wave 3?"

**Auto mode:** Verify element counts meet minimums from prompts. Proceed if met.

Write `data/processed/{TICKER}/{DATE}/source_sufficiency_assessment.md`.

## Step 7: Wave 3 — Analysis (Parallel then Sequential)

### Send to strategy-intel (via SendMessage):

> Proceed to Stage 2 — Strategic Pillar Synthesis.
> Read `prompts/drift/02_map_pillars.md`.
> Inputs: `data/processed/{TICKER}/{DATE}/stage_1a_strategy.json` + `data/processed/{TICKER}/{DATE}/stage_1c_commitments.json`
> Output: `data/processed/{TICKER}/{DATE}/stage_2_pillars.json`

Wait for Stage 2 to complete, then send to execution-intel:

### Send to execution-intel (via SendMessage):

> Proceed to Stage 3 — Action and Commitment to Pillar Mapping.
> Read `prompts/drift/03_map_actions.md`.
> Inputs: `data/processed/{TICKER}/{DATE}/stage_2_pillars.json` + `data/processed/{TICKER}/{DATE}/stage_1b_actions.json` + `data/processed/{TICKER}/{DATE}/stage_1c_commitments.json`
> Output: `data/processed/{TICKER}/{DATE}/stage_3_actions.json`

### Quality Gate 3

**Interactive mode:** Display pillar names, priority ranks. Ask: "Analysis complete. Proceed to final synthesis?"

**Auto mode:** Verify pillar count >= 2 and action mappings exist. Proceed.

## Step 8: Wave 4 — Synthesis (Sequential)

### Agent: drift-analyst

Spawn with Agent tool (subagent_type: general-purpose, name: "drift-analyst", team_name: "drift-{TICKER_LOWER}"):

Instructions:
> You are the drift-analyst agent for the Strategy Drift Detector.
>
> **Company:** {COMPANY} ({EXCHANGE}: {TICKER})
> **Company Context:** Read `data/processed/{TICKER}/{DATE}/company_context.json`
>
> **Task A — Stage 4:** Execute Multi-Dimensional Coherence Analysis.
> Read `prompts/drift/04_coherence_analysis.md`.
> Inputs: ALL stage files in `data/processed/{TICKER}/{DATE}/`
> Output: `data/processed/{TICKER}/{DATE}/stage_4_coherence.json`
>
> **Task B — Stage 5:** Generate Final Report.
> Read `prompts/drift/05_final_report.md`.
> Inputs: ALL stage files in `data/processed/{TICKER}/{DATE}/`
> Output: `data/processed/{TICKER}/{DATE}/final_report.md`
>
> **Task C — HTML Generation:** Convert final_report.md to styled HTML.
> Output: `data/processed/{TICKER}/{DATE}/final_report.html`
> Use clean professional styling: serif body font, bordered tables, company name + date in header, navigation sidebar.

Wait for drift-analyst to complete, then send QA review to prompt-reviewer:

### Send to prompt-reviewer (via SendMessage):

> Review the final report at `data/processed/{TICKER}/{DATE}/final_report.md`.
> Check: academic language, source citations, bias acknowledgments, limitations, scoring consistency, pillar ID consistency.
> Write review to `data/processed/{TICKER}/{DATE}/qa_review.md`.

### Quality Gate 4 (always shown)

Display QA review summary to user regardless of mode.

## Step 9: Cleanup and Report

Display final summary:
- Company analyzed: {COMPANY} ({TICKER})
- Overall coherence score and classification
- Top 3 drift flags
- Report path: `data/processed/{TICKER}/{DATE}/final_report.md`
- HTML path: `data/processed/{TICKER}/{DATE}/final_report.html`

Clean up: `TeamDelete → team_name: "drift-{TICKER_LOWER}"`

Offer to commit:
```
git add data/processed/{TICKER}/{DATE}/ data/raw/{TICKER}/{DATE}/
git commit -m "feat: strategy drift analysis for {COMPANY} ({TICKER})"
```
