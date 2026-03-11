# VDA Agent Orchestration Best Practices

Referenced from [CLAUDE.md](../CLAUDE.md).

Learned from 2026-03-09-run2 (best run to date). These patterns prevent agent stalls and context overflow:

1. **1-agent-per-firm for qualitative tasks** — Never assign 15 firms to a single agent. Each agent handles 1 firm (profile + actions). ~27K tokens each, zero stalls. Dispatch all 15 in parallel.
2. **No WebSearch for qualitative data** — Strategy profiles and strategic actions of major public alt-asset managers are well-known. Use training data only. WebSearch is the #1 context consumer and primary cause of stalls.
3. **Incremental file writing** — Instruct agents to write partial results every 3 firms. If they stall at firm 12, you still have 9 firms saved.
4. **Gap-fill pattern** — When an agent completes partially (e.g., 4 of 8 profiles), dispatch a smaller agent to fill ONLY the gap. Read existing file → append → overwrite. Never redo completed work.
5. **Split read-heavy from write-heavy** — Separate "research + profile" from "research + actions" into two parallel agents per firm if needed.
6. **Simplified schemas for large outputs** — `operational_prerequisites` with 7 nested subfields causes stalls. Use `op_prereq_summary` (single string) instead. Expand in post-processing if needed.
7. **Merge pattern for parallel per-firm agents** — Each agent writes to `profiles/{TICKER}.json` and `actions/{TICKER}.json`. A merge script combines all fragments into the canonical `strategy_profiles.json` and `strategic_actions.json`.
8. **Context budget rule of thumb** — Agents that read >3 files AND do WebSearch will likely stall before writing. Keep total input under 50K tokens per agent.
9. **Stall detection** — Monitor URL log line count + output file existence. If URL log is frozen for >5 min with no new output file, the agent has stalled. Redispatch immediately.
10. **`bypassPermissions` mode** — Background agents with `settings.local.json` restrictions silently fail on Write/Bash. Use `mode: bypassPermissions` or ensure permissions include `Write(**)`, `Bash(*)`.
