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
