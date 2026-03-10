# Langfuse LLM Observability Integration

**Date:** 2026-03-10
**Status:** Approved
**Goal:** Execution-level observability for the VDA pipeline — which LLM call produced which output, token costs, latency per agent, post-hoc hallucination debugging. Complements the claim-level explainability system (which evidence supports which argument) with call-level traceability (which LLM call produced which output).

## Why Langfuse over LangSmith

| Criterion | LangSmith | Langfuse |
|---|---|---|
| Free tier | 5K traces/month | 1M traces/month |
| Self-hosted | No | Yes (MIT, Docker Compose) |
| Open source | No | Yes |
| LangChain required | No, but native ecosystem | No |
| Anthropic SDK support | `wrap_anthropic` | `@observe` decorator + OTel |
| Claude Code hooks integration | Via Stop hooks | Via Stop hooks |

A single VDA run with 13 agents produces 200+ traces. Langfuse's free tier is 200x larger. Self-hosting matters for sensitive financial analysis data.

## Architectural Reality

**Critical insight:** The VDA pipeline does NOT make LLM calls through `src/llm_client.py`. The pipeline is entirely orchestrated through Claude Code's `Agent`/`TeamCreate`/`SendMessage` tools, which spawn subagent CLI processes. The LLM calls happen inside Claude Code's runtime.

This means: traditional SDK-level instrumentation (`wrap_anthropic`, `@observe`) applied to `llm_client.py` would instrument **nothing**. Observability must enter via **Claude Code hooks** (Stop, SubagentStop).

```
User runs /valuation-driver PAX
    ↓
Tauri spawns Claude Code CLI via PTY
    ↓
Orchestrator uses TeamCreate → Agent (13 subagents)
    ↓ (each subagent is a separate Claude Code process)
Stop hook fires after each assistant turn → Python script → Langfuse trace
SubagentStop hook fires when subagent completes → Python script → Langfuse trace summary
```

## Design: Three Layers

### Layer 1: Claude Code Hook Tracing (Primary)

Captures every conversation turn across all 13+ agents as Langfuse traces.

**How it works:** Claude Code's `Stop` hook fires after each assistant response. A Python script reads the hook payload, extracts the latest turn metadata, and sends it to Langfuse.

**Stop hook script** (`.claude/hooks/langfuse_trace.py`):
- Reads `stdin` for hook payload (JSON with session info)
- Extracts: model name, input/output tokens, tool calls, agent name (from `@agent-name` pattern)
- Creates a Langfuse trace with:
  - `session_id` — groups all turns from one Claude Code session (= one VDA run)
  - `name` — agent name (e.g., "universe-scout", "metric-architect")
  - `metadata` — pipeline step, ticker, run date
- Creates generation span for the LLM call with token counts
- Creates tool spans for each tool call (Read, Write, Bash, WebSearch, Agent, SendMessage)
- Uses async flush — non-blocking, <10ms overhead per hook

**SubagentStop hook script** (`.claude/hooks/langfuse_subagent_trace.py`):
- Fires when each subagent completes
- Summarizes: total tokens, duration, output files produced
- Tags with VDA metadata: agent name (via FILE_TO_AGENT-style lookup), pipeline step
- Enables post-hoc: "which agent consumed the most tokens?" "which agent stalled?"

**Configuration:** `.claude/settings.local.json` (project-level, not committed):
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

**Opt-in:** Hooks check `TRACE_TO_LANGFUSE=true` env var. Exit immediately if not set — zero overhead when disabled.

### Layer 2: Claim Bridge (Links traces to CLM-* IDs)

Bridges the gap between Langfuse execution traces and the claim explainability system.

**Problem:** Langfuse traces capture *which LLM call produced which text*. The claim system knows *which claims exist and their evidence chains*. Neither knows about the other.

**Solution:**

1. **`_trace_metadata` in agent output files.** Agent prompts include instruction to add:
   ```json
   {
     "_trace_metadata": {
       "agent_name": "metric-architect",
       "session_id": "...",
       "step": "3-analysis",
       "started_at": "ISO-8601",
       "completed_at": "ISO-8601"
     }
   }
   ```
   The `session_id` creates a join key between Langfuse traces and pipeline output files.

2. **`claim_indexer.py` extension.** When processing `_claims[]`, also reads `_trace_metadata` and adds `trace_session_id` to each claim in `claim_index.json`. Enables: "Show me the Langfuse trace for the LLM call that produced CLM-DVR-010-01."

3. **SubagentStop hook enrichment.** After subagent completes, reads its output file(s), extracts `_claims[]`, tags the Langfuse trace with claim IDs. Enables reverse query in Langfuse: "Show me all traces that produced claims with score < 2."

### Layer 3: `llm_client.py` Instrumentation (Future-proofing)

Instruments `src/llm_client.py` so any future Python code making direct Anthropic API calls is automatically traced.

```python
from langfuse.decorators import observe

@observe(as_type="generation")
def ask(prompt: str, system: str = "", model: str = "claude-sonnet-4-20250514", metadata: dict | None = None) -> str:
    # existing implementation
```

Currently provides zero value (nothing calls `llm_client.py`), but becomes valuable if the project adds Python-native LLM pipelines (e.g., claim_indexer using LLM for claim quality assessment).

## Dependencies

```
Layer 1 (hooks) ──── can start immediately, zero code dependencies
     │
     ├── Layer 2 (claim bridge) ── depends on claim_indexer.py from explainability spec
     │                              depends on Layer 1 being operational
     │
     └── Layer 3 (llm_client) ──── independent, can be done in parallel with anything
```

**Required packages:** `langfuse>=3.0,<4.0`

**Environment variables (`.env`, never committed):**
- `LANGFUSE_PUBLIC_KEY`
- `LANGFUSE_SECRET_KEY`
- `LANGFUSE_HOST` — `https://cloud.langfuse.com` (cloud) or self-hosted URL
- `TRACE_TO_LANGFUSE=true` — opt-in flag

## Risks

| Risk | Mitigation |
|---|---|
| Hook timeout slows pipeline | `timeout: 10` in config; Langfuse SDK v3 async flush is non-blocking |
| Subagent identification unreliable | Use FILE_TO_AGENT output file detection pattern from `usePipeline.ts` |
| Token count extraction from transcripts | Fall back to estimating from message length; Langfuse auto-infers costs from model name |
| Self-hosted adds infrastructure | Start with Langfuse Cloud free tier; migrate to self-hosted only if data sensitivity requires |
| `_trace_metadata` not reliably emitted by agents | Make it optional in `claim_indexer.py`; Layer 2 degrades gracefully |

## Estimated Effort

| Layer | Effort | Value |
|---|---|---|
| Layer 1: Claude Code hooks | 4 hours | High — full agent-level observability |
| Layer 2: Claim bridge | 11 hours | High — bidirectional trace↔claim linkage |
| Layer 3: `llm_client.py` | 1 hour | Low (future-proofing) |
| **Total** | **16 hours** | |
