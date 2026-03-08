import { useState, useEffect, useCallback, useRef } from "react";
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import type { OutputFile } from "../types/pipeline";

export function useFileWatcher(ticker: string | null) {
  const [files, setFiles] = useState<OutputFile[]>([]);
  const [watching, setWatching] = useState(false);
  const [runs, setRuns] = useState<string[]>([]);
  const [selectedRun, setSelectedRun] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Track the set of known run IDs so we can detect newly appearing runs.
  const prevRunsRef = useRef<Set<string>>(new Set());

  const refresh = useCallback(async () => {
    if (!ticker) return;
    try {
      const availableRuns = await invoke<string[]>("list_analysis_runs", { ticker });
      setRuns(availableRuns);

      // Detect newly appeared runs by comparing against the previous snapshot.
      const prevRuns = prevRunsRef.current;
      const newRuns = availableRuns.filter((r) => !prevRuns.has(r));

      // Update the ref with the current full set before any state changes.
      prevRunsRef.current = new Set(availableRuns);

      // If any new run appeared, auto-select the newest one regardless of
      // whether selectedRun was already set (covers the "same ticker, new run"
      // scenario that caused the Results tab to stay on the old run).
      let runDate: string | null;
      if (newRuns.length > 0) {
        // availableRuns is expected to be sorted newest-first by the Rust backend;
        // use the first element as the canonical "newest" run.
        runDate = availableRuns[0] ?? null;
        if (runDate) setSelectedRun(runDate);
      } else {
        // No new runs — keep the current selection or default to the first one.
        runDate = selectedRun || availableRuns[0] || null;
        if (runDate && !selectedRun) setSelectedRun(runDate);
      }

      const result = await invoke<OutputFile[]>("list_outputs", { ticker, runDate });
      setFiles(result);
      setError(null);
    } catch (err) {
      console.error("Failed to list outputs:", err);
      setError(`Failed to list outputs: ${err}`);
    }
  }, [ticker, selectedRun]);

  useEffect(() => {
    if (!ticker) return;

    refresh();

    let unlisten: (() => void) | undefined;

    const setup = async () => {
      try {
        await invoke("start_file_watcher", { ticker });
        setWatching(true);
        setError(null);
        unlisten = await listen<OutputFile[]>("output-files-changed", () => {
          void refresh();
        });
      } catch (err) {
        console.error("Failed to start watcher:", err);
        setError(`File watcher failed: ${err}`);
      }
    };

    setup();

    return () => {
      unlisten?.();
      setWatching(false);
    };
  }, [ticker, refresh]);

  // Reset all file watcher state to a clean slate. Call this when the user
  // starts a new analysis run so the Results tab does not display stale data.
  const resetForNewRun = useCallback(() => {
    setFiles([]);
    setSelectedRun(null);
    setRuns([]);
    // Also reset the previous-runs tracking ref so the next refresh correctly
    // treats all returned runs as "new" and auto-selects the newest one.
    prevRunsRef.current = new Set();
  }, []);

  return { files, watching, refresh, runs, selectedRun, setSelectedRun, error, resetForNewRun };
}
