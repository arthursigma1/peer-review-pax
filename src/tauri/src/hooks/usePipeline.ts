import { useState, useCallback, useRef, useEffect } from "react";
import { invoke } from "@tauri-apps/api/core";
import type {
  PipelineStep,
  PipelineAgent,
  PipelineConfig,
  QualityGate,
  StepStatus,
  Checkpoint,
  OutputFile,
} from "../types/pipeline";
import { PIPELINE_STEPS, DEFAULT_TONE_PROFILE, INITIAL_CHECKPOINTS } from "../types/pipeline";
import { todayISO } from "../lib/utils";

interface PipelineSnapshot {
  steps: PipelineStep[];
  currentStep: number;
  isRunning: boolean;
  startTime: number | null;
  logs: string[];
  config: PipelineConfig | null;
  checkpoints: Checkpoint[];
  savedAt: number;
  runDate?: string | null;
}

const FOLDER_TO_STEP: Record<string, number> = {
  "1-universe": 0,
  "2-data": 1,
  "3-analysis": 2,
  "4-deep-dives": 3,
  "5-playbook": 4,
  "6-review": 5,
};

// Each requirement is an array of alternative filenames — any match satisfies it
const STEP_COMPLETE_REQS: Record<number, string[][]> = {
  0: [["peer_universe.json"], ["metric_taxonomy.json"], ["source_catalog.json"]],
  1: [["quantitative_data.json", "quantitative_tier1.json"], ["strategy_profiles.json"], ["strategic_actions.json"]],
  2: [["standardized_data.json", "standardized_matrix.json"], ["correlations.json", "correlation_results.json"], ["driver_ranking.json"]],
  3: [["platform_profiles.json"], ["asset_class_analysis.json"]],
  4: [["final_report.html"]],
  5: [["methodology_review.md", "results_review.md", "source_coverage_audit.md"]],
};

// Maps output files to the agent that produced them, for historical reconstruction
const FILE_TO_AGENT: Record<string, { step: number; id: string; name: string }> = {
  // Step 0 — Map the Industry
  "peer_universe.json": { step: 0, id: "universe-scout", name: "Industry Scanner" },
  "source_catalog.json": { step: 0, id: "source-mapper", name: "Source Cataloger" },
  "metric_taxonomy.json": { step: 0, id: "metric-architect", name: "Metrics Designer" },
  // Step 1 — Gather Data
  "quantitative_data.json": { step: 1, id: "data-collector", name: "Data Collector" },
  "quantitative_tier1.json": { step: 1, id: "data-collector-t1", name: "Data Collector T1" },
  "quantitative_tier2.json": { step: 1, id: "data-collector-t2", name: "Data Collector T2" },
  "quantitative_tier3.json": { step: 1, id: "data-collector-t3", name: "Data Collector T3" },
  "strategy_profiles.json": { step: 1, id: "strategy-extractor", name: "Strategy Researcher" },
  "strategic_actions.json": { step: 1, id: "strategy-extractor", name: "Strategy Researcher" },
  // Step 2 — Find What Drives Value
  "standardized_data.json": { step: 2, id: "metric-architect", name: "Statistical Analyst" },
  "standardized_matrix.json": { step: 2, id: "metric-architect", name: "Statistical Analyst" },
  "correlations.json": { step: 2, id: "metric-architect", name: "Statistical Analyst" },
  "correlation_results.json": { step: 2, id: "metric-architect", name: "Statistical Analyst" },
  "driver_ranking.json": { step: 2, id: "metric-architect", name: "Statistical Analyst" },
  "final_peer_set.json": { step: 2, id: "metric-architect", name: "Statistical Analyst" },
  // Step 3 — Deep-Dive Peers
  "platform_profiles.json": { step: 3, id: "platform-analyst", name: "Platform Profiler" },
  "asset_class_analysis.json": { step: 3, id: "vertical-analyst", name: "Sector Specialist" },
  // Step 4 — Build the Playbook
  "platform_playbook.json": { step: 4, id: "playbook-synthesizer", name: "Insight Synthesizer" },
  "playbook.json": { step: 4, id: "playbook-synthesizer", name: "Insight Synthesizer" },
  "asset_class_playbooks.json": { step: 4, id: "playbook-synthesizer", name: "Insight Synthesizer" },
  "target_company_lens.json": { step: 4, id: "target-lens", name: "Target Company Lens" },
  "target_lens.json": { step: 4, id: "target-lens", name: "Target Company Lens" },
  "final_report.html": { step: 4, id: "report-builder", name: "Report Composer" },
  // Step 5 — Review Analysis
  "methodology_review.md": { step: 5, id: "methodology-reviewer", name: "Methodology Reviewer" },
  "results_review.md": { step: 5, id: "results-reviewer", name: "Results Reviewer" },
  "source_coverage_audit.md": { step: 5, id: "methodology-reviewer", name: "Methodology Reviewer" },
  // Checkpoints
  "audit_cp1_data.json": { step: 1, id: "claim-auditor", name: "Fact Checker" },
  "audit_cp2_deep_dives.json": { step: 3, id: "claim-auditor", name: "Fact Checker" },
  "audit_cp3_playbook.json": { step: 4, id: "claim-auditor", name: "Fact Checker" },
};

// Infer agents from output files. If OutputFile objects are provided, use their
// modification timestamps to approximate agent start/end times for the timeline.
function inferAgentsFromFiles(
  filenames: string[],
  outputFiles?: OutputFile[],
): { agents: Record<number, PipelineAgent[]>; earliestMs: number | null; latestMs: number | null } {
  // Build a filename → modified-ms lookup from the full OutputFile list
  const tsLookup: Record<string, number> = {};
  if (outputFiles) {
    for (const f of outputFiles) {
      // OutputFile.modified is seconds since epoch; convert to ms
      tsLookup[f.filename] = f.modified * 1000;
    }
  }

  const agentsByStep: Record<number, Map<string, PipelineAgent>> = {};
  let earliestMs: number | null = null;
  let latestMs: number | null = null;

  for (const filename of filenames) {
    const mapping = FILE_TO_AGENT[filename];
    if (!mapping) continue;
    if (!agentsByStep[mapping.step]) agentsByStep[mapping.step] = new Map();
    const map = agentsByStep[mapping.step];

    const fileTs = tsLookup[filename] ?? null;
    if (fileTs !== null) {
      if (earliestMs === null || fileTs < earliestMs) earliestMs = fileTs;
      if (latestMs === null || fileTs > latestMs) latestMs = fileTs;
    }

    if (!map.has(mapping.id)) {
      map.set(mapping.id, {
        id: mapping.id,
        name: mapping.name,
        friendlyName: mapping.name,
        status: "complete",
        outputFile: null,
        logs: [],
        startedAt: null,
        completedAt: fileTs,
      });
    } else {
      // Update completedAt to the latest file timestamp for this agent
      const existing = map.get(mapping.id)!;
      if (fileTs !== null && (existing.completedAt === null || fileTs > existing.completedAt)) {
        existing.completedAt = fileTs;
      }
    }
  }

  // Estimate startedAt per agent: use the earliest file time of the previous step
  // (or pipeline start for step 0). This gives a rough Gantt chart.
  const stepEarliestTs: Record<number, number> = {};
  for (const [step, map] of Object.entries(agentsByStep)) {
    const times = Array.from(map.values())
      .map((a) => a.completedAt)
      .filter((t): t is number => t !== null);
    if (times.length > 0) stepEarliestTs[Number(step)] = Math.min(...times);
  }

  for (const [step, map] of Object.entries(agentsByStep)) {
    const stepIdx = Number(step);
    // Use previous step's earliest time as this step's start estimate
    const prevStepTs = stepIdx > 0 ? stepEarliestTs[stepIdx - 1] : null;
    const fallbackStart = prevStepTs ?? earliestMs;
    for (const agent of map.values()) {
      if (agent.startedAt === null && fallbackStart !== null) {
        agent.startedAt = fallbackStart;
      }
    }
  }

  const result: Record<number, PipelineAgent[]> = {};
  for (const [step, map] of Object.entries(agentsByStep)) {
    result[Number(step)] = Array.from(map.values());
  }
  return { agents: result, earliestMs, latestMs };
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
  const [runDate, setRunDate] = useState<string | null>(null);
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

  const updateCheckpoint = useCallback((id: string, updates: Partial<Checkpoint>) => {
    setCheckpoints((prev) =>
      prev.map((cp) => (cp.id === id ? { ...cp, ...updates } : cp))
    );
  }, []);


  // Sync pipeline step status from detected output files
  const syncFromFiles = useCallback((files: OutputFile[]) => {
    if (!isRunning) return;

    // Only consider files that were created/modified after the pipeline started.
    // This prevents stale files from a previous run from immediately completing all steps.
    const freshFiles = files.filter((f) => f.modified >= (startTime ?? 0));

    // Group files by folder → step
    const filesByStep: Record<number, string[]> = {};
    for (const f of freshFiles) {
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
      const reqs = STEP_COMPLETE_REQS[step.index] || [];
      const allComplete = reqs.length > 0 && reqs.every((alts) => alts.some((f) => detected.includes(f)));

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
  }, [isRunning, startTime, currentStep]);

  const start = useCallback(
    (pipelineConfig: PipelineConfig, fromStep?: number, nextRunDate?: string | null) => {
      const now = Date.now();
      setConfig(pipelineConfig);
      setRunDate(nextRunDate ?? todayISO());
      if (fromStep !== undefined && fromStep > 0) {
        setSteps((prev) =>
          prev.map((s) =>
            s.index < fromStep
              ? {
                  ...s,
                  status: "complete" as StepStatus,
                  completedAt: s.completedAt ?? now,
                }
              : { ...s, status: "pending" as StepStatus, agents: [], gate: null, startedAt: null, completedAt: null }
          )
        );
        setCurrentStep(fromStep);
      } else {
        setSteps(createInitialSteps());
        setCurrentStep(0);
      }
      setIsRunning(true);
      setStartTime(now);
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
    setRunDate(null);
  }, []);

  // Use a ref to capture latest state so saveState callback is stable
  const stateRef = useRef({ steps, currentStep, isRunning, startTime, logs, config, checkpoints, runDate });
  stateRef.current = { steps, currentStep, isRunning, startTime, logs, config, checkpoints, runDate };

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
      runDate: s.runDate,
      savedAt: Date.now(),
    };
    invoke("save_pipeline_state", {
      ticker: s.config.ticker,
      runDate: s.runDate,
      state: JSON.stringify(snapshot),
    }).catch(console.error);
  }, []);

  useEffect(() => {
    if (!isRunning) return;
    const interval = setInterval(saveState, 5000);
    return () => clearInterval(interval);
  }, [isRunning, saveState]);

  const loadExistingSession = useCallback(async (ticker: string, sessionRunDate?: string | null): Promise<boolean> => {
    try {
      const result = await invoke<Array<{
        step_index: number;
        step_name: string;
        files_found: string[];
        complete: boolean;
      }>>("detect_existing_session", { ticker, runDate: sessionRunDate ?? null });

      const hasAnyFiles = result.some((s) => s.files_found.length > 0);
      if (!hasAnyFiles) return false;

      // Fetch full file metadata (with timestamps) for agent timing reconstruction
      const outputFiles = await invoke<OutputFile[]>("list_outputs", {
        ticker,
        runDate: sessionRunDate ?? null,
      }).catch(() => [] as OutputFile[]);

      // Collect all files across steps for agent inference
      const allFiles = result.flatMap((s) => s.files_found);
      const { agents: inferredAgents, earliestMs } = inferAgentsFromFiles(allFiles, outputFiles);

      // Reconstruct pipeline state from existing files
      setSteps((prev) =>
        prev.map((step) => {
          const detected = result.find((r) => r.step_index === step.index);
          if (!detected || detected.files_found.length === 0) return step;
          const stepAgents = inferredAgents[step.index] ?? [];
          // Use file timestamps for step timing
          const agentTimes = stepAgents
            .map((a) => a.completedAt)
            .filter((t): t is number => t !== null);
          const stepStartedAt = stepAgents
            .map((a) => a.startedAt)
            .filter((t): t is number => t !== null);
          return {
            ...step,
            status: detected.complete ? ("complete" as const) : ("running" as const),
            startedAt: stepStartedAt.length > 0 ? Math.min(...stepStartedAt) : null,
            completedAt: detected.complete && agentTimes.length > 0 ? Math.max(...agentTimes) : null,
            agents: stepAgents,
          };
        })
      );

      // Find the last completed step to set currentStep
      const lastComplete = [...result].reverse().find((s) => s.complete);
      setCurrentStep(lastComplete ? lastComplete.step_index : 0);

      // Set startTime from earliest file so the timeline has a reference point
      setStartTime(earliestMs);

      setConfig({
        ticker: ticker.toUpperCase(),
        sector: "",
        autoMode: false,
        sellSideDir: null,
        consultingDir: null,
        referencePeers: null,
        toneProfile: DEFAULT_TONE_PROFILE,
      });
      setRunDate(sessionRunDate ?? null);
      setIsRunning(false);
      return true;
    } catch {
      return false;
    }
  }, []);

  const restore = useCallback(async (ticker: string, restoreRunDate?: string | null): Promise<boolean> => {
    try {
      const raw = await invoke<string | null>("load_pipeline_state", { ticker, runDate: restoreRunDate ?? null });
      if (!raw) return false;
      const snapshot: PipelineSnapshot = JSON.parse(raw);
      setSteps(snapshot.steps);
      setCurrentStep(snapshot.currentStep);
      setStartTime(snapshot.startTime);
      setLogs(snapshot.logs);
      setConfig(snapshot.config);
      setRunDate(snapshot.runDate ?? restoreRunDate ?? null);
      if (snapshot.checkpoints) {
        setCheckpoints(snapshot.checkpoints);
      }
      // Mark as NOT running since the CLI process is gone
      setIsRunning(false);
      // Mark any "running" steps/agents as stale (complete, not failed — session ended normally)
      setSteps((prev) =>
        prev.map((s) => ({
          ...s,
          status: s.status === "running" ? ("complete" as const) : s.status,
          agents: s.agents.map((a) => ({
            ...a,
            status: a.status === "running" ? ("complete" as const) : a.status,
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
    runDate,
    setRunDate,
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
    updateStep,
    addAgent,
    updateCheckpoint,
  };
}
