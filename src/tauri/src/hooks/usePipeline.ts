import { useState, useCallback, useRef, useEffect } from "react";
import { invoke } from "@tauri-apps/api/core";
import type {
  PipelineStep,
  PipelineConfig,
  QualityGate,
  StepStatus,
  Checkpoint,
} from "../types/pipeline";
import { PIPELINE_STEPS, DEFAULT_TONE_PROFILE, INITIAL_CHECKPOINTS } from "../types/pipeline";

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

  // Map output folders to step indices
  const FOLDER_TO_STEP: Record<string, number> = {
    "1-universe": 0,
    "2-data": 1,
    "3-analysis": 2,
    "4-deep-dives": 3,
    "5-playbook": 4,
    "6-review": 5,
  };

  // Key output files that indicate a step is complete
  const STEP_COMPLETE_FILES: Record<number, string[]> = {
    0: ["peer_universe.json", "metric_taxonomy.json", "source_catalog.json"],
    1: ["quantitative_data.json", "strategy_profiles.json"],
    2: ["correlations.json", "driver_ranking.json", "final_peer_set.json"],
    3: ["platform_profiles.json", "asset_class_analysis.json"],
    4: ["final_report.html"],
    5: ["methodology_review.md", "results_review.md"],
  };

  // Sync pipeline step status from detected output files
  const syncFromFiles = useCallback((files: { filename: string; folder: string }[]) => {
    if (!isRunning) return;

    // Group files by folder → step
    const filesByStep: Record<number, string[]> = {};
    for (const f of files) {
      const stepIdx = FOLDER_TO_STEP[f.folder];
      if (stepIdx !== undefined) {
        if (!filesByStep[stepIdx]) filesByStep[stepIdx] = [];
        filesByStep[stepIdx].push(f.filename);
      }
    }

    setSteps((prev) => prev.map((step) => {
      const detected = filesByStep[step.index];
      if (!detected || detected.length === 0) return step;

      // Has files → at least running
      const completionFiles = STEP_COMPLETE_FILES[step.index] || [];
      const allComplete = completionFiles.length > 0 && completionFiles.every((f) => detected.includes(f));

      if (allComplete && step.status !== "complete") {
        return { ...step, status: "complete" as StepStatus, completedAt: Date.now() };
      }
      if (step.status === "pending") {
        return { ...step, status: "running" as StepStatus, startedAt: Date.now() };
      }
      return step;
    }));

    // Update currentStep to highest running/complete step
    const highestActive = Object.keys(filesByStep).map(Number).sort((a, b) => b - a)[0];
    if (highestActive !== undefined && highestActive > currentStep) {
      setCurrentStep(highestActive);
    }
  }, [isRunning, currentStep]);

  const start = useCallback(
    (pipelineConfig: PipelineConfig, fromStep?: number) => {
      setConfig(pipelineConfig);
      if (fromStep !== undefined && fromStep > 0) {
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
      // NOTE: The actual CLI process is spawned by the PTY Terminal component,
      // not here. This function only initializes UI state.
    },
    []
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
    syncFromFiles,
  };
}
