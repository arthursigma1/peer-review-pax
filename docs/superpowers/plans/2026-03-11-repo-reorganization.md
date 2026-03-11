# Repository Reorganization Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reorganize the repository filesystem (data, prompts, docs, root files), update all references, and rewrite the README professionally.

**Architecture:** Archive-based approach — legacy content moves to `archive/`, nothing is deleted. File moves happen first, then all path references are updated in CLAUDE.md, skill files, prompts, and Tauri source. README is rewritten from scratch.

**Tech Stack:** Shell (mv/mkdir), markdown, grep for verification

**Spec:** `docs/superpowers/specs/2026-03-11-repo-reorganization-design.md`

---

## Chunk 1: File Moves

### Task 1: Create directory scaffolding

**Files:**
- Create directories: `archive/`, `archive/data/raw/pax/`, `archive/data/processed/`, `archive/data/processed/pax/`, `archive/docs/`, `archive/schemas/vda/`, `data/raw/block/`, `data/processed/block/`, `data/raw/pax/drift/`, `data/processed/pax/drift/`, `prompts/drift/`, `docs/methodology/`, `docs/vda/`, `docs/pax/`

- [ ] **Step 1: Create all destination directories**

```bash
mkdir -p archive/data/raw/pax archive/data/processed/pax archive/docs archive/schemas/vda
mkdir -p data/raw/block data/processed/block
mkdir -p data/raw/pax/drift data/processed/pax/drift
mkdir -p prompts/drift
mkdir -p docs/methodology docs/vda docs/pax
```

- [ ] **Step 2: Verify directories exist**

Run: `ls -d archive/ data/raw/block/ data/processed/block/ data/raw/pax/drift/ data/processed/pax/drift/ prompts/drift/ docs/methodology/ docs/vda/ docs/pax/`
Expected: All directories listed without error

- [ ] **Step 3: Commit**

```bash
git add archive/.gitkeep 2>/dev/null; touch archive/.gitkeep && git add archive/.gitkeep
git commit -m "chore: create directory scaffolding for repo reorganization"
```

### Task 2: Move Block data files

**Files:**
- Move: `data/raw/block_*` → `data/raw/block/`
- Move: `data/processed/stage_*`, `data/processed/final_report.md`, `data/processed/qa_review.md`, `data/processed/source_sufficiency_assessment.md` → `data/processed/block/`

- [ ] **Step 1: Move Block raw data**

```bash
mv data/raw/block_actions_S-*.txt data/raw/block/
mv data/raw/block_strategy_S-*.txt data/raw/block/
mv data/raw/block_commitments_S-*.txt data/raw/block/
```

- [ ] **Step 2: Move Block processed data**

```bash
mv data/processed/stage_0_sources.md data/processed/block/
mv data/processed/stage_1a_strategy.json data/processed/block/
mv data/processed/stage_1b_actions.json data/processed/block/
mv data/processed/stage_1c_commitments.json data/processed/block/
mv data/processed/stage_2_pillars.json data/processed/block/
mv data/processed/stage_3_actions.json data/processed/block/
mv data/processed/stage_4_coherence.json data/processed/block/
mv data/processed/final_report.md data/processed/block/
mv data/processed/qa_review.md data/processed/block/
mv data/processed/source_sufficiency_assessment.md data/processed/block/
```

- [ ] **Step 3: Verify**

Run: `ls data/raw/block/ && ls data/processed/block/`
Expected: All block files present in their new locations. No `block_*` or `stage_*` files left in `data/raw/` or `data/processed/` roots.

- [ ] **Step 4: Commit**

```bash
git add data/raw/block/ data/processed/block/
git add -u data/raw/ data/processed/
git commit -m "chore: move Block data into data/raw/block/ and data/processed/block/"
```

### Task 3: Move PAX drift files

**Files:**
- Move: `data/raw/pax/pax_actions_S-*.txt` → `data/raw/pax/drift/`
- Move: `data/processed/pax/stage_*`, `data/processed/pax/final_report.md`, `data/processed/pax/source_sufficiency_assessment.md`, `data/processed/pax/peer_p0_*`, `data/processed/pax/peer_p1_*` → `data/processed/pax/drift/`
- Move: `data/processed/final_report_patria.html` → `data/processed/pax/drift/`

- [ ] **Step 1: Move PAX drift raw data**

```bash
mv data/raw/pax/pax_actions_S-*.txt data/raw/pax/drift/
```

- [ ] **Step 2: Move PAX drift processed data**

```bash
mv data/processed/pax/stage_0_sources.md data/processed/pax/drift/
mv data/processed/pax/stage_1a_strategy.json data/processed/pax/drift/
mv data/processed/pax/stage_1b_actions.json data/processed/pax/drift/
mv data/processed/pax/stage_1c_commitments.json data/processed/pax/drift/
mv data/processed/pax/stage_2_pillars.json data/processed/pax/drift/
mv data/processed/pax/stage_3_actions.json data/processed/pax/drift/
mv data/processed/pax/stage_4_coherence.json data/processed/pax/drift/
mv data/processed/pax/final_report.md data/processed/pax/drift/
mv data/processed/pax/source_sufficiency_assessment.md data/processed/pax/drift/
mv data/processed/pax/peer_p0_identification.json data/processed/pax/drift/
mv data/processed/pax/peer_p0_metrics.json data/processed/pax/drift/
mv data/processed/pax/peer_p0_sources.md data/processed/pax/drift/
mv data/processed/pax/peer_p1_data.json data/processed/pax/drift/
mv data/processed/final_report_patria.html data/processed/pax/drift/
```

- [ ] **Step 3: Verify**

Run: `ls data/raw/pax/drift/ && ls data/processed/pax/drift/`
Expected: All drift files present. No `stage_*` or `peer_*` files left in `data/processed/pax/` root. No `pax_actions_*` in `data/raw/pax/` root.

- [ ] **Step 4: Commit**

```bash
git add data/raw/pax/drift/ data/processed/pax/drift/
git add -u data/raw/pax/ data/processed/pax/ data/processed/
git commit -m "chore: move PAX drift data into drift/ subdirectories"
```

### Task 4: Archive empty runs and stubs

**Files:**
- Move: 7 empty raw dirs → `archive/data/raw/pax/`
- Move: `data/processed/paxn/` → `archive/data/processed/`
- Move: `data/processed/pax/2026-03-10/`, `data/processed/pax/2026-03-10-run3/` → `archive/data/processed/pax/`

- [ ] **Step 1: Archive empty raw runs**

```bash
mv data/raw/pax/2026-03-07-run2 archive/data/raw/pax/
mv data/raw/pax/2026-03-07-run3 archive/data/raw/pax/
mv data/raw/pax/2026-03-07-run4 archive/data/raw/pax/
mv data/raw/pax/2026-03-08 archive/data/raw/pax/
mv data/raw/pax/2026-03-08-run2 archive/data/raw/pax/
mv data/raw/pax/2026-03-09 archive/data/raw/pax/
mv data/raw/pax/2026-03-09-run3 archive/data/raw/pax/
```

- [ ] **Step 2: Archive empty/stub processed dirs**

```bash
mv data/processed/paxn archive/data/processed/
mv data/processed/pax/2026-03-10 archive/data/processed/pax/
mv data/processed/pax/2026-03-10-run3 archive/data/processed/pax/
```

- [ ] **Step 3: Verify no empty dirs remain**

Run: `ls data/raw/pax/ | head -20 && echo "---" && ls data/processed/pax/ | head -20`
Expected: No empty run dirs in data/raw/pax/. No stub dirs or `paxn/` in data/processed/.

- [ ] **Step 4: Commit**

```bash
git add archive/data/
git add -u data/
git commit -m "chore: archive empty and stub pipeline runs"
```

### Task 5: Move drift prompts

**Files:**
- Move: `prompts/0*.md` → `prompts/drift/`

- [ ] **Step 1: Move prompt files**

```bash
mv prompts/00_source_mapping.md prompts/drift/
mv prompts/01_gather_actions.md prompts/drift/
mv prompts/01_gather_commitments.md prompts/drift/
mv prompts/01_gather_strategy.md prompts/drift/
mv prompts/02_map_pillars.md prompts/drift/
mv prompts/03_map_actions.md prompts/drift/
mv prompts/04_coherence_analysis.md prompts/drift/
mv prompts/05_final_report.md prompts/drift/
```

- [ ] **Step 2: Verify**

Run: `ls prompts/drift/ && ls prompts/`
Expected: 8 files in `prompts/drift/`. Root `prompts/` should only have `.gitkeep`, `drift/`, `peer/`, `vda/`.

- [ ] **Step 3: Commit**

```bash
git add prompts/drift/
git add -u prompts/
git commit -m "chore: move drift prompts into prompts/drift/"
```

### Task 6: Move docs to subdirectories

**Files:**
- Move: methodology docs → `docs/methodology/`
- Move: VDA reference docs → `docs/vda/`
- Move: PAX-specific docs → `docs/pax/`

- [ ] **Step 1: Move methodology docs**

```bash
mv docs/strategy-drift-methodology.md docs/methodology/
mv docs/peer-comparison-methodology.md docs/methodology/
mv docs/pax-first-valuation-driver-methodology.md docs/methodology/
mv docs/drift-scoring-framework.md docs/methodology/
```

- [ ] **Step 2: Move VDA reference docs**

```bash
mv docs/vda-correlation-classification.md docs/vda/
mv docs/vda-consulting-evidence-hierarchy.md docs/vda/
mv docs/vda-agent-orchestration.md docs/vda/
mv docs/vda-repository-drift-audit.md docs/vda/
mv docs/sigma-final-report-guide.md docs/vda/
```

- [ ] **Step 3: Move PAX-specific docs**

```bash
mv docs/pax-peer-assessment-framework.md docs/pax/
mv docs/pax-peer-strategy-ontology.md docs/pax/
```

- [ ] **Step 4: Verify**

Run: `ls docs/methodology/ && echo "---" && ls docs/vda/ && echo "---" && ls docs/pax/`
Expected: 4 files in methodology, 5 in vda, 2 in pax.

- [ ] **Step 5: Commit**

```bash
git add docs/methodology/ docs/vda/ docs/pax/
git add -u docs/
git commit -m "chore: organize docs into methodology/, vda/, pax/ subdirectories"
```

### Task 7: Archive legacy docs, root files, and schemas

**Files:**
- Move: `docs/FILESYSTEM.md`, `docs/PRESENTATION-INSTRUCTIONS.md`, `docs/valuation-driver-methodology.md`, `docs/valuation-driver-methodology.html` → `archive/docs/`
- Move: `PLAN.md` → `archive/`
- Move: `schemas/vda/` → `archive/schemas/vda/`

- [ ] **Step 1: Archive legacy docs**

```bash
mv docs/FILESYSTEM.md archive/docs/
mv docs/PRESENTATION-INSTRUCTIONS.md archive/docs/
mv docs/valuation-driver-methodology.md archive/docs/
mv docs/valuation-driver-methodology.html archive/docs/
```

- [ ] **Step 2: Archive root PLAN.md**

```bash
mv PLAN.md archive/
```

- [ ] **Step 3: Archive schemas and remove empty dir**

```bash
mv schemas/vda/*.schema.json archive/schemas/vda/
rmdir schemas/vda
rmdir schemas
```

- [ ] **Step 4: Verify**

Run: `ls archive/docs/ && ls archive/schemas/vda/ && ls archive/PLAN.md && test ! -d schemas && echo "schemas/ removed"`
Expected: 4 docs in archive/docs/, 7 schemas in archive/schemas/vda/, PLAN.md in archive/, schemas/ directory gone.

- [ ] **Step 5: Commit**

```bash
git add archive/
git add -u docs/ schemas/ PLAN.md
git commit -m "chore: archive legacy docs, PLAN.md, and standalone schemas"
```

---

## Chunk 2: Reference Updates

### Task 8: Update analyze-drift SKILL.md references

The analyze-drift skill references `prompts/0X_*.md` at runtime. These must point to `prompts/drift/0X_*.md`.

**Files:**
- Modify: `.claude/skills/analyze-drift/SKILL.md`

- [ ] **Step 1: Identify all prompt path references**

Run: `grep -n "prompts/0[0-5]_" .claude/skills/analyze-drift/SKILL.md`
Expected: ~8 hits at lines 122, 167, 190, 194, 212, 221, 244, 249

- [ ] **Step 2: Update references**

Replace all occurrences of `prompts/0` with `prompts/drift/0` in `.claude/skills/analyze-drift/SKILL.md`.

- [ ] **Step 3: Verify**

Run: `grep -c "prompts/drift/0" .claude/skills/analyze-drift/SKILL.md`
Expected: 8 hits, zero hits for the old pattern `prompts/0[0-5]_` (excluding `prompts/drift/`).

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/analyze-drift/SKILL.md
git commit -m "chore: update analyze-drift skill prompt paths to prompts/drift/"
```

### Task 9: Update valuation-driver SKILL.md references

The VDA skill references `docs/sigma-final-report-guide.md`, `docs/pax-peer-*`, and `schemas/vda/` at runtime.

**Files:**
- Modify: `.claude/skills/valuation-driver/SKILL.md`

- [ ] **Step 1: Identify all references that need updating**

Run: `grep -n "docs/sigma-final-report-guide\|docs/pax-peer\|schemas/vda/" .claude/skills/valuation-driver/SKILL.md`
Expected: ~12 hits across multiple lines

- [ ] **Step 2: Update sigma-final-report-guide references**

Replace all `docs/sigma-final-report-guide.md` with `docs/vda/sigma-final-report-guide.md` in `.claude/skills/valuation-driver/SKILL.md`.

- [ ] **Step 3: Update pax-peer references**

Replace all `docs/pax-peer-assessment-framework.md` with `docs/pax/pax-peer-assessment-framework.md`.
Replace all `docs/pax-peer-strategy-ontology.md` with `docs/pax/pax-peer-strategy-ontology.md`.

- [ ] **Step 4: Update schemas/vda references**

Replace all `schemas/vda/` with `archive/schemas/vda/` — or remove references entirely if they are only informational. Check each occurrence: if it instructs an agent to "conform to schema", it's informational (the schema is not loaded at runtime; `vda_contracts.py` handles validation). Replace with a note pointing to `src/validation/vda_contracts.py` instead.

- [ ] **Step 5: Update pax-first-valuation-driver-methodology references**

Replace all `docs/pax-first-valuation-driver-methodology.md` with `docs/methodology/pax-first-valuation-driver-methodology.md`.

- [ ] **Step 6: Verify**

Run: `grep -c "docs/sigma-final-report-guide[^/]" .claude/skills/valuation-driver/SKILL.md` → 0
Run: `grep -c "docs/pax-peer-" .claude/skills/valuation-driver/SKILL.md` → 0
Run: `grep -c "schemas/vda/" .claude/skills/valuation-driver/SKILL.md` → 0

- [ ] **Step 7: Commit**

```bash
git add .claude/skills/valuation-driver/SKILL.md
git commit -m "chore: update valuation-driver skill doc and schema references"
```

### Task 10: Update consistency-check SKILL.md references

**Files:**
- Modify: `.claude/skills/consistency-check/SKILL.md`

- [ ] **Step 1: Identify references**

Run: `grep -n "docs/pax-first-valuation\|docs/sigma-final\|docs/strategy-drift\|docs/peer-comparison\|docs/drift-scoring\|docs/vda-" .claude/skills/consistency-check/SKILL.md`

- [ ] **Step 2: Update all doc path references**

Apply the same path transformations:
- `docs/pax-first-valuation-driver-methodology.md` → `docs/methodology/pax-first-valuation-driver-methodology.md`
- `docs/sigma-final-report-guide.md` → `docs/vda/sigma-final-report-guide.md`
- `docs/strategy-drift-methodology.md` → `docs/methodology/strategy-drift-methodology.md`
- `docs/drift-scoring-framework.md` → `docs/methodology/drift-scoring-framework.md`
- `docs/vda-*` → `docs/vda/vda-*`
- `docs/pax-peer-*` → `docs/pax/pax-peer-*`

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/consistency-check/SKILL.md
git commit -m "chore: update consistency-check skill doc references"
```

### Task 11: Update prompts references

**Files:**
- Modify: `prompts/vda/claim_auditor.md` — update `docs/pax-peer-*` references (7 occurrences)
- Modify: `prompts/peer/p02_source_mapping.md` — update `prompts/00_source_mapping.md` reference
- Modify: `prompts/drift/01_gather_strategy.md`, `prompts/drift/02_map_pillars.md`, etc. — self-references in methodology strings (leave as-is — these are embedded in historical output JSON, not runtime paths)

- [ ] **Step 1: Update claim_auditor.md**

Replace all `docs/pax-peer-assessment-framework.md` with `docs/pax/pax-peer-assessment-framework.md`.
Replace all `docs/pax-peer-strategy-ontology.md` with `docs/pax/pax-peer-strategy-ontology.md`.

- [ ] **Step 2: Update p02_source_mapping.md**

Replace `prompts/00_source_mapping.md` with `prompts/drift/00_source_mapping.md`.

- [ ] **Step 3: Verify**

Run: `grep -c "docs/pax-peer-" prompts/vda/claim_auditor.md` → 0
Run: `grep "prompts/00_" prompts/peer/p02_source_mapping.md` → 0

- [ ] **Step 4: Commit**

```bash
git add prompts/vda/claim_auditor.md prompts/peer/p02_source_mapping.md
git commit -m "chore: update prompt file doc and path references"
```

### Task 12: Update Tauri AgentsOrg.tsx references

**Files:**
- Modify: `src/tauri/src/components/AgentsOrg.tsx`

- [ ] **Step 1: Identify references**

Run: `grep -n "docs/pax-peer\|docs/pax-first" src/tauri/src/components/AgentsOrg.tsx`
Expected: ~10 hits in input_files arrays

- [ ] **Step 2: Update references**

Replace all `docs/pax-peer-assessment-framework.md` with `docs/pax/pax-peer-assessment-framework.md`.
Replace all `docs/pax-peer-strategy-ontology.md` with `docs/pax/pax-peer-strategy-ontology.md`.
Replace all `docs/pax-first-valuation-driver-methodology.md` with `docs/methodology/pax-first-valuation-driver-methodology.md`.

- [ ] **Step 3: Verify**

Run: `grep -c "docs/pax-peer-" src/tauri/src/components/AgentsOrg.tsx` → 0
Run: `grep -c "docs/pax-first-valuation" src/tauri/src/components/AgentsOrg.tsx` → should show `docs/methodology/pax-first-valuation`

- [ ] **Step 4: Commit**

```bash
git add src/tauri/src/components/AgentsOrg.tsx
git commit -m "chore: update AgentsOrg.tsx doc path references"
```

### Task 13: Update docs cross-references

Some docs reference each other and those paths have changed.

**Files:**
- Modify: `docs/methodology/pax-first-valuation-driver-methodology.md` — references `docs/pax-peer-*` and `schemas/vda/`
- Modify: `docs/pax/pax-peer-assessment-framework.md` — references `docs/pax-peer-strategy-ontology.md` and `docs/pax-first-valuation-driver-methodology.md`
- Modify: `docs/methodology/strategy-drift-methodology.md` — references `docs/peer-comparison-methodology.md`
- Modify: `docs/vda/vda-repository-drift-audit.md` — references `docs/pax-first-*`, `schemas/vda/`

- [ ] **Step 1: Update pax-first-valuation-driver-methodology.md**

Replace `docs/pax-peer-assessment-framework.md` with `docs/pax/pax-peer-assessment-framework.md`.
Replace `docs/pax-peer-strategy-ontology.md` with `docs/pax/pax-peer-strategy-ontology.md`.
Replace `schemas/vda/` references — note these now live at `archive/schemas/vda/` but since the methodology doc is a reference document, update to say "archived at `archive/schemas/vda/`; runtime validation is in `src/validation/vda_contracts.py`".

- [ ] **Step 2: Update pax-peer-assessment-framework.md**

Replace `docs/pax-peer-strategy-ontology.md` with `docs/pax/pax-peer-strategy-ontology.md`.
Replace `docs/pax-first-valuation-driver-methodology.md` with `docs/methodology/pax-first-valuation-driver-methodology.md`.

- [ ] **Step 3: Update strategy-drift-methodology.md**

Replace `docs/peer-comparison-methodology.md` with `docs/methodology/peer-comparison-methodology.md`.

- [ ] **Step 4: Update vda-repository-drift-audit.md**

Replace `docs/pax-first-valuation-driver-methodology.md` with `docs/methodology/pax-first-valuation-driver-methodology.md`.
Replace `schemas/vda/` with `archive/schemas/vda/`.

- [ ] **Step 5: Commit**

```bash
git add docs/methodology/ docs/pax/ docs/vda/
git commit -m "chore: update docs cross-references for new directory structure"
```

### Task 14: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update Key Directories section**

Update the Key Directories list:
- `prompts/` description → mention `prompts/drift/` for drift templates
- `docs/strategy-drift-methodology.md` → `docs/methodology/strategy-drift-methodology.md`
- `docs/peer-comparison-methodology.md` → `docs/methodology/peer-comparison-methodology.md`
- `docs/pax-first-valuation-driver-methodology.md` → `docs/methodology/pax-first-valuation-driver-methodology.md`
- `docs/vda-repository-drift-audit.md` → `docs/vda/vda-repository-drift-audit.md`
- `docs/valuation-driver-methodology.md` → note as archived at `archive/docs/`
- `docs/sigma-final-report-guide.md` → `docs/vda/sigma-final-report-guide.md`

- [ ] **Step 2: Update Reference Docs section**

- `docs/drift-scoring-framework.md` → `docs/methodology/drift-scoring-framework.md`
- `docs/vda-correlation-classification.md` → `docs/vda/vda-correlation-classification.md`
- `docs/vda-consulting-evidence-hierarchy.md` → `docs/vda/vda-consulting-evidence-hierarchy.md`
- `docs/vda-agent-orchestration.md` → `docs/vda/vda-agent-orchestration.md`

- [ ] **Step 3: Update Architecture section — Strategy Drift Pipeline description**

Update any mention of `prompts/` for drift to say `prompts/drift/`.

- [ ] **Step 4: Update VDA methodology reference**

- `docs/pax-first-valuation-driver-methodology.md` → `docs/methodology/pax-first-valuation-driver-methodology.md`
- Remove or update the `docs/valuation-driver-methodology.md` reference (now archived)

- [ ] **Step 5: Verify**

Run: `grep -n "docs/strategy-drift-methodology[^/]" CLAUDE.md` → 0
Run: `grep -n "docs/sigma-final-report-guide[^/]" CLAUDE.md` → 0
Run: `grep -n "docs/vda-correlation" CLAUDE.md` → should all show `docs/vda/vda-correlation`

- [ ] **Step 6: Commit**

```bash
git add CLAUDE.md
git commit -m "chore: update CLAUDE.md path references for new directory structure"
```

### Task 15: Post-move verification

- [ ] **Step 1: Run verification greps**

```bash
# These should return zero hits outside archive/ and docs/superpowers/ (specs/plans are historical)
grep -r "docs/pax-peer-" . --include="*.md" --include="*.py" --include="*.ts" --include="*.tsx" --include="*.rs" | grep -v archive/ | grep -v docs/superpowers/ | grep -v docs/plans/ | grep -v node_modules/
grep -r "docs/sigma-final-report-guide[^/]" . --include="*.md" --include="*.py" --include="*.ts" | grep -v archive/ | grep -v docs/superpowers/ | grep -v docs/plans/ | grep -v node_modules/
grep -r "docs/strategy-drift-methodology[^/]" . --include="*.md" --include="*.py" --include="*.ts" | grep -v archive/ | grep -v docs/superpowers/ | grep -v docs/plans/ | grep -v node_modules/
grep -r "schemas/vda/" . --include="*.md" --include="*.py" --include="*.ts" | grep -v archive/ | grep -v docs/superpowers/ | grep -v docs/plans/ | grep -v node_modules/
grep -r "prompts/0[0-5]_" . --include="*.md" --include="*.py" --include="*.ts" | grep -v archive/ | grep -v docs/superpowers/ | grep -v docs/plans/ | grep -v node_modules/ | grep -v "prompts/drift/"
```

Expected: All return empty (no stale references in active files). Historical references in `docs/plans/` and `docs/superpowers/specs/` are acceptable — they document past states.

- [ ] **Step 2: Verify no self-references broken in moved prompt files**

```bash
# Prompt files reference themselves in methodology strings embedded in JSON examples.
# These are output templates, not runtime paths, so the old paths in the methodology
# strings are correct (they describe what prompt generated the data).
grep -n "prompts/" prompts/drift/*.md
```

Expected: Self-references like `"methodology": "... per prompts/01_gather_strategy.md"` are fine — these are output metadata strings, not runtime file reads.

- [ ] **Step 3: Fix any stale references found**

If Step 1 found any hits, update them following the same path transformation rules.

---

## Chunk 3: README Rewrite

### Task 16: Rewrite README.md

**Files:**
- Rewrite: `README.md`

The README should be a professional product README. Reference the current `README.md` for content to preserve (statistical methodology, usage commands), but restructure completely.

**Important context for the README:**
- Read `CLAUDE.md` for authoritative architecture/conventions
- Read `src/tauri/src-tauri/tauri.conf.json` for app metadata
- Read `requirements.txt` for Python dependencies
- Read `src/tauri/package.json` for frontend dependencies

- [ ] **Step 1: Read current state for reference**

Read: `CLAUDE.md`, `requirements.txt`, `src/tauri/package.json`

- [ ] **Step 2: Write the new README**

Structure:
1. **Title + one-line description** — Strategy Intelligence System
2. **What it does** — 2-3 paragraph overview: VDA as flagship, what it produces (HTML decision memos for board governance), anti-hallucination fact-checking, drift and peer as complementary pipelines
3. **VDA Pipeline** — the 5-step pipeline with agent table, input/output per step
4. **Fact Checker** — 3-checkpoint claim verification (keep existing content, it's good)
5. **Desktop Dashboard** — Tauri app description with terminal, agent cards, results browser
6. **Architecture** — Updated directory tree reflecting new structure
7. **Tech Stack** — Full table including: Python 3.11, Crawlee + Playwright (web crawling), Anthropic SDK (LLM), Tauri 2.0 + Rust (desktop), React + TypeScript + Tailwind (frontend), xterm.js + portable-pty (terminal), marker-pdf (document conversion)
8. **Source Tooling** — `src/analyzer/` modules, `src/ingestion/` crawlers, `src/report/` validation, `src/validation/` contracts
9. **Usage** — Slash commands, crawler, data quality tools, dashboard
10. **Statistical Methodology** — Spearman, BH FDR, Bonferroni (keep existing)
11. **Reuse for Another Company** — ticker replacement
12. **Project Status** — Active development, PAX VDA primary use case

- [ ] **Step 3: Verify README renders**

Visually review the markdown structure: headings, tables, code blocks, links.

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: rewrite README as professional product documentation"
```

### Task 17: Update MEMORY.md

**Files:**
- Modify: `.claude/projects/-Users-arthurhrk-Documents-GitHub-peer-review-pax/memory/MEMORY.md`

- [ ] **Step 1: Update any memory entries that reference old paths**

Check if any memory files reference the old directory structure and update them.

- [ ] **Step 2: Commit if changes were made**

```bash
git add .claude/
git commit -m "chore: update memory references for new directory structure"
```

### Task 18: Final verification

- [ ] **Step 1: Run git status to confirm clean state**

Run: `git status`
Expected: Clean working tree (all changes committed).

- [ ] **Step 2: Run a quick test to verify nothing broke**

```bash
python -m pytest tests/ -x -q --timeout=30 2>&1 | tail -20
```

Expected: Tests pass (or fail for pre-existing reasons unrelated to file moves — the tests don't reference docs paths).

- [ ] **Step 3: Verify directory structure matches spec**

```bash
echo "=== prompts ===" && ls prompts/
echo "=== docs ===" && ls docs/
echo "=== data/raw ===" && ls data/raw/
echo "=== data/processed root ===" && ls data/processed/ | head -5
echo "=== data/processed/pax ===" && ls data/processed/pax/ | head -10
echo "=== archive ===" && find archive -maxdepth 3 -type d
```

Expected: Structure matches the spec diagram.
