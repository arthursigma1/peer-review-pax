#!/usr/bin/env python3
"""Claude Code SubagentStop hook: send per-agent summary traces to Langfuse.

Fires when a subagent completes. Summarizes: agent name, total tokens, duration,
output files produced. Tags with VDA pipeline metadata.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langfuse_utils import detect_agent_name, get_langfuse_client, is_tracing_enabled


def main() -> None:
    if not is_tracing_enabled():
        return

    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return

    client = get_langfuse_client()
    if not client:
        return

    try:
        session_id = payload.get("session_id", "unknown")
        agent_id = payload.get("agent_id", "unknown")
        model = payload.get("model", "unknown")
        duration_ms = payload.get("duration_ms", 0)

        usage = payload.get("usage", {})
        total_tokens = usage.get("total_tokens", 0)

        # Try to detect which VDA agent this was
        output_files = payload.get("output_files", [])
        agent_name = detect_agent_name(output_files)

        # Extract pipeline metadata
        metadata = payload.get("metadata", {})
        step = metadata.get("step", "unknown")
        ticker = metadata.get("ticker", "unknown")

        trace = client.trace(
            name=f"agent:{agent_name}",
            session_id=session_id,
            metadata={
                "agent_id": agent_id,
                "agent_name": agent_name,
                "model": model,
                "step": step,
                "ticker": ticker,
                "duration_ms": duration_ms,
                "total_tokens": total_tokens,
                "output_files": output_files,
                "hook_type": "SubagentStop",
            },
        )

        # Log generation summary
        trace.generation(
            name=f"{agent_name}-session",
            model=model,
            usage={"total": total_tokens},
            metadata={"duration_ms": duration_ms},
        )

        # Extract claim IDs from output files for trace↔claim bridge
        run_dir = metadata.get("run_dir", "")
        claim_ids = []
        claim_scores = []
        for filepath in output_files:
            full_path = os.path.join(run_dir, filepath) if run_dir else filepath
            if not os.path.exists(full_path):
                continue
            try:
                with open(full_path) as f:
                    file_data = json.load(f)
                for claim in file_data.get("_claims", []):
                    if isinstance(claim, dict) and "id" in claim:
                        claim_ids.append(claim["id"])
                        claim_scores.append(claim.get("score", -1))
            except (json.JSONDecodeError, OSError):
                continue

        if claim_ids:
            trace.update(
                metadata={
                    "claim_ids": claim_ids,
                    "claim_count": len(claim_ids),
                    "min_claim_score": min(claim_scores),
                },
            )

        client.flush()

    except Exception:
        pass


if __name__ == "__main__":
    main()
