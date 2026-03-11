#!/usr/bin/env python3
"""Claude Code Stop hook: send per-turn traces to Langfuse.

Reads hook payload from stdin, extracts turn metadata, creates a Langfuse trace.
Exits immediately if TRACE_TO_LANGFUSE != 'true'.
"""

from __future__ import annotations

import json
import os
import sys

# Add hooks dir to path for langfuse_utils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langfuse_utils import get_langfuse_client, is_tracing_enabled


def main() -> None:
    if not is_tracing_enabled():
        return

    # Read hook payload from stdin
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return

    client = get_langfuse_client()
    if not client:
        return

    try:
        session_id = payload.get("session_id", "unknown")
        model = payload.get("model", "unknown")

        # Extract token usage if available
        usage = payload.get("usage", {})
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)

        # Extract tool calls
        tool_calls = payload.get("tool_calls", [])

        trace = client.trace(
            name="claude-code-turn",
            session_id=session_id,
            metadata={
                "model": model,
                "tool_count": len(tool_calls),
                "hook_type": "Stop",
            },
        )

        # Log the generation
        trace.generation(
            name="llm-call",
            model=model,
            usage={
                "input": input_tokens,
                "output": output_tokens,
            },
        )

        # Log each tool call as a span
        for tc in tool_calls:
            trace.span(
                name=tc.get("name", "unknown-tool"),
                metadata={"tool_input_preview": str(tc.get("input", ""))[:200]},
            )

        client.flush()

    except Exception:
        pass  # Never block the pipeline on tracing failures


if __name__ == "__main__":
    main()
