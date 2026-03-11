"""Shared utilities for Langfuse tracing hooks.

Used by langfuse_trace.py (Stop hook) and langfuse_subagent_trace.py (SubagentStop hook).
"""

from __future__ import annotations

import os

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
    """Create and return a Langfuse client. Returns None if keys not configured."""
    try:
        from langfuse import Langfuse
        return Langfuse(
            public_key=os.environ.get("LANGFUSE_PUBLIC_KEY", ""),
            secret_key=os.environ.get("LANGFUSE_SECRET_KEY", ""),
            host=os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com"),
        )
    except Exception:
        return None
