import { useState, useEffect } from "react";
import type { PipelineStep, Checkpoint } from "../types/pipeline";
import type { RunDigest } from "../hooks/useRunDigest";
import { StepCard } from "./StepCard";
import { AgentCard } from "./AgentCard";
import { CheckpointBar } from "./CheckpointBar";
import { Terminal } from "./Terminal";
import { AgentTimeline } from "./AgentTimeline";
import { RunDigestPanel } from "./RunDigestPanel";
import { formatElapsed } from "../lib/cli";

interface PipelineMonitorProps {
  steps: PipelineStep[];
  currentStep: number;
  logs: string[];
  startTime: number | null;
  isRunning: boolean;
  checkpoints: Checkpoint[];
  digest?: RunDigest | null;
  digestTicker?: string;
  digestRunDate?: string;
  onRerunFromStep?: (stepIndex: number) => void;
  onRunNextStep?: () => void;
  ptyCommand?: string | null;
  ptyArgs?: string[];
  onPtyExit?: () => void;
  onPtyData?: (text: string) => void;
}

function getStepSubtitle(index: number, digest: RunDigest | null | undefined): string | null {
  if (!digest) return null;
  switch (index) {
    case 0:
      if (digest.peers_total != null || digest.metrics_total != null)
        return [
          digest.peers_total != null ? `${digest.peers_total} peers` : null,
          digest.metrics_total != null ? `${digest.metrics_total} metrics` : null,
        ].filter(Boolean).join(" · ");
      return null;
    case 2:
      if (digest.drivers.length > 0) {
        const top = digest.drivers[0];
        return `${top.id} ρ=${top.rho.toFixed(2)}${digest.stable_drivers_count ? ` · ${digest.stable_drivers_count} stable` : ""}`;
      }
      return null;
    case 4:
      if (digest.plays_total > 0)
        return `${digest.plays_total} plays · ${digest.anti_patterns_total} anti-patterns`;
      return null;
    default:
      return null;
  }
}

export function PipelineMonitor({
  steps,
  currentStep,
  logs: _logs,
  startTime,
  isRunning,
  checkpoints,
  digest,
  digestTicker,
  digestRunDate,
  onRerunFromStep,
  onRunNextStep,
  ptyCommand,
  ptyArgs = [],
  onPtyExit,
  onPtyData,
}: PipelineMonitorProps) {
  const [selectedStep, setSelectedStep] = useState<number>(0);
  const [expandedAgent, setExpandedAgent] = useState<string | null>(null);
  const hasDigest = !!(digest && (digest.drivers.length > 0 || digest.plays_total > 0));
  const [bottomTab, setBottomTab] = useState<"agents" | "timeline" | "digest">("agents");

  // Auto-switch to Digest tab when data arrives and no terminal is active
  useEffect(() => {
    if (hasDigest && !ptyCommand && bottomTab === "agents") {
      setBottomTab("digest");
    }
  }, [hasDigest, ptyCommand]);

  const activeStep = steps[selectedStep] || steps[0];
  const elapsed = startTime ? Date.now() - startTime : 0;
  const completedSteps = steps.filter((s) => s.status === "complete").length;

  return (
    <div className="flex flex-col h-full">
      {/* Progress bar */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-3">
            {isRunning ? (
              <div className="w-2 h-2 rounded-full bg-[#0068ff]" />
            ) : completedSteps >= 5 ? (
              <div className="w-2 h-2 rounded-full bg-emerald-500" />
            ) : null}
            <span className={`text-sm ${completedSteps >= 5 && !isRunning ? "text-emerald-600 font-medium" : "text-gray-700"}`}>
              {isRunning
                ? `Step ${currentStep + 1} of ${steps.length}`
                : completedSteps >= 5
                ? "✓ Pipeline Complete"
                : completedSteps > 0
                ? `${completedSteps}/${steps.length} Steps Complete`
                : "Pipeline Ready"}
            </span>
          </div>
          <div className="flex items-center gap-3">
            {!isRunning && onRunNextStep && completedSteps > 0 && completedSteps < steps.length && (
              <button
                onClick={onRunNextStep}
                className="px-3 py-1 rounded text-xs font-medium text-[#0068ff] border border-[#0068ff]/40 hover:bg-[#0068ff]/5 transition-colors"
              >
                Run Next Step →
              </button>
            )}
            {startTime && (
              <span className="text-xs text-gray-400 font-mono">
                {formatElapsed(elapsed)}
              </span>
            )}
          </div>
        </div>
        <div className="h-1 rounded-full bg-gray-200 overflow-hidden">
          <div
            className="h-full rounded-full bg-[#0068ff] transition-all duration-500"
            style={{ width: `${(completedSteps / steps.length) * 100}%` }}
          />
        </div>
      </div>

      <div className="flex flex-1 min-h-0">
        {/* Step sidebar */}
        <div className="w-72 border-r border-gray-200 p-4 space-y-2 overflow-y-auto">
          {steps.map((step) => (
            <div key={step.index}>
              <StepCard
                step={step}
                isActive={selectedStep === step.index}
                onClick={() => setSelectedStep(step.index)}
                subtitle={getStepSubtitle(step.index, digest)}
              />
              {checkpoints
                .filter((cp) => cp.afterStep === step.index)
                .map((cp) => (
                  <CheckpointBar key={cp.id} checkpoint={cp} />
                ))}
            </div>
          ))}
        </div>

        {/* Main content area */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Terminal (primary) */}
          {ptyCommand && (
            <div className="flex-1 min-h-0">
              <Terminal command={ptyCommand} args={ptyArgs} autoStart onExit={onPtyExit} onData={onPtyData} />
            </div>
          )}

          {/* Bottom panel: tabbed between Agents, Timeline, and Digest */}
          <div className={`border-t border-gray-200 flex flex-col ${ptyCommand ? "h-[35%]" : "flex-1"}`}>
            {/* Tab bar */}
            <div className="flex items-center justify-between px-4 py-0 bg-gray-50/50 border-b border-gray-200">
              <div className="flex items-center gap-0">
                <button
                  onClick={() => setBottomTab("agents")}
                  className={`px-3 py-2 text-[11px] font-medium border-b-2 transition-colors ${
                    bottomTab === "agents"
                      ? "border-[#0068ff] text-[#0068ff]"
                      : "border-transparent text-gray-500 hover:text-gray-700"
                  }`}
                >
                  {activeStep.name}
                  {activeStep.agents.length > 0 && (
                    <span className="ml-1.5 text-[9px] text-gray-400">
                      {activeStep.agents.length} agent{activeStep.agents.length !== 1 ? "s" : ""}
                    </span>
                  )}
                </button>
                {completedSteps > 0 && (
                  <button
                    onClick={() => setBottomTab("timeline")}
                    className={`px-3 py-2 text-[11px] font-medium border-b-2 transition-colors ${
                      bottomTab === "timeline"
                        ? "border-[#0068ff] text-[#0068ff]"
                        : "border-transparent text-gray-500 hover:text-gray-700"
                    }`}
                  >
                    Timeline
                  </button>
                )}
                {digest && (digest.drivers.length > 0 || digest.plays_total > 0) && (
                  <button
                    onClick={() => setBottomTab("digest")}
                    className={`px-3 py-2 text-[11px] font-medium border-b-2 transition-colors ${
                      bottomTab === "digest"
                        ? "border-[#0068ff] text-[#0068ff]"
                        : "border-transparent text-gray-500 hover:text-gray-700"
                    }`}
                  >
                    Digest
                  </button>
                )}
              </div>
              {bottomTab === "agents" && !isRunning && onRerunFromStep && (activeStep.status === "complete" || activeStep.status === "failed") && (
                <button
                  onClick={() => onRerunFromStep(activeStep.index)}
                  className="px-2 py-1 rounded text-[10px] font-medium text-amber-600 border border-amber-300 hover:bg-amber-50 transition-colors"
                >
                  Re-run from here
                </button>
              )}
            </div>

            {/* Tab content */}
            <div className="flex-1 overflow-y-auto">
              {bottomTab === "agents" ? (
                <div className="px-4 py-2">
                  {activeStep.agents.length > 0 ? (
                    <div className="grid gap-1.5">
                      {activeStep.agents.map((agent) => (
                        <AgentCard
                          key={agent.id}
                          agent={agent}
                          isExpanded={expandedAgent === agent.id}
                          onToggle={() =>
                            setExpandedAgent(expandedAgent === agent.id ? null : agent.id)
                          }
                        />
                      ))}
                    </div>
                  ) : !ptyCommand ? (
                    <div className="flex items-center justify-center h-full text-gray-400 text-sm">
                      {activeStep.status === "pending"
                        ? "Waiting to start..."
                        : "No agents dispatched yet"}
                    </div>
                  ) : null}
                </div>
              ) : bottomTab === "timeline" ? (
                <div className="px-4 py-3">
                  <AgentTimeline steps={steps} startTime={startTime} />
                </div>
              ) : digest && digestTicker && digestRunDate ? (
                <RunDigestPanel digest={digest} ticker={digestTicker} runDate={digestRunDate} />
              ) : null}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
