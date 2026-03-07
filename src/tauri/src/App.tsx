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

  const pipeline = usePipeline();
  const { files, runs, selectedRun, setSelectedRun, error: watcherError } = useFileWatcher(pipeline.config?.ticker || ticker || null);
  const { notify } = useNotifications();

  const [isReviewRunning, setIsReviewRunning] = useState(false);
  const [restored, setRestored] = useState(false);
  const [existingSession, setExistingSession] = useState<ExistingSession | null>(null);
  const knownAgentsRef = useRef(new Set<string>());

  // Parse PTY output to detect agents and step transitions
  const handlePtyData = useCallback((text: string) => {
    if (!pipeline.isRunning) return;
    const events = parsePtyChunk(text, knownAgentsRef.current);
    for (const ev of events) {
      switch (ev.type) {
        case "agent-spawned":
          if (ev.agent) {
            pipeline.addAgent(ev.stepIndex, ev.agent);
            pipeline.updateStep(ev.stepIndex, { status: "running", startedAt: Date.now() });
          }
          break;
        case "agent-complete":
          if (ev.agent) {
            pipeline.addAgent(ev.stepIndex, ev.agent);
          }
          break;
        case "step-started":
          pipeline.updateStep(ev.stepIndex, { status: "running", startedAt: Date.now() });
          break;
        case "step-complete":
          pipeline.updateStep(ev.stepIndex, { status: "complete", completedAt: Date.now() });
          // Mark all agents in this step as complete
          markStepAgentsComplete(ev.stepIndex);
          break;
        case "checkpoint": {
          if (ev.message) pipeline.addLog(`[CHECKPOINT] ${ev.message}`);
          // Find the checkpoint that matches this step and update its status
          const cp = pipeline.checkpoints.find(c => c.afterStep === ev.stepIndex);
          if (cp && cp.status === "pending") {
            const passed = /PASSED|passed/i.test(ev.message || "");
            const blocked = /BLOCKED|blocked/i.test(ev.message || "");
            pipeline.updateCheckpoint(cp.id, {
              status: blocked ? "blocked" : passed ? "passed" : "scanning",
            });
          }
          break;
        }
        case "quality-gate":
          if (ev.message) pipeline.addLog(`[GATE] ${ev.message}`);
          break;
      }
    }
  }, [pipeline.isRunning, pipeline.addAgent, pipeline.updateStep, pipeline.addLog]);

  // When file sync marks a step as complete, also mark its agents complete
  const markStepAgentsComplete = useCallback((stepIndex: number) => {
    const step = pipeline.steps[stepIndex];
    if (!step) return;
    for (const agent of step.agents) {
      if (agent.status === "running") {
        pipeline.addAgent(stepIndex, { ...agent, status: "complete" });
      }
    }
  }, [pipeline.steps, pipeline.addAgent]);

  // Sync pipeline step status from detected files
  // Also mark agents complete when their step completes via file detection
  const prevStepStatuses = useRef<string[]>([]);
  useEffect(() => {
    if (files.length > 0) {
      pipeline.syncFromFiles(files);
    }
  }, [files, pipeline.syncFromFiles]);

  // Watch for step status changes and mark agents complete
  useEffect(() => {
    const currentStatuses = pipeline.steps.map(s => s.status);
    const prev = prevStepStatuses.current;
    for (let i = 0; i < currentStatuses.length; i++) {
      if (currentStatuses[i] === "complete" && prev[i] !== "complete") {
        markStepAgentsComplete(i);
      }
    }
    prevStepStatuses.current = currentStatuses;
  }, [pipeline.steps, markStepAgentsComplete]);

  // Notify on quality gate awaiting review
  useEffect(() => {
    if (pipeline.pendingGate) {
      const stepName = pipeline.steps[pipeline.pendingGate.stepIndex]?.name ?? `Step ${pipeline.pendingGate.stepIndex + 1}`;
      notify("Quality Gate — Action Required", `"${stepName}" needs your review before the pipeline can continue.`);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- steps accessed for display only, trigger is pendingGate
  }, [pipeline.pendingGate, notify]);

  // Notify on pipeline completion or failure
  useEffect(() => {
    if (!pipeline.isRunning && pipeline.steps.length > 0) {
      const allDone = pipeline.steps.every((s) => s.status === "complete");
      const anyFailed = pipeline.steps.some((s) => s.status === "failed");
      if (allDone) {
        notify("Pipeline Complete", `Analysis for ${pipeline.config?.ticker ?? "ticker"} finished successfully.`);
      } else if (anyFailed) {
        const failed = pipeline.steps.filter((s) => s.status === "failed").map((s) => s.name);
        notify("Pipeline Error", `Failed steps: ${failed.join(", ")}`);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- steps/config read at trigger time; adding them would cause spurious notifications
  }, [pipeline.isRunning, notify]);

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
          const steps = await invoke<Array<{ step_index: number; files_found: string[]; complete: boolean }>>(
            "detect_existing_session", { ticker: lastTicker }
          );
          const completed = steps.filter((s) => s.complete).length;
          const hasFiles = steps.some((s) => s.files_found.length > 0);
          if (hasFiles) {
            setExistingSession({
              ticker: lastTicker,
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

  const handleStartReview = async () => {
    const reviewTicker = pipeline.config?.ticker || ticker;
    if (!reviewTicker || isReviewRunning) return;
    setIsReviewRunning(true);
    setPtyCommand("claude");
    setPtyArgs(["--dangerously-skip-permissions", "--model", "sonnet", `/review-analysis ${reviewTicker}`]);
    setScreen("monitor");
  };

  useEffect(() => {
    const lastTicker = localStorage.getItem("vda-last-ticker");
    if (lastTicker && !restored) {
      pipeline.restore(lastTicker).then((didRestore) => {
        if (didRestore) {
          setTicker(lastTicker);
          setScreen("monitor");
          setRestored(true);
        }
      });
    }
  }, []);

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

  const handleStart = () => {
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

    // Build claude CLI command for interactive PTY session
    let skillCmd = `/valuation-driver ${t}`;
    if (autoMode) skillCmd += " --auto";
    const sourcesDirs = [sources.sellSide, sources.consulting].filter(Boolean);
    if (sourcesDirs.length > 0) skillCmd += ` --sources ${sourcesDirs.join(",")}`;
    setPtyCommand("claude");
    setPtyArgs(["--dangerously-skip-permissions", "--model", "sonnet", skillCmd]);

    // Also set pipeline config for UI state tracking
    knownAgentsRef.current.clear();
    pipeline.start(config);
    setScreen("monitor");
  };

  return (
    <div className="h-screen flex flex-col bg-zinc-950 text-zinc-100 overflow-hidden">
      {/* Top nav */}
      <header className="h-12 flex items-center justify-between px-5 border-b border-zinc-800/80 bg-zinc-950/90 backdrop-blur shrink-0">
        <div className="flex items-center gap-4">
          <h1 className="text-sm font-semibold tracking-tight">
            <span className="text-teal-400">VDA</span>{" "}
            <span className="text-zinc-400 font-normal">Pipeline Dashboard</span>
          </h1>
          {pipeline.config && (
            <span className="text-xs px-2 py-0.5 rounded bg-zinc-800 text-zinc-400 font-mono">
              {pipeline.config.ticker}
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
                    ? "bg-zinc-800 text-zinc-100"
                    : "text-zinc-500 hover:text-zinc-300"
                }
              `}
            >
              {s === "home" ? "New Analysis"
                : s === "monitor" ? "Pipeline"
                : s === "results" ? "Results"
                : "Agents"}
              <kbd className={`text-[9px] px-1 py-0.5 rounded hidden lg:inline ${
                screen === s ? "bg-zinc-700 text-zinc-400" : "bg-zinc-800/60 text-zinc-500"
              }`}>⌘{i + 1}</kbd>
            </button>
          ))}
        </nav>
      </header>

      {/* Main content */}
      <main className="flex-1 min-h-0">
        {screen === "home" && (
          <div className="h-full overflow-y-auto flex items-start justify-center py-8">
            <div className="w-full max-w-md space-y-6 px-6">
              <div className="text-center mb-8">
                <h2 className="text-2xl font-bold text-zinc-100 tracking-tight">
                  Valuation Driver Analysis
                </h2>
                <p className="text-sm text-zinc-500 mt-2">
                  Identify what drives valuation multiples and build a strategic playbook.
                  Enter a ticker to begin — the pipeline will scan peers, collect data,
                  and generate an actionable report.
                </p>
              </div>

              {/* Ticker input */}
              <div>
                <label htmlFor="ticker" className="block text-xs uppercase tracking-wider text-zinc-400 mb-2">
                  Company Ticker
                </label>
                <input
                  id="ticker"
                  type="text"
                  value={ticker}
                  onChange={(e) => setTicker(e.target.value.toUpperCase())}
                  placeholder="PAX"
                  className="w-full px-4 py-3 rounded-lg bg-zinc-800/60 ring-1 ring-zinc-700 text-lg font-mono text-zinc-100 placeholder:text-zinc-500 focus:ring-teal-500/60 focus:outline-none"
                  autoFocus
                />
              </div>

              {/* Sector */}
              <div>
                <label htmlFor="sector" className="block text-xs uppercase tracking-wider text-zinc-400 mb-2">
                  Sector
                </label>
                <select
                  id="sector"
                  value={sector}
                  onChange={(e) => setSector(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-lg bg-zinc-800/60 ring-1 ring-zinc-700 text-sm text-zinc-200 focus:ring-teal-500/60 focus:outline-none appearance-none"
                >
                  {SECTORS.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </div>

              {/* Reference peers */}
              <div>
                <label htmlFor="reference-peers" className="block text-xs uppercase tracking-wider text-zinc-400 mb-2">
                  Reference Peer List (optional)
                </label>
                <input
                  id="reference-peers"
                  type="text"
                  value={referencePeers}
                  onChange={(e) => setReferencePeers(e.target.value)}
                  placeholder="BX, KKR, APO, ARES, BAM..."
                  className="w-full px-4 py-2.5 rounded-lg bg-zinc-800/60 ring-1 ring-zinc-700 text-sm text-zinc-200 placeholder:text-zinc-500 focus:ring-teal-500/60 focus:outline-none font-mono"
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
                  <span id="auto-mode-label" className="text-sm text-zinc-300">Auto Mode</span>
                  <p className="text-xs text-zinc-500">
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
                  <div className={`w-10 h-5 rounded-full transition-colors relative ${autoMode ? "bg-teal-500" : "bg-zinc-700"}`}>
                    <div
                      className={`
                        absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform
                        ${autoMode ? "translate-x-5" : "translate-x-0.5"}
                      `}
                    />
                  </div>
                </button>
              </div>

              {/* Start button */}
              <button
                onClick={handleStart}
                disabled={!ticker.trim() || pipeline.isRunning}
                className={`
                  w-full py-3 rounded-lg text-sm font-semibold transition-all
                  ${
                    ticker.trim() && !pipeline.isRunning
                      ? "bg-teal-500 text-zinc-950 hover:bg-teal-400 shadow-lg shadow-teal-500/20"
                      : "bg-zinc-800 text-zinc-500 cursor-not-allowed"
                  }
                `}
              >
                {pipeline.isRunning ? "Pipeline Running..." : "Start New Analysis"}
              </button>

              {/* Existing session banner */}
              {existingSession && (
                <div className="rounded-lg ring-1 ring-zinc-700 bg-zinc-800/40 p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-zinc-200">
                        Existing analysis for <span className="font-mono text-teal-400">{existingSession.ticker}</span>
                      </p>
                      <p className="text-xs text-zinc-400 mt-0.5">
                        {existingSession.completedSteps}/{existingSession.totalSteps} steps completed
                        {existingSession.hasReport && " — report ready"}
                      </p>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={async () => {
                        const loaded = await pipeline.loadExistingSession(existingSession.ticker);
                        if (loaded) {
                          localStorage.setItem("vda-last-ticker", existingSession.ticker);
                          setScreen("monitor");
                        }
                      }}
                      className="flex-1 px-3 py-2 rounded-md text-xs font-medium text-zinc-200 ring-1 ring-zinc-600 hover:bg-zinc-700/50 transition-colors"
                    >
                      Load Pipeline View
                    </button>
                    {existingSession.hasReport && (
                      <button
                        onClick={() => setScreen("results")}
                        className="flex-1 px-3 py-2 rounded-md text-xs font-medium text-teal-400 ring-1 ring-teal-500/30 hover:bg-teal-500/10 transition-colors"
                      >
                        View Results
                      </button>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Keep PipelineMonitor mounted (hidden) so the PTY terminal survives screen switches */}
        <div className={screen === "monitor" ? "flex-1 min-h-0" : "hidden"}>
          <PipelineMonitor
            steps={pipeline.steps}
            currentStep={pipeline.currentStep}
            logs={pipeline.logs}
            startTime={pipeline.startTime}
            isRunning={pipeline.isRunning}
            checkpoints={pipeline.checkpoints}
            onRerunFromStep={pipeline.config ? (stepIndex) => {
              pipeline.start(pipeline.config!, stepIndex);
            } : undefined}
            ptyCommand={ptyCommand}
            ptyArgs={ptyArgs}
            onPtyData={handlePtyData}
            onPtyExit={() => {
              // Mark all running agents as complete when session ends
              for (const step of pipeline.steps) {
                for (const agent of step.agents) {
                  if (agent.status === "running") {
                    pipeline.addAgent(step.index, { ...agent, status: "complete" });
                  }
                }
                if (step.status === "running") {
                  pipeline.updateStep(step.index, { status: "complete", completedAt: Date.now() });
                }
              }
              pipeline.stop();
              setPtyCommand(null);
              setPtyArgs([]);
              knownAgentsRef.current.clear();
            }}
          />
        </div>

        {screen === "results" && (
          <ResultsBrowser
            files={files}
            ticker={pipeline.config?.ticker || ticker || ""}
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
      {pipeline.pendingGate && (
        <QualityGate
          gate={pipeline.pendingGate}
          onApprove={pipeline.approveGate}
          onReject={pipeline.rejectGate}
        />
      )}
    </div>
  );
}

export default App;
