"""Tests for src.report.report_validator."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from src.report.report_validator import validate_html, load_schema


# ---------------------------------------------------------------------------
# HTML fixture helpers
# ---------------------------------------------------------------------------


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
<p>Key finding supports the thesis (PS-VD-001).</p>
<h2 id="methodology">Methodology</h2>
<p>Our approach.</p>
<h2 id="driver-ranking">Driver Ranking</h2>
<figure data-chart-type="horizontalBar">
  <h4 class="chart-title">DE/share drives 73% of P/E variation</h4>
  <div class="bar-chart"><div class="bar-row"><div class="bar">0.73</div></div></div>
  <p class="chart-so-what">Only stable driver across multiples</p>
</figure>
<p>Analysis confirms the driver hierarchy (PS-VD-002).</p>
<h2 id="correlation-analysis">Correlation Analysis</h2>
<p>Spearman correlation results support the ranking (PS-VD-003).</p>
<h2 id="peer-deep-dives">Peer Deep-Dives</h2>
<p>Firm profiles show differentiated positioning (PS-VD-004).</p>
<h2 id="strategic-playbook">Strategic Playbook</h2>
<p>Ten plays drawn from peer evidence (PS-VD-005).</p>
<h2 id="target-company-lens">Target Company Lens</h2>
<p>Transferable principles for governance cascade (PS-VD-006).</p>
<h2 id="appendix">Appendix</h2>
<p>Data tables.</p>
</body></html>"""


def _html_missing_section(section_id: str) -> str:
    """Valid HTML with one h2 section (and its content) removed."""
    html = _valid_html()
    pattern = rf'<h2 id="{section_id}">.*?(?=<h2 |</body>)'
    return re.sub(pattern, "", html, flags=re.DOTALL)


def _html_forbidden_chart() -> str:
    """HTML with a forbidden chart type (pie)."""
    return _valid_html().replace(
        'data-chart-type="horizontalBar"',
        'data-chart-type="pie"',
    )


def _html_missing_chart_title() -> str:
    """HTML with chart figure missing .chart-title."""
    return _valid_html().replace(
        '<h4 class="chart-title">DE/share drives 73% of P/E variation</h4>',
        "",
    )


def _html_label_title() -> str:
    """HTML with chart title that is a label (no verb), not an action title."""
    return _valid_html().replace(
        "DE/share drives 73% of P/E variation",
        "P/E vs DE/share",
    )


def _html_missing_so_what() -> str:
    """HTML with chart figure missing .chart-so-what caption."""
    return _valid_html().replace(
        '<p class="chart-so-what">Only stable driver across multiples</p>',
        "",
    )


def _html_missing_citation() -> str:
    """HTML with a non-exempt content paragraph lacking a PS-VD citation."""
    return _valid_html().replace(
        "<p>Analysis confirms the driver hierarchy (PS-VD-002).</p>",
        "<p>Analysis shows a strong correlation between metrics.</p>",
    )


def _html_missing_heading_ids() -> str:
    """HTML with one h2 heading missing its id attribute."""
    return _valid_html().replace('id="driver-ranking"', "")


def _html_missing_toc() -> str:
    """HTML without a nav.toc component."""
    return _valid_html().replace(
        '<nav class="toc"><a href="#executive-summary">Executive Summary</a></nav>',
        "",
    )


def _html_missing_css_tokens() -> str:
    """HTML with --color-primary removed from the :root block."""
    return _valid_html().replace("--color-primary: #0068ff;", "")


def _html_no_style_block() -> str:
    """HTML with the entire <style> block removed."""
    return re.sub(r"<style[^>]*>.*?</style>", "", _valid_html(), flags=re.DOTALL)


# ---------------------------------------------------------------------------
# Schema fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def schema():
    schema_path = Path(__file__).parent.parent / "src" / "report" / "report_schema.json"
    return load_schema(schema_path)


# ---------------------------------------------------------------------------
# Section validation
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Chart validation
# ---------------------------------------------------------------------------


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
        assert any(
            "chart-title" in w.lower() or "action title" in w.lower()
            for w in result["warnings"]
        )

    def test_label_title_warns(self, schema):
        result = validate_html(_html_label_title(), schema)
        assert any(
            "action title" in w.lower() or "verb" in w.lower()
            for w in result["warnings"]
        )

    def test_missing_so_what_warns(self, schema):
        result = validate_html(_html_missing_so_what(), schema)
        assert any(
            "so-what" in w.lower() or "chart-so-what" in w.lower()
            for w in result["warnings"]
        )


# ---------------------------------------------------------------------------
# Citation validation
# ---------------------------------------------------------------------------


class TestCitationValidation:
    def test_citations_present_passes(self, schema):
        result = validate_html(_valid_html(), schema)
        cite_warnings = [w for w in result["warnings"] if "citation" in w.lower()]
        assert len(cite_warnings) == 0

    def test_missing_citation_warns(self, schema):
        result = validate_html(_html_missing_citation(), schema)
        assert any(
            "citation" in w.lower() or "PS-VD" in w
            for w in result["warnings"]
        )

    def test_methodology_exempt_from_citations(self, schema):
        """Methodology and appendix sections must not trigger citation warnings."""
        result = validate_html(_valid_html(), schema)
        # The valid HTML has methodology/appendix paragraphs without PS-VD citations.
        # No citation warning should mention these exempt sections.
        cite_warnings = [
            w for w in result["warnings"]
            if "citation" in w.lower() and "methodology" in w.lower()
        ]
        assert len(cite_warnings) == 0


# ---------------------------------------------------------------------------
# Navigation validation
# ---------------------------------------------------------------------------


class TestNavigationValidation:
    def test_heading_ids_present_passes(self, schema):
        result = validate_html(_valid_html(), schema)
        nav_errors = [
            e for e in result["errors"]
            if "heading" in e.lower() and "id" in e.lower()
        ]
        assert len(nav_errors) == 0

    def test_missing_heading_id_warns(self, schema):
        result = validate_html(_html_missing_heading_ids(), schema)
        assert any(
            "id" in w.lower() and ("heading" in w.lower() or "driver-ranking" in w.lower())
            for w in result["warnings"]
        )

    def test_missing_toc_warns(self, schema):
        result = validate_html(_html_missing_toc(), schema)
        assert any("toc" in w.lower() or "nav" in w.lower() for w in result["warnings"])


# ---------------------------------------------------------------------------
# CSS validation
# ---------------------------------------------------------------------------


class TestCSSValidation:
    def test_css_tokens_present_passes(self, schema):
        result = validate_html(_valid_html(), schema)
        css_warnings = [
            w for w in result["warnings"]
            if "css" in w.lower() or "token" in w.lower()
        ]
        assert len(css_warnings) == 0

    def test_missing_css_token_warns(self, schema):
        result = validate_html(_html_missing_css_tokens(), schema)
        assert any("--color-primary" in w for w in result["warnings"])

    def test_no_style_block_warns(self, schema):
        result = validate_html(_html_no_style_block(), schema)
        assert any("style" in w.lower() or "css" in w.lower() for w in result["warnings"])


# ---------------------------------------------------------------------------
# Regression check
# ---------------------------------------------------------------------------


class TestRegressionCheck:
    def test_no_base_run_skips_regression(self, schema):
        """Without base_run_dir, regression check is skipped entirely."""
        result = validate_html(_valid_html(), schema)
        regression_warnings = [
            w for w in result["warnings"]
            if "removed" in w.lower() or "deprecated" in w.lower()
        ]
        assert len(regression_warnings) == 0

    def test_removed_play_warns(self, schema, tmp_path):
        from src.report.report_validator import _check_regression

        base_dir = tmp_path / "base"
        current_dir = tmp_path / "current"
        (base_dir / "5-playbook").mkdir(parents=True)
        (current_dir / "5-playbook").mkdir(parents=True)

        base_playbook = {
            "plays": [
                {"play_id": "PLAY-001", "title": "Play 1"},
                {"play_id": "PLAY-002", "title": "Play 2"},
            ]
        }
        current_playbook = {
            "plays": [
                {"play_id": "PLAY-001", "title": "Play 1"},
            ]
        }

        (base_dir / "5-playbook" / "playbook.json").write_text(
            json.dumps(base_playbook)
        )
        (current_dir / "5-playbook" / "playbook.json").write_text(
            json.dumps(current_playbook)
        )

        warnings: list[str] = []
        _check_regression(base_dir, current_dir, warnings)
        assert any("PLAY-002" in w for w in warnings)

    def test_deprecated_play_no_warn(self, schema, tmp_path):
        from src.report.report_validator import _check_regression

        base_dir = tmp_path / "base"
        current_dir = tmp_path / "current"
        (base_dir / "5-playbook").mkdir(parents=True)
        (current_dir / "5-playbook").mkdir(parents=True)

        base_playbook = {
            "plays": [
                {"play_id": "PLAY-001", "title": "Play 1"},
                {"play_id": "PLAY-002", "title": "Play 2"},
            ]
        }
        current_playbook = {
            "plays": [
                {"play_id": "PLAY-001", "title": "Play 1"},
                {
                    "play_id": "PLAY-002",
                    "status": "deprecated",
                    "deprecated_reason": "Merged into PLAY-001",
                },
            ]
        }

        (base_dir / "5-playbook" / "playbook.json").write_text(
            json.dumps(base_playbook)
        )
        (current_dir / "5-playbook" / "playbook.json").write_text(
            json.dumps(current_playbook)
        )

        warnings: list[str] = []
        _check_regression(base_dir, current_dir, warnings)
        assert not any("PLAY-002" in w for w in warnings)


# ---------------------------------------------------------------------------
# Overall status
# ---------------------------------------------------------------------------


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
