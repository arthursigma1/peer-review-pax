# Repository Reorganization — Design Spec

**Date:** 2026-03-11
**Scope:** Full repository cleanup — data, prompts, docs, root files, README rewrite
**Principle:** Nothing is deleted. Legacy content moves to `archive/`. Active code untouched.

---

## 1. `data/` Reorganization

### 1.1 Block gets its own ticker directories

| Current location | New location |
|---|---|
| `data/raw/block_actions_S-*.txt` | `data/raw/block/` |
| `data/raw/block_strategy_S-*.txt` | `data/raw/block/` |
| `data/raw/block_commitments_S-*.txt` | `data/raw/block/` |
| `data/processed/stage_0_sources.md` | `data/processed/block/` |
| `data/processed/stage_1a_strategy.json` | `data/processed/block/` |
| `data/processed/stage_1b_actions.json` | `data/processed/block/` |
| `data/processed/stage_1c_commitments.json` | `data/processed/block/` |
| `data/processed/stage_2_pillars.json` | `data/processed/block/` |
| `data/processed/stage_3_actions.json` | `data/processed/block/` |
| `data/processed/stage_4_coherence.json` | `data/processed/block/` |
| `data/processed/final_report.md` | `data/processed/block/` |
| `data/processed/qa_review.md` | `data/processed/block/` |
| `data/processed/source_sufficiency_assessment.md` | `data/processed/block/` |

### 1.2 PAX drift outputs separated from VDA

| Current location | New location |
|---|---|
| `data/raw/pax/pax_actions_S-*.txt` | `data/raw/pax/drift/` |
| `data/processed/pax/stage_0_sources.md` | `data/processed/pax/drift/` |
| `data/processed/pax/stage_1a_strategy.json` | `data/processed/pax/drift/` |
| `data/processed/pax/stage_1b_actions.json` | `data/processed/pax/drift/` |
| `data/processed/pax/stage_1c_commitments.json` | `data/processed/pax/drift/` |
| `data/processed/pax/stage_2_pillars.json` | `data/processed/pax/drift/` |
| `data/processed/pax/stage_3_actions.json` | `data/processed/pax/drift/` |
| `data/processed/pax/stage_4_coherence.json` | `data/processed/pax/drift/` |
| `data/processed/pax/final_report.md` | `data/processed/pax/drift/` |
| `data/processed/pax/source_sufficiency_assessment.md` | `data/processed/pax/drift/` |
| `data/processed/pax/peer_p0_identification.json` | `data/processed/pax/drift/` |
| `data/processed/pax/peer_p0_metrics.json` | `data/processed/pax/drift/` |
| `data/processed/pax/peer_p0_sources.md` | `data/processed/pax/drift/` |
| `data/processed/pax/peer_p1_data.json` | `data/processed/pax/drift/` |
| `data/processed/final_report_patria.html` | `data/processed/pax/drift/` |

### 1.3 Empty runs and dirs → archive

| Current location | Destination |
|---|---|
| `data/raw/pax/2026-03-07-run2/` (empty) | `archive/data/raw/pax/` |
| `data/raw/pax/2026-03-07-run3/` (empty) | `archive/data/raw/pax/` |
| `data/raw/pax/2026-03-07-run4/` (empty) | `archive/data/raw/pax/` |
| `data/raw/pax/2026-03-08/` (empty) | `archive/data/raw/pax/` |
| `data/raw/pax/2026-03-08-run2/` (empty) | `archive/data/raw/pax/` |
| `data/raw/pax/2026-03-09/` (empty) | `archive/data/raw/pax/` |
| `data/raw/pax/2026-03-09-run3/` (empty) | `archive/data/raw/pax/` |
| `data/processed/paxn/` (empty) | `archive/data/processed/` |

### 1.4 Stub runs → archive

| Current location | Status | Destination |
|---|---|---|
| `data/processed/pax/2026-03-10/` | stub (pipeline_state + session_id only) | `archive/data/processed/pax/` |
| `data/processed/pax/2026-03-10-run3/` | stub (pipeline_state + session_id only) | `archive/data/processed/pax/` |

### 1.5 Unchanged

- `data/raw/pax/canonical/`, `data/raw/pax/crawled/` — stay (VDA crawl outputs)
- `data/raw/pax/2026-03-07/`, `2026-03-09-run2/`, `2026-03-10-run2/`, `2026-03-10-run4/` — stay (runs with content)
- All other VDA runs in `data/processed/pax/2026-*` with step folders — stay (including `2026-03-07/`, `2026-03-07-run2/`, `2026-03-08/`, `2026-03-08-run2/`, `2026-03-09/`, `2026-03-09-run2/`, `2026-03-10-run2/`, `2026-03-10-run4/`, `2026-03-11-incremental-pilot/`)
- `data/processed/pax/source_inventory/` — stays
- `data/raw/pax/` PAX-specific default paths in Python code (`source_inventory/`, `canonical/`, `crawled/`) are by design and are NOT updated

---

## 2. `prompts/` Reorganization

| Current location | New location |
|---|---|
| `prompts/00_source_mapping.md` | `prompts/drift/` |
| `prompts/01_gather_actions.md` | `prompts/drift/` |
| `prompts/01_gather_commitments.md` | `prompts/drift/` |
| `prompts/01_gather_strategy.md` | `prompts/drift/` |
| `prompts/02_map_pillars.md` | `prompts/drift/` |
| `prompts/03_map_actions.md` | `prompts/drift/` |
| `prompts/04_coherence_analysis.md` | `prompts/drift/` |
| `prompts/05_final_report.md` | `prompts/drift/` |

`prompts/peer/` and `prompts/vda/` stay as-is.

---

## 3. `docs/` Reorganization

### New structure:

```
docs/
  methodology/
    strategy-drift-methodology.md
    peer-comparison-methodology.md
    pax-first-valuation-driver-methodology.md
    drift-scoring-framework.md
  vda/
    vda-correlation-classification.md
    vda-consulting-evidence-hierarchy.md
    vda-agent-orchestration.md
    vda-repository-drift-audit.md
    sigma-final-report-guide.md
  pax/
    pax-peer-assessment-framework.md
    pax-peer-strategy-ontology.md
  plans/           (stays)
  superpowers/     (stays)
  onboarding.html  (stays)
  sigma-logo.svg   (stays)
```

### Archived:

| File | Destination |
|---|---|
| `docs/FILESYSTEM.md` | `archive/docs/` |
| `docs/PRESENTATION-INSTRUCTIONS.md` | `archive/docs/` |
| `docs/valuation-driver-methodology.md` | `archive/docs/` |
| `docs/valuation-driver-methodology.html` | `archive/docs/` |

---

## 4. Root files + schemas

| Current | Destination |
|---|---|
| `PLAN.md` | `archive/` |
| `schemas/vda/*.schema.json` | `archive/schemas/vda/` |
| `schemas/` directory | removed after move (empty) |

The 7 JSON schemas in `schemas/vda/` are not loaded or imported by any runtime code. `src/validation/vda_contracts.py` embeds its own validation logic. Verified: `grep -r "schemas/vda" .` returns zero hits in Python/TS/Rust source. Safe to archive.

---

## 5. README Rewrite

Complete rewrite of `README.md` to be a professional product README:

1. **Hero** — What it is, who it's for (board/C-suite governance), what it produces
2. **Product overview** — VDA as flagship, drift and peer as complementary pipelines
3. **How it works** — Pipeline diagram, agent orchestration, fact-checking
4. **Architecture** — Updated directory tree reflecting reorganization
5. **Tech stack** — Full stack table (Python, Crawlee, Playwright, Anthropic SDK, Tauri, React, TypeScript, Tailwind, Rust, portable-pty, marker-pdf, xterm.js)
6. **Tooling** — src/analyzer modules, crawlers, report system, data quality tools
7. **Usage** — Slash commands, crawler usage, dashboard, data quality commands
8. **Statistical methodology** — Spearman, BH FDR, Bonferroni (keep existing)
9. **Reuse** — How to run for another company
10. **Project status** — Active development, current state (PAX VDA as primary use case)

---

## 6. CLAUDE.md + Skill/Prompt Reference Updates

Update all path references in CLAUDE.md to reflect new locations:
- `prompts/` description → `prompts/drift/` for drift templates
- `prompts/0X_*.md` → `prompts/drift/0X_*.md`
- `docs/strategy-drift-methodology.md` → `docs/methodology/strategy-drift-methodology.md`
- `docs/peer-comparison-methodology.md` → `docs/methodology/peer-comparison-methodology.md`
- `docs/pax-first-valuation-driver-methodology.md` → `docs/methodology/pax-first-valuation-driver-methodology.md`
- `docs/valuation-driver-methodology.md` → noted as archived
- `docs/vda-*.md` → `docs/vda/vda-*.md`
- `docs/sigma-final-report-guide.md` → `docs/vda/sigma-final-report-guide.md`
- `docs/drift-scoring-framework.md` → `docs/methodology/drift-scoring-framework.md`

Update prompt file references:
- `prompts/vda/claim_auditor.md` — update all references to `docs/pax-peer-assessment-framework.md` → `docs/pax/pax-peer-assessment-framework.md` and `docs/pax-peer-strategy-ontology.md` → `docs/pax/pax-peer-strategy-ontology.md`

Update skill file references:
- `valuation-driver/SKILL.md` — update all references to `docs/sigma-final-report-guide.md` → `docs/vda/sigma-final-report-guide.md`

---

## 7. Reference Check

Before any move, grep for hardcoded paths in:
- All Python files (`src/**/*.py`, `tests/**/*.py`)
- CLAUDE.md
- Skill files (`.claude/`) — including `review-analysis/SKILL.md` filename audit (stale canonical filenames, not just paths)
- Prompt files (`prompts/**/*.md`) — especially `prompts/vda/claim_auditor.md`
- Tauri source (`src/tauri/`)
- docs cross-references

Update any references found.

### Post-move verification

After all moves complete:
- `grep -r "docs/pax-peer" .` → should return zero hits outside archive/
- `grep -r "sigma-final-report-guide" .` → all hits should point to `docs/vda/`
- `grep -r "docs/strategy-drift-methodology" .` → all hits should point to `docs/methodology/`
- `grep -r "schemas/vda" .` → should return zero hits outside archive/

---

## What does NOT change

- `src/` code (no file moves)
- `tests/` (no file moves)
- `.gitignore`, `.env`, `requirements.txt`
- VDA runs with content in `data/processed/pax/2026-*`
- `data/raw/pax/canonical/`, `data/raw/pax/crawled/`
- `src/tauri/` (no structural changes)
- `docs/plans/`, `docs/superpowers/`
