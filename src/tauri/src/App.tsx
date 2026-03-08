import { useState, useEffect, useCallback, useRef } from "react";
import { invoke } from "@tauri-apps/api/core";
import { PipelineMonitor } from "./components/PipelineMonitor";
import { QualityGate } from "./components/QualityGate";
import { ResultsBrowser } from "./components/ResultsBrowser";
import { AgentsOrg } from "./components/AgentsOrg";
import { SourceUpload, ToneUpload } from "./components/SourceUpload";
import type { SourcePaths } from "./components/SourceUpload";
import { usePipeline } from "./hooks/usePipeline";
import { useFileWatcher } from "./hooks/useFileWatcher";
import { useNotifications } from "./hooks/useNotifications";
import type { PipelineConfig, ToneProfile } from "./types/pipeline";
import { DEFAULT_TONE_PROFILE } from "./types/pipeline";
import { parsePtyChunk } from "./lib/ptyParser";

interface ExistingSession {
  ticker: string;
  runDate: string | null;
  completedSteps: number;
  totalSteps: number;
  hasReport: boolean;
}

type Screen = "home" | "monitor" | "results" | "agents";

const SECTORS = [
  "Alternative Asset Management",
  "Banking & Financial Services",
  "Insurance",
  "Fintech",
  "Real Estate",
  "Technology",
  "Healthcare",
  "Energy",
  "Consumer",
  "Industrials",
];

const STEP_RANGE_OPTIONS = [
  { index: 1, label: "Step 1 — Map the Industry" },
  { index: 2, label: "Step 2 — Gather Data" },
  { index: 3, label: "Step 3 — Find What Drives Value" },
  { index: 4, label: "Step 4 — Deep-Dive Peers" },
  { index: 5, label: "Step 5 — Build the Playbook" },
  { index: 6, label: "Step 6 — Review Analysis" },
];

function buildSkillCmd(
  ticker: string,
  autoMode: boolean,
  sourcesDirs: (string | null)[],
  fromStep: number,
  toStep: number,
): string {
  let cmd = `/valuation-driver ${ticker}`;
  if (autoMode) cmd += " --auto";
  const dirs = sourcesDirs.filter(Boolean);
  if (dirs.length > 0) cmd += ` --sources ${dirs.join(",")}`;
  if (fromStep !== 1 || toStep !== 6) cmd += ` --from-step ${fromStep} --to-step ${toStep}`;
  return cmd;
}

function App() {
  const [screen, setScreen] = useState<Screen>("home");
  const [ticker, setTicker] = useState("");
  const [sector, setSector] = useState(SECTORS[0]);
  const [autoMode, setAutoMode] = useState(false);
  const [sources, setSources] = useState<SourcePaths>({ sellSide: null, consulting: null });
  const [referencePeers, setReferencePeers] = useState("");
  const [toneFiles, setToneFiles] = useState<string[]>([]);
  const [toneProfile, setToneProfile] = useState<ToneProfile>(DEFAULT_TONE_PROFILE);
  const [toneStatus, setToneStatus] = useState<"idle" | "extracting" | "done" | "error">("idle");
  const [ptyCommand, setPtyCommand] = useState<string | null>(null);
  const [ptyArgs, setPtyArgs] = useState<string[]>([]);
  const [fromStep, setFromStep] = useState(1);
  const [toStep, setToStep] = useState(6);

  const pipeline = usePipeline();
  const { files, runs, selectedRun, setSelectedRun, error: watcherError, resetForNewRun } = useFileWatcher(pipeline.config?.ticker || ticker || null);
  const { notify } = useNotifications();
  const {
    addAgent,
    addLog,
    approveGate,
    checkpoints,
    config,
    currentStep,
    isRunning,
    loadExistingSession,
    logs,
    pendingGate,
    restore,
    runDate,
    saveState,
    start,
    startTime,
    steps,
    stop,
    syncFromFiles,
    updateCheckpoint,
    updateStep,
    rejectGate,
  } = pipeline;

  const [isReviewRunning, setIsReviewRunning] = useState(false);
  const [restored, setRestored] = useState(false);
  const [existingSession, setExistingSession] = useState<ExistingSession | null>(null);
  const knownAgentsRef = useRef(new Set<string>());
  const validatedContractRef = useRef<string | null>(null);

  // Sync run selection: when user switches run in Results, also load that run's pipeline state
  useEffect(() => {
    if (!selectedRun || isRunning) return;
    const t = config?.ticker || ticker;
    if (!t) return;
    // Only reload if the run changed from what pipeline currently has
    if (selectedRun === runDate) return;
    restore(t, selectedRun).then((loaded) => {
      if (!loaded) {
        // No saved pipeline state for this run — reconstruct from files
        loadExistingSession(t, selectedRun);
      }
    });
  }, [selectedRun, isRunning, config?.ticker, ticker, runDate, restore, loadExistingSession]);

  // When file sync marks a step as complete, also mark its agents complete
  const markStepAgentsComplete = useCallback((stepIndex: number) => {
    const step = steps[stepIndex];
    if (!step) return;
    for (const agent of step.agents) {
      if (agent.status === "running") {
        addAgent(stepIndex, { ...agent, status: "complete" });
      }
    }
  }, [steps, addAgent]);

  // Parse PTY output to detect agents and step transitions
  const handlePtyData = useCallback((text: string) => {
    if (!isRunning) return;
    const events = parsePtyChunk(text, knownAgentsRef.current, currentStep);
    for (const ev of events) {
      switch (ev.type) {
        case "agent-spawned":
          if (ev.agent) {
            addAgent(ev.stepIndex, ev.agent);
            updateStep(ev.stepIndex, { status: "running", startedAt: Date.now() });
          }
          break;
        case "agent-complete":
          if (ev.agent) {
            addAgent(ev.stepIndex, ev.agent);
          }
          break;
        case "step-started":
          updateStep(ev.stepIndex, { status: "running", startedAt: Date.now() });
          break;
        case "step-complete":
          updateStep(ev.stepIndex, { status: "complete", completedAt: Date.now() });
          markStepAgentsComplete(ev.stepIndex);
          break;
        case "checkpoint": {
          if (ev.message) addLog(`[CHECKPOINT] ${ev.message}`);
          const cp = checkpoints.find(c => c.afterStep === ev.stepIndex);
          if (cp && (cp.status === "pending" || cp.status === "scanning")) {
            const passed = /PASSED|passed/i.test(ev.message || "");
            const blocked = /BLOCKED|blocked/i.test(ev.message || "");
            updateCheckpoint(cp.id, {
              status: blocked ? "blocked" : passed ? "passed" : "scanning",
            });
          }
          break;
        }
        case "quality-gate":
          if (ev.message) addLog(`[GATE] ${ev.message}`);
          break;
      }
    }
  }, [isRunning, currentStep, addAgent, updateStep, addLog, checkpoints, updateCheckpoint, markStepAgentsComplete]);

  const prevStepStatuses = useRef<string[]>([]);
  useEffect(() => {
    if (files.length > 0) {
      syncFromFiles(files);
    }
  }, [files, syncFromFiles]);

  // Watch for step status changes and mark agents complete
  useEffect(() => {
    const currentStatuses = steps.map(s => s.status);
    const prev = prevStepStatuses.current;
    for (let i = 0; i < currentStatuses.length; i++) {
      if (currentStatuses[i] === "complete" && prev[i] !== "complete") {
        markStepAgentsComplete(i);
      }
    }
    prevStepStatuses.current = currentStatuses;
  }, [steps, markStepAgentsComplete]);

  // Notify on quality gate awaiting review
  useEffect(() => {
    if (pendingGate) {
      const stepName = steps[pendingGate.stepIndex]?.name ?? `Step ${pendingGate.stepIndex + 1}`;
      notify("Quality Gate — Action Required", `"${stepName}" needs your review before the pipeline can continue.`);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- steps accessed for display only, trigger is pendingGate
  }, [pendingGate, notify]);

  // Notify on pipeline completion or failure
  useEffect(() => {
    if (!isRunning && steps.length > 0) {
      const allDone = steps.every((s) => s.status === "complete");
      const anyFailed = steps.some((s) => s.status === "failed");
      if (allDone) {
        notify("Pipeline Complete", `Analysis for ${config?.ticker ?? "ticker"} finished successfully.`);
      } else if (anyFailed) {
        const failed = steps.filter((s) => s.status === "failed").map((s) => s.name);
        notify("Pipeline Error", `Failed steps: ${failed.join(", ")}`);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- steps/config read at trigger time; adding them would cause spurious notifications
  }, [isRunning, notify]);

  // Read launch config (env vars) and pre-fill form, then check for existing session
  useEffect(() => {
    const init = async () => {
      // Check for CLI launch config (env vars: VDA_TICKER, VDA_AUTO, VDA_SECTOR)
      try {
        const launch = await invoke<{ ticker: string | null; auto_mode: boolean; sector: string | null }>("get_launch_config");
        if (launch.ticker) {
          setTicker(launch.ticker);
          setAutoMode(launch.auto_mode);
          if (launch.sector) {
            const match = SECTORS.find(s => s.toLowerCase().includes(launch.sector!.toLowerCase()));
            if (match) setSector(match);
          }
          return; // Don't also load from localStorage if env vars are set
        }
      } catch { /* ignore */ }

      // Fall back to localStorage for existing session detection
      const lastTicker = localStorage.getItem("vda-last-ticker");
      if (lastTicker && !ticker) {
        setTicker(lastTicker);
        try {
          const availableRuns = await invoke<string[]>("list_analysis_runs", { ticker: lastTicker });
          const latestRun = availableRuns[0] ?? null;
          const steps = await invoke<Array<{ step_index: number; files_found: string[]; complete: boolean }>>(
            "detect_existing_session", { ticker: lastTicker, runDate: latestRun }
          );
          const completed = steps.filter((s) => s.complete).length;
          const hasFiles = steps.some((s) => s.files_found.length > 0);
          if (hasFiles) {
            setExistingSession({
              ticker: lastTicker,
              runDate: latestRun,
              completedSteps: completed,
              totalSteps: 6,
              hasReport: steps.some((s) => s.files_found.some((f) => f.includes("final_report"))),
            });
          }
        } catch { /* ignore */ }
      }
    };
    init();
  }, []);

  const launchPipelineRun = useCallback(
    async (config: PipelineConfig, startStepNumber: number, endStepNumber: number) => {
      let nextRunDate: string | null = null;
      try {
        nextRunDate = await invoke<string>("resolve_next_run_dir", { ticker: config.ticker });
      } catch (err) {
        console.error("Failed to resolve next run directory:", err);
      }

      const skillCmd = buildSkillCmd(
        config.ticker,
        config.autoMode,
        [config.sellSideDir, config.consultingDir],
        startStepNumber,
        endStepNumber,
      );

      validatedContractRef.current = null;
      resetForNewRun();
      knownAgentsRef.current.clear();
      start(config, startStepNumber - 1, nextRunDate);
      if (nextRunDate) {
        setSelectedRun(nextRunDate);
      }
      setPtyCommand("claude");
      setPtyArgs(["--dangerously-skip-permissions", "--model", "sonnet", skillCmd]);
      setScreen("monitor");
    },
    [resetForNewRun, setSelectedRun, start],
  );

  const handleRunNextStep = useCallback(async () => {
    if (!config || isRunning) return;
    const nextStepIndex = steps.findIndex((s) => s.status !== "complete");
    if (nextStepIndex < 0 || nextStepIndex >= steps.length) return;
    const nextStepNumber = nextStepIndex + 1;
    await launchPipelineRun(config, nextStepNumber, nextStepNumber);
  }, [config, isRunning, steps, launchPipelineRun]);

  const handleStartReview = async () => {
    const reviewTicker = config?.ticker || ticker;
    if (!reviewTicker || isReviewRunning) return;
    setIsReviewRunning(true);
    setPtyCommand("claude");
    setPtyArgs(["--dangerously-skip-permissions", "--model", "sonnet", `/review-analysis ${reviewTicker}`]);
    setScreen("monitor");
  };

  useEffect(() => {
    const lastTicker = localStorage.getItem("vda-last-ticker");
    if (lastTicker && !restored) {
      const restoreLatestRun = async () => {
        let latestRun: string | null = null;
        try {
          const availableRuns = await invoke<string[]>("list_analysis_runs", { ticker: lastTicker });
          latestRun = availableRuns[0] ?? null;
        } catch {
          latestRun = null;
        }

        const didRestore = await restore(lastTicker, latestRun);
        if (didRestore) {
          setTicker(lastTicker);
          if (latestRun) setSelectedRun(latestRun);
          setScreen("monitor");
          setRestored(true);
        }
      };

      void restoreLatestRun();
    }
  }, [restore, restored, setSelectedRun]);

  useEffect(() => {
    if (isRunning || !config || !runDate || files.length === 0) return;

    const requiredPlaybookFiles = [
      "value_principles.md",
      "platform_playbook.json",
      "asset_class_playbooks.json",
      "report_metadata.json",
      "target_company_lens.json",
      "final_report.html",
    ];
    const hasBuildArtifacts = requiredPlaybookFiles.every((filename) =>
      files.some((file) => file.folder === "5-playbook" && file.filename === filename),
    );
    if (!hasBuildArtifacts) return;

    const firstFile = files[0];
    if (!firstFile) return;
    const runDir = firstFile.path.split("/").slice(0, -2).join("/");
    const latestModified = Math.max(...files.map((file) => file.modified));
    const validationKey = `${runDir}:${latestModified}`;
    if (validatedContractRef.current === validationKey) return;
    validatedContractRef.current = validationKey;

    invoke<{ passed: boolean; message: string }>("validate_contract", { runDir })
      .then((result) => {
        addLog(`[CONTRACT] ${result.passed ? "PASS" : "FAIL"} ${result.message}`);
        if (result.passed) {
          updateStep(4, { status: "complete", completedAt: Date.now() });
          window.setTimeout(saveState, 0);
          return;
        }
        updateStep(4, { status: "failed", completedAt: Date.now() });
        window.setTimeout(saveState, 0);
      })
      .catch((err) => {
        addLog(`[CONTRACT] FAIL ${err}`);
        updateStep(4, { status: "failed", completedAt: Date.now() });
        window.setTimeout(saveState, 0);
      });
  }, [files, isRunning, config, runDate, addLog, updateStep, saveState]);

  // Keyboard shortcuts: ⌘1 / ⌘2 / ⌘3 for navigation
  useEffect(() => {
    const screens: Screen[] = ["home", "monitor", "results", "agents"];
    const handler = (e: KeyboardEvent) => {
      if (!e.metaKey && !e.ctrlKey) return;
      const idx = parseInt(e.key) - 1;
      if (idx >= 0 && idx < screens.length) {
        e.preventDefault();
        setScreen(screens[idx]);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  useEffect(() => {
    if (toneFiles.length === 0) {
      setToneProfile(DEFAULT_TONE_PROFILE);
      setToneStatus("idle");
      return;
    }
    const extractTone = async () => {
      setToneStatus("extracting");
      try {
        await invoke("copy_tone_files", {
          ticker: ticker || "default",
          files: toneFiles,
        });
        const { Command } = await import("@tauri-apps/plugin-shell");
        const prompt = `Read the following documents and extract a writing tone profile as JSON. Documents: ${toneFiles.join(" and ")}.

Output ONLY valid JSON matching this schema:
{
  "source": "extracted",
  "reference_files": [${toneFiles.map(f => `"${f.split("/").pop()}"`).join(", ")}],
  "formality": "academic" | "professional" | "conversational",
  "voice": "active" | "passive" | "mixed",
  "sentence_style": "concise" | "elaborate" | "mixed",
  "hedging": "explicit" | "moderate" | "minimal",
  "data_presentation": "tables-first" | "narrative-first" | "integrated",
  "terminology": "technical" | "accessible" | "mixed",
  "nuances": "A 2-3 sentence description of distinctive writing style patterns, preferred phrasing, structural habits, and any unique stylistic choices observed across the documents."
}`;
        const command = Command.create("claude", ["--print", prompt]);
        let output = "";
        command.stdout.on("data", (line: string) => { output += line; });
        await command.spawn();
        await new Promise<void>((resolve) => {
          command.on("close", () => resolve());
        });
        const jsonStart = output.indexOf("{");
        const jsonEnd = output.lastIndexOf("}");
        if (jsonStart >= 0 && jsonEnd > jsonStart) {
          const parsed = JSON.parse(output.substring(jsonStart, jsonEnd + 1)) as ToneProfile;
          parsed.source = "extracted";
          parsed.reference_files = toneFiles.map(f => f.split("/").pop() || f);
          setToneProfile(parsed);
          setToneStatus("done");
        } else {
          throw new Error("No valid JSON in output");
        }
      } catch (err) {
        console.error("Tone extraction failed:", err);
        setToneStatus("error");
      }
    };
    extractTone();
  }, [toneFiles]);

  const handleStart = async () => {
    if (!ticker.trim()) return;
    const t = ticker.trim().toUpperCase();
    const config: PipelineConfig = {
      ticker: t,
      sector,
      autoMode,
      sellSideDir: sources.sellSide,
      consultingDir: sources.consulting,
      referencePeers: referencePeers.trim() || null,
      toneProfile,
    };
    localStorage.setItem("vda-last-ticker", config.ticker);
    await launchPipelineRun(config, fromStep, toStep);
  };

  return (
    <div className="h-screen flex flex-col bg-white text-gray-900 overflow-hidden">
      {/* Top nav */}
      <header className="h-12 flex items-center justify-between px-5 border-b border-gray-200 bg-white shrink-0">
        <div className="flex items-center gap-4">
          <h1 className="text-sm font-semibold tracking-tight">
            <span className="text-[#0068ff] font-semibold text-base">VDA</span>{" "}
            <span className="text-gray-500 font-normal">Pipeline Dashboard</span>
          </h1>
          {config && (
            <span className="text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-500 font-mono">
              {config.ticker}
            </span>
          )}
        </div>
        <nav className="flex items-center gap-1">
          {(["home", "monitor", "results", "agents"] as Screen[]).map((s, i) => (
            <button
              key={s}
              onClick={() => setScreen(s)}
              className={`
                px-3 py-1.5 rounded-md text-xs font-medium transition-colors flex items-center gap-1.5
                ${
                  screen === s
                    ? "bg-gray-100 text-gray-900"
                    : "text-gray-400 hover:text-gray-700"
                }
              `}
            >
              {s === "home" ? "New Analysis"
                : s === "monitor" ? "Pipeline"
                : s === "results" ? "Results"
                : "Agents"}
              <kbd className={`text-[9px] px-1 py-0.5 rounded hidden lg:inline ${
                screen === s ? "bg-gray-200 text-gray-500" : "bg-gray-100 text-gray-400"
              }`}>⌘{i + 1}</kbd>
            </button>
          ))}
        </nav>
      </header>

      {/* Main content */}
      <main className="flex-1 min-h-0">
        {screen === "home" && (
          <div className="h-full overflow-y-auto">
            {/* Existing session hero */}
            {existingSession && (
              <div className="border-b border-gray-200 bg-gray-50/50 px-8 py-8">
                <div className="max-w-3xl mx-auto">
                  <p className="text-sm text-gray-500 mb-1">Last analysis</p>
                  <h2 className="text-4xl font-semibold text-gray-900 tracking-tight">
                    {existingSession.ticker}
                  </h2>
                  <p className="text-sm text-gray-500 mt-2">
                    {existingSession.completedSteps}/{existingSession.totalSteps} steps completed
                    {existingSession.hasReport && " — report ready"}
                  </p>
                  <div className="mt-1 h-1 rounded-full bg-gray-200 overflow-hidden max-w-xs">
                    <div
                      className="h-full rounded-full bg-[#0068ff]"
                      style={{ width: `${(existingSession.completedSteps / existingSession.totalSteps) * 100}%` }}
                    />
                  </div>
                  <div className="flex gap-3 mt-5">
                    {existingSession.hasReport && (
                      <button
                        onClick={() => {
                          if (existingSession.runDate) setSelectedRun(existingSession.runDate);
                          setScreen("results");
                        }}
                        className="px-5 py-2 rounded-md text-sm font-medium bg-[#0068ff] text-white hover:bg-[#0055d4] transition-colors"
                      >
                        View Results
                      </button>
                    )}
                      <button
                      onClick={async () => {
                        const loaded = await loadExistingSession(existingSession.ticker, existingSession.runDate);
                        if (loaded) {
                          localStorage.setItem("vda-last-ticker", existingSession.ticker);
                          if (existingSession.runDate) setSelectedRun(existingSession.runDate);
                          setScreen("monitor");
                        }
                      }}
                      className="px-5 py-2 rounded-md text-sm font-medium text-gray-700 border border-gray-300 hover:bg-gray-50 transition-colors"
                    >
                      Pipeline View
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* New analysis section */}
            <div className="px-8 py-8">
              <div className="max-w-3xl mx-auto">
                {existingSession && (
                  <div className="flex items-center gap-3 mb-6">
                    <div className="h-px flex-1 bg-gray-200" />
                    <span className="text-xs text-gray-400">or start a new analysis</span>
                    <div className="h-px flex-1 bg-gray-200" />
                  </div>
                )}

                {!existingSession && (
                  <div className="mb-8">
                    <h2 className="text-3xl font-semibold text-gray-900 tracking-tight">
                      Valuation Driver Analysis
                    </h2>
                    <p className="text-sm text-gray-500 mt-2 max-w-lg">
                      Identify what drives valuation multiples and build a strategic playbook.
                    </p>
                  </div>
                )}

                {/* Ticker + Sector + Start in a single row */}
                <div className="flex items-end gap-3">
                  <div className="flex-1 max-w-[200px]">
                    <label htmlFor="ticker" className="block text-xs text-gray-500 mb-1.5">
                      Ticker
                    </label>
                    <input
                      id="ticker"
                      type="text"
                      value={ticker}
                      onChange={(e) => setTicker(e.target.value.toUpperCase())}
                      placeholder="PAX"
                      className="w-full px-4 py-2.5 rounded-md bg-gray-50 border border-gray-200 text-lg font-mono text-gray-900 placeholder:text-gray-400 focus:ring-2 focus:ring-[#0068ff]/40 focus:border-[#0068ff] focus:outline-none"
                      autoFocus
                    />
                  </div>
                  <div className="flex-1 max-w-[260px]">
                    <label htmlFor="sector" className="block text-xs text-gray-500 mb-1.5">
                      Sector
                    </label>
                    <select
                      id="sector"
                      value={sector}
                      onChange={(e) => setSector(e.target.value)}
                      className="w-full px-4 py-2.5 rounded-md bg-gray-50 border border-gray-200 text-sm text-gray-700 focus:ring-2 focus:ring-[#0068ff]/40 focus:border-[#0068ff] focus:outline-none appearance-none"
                    >
                      {SECTORS.map((s) => (
                        <option key={s} value={s}>
                          {s}
                        </option>
                      ))}
                    </select>
                  </div>
                  <button
                    onClick={handleStart}
                    disabled={!ticker.trim() || isRunning}
                    className={`
                      px-6 py-2.5 rounded-md text-sm font-semibold transition-all whitespace-nowrap
                      ${
                        ticker.trim() && !isRunning
                          ? "bg-[#0068ff] text-white hover:bg-[#0055d4]"
                          : "bg-gray-100 text-gray-400 cursor-not-allowed"
                      }
                    `}
                  >
                    {isRunning ? "Running..." : "Run VDA →"}
                  </button>
                </div>

                {/* Expectation setter */}
                <p className="text-xs text-gray-400 mt-3">
                  ~45 min · 13 agents · HTML report
                </p>

                {/* Advanced options (collapsed) */}
                <details className="mt-6 group">
                  <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700 select-none list-none flex items-center gap-1.5">
                    <span className="text-[10px] group-open:rotate-90 transition-transform">▸</span>
                    Advanced options
                  </summary>
                  <div className="mt-4 space-y-5 pl-0">
                    {/* Step range */}
                    <div>
                      <label className="block text-xs text-gray-500 mb-1.5">
                        Step range
                      </label>
                      <div className="flex items-center gap-2">
                        <div className="flex items-center gap-1.5">
                          <span className="text-xs text-gray-400">From</span>
                          <select
                            value={fromStep}
                            onChange={(e) => {
                              const val = Number(e.target.value);
                              setFromStep(val);
                              if (val > toStep) setToStep(val);
                            }}
                            className="px-3 py-2 rounded-md bg-gray-50 border border-gray-200 text-sm text-gray-700 focus:ring-2 focus:ring-[#0068ff]/40 focus:border-[#0068ff] focus:outline-none appearance-none"
                          >
                            {STEP_RANGE_OPTIONS.map((s) => (
                              <option key={s.index} value={s.index}>
                                {s.label}
                              </option>
                            ))}
                          </select>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <span className="text-xs text-gray-400">To</span>
                          <select
                            value={toStep}
                            onChange={(e) => {
                              const val = Number(e.target.value);
                              setToStep(val);
                              if (val < fromStep) setFromStep(val);
                            }}
                            className="px-3 py-2 rounded-md bg-gray-50 border border-gray-200 text-sm text-gray-700 focus:ring-2 focus:ring-[#0068ff]/40 focus:border-[#0068ff] focus:outline-none appearance-none"
                          >
                            {STEP_RANGE_OPTIONS.map((s) => (
                              <option key={s.index} value={s.index}>
                                {s.label}
                              </option>
                            ))}
                          </select>
                        </div>
                        {(fromStep !== 1 || toStep !== 6) && (
                          <button
                            onClick={() => { setFromStep(1); setToStep(6); }}
                            className="text-xs text-gray-400 hover:text-gray-600 transition-colors"
                          >
                            Reset
                          </button>
                        )}
                      </div>
                      {(fromStep !== 1 || toStep !== 6) && (
                        <p className="text-[11px] text-[#0068ff] mt-1.5">
                          Running steps {fromStep}–{toStep} only
                        </p>
                      )}
                    </div>

                    {/* Reference peers */}
                    <div>
                      <label htmlFor="reference-peers" className="block text-xs text-gray-500 mb-1.5">
                        Reference peer list
                      </label>
                      <input
                        id="reference-peers"
                        type="text"
                        value={referencePeers}
                        onChange={(e) => setReferencePeers(e.target.value)}
                        placeholder="BX, KKR, APO, ARES, BAM..."
                        className="w-full px-4 py-2.5 rounded-md bg-gray-50 border border-gray-200 text-sm text-gray-700 placeholder:text-gray-400 focus:ring-2 focus:ring-[#0068ff]/40 focus:border-[#0068ff] focus:outline-none font-mono"
                      />
                    </div>

                    {/* Source upload */}
                    <SourceUpload
                      sources={sources}
                      onSourcesChanged={setSources}
                    />

                    {/* Tone upload */}
                    <ToneUpload
                      files={toneFiles}
                      onFilesChanged={setToneFiles}
                      extractionStatus={toneStatus}
                    />

                    {/* Auto mode toggle */}
                    <div className="flex items-center justify-between py-2">
                      <div>
                        <span id="auto-mode-label" className="text-sm text-gray-700">Auto mode</span>
                        <p className="text-xs text-gray-400">
                          Quality gates validated automatically
                        </p>
                      </div>
                      <button
                        role="switch"
                        aria-checked={autoMode}
                        aria-labelledby="auto-mode-label"
                        onClick={() => setAutoMode(!autoMode)}
                        className="p-3 -m-3 cursor-pointer"
                      >
                        <div className={`w-10 h-5 rounded-full transition-colors relative ${autoMode ? "bg-[#0068ff]" : "bg-gray-300"}`}>
                          <div
                            className={`
                              absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform
                              ${autoMode ? "translate-x-5" : "translate-x-0.5"}
                            `}
                          />
                        </div>
                      </button>
                    </div>
                  </div>
                </details>
              </div>
            </div>
          </div>
        )}

        {/* Keep PipelineMonitor mounted (hidden) so the PTY terminal survives screen switches */}
        <div className={screen === "monitor" ? "flex-1 min-h-0" : "hidden"}>
          <PipelineMonitor
            steps={steps}
            currentStep={currentStep}
            logs={logs}
            startTime={startTime}
            isRunning={isRunning}
            checkpoints={checkpoints}
            runs={runs}
            selectedRun={selectedRun}
            onSelectRun={setSelectedRun}
            onRerunFromStep={config ? (stepIndex) => {
              void launchPipelineRun(config, stepIndex + 1, 6);
            } : undefined}
            onRunNextStep={config ? () => { void handleRunNextStep(); } : undefined}
            ptyCommand={ptyCommand}
            ptyArgs={ptyArgs}
            onPtyData={handlePtyData}
            onPtyExit={() => {
              // Mark all running agents as complete when session ends
              for (const step of steps) {
                for (const agent of step.agents) {
                  if (agent.status === "running") {
                    addAgent(step.index, { ...agent, status: "complete" });
                  }
                }
                if (step.status === "running") {
                  updateStep(step.index, { status: "complete", completedAt: Date.now() });
                }
              }
              stop();
              setPtyCommand(null);
              setPtyArgs([]);
              knownAgentsRef.current.clear();
              window.setTimeout(saveState, 0);
            }}
          />
        </div>

        {screen === "results" && (
          <ResultsBrowser
            files={files}
            ticker={config?.ticker || ticker || ""}
            onStartReview={ticker ? handleStartReview : undefined}
            isReviewRunning={isReviewRunning}
            runs={runs}
            selectedRun={selectedRun}
            onSelectRun={setSelectedRun}
            watcherError={watcherError}
          />
        )}

        {screen === "agents" && (
          <AgentsOrg />
        )}
      </main>

      {/* Quality gate modal */}
      {pendingGate && (
        <QualityGate
          gate={pendingGate}
          onApprove={approveGate}
          onReject={rejectGate}
        />
      )}
    </div>
  );
}

export default App;
