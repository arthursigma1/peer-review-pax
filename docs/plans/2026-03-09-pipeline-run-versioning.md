# Pipeline Run Versioning Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix pipeline state being stuck on old run, and add a run picker to the header so users can switch between historical analysis runs.

**Architecture:** Three focused changes: (1) always assign `runDate` when a pipeline starts so state is always saved per-run; (2) remove the auto-restore on boot that loads stale state; (3) move the existing run selector from `PipelineMonitor` into the app header so it's visible on all tabs and shows a live indicator.

**Tech Stack:** React + TypeScript, Tauri IPC (`invoke`), existing `useFileWatcher` / `usePipeline` hooks.

---

### Task 1: Fix runDate always being assigned on pipeline start

**Files:**
- Modify: `src/tauri/src/hooks/usePipeline.ts:154-185`

**Context:** The `start()` function accepts `nextRunDate` but it can be `null`. When null, `saveState()` saves to the ticker root dir, overwriting all previous runs. Fix: generate today's date string if no runDate is passed.

**Step 1: Open the file and locate the `start` callback**

Read `src/tauri/src/hooks/usePipeline.ts`, find lines 154–185.

**Step 2: Change the runDate assignment inside `start()`**

Find this line inside `start()`:
```ts
setRunDate(nextRunDate ?? null);
```

Replace with:
```ts
const today = new Date().toISOString().split("T")[0];
setRunDate(nextRunDate ?? today);
```

**Step 3: Verify no TypeScript errors**

```bash
cd src/tauri && npm run build 2>&1 | head -30
```
Expected: no errors related to `usePipeline.ts`.

**Step 4: Commit**

```bash
git add src/tauri/src/hooks/usePipeline.ts
git commit -m "fix: always assign runDate on pipeline start to prevent root-level state overwrite"
```

---

### Task 2: Remove auto-restore on boot

**Files:**
- Modify: `src/tauri/src/App.tsx:263-274`

**Context:** There's a `useEffect` that on mount calls `pipeline.restore(lastTicker)` and navigates to the monitor screen. This loads a potentially stale `pipeline_state.json` (saved at ticker root, with `isRunning: true`) unconditionally. The run picker (Task 3) will handle loading — this auto-restore should be removed entirely.

**Step 1: Locate the useEffect**

In `App.tsx`, find this block (around lines 263–274):
```ts
useEffect(() => {
  const lastTicker = localStorage.getItem("vda-last-ticker");
  if (lastTicker && !restored) {
    pipeline.restore(lastTicker).then((didRestore) => {
      if (didRestore) {
        setTicker(lastTicker);
        setScreen("monitor");
        setRestored(true);
      }
    });
  }
}, []);
```

**Step 2: Delete that entire useEffect block**

Remove the 11 lines above completely. Also remove the `restored` state variable (line ~83: `const [restored, setRestored] = useState(false);`) since it's no longer needed.

**Step 3: Verify TypeScript**

```bash
cd src/tauri && npm run build 2>&1 | head -30
```
Expected: no errors. If `restored` is referenced elsewhere, remove those references too.

**Step 4: Commit**

```bash
git add src/tauri/src/App.tsx
git commit -m "fix: remove auto-restore on boot — run picker will handle loading"
```

---

### Task 3: Move run picker to header

**Files:**
- Modify: `src/tauri/src/App.tsx:370-410` (header section)
- Modify: `src/tauri/src/components/PipelineMonitor.tsx:10-26, 77-89` (remove internal picker)

**Context:** The run selector currently lives inside `PipelineMonitor` (lines 79–89) and is hidden when `isRunning` or `runs.length <= 1`. It needs to move to the app header so it's visible on all tabs (Pipeline, Results, Agents). The `runs` and `selectedRun` state already exist in `App.tsx` via `useFileWatcher`.

**Step 1: Add run picker to the app header in `App.tsx`**

In `App.tsx`, find the header section. The left side currently looks like:
```tsx
<div className="flex items-center gap-4">
  <h1 className="text-sm font-semibold tracking-tight">
    <span className="text-[#0068ff] font-semibold text-base">VDA</span>{" "}
    <span className="text-gray-500 font-normal">Pipeline Dashboard</span>
  </h1>
  {pipeline.config && (
    <span className="text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-500 font-mono">
      {pipeline.config.ticker}
    </span>
  )}
</div>
```

Replace with:
```tsx
<div className="flex items-center gap-3">
  <h1 className="text-sm font-semibold tracking-tight">
    <span className="text-[#0068ff] font-semibold text-base">VDA</span>{" "}
    <span className="text-gray-500 font-normal">Pipeline Dashboard</span>
  </h1>
  {pipeline.config && (
    <span className="text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-500 font-mono">
      {pipeline.config.ticker}
    </span>
  )}
  {pipeline.config && runs.length > 0 && (
    <div className="flex items-center gap-1.5">
      <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
        pipeline.isRunning
          ? "bg-emerald-500 animate-pulse"
          : "bg-[#0068ff]"
      }`} />
      <select
        value={selectedRun || ""}
        onChange={(e) => setSelectedRun(e.target.value)}
        className="px-2 py-0.5 rounded bg-gray-50 border border-gray-200 text-xs text-gray-600 font-mono focus:ring-2 focus:ring-[#0068ff]/40 focus:border-[#0068ff] focus:outline-none appearance-none"
      >
        {runs.map((r) => (
          <option key={r} value={r}>{r}</option>
        ))}
      </select>
    </div>
  )}
</div>
```

**Step 2: Remove internal run picker from `PipelineMonitor`**

In `PipelineMonitor.tsx`, remove the `runs`, `selectedRun`, `onSelectRun` props from the interface and destructuring, and delete the select block (lines 79–89):
```tsx
{runs && runs.length > 1 && !isRunning && onSelectRun && (
  <select
    value={selectedRun || ""}
    onChange={(e) => onSelectRun(e.target.value)}
    ...
  >
    {runs.map((r) => (
      <option key={r} value={r}>{r}</option>
    ))}
  </select>
)}
```

Also remove the corresponding props from where `PipelineMonitor` is called in `App.tsx` (the `runs`, `selectedRun`, `onSelectRun` props passed to `<PipelineMonitor>`).

**Step 3: Verify TypeScript**

```bash
cd src/tauri && npm run build 2>&1 | head -30
```
Expected: no errors. Fix any leftover prop references.

**Step 4: Commit**

```bash
git add src/tauri/src/App.tsx src/tauri/src/components/PipelineMonitor.tsx
git commit -m "feat: move run picker to app header, visible on all tabs"
```

---

### Task 4: Wire run picker selection to pipeline state reload

**Files:**
- Modify: `src/tauri/src/App.tsx:86-99`

**Context:** There's already a `useEffect` that watches `selectedRun` and calls `pipeline.restore()` / `pipeline.loadExistingSession()` (lines 87–99). That logic is correct and should still work — but verify it handles the case where `pipeline.config` is null (ticker not yet set) gracefully.

**Step 1: Read the existing effect**

In `App.tsx` lines 87–99:
```ts
useEffect(() => {
  if (!selectedRun || pipeline.isRunning) return;
  const t = pipeline.config?.ticker || ticker;
  if (!t) return;
  if (selectedRun === pipeline.runDate) return;
  pipeline.restore(t, selectedRun).then((loaded) => {
    if (!loaded) {
      pipeline.loadExistingSession(t, selectedRun);
    }
  });
}, [selectedRun]);
```

This is already correct. Confirm it handles `ticker` fallback (it does via `pipeline.config?.ticker || ticker`).

**Step 2: Ensure `pipeline.config` is set when loading an existing session without running**

In `loadExistingSession()` in `usePipeline.ts` (lines 291–295), the config is set with empty `sector`. This means the header ticker badge will appear after `loadExistingSession` even if no run was manually started. That's the desired behavior — no change needed.

**Step 3: Smoke test**

Run the dev app:
```bash
cd src/tauri && npm run tauri dev
```

1. Verify the header shows the run picker for PAX with all existing runs
2. Select an older run — pipeline tab should show that run's step states
3. Select the newest run — should switch back
4. Start a new run — picker should auto-select the new run date

**Step 4: Commit if any small fixes were needed**

```bash
git add src/tauri/src/App.tsx src/tauri/src/hooks/usePipeline.ts
git commit -m "fix: verify run picker wiring and session restore on run switch"
```

---

### Task 5: Clean up stale root-level pipeline_state.json

**Files:**
- `data/processed/pax/pipeline_state.json` — delete

**Context:** The existing `pipeline_state.json` at the ticker root is stale (runDate: null, isRunning: true). Now that state is always saved per-run, this file serves no purpose and will confuse the fallback logic in `lib.rs:279-290`.

**Step 1: Delete the stale file**

```bash
rm data/processed/pax/pipeline_state.json
```

**Step 2: Commit**

```bash
git add -u data/processed/pax/pipeline_state.json
git commit -m "chore: remove stale root-level pipeline_state.json"
```
