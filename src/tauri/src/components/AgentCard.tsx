import { memo, useEffect, useRef } from "react";
import type { PipelineAgent } from "../types/pipeline";
import { STATUS_TEXT, STATUS_DOT } from "../lib/theme";

interface AgentCardProps {
  agent: PipelineAgent;
  isExpanded: boolean;
  onToggle: () => void;
}

export const AgentCard = memo(function AgentCard({ agent, isExpanded, onToggle }: AgentCardProps) {
  const logEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isExpanded && logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [isExpanded, agent.logs.length]);

  return (
    <div
      className={`
        rounded-md border bg-white border-gray-200 overflow-hidden transition-all duration-200
        ${agent.status === "running" ? "border-blue-300" : "border-gray-200"}
        ${isExpanded ? "border-2" : ""}
      `}
    >
      {/* Header — always visible, clickable */}
      <button
        onClick={onToggle}
        aria-expanded={isExpanded}
        className="w-full text-left px-3 py-2.5 flex items-center justify-between hover:bg-gray-50 transition-colors cursor-pointer"
      >
        <div className="flex items-center gap-2 min-w-0">
          <div
            className={`w-1.5 h-1.5 rounded-full shrink-0 ${STATUS_DOT[agent.status] ?? "bg-gray-300"}`}
          />
          <span className="text-sm font-medium text-gray-800 truncate">
            {agent.friendlyName}
          </span>
          {agent.outputFile && (
            <span className="text-[10px] text-gray-400 font-mono truncate hidden sm:inline">
              {agent.outputFile}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2 shrink-0 ml-2">
          <span className={`text-[10px] ${STATUS_TEXT[agent.status] ?? "text-gray-400"}`}>
            {agent.status}
          </span>
          <span className="text-gray-400 text-xs">
            {isExpanded ? "▾" : "▸"}
          </span>
        </div>
      </button>

      {/* Collapsed preview — last log line */}
      {!isExpanded && agent.logs.length > 0 && (
        <div className="px-3 pb-2 -mt-1">
          <div className="text-[11px] text-gray-500 font-mono truncate">
            {agent.logs[agent.logs.length - 1]}
          </div>
        </div>
      )}

      {/* Expanded terminal view */}
      {isExpanded && (
        <div className="border-t border-gray-200">
          <div className="flex items-center justify-between px-3 py-1.5 bg-gray-50">
            <span className="text-[10px] text-gray-500 font-mono">
              {agent.friendlyName} — {agent.logs.length} lines
            </span>
            {agent.status === "running" && (
              <span className="text-[10px] text-blue-600">
                live
              </span>
            )}
          </div>
          <div className="max-h-80 overflow-y-auto bg-gray-900 px-3 py-2 font-mono text-[11px] leading-relaxed scroll-smooth">
            {agent.logs.length === 0 ? (
              <div className="text-gray-500 italic">No output yet...</div>
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
                      : "text-gray-400"
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
});
