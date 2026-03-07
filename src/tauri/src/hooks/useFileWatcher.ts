import { useState, useEffect, useCallback } from "react";
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import type { OutputFile } from "../types/pipeline";

export function useFileWatcher(ticker: string | null) {
  const [files, setFiles] = useState<OutputFile[]>([]);
  const [watching, setWatching] = useState(false);
  const [runs, setRuns] = useState<string[]>([]);
  const [selectedRun, setSelectedRun] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!ticker) return;
    try {
      const availableRuns = await invoke<string[]>("list_analysis_runs", { ticker });
      setRuns(availableRuns);
      const runDate = selectedRun || availableRuns[0] || null;
      if (runDate && !selectedRun) setSelectedRun(runDate);
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
        unlisten = await listen<OutputFile[]>("output-files-changed", (event) => {
          setFiles(event.payload);
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

  return { files, watching, refresh, runs, selectedRun, setSelectedRun, error };
}
