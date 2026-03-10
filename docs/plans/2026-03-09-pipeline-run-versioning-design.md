# Pipeline Run Versioning & History — Design

**Date:** 2026-03-09
**Status:** Approved

## Problem

1. `pipeline_state.json` is saved at the ticker root (`data/processed/pax/pipeline_state.json`) when `runDate` is null, overwriting previous run states.
2. On app boot, `restore()` auto-loads this stale state (with `isRunning: true`) regardless of which ticker the user wants to view.
3. Switching tickers does not reset pipeline state — the old run keeps showing.

## Solution: Run Picker in Header + Per-Run State Persistence

### Bug Fix: Always assign runDate on start

In `usePipeline.ts`, the `start()` function generates a `runDate` if none is provided:

```ts
const today = new Date().toISOString().split("T")[0]; // "2026-03-09"
setRunDate(nextRunDate ?? today);
```

This ensures `saveState()` always writes to `{ticker}/{run-date}/pipeline_state.json`, never the ticker root.

### Remove auto-restore on boot

Remove the `useEffect` in `App.tsx` (lines 263–274) that auto-calls `pipeline.restore()` from `localStorage`. Boot state is always clean; the run picker drives loading.

### Run picker in header

A dropdown added to the app header between the ticker badge and the nav tabs:

```
[VDA Pipeline Dashboard] [PAX]  [2026-03-09-run2 ▾]    [New Analysis ⌘1] [Pipeline ⌘2] ...
```

**Behavior:**
- Visible only when `runs.length > 0` and a ticker is active
- Lists runs newest-first (backend already sorts this way)
- Active run highlighted with blue dot
- Live run (isRunning) shows pulsing green dot
- On select: calls `pipeline.restore(ticker, runDate)`, falls back to `pipeline.loadExistingSession(ticker, runDate)` if no saved state
- On new run start: auto-selects the new run in the picker

### Ticker switch

When user starts a new analysis with a different ticker:
- File watcher restarts for new ticker
- Picker shows runs for new ticker (empty if first time)
- Pipeline state is reset via `pipeline.reset()`

## Files Changed

| File | Change |
|------|--------|
| `src/tauri/src/hooks/usePipeline.ts` | Generate `runDate` in `start()` if not provided |
| `src/tauri/src/App.tsx` | Remove auto-restore useEffect; add run picker to header; wire picker selection to restore |
| `src/tauri/src/components/PipelineMonitor.tsx` | Remove internal run selector (responsibility moves to header) |

## Non-Goals

- No sidebar or modal for run history
- No deletion of old runs from the UI
- No cross-ticker comparison view
