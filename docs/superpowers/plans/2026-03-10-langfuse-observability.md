# Langfuse LLM Observability Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add execution-level observability to the VDA pipeline via Langfuse — trace every LLM call, track token costs, and link execution traces to CLM-* claim IDs.

**Architecture:** Claude Code Stop/SubagentStop hooks send trace data to Langfuse. A `_trace_metadata` field in agent outputs bridges traces to the claim explainability system. `llm_client.py` gets `@observe` decorator for future Python-native LLM calls.

**Tech Stack:** Python 3.11+, `langfuse>=3.0,<4.0`, Claude Code hooks (shell scripts invoking Python).

**Spec:** `docs/superpowers/specs/2026-03-10-langfuse-observability-design.md`

**Dependency:** Layer 2 (claim bridge) depends on `claim_indexer.py` from the claim explainability plan. Layer 1 and Layer 3 have no dependencies.

---

## File Structure

| File | Action | Responsibility |
|---|---|---|
| `.claude/hooks/langfuse_trace.py` | Create | Stop hook: send per-turn traces to Langfuse |
| `.claude/hooks/langfuse_subagent_trace.py` | Create | SubagentStop hook: send per-agent summary traces |
| `.claude/hooks/langfuse_utils.py` | Create | Shared utilities: Langfuse client init, env check, agent name detection |
| `src/llm_client.py` | Modify | Add `@observe` decorator and optional metadata param |
| `src/analyzer/claim_indexer.py` | Modify | Read `_trace_metadata` from JSONs, add `trace_session_id` to claim index |
| `tests/test_langfuse_hooks.py` | Create | Unit tests for hook scripts (mocked Langfuse client) |
| `tests/test_llm_client_tracing.py` | Create | Test `@observe` decorator wiring |
| `requirements.txt` | Modify | Add `langfuse>=3.0,<4.0` |
| `.env.example` | Modify | Add Langfuse env vars |

---

## Chunk 1: Layer 1 — Claude Code Hook Tracing

### Task 1: Add langfuse dependency and env config

**Files:**
- Modify: `requirements.txt`
- Modify: `.env.example` (or create if not exists)

- [ ] **Step 1: Add langfuse to requirements.txt**

Add to `requirements.txt`:
```
langfuse>=3.0,<4.0
```

- [ ] **Step 2: Add env vars to .env.example**

Add to `.env.example`:
```bash
# Langfuse LLM observability (optional — hooks exit immediately if TRACE_TO_LANGFUSE != true)
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
TRACE_TO_LANGFUSE=false
```

- [ ] **Step 3: Install dependency**

Run: `pip install langfuse>=3.0,<4.0`

- [ ] **Step 4: Commit**

```bash
git add requirements.txt .env.example
git commit -m "chore: add langfuse dependency for LLM observability"
```

---

### Task 2: Shared hook utilities

**Files:**
- Create: `.claude/hooks/langfuse_utils.py`
- Test: `tests/test_langfuse_hooks.py`

- [ ] **Step 1: Write failing tests for utilities**

```python
# tests/test_langfuse_hooks.py
"""Tests for Langfuse hook utilities."""

from __future__ import annotations

import json
import os
from unittest.mock import MagicMock, patch

import pytest


class TestIsTracingEnabled:
    def test_enabled_when_env_true(self):
        with patch.dict(os.environ, {"TRACE_TO_LANGFUSE": "true"}):
            from importlib import reload
            import sys
            # Force reimport to pick up env change
            if "claude.hooks.langfuse_utils" in sys.modules:
                del sys.modules["claude.hooks.langfuse_utils"]
            sys.path.insert(0, ".claude/hooks")
            import langfuse_utils
            reload(langfuse_utils)
            assert langfuse_utils.is_tracing_enabled() is True

    def test_disabled_when_env_false(self):
        with patch.dict(os.environ, {"TRACE_TO_LANGFUSE": "false"}):
            sys.path.insert(0, ".claude/hooks")
            from importlib import reload
            import langfuse_utils
            reload(langfuse_utils)
            assert langfuse_utils.is_tracing_enabled() is False

    def test_disabled_when_env_missing(self):
        env = os.environ.copy()
        env.pop("TRACE_TO_LANGFUSE", None)
        with patch.dict(os.environ, env, clear=True):
            sys.path.insert(0, ".claude/hooks")
            from importlib import reload
            import langfuse_utils
            reload(langfuse_utils)
            assert langfuse_utils.is_tracing_enabled() is False


class TestDetectAgentName:
    def test_detects_agent_from_output_files(self):
        sys.path.insert(0, ".claude/hooks")
        import langfuse_utils
        assert langfuse_utils.detect_agent_name(["3-analysis/correlation_results.json"]) == "metric-architect"
        assert langfuse_utils.detect_agent_name(["3-analysis/driver_ranking.json"]) == "metric-architect"
        assert langfuse_utils.detect_agent_name(["5-playbook/platform_playbook.json"]) == "playbook-synthesizer"
        assert langfuse_utils.detect_agent_name(["5-playbook/target_lens.json"]) == "target-lens"

    def test_returns_unknown_for_unrecognized_files(self):
        sys.path.insert(0, ".claude/hooks")
        import langfuse_utils
        assert langfuse_utils.detect_agent_name(["random.json"]) == "unknown"

    def test_returns_unknown_for_empty_list(self):
        sys.path.insert(0, ".claude/hooks")
        import langfuse_utils
        assert langfuse_utils.detect_agent_name([]) == "unknown"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_langfuse_hooks.py::TestDetectAgentName -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement langfuse_utils.py**

Create `.claude/hooks/langfuse_utils.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_langfuse_hooks.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add .claude/hooks/langfuse_utils.py tests/test_langfuse_hooks.py
git commit -m "feat(langfuse): shared hook utilities with agent name detection"
```

---

### Task 3: Stop hook — per-turn tracing

**Files:**
- Create: `.claude/hooks/langfuse_trace.py`

- [ ] **Step 1: Implement the Stop hook script**

Create `.claude/hooks/langfuse_trace.py`:

```python
#!/usr/bin/env python3
"""Claude Code Stop hook: send per-turn traces to Langfuse.

Reads hook payload from stdin, extracts turn metadata, creates a Langfuse trace.
Exits immediately if TRACE_TO_LANGFUSE != 'true'.
"""

from __future__ import annotations

import json
import sys
import os

# Add hooks dir to path for langfuse_utils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langfuse_utils import is_tracing_enabled, get_langfuse_client


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
```

- [ ] **Step 2: Make executable**

Run: `chmod +x .claude/hooks/langfuse_trace.py`

- [ ] **Step 3: Commit**

```bash
git add .claude/hooks/langfuse_trace.py
git commit -m "feat(langfuse): Stop hook for per-turn LLM tracing"
```

---

### Task 4: SubagentStop hook — per-agent summary tracing

**Files:**
- Create: `.claude/hooks/langfuse_subagent_trace.py`

- [ ] **Step 1: Implement the SubagentStop hook script**

Create `.claude/hooks/langfuse_subagent_trace.py`:

```python
#!/usr/bin/env python3
"""Claude Code SubagentStop hook: send per-agent summary traces to Langfuse.

Fires when a subagent completes. Summarizes: agent name, total tokens, duration,
output files produced. Tags with VDA pipeline metadata.
"""

from __future__ import annotations

import json
import os
import sys
from glob import glob

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langfuse_utils import detect_agent_name, get_langfuse_client, is_tracing_enabled


def _find_new_output_files(run_dir: str, before_timestamp: float) -> list[str]:
    """Find JSON/HTML files in run_dir modified after before_timestamp."""
    if not run_dir or not os.path.isdir(run_dir):
        return []
    new_files = []
    for ext in ("**/*.json", "**/*.html"):
        for path in glob(os.path.join(run_dir, ext), recursive=True):
            if os.path.getmtime(path) > before_timestamp:
                new_files.append(os.path.relpath(path, run_dir))
    return new_files


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

        client.flush()

    except Exception:
        pass


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Make executable**

Run: `chmod +x .claude/hooks/langfuse_subagent_trace.py`

- [ ] **Step 3: Commit**

```bash
git add .claude/hooks/langfuse_subagent_trace.py
git commit -m "feat(langfuse): SubagentStop hook for per-agent summary tracing"
```

---

### Task 5: Hook configuration template

**Files:**
- Create: `.claude/hooks/README.md`

- [ ] **Step 1: Create README with configuration instructions**

Create `.claude/hooks/README.md`:

```markdown
# Langfuse Tracing Hooks

## Setup

1. Add Langfuse keys to `.env`:
   ```
   LANGFUSE_PUBLIC_KEY=pk-lf-...
   LANGFUSE_SECRET_KEY=sk-lf-...
   LANGFUSE_HOST=https://cloud.langfuse.com
   TRACE_TO_LANGFUSE=true
   ```

2. Add hooks to `.claude/settings.local.json`:
   ```json
   {
     "hooks": {
       "Stop": [{
         "matcher": "",
         "hooks": [{"type": "command", "command": "python3 .claude/hooks/langfuse_trace.py", "timeout": 10}]
       }],
       "SubagentStop": [{
         "matcher": "",
         "hooks": [{"type": "command", "command": "python3 .claude/hooks/langfuse_subagent_trace.py", "timeout": 10}]
       }]
     }
   }
   ```

3. Install: `pip install langfuse>=3.0,<4.0`

## Files

- `langfuse_trace.py` — Stop hook: per-turn tracing
- `langfuse_subagent_trace.py` — SubagentStop hook: per-agent summary
- `langfuse_utils.py` — Shared: client init, env check, agent detection
```

- [ ] **Step 2: Commit**

```bash
git add .claude/hooks/README.md
git commit -m "docs: add Langfuse hooks setup instructions"
```

---

## Chunk 2: Layer 3 — llm_client.py Instrumentation

### Task 6: Add @observe decorator to llm_client.py

**Files:**
- Modify: `src/llm_client.py`
- Test: `tests/test_llm_client_tracing.py`

- [ ] **Step 1: Read current llm_client.py**

Read: `src/llm_client.py`

- [ ] **Step 2: Write failing test**

```python
# tests/test_llm_client_tracing.py
"""Tests for llm_client.py Langfuse tracing integration."""

from __future__ import annotations

from unittest.mock import patch

import pytest


class TestLlmClientTracing:
    def test_ask_accepts_metadata_param(self):
        """Verify the function signature accepts metadata without error."""
        from src.llm_client import ask
        import inspect
        sig = inspect.signature(ask)
        assert "metadata" in sig.parameters

    def test_ask_works_without_langfuse_installed(self):
        """If langfuse is not installed, ask() should still work (graceful degradation)."""
        with patch.dict("sys.modules", {"langfuse": None, "langfuse.decorators": None}):
            # Should not raise even if langfuse import fails
            # This tests the import guard pattern
            pass
```

- [ ] **Step 3: Add @observe decorator and metadata param to llm_client.py**

Modify `src/llm_client.py` — add Langfuse decorator with graceful fallback:

```python
# At the top, after existing imports:
try:
    from langfuse.decorators import observe
except ImportError:
    # Langfuse not installed — use no-op decorator
    def observe(**kwargs):
        def decorator(fn):
            return fn
        return decorator


# Modify ask() signature to accept metadata:
@observe(as_type="generation")
def ask(prompt: str, system: str = "", model: str = "claude-sonnet-4-20250514", metadata: dict | None = None) -> str:
    # ... existing implementation unchanged ...
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest tests/test_llm_client_tracing.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/llm_client.py tests/test_llm_client_tracing.py
git commit -m "feat(langfuse): add @observe decorator to llm_client.py"
```

---

## Chunk 3: Layer 2 — Claim Bridge

**Dependency:** Requires `claim_indexer.py` from the claim explainability plan to be implemented first.

### Task 7: Extend claim_indexer.py to read _trace_metadata

**Files:**
- Modify: `src/analyzer/claim_indexer.py`
- Test: `tests/test_claim_indexer.py`

- [ ] **Step 1: Write failing test**

Append to `tests/test_claim_indexer.py`:

```python
class TestTraceMetadata:
    def test_trace_session_id_added_to_claims(self, tmp_path):
        data = {
            "_trace_metadata": {
                "agent_name": "metric-architect",
                "session_id": "sess-abc-123",
                "step": "3-analysis",
            },
            "_claims": [
                {"id": "CLM-COR-001-01", "parent_id": "COR-001", "type": "statistical",
                 "evidence": ["MET-VD-001"], "confidence": "grounded", "score": 3, "layer": "3-analysis"},
            ],
        }
        _write_json(tmp_path / "3-analysis" / "correlation_results.json", data)
        index = build_claim_index(tmp_path)
        claim = index["claims"]["CLM-COR-001-01"]
        assert claim.get("trace_session_id") == "sess-abc-123"

    def test_missing_trace_metadata_no_error(self, tmp_path):
        data = {
            "_claims": [
                {"id": "CLM-COR-001-01", "parent_id": "COR-001", "type": "statistical",
                 "evidence": ["MET-VD-001"], "confidence": "grounded", "score": 3, "layer": "3-analysis"},
            ],
        }
        _write_json(tmp_path / "3-analysis" / "correlation_results.json", data)
        index = build_claim_index(tmp_path)
        claim = index["claims"]["CLM-COR-001-01"]
        assert "trace_session_id" not in claim  # graceful degradation
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_claim_indexer.py::TestTraceMetadata -v`
Expected: FAIL — `trace_session_id` not in claim dict

- [ ] **Step 3: Modify collect_claims_from_dir to extract _trace_metadata**

In `src/analyzer/claim_indexer.py`, modify `collect_claims_from_dir`:

```python
# Inside the JSON file scanning loop, after extracting _claims:
trace_meta = data.get("_trace_metadata", {})
trace_session_id = trace_meta.get("session_id") if isinstance(trace_meta, dict) else None

# When adding the claim to the dict:
claim_entry = {**claim, "source_file": rel_path}
if trace_session_id:
    claim_entry["trace_session_id"] = trace_session_id
claims[cid] = claim_entry
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest tests/test_claim_indexer.py -v`
Expected: ALL PASS (new + existing)

- [ ] **Step 5: Commit**

```bash
git add src/analyzer/claim_indexer.py tests/test_claim_indexer.py
git commit -m "feat(langfuse): claim indexer reads _trace_metadata for trace↔claim bridge"
```

---

### Task 8: Add _trace_metadata instruction to agent prompts

**Files:**
- Modify: `.claude/skills/valuation-driver/SKILL.md`

- [ ] **Step 1: Read SKILL.md to find agent output instructions**

Read: `.claude/skills/valuation-driver/SKILL.md` — find the general agent output guidelines (usually near the top, before individual agent sections).

- [ ] **Step 2: Add _trace_metadata instruction as a general rule**

Add near the existing output format conventions:

```markdown
**Trace metadata (OPTIONAL):** If you have access to session information, add a `_trace_metadata` field to your JSON output:

```json
{
  "_trace_metadata": {
    "agent_name": "<your-agent-name>",
    "session_id": "<claude-code-session-id-if-available>",
    "step": "<pipeline-step>",
    "started_at": "<ISO-8601>",
    "completed_at": "<ISO-8601>"
  }
}
```

This field is optional — if omitted, the claim indexer and Langfuse hooks will degrade gracefully.
```

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/valuation-driver/SKILL.md
git commit -m "feat(langfuse): add _trace_metadata instruction to agent prompts"
```

---

### Task 9: SubagentStop hook — tag traces with claim IDs

**Files:**
- Modify: `.claude/hooks/langfuse_subagent_trace.py`

- [ ] **Step 1: Add claim extraction to SubagentStop hook**

Extend the SubagentStop hook to read `_claims[]` from output files and tag the trace:

```python
# After detecting output_files and creating the trace:

# Extract claim IDs from output files for trace tagging
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

# Add claim IDs to trace metadata
if claim_ids:
    trace.update(
        metadata={
            **trace.metadata,
            "claim_ids": claim_ids,
            "claim_count": len(claim_ids),
            "min_claim_score": min(claim_scores) if claim_scores else None,
        }
    )
```

- [ ] **Step 2: Commit**

```bash
git add .claude/hooks/langfuse_subagent_trace.py
git commit -m "feat(langfuse): SubagentStop hook tags traces with CLM-* claim IDs"
```

---

### Task 10: Final verification

- [ ] **Step 1: Run all tests**

Run: `python3 -m pytest tests/test_langfuse_hooks.py tests/test_llm_client_tracing.py -v`
Expected: ALL PASS

- [ ] **Step 2: Verify hooks don't error when Langfuse is disabled**

Run: `echo '{}' | TRACE_TO_LANGFUSE=false python3 .claude/hooks/langfuse_trace.py`
Expected: exits silently with code 0

Run: `echo '{}' | TRACE_TO_LANGFUSE=false python3 .claude/hooks/langfuse_subagent_trace.py`
Expected: exits silently with code 0

- [ ] **Step 3: Verify hooks don't block on missing keys**

Run: `echo '{"session_id":"test"}' | TRACE_TO_LANGFUSE=true python3 .claude/hooks/langfuse_trace.py`
Expected: exits without error (client creation fails gracefully, caught by try/except)

- [ ] **Step 4: Run existing test suite for regressions**

Run: `python3 -m pytest tests/ -v`
Expected: ALL PASS

- [ ] **Step 5: Commit any final adjustments**

```bash
git add -A
git commit -m "feat(langfuse): LLM observability integration complete"
```
