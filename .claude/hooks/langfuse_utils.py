"""Shared utilities for Langfuse tracing hooks.

Used by langfuse_trace.py (Stop hook) and langfuse_subagent_trace.py (SubagentStop hook).
"""

from __future__ import annotations

import os
from pathlib import Path

# Load .env from project root (hooks run as standalone scripts).
# Only loads once; skipped if _LANGFUSE_ENV_LOADED is set (e.g., by tests).
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_ENV_FILE = _PROJECT_ROOT / ".env"
if _ENV_FILE.exists() and "_LANGFUSE_ENV_LOADED" not in os.environ:
    for line in _ENV_FILE.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())
    os.environ["_LANGFUSE_ENV_LOADED"] = "1"

# Maps output filename patterns to VDA agent names (mirrors FILE_TO_AGENT in usePipeline.ts)
_FILE_TO_AGENT: dict[str, str] = {
    "peer_universe.json": "universe-scout",
    "source_catalog.json": "source-mapper",
    "metric_taxonomy.json": "metric-architect",
    "quantitative_tier1.json": "data-collector-t1",
    "quantitative_tier2.json": "data-collector-t2",
    "quantitative_tier3.json": "data-collector-t3",
    "strategy_profiles.json": "strategy-extractor",
    "strategic_actions.json": "strategy-extractor",
    "standardized_matrix.json": "metric-architect",
    "correlation_results.json": "metric-architect",
    "driver_ranking.json": "metric-architect",
    "data_gaps.json": "metric-architect",
    "platform_profiles.json": "platform-analyst",
    "asset_class_analysis.json": "vertical-analyst",
    "platform_playbook.json": "playbook-synthesizer",
    "asset_class_playbooks.json": "playbook-synthesizer",
    "playbook.json": "playbook-synthesizer",
    "target_lens.json": "target-lens",
    "final_report.html": "report-builder",
    "audit_cp1_data.json": "claim-auditor",
    "audit_cp2_deep_dives.json": "claim-auditor",
    "audit_cp3_playbook.json": "claim-auditor",
}


def is_tracing_enabled() -> bool:
    """Check if Langfuse tracing is opted in."""
    return os.environ.get("TRACE_TO_LANGFUSE", "").lower() == "true"


def detect_agent_name(output_files: list[str]) -> str:
    """Detect the VDA agent name from output file paths."""
    for filepath in output_files:
        filename = filepath.rsplit("/", 1)[-1] if "/" in filepath else filepath
        if filename in _FILE_TO_AGENT:
            return _FILE_TO_AGENT[filename]
    return "unknown"


def get_langfuse_client():
    """Create and return a Langfuse client. Returns None if keys not configured.

    Langfuse v3 reads LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, and LANGFUSE_HOST
    from environment variables automatically.
    """
    try:
        from langfuse import Langfuse
        return Langfuse()
    except Exception:
        return None
