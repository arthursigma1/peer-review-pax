import { memo } from "react";
import type { PipelineStep } from "../types/pipeline";

const STATUS_STYLES: Record<string, { bg: string; border: string; icon: string }> = {
  pending: { bg: "bg-gray-50", border: "border-gray-200", icon: "○" },
  running: { bg: "bg-blue-50", border: "border-blue-200", icon: "◉" },
  complete: { bg: "bg-emerald-50", border: "border-emerald-200", icon: "●" },
  failed: { bg: "bg-red-50", border: "border-red-200", icon: "✕" },
};

interface StepCardProps {
  step: PipelineStep;
  isActive: boolean;
  onClick: () => void;
  subtitle?: string | null;
}

export const StepCard = memo(function StepCard({ step, isActive, onClick, subtitle }: StepCardProps) {
  const style = STATUS_STYLES[step.status];
  const activeAgents = step.agents.filter((a) => a.status === "running").length;
  const doneAgents = step.agents.filter((a) => a.status === "complete").length;

  return (
    <button
      onClick={onClick}
      className={`
        w-full text-left px-4 py-3 rounded-lg border transition-all duration-200
        ${style.bg} ${style.border}
        ${isActive ? "border-2 border-[#0068ff] shadow-sm" : ""}
        hover:bg-gray-100/50 cursor-pointer
      `}
    >
      <div className="flex items-center gap-3">
        <span
          className={`text-lg ${
            step.status === "running" ? "text-blue-600" :
            step.status === "complete" ? "text-emerald-600" :
            step.status === "failed" ? "text-red-600" : "text-gray-400"
          }`}
        >
          {style.icon}
        </span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold text-gray-900 truncate">
              {step.name}
            </span>
            <span className="text-[10px] text-gray-500 ml-2 shrink-0">
              {step.status}
            </span>
          </div>
          <p className="text-xs text-gray-500 mt-0.5 truncate">
            {step.description}
          </p>
          {subtitle && step.status === "complete" && (
            <p className="text-[10px] text-emerald-700 font-mono mt-1 truncate">{subtitle}</p>
          )}
          {step.agents.length > 0 && (
            <div className="flex items-center gap-2 mt-1.5">
              {activeAgents > 0 && (
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-100 text-blue-700">
                  {activeAgents} active
                </span>
              )}
              {doneAgents > 0 && (
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-700">
                  {doneAgents} done
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    </button>
  );
});
