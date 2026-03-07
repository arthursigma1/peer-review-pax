import type { PipelineStep } from "../types/pipeline";

const STATUS_STYLES: Record<string, { bg: string; ring: string; icon: string }> = {
  pending: { bg: "bg-zinc-800/50", ring: "ring-zinc-700", icon: "○" },
  running: { bg: "bg-teal-900/30", ring: "ring-teal-500/60", icon: "◉" },
  complete: { bg: "bg-emerald-900/20", ring: "ring-emerald-500/50", icon: "●" },
  failed: { bg: "bg-red-900/20", ring: "ring-red-500/50", icon: "✕" },
};

interface StepCardProps {
  step: PipelineStep;
  isActive: boolean;
  onClick: () => void;
}

export function StepCard({ step, isActive, onClick }: StepCardProps) {
  const style = STATUS_STYLES[step.status];
  const activeAgents = step.agents.filter((a) => a.status === "running").length;
  const doneAgents = step.agents.filter((a) => a.status === "complete").length;

  return (
    <button
      onClick={onClick}
      className={`
        w-full text-left px-4 py-3 rounded-lg ring-1 transition-all duration-200
        ${style.bg} ${style.ring}
        ${isActive ? "ring-2 ring-teal-400 shadow-lg shadow-teal-500/10" : ""}
        hover:brightness-110 cursor-pointer
      `}
    >
      <div className="flex items-center gap-3">
        <span
          className={`text-lg ${
            step.status === "running" ? "text-teal-400 animate-pulse" :
            step.status === "complete" ? "text-emerald-400" :
            step.status === "failed" ? "text-red-400" : "text-zinc-500"
          }`}
        >
          {style.icon}
        </span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold text-zinc-100 truncate">
              {step.name}
            </span>
            <span className="text-[10px] uppercase tracking-wider text-zinc-500 ml-2 shrink-0">
              {step.status}
            </span>
          </div>
          <p className="text-xs text-zinc-500 mt-0.5 truncate">
            {step.description}
          </p>
          {step.agents.length > 0 && (
            <div className="flex items-center gap-2 mt-1.5">
              {activeAgents > 0 && (
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-teal-500/20 text-teal-300">
                  {activeAgents} active
                </span>
              )}
              {doneAgents > 0 && (
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300">
                  {doneAgents} done
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    </button>
  );
}
