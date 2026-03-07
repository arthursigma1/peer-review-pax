import { useEffect, useRef } from "react";
import type { PipelineAgent } from "../types/pipeline";

const STATUS_COLORS: Record<string, string> = {
  idle: "text-zinc-500",
  running: "text-teal-400",
  complete: "text-emerald-400",
  failed: "text-red-400",
};

interface AgentCardProps {
  agent: PipelineAgent;
  isExpanded: boolean;
  onToggle: () => void;
}

export function AgentCard({ agent, isExpanded, onToggle }: AgentCardProps) {
  const logEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isExpanded && logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [isExpanded, agent.logs.length]);

  return (
    <div
      className={`
        rounded-md ring-1 bg-zinc-800/40 overflow-hidden transition-all duration-200
        ${agent.status === "running" ? "ring-teal-500/40" : "ring-zinc-700/80"}
        ${isExpanded ? "ring-2" : ""}
      `}
    >
      {/* Header — always visible, clickable */}
      <button
        onClick={onToggle}
        className="w-full text-left px-3 py-2.5 flex items-center justify-between hover:bg-zinc-700/30 transition-colors cursor-pointer"
      >
        <div className="flex items-center gap-2 min-w-0">
          <div
            className={`w-1.5 h-1.5 rounded-full shrink-0 ${
              agent.status === "running"
                ? "bg-teal-400 animate-pulse"
                : agent.status === "complete"
                ? "bg-emerald-400"
                : agent.status === "failed"
                ? "bg-red-400"
                : "bg-zinc-600"
            }`}
          />
          <span className="text-sm font-medium text-zinc-200 truncate">
            {agent.friendlyName}
          </span>
          {agent.outputFile && (
            <span className="text-[10px] text-zinc-600 font-mono truncate hidden sm:inline">
              {agent.outputFile}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2 shrink-0 ml-2">
          <span className={`text-[10px] uppercase tracking-wider ${STATUS_COLORS[agent.status]}`}>
            {agent.status}
          </span>
          <span className="text-zinc-600 text-xs">
            {isExpanded ? "▾" : "▸"}
          </span>
        </div>
      </button>

      {/* Collapsed preview — last log line */}
      {!isExpanded && agent.logs.length > 0 && (
        <div className="px-3 pb-2 -mt-1">
          <div className="text-[11px] text-zinc-500 font-mono truncate">
            {agent.logs[agent.logs.length - 1]}
          </div>
        </div>
      )}

      {/* Expanded terminal view */}
      {isExpanded && (
        <div className="border-t border-zinc-700/60">
          <div className="flex items-center justify-between px-3 py-1.5 bg-zinc-900/60">
            <span className="text-[10px] text-zinc-500 font-mono">
              {agent.friendlyName} — {agent.logs.length} lines
            </span>
            {agent.status === "running" && (
              <span className="text-[10px] text-teal-500 animate-pulse">
                live
              </span>
            )}
          </div>
          <div className="max-h-80 overflow-y-auto bg-zinc-950/80 px-3 py-2 font-mono text-[11px] leading-relaxed scroll-smooth">
            {agent.logs.length === 0 ? (
              <div className="text-zinc-600 italic">No output yet...</div>
            ) : (
              agent.logs.map((line, i) => (
                <div
                  key={i}
                  className={`whitespace-pre-wrap break-all ${
                    line.includes("[ERROR]") || line.toLowerCase().includes("error")
                      ? "text-red-400"
                      : line.includes("[stderr]")
                      ? "text-amber-500/70"
                      : line.includes("complete") || line.includes("finished")
                      ? "text-emerald-400/80"
                      : "text-zinc-400"
                  }`}
                >
                  {line}
                </div>
              ))
            )}
            <div ref={logEndRef} />
          </div>
        </div>
      )}
    </div>
  );
}
