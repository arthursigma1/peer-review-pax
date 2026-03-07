import { useState } from "react";
import type { PipelineStep } from "../types/pipeline";
import { StepCard } from "./StepCard";
import { AgentCard } from "./AgentCard";
import { formatElapsed } from "../lib/cli";

interface PipelineMonitorProps {
  steps: PipelineStep[];
  currentStep: number;
  logs: string[];
  startTime: number | null;
  isRunning: boolean;
  onRerunFromStep?: (stepIndex: number) => void;
}

export function PipelineMonitor({
  steps,
  currentStep,
  logs,
  startTime,
  isRunning,
  onRerunFromStep,
}: PipelineMonitorProps) {
  const [selectedStep, setSelectedStep] = useState<number>(0);
  const [showLogs, setShowLogs] = useState(false);
  const [expandedAgent, setExpandedAgent] = useState<string | null>(null);

  const activeStep = steps[selectedStep] || steps[0];
  const elapsed = startTime ? Date.now() - startTime : 0;
  const completedSteps = steps.filter((s) => s.status === "complete").length;

  return (
    <div className="flex flex-col h-full">
      {/* Progress bar */}
      <div className="px-6 py-4 border-b border-zinc-800/80">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-3">
            {isRunning && (
              <div className="w-2 h-2 rounded-full bg-teal-400 animate-pulse" />
            )}
            <span className="text-sm text-zinc-300">
              {isRunning
                ? `Step ${currentStep + 1} of ${steps.length}`
                : completedSteps >= 5
                ? "Pipeline Complete"
                : completedSteps > 0
                ? `${completedSteps}/${steps.length} Steps Complete`
                : "Pipeline Ready"}
            </span>
          </div>
          {startTime && (
            <span className="text-xs text-zinc-500 font-mono">
              {formatElapsed(elapsed)}
            </span>
          )}
        </div>
        <div className="h-1 rounded-full bg-zinc-800 overflow-hidden">
          <div
            className="h-full rounded-full bg-gradient-to-r from-teal-500 to-emerald-400 transition-all duration-500"
            style={{ width: `${(completedSteps / steps.length) * 100}%` }}
          />
        </div>
      </div>

      <div className="flex flex-1 min-h-0">
        {/* Step sidebar */}
        <div className="w-72 border-r border-zinc-800/80 p-4 space-y-2 overflow-y-auto">
          {steps.map((step) => (
            <StepCard
              key={step.index}
              step={step}
              isActive={selectedStep === step.index}
              onClick={() => setSelectedStep(step.index)}
            />
          ))}
        </div>

        {/* Step detail center */}
        <div className="flex-1 flex flex-col min-w-0">
          <div className="px-6 py-4 border-b border-zinc-800/80">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-zinc-100">
                  {activeStep.name}
                </h2>
                <p className="text-sm text-zinc-500 mt-1">
                  {activeStep.description}
                </p>
              </div>
              {!isRunning && onRerunFromStep && (activeStep.status === "complete" || activeStep.status === "failed") && (
                <button
                  onClick={() => onRerunFromStep(activeStep.index)}
                  className="px-3 py-1.5 rounded-md text-xs font-medium text-amber-400 ring-1 ring-amber-500/30 hover:bg-amber-500/10 transition-colors shrink-0 ml-4"
                >
                  Re-run from here
                </button>
              )}
            </div>
          </div>

          {/* Agents grid */}
          <div className="flex-1 overflow-y-auto px-6 py-4">
            {activeStep.agents.length > 0 ? (
              <div className="space-y-2">
                <h3 className="text-xs uppercase tracking-wider text-zinc-500 mb-3">
                  Agents ({activeStep.agents.length})
                </h3>
                <div className="grid gap-2">
                  {activeStep.agents.map((agent) => (
                    <AgentCard
                      key={agent.id}
                      agent={agent}
                      isExpanded={expandedAgent === agent.id}
                      onToggle={() =>
                        setExpandedAgent(
                          expandedAgent === agent.id ? null : agent.id
                        )
                      }
                    />
                  ))}
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center h-full text-zinc-600 text-sm">
                {activeStep.status === "pending"
                  ? "Waiting to start..."
                  : "No agents dispatched yet"}
              </div>
            )}
          </div>

          {/* Log toggle */}
          <div className="border-t border-zinc-800/80">
            <button
              onClick={() => setShowLogs(!showLogs)}
              className="w-full px-6 py-2 text-left text-xs text-zinc-500 hover:text-zinc-300 transition-colors flex items-center justify-between"
            >
              <span>Pipeline Logs ({logs.length})</span>
              <span>{showLogs ? "Hide" : "Show"}</span>
            </button>
            {showLogs && (
              <div className="max-h-48 overflow-y-auto px-6 pb-3">
                <div className="font-mono text-[11px] text-zinc-600 space-y-0.5">
                  {logs.slice(-100).map((line, i) => (
                    <div
                      key={i}
                      className={
                        line.includes("[ERROR]")
                          ? "text-red-400"
                          : line.includes("[stderr]")
                          ? "text-amber-500/70"
                          : ""
                      }
                    >
                      {line}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
