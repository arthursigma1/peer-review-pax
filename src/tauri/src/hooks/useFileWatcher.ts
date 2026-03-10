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

  // When true, the user has explicitly picked a run via the UI — suppress
  // auto-selection from filesystem events so we don't yank their view away.
  const userPickedRef = useRef(false);

  // Mirror selectedRun in a ref so refresh() can read it without depending on
  // the state value (which would recreate refresh on every selection change and
  // cause a re-entrancy loop via the useEffect that listens to refresh).
  const selectedRunRef = useRef<string | null>(null);
  useEffect(() => { selectedRunRef.current = selectedRun; }, [selectedRun]);

  const refresh = useCallback(async () => {
    if (!ticker) return;
    try {
      const availableRuns = await invoke<string[]>("list_analysis_runs", { ticker });
      setRuns(availableRuns);

      const prevRuns = prevRunsRef.current;
      const newRuns = availableRuns.filter((r) => !prevRuns.has(r));
      prevRunsRef.current = new Set(availableRuns);

      let runDate: string | null;
      if (newRuns.length > 0 && !userPickedRef.current) {
        // New run appeared and user hasn't explicitly picked one — auto-select newest.
        runDate = availableRuns[0] ?? null;
        if (runDate) setSelectedRun(runDate);
      } else if (!selectedRunRef.current) {
        // No selection yet — prefer the newest run with a complete report.
        const bestRun = await invoke<string | null>("find_latest_complete_run", { ticker });
        runDate = bestRun || availableRuns[0] || null;
        if (runDate) setSelectedRun(runDate);
      } else {
        runDate = selectedRunRef.current;
      }

      const result = await invoke<OutputFile[]>("list_outputs", { ticker, runDate });
      setFiles(result);
      setError(null);
    } catch (err) {
      console.error("Failed to list outputs:", err);
      setError(`Failed to list outputs: ${err}`);
    }
  }, [ticker]); // no selectedRun dependency — uses ref instead

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

  // Re-fetch files when the selected run changes (user pick or auto-selection).
  // This is separate from refresh() to avoid the re-entrancy loop — we only
  // need to list files, not re-run the run-detection logic.
  useEffect(() => {
    if (!selectedRun || !ticker) return;
    invoke<OutputFile[]>("list_outputs", { ticker, runDate: selectedRun })
      .then((result) => { setFiles(result); setError(null); })
      .catch((err) => setError(`Failed to list outputs: ${err}`));
  }, [selectedRun, ticker]);

  // User-facing selection — marks that the user explicitly chose a run.
  // Once set, filesystem events will NOT override the selection.
  const selectRun = useCallback((run: string | null) => {
    userPickedRef.current = true;
    setSelectedRun(run);
  }, []);

  // Reset all file watcher state to a clean slate. Call this when the user
  // starts a new analysis run so the Results tab does not display stale data.
  const resetForNewRun = useCallback(() => {
    setFiles([]);
    setSelectedRun(null);
    setRuns([]);
    prevRunsRef.current = new Set();
    userPickedRef.current = false; // allow auto-selection for the new run
  }, []);

  return { files, watching, refresh, runs, selectedRun, setSelectedRun: selectRun, error, resetForNewRun };
}
