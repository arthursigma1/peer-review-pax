import { useState, useEffect, useCallback } from "react";
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import type { OutputFile } from "../types/pipeline";

export function useFileWatcher(ticker: string | null) {
  const [files, setFiles] = useState<OutputFile[]>([]);
  const [watching, setWatching] = useState(false);

  const refresh = useCallback(async () => {
    if (!ticker) return;
    try {
      const result = await invoke<OutputFile[]>("list_outputs", { ticker });
      setFiles(result);
    } catch (err) {
      console.error("Failed to list outputs:", err);
    }
  }, [ticker]);

  useEffect(() => {
    if (!ticker) return;

    refresh();

    let unlisten: (() => void) | undefined;

    const setup = async () => {
      try {
        await invoke("start_file_watcher", { ticker });
        setWatching(true);
        unlisten = await listen<OutputFile[]>("output-files-changed", (event) => {
          setFiles(event.payload);
        });
      } catch (err) {
        console.error("Failed to start watcher:", err);
      }
    };

    setup();

    return () => {
      unlisten?.();
      setWatching(false);
    };
  }, [ticker, refresh]);

  return { files, watching, refresh };
}
