import { useState, useEffect } from "react";
import { invoke } from "@tauri-apps/api/core";

interface AgentDef {
  id: string;
  name: string;
  role: string;
  step: number;
  parallel: boolean;
  model: string;
  timeout_minutes: number;
}

interface PipelineStepDef {
  index: number;
  name: string;
  folder: string;
  agents: string[];
}

interface SlashCommandConfig {
  default_sector: string;
  auto_mode: boolean;
  max_retries: number;
  timeout_minutes: number;
  tier_size: number;
  max_depth_tables: number;
  max_rows_tables: number;
}

interface AgentConfig {
  agents: AgentDef[];
  steps: PipelineStepDef[];
  command: SlashCommandConfig;
}

const DEFAULT_CONFIG: AgentConfig = {
  agents: [
    { id: "universe-scout", name: "Industry Scanner", role: "Maps the full peer universe — identifies all publicly listed firms in the sector, classifies by business model", step: 0, parallel: true, model: "claude-sonnet-4-20250514", timeout_minutes: 15 },
    { id: "source-mapper", name: "Source Cataloger", role: "Catalogs public data sources per firm — filings, transcripts, research reports — with bias tags", step: 0, parallel: true, model: "claude-sonnet-4-20250514", timeout_minutes: 15 },
    { id: "metric-architect", name: "Metrics Designer", role: "Defines the metric taxonomy — driver candidates, valuation multiples, and contextual metrics", step: 0, parallel: true, model: "claude-sonnet-4-20250514", timeout_minutes: 10 },
    { id: "data-collector-t1", name: "Data Collector (Tier 1)", role: "Extracts quantitative data for top ~9 firms by AUM — earnings, scale, growth, efficiency metrics", step: 1, parallel: true, model: "claude-sonnet-4-20250514", timeout_minutes: 20 },
    { id: "data-collector-t2", name: "Data Collector (Tier 2)", role: "Extracts quantitative data for mid-tier ~9 firms", step: 1, parallel: true, model: "claude-sonnet-4-20250514", timeout_minutes: 20 },
    { id: "data-collector-t3", name: "Data Collector (Tier 3)", role: "Extracts quantitative data for remaining smaller firms", step: 1, parallel: true, model: "claude-sonnet-4-20250514", timeout_minutes: 20 },
    { id: "strategy-extractor", name: "Strategy Researcher", role: "Extracts qualitative strategy profiles and catalogs strategic actions for all peer firms", step: 1, parallel: true, model: "claude-sonnet-4-20250514", timeout_minutes: 25 },
    { id: "statistical-analyst", name: "Statistical Analyst", role: "Standardizes data, runs Spearman correlations, bootstrap CIs, and ranks value drivers", step: 2, parallel: false, model: "claude-sonnet-4-20250514", timeout_minutes: 20 },
    { id: "convergence-analyst", name: "Convergence Analyst", role: "Merges quantitative and qualitative tracks — selects final 9-12 peer set for deep-dives", step: 2, parallel: false, model: "claude-sonnet-4-20250514", timeout_minutes: 10 },
    { id: "platform-analyst", name: "Platform Profiler", role: "Produces platform-level deep-dives — strategic agendas, value creation narratives, transferable insights", step: 3, parallel: true, model: "claude-sonnet-4-20250514", timeout_minutes: 20 },
    { id: "vertical-analyst", name: "Sector Specialist", role: "Conducts asset-class deep-dives across Credit, PE, Infra, Real Estate, GP-Led Solutions", step: 3, parallel: true, model: "claude-sonnet-4-20250514", timeout_minutes: 20 },
    { id: "playbook-synthesizer", name: "Insight Synthesizer", role: "Synthesizes value principles, platform strategic menu, and asset-class playbooks", step: 4, parallel: false, model: "claude-sonnet-4-20250514", timeout_minutes: 20 },
    { id: "report-builder", name: "Report Composer", role: "Generates the final navigable HTML report with all layers and statistical appendix", step: 4, parallel: false, model: "claude-sonnet-4-20250514", timeout_minutes: 15 },
    { id: "methodology-reviewer", name: "Methodology Reviewer", role: "Reviews statistical methodology, data coverage, metric selection, and peer selection logic", step: 5, parallel: true, model: "claude-sonnet-4-20250514", timeout_minutes: 15 },
    { id: "results-reviewer", name: "Results Reviewer", role: "Reviews final report for missed insights, weak conclusions, and untapped analytical angles", step: 5, parallel: true, model: "claude-sonnet-4-20250514", timeout_minutes: 15 },
  ],
  steps: [
    { index: 0, name: "Map the Industry", folder: "1-universe", agents: ["universe-scout", "source-mapper", "metric-architect"] },
    { index: 1, name: "Gather Data", folder: "2-data", agents: ["data-collector-t1", "data-collector-t2", "data-collector-t3", "strategy-extractor"] },
    { index: 2, name: "Find What Drives Value", folder: "3-analysis", agents: ["statistical-analyst", "convergence-analyst"] },
    { index: 3, name: "Deep-Dive Peers", folder: "4-deep-dives", agents: ["platform-analyst", "vertical-analyst"] },
    { index: 4, name: "Build the Playbook", folder: "5-playbook", agents: ["playbook-synthesizer", "report-builder"] },
    { index: 5, name: "Review Analysis", folder: "6-review", agents: ["methodology-reviewer", "results-reviewer"] },
  ],
  command: {
    default_sector: "Alternative Asset Management",
    auto_mode: false,
    max_retries: 2,
    timeout_minutes: 15,
    tier_size: 9,
    max_depth_tables: 3,
    max_rows_tables: 100,
  },
};

const STEP_COLORS = [
  "text-cyan-400 bg-cyan-500/10 ring-cyan-500/30",
  "text-blue-400 bg-blue-500/10 ring-blue-500/30",
  "text-violet-400 bg-violet-500/10 ring-violet-500/30",
  "text-amber-400 bg-amber-500/10 ring-amber-500/30",
  "text-teal-400 bg-teal-500/10 ring-teal-500/30",
  "text-rose-400 bg-rose-500/10 ring-rose-500/30",
];

const MODELS = [
  "claude-sonnet-4-20250514",
  "claude-opus-4-20250514",
  "claude-haiku-4-5-20251001",
];

export function AgentsOrg() {
  const [config, setConfig] = useState<AgentConfig>(DEFAULT_CONFIG);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [tab, setTab] = useState<"pipeline" | "command">("pipeline");
  const [dirty, setDirty] = useState(false);

  useEffect(() => {
    invoke<string>("read_output_file", { path: getConfigPath() })
      .then((content) => {
        const loaded = JSON.parse(content) as AgentConfig;
        setConfig(loaded);
      })
      .catch(() => {
        // No config saved yet, use defaults
      });
  }, []);

  function getConfigPath() {
    // Store at project level
    return "";
  }

  const updateAgent = (id: string, field: keyof AgentDef, value: string | number | boolean) => {
    setConfig((prev) => ({
      ...prev,
      agents: prev.agents.map((a) => a.id === id ? { ...a, [field]: value } : a),
    }));
    setDirty(true);
  };

  const updateCommand = (field: keyof SlashCommandConfig, value: string | number | boolean) => {
    setConfig((prev) => ({
      ...prev,
      command: { ...prev.command, [field]: value },
    }));
    setDirty(true);
  };

  const handleSave = async () => {
    try {
      const root = await invoke<string>("get_project_root");
      const path = `${root}/.claude/agent_config.json`;
      await invoke("write_output_file", {
        path,
        content: JSON.stringify(config, null, 2),
      });
      setDirty(false);
    } catch (err) {
      console.error("Failed to save config:", err);
    }
  };

  const handleReset = () => {
    setConfig(DEFAULT_CONFIG);
    setDirty(true);
  };

  const selected = config.agents.find((a) => a.id === selectedAgent);

  return (
    <div className="h-full flex flex-col">
      {/* Tab bar */}
      <div className="flex items-center justify-between px-5 py-2 border-b border-zinc-800/80 shrink-0">
        <div className="flex items-center gap-1">
          {(["pipeline", "command"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                tab === t ? "bg-zinc-800 text-zinc-100" : "text-zinc-500 hover:text-zinc-300"
              }`}
            >
              {t === "pipeline" ? "Pipeline & Agents" : "Command Config"}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleReset}
            className="px-3 py-1.5 rounded-md text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
          >
            Reset Defaults
          </button>
          <button
            onClick={handleSave}
            disabled={!dirty}
            className={`px-4 py-1.5 rounded-md text-xs font-medium transition-colors ${
              dirty
                ? "bg-teal-500/15 text-teal-400 ring-1 ring-teal-500/30 hover:bg-teal-500/25"
                : "text-zinc-600 cursor-default"
            }`}
          >
            {dirty ? "Save Config" : "Saved"}
          </button>
        </div>
      </div>

      {tab === "pipeline" && (
        <div className="flex-1 flex min-h-0">
          {/* Left: Pipeline flow */}
          <div className="w-80 border-r border-zinc-800/80 overflow-y-auto p-4 space-y-3">
            <h3 className="text-xs uppercase tracking-wider text-zinc-500 mb-3">Pipeline Steps</h3>
            {config.steps.map((step) => {
              const stepAgents = config.agents.filter((a) => a.step === step.index);
              const color = STEP_COLORS[step.index] || STEP_COLORS[0];
              const hasParallel = stepAgents.some((a) => a.parallel);
              return (
                <div key={step.index} className="space-y-1">
                  <div className={`px-3 py-2 rounded-md ring-1 ${color}`}>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-mono opacity-60">S{step.index + 1}</span>
                      <span className="text-xs font-medium">{step.name}</span>
                      {hasParallel && (
                        <span className="text-[9px] px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-500 ml-auto">parallel</span>
                      )}
                    </div>
                    <div className="text-[10px] opacity-50 mt-0.5 font-mono">→ {step.folder}/</div>
                  </div>
                  <div className="pl-4 space-y-0.5">
                    {stepAgents.map((agent) => (
                      <button
                        key={agent.id}
                        onClick={() => setSelectedAgent(agent.id)}
                        className={`w-full text-left px-3 py-1.5 rounded text-xs transition-colors flex items-center gap-2 ${
                          selectedAgent === agent.id
                            ? "bg-zinc-800 text-zinc-100"
                            : "text-zinc-400 hover:bg-zinc-800/50 hover:text-zinc-300"
                        }`}
                      >
                        <span className="w-1.5 h-1.5 rounded-full bg-current shrink-0 opacity-40" />
                        <span className="truncate">{agent.name}</span>
                        {agent.parallel && (
                          <span className="text-[8px] text-zinc-600 ml-auto shrink-0">∥</span>
                        )}
                      </button>
                    ))}
                  </div>
                  {step.index < config.steps.length - 1 && (
                    <div className="flex justify-center py-1">
                      <span className="text-zinc-700 text-xs">↓</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Right: Agent detail */}
          <div className="flex-1 overflow-y-auto p-6">
            {selected ? (
              <div className="max-w-lg space-y-6">
                <div>
                  <div className="flex items-center gap-3 mb-1">
                    <h2 className="text-lg font-semibold text-zinc-100">{selected.name}</h2>
                    <span className={`text-[10px] px-2 py-0.5 rounded ring-1 ${STEP_COLORS[selected.step]}`}>
                      {config.steps[selected.step]?.name}
                    </span>
                  </div>
                  <p className="text-xs text-zinc-500 font-mono">{selected.id}</p>
                </div>

                <div>
                  <label className="block text-xs uppercase tracking-wider text-zinc-500 mb-2">Role</label>
                  <textarea
                    value={selected.role}
                    onChange={(e) => updateAgent(selected.id, "role", e.target.value)}
                    rows={3}
                    className="w-full px-3 py-2 rounded-lg bg-zinc-800/60 ring-1 ring-zinc-700 text-sm text-zinc-200 focus:ring-teal-500/60 focus:outline-none resize-none"
                  />
                </div>

                <div>
                  <label className="block text-xs uppercase tracking-wider text-zinc-500 mb-2">Display Name</label>
                  <input
                    type="text"
                    value={selected.name}
                    onChange={(e) => updateAgent(selected.id, "name", e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-zinc-800/60 ring-1 ring-zinc-700 text-sm text-zinc-200 focus:ring-teal-500/60 focus:outline-none"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs uppercase tracking-wider text-zinc-500 mb-2">Model</label>
                    <select
                      value={selected.model}
                      onChange={(e) => updateAgent(selected.id, "model", e.target.value)}
                      className="w-full px-3 py-2 rounded-lg bg-zinc-800/60 ring-1 ring-zinc-700 text-sm text-zinc-200 focus:ring-teal-500/60 focus:outline-none appearance-none"
                    >
                      {MODELS.map((m) => (
                        <option key={m} value={m}>{m.replace("claude-", "").replace("-20250514", "").replace("-20251001", "")}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs uppercase tracking-wider text-zinc-500 mb-2">Timeout (min)</label>
                    <input
                      type="number"
                      value={selected.timeout_minutes}
                      onChange={(e) => updateAgent(selected.id, "timeout_minutes", parseInt(e.target.value) || 10)}
                      min={5}
                      max={60}
                      className="w-full px-3 py-2 rounded-lg bg-zinc-800/60 ring-1 ring-zinc-700 text-sm text-zinc-200 focus:ring-teal-500/60 focus:outline-none"
                    />
                  </div>
                </div>

                <div className="flex items-center justify-between py-2">
                  <div>
                    <span className="text-sm text-zinc-300">Parallel Execution</span>
                    <p className="text-xs text-zinc-600">Runs alongside other agents in same step</p>
                  </div>
                  <button
                    onClick={() => updateAgent(selected.id, "parallel", !selected.parallel)}
                    className={`w-10 h-5 rounded-full transition-colors relative ${
                      selected.parallel ? "bg-teal-500" : "bg-zinc-700"
                    }`}
                  >
                    <div className={`absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform ${
                      selected.parallel ? "translate-x-5" : "translate-x-0.5"
                    }`} />
                  </button>
                </div>

                <div className="pt-4 border-t border-zinc-800/80">
                  <h3 className="text-xs uppercase tracking-wider text-zinc-500 mb-3">Output Files</h3>
                  <div className="text-xs font-mono text-zinc-500 space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-zinc-600">→</span>
                      <span>{config.steps[selected.step]?.folder}/</span>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="h-full flex items-center justify-center text-zinc-600 text-sm">
                Select an agent to view and edit its configuration
              </div>
            )}
          </div>
        </div>
      )}

      {tab === "command" && (
        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-lg mx-auto space-y-8">
            <div>
              <h2 className="text-lg font-semibold text-zinc-100 mb-1">Slash Command Configuration</h2>
              <p className="text-sm text-zinc-500">
                Parameters for <code className="text-teal-400 bg-zinc-800 px-1.5 py-0.5 rounded text-xs">/valuation-driver TICKER</code>
              </p>
            </div>

            <div className="space-y-5">
              <div>
                <label className="block text-xs uppercase tracking-wider text-zinc-500 mb-2">Default Sector</label>
                <select
                  value={config.command.default_sector}
                  onChange={(e) => updateCommand("default_sector", e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-zinc-800/60 ring-1 ring-zinc-700 text-sm text-zinc-200 focus:ring-teal-500/60 focus:outline-none appearance-none"
                >
                  {["Alternative Asset Management", "Banking & Financial Services", "Insurance", "Fintech", "Real Estate", "Technology", "Healthcare", "Energy", "Consumer", "Industrials"].map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>

              <div className="flex items-center justify-between py-2">
                <div>
                  <span className="text-sm text-zinc-300">Auto Mode Default</span>
                  <p className="text-xs text-zinc-600">Quality gates validated automatically</p>
                </div>
                <button
                  onClick={() => updateCommand("auto_mode", !config.command.auto_mode)}
                  className={`w-10 h-5 rounded-full transition-colors relative ${
                    config.command.auto_mode ? "bg-teal-500" : "bg-zinc-700"
                  }`}
                >
                  <div className={`absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform ${
                    config.command.auto_mode ? "translate-x-5" : "translate-x-0.5"
                  }`} />
                </button>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs uppercase tracking-wider text-zinc-500 mb-2">Agent Timeout (min)</label>
                  <input
                    type="number"
                    value={config.command.timeout_minutes}
                    onChange={(e) => updateCommand("timeout_minutes", parseInt(e.target.value) || 15)}
                    min={5}
                    max={60}
                    className="w-full px-3 py-2 rounded-lg bg-zinc-800/60 ring-1 ring-zinc-700 text-sm text-zinc-200 focus:ring-teal-500/60 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs uppercase tracking-wider text-zinc-500 mb-2">Max Retries</label>
                  <input
                    type="number"
                    value={config.command.max_retries}
                    onChange={(e) => updateCommand("max_retries", parseInt(e.target.value) || 2)}
                    min={0}
                    max={5}
                    className="w-full px-3 py-2 rounded-lg bg-zinc-800/60 ring-1 ring-zinc-700 text-sm text-zinc-200 focus:ring-teal-500/60 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs uppercase tracking-wider text-zinc-500 mb-2">Data Collection Tier Size</label>
                <p className="text-xs text-zinc-600 mb-2">Number of firms per data-collector tier (universe split into N/tier_size parallel agents)</p>
                <input
                  type="number"
                  value={config.command.tier_size}
                  onChange={(e) => updateCommand("tier_size", parseInt(e.target.value) || 9)}
                  min={3}
                  max={15}
                  className="w-full px-3 py-2 rounded-lg bg-zinc-800/60 ring-1 ring-zinc-700 text-sm text-zinc-200 focus:ring-teal-500/60 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs uppercase tracking-wider text-zinc-500 mb-2">Table Max Depth</label>
                  <input
                    type="number"
                    value={config.command.max_depth_tables}
                    onChange={(e) => updateCommand("max_depth_tables", parseInt(e.target.value) || 3)}
                    min={1}
                    max={10}
                    className="w-full px-3 py-2 rounded-lg bg-zinc-800/60 ring-1 ring-zinc-700 text-sm text-zinc-200 focus:ring-teal-500/60 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs uppercase tracking-wider text-zinc-500 mb-2">Table Max Rows</label>
                  <input
                    type="number"
                    value={config.command.max_rows_tables}
                    onChange={(e) => updateCommand("max_rows_tables", parseInt(e.target.value) || 100)}
                    min={10}
                    max={500}
                    className="w-full px-3 py-2 rounded-lg bg-zinc-800/60 ring-1 ring-zinc-700 text-sm text-zinc-200 focus:ring-teal-500/60 focus:outline-none"
                  />
                </div>
              </div>
            </div>

            {/* Pipeline summary */}
            <div className="pt-6 border-t border-zinc-800/80">
              <h3 className="text-xs uppercase tracking-wider text-zinc-500 mb-3">Pipeline Summary</h3>
              <div className="grid grid-cols-3 gap-4 text-center">
                <div className="bg-zinc-800/40 rounded-lg px-3 py-4">
                  <div className="text-2xl font-bold text-zinc-100">{config.agents.length}</div>
                  <div className="text-xs text-zinc-500 mt-1">Total Agents</div>
                </div>
                <div className="bg-zinc-800/40 rounded-lg px-3 py-4">
                  <div className="text-2xl font-bold text-zinc-100">{config.steps.length}</div>
                  <div className="text-xs text-zinc-500 mt-1">Pipeline Steps</div>
                </div>
                <div className="bg-zinc-800/40 rounded-lg px-3 py-4">
                  <div className="text-2xl font-bold text-zinc-100">{config.agents.filter((a) => a.parallel).length}</div>
                  <div className="text-xs text-zinc-500 mt-1">Parallel Agents</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
