# Play Trade-Off Intelligence for Target Company Lens

**Date:** 2026-03-11
**Status:** Approved
**Scope:** Add per-play trade-off analysis to the target-lens agent output, rendered inline in the final report via the claim evidence layer.

---

## Problem

The VDA pipeline produces plays (PLAY-NNN) and anti-patterns (ANTI-NNN) grounded in peer evidence. The target-lens agent classifies each play's applicability to the target company. But it does not surface the **trade-offs** — the bilateral tensions that arise when a specific play is considered in the target company's context (scale, geography, asset mix, driver position).

These trade-offs are the most governance-relevant output. A board member needs to know not just "this play is directly applicable" but "here's what you'd be trading away if you pursue it."

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Where trade-offs appear | Inline within each play card in the report | Density over simplicity — executives scan, not browse |
| Who generates | target-lens agent | Already has full context: PAX driver positions, playbooks, anti-patterns |
| How many per play | 1-2 preferred, 3 only if strongly evidenced | Earn every element — force prioritization |
| Evidence grounding | Required via `evidence_basis` array + claim emission | Tooltip on click shows evidence chain |
| Plays classified `not_applicable` | No trade-offs required | Irrelevant plays don't need trade-off analysis |

## Schema

New `trade_offs` array field on each play assessment in `target_lens.json`:

```json
{
  "play_id": "PLAY-005",
  "applicability": "directly_applicable",
  "priority": "high",
  "trade_offs": [
    {
      "trade_off": "Conservative gate design limits LP appeal vs. aggressive gates expose redemption crisis risk",
      "mechanism": "At $40.8B FEAUM, PAX lacks the liquidity buffer that BX ($400B+) used to absorb BREIT stress redemptions. A gate activation on PAX's first open-end vehicle would damage permanent capital credibility before it's established.",
      "linked_anti_pattern": "ANTI-003",
      "severity": "high",
      "evidence_basis": ["DVR-003 Q1 position ($40.8B FEAUM)", "ANTI-003 BREIT gate crisis", "BX FEAUM $400B+ as liquidity benchmark"],
      "claim_id": "CLM-TL-TO-005-01"
    }
  ],
  "rationale": "...",
  "adaptation_notes": "...",
  "implementation_pathway": "..."
}
```

### Field definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `trade_off` | string | yes | Bilateral tension framed as "X vs. Y" |
| `mechanism` | string | yes | How this specifically affects the target company given its context (drivers, scale, geography) |
| `linked_anti_pattern` | string or null | no | ANTI-NNN that materializes this risk, if one exists |
| `severity` | enum: high/medium/low | yes | Materiality for the target company |
| `evidence_basis` | array of strings | yes | References grounding the trade-off (driver positions, anti-patterns, target company metrics, conflicting plays). Minimum 1 concrete reference. |
| `claim_id` | string | yes | CLM-TL-TO-{play_number}-{seq} for the claim evidence layer |

### Rules for the target-lens agent

- 1-2 trade-offs per play preferred. 3 only if each is strongly evidenced and independent.
- Plays classified `not_applicable` do not require trade-offs.
- Every trade-off must be grounded in the target company's position on value drivers or in observed anti-patterns. Generic trade-offs ("all M&A has integration risk") are blocked.
- `evidence_basis` must contain at least 1 concrete reference (DVR-NNN position with value, ANTI-NNN, target company metric with number).
- Existing language rules apply: "The peer evidence suggests...", never prescriptive.

### Claim emission

Each trade-off emits a claim in the `_claims` array of `target_lens.json`:

```json
{
  "id": "CLM-TL-TO-005-01",
  "parent_id": "PLAY-005",
  "type": "comparative",
  "evidence": ["DVR-003", "ANTI-003", "CLM-PLAY-005-01"],
  "confidence": "partial",
  "score": 2,
  "layer": "5-playbook"
}
```

Score max 2 (analogy-based). The tooltip renders the full evidence chain on click.

## Rendering

Trade-offs render inline within the play card in the final HTML report, between the evidence badges and the recommendation block. One line per trade-off.

### CSS component: `.play-trade-off`

```css
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

### HTML structure within play card

```html
<div class="play-card">
  <div class="play-header">...</div>
  <div class="play-body">
    <p><strong>Reference firm:</strong> ...</p>
    <p><strong>What was done:</strong> ...</p>
    <p><strong>Why it works:</strong> ...</p>
    <p><strong>Operational prerequisites:</strong> ...</p>
    <div class="play-evidence">...</div>

    <!-- Trade-offs render here -->
    <div class="play-trade-off" data-severity="high">
      <span class="trade-off-label">Trade-off</span>
      <span class="claim" data-claim="CLM-TL-TO-005-01">
        Conservative gate design limits LP appeal vs. aggressive gates
        expose redemption crisis risk — At $40.8B FEAUM, PAX lacks the
        liquidity buffer to absorb stress redemptions (cf. ANTI-003).
      </span>
    </div>

    <div class="play-recommendation">...</div>
  </div>
</div>
```

Design rationale:
- **Amber left border** for high severity — consistent with `--color-warning` for status signals. Not red (reserved for anti-patterns/errors).
- **Gray left border** for medium/low — recedes visually, doesn't compete with the play content.
- **Mono uppercase label** — matches existing badge/label patterns in the style guide.
- **Claim wrapping** — entire trade-off text is clickable, tooltip shows evidence chain.
- No emoji/icon — consistent with "no decoration, no personality injection."

## Context Window Impact

**Target-lens agent:** Currently ~77K tokens input (38.5% of 200K). Adding trade-off generation requires no additional input files. Output grows ~3KB. No risk.

**Report-builder:** Currently ~175K tokens. `target_lens.json` grows from ~94KB to ~97KB. Negligible impact.

## Files to Modify

| File | Change |
|------|--------|
| `.claude/skills/valuation-driver/SKILL.md` | Add `trade_offs` field spec to target-lens prompt. Add rendering instruction to report-builder prompt. |
| `src/report/report_schema.json` | Add `trade_offs` to `playbook_subsections` array |
| `src/report/style_guide.html` | Add `.play-trade-off` CSS component + example in play card section |

## Files NOT Modified

- Dashboard (usePipeline.ts, lib.rs, ptyParser.ts) — trade-offs are report content, not canonical pipeline outputs
- context_slicer.py — target_lens.json is not sliced
- report_validator.py — validates HTML structure (sections, charts, citations), not play card content
- claim-auditor CP-3 — already audits target_lens.json claims; trade-off claims are audited as normal comparative claims

## Verification

1. Run existing tests: `python3 -m pytest tests/ -v` (no new tests needed — this is prompt + CSS, not Python logic)
2. Next VDA run: verify `target_lens.json` contains `trade_offs` arrays on play assessments
3. Verify final report HTML: `.play-trade-off` elements render within play cards, claim tooltips work on click
4. Verify claim-auditor CP-3: trade-off claims (CLM-TL-TO-*) appear in audit output
