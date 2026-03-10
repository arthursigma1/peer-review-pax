# Report Consistency System Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ensure visual/structural consistency across iterative VDA report generations via a style guide, JSON schema, and post-generation validator.

**Architecture:** Three static artefacts (`style_guide.html`, `report_schema.json`) consumed by the report-builder agent at generation time, plus a Python validator (`report_validator.py`) that checks the generated HTML post-hoc. An architecture guardian skill (`/consistency-check`) audits cross-cutting dependencies.

**Tech Stack:** Python 3.11+, BeautifulSoup4 (via crawlee[beautifulsoup]), pytest, HTML/CSS

**Spec:** `docs/superpowers/specs/2026-03-10-report-consistency-design.md`

---

## File Structure

| File | Responsibility |
|---|---|
| `src/report/__init__.py` | Package init (empty) |
| `src/report/report_schema.json` | Declarative rules: required sections, chart rules, citation rules, regression policy |
| `src/report/style_guide.html` | CSS design system + component examples for report-builder to copy |
| `src/report/report_validator.py` | CLI tool: parses HTML, checks against schema, outputs JSON verdict |
| `tests/test_report_validator.py` | Unit tests with HTML fixture strings for each violation type |
| `.claude/skills/consistency-check/SKILL.md` | Architecture guardian slash command |

---

## Chunk 1: Schema + Style Guide (static artefacts)

### Task 1: Create report_schema.json

**Files:**
- Create: `src/report/__init__.py`
- Create: `src/report/report_schema.json`

- [ ] **Step 1: Create package directory and schema file**

```bash
mkdir -p src/report
touch src/report/__init__.py
```

Write `src/report/report_schema.json` with the exact content from the spec:

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
    "canonical_ids": {
      "executive_summary": "executive-summary",
      "methodology": "methodology",
      "driver_ranking": "driver-ranking",
      "correlation_analysis": "correlation-analysis",
      "peer_deep_dives": "peer-deep-dives",
      "strategic_playbook": "strategic-playbook",
      "target_company_lens": "target-company-lens",
      "appendix": "appendix"
    },
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
  "chart_title_verbs": [
    "drives", "explains", "shows", "reveals", "indicates",
    "suggests", "dominates", "outperforms", "correlates",
    "predicts", "leads", "exceeds", "trails", "separates",
    "distinguishes", "accounts", "contributes", "represents"
  ],
  "citation_rules": {
    "required_prefix": "PS-VD-",
    "min_citations_per_claim": 1,
    "exempt_sections": ["methodology", "appendix"]
  },
  "navigation": {
    "require_heading_ids": true,
    "require_toc_component": true,
    "toc_selector": "nav.toc"
  },
  "css_required_tokens": [
    "--color-primary",
    "--color-text-primary",
    "--font-body",
    "--font-mono"
  ],
  "regression": {
    "plays_removed_require_reason": true,
    "severity": "warning"
  }
}
```

- [ ] **Step 2: Validate JSON is parseable**

Run: `python3 -c "import json; json.load(open('src/report/report_schema.json')); print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add src/report/__init__.py src/report/report_schema.json
git commit -m "feat: add report schema with section, chart, and citation rules"
```

### Task 2: Create style_guide.html

**Files:**
- Create: `src/report/style_guide.html`
- Reference: `data/processed/pax/2026-03-10-run2/5-playbook/final_report.html` (CSS source)
- Reference: `data/processed/pax/2026-03-09-run2/5-playbook/final_report.html` (chart patterns)

- [ ] **Step 1: Extract and codify CSS from best reports**

Read the CSS from the 2026-03-10 report (`:root` block, component styles) and the 2026-03-09 report (bar charts, heatmap, badge system). Merge into a single `<style>` block using the `--color-*` variable naming convention from the spec.

Write `src/report/style_guide.html` as a self-contained HTML file with:

1. **`<head>`**: Google Fonts CDN link (DM Sans + IBM Plex Mono), `<style>` block with:
   - `:root` CSS variables (exact values from spec)
   - Base typography (body, headings, mono)
   - Layout (container max-width 1100px, padding, grid)
   - Component styles for each codified component (see below)

2. **`<body>`**: One example of each component, wrapped in `<!-- COMPONENT: name -->` comments:
   - Bumper statement
   - Play card (PLAY-NNN)
   - Anti-pattern card (ANTI-NNN)
   - Horizontal bar chart (inside `<figure data-chart-type="horizontalBar">`)
   - Heatmap table (inside `<figure data-chart-type="heatmap">`)
   - Simple text callout (inside `<figure data-chart-type="simpleText">`)
   - Footnote apparatus with bias tags
   - Collapsible details (`<details>`)
   - Quartile badge (q1-q4)
   - Two-column grid
   - Navigation component (floating button + sidebar overlay)

Key CSS rules from the spec:

```css
/* Horizontal bar */
.bar-chart { display: flex; flex-direction: column; gap: 6px; }
.bar-row { display: flex; align-items: center; gap: 12px; }
.bar-label { width: 140px; font-size: 0.85rem; text-align: right; color: var(--color-text-secondary); }
.bar { height: 28px; background: var(--color-bar-default); border-radius: 2px;
       font-family: var(--font-mono); font-size: 0.75rem; color: var(--color-text-secondary);
       display: flex; align-items: center; padding-left: 8px; }
.bar.highlight { background: var(--color-primary); color: white; }

/* Heatmap */
.heatmap td { width: 48px; height: 36px; text-align: center;
              font-family: var(--font-mono); font-size: 0.75rem; border: 1px solid var(--color-surface-base); }
.heatmap .strength-1 { background: rgba(0, 104, 255, 0.08); }
.heatmap .strength-2 { background: rgba(0, 104, 255, 0.20); }
.heatmap .strength-3 { background: rgba(0, 104, 255, 0.40); }
.heatmap .strength-4 { background: rgba(0, 104, 255, 0.65); }
.heatmap .strength-5 { background: rgba(0, 104, 255, 1.0); color: white; }

/* Chart wrapper (Knaflic: proximity) */
figure[data-chart-type] { margin: 1.5rem 0; padding: 0; }
figure[data-chart-type] .chart-title { font-size: 1rem; font-weight: 600; margin: 0 0 0.75rem 0; color: var(--color-text-primary); }
figure[data-chart-type] .chart-so-what { font-size: 0.85rem; color: var(--color-text-secondary); margin: 0.5rem 0 0 0; font-style: italic; }

/* Simple text callout */
.stat-callout { text-align: center; padding: 1.5rem; }
.stat-callout .stat-value { font-size: 2.5rem; font-weight: 700; color: var(--color-primary); font-family: var(--font-mono); }
.stat-callout .stat-label { font-size: 0.9rem; color: var(--color-text-secondary); margin-top: 0.25rem; }

/* Navigation */
.nav-trigger { position: fixed; bottom: 24px; right: 24px; width: 44px; height: 44px;
               border-radius: 50%; background: var(--color-primary); color: white; border: none;
               cursor: pointer; box-shadow: 0 2px 8px rgba(0,0,0,0.15); z-index: 1000;
               font-size: 1.2rem; display: flex; align-items: center; justify-content: center; }
.nav-sidebar { position: fixed; top: 0; right: -320px; width: 300px; height: 100vh;
               background: var(--color-surface-base); border-left: 1px solid var(--color-border);
               z-index: 1001; padding: 2rem 1.5rem; overflow-y: auto;
               transition: right 0.25s ease; }
.nav-sidebar.open { right: 0; }
.nav-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.3); z-index: 1000; display: none; }
.nav-backdrop.open { display: block; }
.nav-sidebar a { display: block; padding: 6px 0; font-size: 0.85rem; color: var(--color-text-secondary);
                 text-decoration: none; border-left: 2px solid transparent; padding-left: 12px; }
.nav-sidebar a.active { color: var(--color-primary); border-left-color: var(--color-primary); font-weight: 500; }
```

The navigation component also requires a small `<script>` block at the end of the HTML for scroll spy + toggle behavior (~30 lines of vanilla JS).

- [ ] **Step 2: Open style_guide.html in browser to visually verify**

Run: `open src/report/style_guide.html`

Verify: All components render correctly, colors match the design system, charts look clean.

- [ ] **Step 3: Commit**

```bash
git add src/report/style_guide.html
git commit -m "feat: add style guide HTML with codified report components"
```

---

## Chunk 2: Report Validator (TDD)

### Task 3: Write test fixtures

**Files:**
- Create: `tests/test_report_validator.py`

- [ ] **Step 1: Create test file with HTML fixture helpers**

```python
"""Tests for src.report.report_validator."""
import json
import pytest
from pathlib import Path


def _valid_html() -> str:
    """Minimal HTML that passes all validation checks."""
    return """<!DOCTYPE html>
<html>
<head><style>
:root {
  --color-primary: #0068ff;
  --color-text-primary: #1a1a1a;
  --font-body: 'DM Sans', sans-serif;
  --font-mono: 'IBM Plex Mono', monospace;
}
</style></head>
<body>
<nav class="toc"><a href="#executive-summary">Executive Summary</a></nav>
<h2 id="executive-summary">Executive Summary</h2>
<p>Key finding (PS-VD-001).</p>
<h2 id="methodology">Methodology</h2>
<p>Our approach.</p>
<h2 id="driver-ranking">Driver Ranking</h2>
<figure data-chart-type="horizontalBar">
  <h4 class="chart-title">DE/share drives 73% of P/E variation</h4>
  <div class="bar-chart"><div class="bar-row"><div class="bar">0.73</div></div></div>
  <p class="chart-so-what">Only stable driver across multiples</p>
</figure>
<p>Analysis (PS-VD-002).</p>
<h2 id="correlation-analysis">Correlation Analysis</h2>
<p>Results (PS-VD-003).</p>
<h2 id="peer-deep-dives">Peer Deep-Dives</h2>
<p>Profiles (PS-VD-004).</p>
<h2 id="strategic-playbook">Strategic Playbook</h2>
<p>Plays (PS-VD-005).</p>
<h2 id="target-company-lens">Target Company Lens</h2>
<p>Lens (PS-VD-006).</p>
<h2 id="appendix">Appendix</h2>
<p>Data tables.</p>
</body></html>"""


def _html_missing_section(section_id: str) -> str:
    """Valid HTML with one section removed."""
    html = _valid_html()
    # Remove the h2 with the given id and its following content up to next h2
    import re
    pattern = rf'<h2 id="{section_id}">.*?(?=<h2 |</body>)'
    return re.sub(pattern, '', html, flags=re.DOTALL)


def _html_forbidden_chart() -> str:
    """HTML with a forbidden chart type (pie)."""
    html = _valid_html()
    return html.replace(
        'data-chart-type="horizontalBar"',
        'data-chart-type="pie"'
    )


def _html_missing_chart_title() -> str:
    """HTML with chart figure missing .chart-title."""
    html = _valid_html()
    return html.replace(
        '<h4 class="chart-title">DE/share drives 73% of P/E variation</h4>',
        ''
    )


def _html_label_title() -> str:
    """HTML with chart title that's a label, not an action title."""
    html = _valid_html()
    return html.replace(
        'DE/share drives 73% of P/E variation',
        'P/E vs DE/share'
    )


def _html_missing_so_what() -> str:
    """HTML with chart figure missing .chart-so-what."""
    html = _valid_html()
    return html.replace(
        '<p class="chart-so-what">Only stable driver across multiples</p>',
        ''
    )


def _html_missing_citation() -> str:
    """HTML with a content paragraph lacking PS-VD citation."""
    html = _valid_html()
    return html.replace(
        '<p>Analysis (PS-VD-002).</p>',
        '<p>Analysis shows strong correlation.</p>'
    )


def _html_missing_heading_ids() -> str:
    """HTML with headings lacking id attributes."""
    html = _valid_html()
    return html.replace('id="driver-ranking"', '')


def _html_missing_toc() -> str:
    """HTML without nav.toc component."""
    html = _valid_html()
    return html.replace(
        '<nav class="toc"><a href="#executive-summary">Executive Summary</a></nav>',
        ''
    )


def _html_missing_css_tokens() -> str:
    """HTML missing required CSS tokens in :root."""
    return _valid_html().replace('--color-primary: #0068ff;', '')


def _html_no_style_block() -> str:
    """HTML without any <style> block."""
    html = _valid_html()
    import re
    return re.sub(r'<style>.*?</style>', '', html, flags=re.DOTALL)
```

- [ ] **Step 2: Commit fixtures**

```bash
git add tests/test_report_validator.py
git commit -m "test: add HTML fixture helpers for report validator"
```

### Task 4: Write failing tests for section checks

**Files:**
- Modify: `tests/test_report_validator.py`

- [ ] **Step 1: Add section validation tests**

Append to `tests/test_report_validator.py`:

```python
from src.report.report_validator import validate_html, load_schema


@pytest.fixture
def schema():
    schema_path = Path(__file__).parent.parent / "src" / "report" / "report_schema.json"
    return load_schema(schema_path)


class TestSectionValidation:
    def test_all_sections_present_passes(self, schema):
        result = validate_html(_valid_html(), schema)
        section_errors = [e for e in result["errors"] if "section" in e.lower()]
        assert len(section_errors) == 0

    def test_missing_executive_summary_fails(self, schema):
        result = validate_html(_html_missing_section("executive-summary"), schema)
        assert result["status"] in ("WARN", "FAIL")
        assert any("executive-summary" in e for e in result["errors"])

    def test_missing_methodology_fails(self, schema):
        result = validate_html(_html_missing_section("methodology"), schema)
        assert result["status"] in ("WARN", "FAIL")
        assert any("methodology" in e for e in result["errors"])

    def test_missing_appendix_fails(self, schema):
        result = validate_html(_html_missing_section("appendix"), schema)
        assert result["status"] in ("WARN", "FAIL")
        assert any("appendix" in e for e in result["errors"])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_report_validator.py::TestSectionValidation -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.report.report_validator'`

- [ ] **Step 3: Commit**

```bash
git add tests/test_report_validator.py
git commit -m "test: add failing section validation tests"
```

### Task 5: Write failing tests for chart checks

**Files:**
- Modify: `tests/test_report_validator.py`

- [ ] **Step 1: Add chart validation tests**

Append to `tests/test_report_validator.py`:

```python
class TestChartValidation:
    def test_valid_chart_passes(self, schema):
        result = validate_html(_valid_html(), schema)
        chart_warnings = [w for w in result["warnings"] if "chart" in w.lower()]
        assert len(chart_warnings) == 0

    def test_forbidden_chart_type_warns(self, schema):
        result = validate_html(_html_forbidden_chart(), schema)
        assert any("pie" in w.lower() for w in result["warnings"])

    def test_missing_chart_title_warns(self, schema):
        result = validate_html(_html_missing_chart_title(), schema)
        assert any("chart-title" in w.lower() or "action title" in w.lower() for w in result["warnings"])

    def test_label_title_warns(self, schema):
        result = validate_html(_html_label_title(), schema)
        assert any("action title" in w.lower() or "verb" in w.lower() for w in result["warnings"])

    def test_missing_so_what_warns(self, schema):
        result = validate_html(_html_missing_so_what(), schema)
        assert any("so-what" in w.lower() or "chart-so-what" in w.lower() for w in result["warnings"])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_report_validator.py::TestChartValidation -v`
Expected: FAIL (same import error)

- [ ] **Step 3: Commit**

```bash
git add tests/test_report_validator.py
git commit -m "test: add failing chart validation tests"
```

### Task 6: Write failing tests for citation, navigation, and CSS checks

**Files:**
- Modify: `tests/test_report_validator.py`

- [ ] **Step 1: Add remaining validation tests**

Append to `tests/test_report_validator.py`:

```python
class TestCitationValidation:
    def test_citations_present_passes(self, schema):
        result = validate_html(_valid_html(), schema)
        cite_warnings = [w for w in result["warnings"] if "citation" in w.lower()]
        assert len(cite_warnings) == 0

    def test_missing_citation_warns(self, schema):
        result = validate_html(_html_missing_citation(), schema)
        assert any("citation" in w.lower() or "PS-VD" in w for w in result["warnings"])

    def test_methodology_exempt_from_citations(self, schema):
        """Methodology and appendix sections don't require PS-VD citations."""
        result = validate_html(_valid_html(), schema)
        # Valid HTML has methodology without citation — should not warn
        cite_warnings = [w for w in result["warnings"]
                        if "citation" in w.lower() and "methodology" in w.lower()]
        assert len(cite_warnings) == 0


class TestNavigationValidation:
    def test_heading_ids_present_passes(self, schema):
        result = validate_html(_valid_html(), schema)
        nav_errors = [e for e in result["errors"] if "heading" in e.lower() and "id" in e.lower()]
        assert len(nav_errors) == 0

    def test_missing_heading_id_warns(self, schema):
        result = validate_html(_html_missing_heading_ids(), schema)
        assert any("id" in w.lower() and ("heading" in w.lower() or "driver-ranking" in w.lower())
                   for w in result["warnings"])

    def test_missing_toc_warns(self, schema):
        result = validate_html(_html_missing_toc(), schema)
        assert any("toc" in w.lower() or "nav" in w.lower() for w in result["warnings"])


class TestCSSValidation:
    def test_css_tokens_present_passes(self, schema):
        result = validate_html(_valid_html(), schema)
        css_warnings = [w for w in result["warnings"] if "css" in w.lower() or "token" in w.lower()]
        assert len(css_warnings) == 0

    def test_missing_css_token_warns(self, schema):
        result = validate_html(_html_missing_css_tokens(), schema)
        assert any("--color-primary" in w for w in result["warnings"])

    def test_no_style_block_warns(self, schema):
        result = validate_html(_html_no_style_block(), schema)
        assert any("style" in w.lower() or "css" in w.lower() for w in result["warnings"])


class TestRegressionCheck:
    def test_no_base_run_skips_regression(self, schema):
        """Without --base-run, regression check is skipped."""
        result = validate_html(_valid_html(), schema)
        regression_warnings = [w for w in result["warnings"] if "removed" in w.lower() or "deprecated" in w.lower()]
        assert len(regression_warnings) == 0

    def test_removed_play_warns(self, schema, tmp_path):
        from src.report.report_validator import _check_regression
        base_dir = tmp_path / "base"
        current_dir = tmp_path / "current"
        (base_dir / "5-playbook").mkdir(parents=True)
        (current_dir / "5-playbook").mkdir(parents=True)

        base_playbook = {"plays": [
            {"play_id": "PLAY-001", "title": "Play 1"},
            {"play_id": "PLAY-002", "title": "Play 2"},
        ]}
        current_playbook = {"plays": [
            {"play_id": "PLAY-001", "title": "Play 1"},
        ]}

        (base_dir / "5-playbook" / "playbook.json").write_text(json.dumps(base_playbook))
        (current_dir / "5-playbook" / "playbook.json").write_text(json.dumps(current_playbook))

        warnings: list[str] = []
        _check_regression(base_dir, current_dir, warnings)
        assert any("PLAY-002" in w for w in warnings)

    def test_deprecated_play_no_warn(self, schema, tmp_path):
        from src.report.report_validator import _check_regression
        base_dir = tmp_path / "base"
        current_dir = tmp_path / "current"
        (base_dir / "5-playbook").mkdir(parents=True)
        (current_dir / "5-playbook").mkdir(parents=True)

        base_playbook = {"plays": [
            {"play_id": "PLAY-001", "title": "Play 1"},
            {"play_id": "PLAY-002", "title": "Play 2"},
        ]}
        current_playbook = {"plays": [
            {"play_id": "PLAY-001", "title": "Play 1"},
            {"play_id": "PLAY-002", "status": "deprecated",
             "deprecated_reason": "Merged into PLAY-001"},
        ]}

        (base_dir / "5-playbook" / "playbook.json").write_text(json.dumps(base_playbook))
        (current_dir / "5-playbook" / "playbook.json").write_text(json.dumps(current_playbook))

        warnings: list[str] = []
        _check_regression(base_dir, current_dir, warnings)
        assert not any("PLAY-002" in w for w in warnings)


class TestOverallStatus:
    def test_valid_html_passes(self, schema):
        result = validate_html(_valid_html(), schema)
        assert result["status"] == "PASS"

    def test_missing_section_is_fail(self, schema):
        result = validate_html(_html_missing_section("executive-summary"), schema)
        assert result["status"] == "FAIL"

    def test_chart_issues_are_warn(self, schema):
        result = validate_html(_html_forbidden_chart(), schema)
        assert result["status"] == "WARN"
```

- [ ] **Step 2: Run all tests to verify they fail**

Run: `python3 -m pytest tests/test_report_validator.py -v`
Expected: FAIL (import error — module doesn't exist yet)

- [ ] **Step 3: Commit**

```bash
git add tests/test_report_validator.py
git commit -m "test: add citation, navigation, CSS, and status tests"
```

### Task 7: Implement report_validator.py — core structure

**Files:**
- Create: `src/report/report_validator.py`

- [ ] **Step 1: Write the module skeleton with load_schema and validate_html**

```python
"""Report validator — checks generated VDA report HTML against report_schema.json.

Usage:
    python3 -m src.report.report_validator --html path/to/final_report.html [--base-run path/to/base/run]

Output:
    JSON to stdout: {"status": "PASS|WARN|FAIL", "warnings": [...], "errors": [...]}
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup


def load_schema(path: Path | None = None) -> dict[str, Any]:
    """Load report_schema.json. Defaults to the schema bundled with this package."""
    if path is None:
        path = Path(__file__).parent / "report_schema.json"
    with open(path) as f:
        return json.load(f)


def validate_html(
    html: str,
    schema: dict[str, Any],
    base_run_dir: Path | None = None,
    current_run_dir: Path | None = None,
) -> dict[str, Any]:
    """Validate report HTML against the schema. Returns verdict dict."""
    soup = BeautifulSoup(html, "html.parser")
    errors: list[str] = []
    warnings: list[str] = []

    _check_sections(soup, schema, errors)
    _check_charts(soup, schema, warnings)
    _check_citations(soup, schema, warnings)
    _check_navigation(soup, schema, warnings)
    _check_css_tokens(html, schema, warnings)

    if base_run_dir and current_run_dir:
        _check_regression(base_run_dir, current_run_dir, warnings)

    status = "FAIL" if errors else ("WARN" if warnings else "PASS")
    return {"status": status, "errors": errors, "warnings": warnings}
```

- [ ] **Step 2: Run tests — should fail with missing check functions**

Run: `python3 -m pytest tests/test_report_validator.py -v --tb=short 2>&1 | head -30`
Expected: FAIL with `AttributeError` or `NameError` for `_check_sections`

- [ ] **Step 3: Commit skeleton**

```bash
git add src/report/report_validator.py
git commit -m "feat: add report validator skeleton with load_schema and validate_html"
```

### Task 8: Implement section checks

**Files:**
- Modify: `src/report/report_validator.py`

- [ ] **Step 1: Add _check_sections function**

Add after the `validate_html` function:

```python
def _check_sections(
    soup: BeautifulSoup,
    schema: dict[str, Any],
    errors: list[str],
) -> None:
    """Check that all required sections exist (matched by heading id)."""
    canonical_ids = schema["sections"]["canonical_ids"]
    for section_name, section_id in canonical_ids.items():
        heading = soup.find(["h1", "h2", "h3"], id=section_id)
        if heading is None:
            errors.append(
                f"Missing required section: '{section_name}' (expected heading with id='{section_id}')"
            )
```

- [ ] **Step 2: Run section tests**

Run: `python3 -m pytest tests/test_report_validator.py::TestSectionValidation -v`
Expected: PASS (3/3)

- [ ] **Step 3: Commit**

```bash
git add src/report/report_validator.py
git commit -m "feat: implement section validation check"
```

### Task 9: Implement chart checks

**Files:**
- Modify: `src/report/report_validator.py`

- [ ] **Step 1: Add _check_charts function**

```python
def _check_charts(
    soup: BeautifulSoup,
    schema: dict[str, Any],
    warnings: list[str],
) -> None:
    """Check chart figures for compliance with Knaflic rules."""
    chart_rules = schema["chart_rules"]
    forbidden = set(chart_rules["forbidden_types"])
    verbs = schema.get("chart_title_verbs", [])

    for fig in soup.find_all("figure", attrs={"data-chart-type": True}):
        chart_type = fig["data-chart-type"]

        # Forbidden type check
        if chart_type.lower() in {t.lower() for t in forbidden}:
            warnings.append(f"Forbidden chart type: '{chart_type}'")

        # Action title check
        title_el = fig.find(class_="chart-title")
        if title_el is None:
            warnings.append(
                f"Chart ({chart_type}) missing .chart-title element (action title required)"
            )
        elif verbs:
            title_text = title_el.get_text().lower()
            if not any(verb in title_text for verb in verbs):
                warnings.append(
                    f"Chart title may be a label, not an action title (no verb found): "
                    f"'{title_el.get_text().strip()}'"
                )

        # "So what" caption check
        so_what = fig.find(class_="chart-so-what")
        if so_what is None:
            warnings.append(
                f"Chart ({chart_type}) missing .chart-so-what caption"
            )
```

- [ ] **Step 2: Run chart tests**

Run: `python3 -m pytest tests/test_report_validator.py::TestChartValidation -v`
Expected: PASS (5/5)

- [ ] **Step 3: Commit**

```bash
git add src/report/report_validator.py
git commit -m "feat: implement chart validation with Knaflic rules"
```

### Task 10: Implement citation, navigation, and CSS checks

**Files:**
- Modify: `src/report/report_validator.py`

- [ ] **Step 1: Add _check_citations function**

```python
def _check_citations(
    soup: BeautifulSoup,
    schema: dict[str, Any],
    warnings: list[str],
) -> None:
    """Check that content paragraphs cite PS-VD-* sources."""
    cite_rules = schema["citation_rules"]
    prefix = cite_rules["required_prefix"]
    exempt_ids = {
        schema["sections"]["canonical_ids"][s]
        for s in cite_rules.get("exempt_sections", [])
        if s in schema["sections"]["canonical_ids"]
    }

    # Walk through h2 sections
    current_section_id = None
    for el in soup.find_all(["h2", "p"]):
        if el.name == "h2":
            current_section_id = el.get("id", "")
            continue
        if current_section_id in exempt_ids:
            continue
        text = el.get_text()
        if len(text.strip()) > 20 and prefix not in text:
            warnings.append(
                f"Citation missing in section '{current_section_id}': "
                f"'{text.strip()[:60]}...'"
            )
```

- [ ] **Step 2: Add _check_navigation function**

```python
def _check_navigation(
    soup: BeautifulSoup,
    schema: dict[str, Any],
    warnings: list[str],
) -> None:
    """Check heading IDs and TOC component."""
    nav_rules = schema["navigation"]

    if nav_rules.get("require_heading_ids"):
        for heading in soup.find_all(["h2", "h3"]):
            if not heading.get("id"):
                warnings.append(
                    f"Heading missing id attribute: '{heading.get_text().strip()[:40]}'"
                )

    if nav_rules.get("require_toc_component"):
        toc_selector = nav_rules.get("toc_selector", "nav.toc")
        # Parse selector: "nav.toc" -> tag=nav, class=toc
        parts = toc_selector.split(".")
        tag = parts[0] if parts[0] else None
        cls = parts[1] if len(parts) > 1 else None
        toc = soup.find(tag, class_=cls) if cls else soup.find(tag)
        if toc is None:
            warnings.append(
                f"Missing TOC component (expected '{toc_selector}')"
            )
```

- [ ] **Step 3: Add _check_css_tokens function**

```python
def _check_css_tokens(
    html: str,
    schema: dict[str, Any],
    warnings: list[str],
) -> None:
    """Check that required CSS custom properties exist in a <style> block."""
    required = schema.get("css_required_tokens", [])
    if not required:
        return

    style_match = re.search(r"<style[^>]*>(.*?)</style>", html, re.DOTALL)
    if style_match is None:
        warnings.append("No <style> block found — CSS tokens cannot be verified")
        return

    style_content = style_match.group(1)
    for token in required:
        if token not in style_content:
            warnings.append(f"Missing required CSS token: '{token}'")
```

- [ ] **Step 4: Add _check_regression stub**

```python
def _check_regression(
    base_run_dir: Path,
    current_run_dir: Path,
    warnings: list[str],
) -> None:
    """Check for plays removed between runs without deprecated_reason."""
    base_playbook = base_run_dir / "5-playbook" / "playbook.json"
    current_playbook = current_run_dir / "5-playbook" / "playbook.json"

    if not base_playbook.exists() or not current_playbook.exists():
        return

    with open(base_playbook) as f:
        base_data = json.load(f)
    with open(current_playbook) as f:
        current_data = json.load(f)

    base_plays = {p["play_id"] for p in base_data.get("plays", []) if "play_id" in p}
    current_plays = {p["play_id"] for p in current_data.get("plays", []) if "play_id" in p}
    deprecated = {
        p["play_id"] for p in current_data.get("plays", [])
        if p.get("status") == "deprecated" and p.get("deprecated_reason")
    }

    removed = base_plays - current_plays - deprecated
    for play_id in sorted(removed):
        warnings.append(
            f"Play '{play_id}' was in base run but removed without deprecated_reason"
        )
```

- [ ] **Step 5: Run all tests**

Run: `python3 -m pytest tests/test_report_validator.py -v`
Expected: ALL PASS

- [ ] **Step 6: Commit**

```bash
git add src/report/report_validator.py
git commit -m "feat: implement citation, navigation, CSS, and regression checks"
```

### Task 11: Add CLI entry point

**Files:**
- Modify: `src/report/report_validator.py`

- [ ] **Step 1: Add argparse and main()**

Append to `src/report/report_validator.py`:

```python
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate VDA report HTML against report_schema.json"
    )
    parser.add_argument(
        "--html", required=True, type=Path,
        help="Path to the generated final_report.html"
    )
    parser.add_argument(
        "--schema", type=Path, default=None,
        help="Path to report_schema.json (defaults to bundled schema)"
    )
    parser.add_argument(
        "--base-run", type=Path, default=None,
        help="Path to base run directory for regression check"
    )
    parser.add_argument(
        "--current-run", type=Path, default=None,
        help="Path to current run directory (inferred from --html if not set)"
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    html_path: Path = args.html
    if not html_path.exists():
        print(json.dumps({"status": "FAIL", "errors": [f"File not found: {html_path}"], "warnings": []}))
        sys.exit(1)

    schema = load_schema(args.schema)
    html = html_path.read_text(encoding="utf-8")

    current_run_dir = args.current_run or html_path.parent.parent
    result = validate_html(
        html, schema,
        base_run_dir=args.base_run,
        current_run_dir=current_run_dir,
    )

    print(json.dumps(result, indent=2))
    sys.exit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Test CLI against a real report**

Run: `python3 -m src.report.report_validator --html data/processed/pax/2026-03-10-run2/5-playbook/final_report.html 2>&1 | python3 -m json.tool | head -20`
Expected: FAIL status with multiple section and chart errors. This is correct — existing reports predate the new conventions (no `data-chart-type` attributes, no canonical heading IDs, no `nav.toc`). The output documents the gap between existing reports and the new standard.

- [ ] **Step 3: Commit**

```bash
git add src/report/report_validator.py
git commit -m "feat: add CLI entry point for report validator"
```

### Task 12: Verify all tests pass end-to-end

**Files:** (none — verification only)

- [ ] **Step 1: Run full test suite**

Run: `python3 -m pytest tests/test_report_validator.py -v`
Expected: ALL PASS

- [ ] **Step 2: Commit if any test fixes were needed**

```bash
git add tests/test_report_validator.py src/report/report_validator.py
git commit -m "fix: address any test issues found during verification"
```

---

## Chunk 3: Architecture Guardian + Wiring

### Task 13: Create `/consistency-check` skill

**Files:**
- Create: `.claude/skills/consistency-check/SKILL.md`

- [ ] **Step 1: Write the skill file**

```markdown
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

Verify hex values match across files.

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
- Note: The report's `style_guide.html` uses `--font-body` while the dashboard's `index.css` uses `--font-sans`. Same value, different name by design — the report is a standalone artefact. Flag as informational, not a mismatch.
```

- [ ] **Step 2: Commit**

```bash
git add .claude/skills/consistency-check/SKILL.md
git commit -m "feat: add /consistency-check architecture guardian skill"
```

### Task 14: Update CLAUDE.md with new artefacts

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Add report consistency entries to CLAUDE.md**

In the **Key Directories** section, add:
```
- `src/report/` — Report consistency system (style_guide.html, report_schema.json, report_validator.py)
```

In the **Commands** section, add:
```bash
# Validate a generated VDA report
python3 -m src.report.report_validator --html data/processed/pax/2026-03-10-run2/5-playbook/final_report.html

# Validate with regression check against a base run
python3 -m src.report.report_validator --html path/to/final_report.html --base-run data/processed/pax/2026-03-09-run2/
```

In the **Skills** section, add:
```
### `/consistency-check`

Audit cross-cutting dependencies across pipeline agents, dashboard, CLAUDE.md, and report system. Read-only — flags mismatches in canonical filenames, agent names, design tokens, report schema, and pipeline flow.
```

In the **VDA canonical output filenames** table, add a note:
```
- Report validation: `python3 -m src.report.report_validator --html {path}` after step 5 report generation
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add report consistency system and /consistency-check to CLAUDE.md"
```

### Task 15: Run full test suite and validate against real report

**Files:** (none — verification only)

- [ ] **Step 1: Run all validator tests**

Run: `python3 -m pytest tests/test_report_validator.py -v`
Expected: ALL PASS

- [ ] **Step 2: Run validator against 2026-03-10 report**

Run: `python3 -m src.report.report_validator --html data/processed/pax/2026-03-10-run2/5-playbook/final_report.html`

Expected: FAIL status with multiple section errors (existing report uses different heading IDs like `exec-summary`, `section-1` instead of `executive-summary`, `driver-ranking`) and chart warnings (no `data-chart-type` attributes, no `chart-title` class, no `chart-so-what` class). This is correct — the validator documents the gap between existing reports and the new standard. No action required on existing reports.

- [ ] **Step 3: Run validator with regression check**

Run: `python3 -m src.report.report_validator --html data/processed/pax/2026-03-10-run2/5-playbook/final_report.html --base-run data/processed/pax/2026-03-09-run2/`

Expected: Same FAIL output as above, plus any regression warnings about plays that were removed between runs without `deprecated_reason`.

- [ ] **Step 4: Run /consistency-check to verify the new artefacts don't introduce mismatches**

Run: `/consistency-check`

Expected: Report showing alignment across the new files. Will flag pre-existing mismatches: `lib.rs` reading `platform_playbook.json`/`target_company_lens.json` (legacy names — known issue, do not fix in this task). Will also note `--font-body` vs `--font-sans` naming difference (informational, by design).

- [ ] **Step 5: Final commit if any fixes were needed**

```bash
git add src/report/ tests/test_report_validator.py CLAUDE.md .claude/skills/consistency-check/
git commit -m "fix: address issues found during validation"
```
