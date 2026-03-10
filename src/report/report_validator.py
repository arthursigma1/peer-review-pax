"""Report consistency validator for VDA final HTML reports.

Validates HTML reports against report_schema.json, checking sections,
charts, citations, navigation, CSS tokens, and play regression.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

_DEFAULT_SCHEMA_PATH = Path(__file__).parent / "report_schema.json"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load_schema(path: Path | None = None) -> dict[str, Any]:
    """Load report_schema.json from *path*, defaulting to the bundled copy."""
    schema_path = path if path is not None else _DEFAULT_SCHEMA_PATH
    return json.loads(Path(schema_path).read_text(encoding="utf-8"))


def validate_html(
    html: str,
    schema: dict[str, Any],
    base_run_dir: Path | None = None,
    current_run_dir: Path | None = None,
) -> dict[str, Any]:
    """Validate *html* against *schema*.

    Returns a verdict dict::

        {"status": "PASS|WARN|FAIL", "errors": [...], "warnings": [...]}

    ``"FAIL"`` when errors exist, ``"WARN"`` when only warnings exist,
    ``"PASS"`` otherwise.
    """
    soup = BeautifulSoup(html, "html.parser")
    errors: list[str] = []
    warnings: list[str] = []

    _check_sections(soup, schema, errors)
    _check_charts(soup, schema, warnings)
    _check_citations(soup, schema, warnings)
    _check_navigation(soup, schema, warnings)
    _check_css_tokens(html, schema, warnings)

    if base_run_dir is not None and current_run_dir is not None:
        _check_regression(base_run_dir, current_run_dir, warnings)

    if errors:
        status = "FAIL"
    elif warnings:
        status = "WARN"
    else:
        status = "PASS"

    return {"status": status, "errors": errors, "warnings": warnings}


# ---------------------------------------------------------------------------
# Private check functions
# ---------------------------------------------------------------------------


def _check_sections(
    soup: BeautifulSoup,
    schema: dict[str, Any],
    errors: list[str],
) -> None:
    """Check that all required sections are present by heading id."""
    canonical_ids: dict[str, str] = schema["sections"]["canonical_ids"]
    required: list[str] = schema["sections"]["required"]

    for section_name in required:
        section_id = canonical_ids.get(section_name, section_name)
        heading = soup.find(["h1", "h2", "h3"], id=section_id)
        if heading is None:
            errors.append(
                f"Missing required section: {section_id} (expected heading with id='{section_id}')"
            )


def _check_charts(
    soup: BeautifulSoup,
    schema: dict[str, Any],
    warnings: list[str],
) -> None:
    """Check chart figures: forbidden types, action titles (verbs), so-what captions."""
    chart_rules: dict[str, Any] = schema.get("chart_rules", {})
    forbidden_types: list[str] = chart_rules.get("forbidden_types", [])
    verbs: list[str] = schema.get("chart_title_verbs", [])

    figures = soup.find_all("figure", attrs={"data-chart-type": True})
    for fig in figures:
        chart_type: str = fig["data-chart-type"]

        # Forbidden chart type check
        if chart_type.lower() in [ft.lower() for ft in forbidden_types]:
            warnings.append(
                f"Forbidden chart type '{chart_type}' — use horizontalBar or heatmap instead"
            )

        # Chart title presence check
        title_el = fig.find(class_="chart-title")
        if title_el is None:
            warnings.append(
                "Chart missing chart-title element — every figure needs an action title"
            )
        else:
            # Action title verb check
            title_text: str = title_el.get_text(strip=True)
            if not any(verb in title_text for verb in verbs):
                warnings.append(
                    f"Chart action title '{title_text}' lacks an action verb — "
                    "titles should state what the data shows (e.g., 'drives', 'explains')"
                )

        # So-what caption presence check
        so_what_el = fig.find(class_="chart-so-what")
        if so_what_el is None:
            warnings.append(
                "Chart missing chart-so-what caption — every figure needs a so-what takeaway"
            )


def _check_citations(
    soup: BeautifulSoup,
    schema: dict[str, Any],
    warnings: list[str],
) -> None:
    """Check PS-VD-* citations in content paragraphs (exempt sections skip)."""
    citation_rules: dict[str, Any] = schema.get("citation_rules", {})
    required_prefix: str = citation_rules.get("required_prefix", "PS-VD-")
    exempt_section_names: list[str] = citation_rules.get("exempt_sections", [])

    canonical_ids: dict[str, str] = schema["sections"]["canonical_ids"]

    # Map exempt section names to their canonical IDs
    exempt_ids: set[str] = set()
    for name in exempt_section_names:
        section_id = canonical_ids.get(name, name)
        exempt_ids.add(section_id)

    # Walk h2 and p elements tracking the current section
    current_section_id: str | None = None
    for element in soup.find_all(["h2", "p"]):
        if element.name == "h2":
            current_section_id = element.get("id") or current_section_id
        elif element.name == "p":
            if current_section_id in exempt_ids:
                continue
            # Skip paragraphs inside figures (chart captions, so-what, etc.)
            if element.find_parent("figure") is not None:
                continue
            text = element.get_text()
            if len(text.strip()) <= 20:
                continue
            if required_prefix not in text:
                warnings.append(
                    f"Paragraph missing PS-VD citation in section '{current_section_id}': "
                    f"'{text.strip()[:60]}...'"
                )


def _check_navigation(
    soup: BeautifulSoup,
    schema: dict[str, Any],
    warnings: list[str],
) -> None:
    """Check heading IDs and nav.toc presence."""
    nav_config: dict[str, Any] = schema.get("navigation", {})

    # Check that all h2/h3 headings have an id attribute
    if nav_config.get("require_heading_ids", True):
        for heading in soup.find_all(["h2", "h3"]):
            if not heading.get("id"):
                heading_text = heading.get_text(strip=True)
                warnings.append(
                    f"Heading missing id attribute: '{heading_text}' — "
                    f"add an id so the table of contents can link to it "
                    f"(suggested: driver-ranking)"
                )

    # Check for nav.toc component
    if nav_config.get("require_toc_component", True):
        toc_selector: str = nav_config.get("toc_selector", "nav.toc")
        # Parse selector: e.g. "nav.toc" → tag="nav", class="toc"
        match = re.match(r"^(\w+)\.(\S+)$", toc_selector)
        if match:
            tag, css_class = match.group(1), match.group(2)
            toc_el = soup.find(tag, class_=css_class)
        else:
            toc_el = soup.select_one(toc_selector)

        if toc_el is None:
            warnings.append(
                f"Missing nav.toc component — add a <nav class='toc'> table of contents"
            )


def _check_css_tokens(
    html: str,
    schema: dict[str, Any],
    warnings: list[str],
) -> None:
    """Check CSS custom properties in the style block."""
    required_tokens: list[str] = schema.get("css_required_tokens", [])

    # Find the <style> block
    style_match = re.search(r"<style[^>]*>(.*?)</style>", html, re.DOTALL | re.IGNORECASE)
    if style_match is None:
        warnings.append(
            "No <style> block found — CSS design tokens are missing from the report"
        )
        return

    style_content = style_match.group(1)

    for token in required_tokens:
        if token not in style_content:
            warnings.append(
                f"Missing CSS token '{token}' — add it to the :root block in the style block"
            )


def _check_regression(
    base_run_dir: Path,
    current_run_dir: Path,
    warnings: list[str],
) -> None:
    """Check for plays removed between base run and current run without deprecation."""
    base_playbook_path = Path(base_run_dir) / "5-playbook" / "playbook.json"
    current_playbook_path = Path(current_run_dir) / "5-playbook" / "playbook.json"

    if not base_playbook_path.exists() or not current_playbook_path.exists():
        return

    base_data = json.loads(base_playbook_path.read_text(encoding="utf-8"))
    current_data = json.loads(current_playbook_path.read_text(encoding="utf-8"))

    base_plays: set[str] = {p["play_id"] for p in base_data.get("plays", [])}
    current_plays_list = current_data.get("plays", [])

    current_plays: set[str] = {p["play_id"] for p in current_plays_list}

    # Plays that are present in current but marked deprecated WITH a reason
    deprecated: set[str] = {
        p["play_id"]
        for p in current_plays_list
        if p.get("status") == "deprecated" and p.get("deprecated_reason")
    }

    removed = base_plays - current_plays - deprecated

    for play_id in sorted(removed):
        warnings.append(
            f"Play {play_id} was removed without a deprecation reason — "
            "add 'status': 'deprecated' and 'deprecated_reason' to the current playbook"
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Validate a VDA final HTML report against report_schema.json"
    )
    parser.add_argument(
        "--html",
        type=Path,
        required=True,
        help="Path to the HTML report to validate",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=None,
        help="Path to report_schema.json (defaults to bundled copy)",
    )
    parser.add_argument(
        "--base-run",
        type=Path,
        default=None,
        help="Base run directory for regression check (e.g. data/processed/pax/2026-03-09-run2)",
    )
    parser.add_argument(
        "--current-run",
        type=Path,
        default=None,
        help="Current run directory (defaults to html_path.parent.parent)",
    )
    return parser


def main() -> None:
    """CLI entry point: reads HTML, runs validation, prints JSON, exits with code."""
    parser = build_parser()
    args = parser.parse_args()

    html_path: Path = args.html
    html = html_path.read_text(encoding="utf-8")

    schema = load_schema(args.schema)

    current_run_dir: Path | None = args.current_run
    if current_run_dir is None and html_path is not None:
        current_run_dir = html_path.parent.parent

    result = validate_html(
        html,
        schema,
        base_run_dir=args.base_run,
        current_run_dir=current_run_dir,
    )

    print(json.dumps(result, indent=2))
    sys.exit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
