import { useRef, useCallback, useState, useEffect } from "react";
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import type { Terminal } from "@xterm/xterm";

export function usePty() {
  const termRef = useRef<Terminal | null>(null);
  const [isRunning, setIsRunning] = useState(false);

  // Listen for PTY output and exit events
  useEffect(() => {
    const unlisten1 = listen<string>("pty-output", (event) => {
      if (!termRef.current) {
        console.warn("[usePty] pty-output received but termRef is null");
        return;
      }
      // Decode base64 back to raw bytes
      const binary = atob(event.payload);
      const bytes = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i);
      }
      const text = new TextDecoder().decode(bytes);
      termRef.current.write(text);
    });

    const unlisten2 = listen("pty-exit", () => {
      setIsRunning(false);
      termRef.current?.writeln("\r\n\x1b[90m--- Session ended ---\x1b[0m");
    });

    return () => {
      unlisten1.then((fn) => fn());
      unlisten2.then((fn) => fn());
    };
  }, []);

  const spawn = useCallback(async (command: string, args: string[], cols: number, rows: number) => {
    try {
      await invoke("pty_spawn", { command, args, cols, rows });
      setIsRunning(true);
    } catch (err) {
      console.error("Failed to spawn PTY:", err);
      termRef.current?.writeln(`\r\n\x1b[31mFailed to spawn: ${err}\x1b[0m`);
    }
  }, []);

  const write = useCallback(async (data: string) => {
    try {
      await invoke("pty_write", { data });
    } catch { /* session may have ended */ }
  }, []);

  const kill = useCallback(async () => {
    try {
      await invoke("pty_kill");
    } catch { /* already dead */ }
    setIsRunning(false);
  }, []);

  const resize = useCallback(async (cols: number, rows: number) => {
    try {
      await invoke("pty_resize", { cols, rows });
    } catch { /* ignore */ }
  }, []);

  return { termRef, isRunning, spawn, write, kill, resize };
}
