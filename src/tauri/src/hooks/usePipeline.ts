import { useState, useCallback, useRef, useEffect } from "react";
import { invoke } from "@tauri-apps/api/core";
import { Command } from "@tauri-apps/plugin-shell";
import type {
  PipelineStep,
  PipelineConfig,
  PipelineAgent,
  QualityGate,
  StepStatus,
  Checkpoint,
} from "../types/pipeline";
import { PIPELINE_STEPS, AGENT_NAMES, DEFAULT_TONE_PROFILE, INITIAL_CHECKPOINTS } from "../types/pipeline";
import { parseCLILine } from "../lib/cli";

interface PipelineSnapshot {
  steps: PipelineStep[];
  currentStep: number;
  isRunning: boolean;
  startTime: number | null;
  logs: string[];
  config: PipelineConfig | null;
  checkpoints: Checkpoint[];
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

function createInitialCheckpoints(): Checkpoint[] {
  return INITIAL_CHECKPOINTS.map((cp) => ({
    ...cp,
    status: "pending" as const,
    summary: null,
    blockedClaims: [],
    retryCount: 0,
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
  const [checkpoints, setCheckpoints] = useState<Checkpoint[]>(createInitialCheckpoints());
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

  const updateCheckpoint = useCallback((id: string, updates: Partial<Checkpoint>) => {
    setCheckpoints((prev) =>
      prev.map((cp) => (cp.id === id ? { ...cp, ...updates } : cp))
    );
  }, []);

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
      setCheckpoints(createInitialCheckpoints());

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
            case "checkpoint":
              if (parsed.checkpointId && parsed.checkpointStatus) {
                const updates: Partial<Checkpoint> = { status: parsed.checkpointStatus };
                if (parsed.retryAttempt !== undefined) {
                  updates.retryCount = parsed.retryAttempt;
                }
                if (parsed.checkpointStatus === "passed" && parsed.claimsTotal) {
                  updates.summary = {
                    total: parsed.claimsTotal,
                    grounded: parsed.claimsPassed ?? 0,
                    inferred: 0,
                    weakEvidence: 0,
                    ungrounded: 0,
                    fabricated: 0,
                  };
                }
                if (parsed.checkpointStatus === "blocked") {
                  updates.summary = {
                    total: 0,
                    grounded: 0,
                    inferred: 0,
                    weakEvidence: 0,
                    ungrounded: parsed.claimsUngrounded ?? 0,
                    fabricated: parsed.claimsFabricated ?? 0,
                  };
                }
                updateCheckpoint(parsed.checkpointId, updates);
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
    [addLog, updateStep, addAgent, updateCheckpoint, currentStep]
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
    setCheckpoints(createInitialCheckpoints());
  }, []);

  // Use a ref to capture latest state so saveState callback is stable
  const stateRef = useRef({ steps, currentStep, isRunning, startTime, logs, config, checkpoints });
  stateRef.current = { steps, currentStep, isRunning, startTime, logs, config, checkpoints };

  const saveState = useCallback(() => {
    const s = stateRef.current;
    if (!s.config) return;
    const snapshot: PipelineSnapshot = {
      steps: s.steps,
      currentStep: s.currentStep,
      isRunning: s.isRunning,
      startTime: s.startTime,
      logs: s.logs.slice(-500), // Keep last 500 lines
      config: s.config,
      checkpoints: s.checkpoints,
      savedAt: Date.now(),
    };
    invoke("save_pipeline_state", {
      ticker: s.config.ticker,
      state: JSON.stringify(snapshot),
    }).catch(console.error);
  }, []);

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
        sector: "", // Resolved from company_context.json at pipeline start
        autoMode: false,
        sellSideDir: null,
        consultingDir: null,
        referencePeers: null,
        toneProfile: DEFAULT_TONE_PROFILE,
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
      if (snapshot.checkpoints) {
        setCheckpoints(snapshot.checkpoints);
      }
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
    checkpoints,
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
