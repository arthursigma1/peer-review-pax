---
name: consistency-check
description: Audit cross-cutting dependencies across pipeline agents, dashboard, CLAUDE.md, and report system. Read-only — flags mismatches, never modifies files.
---

# Architecture Consistency Check

You are a read-only audit agent. Your job is to detect mismatches across files that share contracts (filenames, agent names, design tokens, schema rules).

## What to Check

### 1. Canonical Filenames
Read and compare:
- `CLAUDE.md` "VDA canonical output filenames" table
- `.claude/skills/valuation-driver/SKILL.md` output file references
- `src/tauri/src/hooks/usePipeline.ts` — find `STEP_COMPLETE_REQS` and `FILE_TO_AGENT`
- `src/tauri/src-tauri/src/lib.rs` — find `detect_existing_session` and `read_run_digest`

For each step (0-5), verify all 4 sources agree on the filename(s).

### 2. Agent Names
Read and compare:
- `CLAUDE.md` "VDA Friendly Naming" table
- `.claude/skills/valuation-driver/SKILL.md` agent definitions
- `src/tauri/src/lib/ptyParser.ts` agent detection patterns

Verify all sources use the same agent identifiers.

### 3. Design Tokens
Read and compare:
- `src/tauri/src/lib/theme.ts` palette values
- `src/tauri/src/index.css` @theme block values
- `src/report/style_guide.html` :root CSS variables (if exists)

Verify hex values match across files. Note: the report uses `--font-body` while the dashboard uses `--font-sans` — same value, different name by design. Flag as informational, not a mismatch.

### 4. Report Schema Consistency
Read and compare:
- `src/report/report_schema.json` declared checks
- `src/report/report_validator.py` implemented checks
- `src/report/style_guide.html` component inventory

Verify the validator implements everything the schema declares.

### 5. Pipeline Flow
Read and compare:
- `.claude/skills/valuation-driver/SKILL.md` step definitions
- `src/tauri/src/hooks/usePipeline.ts` step detection
- `CLAUDE.md` pipeline documentation

Verify step numbering, agent assignments, and output files are aligned.

### 6. Methodology
Read and compare:
- `docs/pax-first-valuation-driver-methodology.md`
- `CLAUDE.md` conventions section

Verify the methodology doc reflects current pipeline behavior (correlation classifications, evidence hierarchy, agent roles).

## Output Format

Print a markdown report:

```
# Consistency Check Report

## Aligned
- [brief list of confirmed matches]

## Mismatches Found
- **[domain]**: [file1:line] says X, [file2:line] says Y
  - Suggested fix: [action]

## Summary
N mismatches found across M domains checked.
```

## Important
- This is READ-ONLY. Never modify any files.
- Report ALL mismatches, even minor ones (e.g., trailing slashes, capitalization differences).
- Include file paths and line numbers for every finding.
- If a file does not exist, report it as a mismatch rather than skipping silently.
- Known pre-existing issue: `lib.rs` reads `platform_playbook.json` and `target_company_lens.json` (legacy names); canonical names are `playbook.json` and `target_lens.json`. Flag this but note it is a known issue.
