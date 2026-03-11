# Play Trade-Off Intelligence Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add per-play trade-off analysis to the target-lens agent output, rendered inline in the final report via the claim evidence layer.

**Architecture:** The target-lens agent generates 1-2 trade-offs per applicable play, each grounded in evidence (driver positions, anti-patterns, target company metrics). Trade-offs are stored as a `trade_offs` array in `target_lens.json`, emitted as claims, and rendered as amber-bordered inline blocks in play cards.

**Tech Stack:** Prompt engineering (SKILL.md), JSON schema (report_schema.json), CSS/HTML (style_guide.html). No Python code changes.

**Spec:** `docs/superpowers/specs/2026-03-11-play-trade-offs-design.md`

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `src/report/report_schema.json` | Modify | Add `trade_offs` to `playbook_subsections` |
| `src/report/style_guide.html` | Modify | Add `.play-trade-off` CSS component + HTML example in play card |
| `.claude/skills/valuation-driver/SKILL.md` | Modify | Add `trade_offs` schema to target-lens output + rendering instruction to report-builder |

---

## Chunk 1: Schema + Style Guide

### Task 1: Add `trade_offs` to report_schema.json

**Files:**
- Modify: `src/report/report_schema.json:24`

- [ ] **Step 1: Add `trade_offs` to playbook_subsections array**

In `src/report/report_schema.json`, line 24, change:

```json
"playbook_subsections": ["plays", "anti_patterns", "emerging_themes", "transferability_matrix"]
```

to:

```json
"playbook_subsections": ["plays", "anti_patterns", "emerging_themes", "transferability_matrix", "trade_offs"]
```

- [ ] **Step 2: Verify JSON is valid**

Run: `python3 -c "import json; json.load(open('src/report/report_schema.json'))"`
Expected: No output (no error)

- [ ] **Step 3: Run existing tests to confirm no regressions**

Run: `python3 -m pytest tests/ -v --tb=short 2>&1 | tail -20`
Expected: All tests pass

- [ ] **Step 4: Commit**

```bash
git add src/report/report_schema.json
git commit -m "feat: add trade_offs to playbook_subsections in report schema"
```

---

### Task 2: Add `.play-trade-off` CSS to style_guide.html

**Files:**
- Modify: `src/report/style_guide.html:307-308` (insert after `.play-recommendation` closing brace)
- Modify: `src/report/style_guide.html:1589-1593` (insert trade-off example in play card HTML)

- [ ] **Step 1: Add CSS component after `.play-recommendation`**

In `src/report/style_guide.html`, insert between the closing `}` of `.play-recommendation` (line 307) and the `/* ══ COMPONENT: ANTI-PATTERN CARD ══ */` comment block (line 309). The new CSS block goes in the blank line 308:

```css

/* ── Play Trade-Off (inline within play card, between evidence and recommendation) ── */
.play-trade-off {
  border-left: 3px solid var(--color-warning);
  padding: 0.5rem 0.75rem;
  margin: 0.75rem 0;
  font-size: 0.82rem;
  line-height: 1.5;
  color: var(--color-text-secondary);
}

.play-trade-off[data-severity="high"] {
  border-left-color: var(--color-warning);
}

.play-trade-off[data-severity="medium"] {
  border-left-color: var(--color-border);
}

.play-trade-off[data-severity="low"] {
  border-left-color: var(--color-border);
}

.play-trade-off .trade-off-label {
  font-family: var(--font-mono);
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--color-warning);
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.play-trade-off[data-severity="medium"] .trade-off-label,
.play-trade-off[data-severity="low"] .trade-off-label {
  color: var(--color-text-muted);
}
```

- [ ] **Step 2: Add trade-off example to play card HTML**

In `src/report/style_guide.html`, after the `play-evidence` div (line 1589, after the closing `</div>` of `.play-evidence`) and before the `play-recommendation` div (line 1590), insert:

```html
        <!-- Trade-offs render here (between evidence and recommendation) -->
        <div class="play-trade-off" data-severity="high">
          <span class="trade-off-label">Trade-off</span>
          <span class="claim" data-claim="CLM-TL-TO-003-01">
            Conservative gate design limits LP appeal vs. aggressive gates expose redemption crisis risk — At $40.8B FEAUM, PAX lacks the liquidity buffer to absorb stress redemptions (cf. ANTI-003).
          </span>
        </div>
```

- [ ] **Step 3: Verify HTML is well-formed**

Run: `python3 -c "from html.parser import HTMLParser; HTMLParser().feed(open('src/report/style_guide.html').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 4: Run existing tests**

Run: `python3 -m pytest tests/ -v --tb=short 2>&1 | tail -20`
Expected: All tests pass

- [ ] **Step 5: Commit**

```bash
git add src/report/style_guide.html
git commit -m "feat: add .play-trade-off CSS component and HTML example to style guide"
```

---

## Chunk 2: SKILL.md — Target-Lens Agent

### Task 3: Add `trade_offs` field to target-lens output schema

**Files:**
- Modify: `.claude/skills/valuation-driver/SKILL.md:1610-1620` (target-lens output schema)

- [ ] **Step 1: Add `trade_offs` field to the play assessment schema**

In `.claude/skills/valuation-driver/SKILL.md`, after line 1620 (`> - \`principle_extracted\`: the general principle this play illustrates (not the specific action)`), insert the following block. Keep the existing blank line 1621 in place — the new text goes between lines 1620 and 1621:

```
> - `trade_offs`: array of trade-off objects (1-2 preferred, 3 only if strongly evidenced). Required for `directly_applicable` and `requires_adaptation` plays. Not required for `not_applicable`. Each object:
>   - `trade_off` (string, required): Bilateral tension framed as "X vs. Y"
>   - `mechanism` (string, required): How this specifically affects {COMPANY} given its context (drivers, scale, geography)
>   - `linked_anti_pattern` (string or null, optional): ANTI-NNN that materializes this risk, if one exists
>   - `severity` (enum: high/medium/low, required): Materiality for {COMPANY}
>   - `evidence_basis` (array of strings, required): References grounding the trade-off. Minimum 1 concrete reference (DVR-NNN position with value, ANTI-NNN, {COMPANY} metric with number). Generic trade-offs ("all M&A has integration risk") are blocked.
>   - `claim_id` (string, required): CLM-TL-TO-{play_number}-{seq} (e.g., CLM-TL-TO-005-01)
```

- [ ] **Step 2: Add trade-off claim emission rules**

In `.claude/skills/valuation-driver/SKILL.md`, after line 1664 (`> - Language reminder: "suggests", "appears to", "data is consistent with" — never imperative`), insert:

```
>
> **Trade-off claim emission:** Each trade-off object also emits a claim in `_claims`:
> ```json
> {
>   "id": "CLM-TL-TO-005-01",
>   "parent_id": "PLAY-005",
>   "type": "comparative",
>   "evidence": ["DVR-003", "ANTI-003", "CLM-PLAY-005-01"],
>   "confidence": "partial",
>   "score": 2,
>   "layer": "5-playbook"
> }
> ```
> - Trade-off claim IDs use pattern CLM-TL-TO-{play_number}-{seq} (separate from the play assessment CLM-TL-{NNN}-01)
> - Score max 2 (analogy-based). `evidence` must include the references from the trade-off's `evidence_basis`, resolved to IDs.
> - The tooltip renders the full evidence chain on click via the existing claim evidence layer.
```

- [ ] **Step 3: Verify SKILL.md is not corrupted**

Run: `wc -l .claude/skills/valuation-driver/SKILL.md`
Expected: Line count increased by ~25 lines from current (should be ~1780+)

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/valuation-driver/SKILL.md
git commit -m "feat: add trade_offs schema and claim emission to target-lens agent prompt"
```

---

## Chunk 3: SKILL.md — Report-Builder Agent

### Task 4: Add trade-off rendering instruction to report-builder

**Files:**
- Modify: `.claude/skills/valuation-driver/SKILL.md:1539-1559` (report-builder transferability matrix section — add after this block)

- [ ] **Step 1: Add rendering instruction for trade-offs**

In `.claude/skills/valuation-driver/SKILL.md`, after the transferability matrix block (after line 1559, the bumper statement line: `> 6. **Bumper statement:** End the matrix section with "Therefore: [summary of {COMPANY}'s transferability position relative to the peer universe]."`), insert:

```
>
> **Trade-off rendering (required if `target_company_lens.json` contains `trade_offs`):**
>
> Note: The SKILL.md target-lens agent outputs `target_company_lens.json` (line 1639). CLAUDE.md canonical table lists `target_lens.json`. Use whichever name the target-lens agent actually produced in the run directory.
>
> For each play card in the Strategic Implications section, render trade-offs inline between the evidence badges (`play-evidence`) and the recommendation block (`play-recommendation`). One `div` per trade-off:
>
> ```html
> <div class="play-trade-off" data-severity="high">
>   <span class="trade-off-label">Trade-off</span>
>   <span class="claim" data-claim="CLM-TL-TO-005-01">
>     Conservative gate design limits LP appeal vs. aggressive gates expose
>     redemption crisis risk — At $40.8B FEAUM, PAX lacks the liquidity
>     buffer to absorb stress redemptions (cf. ANTI-003).
>   </span>
> </div>
> ```
>
> Rules:
> - CSS classes (`play-trade-off`, `trade-off-label`) are defined in `style_guide.html`
> - `data-severity` attribute controls border color: `high` = amber, `medium`/`low` = gray
> - Trade-off text format: `{trade_off} — {mechanism} (cf. {linked_anti_pattern})` where mechanism is condensed to 1-2 sentences
> - The entire text is wrapped in `<span class="claim" data-claim="...">` for the tooltip evidence chain
> - Plays classified `not_applicable` have no trade-offs — skip rendering
> - If a play has zero trade-offs (e.g., empty array), do not render any trade-off divs for that play
```

- [ ] **Step 2: Verify SKILL.md is not corrupted**

Run: `wc -l .claude/skills/valuation-driver/SKILL.md`
Expected: Line count increased by ~20 more lines from Task 3

- [ ] **Step 3: Run full test suite**

Run: `python3 -m pytest tests/ -v --tb=short 2>&1 | tail -30`
Expected: All tests pass (no Python logic changed)

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/valuation-driver/SKILL.md
git commit -m "feat: add trade-off rendering instructions to report-builder agent prompt"
```

---

## Verification

After all tasks are complete:

- [ ] **Step 1: Run full test suite**

Run: `python3 -m pytest tests/ -v`
Expected: All tests pass

- [ ] **Step 2: Validate report_schema.json**

Run: `python3 -c "import json; d=json.load(open('src/report/report_schema.json')); assert 'trade_offs' in d['sections']['playbook_subsections']; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Validate style_guide.html has new CSS**

Run: `grep -c 'play-trade-off' src/report/style_guide.html`
Expected: >= 5 (CSS selectors + HTML example)

- [ ] **Step 4: Validate SKILL.md has trade-off schema**

Run: `grep -c 'trade_off' .claude/skills/valuation-driver/SKILL.md`
Expected: >= 10

- [ ] **Step 5: Validate SKILL.md has rendering instruction**

Run: `grep -c 'CLM-TL-TO' .claude/skills/valuation-driver/SKILL.md`
Expected: >= 3
