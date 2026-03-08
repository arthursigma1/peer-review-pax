import type { PipelineStep, PipelineAgent } from "../types/pipeline";

interface AgentTimelineProps {
  steps: PipelineStep[];
  startTime: number | null;
}

// Step color palette — light theme, Bloomberg aesthetic
const STEP_COLORS: Record<number, { bar: string; label: string; text: string }> = {
  0: { bar: "#06b6d4", label: "bg-cyan-100", text: "text-cyan-700" },      // cyan-500
  1: { bar: "#3b82f6", label: "bg-blue-100", text: "text-blue-700" },      // blue-500
  2: { bar: "#8b5cf6", label: "bg-violet-100", text: "text-violet-700" },  // violet-500
  3: { bar: "#f59e0b", label: "bg-amber-100", text: "text-amber-700" },    // amber-500
  4: { bar: "#10b981", label: "bg-emerald-100", text: "text-emerald-700" }, // emerald-500
  5: { bar: "#f43f5e", label: "bg-rose-100", text: "text-rose-700" },      // rose-500
};

function formatDuration(ms: number): string {
  if (!Number.isFinite(ms) || ms < 0) return "—";
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60_000) return `${(ms / 1000).toFixed(1)}s`;
  const minutes = Math.floor(ms / 60_000);
  const seconds = Math.round((ms % 60_000) / 1000);
  return seconds > 0 ? `${minutes}m ${seconds}s` : `${minutes}m`;
}

function formatAxisLabel(ms: number): string {
  if (ms === 0) return "0s";
  if (ms < 60_000) return `${Math.round(ms / 1000)}s`;
  const minutes = Math.floor(ms / 60_000);
  const seconds = Math.round((ms % 60_000) / 1000);
  return seconds === 0 ? `${minutes}m` : `${minutes}m${seconds}s`;
}

function buildTicks(totalMs: number): number[] {
  const magnitudes = [1000, 5000, 10000, 15000, 30000, 60000, 120000, 300000, 600000];
  const interval = totalMs / 5;
  const bestInterval = magnitudes.reduce((prev, curr) =>
    Math.abs(curr - interval) < Math.abs(prev - interval) ? curr : prev
  );
  const ticks: number[] = [];
  let t = 0;
  while (t <= totalMs) {
    ticks.push(t);
    t += bestInterval;
  }
  return ticks;
}

interface AgentRow {
  agent: PipelineAgent;
  stepIndex: number;
  stepName: string;
}

export function AgentTimeline({ steps, startTime }: AgentTimelineProps) {
  // Collect all agents with timing data
  const allAgentRows: AgentRow[] = [];
  for (const step of steps) {
    for (const agent of step.agents) {
      allAgentRows.push({
        agent,
        stepIndex: step.index,
        stepName: step.name,
      });
    }
  }

  // Check if any agent has timing data
  const hasAnyTiming = allAgentRows.some(
    (r) => r.agent.startedAt != null
  );

  if (!hasAnyTiming || startTime === null) {
    return (
      <div className="flex items-center justify-center h-20 text-xs text-gray-400 font-mono">
        No timing data yet — timeline appears once agents start
      </div>
    );
  }

  // Compute the global time window
  const pipelineStart = startTime;

  const allEndTimes: number[] = [];
  for (const { agent } of allAgentRows) {
    if (agent.completedAt != null) allEndTimes.push(agent.completedAt);
    if (agent.startedAt != null) allEndTimes.push(agent.startedAt);
  }
  // Add a small buffer to end of timeline (10% or at least 5s)
  const rawEndMs = Math.max(...allEndTimes) - pipelineStart;
  const totalMs = Math.max(rawEndMs * 1.08, rawEndMs + 5_000);

  const ticks = buildTicks(totalMs);

  // Group rows by step for display
  const stepGroups: { step: PipelineStep; rows: AgentRow[] }[] = [];
  for (const step of steps) {
    const rows = allAgentRows.filter(
      (r) => r.stepIndex === step.index && r.agent.startedAt != null
    );
    if (rows.length > 0) {
      stepGroups.push({ step, rows });
    }
  }

  if (stepGroups.length === 0) return null;

  // Row height in px (used for consistent sizing)
  const ROW_H = 22;
  const LABEL_W = 156; // px — left label column (fixed)

  return (
    <div className="w-full overflow-x-auto">
      {/* Time axis header */}
      <div className="flex" style={{ paddingLeft: LABEL_W }}>
        <div className="relative flex-1 h-6">
          {ticks.map((tick) => {
            const pct = (tick / totalMs) * 100;
            return (
              <div
                key={tick}
                className="absolute top-0 flex flex-col items-center"
                style={{ left: `${pct}%`, transform: "translateX(-50%)" }}
              >
                <span className="text-[9px] text-gray-400 font-mono leading-none whitespace-nowrap">
                  {formatAxisLabel(tick)}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Tick grid lines + bars */}
      {stepGroups.map(({ step, rows }) => {
        const color = STEP_COLORS[step.index] ?? STEP_COLORS[0];
        return (
          <div key={step.id} className="mb-3">
            {/* Step group header */}
            <div
              className={`flex items-center gap-1.5 mb-1 rounded-sm px-1.5 py-0.5 ${color.label}`}
              style={{ marginLeft: LABEL_W }}
            >
              <span className={`text-[9px] font-semibold uppercase tracking-wider ${color.text}`}>
                Step {step.index} — {step.name}
              </span>
            </div>

            {/* Agent rows */}
            {rows.map(({ agent }) => {
              const agentStart = agent.startedAt! - pipelineStart;
              const agentEnd =
                agent.completedAt !== null
                  ? agent.completedAt - pipelineStart
                  : Date.now() - pipelineStart;
              const duration =
                agent.completedAt !== null
                  ? agent.completedAt - agent.startedAt!
                  : null;

              const leftPct = (agentStart / totalMs) * 100;
              const widthPct = Math.max(
                ((agentEnd - agentStart) / totalMs) * 100,
                0.4 // min visible width
              );

              const isRunning = agent.status === "running";
              const isFailed = agent.status === "failed";
              const barColor = isFailed
                ? "#ef4444"
                : color.bar;

              return (
                <div
                  key={agent.id}
                  className="flex items-center mb-px group"
                  style={{ height: ROW_H }}
                >
                  {/* Agent label */}
                  <div
                    className="shrink-0 flex items-center"
                    style={{ width: LABEL_W, paddingRight: 8 }}
                  >
                    <span
                      className="text-[10px] text-gray-600 font-sans truncate leading-none"
                      title={agent.friendlyName || agent.name}
                    >
                      {agent.friendlyName || agent.name}
                    </span>
                  </div>

                  {/* Bar track */}
                  <div className="relative flex-1 h-full flex items-center">
                    {/* Grid lines */}
                    {ticks.slice(1).map((tick) => (
                      <div
                        key={tick}
                        className="absolute top-0 bottom-0 border-l border-gray-100"
                        style={{ left: `${(tick / totalMs) * 100}%` }}
                      />
                    ))}

                    {/* Bar */}
                    <div
                      className="absolute rounded-sm flex items-center overflow-hidden"
                      style={{
                        left: `${leftPct}%`,
                        width: `${widthPct}%`,
                        height: ROW_H - 6,
                        backgroundColor: barColor,
                        opacity: isRunning ? 0.85 : 1,
                      }}
                    >
                      {/* Animated shimmer for running agents */}
                      {isRunning && (
                        <div
                          className="absolute inset-0 animate-pulse"
                          style={{ backgroundColor: "rgba(255,255,255,0.25)" }}
                        />
                      )}
                      {/* Duration label inside bar if bar is wide enough */}
                      {widthPct > 8 && duration !== null && (
                        <span
                          className="relative z-10 px-1.5 text-[9px] font-mono text-white/90 truncate leading-none whitespace-nowrap"
                        >
                          {formatDuration(duration)}
                        </span>
                      )}
                    </div>

                    {/* Duration label outside bar (tooltip-style, shown on hover) */}
                    {(widthPct <= 8 || duration === null) && (
                      <div
                        className="absolute z-20 pointer-events-none hidden group-hover:flex items-center"
                        style={{
                          left: `calc(${leftPct + widthPct}% + 4px)`,
                          top: "50%",
                          transform: "translateY(-50%)",
                        }}
                      >
                        <span className="bg-gray-800 text-white text-[9px] font-mono px-1.5 py-0.5 rounded whitespace-nowrap shadow">
                          {isRunning
                            ? `${formatDuration(Date.now() - agent.startedAt!)} (running)`
                            : duration !== null
                            ? formatDuration(duration)
                            : "running..."}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Right: status + duration summary */}
                  <div className="shrink-0 w-20 pl-2 text-right">
                    {duration !== null ? (
                      <span className="text-[9px] font-mono text-gray-400">
                        {formatDuration(duration)}
                      </span>
                    ) : isRunning ? (
                      <span className="text-[9px] font-mono text-[#0068ff]">
                        running
                      </span>
                    ) : null}
                  </div>
                </div>
              );
            })}
          </div>
        );
      })}

      {/* Legend */}
      <div className="flex items-center gap-4 mt-2 pt-2 border-t border-gray-100 flex-wrap">
        <span className="text-[9px] text-gray-400 uppercase tracking-wider font-sans">Legend</span>
        {stepGroups.map(({ step }) => {
          const color = STEP_COLORS[step.index] ?? STEP_COLORS[0];
          return (
            <div key={step.id} className="flex items-center gap-1">
              <div
                className="w-2.5 h-2.5 rounded-sm shrink-0"
                style={{ backgroundColor: color.bar }}
              />
              <span className="text-[9px] text-gray-500 font-sans whitespace-nowrap">
                {step.name}
              </span>
            </div>
          );
        })}
        <div className="flex items-center gap-1">
          <div className="w-2.5 h-2.5 rounded-sm shrink-0 bg-red-400" />
          <span className="text-[9px] text-gray-500 font-sans">Failed</span>
        </div>
      </div>
    </div>
  );
}
