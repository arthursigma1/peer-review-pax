import { useEffect, useRef } from "react";
import { Terminal as XTerm } from "@xterm/xterm";
import { FitAddon } from "@xterm/addon-fit";
import { WebLinksAddon } from "@xterm/addon-web-links";
import "@xterm/xterm/css/xterm.css";
import { usePty } from "../hooks/usePty";
import { terminalTheme } from "../lib/theme";

interface TerminalProps {
  command: string;
  args: string[];
  autoStart?: boolean;
  onExit?: () => void;
  onData?: (text: string) => void;
}

export function Terminal({ command, args, autoStart = false, onExit, onData }: TerminalProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const xtermRef = useRef<XTerm | null>(null);
  const fitAddonRef = useRef<FitAddon | null>(null);
  const startedRef = useRef(false);
  const { termRef, isRunning, spawn, write, kill } = usePty(onData);

  // Initialize xterm.js
  useEffect(() => {
    if (!containerRef.current) return;

    const term = new XTerm({
      cursorBlink: true,
      fontFamily: "'SF Mono', 'Cascadia Code', 'Fira Code', Menlo, monospace",
      fontSize: 12,
      lineHeight: 1.3,
      theme: terminalTheme,
      scrollback: 10000,
      convertEol: true,
    });

    const fitAddon = new FitAddon();
    term.loadAddon(fitAddon);
    term.loadAddon(new WebLinksAddon());
    term.open(containerRef.current);
    fitAddon.fit();

    // Forward user input to PTY
    term.onData((data) => {
      write(data);
    });

    xtermRef.current = term;
    fitAddonRef.current = fitAddon;
    termRef.current = term;

    // Handle resize
    const observer = new ResizeObserver(() => {
      fitAddon.fit();
    });
    observer.observe(containerRef.current);

    return () => {
      observer.disconnect();
      term.dispose();
      xtermRef.current = null;
      fitAddonRef.current = null;
    };
  }, []);

  // Auto-start: wait a tick for xterm to initialize, then spawn
  useEffect(() => {
    if (!autoStart || startedRef.current) return;
    // Small delay to ensure xterm is fully initialized
    const timer = setTimeout(() => {
      const term = xtermRef.current;
      if (!term) {
        console.error("[Terminal] xterm not ready for auto-start");
        return;
      }
      startedRef.current = true;
      const cols = term.cols;
      const rows = term.rows;
      term.writeln(`\x1b[90mSpawning: ${command} ${args.join(" ")} (${cols}x${rows})\x1b[0m`);
      spawn(command, args, cols, rows).then(() => {
        term.writeln("\x1b[90mPTY spawn returned OK\x1b[0m");
      }).catch((err) => {
        term.writeln(`\x1b[31mPTY spawn failed: ${err}\x1b[0m`);
      });
    }, 100);
    return () => clearTimeout(timer);
  }, [autoStart, command, args, spawn]);

  // Notify parent on exit
  useEffect(() => {
    if (!isRunning && startedRef.current && onExit) {
      onExit();
    }
  }, [isRunning, onExit]);

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-3 py-1.5 bg-zinc-900/80 border-b border-zinc-800/60">
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${isRunning ? "bg-teal-400 animate-pulse" : "bg-zinc-600"}`} />
          <span className="text-[11px] font-mono text-zinc-500">
            {isRunning ? `${command} ${args.join(" ")}` : startedRef.current ? "Session ended" : "Ready"}
          </span>
        </div>
        {isRunning && (
          <button
            onClick={kill}
            className="text-[10px] px-3 py-2 rounded bg-red-500/10 text-red-400 hover:bg-red-500/20 transition-colors"
          >
            Kill
          </button>
        )}
      </div>
      <div ref={containerRef} className="flex-1 min-h-0" />
    </div>
  );
}
