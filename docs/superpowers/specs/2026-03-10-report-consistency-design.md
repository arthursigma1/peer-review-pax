# Report Consistency System — Design Spec

**Date**: 2026-03-10
**Status**: Approved
**Problem**: 4 VDA report versions (03-07 through 03-10) vary wildly in HTML structure, CSS, content taxonomy, and visual quality. No mechanism ensures consistency across iterative runs or prevents regression.

## Approach

**Style Guide + JSON Schema + Post-Validation.** Three artefacts that the report-builder agent receives as static prompt prefix, plus a Python validator that enforces rules after generation.

Not a rigid template with placeholders — the report-builder retains creative capacity for content and narrative, but operates within a defined visual and structural skeleton.

## Artefact 1: `src/report/style_guide.html` (~3K tokens)

Self-contained HTML with the report's CSS and one example of each component. The report-builder copies the `<style>` block and adapts content.

### CSS Variables

Values match `src/tauri/src/lib/theme.ts` and `src/tauri/src/index.css`. Variable names use the `--color-*` prefix from `index.css` for consistency. The report HTML is a standalone artefact (not consumed by the Tauri dashboard), but shares the same design tokens.

```css
:root {
  --color-primary: #0068ff;
  --color-primary-hover: #0055d4;
  --color-primary-dim: #e8f0ff;
  --color-text-primary: #1a1a1a;
  --color-text-secondary: #6b7280;
  --color-text-muted: #9ca3af;
  --color-surface-base: #ffffff;
  --color-surface-raised: #f8f9fa;
  --color-surface-alt: #f3f4f6;
  --color-border: #e0e0e0;
  --color-success: #10b981;
  --color-warning: #d97706;
  --color-error: #dc2626;
  --color-bar-default: #e5e7eb;
  --font-body: 'DM Sans', system-ui, sans-serif;
  --font-mono: 'IBM Plex Mono', monospace;
}
```

### Codified Components

Extracted from the two best reports (2026-03-09-run2 visual, 2026-03-10-run2 content):

| Component | Origin | Usage |
|---|---|---|
| Bumper statement | 03-10 | Key conclusions (blue left-border box) |
| Play card | 03-10 | PLAY-NNN with gray header + body |
| Anti-pattern card | 03-10 | ANTI-NNN with red border/header |
| Horizontal bar (CSS) | 03-09 | Driver ranking, firm positioning |
| Heatmap (table) | 03-09 | Correlation matrix |
| Simple text callout | both | Executive summary, headline numbers |
| Footnote apparatus | 03-10 | PS-VD-* citations with bias tags |
| Collapsible details | 03-10 | Deep-dives, supplementary data |
| Quartile badge | 03-09 | q1/q2/q3/q4 positioning |
| Two-col grid | 03-09 | Side-by-side comparisons |
| Navigation (floating + sidebar) | new | TOC with scroll spy |

### CSS-Only Charts (no JavaScript libraries)

Charts are pure HTML + CSS. No Chart.js, D3, or any external dependency.

Each chart is wrapped in a `<figure data-chart-type="TYPE">` element where TYPE is one of: `horizontalBar`, `heatmap`, `simpleText`. This attribute is the validator's detection mechanism for chart type compliance.

**HTML contract for charts** (the validator relies on this structure):

```html
<figure data-chart-type="horizontalBar">
  <h4 class="chart-title">DE/share drives 73% of P/E variation</h4>
  <div class="bar-chart">
    <div class="bar-row">
      <span class="bar-label">DE/share</span>
      <div class="bar highlight" style="width: 73%">0.73</div>
    </div>
    <div class="bar-row">
      <span class="bar-label">FRE Growth</span>
      <div class="bar" style="width: 58%">0.58</div>
    </div>
  </div>
  <p class="chart-so-what">Only stable driver with rho >= 0.5 on 2/3 multiples</p>
</figure>
```

**Validator selectors:**
- Chart type: `figure[data-chart-type]` attribute
- Action title: `figure .chart-title` (must contain a verb, checked against a verb list)
- "So what" caption: `figure .chart-so-what` (must exist inside every `<figure data-chart-type>`)

**Chart types:**

| Type | Element | Description |
|---|---|---|
| `horizontalBar` | `<div class="bar-chart">` with `.bar-row` children | `width: N%` bars, `.highlight` class for key data in blue, rest in `--color-bar-default` |
| `heatmap` | `<table class="heatmap">` | Cells colored via opacity of `--color-primary` (`rgba(0, 104, 255, opacity)`), 5 intensity levels |
| `simpleText` | `<div class="stat-callout">` | Large number with context caption for headline stats |

### Knaflic "Storytelling with Data" Principles (embedded in components)

Based on chapters 1-4 of Cole Nussbaumer Knaflic's book:

- **Action titles**: Every chart heading is a sentence with a verb ("DE/share drives 73% of P/E variation"), never a label ("P/E vs DE/share")
- **"So what" captions**: Every chart has a `<p class="chart-caption">` below it stating the conclusion
- **Preattentive attributes**: Only 1 highlight color (blue) for the data that matters. Everything else is gray. Never rainbow palettes
- **Declutter**: No gridlines, no chart borders, no separate legends. Labels inline on data
- **Gestalt proximity**: Chart + title + caption grouped in `<figure>` with no margin between them
- **Gestalt similarity**: All charts of the same type use identical sizing and palette
- **Forbidden types**: pie, donut, radar, 3D — per Knaflic Ch2 guidance

### Navigation Component

Floating button (bottom-right) triggers a sidebar overlay with scroll spy. Preserves 100% content width.

- Sidebar slides in from right, semi-transparent backdrop
- Highlights current section based on scroll position
- Click navigates to section via heading `id` attributes
- Dismisses on outside click or Escape key

### Font Loading

`@font-face` declarations reference woff2 files via relative path (`./fonts/`). The style_guide.html is NOT self-contained for fonts — it expects font files to be copied alongside the report at build time. This avoids base64-embedding (~200KB+ of font data) which would blow the ~3K token budget.

For generated reports, the report-builder embeds a Google Fonts CDN fallback (`<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap">`) so reports remain readable without local font files. Matches `src/tauri/public/fonts/fonts.css` definitions.

## Artefact 2: `src/report/report_schema.json` (~1.5K tokens)

Defines structure, chart rules, and citation requirements that the validator checks.

```json
{
  "version": "1.0",
  "sections": {
    "required": [
      "executive_summary",
      "methodology",
      "driver_ranking",
      "correlation_analysis",
      "peer_deep_dives",
      "strategic_playbook",
      "target_company_lens",
      "appendix"
    ],
    "playbook_subsections": ["plays", "anti_patterns"]
  },
  "chart_rules": {
    "forbidden_types": ["pie", "donut", "radar", "3d"],
    "allowed_types": ["horizontalBar", "heatmap", "simpleText"],
    "require_action_title": true,
    "require_so_what_caption": true,
    "max_highlight_colors": 1,
    "highlight_color": "#0068ff",
    "default_color": "#e5e7eb"
  },
  "citation_rules": {
    "required_prefix": "PS-VD-",
    "min_citations_per_claim": 1
  },
  "navigation": {
    "require_heading_ids": true,
    "require_toc_component": true
  },
  "regression": {
    "plays_removed_require_reason": true,
    "severity": "warning"
  }
}
```

## Artefact 3: `src/report/report_validator.py`

Python script that parses generated HTML and checks against the schema.

### Checks

1. **Required sections** — all `required` sections present, matched by heading `id` attribute. Canonical IDs: `executive-summary`, `methodology`, `driver-ranking`, `correlation-analysis`, `peer-deep-dives`, `strategic-playbook`, `target-company-lens`, `appendix`
2. **Chart compliance** — `figure[data-chart-type]` attribute checked against `forbidden_types`; `figure .chart-title` must exist and contain a verb (checked against verb list: drives, explains, shows, reveals, indicates, suggests, dominates, outperforms, correlates, predicts); `figure .chart-so-what` must exist inside every chart figure
3. **Citation density** — `<p>` elements in content sections without PS-VD-* references trigger warning (excludes methodology, appendix)
4. **Navigation** — `<h2>` and `<h3>` elements have `id` attributes; TOC component (`<nav class="toc">`) present
5. **Regression** — if `--base-run` provided, reads `playbook.json` from both runs; plays in base but absent in new without `deprecated_reason` field trigger warning
6. **CSS variables** — verifies `:root` block contains `--color-primary`, `--color-text-primary`, `--font-body`, `--font-mono` (minimum required tokens)

### Output

```json
{"status": "PASS|WARN|FAIL", "warnings": [...], "errors": [...]}
```

### Enforcement

- WARN → the SKILL.md orchestrator (step 5) re-invokes the report-builder agent with the validator JSON output appended to the prompt as a "fix list". The report-builder reads the existing HTML + fix list and outputs a corrected version. One repair pass only.
- FAIL → same mechanism, 1 attempt.
- Still FAIL after repair → HTML emits with a `<div class="validation-banner">` warning banner at top listing unresolved issues. Never blocks generation completely.

## Pipeline Integration

```
playbook-synthesizer agent (step 5, already exists)
    produces: Ghost Report Skeleton (section headings + play titles, no prose)
    │
    ▼
report-builder agent
    receives static prefix: style_guide.html + report_schema.json (~6.5K tokens)
    receives dynamic data: playbook.json + target_lens.json + driver_ranking.json + strategy_profiles.json (top 5)
    receives: Ghost Report Skeleton as structural guide
    │
    ▼
SKILL.md orchestrator runs: python3 -m src.report.report_validator --html final_report.html [--base-run path]
    │
    ├─ PASS → done
    └─ WARN/FAIL → orchestrator re-invokes report-builder with validator output as fix list → 1 repair pass → done
```

**Note on pre-existing filename drift**: `lib.rs` currently reads `platform_playbook.json` and `target_company_lens.json` (legacy names). The canonical names are `playbook.json` and `target_lens.json` per CLAUDE.md. The `/consistency-check` agent (see Architecture Guardian below) will flag and resolve these mismatches.

### Context Budget

| Artefact | Tokens |
|---|---|
| style_guide.html | ~3K |
| report_schema.json | ~1.5K |
| Prompt instructions | ~2K |
| playbook.json | ~8K |
| target_lens.json | ~4K |
| driver_ranking.json | ~2K |
| strategy_profiles.json (top 5) | ~5K |
| Ghost Skeleton | ~1K |
| **Total** | **~26.5K** |

Well within the 50K agent context budget. The static prefix (~6.5K) benefits from Anthropic API prompt caching.

## Architecture Guardian

### Problem

The project has grown complex: pipeline agents produce canonical files → dashboard detects them → SKILL.md references them → CLAUDE.md documents them. Changing one thing (e.g., a filename) can silently break the dashboard, the pipeline skill, or the methodology docs. The CLAUDE.md already documents this as "filename drift risk."

This report consistency system adds new coupling: style_guide.html CSS tokens must match theme.ts, report_schema.json sections must match what the report-builder actually generates, the validator must understand the HTML structure the style_guide defines.

### Solution: `/consistency-check` Slash Command

A read-only audit agent that maps cross-cutting dependencies and flags mismatches. Runs before implementations that touch shared contracts.

**What it checks:**

| Domain | Files Involved | Check |
|---|---|---|
| Canonical filenames | CLAUDE.md table, SKILL.md, `usePipeline.ts` (STEP_COMPLETE_REQS + FILE_TO_AGENT), `lib.rs` (detect_existing_session) | All 4 sources agree on filenames per step |
| Agent names | CLAUDE.md VDA Friendly Naming table, SKILL.md agent definitions, `ptyParser.ts` agent detection patterns | All sources agree on agent identifiers |
| Design tokens | `theme.ts`, `index.css` (@theme block), `style_guide.html` (:root), report HTML files | CSS variables consistent across all files |
| Report schema | `report_schema.json`, `report_validator.py` check list, `style_guide.html` component inventory | Validator checks everything the schema declares |
| Pipeline flow | SKILL.md step definitions, `usePipeline.ts` step detection, CLAUDE.md pipeline docs | Step numbering, agent assignments, and output files aligned |
| Methodology | `docs/pax-first-valuation-driver-methodology.md`, CLAUDE.md conventions | Methodology doc reflects current pipeline behavior |

**Output**: Markdown report listing:
- Confirmed alignments (brief)
- Mismatches found (with file paths and line numbers)
- Suggested fixes

**When to run:**
- Before implementing changes that touch shared contracts (filenames, agent names, design tokens)
- After completing implementation of new features that add cross-cutting dependencies
- On-demand via `/consistency-check`

**Implementation**: A Claude Code skill file at the project root (same pattern as existing `/analyze-drift` and `/valuation-driver` skills) that dispatches a read-only Explore-type agent. No code changes — pure audit.

## Chart-to-Section Mapping

| Report Section | Chart Type | Knaflic Rationale |
|---|---|---|
| Executive Summary | `simpleText` | 1-2 key numbers; no chart needed |
| Driver Ranking | `horizontalBar` | Categorical comparison; horizontal for long labels |
| Correlation Analysis | `heatmap` | Pattern spotting in numeric grid |
| Peer Deep-Dives | `horizontalBar` (grouped) | Few attributes across firms |
| Strategic Playbook | none | Narrative — plays are arguments, not data |
| Target Company Lens | `simpleText` + `horizontalBar` | Headline number + relative positioning |
| Methodology | none | Process description |
| Appendix | tables | Raw data reference |

## Regression Protection

Plays removed between runs require `deprecated_reason` in playbook.json:

```json
{
  "play_id": "PLAY-003",
  "status": "deprecated",
  "deprecated_reason": "Merged into PLAY-007 after correlation analysis showed shared driver"
}
```

This is a warning, not a hard block. The validator flags it; the report-builder can proceed.

## Files to Create

| File | Purpose |
|---|---|
| `src/report/style_guide.html` | Design system reference + CSS + component examples |
| `src/report/report_schema.json` | Structure and validation rules |
| `src/report/report_validator.py` | Post-generation HTML validator |
| `tests/test_report_validator.py` | Validator unit tests (fixtures: valid HTML, each violation type as separate fixture) |
| Consistency-check skill (location TBD per project skill convention) | Architecture guardian slash command |
