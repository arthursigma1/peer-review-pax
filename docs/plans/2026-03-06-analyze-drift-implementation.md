# `/analyze-drift` Skill Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a Claude Code slash command (`/analyze-drift TICKER [--auto]`) that automates the full Strategy Drift Detection pipeline for any public company.

**Architecture:** A skill file (`.claude/skills/analyze-drift/SKILL.md`) that orchestrates 5 agents across 4 waves, with parameterized prompts using `{COMPANY}`, `{TICKER}`, etc. placeholders replaced at runtime via a company context discovery stage.

**Tech Stack:** Claude Code skills (markdown), agent teams (TeamCreate/Agent/SendMessage)

---

## Task 1: Parameterize Prompt — `00_source_mapping.md`

**Files:**
- Modify: `prompts/00_source_mapping.md`

**Step 1: Replace hardcoded references**

Replace all Block-specific references with placeholders:

| Find | Replace With |
|------|-------------|
| `Block, Inc. (formerly Square, Inc.)` | `{COMPANY}` |
| `Block, Inc.` | `{COMPANY}` |
| `(NYSE: XYZ → SQ; legal name change effective December 2021)` | `({EXCHANGE}: {TICKER})` |
| `Jack Dorsey / CEO communications` | `{CEO} / CEO communications` |
| `Block newsroom` | `{COMPANY} newsroom` |
| `Block's competitive positioning` | `{COMPANY}'s competitive positioning` |
| The entire segment coverage bullet: `Sources available for all major business segments (Cash App, Square/Seller, TIDAL/music, Bitcoin/TBD)` | `Sources available for all major business segments (as identified in company_context.json)` |

**Step 2: Update output path reference**

Change:
```
data/processed/stage_0_sources.md
```
To:
```
data/processed/{TICKER}/{DATE}/stage_0_sources.md
```

(Apply this path update everywhere the output path appears in the file.)

**Step 3: Verify no remaining hardcoded references**

Run: `grep -in "block\|square\|jack dorsey\|cash app\|tidal\|spiral\|tbd" prompts/00_source_mapping.md`
Expected: No matches.

**Step 4: Commit**

```bash
git add prompts/00_source_mapping.md
git commit -m "feat: parameterize source mapping prompt for any company"
```

---

## Task 2: Parameterize Prompt — `01_gather_strategy.md`

**Files:**
- Modify: `prompts/01_gather_strategy.md`

**Step 1: Replace hardcoded references**

| Find | Replace With |
|------|-------------|
| `Block, Inc.` | `{COMPANY}` |
| `block_strategy_{source_id}.txt` | `{TICKER_LOWER}_strategy_{source_id}.txt` |
| `"company": "Block, Inc."` (in JSON example) | `"company": "{COMPANY}"` |

**Step 2: Update output/input path references**

All paths like `data/processed/stage_*` become `data/processed/{TICKER}/{DATE}/stage_*`.
All paths like `data/raw/block_*` become `data/raw/{TICKER}/{DATE}/{TICKER_LOWER}_*`.

**Step 3: Verify no remaining hardcoded references**

Run: `grep -in "block\|square\|jack dorsey\|cash app" prompts/01_gather_strategy.md`
Expected: No matches.

**Step 4: Commit**

```bash
git add prompts/01_gather_strategy.md
git commit -m "feat: parameterize strategy gathering prompt for any company"
```

---

## Task 3: Parameterize Prompt — `01_gather_actions.md`

**Files:**
- Modify: `prompts/01_gather_actions.md`

**Step 1: Replace hardcoded references**

| Find | Replace With |
|------|-------------|
| `Block, Inc.` | `{COMPANY}` |
| `block_actions_{source_id}.txt` | `{TICKER_LOWER}_actions_{source_id}.txt` |
| `"company": "Block, Inc."` (in JSON example) | `"company": "{COMPANY}"` |

**Step 2: Update output/input path references**

Same pattern as Task 2.

**Step 3: Verify**

Run: `grep -in "block\|square" prompts/01_gather_actions.md`
Expected: No matches.

**Step 4: Commit**

```bash
git add prompts/01_gather_actions.md
git commit -m "feat: parameterize actions gathering prompt for any company"
```

---

## Task 4: Parameterize Prompt — `01_gather_commitments.md`

**Files:**
- Modify: `prompts/01_gather_commitments.md`

**Step 1: Replace hardcoded references**

| Find | Replace With |
|------|-------------|
| `Block, Inc.` | `{COMPANY}` |
| `block_commitments_{source_id}.txt` | `{TICKER_LOWER}_commitments_{source_id}.txt` |
| `"company": "Block, Inc."` (in JSON example) | `"company": "{COMPANY}"` |
| `'Jack Dorsey, CEO'` | `'{CEO}, CEO'` |
| `'Amrita Ahuja, CFO'` | `'{CFO}, CFO'` |

**Step 2: Update output/input path references**

Same pattern as Task 2.

**Step 3: Verify**

Run: `grep -in "block\|jack dorsey\|amrita ahuja" prompts/01_gather_commitments.md`
Expected: No matches.

**Step 4: Commit**

```bash
git add prompts/01_gather_commitments.md
git commit -m "feat: parameterize commitments gathering prompt for any company"
```

---

## Task 5: Parameterize Prompt — `02_map_pillars.md`

**Files:**
- Modify: `prompts/02_map_pillars.md`

**Step 1: Replace hardcoded references**

| Find | Replace With |
|------|-------------|
| `Block, Inc.` | `{COMPANY}` |
| `"company": "Block, Inc."` | `"company": "{COMPANY}"` |
| The entire "Expected pillar areas for Block, Inc." block (lines listing Bitcoin, Cash App, Square/Seller, etc.) | Replace with: `**Expected pillar areas:** Review the business segments listed in company_context.json. Use these as initial hypotheses for pillar clustering, but do not force-fit — follow the evidence.` |

**Step 2: Update path references**

Same pattern.

**Step 3: Verify**

Run: `grep -in "block\|bitcoin\|cash app\|square\|seller\|tidal" prompts/02_map_pillars.md`
Expected: No matches.

**Step 4: Commit**

```bash
git add prompts/02_map_pillars.md
git commit -m "feat: parameterize pillar mapping prompt for any company"
```

---

## Task 6: Parameterize Prompt — `03_map_actions.md`

**Files:**
- Modify: `prompts/03_map_actions.md`

**Step 1: Replace hardcoded references**

| Find | Replace With |
|------|-------------|
| `Block, Inc.` (if any remain — check the count of 1 match) | `{COMPANY}` |
| `"company": "Block, Inc."` | `"company": "{COMPANY}"` |

**Step 2: Update path references**

Same pattern.

**Step 3: Verify**

Run: `grep -in "block" prompts/03_map_actions.md`
Expected: No matches.

**Step 4: Commit**

```bash
git add prompts/03_map_actions.md
git commit -m "feat: parameterize action mapping prompt for any company"
```

---

## Task 7: Parameterize Prompt — `04_coherence_analysis.md`

**Files:**
- Modify: `prompts/04_coherence_analysis.md`

**Step 1: Replace hardcoded references**

| Find | Replace With |
|------|-------------|
| `Block, Inc.` | `{COMPANY}` |
| `"company": "Block, Inc."` | `"company": "{COMPANY}"` |

**Step 2: Update path references**

Same pattern.

**Step 3: Verify**

Run: `grep -in "block" prompts/04_coherence_analysis.md`
Expected: No matches.

**Step 4: Commit**

```bash
git add prompts/04_coherence_analysis.md
git commit -m "feat: parameterize coherence analysis prompt for any company"
```

---

## Task 8: Parameterize Prompt — `05_final_report.md`

**Files:**
- Modify: `prompts/05_final_report.md`

**Step 1: Replace hardcoded references**

| Find | Replace With |
|------|-------------|
| `Block, Inc.` | `{COMPANY}` |
| `# Strategy Drift Analysis: Block, Inc.` (in the example output) | `# Strategy Drift Analysis: {COMPANY}` |

**Step 2: Update path references**

Same pattern.

**Step 3: Verify**

Run: `grep -in "block" prompts/05_final_report.md`
Expected: No matches.

**Step 4: Commit**

```bash
git add prompts/05_final_report.md
git commit -m "feat: parameterize final report prompt for any company"
```

---

## Task 9: Create the Skill File

**Files:**
- Create: `.claude/skills/analyze-drift/SKILL.md`

**Step 1: Create skill directory**

Run: `mkdir -p .claude/skills/analyze-drift`

**Step 2: Write the skill file**

Create `.claude/skills/analyze-drift/SKILL.md` with the following content:

```markdown
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

Set `DATE` to today's date in `YYYY-MM-DD` format.

Set `TICKER_LOWER` to the lowercase version of `TICKER`.

## Step 1: Create Directory Structure

Create the following directories:

```
data/processed/{TICKER}/{DATE}/
data/raw/{TICKER}/{DATE}/
```

## Step 2: Stage -1 — Company Context Discovery

Before spawning agents, research the company and create `data/processed/{TICKER}/{DATE}/company_context.json`:

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

This context will be included in every agent's instructions so they know which company to analyze.

## Step 3: Placeholder Resolution Reference

When agents use prompts from `prompts/`, they must mentally replace these placeholders with values from `company_context.json`:

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

### Agent: `source-scout`

**Instructions:**
> You are the source-scout agent for the Strategy Drift Detector.
>
> **Company:** {COMPANY} ({EXCHANGE}: {TICKER})
> **CEO:** {CEO} | **CFO:** {CFO}
> **Business Segments:** {SEGMENTS}
> **IR URL:** {IR_URL}
> **SEC CIK:** {SEC_CIK}
>
> **Your task:** Execute Stage 0 — Source Identification and Classification.
> Read the prompt at `prompts/00_source_mapping.md` and follow it exactly.
> Replace all `{COMPANY}` placeholders with "{COMPANY}" and `{TICKER}` with "{TICKER}".
>
> **Output paths:**
> - `data/processed/{TICKER}/{DATE}/stage_0_sources.md`
>
> Search the web for public sources. Catalog each source. Run the sufficiency assessment.

### Agent: `prompt-engineer`

**Instructions:**
> You are the prompt-engineer agent. Your tasks during this wave:
> 1. Review all prompt files in `prompts/` to ensure they are ready for use with {COMPANY}.
> 2. Verify placeholder consistency (`{COMPANY}`, `{TICKER}`, etc. are used instead of hardcoded names).
> 3. Report any issues found.
>
> In Wave 4, you will be recalled for QA review of the final report.

### Quality Gate 1

**Interactive mode:** Display to user:
- Source count and bias distribution
- Sufficiency verdict
- Ask: "Sources look good. Proceed to Wave 2?"

**Auto mode:** Lead agent reviews sufficiency verdict. If INSUFFICIENT, message source-scout to fill gaps. If SUFFICIENT, proceed.

## Step 6: Wave 2 — Information Gathering (Parallel)

Spawn two agents:

### Agent: `strategy-intel`

**Instructions:**
> You are the strategy-intel agent for the Strategy Drift Detector.
>
> **Company:** {COMPANY} ({EXCHANGE}: {TICKER})
> **CEO:** {CEO} | **CFO:** {CFO}
> **Business Segments:** {SEGMENTS}
> **Company Context:** Read `data/processed/{TICKER}/{DATE}/company_context.json`
>
> **Your task:** Execute Stage 1A — Strategy Element Extraction.
> Read the prompt at `prompts/01_gather_strategy.md` and follow it exactly.
> Use the source catalog at `data/processed/{TICKER}/{DATE}/stage_0_sources.md`.
>
> **Output paths:**
> - Raw texts: `data/raw/{TICKER}/{DATE}/{TICKER_LOWER}_strategy_{source_id}.txt`
> - Structured output: `data/processed/{TICKER}/{DATE}/stage_1a_strategy.json`

### Agent: `execution-intel`

**Instructions:**
> You are the execution-intel agent for the Strategy Drift Detector.
>
> **Company:** {COMPANY} ({EXCHANGE}: {TICKER})
> **CEO:** {CEO} | **CFO:** {CFO}
> **Business Segments:** {SEGMENTS}
> **Company Context:** Read `data/processed/{TICKER}/{DATE}/company_context.json`
>
> **Your tasks (sequential):**
>
> **Task A — Stage 1B:** Execute Action and Execution Evidence Extraction.
> Read `prompts/01_gather_actions.md`. Use source catalog at `data/processed/{TICKER}/{DATE}/stage_0_sources.md`.
> Output: `data/raw/{TICKER}/{DATE}/{TICKER_LOWER}_actions_{source_id}.txt` + `data/processed/{TICKER}/{DATE}/stage_1b_actions.json`
>
> **Task B — Stage 1C:** Execute Forward-Looking Commitment Extraction.
> Read `prompts/01_gather_commitments.md`. Use same source catalog.
> Output: `data/raw/{TICKER}/{DATE}/{TICKER_LOWER}_commitments_{source_id}.txt` + `data/processed/{TICKER}/{DATE}/stage_1c_commitments.json`

### Quality Gate 2

**Interactive mode:** Display to user:
- Count of STR-*, ACT-*, CMT-* elements extracted
- Data sufficiency assessment
- Ask: "Data gathering complete. Proceed to Wave 3?"

**Auto mode:** Lead agent reviews element counts. If minimums not met (per prompt requirements), message agents to gather more. Otherwise proceed.

Write `data/processed/{TICKER}/{DATE}/source_sufficiency_assessment.md`.

## Step 7: Wave 3 — Analysis (Parallel)

### Agent: `strategy-intel` (reuse)

**Instructions via SendMessage:**
> Proceed to Stage 2 — Strategic Pillar Synthesis.
> Read `prompts/02_map_pillars.md`.
> Inputs: `data/processed/{TICKER}/{DATE}/stage_1a_strategy.json` + `data/processed/{TICKER}/{DATE}/stage_1c_commitments.json`
> Output: `data/processed/{TICKER}/{DATE}/stage_2_pillars.json`

### Agent: `execution-intel` (reuse, after Stage 2 pillars are ready)

**Instructions via SendMessage:**
> Proceed to Stage 3 — Action and Commitment to Pillar Mapping.
> Read `prompts/03_map_actions.md`.
> Inputs: `data/processed/{TICKER}/{DATE}/stage_2_pillars.json` + `data/processed/{TICKER}/{DATE}/stage_1b_actions.json` + `data/processed/{TICKER}/{DATE}/stage_1c_commitments.json`
> Output: `data/processed/{TICKER}/{DATE}/stage_3_actions.json`

### Quality Gate 3

**Interactive mode:** Display pillar names, priority ranks, and action mapping summary. Ask: "Analysis looks good. Proceed to final synthesis?"

**Auto mode:** Lead verifies pillar count >= 2 and action mappings exist. Proceed.

## Step 8: Wave 4 — Synthesis (Sequential)

### Agent: `drift-analyst`

**Instructions:**
> You are the drift-analyst agent for the Strategy Drift Detector.
>
> **Company:** {COMPANY} ({EXCHANGE}: {TICKER})
> **Company Context:** Read `data/processed/{TICKER}/{DATE}/company_context.json`
>
> **Task A — Stage 4:** Execute Multi-Dimensional Coherence Analysis.
> Read `prompts/04_coherence_analysis.md`.
> Inputs: ALL files in `data/processed/{TICKER}/{DATE}/` (stages 0-3).
> Output: `data/processed/{TICKER}/{DATE}/stage_4_coherence.json`
>
> **Task B — Stage 5:** Generate Final Report.
> Read `prompts/05_final_report.md`.
> Inputs: ALL files in `data/processed/{TICKER}/{DATE}/` (stages 0-4).
> Output: `data/processed/{TICKER}/{DATE}/final_report.md`
>
> **Task C — HTML Generation:** Convert final_report.md into a styled HTML file.
> Output: `data/processed/{TICKER}/{DATE}/final_report.html`
> Use clean, professional styling with a serif font for body text, tables with borders, and a navigation sidebar. Include the company name and date in the header.

### QA Review: `prompt-engineer` (reuse)

**Instructions via SendMessage:**
> Review the final report at `data/processed/{TICKER}/{DATE}/final_report.md`.
> Check for:
> - Academic language throughout (no marketing speak)
> - Every claim has source citation (S-*, STR-*, ACT-*, CMT-*)
> - Bias acknowledgments present per finding
> - Limitations honestly stated
> - Scoring methodology consistently applied
> - Pillar IDs used consistently
> - Shadow strategies identified (if any)
>
> Write your review to `data/processed/{TICKER}/{DATE}/qa_review.md`.
> If critical issues found, report them so drift-analyst can revise.

### Quality Gate 4 (always interactive)

Display QA review summary to user regardless of mode.

## Step 9: Cleanup & Report

1. Display final summary:
   - Company analyzed
   - Overall coherence score and classification
   - Top 3 drift flags
   - Path to full report: `data/processed/{TICKER}/{DATE}/final_report.md`
   - Path to HTML: `data/processed/{TICKER}/{DATE}/final_report.html`

2. Clean up agent team:
   ```
   TeamDelete → team_name: "drift-{TICKER_LOWER}"
   ```

3. Offer to commit all outputs:
   ```
   git add data/processed/{TICKER}/{DATE}/ data/raw/{TICKER}/{DATE}/
   git commit -m "feat: strategy drift analysis for {COMPANY} ({TICKER})"
   ```
```

**Step 3: Commit**

```bash
git add .claude/skills/analyze-drift/SKILL.md
git commit -m "feat: add /analyze-drift skill for any ticker"
```

---

## Task 10: Update Execution Plan for Reusability

**Files:**
- Modify: `docs/plans/2026-02-28-strategy-drift-detector.md`

**Step 1: Add note at top of file**

Add after the first line:

```markdown
> **Note:** This plan was originally written for Block, Inc. For reusable execution, use `/analyze-drift TICKER` which automates this entire pipeline for any company. See `.claude/skills/analyze-drift/SKILL.md`.
```

**Step 2: Commit**

```bash
git add docs/plans/2026-02-28-strategy-drift-detector.md
git commit -m "docs: add reusability note to original execution plan"
```

---

## Task 11: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Add skill documentation**

Add a new section after "## Commands":

```markdown
## Skills (Slash Commands)

### `/analyze-drift TICKER [--auto]`

Run the full Strategy Drift Detection pipeline for any public company.

- `TICKER` — stock ticker symbol (e.g., `SQ`, `PAX`, `AAPL`)
- `--auto` — optional flag for fire-and-forget mode (quality gates validated automatically)
- Without `--auto` — interactive mode, pauses at each quality gate for user approval

Output: `data/processed/{TICKER}/{YYYY-MM-DD}/final_report.md` + `final_report.html`
```

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: document /analyze-drift skill in CLAUDE.md"
```

---

## Task 12: Smoke Test

**Step 1: Verify skill is discoverable**

In Claude Code, type `/analyze-drift` and verify the skill appears in autocomplete.

**Step 2: Dry run with a ticker**

Run `/analyze-drift SQ` and verify:
1. Directory `data/processed/SQ/{DATE}/` is created
2. `company_context.json` is generated with correct Block, Inc. info
3. Agent team `drift-sq` is created
4. Wave 1 agents are spawned correctly
5. Quality gate 1 pauses for input (interactive mode)

**Step 3: Verify prompt placeholders**

Run: `grep -rn "Block\|Jack Dorsey\|Cash App\|Square/Seller\|TIDAL" prompts/`
Expected: No matches (all parameterized).

---

## Summary of Commits

| # | Message |
|---|---------|
| 1 | `feat: parameterize source mapping prompt for any company` |
| 2 | `feat: parameterize strategy gathering prompt for any company` |
| 3 | `feat: parameterize actions gathering prompt for any company` |
| 4 | `feat: parameterize commitments gathering prompt for any company` |
| 5 | `feat: parameterize pillar mapping prompt for any company` |
| 6 | `feat: parameterize action mapping prompt for any company` |
| 7 | `feat: parameterize coherence analysis prompt for any company` |
| 8 | `feat: parameterize final report prompt for any company` |
| 9 | `feat: add /analyze-drift skill for any ticker` |
| 10 | `docs: add reusability note to original execution plan` |
| 11 | `docs: document /analyze-drift skill in CLAUDE.md` |
| 12 | Smoke test (no commit) |
