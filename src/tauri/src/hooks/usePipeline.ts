import { useState, useCallback, useRef, useEffect } from "react";
import { invoke } from "@tauri-apps/api/core";
import { Command } from "@tauri-apps/plugin-shell";
import type {
  PipelineStep,
  PipelineConfig,
  PipelineAgent,
  QualityGate,
  StepStatus,
} from "../types/pipeline";
import { PIPELINE_STEPS, AGENT_NAMES } from "../types/pipeline";
import { parseCLILine } from "../lib/cli";

interface PipelineSnapshot {
  steps: PipelineStep[];
  currentStep: number;
  isRunning: boolean;
  startTime: number | null;
  logs: string[];
  config: PipelineConfig | null;
  savedAt: number;
}

function createInitialSteps(): PipelineStep[] {
  return PIPELINE_STEPS.map((s) => ({
    ...s,
    status: "pending" as StepStatus,
    agents: [],
    gate: null,
    startedAt: null,
    completedAt: null,
  }));
}

export function usePipeline() {
  const [steps, setSteps] = useState<PipelineStep[]>(createInitialSteps());
  const [currentStep, setCurrentStep] = useState<number>(-1);
  const [isRunning, setIsRunning] = useState(false);
  const [startTime, setStartTime] = useState<number | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [pendingGate, setPendingGate] = useState<QualityGate | null>(null);
  const [config, setConfig] = useState<PipelineConfig | null>(null);
  const childRef = useRef<any | null>(null);

  const addLog = useCallback((line: string) => {
    setLogs((prev) => [...prev, line]);
  }, []);

  const updateStep = useCallback(
    (index: number, updates: Partial<PipelineStep>) => {
      setSteps((prev) =>
        prev.map((s, i) => (i === index ? { ...s, ...updates } : s))
      );
    },
    []
  );

  const addAgent = useCallback(
    (stepIndex: number, agent: PipelineAgent) => {
      setSteps((prev) =>
        prev.map((s, i) =>
          i === stepIndex
            ? { ...s, agents: [...s.agents.filter((a) => a.id !== agent.id), agent] }
            : s
        )
      );
    },
    []
  );

  const appendAgentLog = useCallback(
    (stepIndex: number, agentId: string, line: string) => {
      setSteps((prev) =>
        prev.map((s, i) =>
          i === stepIndex
            ? {
                ...s,
                agents: s.agents.map((a) =>
                  a.id === agentId
                    ? { ...a, logs: [...a.logs, line] }
                    : a
                ),
              }
            : s
        )
      );
    },
    []
  );

  const start = useCallback(
    async (pipelineConfig: PipelineConfig, fromStep?: number) => {
      setConfig(pipelineConfig);
      if (fromStep !== undefined && fromStep > 0) {
        // Keep completed steps, reset from fromStep onward
        setSteps((prev) =>
          prev.map((s) =>
            s.index < fromStep
              ? s
              : { ...s, status: "pending" as StepStatus, agents: [], gate: null, startedAt: null, completedAt: null }
          )
        );
        setCurrentStep(fromStep);
      } else {
        setSteps(createInitialSteps());
        setCurrentStep(0);
      }
      setIsRunning(true);
      setStartTime(Date.now());
      setLogs([]);
      setPendingGate(null);

      const args = [
        "--print",
        `/valuation-driver ${pipelineConfig.ticker}`,
      ];

      if (pipelineConfig.autoMode) {
        args[1] += " --auto";
      }
      if (fromStep !== undefined && fromStep > 0) {
        args[1] += ` --from-step ${fromStep + 1}`;
      }
      const sourcesDirs = [pipelineConfig.sellSideDir, pipelineConfig.consultingDir].filter(Boolean);
      if (sourcesDirs.length > 0) {
        args[1] += ` --sources ${sourcesDirs.join(",")}`;
      }

      try {
        const command = Command.create("claude", args);

        command.stdout.on("data", (line: string) => {
          addLog(line);
          const parsed = parseCLILine(line);

          switch (parsed.type) {
            case "step_start":
              if (parsed.stepIndex !== undefined) {
                setCurrentStep(parsed.stepIndex);
                updateStep(parsed.stepIndex, {
                  status: "running",
                  startedAt: Date.now(),
                });
              }
              break;
            case "step_complete":
              if (parsed.stepIndex !== undefined) {
                updateStep(parsed.stepIndex, {
                  status: "complete",
                  completedAt: Date.now(),
                });
              }
              break;
            case "agent_start":
              if (parsed.agentId) {
                const stepIdx = currentStep >= 0 ? currentStep : 0;
                addAgent(stepIdx, {
                  id: parsed.agentId,
                  name: parsed.agentId,
                  friendlyName:
                    AGENT_NAMES[parsed.agentId] || parsed.agentId,
                  status: "running",
                  outputFile: null,
                  logs: [line],
                });
              }
              break;
            case "agent_complete":
              if (parsed.agentId) {
                const stepIdx = currentStep >= 0 ? currentStep : 0;
                appendAgentLog(stepIdx, parsed.agentId, line);
                setSteps((prev) =>
                  prev.map((s, i) =>
                    i === stepIdx
                      ? {
                          ...s,
                          agents: s.agents.map((a) =>
                            a.id === parsed.agentId
                              ? { ...a, status: "complete" as const }
                              : a
                          ),
                        }
                      : s
                  )
                );
              }
              break;
            case "gate":
              if (parsed.stepIndex !== undefined && !pipelineConfig.autoMode) {
                setPendingGate({
                  stepIndex: parsed.stepIndex,
                  status: "awaiting_review",
                  criteria: [],
                  results: [],
                  notes: "",
                });
              }
              break;
            case "error":
              addLog(`[ERROR] ${line}`);
              break;
            case "log": {
              // Route log lines to active (running) agents in the current step
              const stepIdx = currentStep >= 0 ? currentStep : 0;
              setSteps((prev) => {
                const step = prev[stepIdx];
                if (!step) return prev;
                const runningAgents = step.agents.filter((a) => a.status === "running");
                if (runningAgents.length === 1) {
                  // Only one running agent — attribute the line to it
                  return prev.map((s, i) =>
                    i === stepIdx
                      ? {
                          ...s,
                          agents: s.agents.map((a) =>
                            a.id === runningAgents[0].id
                              ? { ...a, logs: [...a.logs, line] }
                              : a
                          ),
                        }
                      : s
                  );
                }
                // Multiple running agents — check if line mentions one by name
                for (const agent of runningAgents) {
                  if (line.includes(agent.id) || line.includes(agent.name)) {
                    return prev.map((s, i) =>
                      i === stepIdx
                        ? {
                            ...s,
                            agents: s.agents.map((a) =>
                              a.id === agent.id
                                ? { ...a, logs: [...a.logs, line] }
                                : a
                            ),
                          }
                        : s
                    );
                  }
                }
                // Can't attribute — add to all running agents
                return prev.map((s, i) =>
                  i === stepIdx
                    ? {
                        ...s,
                        agents: s.agents.map((a) =>
                          a.status === "running"
                            ? { ...a, logs: [...a.logs, line] }
                            : a
                        ),
                      }
                    : s
                );
              });
              break;
            }
          }
        });

        command.stderr.on("data", (line: string) => {
          addLog(`[stderr] ${line}`);
        });

        command.on("close", (data) => {
          setIsRunning(false);
          if (data.code === 0) {
            setSteps((prev) =>
              prev.map((s) =>
                s.status === "running"
                  ? { ...s, status: "complete", completedAt: Date.now() }
                  : s
              )
            );
          } else {
            addLog(`[EXIT] Process exited with code ${data.code}`);
          }
        });

        const child = await command.spawn();
        childRef.current = child;
      } catch (err) {
        addLog(`[ERROR] Failed to start pipeline: ${err}`);
        setIsRunning(false);
      }
    },
    [addLog, updateStep, addAgent, currentStep]
  );

  const approveGate = useCallback(
    async (notes: string) => {
      if (!pendingGate || !childRef.current) return;
      await childRef.current.write(
        new TextEncoder().encode(`approve\n${notes}\n`)
      );
      setPendingGate(null);
    },
    [pendingGate]
  );

  const rejectGate = useCallback(
    async (notes: string) => {
      if (!pendingGate || !childRef.current) return;
      await childRef.current.write(
        new TextEncoder().encode(`reject\n${notes}\n`)
      );
      setPendingGate((prev) =>
        prev ? { ...prev, status: "rejected", notes } : null
      );
    },
    [pendingGate]
  );

  const stop = useCallback(async () => {
    if (childRef.current) {
      await childRef.current.kill();
      childRef.current = null;
    }
    setIsRunning(false);
  }, []);

  const reset = useCallback(() => {
    setSteps(createInitialSteps());
    setCurrentStep(-1);
    setIsRunning(false);
    setStartTime(null);
    setLogs([]);
    setPendingGate(null);
    setConfig(null);
  }, []);

  const saveState = useCallback(() => {
    if (!config) return;
    const snapshot: PipelineSnapshot = {
      steps,
      currentStep,
      isRunning,
      startTime,
      logs: logs.slice(-500), // Keep last 500 lines
      config,
      savedAt: Date.now(),
    };
    invoke("save_pipeline_state", {
      ticker: config.ticker,
      state: JSON.stringify(snapshot),
    }).catch(console.error);
  }, [steps, currentStep, isRunning, startTime, logs, config]);

  useEffect(() => {
    if (!isRunning) return;
    const interval = setInterval(saveState, 5000);
    return () => clearInterval(interval);
  }, [isRunning, saveState]);

  const loadExistingSession = useCallback(async (ticker: string): Promise<boolean> => {
    try {
      const result = await invoke<Array<{
        step_index: number;
        step_name: string;
        files_found: string[];
        complete: boolean;
      }>>("detect_existing_session", { ticker });

      const hasAnyFiles = result.some((s) => s.files_found.length > 0);
      if (!hasAnyFiles) return false;

      // Reconstruct pipeline state from existing files
      setSteps((prev) =>
        prev.map((step) => {
          const detected = result.find((r) => r.step_index === step.index);
          if (!detected || detected.files_found.length === 0) return step;
          return {
            ...step,
            status: detected.complete ? ("complete" as const) : ("running" as const),
            completedAt: detected.complete ? Date.now() : null,
          };
        })
      );

      // Find the last completed step to set currentStep
      const lastComplete = [...result].reverse().find((s) => s.complete);
      setCurrentStep(lastComplete ? lastComplete.step_index : 0);

      setConfig({
        ticker: ticker.toUpperCase(),
        sector: "Alternative Asset Management",
        autoMode: false,
        sellSideDir: null,
        consultingDir: null,
        referencePeers: null,
      });
      setIsRunning(false);
      return true;
    } catch {
      return false;
    }
  }, []);

  const restore = useCallback(async (ticker: string): Promise<boolean> => {
    try {
      const raw = await invoke<string | null>("load_pipeline_state", { ticker });
      if (!raw) return false;
      const snapshot: PipelineSnapshot = JSON.parse(raw);
      // Only restore if pipeline was running (not finished cleanly)
      if (!snapshot.isRunning) return false;
      setSteps(snapshot.steps);
      setCurrentStep(snapshot.currentStep);
      setStartTime(snapshot.startTime);
      setLogs(snapshot.logs);
      setConfig(snapshot.config);
      // Mark as NOT running since the CLI process is gone
      setIsRunning(false);
      // Mark any "running" steps/agents as "failed" since the process died
      setSteps((prev) =>
        prev.map((s) => ({
          ...s,
          status: s.status === "running" ? ("failed" as const) : s.status,
          agents: s.agents.map((a) => ({
            ...a,
            status: a.status === "running" ? ("failed" as const) : a.status,
          })),
        }))
      );
      return true;
    } catch {
      return false;
    }
  }, []);

  return {
    steps,
    currentStep,
    isRunning,
    startTime,
    logs,
    pendingGate,
    config,
    start,
    stop,
    reset,
    approveGate,
    rejectGate,
    saveState,
    restore,
    loadExistingSession,
    addLog,
  };
}
