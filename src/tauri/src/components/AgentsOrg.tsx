import { useState, useEffect } from "react";
import { invoke } from "@tauri-apps/api/core";
import type { ToneProfile } from "../types/pipeline";
import { DEFAULT_TONE_PROFILE } from "../types/pipeline";

interface AgentDef {
  id: string;
  name: string;
  role: string;
  instructions: string;
  step: number;
  parallel: boolean;
  model: string;
  temperature: number;
  max_output_tokens: number;
  timeout_minutes: number;
  tools: string[];
  input_files: string[];
  output_files: string[];
  retry_strategy: "simplified_prompt" | "same_prompt" | "skip";
}

interface PipelineStepDef {
  index: number;
  name: string;
  folder: string;
  agents: string[];
  gate_criteria: string[];
}

interface SlashCommandConfig {
  default_sector: string;
  auto_mode: boolean;
  max_retries: number;
  tier_size: number;
  base_run: string | null;
  tone_profile: ToneProfile;
}

interface AgentConfig {
  agents: AgentDef[];
  steps: PipelineStepDef[];
  command: SlashCommandConfig;
}

const AVAILABLE_TOOLS = ["WebSearch", "Read", "Write", "Glob", "Grep", "Bash", "Agent", "SendMessage"];

const DEFAULT_CONFIG: AgentConfig = {
  agents: [
    {
      id: "universe-scout", name: "Industry Scanner",
      role: "Maps the full peer universe — identifies all publicly listed firms in the sector, classifies by business model",
      instructions: "Catalog all publicly listed alternative asset managers globally. Target ~25 firms. Classify each as pure-play-alt (≥90% revenue from alts), majority-alt (60-89%), or partial-alt. Use WebSearch extensively for regulatory filings and factual data. Record null with missing_reason for unavailable data — never estimate.",
      step: 0, parallel: true, model: "claude-sonnet-4-6", temperature: 0.2, max_output_tokens: 16000, timeout_minutes: 15,
      tools: ["WebSearch", "Read", "Write"],
      input_files: ["company_context.json"],
      output_files: ["1-universe/peer_universe.json"],
      retry_strategy: "simplified_prompt",
    },
    {
      id: "source-mapper", name: "Source Cataloger",
      role: "Catalogs public data sources per firm — filings, transcripts, research reports — with bias tags",
      instructions: "Catalog sources for ~15 qualitative peers. Source types: 20-F/10-K, investor day presentations, earnings transcripts, Preqin/Bain/McKinsey reports, sell-side research, pension fund board docs, job postings. Assign PS-VD-NNN IDs and bias tags (company-produced, regulatory-filing, third-party-analyst, journalist, industry-report, peer-disclosure). Check supplemental manifest first if available.",
      step: 0, parallel: true, model: "claude-sonnet-4-6", temperature: 0.2, max_output_tokens: 16000, timeout_minutes: 15,
      tools: ["WebSearch", "Read", "Write"],
      input_files: ["company_context.json"],
      output_files: ["1-universe/source_catalog.json"],
      retry_strategy: "simplified_prompt",
    },
    {
      id: "metric-architect", name: "Metrics Designer",
      role: "Defines the metric taxonomy — driver candidates, valuation multiples, and contextual metrics",
      instructions: "Define all metrics by category. Drivers: DE/share, EPS, FEAUM, organic growth, asset class HHI, permanent capital %, FRE margin, mgmt fee rate. Valuation multiples (dependent): P/FRE, P/DE, EV/FEAUM. Market structure (contextual only — exclude from correlation): trading volume, passive ownership, free float. Each metric gets MET-VD-NNN ID with unit, category, and calculation notes.",
      step: 0, parallel: true, model: "claude-sonnet-4-6", temperature: 0.1, max_output_tokens: 12000, timeout_minutes: 10,
      tools: ["Read", "Write"],
      input_files: ["company_context.json"],
      output_files: ["1-universe/metric_taxonomy.json"],
      retry_strategy: "same_prompt",
    },
    {
      id: "data-collector-t1", name: "Data Collector (Tier 1)",
      role: "Extracts quantitative data for top ~9 firms by AUM",
      instructions: "Extract FY1, FY2, and 3-year historical data for firms ranked 1-9 by AUM. Primary sources: earnings releases, 20-F/10-K, investor day presentations. Supplemental data takes priority over web search. For each data point: firm_id, metric_id, value, period, currency, source_id, confidence (high/medium/low). Missing data → null with missing_reason. No estimation.",
      step: 1, parallel: true, model: "claude-sonnet-4-6", temperature: 0.1, max_output_tokens: 16000, timeout_minutes: 20,
      tools: ["WebSearch", "Read", "Write"],
      input_files: ["1-universe/peer_universe.json", "1-universe/metric_taxonomy.json"],
      output_files: ["2-data/quantitative_tier1.json"],
      retry_strategy: "simplified_prompt",
    },
    {
      id: "data-collector-t2", name: "Data Collector (Tier 2)",
      role: "Extracts quantitative data for mid-tier ~9 firms",
      instructions: "Same methodology as Tier 1 but for firms ranked 10-18 by AUM.",
      step: 1, parallel: true, model: "claude-sonnet-4-6", temperature: 0.1, max_output_tokens: 16000, timeout_minutes: 20,
      tools: ["WebSearch", "Read", "Write"],
      input_files: ["1-universe/peer_universe.json", "1-universe/metric_taxonomy.json"],
      output_files: ["2-data/quantitative_tier2.json"],
      retry_strategy: "simplified_prompt",
    },
    {
      id: "data-collector-t3", name: "Data Collector (Tier 3)",
      role: "Extracts quantitative data for remaining smaller firms",
      instructions: "Same methodology as Tier 1 but for firms ranked 19+ by AUM.",
      step: 1, parallel: true, model: "claude-sonnet-4-6", temperature: 0.1, max_output_tokens: 16000, timeout_minutes: 20,
      tools: ["WebSearch", "Read", "Write"],
      input_files: ["1-universe/peer_universe.json", "1-universe/metric_taxonomy.json"],
      output_files: ["2-data/quantitative_tier3.json"],
      retry_strategy: "simplified_prompt",
    },
    {
      id: "strategy-extractor", name: "Strategy Researcher",
      role: "Extracts qualitative strategy profiles and catalogs strategic actions for all peer firms",
      instructions: "For each of ~15 peer firms, extract standalone strategic profile across 10 dimensions: geographic reach, asset focus, asset class mix, origination model, fund type emphasis, capital source, distribution strategy, client segment, growth model, stated strategic priorities. Then catalog concrete strategic actions (M&A, product launches, geographic expansion) from prior 2-3 years with ACT-VD-NNN IDs. Profiles are peer-centric — do NOT use the target company as baseline.",
      step: 1, parallel: true, model: "claude-sonnet-4-6", temperature: 0.3, max_output_tokens: 32000, timeout_minutes: 25,
      tools: ["WebSearch", "Read", "Write", "Agent"],
      input_files: ["1-universe/source_catalog.json"],
      output_files: ["2-data/strategy_profiles.json", "2-data/strategic_actions.json"],
      retry_strategy: "simplified_prompt",
    },
    {
      id: "statistical-analyst", name: "Statistical Analyst",
      role: "Standardizes data, runs Spearman correlations, bootstrap CIs, ranks value drivers",
      instructions: "Sequential tasks: (1) Standardize — currency conversion to USD, fiscal year alignment, FRE definition reconciliation, coverage/outlier flagging. (2) Correlations — Spearman rank for each driver vs each valuation multiple (~45 pairs). Classify as stable driver (ρ>0.5 all 3), multiple-specific (ρ>0.5 for 1), moderate (0.3-0.5), or not a driver (<0.3). (3) Bootstrap 1000-iteration CIs, Bonferroni correction, leave-one-out sensitivity, temporal stability. (4) Rank top 5-6 drivers by avg |ρ|, compute quartile positions for all firms.",
      step: 2, parallel: false, model: "claude-opus-4-6", temperature: 0.1, max_output_tokens: 32000, timeout_minutes: 25,
      tools: ["Read", "Write", "Bash"],
      input_files: ["2-data/quantitative_data.json", "1-universe/metric_taxonomy.json"],
      output_files: ["3-analysis/standardized_data.json", "3-analysis/correlations.json", "3-analysis/statistical_methodology.md", "3-analysis/driver_ranking.json"],
      retry_strategy: "same_prompt",
    },
    {
      id: "convergence-analyst", name: "Convergence Analyst",
      role: "Merges quantitative and qualitative tracks — selects final 9-12 peer set for deep-dives",
      instructions: "Score firms on quantitative relevance (top quartile on 2+ stable drivers), qualitative relevance (strategic instructiveness), and source coverage (min 2 sources). Auto-include top-quartile firms, include bottom-quartile as cautionary cases if well-documented. Flag non-obvious peers from driver ranking. Target 9-12 firms. Document inclusion/exclusion rationale for each.",
      step: 2, parallel: false, model: "claude-opus-4-6", temperature: 0.2, max_output_tokens: 12000, timeout_minutes: 10,
      tools: ["Read", "Write"],
      input_files: ["3-analysis/driver_ranking.json", "2-data/strategic_actions.json", "1-universe/source_catalog.json"],
      output_files: ["3-analysis/final_peer_set.json"],
      retry_strategy: "same_prompt",
    },
    {
      id: "platform-analyst", name: "Platform Profiler",
      role: "Produces platform-level deep-dives — identity, strategy, actions, driver performance, value narrative, transferable insights",
      instructions: "For each firm in the final set (9-12), produce a 6-section profile: (1) Identity and scale, (2) Strategic agenda from Investor Day/annual report, (3) Key actions catalog from strategic_actions.json with citations, (4) Performance on top stable drivers with quartile positions, (5) Value creation narrative connecting strategy to valuation, (6) 3-5 transferable insights with implementation pathways: for each insight include HOW they did it (implementation sequence, what came first, prerequisites), timeline from announcement to measurable impact, and enabling conditions (organizational, capital, or market). Keep self-contained — do not reference the target company. All insights must cite ACT-VD-NNN or PS-VD-NNN IDs.",
      step: 3, parallel: true, model: "claude-opus-4-6", temperature: 0.3, max_output_tokens: 32000, timeout_minutes: 20,
      tools: ["WebSearch", "Read", "Write", "Agent"],
      input_files: ["3-analysis/final_peer_set.json", "3-analysis/driver_ranking.json", "2-data/strategy_profiles.json", "2-data/strategic_actions.json"],
      output_files: ["4-deep-dives/platform_profiles.json"],
      retry_strategy: "simplified_prompt",
    },
    {
      id: "vertical-analyst", name: "Sector Specialist",
      role: "Conducts asset-class deep-dives across 5 verticals with reference firms",
      instructions: "Deep-dive 5 verticals: Credit (ARES, OWL, HLN), PE (KKR, APO, CG, TPG), Infrastructure (BAM, EQT), Real Estate (BX, BAM), GP-Led Solutions (STEP, HLN, PGHN). For each: best-in-class profiles, winning strategies with evidence, vertical-specific driver salience, emerging trends. Ground all claims in specific peer actions.",
      step: 3, parallel: true, model: "claude-opus-4-6", temperature: 0.3, max_output_tokens: 24000, timeout_minutes: 20,
      tools: ["WebSearch", "Read", "Write"],
      input_files: ["3-analysis/driver_ranking.json", "2-data/strategic_actions.json"],
      output_files: ["4-deep-dives/asset_class_analysis.json"],
      retry_strategy: "simplified_prompt",
    },
    {
      id: "playbook-synthesizer", name: "Insight Synthesizer",
      role: "Synthesizes value principles, platform strategic menu, and asset-class playbooks",
      instructions: "Sequential outputs: (1) Value Principles — for each stable driver, plain-language finding with full statistical docs (rho, CI, p-value), economic mechanism, illustrative firms, limitations. (2) Platform Strategic Menu — organize by driver, enumerate proven plays (PLAY-NNN) with firms, actions, metric impact, prerequisites, risks. Cite ACT-VD-NNN and PS-VD-NNN throughout. (3) Asset Class Playbooks — same structure per vertical. For each stable value driver, also include Anti-patterns (ANTI-NNN): strategic actions that peers executed which did NOT improve performance or destroyed value. Frame as Don'ts with firm, action, negative outcome, and why it failed. Cite ACT-VD-NNN throughout.",
      step: 4, parallel: false, model: "claude-opus-4-6", temperature: 0.3, max_output_tokens: 32000, timeout_minutes: 20,
      tools: ["Read", "Write"],
      input_files: ["3-analysis/driver_ranking.json", "3-analysis/statistical_methodology.md", "4-deep-dives/platform_profiles.json", "4-deep-dives/asset_class_analysis.json"],
      output_files: ["5-playbook/value_principles.md", "5-playbook/platform_playbook.json", "5-playbook/asset_class_playbooks.json"],
      retry_strategy: "same_prompt",
    },
    {
      id: "report-builder", name: "Report Composer",
      role: "Generates the final navigable HTML report with sidebar nav, collapsible sections, sortable tables",
      instructions: "Produce a single self-contained HTML file with two layers: Platform (exec summary, methodology, drivers, firm strategies, strategic menu) and Asset Class (5 vertical sections). Requirements: sidebar navigation, collapsible sections, sortable data tables, statistical appendix with rho/CI/p-values, mandatory disclaimers verbatim from methodology. Styling: Georgia serif, teal/navy scheme, company name in header. If target_company_lens.json exists, add a 'Strategic Implications for {COMPANY}' chapter after Executive Summary with PHL/Board Guidance, Management Priorities, and Per-BU Recommendations. Include Anti-patterns & Cautionary Lessons section after Platform Strategic Menu. If style_guide.json exists, adapt tone and terminology to match while preserving analytical rigor.",
      step: 4, parallel: false, model: "claude-opus-4-6", temperature: 0.2, max_output_tokens: 32000, timeout_minutes: 15,
      tools: ["Read", "Write"],
      input_files: ["5-playbook/value_principles.md", "5-playbook/platform_playbook.json", "5-playbook/asset_class_playbooks.json", "4-deep-dives/platform_profiles.json", "3-analysis/statistical_methodology.md", "3-analysis/driver_ranking.json", "5-playbook/target_company_lens.json"],
      output_files: ["5-playbook/final_report.html"],
      retry_strategy: "same_prompt",
    },
    {
      id: "target-lens", name: "Target Company Lens",
      role: "Contextualizes playbook for the target company — filters plays by applicability, produces governance-ready strategic guidance",
      instructions: "For each PLAY-NNN in playbooks, classify as directly_applicable, requires_adaptation, or not_applicable based on target company's geography, asset classes, and scale. Produce Strategic Guidance structured for governance cascade: PHL/Board level (top 5 principles, portfolio priorities, 3-year targets), CEO/Management (priority initiatives, resource allocation, quick wins vs structural), Per-BU (top 3 plays per segment, competitive positioning, do's and don'ts). Include implementation pathways with sequencing and prerequisites.",
      step: 4, parallel: false, model: "claude-opus-4-6", temperature: 0.3, max_output_tokens: 32000, timeout_minutes: 20,
      tools: ["Read", "Write"],
      input_files: ["company_context.json", "5-playbook/platform_playbook.json", "5-playbook/asset_class_playbooks.json", "4-deep-dives/platform_profiles.json", "3-analysis/driver_ranking.json"],
      output_files: ["5-playbook/target_company_lens.json"],
      retry_strategy: "same_prompt",
    },
    {
      id: "methodology-reviewer", name: "Methodology Reviewer",
      role: "Reviews statistical methodology, data coverage, metric selection, and peer selection logic",
      instructions: "Read all pipeline outputs and the design doc. Identify gaps in: statistical methodology (correlation approach, sample size, corrections), data coverage (missing metrics, firms with low coverage), metric selection (missing drivers, redundant metrics), peer selection logic (inclusion/exclusion criteria). Produce structured improvement report with severity ratings.",
      step: 5, parallel: true, model: "claude-opus-4-6", temperature: 0.3, max_output_tokens: 16000, timeout_minutes: 15,
      tools: ["Read", "Write", "Glob"],
      input_files: ["3-analysis/statistical_methodology.md", "3-analysis/correlations.json", "3-analysis/driver_ranking.json", "3-analysis/final_peer_set.json"],
      output_files: ["6-review/methodology_review.md"],
      retry_strategy: "same_prompt",
    },
    {
      id: "results-reviewer", name: "Results Reviewer",
      role: "Reviews final report for missed insights, weak conclusions, and untapped analytical angles",
      instructions: "Read the final report and all supporting data. Identify: missed insights (data supports conclusions not drawn), weak conclusions (claims without strong evidence), data quality issues (suspicious values, inconsistencies), untapped analytical angles (cross-cutting themes, contrarian findings). Produce structured improvement report.",
      step: 5, parallel: true, model: "claude-opus-4-6", temperature: 0.4, max_output_tokens: 16000, timeout_minutes: 15,
      tools: ["Read", "Write"],
      input_files: ["5-playbook/final_report.html", "3-analysis/correlations.json", "4-deep-dives/platform_profiles.json"],
      output_files: ["6-review/results_review.md"],
      retry_strategy: "same_prompt",
    },
  ],
  steps: [
    { index: 0, name: "Map the Industry", folder: "1-universe", agents: ["universe-scout", "source-mapper", "metric-architect"], gate_criteria: ["Universe ≥ 20 firms", "Metric taxonomy complete (no duplicate IDs)", "Source coverage ≥ 3 per qualitative peer"] },
    { index: 1, name: "Gather Data", folder: "2-data", agents: ["data-collector-t1", "data-collector-t2", "data-collector-t3", "strategy-extractor"], gate_criteria: ["Metric coverage ≥ 60% for ≥ 80% of firms", "All 3 valuation multiples populated", "≥ 2 actions per qualitative peer"] },
    { index: 2, name: "Find What Drives Value", folder: "3-analysis", agents: ["statistical-analyst", "convergence-analyst"], gate_criteria: ["Final peer set is 9-12 firms", "Non-obvious peers resolved", "No CIs crossing zero without flag"] },
    { index: 3, name: "Deep-Dive Peers", folder: "4-deep-dives", agents: ["platform-analyst", "vertical-analyst"], gate_criteria: ["All final set firms profiled", "All 5 verticals covered", "Insights cite specific source IDs"] },
    { index: 4, name: "Build the Playbook", folder: "5-playbook", agents: ["playbook-synthesizer", "report-builder", "target-lens"], gate_criteria: ["HTML report renders correctly", "All mandatory disclaimers present", "Statistical appendix complete", "Target company lens produced (if applicable)", "Anti-patterns section included"] },
    { index: 5, name: "Review Analysis", folder: "6-review", agents: ["methodology-reviewer", "results-reviewer"], gate_criteria: ["Both review reports produced", "Findings categorized by severity"] },
  ],
  command: {
    default_sector: "Alternative Asset Management",
    auto_mode: false,
    max_retries: 2,
    tier_size: 9,
    base_run: null,
    tone_profile: DEFAULT_TONE_PROFILE,
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
  { id: "claude-sonnet-4-6", label: "Sonnet 4.6", desc: "Fast, structured extraction" },
  { id: "claude-opus-4-6", label: "Opus 4.6", desc: "Complex reasoning & synthesis" },
  { id: "claude-haiku-4-5-20251001", label: "Haiku 4.5", desc: "Quick validation tasks" },
];

export function AgentsOrg() {
  const [config, setConfig] = useState<AgentConfig>(DEFAULT_CONFIG);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [tab, setTab] = useState<"pipeline" | "command">("pipeline");
  const [dirty, setDirty] = useState(false);

  useEffect(() => {
    invoke<string>("get_project_root").then((root) => {
      invoke<string>("read_output_file", { path: `${root}/.claude/agent_config.json` })
        .then((content) => setConfig(JSON.parse(content) as AgentConfig))
        .catch(() => {});
    });
  }, []);

  const updateAgent = (id: string, updates: Partial<AgentDef>) => {
    setConfig((prev) => ({
      ...prev,
      agents: prev.agents.map((a) => a.id === id ? { ...a, ...updates } : a),
    }));
    setDirty(true);
  };

  const toggleTool = (agentId: string, tool: string) => {
    const agent = config.agents.find((a) => a.id === agentId);
    if (!agent) return;
    const tools = agent.tools.includes(tool)
      ? agent.tools.filter((t) => t !== tool)
      : [...agent.tools, tool];
    updateAgent(agentId, { tools });
  };

  const updateCommand = (field: keyof SlashCommandConfig, value: string | number | boolean | ToneProfile) => {
    setConfig((prev) => ({ ...prev, command: { ...prev.command, [field]: value } }));
    setDirty(true);
  };

  const updateToneProfile = (updates: Partial<ToneProfile>) => {
    const updated = { ...config.command.tone_profile, ...updates };
    updateCommand("tone_profile", updated);
  };

  const handleSave = async () => {
    try {
      const root = await invoke<string>("get_project_root");
      await invoke("write_output_file", {
        path: `${root}/.claude/agent_config.json`,
        content: JSON.stringify(config, null, 2),
      });
      setDirty(false);
    } catch (err) {
      console.error("Failed to save config:", err);
    }
  };

  const selected = config.agents.find((a) => a.id === selectedAgent);

  return (
    <div className="h-full flex flex-col">
      {/* Tab bar */}
      <div className="flex items-center justify-between px-5 py-2 border-b border-zinc-800/80 shrink-0">
        <div className="flex items-center gap-1">
          {(["pipeline", "command"] as const).map((t) => (
            <button key={t} onClick={() => setTab(t)}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${tab === t ? "bg-zinc-800 text-zinc-100" : "text-zinc-500 hover:text-zinc-300"}`}
            >
              {t === "pipeline" ? "Pipeline & Agents" : "Command Config"}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => { setConfig(DEFAULT_CONFIG); setDirty(true); }}
            className="px-3 py-1.5 rounded-md text-xs text-zinc-500 hover:text-zinc-300 transition-colors">
            Reset
          </button>
          <button onClick={handleSave} disabled={!dirty}
            className={`px-4 py-1.5 rounded-md text-xs font-medium transition-colors ${dirty ? "bg-teal-500/15 text-teal-400 ring-1 ring-teal-500/30 hover:bg-teal-500/25" : "text-zinc-600 cursor-default"}`}>
            {dirty ? "Save Config" : "Saved"}
          </button>
        </div>
      </div>

      {tab === "pipeline" && (
        <div className="flex-1 flex min-h-0">
          {/* Left: Pipeline flow */}
          <div className="w-80 border-r border-zinc-800/80 overflow-y-auto p-4 space-y-3 shrink-0">
            <h3 className="text-xs uppercase tracking-wider text-zinc-500 mb-3">Pipeline Steps</h3>
            {config.steps.map((step) => {
              const stepAgents = config.agents.filter((a) => a.step === step.index);
              const color = STEP_COLORS[step.index];
              return (
                <div key={step.index} className="space-y-1">
                  <div className={`px-3 py-2 rounded-md ring-1 ${color}`}>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-mono opacity-60">S{step.index + 1}</span>
                      <span className="text-xs font-medium">{step.name}</span>
                      {stepAgents.some((a) => a.parallel) && (
                        <span className="text-[9px] px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-500 ml-auto">parallel</span>
                      )}
                    </div>
                    <div className="text-[10px] opacity-50 mt-0.5 font-mono">→ {step.folder}/</div>
                  </div>
                  <div className="pl-4 space-y-0.5">
                    {stepAgents.map((agent) => (
                      <button key={agent.id} onClick={() => setSelectedAgent(agent.id)}
                        className={`w-full text-left px-3 py-1.5 rounded text-xs transition-colors flex items-center gap-2 ${selectedAgent === agent.id ? "bg-zinc-800 text-zinc-100" : "text-zinc-400 hover:bg-zinc-800/50 hover:text-zinc-300"}`}
                      >
                        <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${agent.model.includes("opus") ? "bg-violet-400" : agent.model.includes("haiku") ? "bg-green-400" : "bg-blue-400"}`} />
                        <span className="truncate">{agent.name}</span>
                        {agent.parallel && <span className="text-[8px] text-zinc-600 ml-auto shrink-0">∥</span>}
                      </button>
                    ))}
                  </div>
                  {step.index < config.steps.length - 1 && (
                    <div className="flex justify-center py-1"><span className="text-zinc-700 text-xs">↓</span></div>
                  )}
                </div>
              );
            })}
            {/* Model legend */}
            <div className="pt-4 border-t border-zinc-800/60 space-y-1.5">
              <h4 className="text-[10px] uppercase tracking-wider text-zinc-600">Model Legend</h4>
              {MODELS.map((m) => (
                <div key={m.id} className="flex items-center gap-2 text-[10px]">
                  <span className={`w-1.5 h-1.5 rounded-full ${m.id.includes("opus") ? "bg-violet-400" : m.id.includes("haiku") ? "bg-green-400" : "bg-blue-400"}`} />
                  <span className="text-zinc-400">{m.label}</span>
                  <span className="text-zinc-600">— {m.desc}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Right: Agent detail */}
          <div className="flex-1 overflow-y-auto p-6">
            {selected ? (
              <div className="max-w-2xl space-y-5">
                {/* Header */}
                <div>
                  <div className="flex items-center gap-3 mb-1">
                    <h2 className="text-lg font-semibold text-zinc-100">{selected.name}</h2>
                    <span className={`text-[10px] px-2 py-0.5 rounded ring-1 ${STEP_COLORS[selected.step]}`}>
                      {config.steps[selected.step]?.name}
                    </span>
                  </div>
                  <p className="text-xs text-zinc-500 font-mono">{selected.id}</p>
                </div>

                {/* Name + Role */}
                <div className="grid grid-cols-[1fr_2fr] gap-4">
                  <div>
                    <label className="block text-[10px] uppercase tracking-wider text-zinc-500 mb-1.5">Display Name</label>
                    <input type="text" value={selected.name}
                      onChange={(e) => updateAgent(selected.id, { name: e.target.value })}
                      className="w-full px-3 py-2 rounded-lg bg-zinc-800/60 ring-1 ring-zinc-700 text-sm text-zinc-200 focus:ring-teal-500/60 focus:outline-none" />
                  </div>
                  <div>
                    <label className="block text-[10px] uppercase tracking-wider text-zinc-500 mb-1.5">Role Summary</label>
                    <input type="text" value={selected.role}
                      onChange={(e) => updateAgent(selected.id, { role: e.target.value })}
                      className="w-full px-3 py-2 rounded-lg bg-zinc-800/60 ring-1 ring-zinc-700 text-sm text-zinc-200 focus:ring-teal-500/60 focus:outline-none" />
                  </div>
                </div>

                {/* Instructions */}
                <div>
                  <label className="block text-[10px] uppercase tracking-wider text-zinc-500 mb-1.5">Agent Instructions</label>
                  <textarea value={selected.instructions}
                    onChange={(e) => updateAgent(selected.id, { instructions: e.target.value })}
                    rows={5}
                    className="w-full px-3 py-2 rounded-lg bg-zinc-800/60 ring-1 ring-zinc-700 text-xs text-zinc-300 focus:ring-teal-500/60 focus:outline-none resize-y font-mono leading-relaxed" />
                </div>

                {/* Model + Temperature + Tokens + Timeout */}
                <div className="grid grid-cols-4 gap-3">
                  <div>
                    <label className="block text-[10px] uppercase tracking-wider text-zinc-500 mb-1.5">Model</label>
                    <select value={selected.model}
                      onChange={(e) => updateAgent(selected.id, { model: e.target.value })}
                      className="w-full px-2 py-2 rounded-lg bg-zinc-800/60 ring-1 ring-zinc-700 text-xs text-zinc-200 focus:ring-teal-500/60 focus:outline-none appearance-none">
                      {MODELS.map((m) => (
                        <option key={m.id} value={m.id}>{m.label}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-[10px] uppercase tracking-wider text-zinc-500 mb-1.5">Temperature</label>
                    <input type="number" value={selected.temperature} step={0.1} min={0} max={1}
                      onChange={(e) => updateAgent(selected.id, { temperature: parseFloat(e.target.value) || 0 })}
                      className="w-full px-2 py-2 rounded-lg bg-zinc-800/60 ring-1 ring-zinc-700 text-xs text-zinc-200 focus:ring-teal-500/60 focus:outline-none" />
                  </div>
                  <div>
                    <label className="block text-[10px] uppercase tracking-wider text-zinc-500 mb-1.5">Max Tokens</label>
                    <input type="number" value={selected.max_output_tokens} step={4000} min={4000} max={64000}
                      onChange={(e) => updateAgent(selected.id, { max_output_tokens: parseInt(e.target.value) || 16000 })}
                      className="w-full px-2 py-2 rounded-lg bg-zinc-800/60 ring-1 ring-zinc-700 text-xs text-zinc-200 focus:ring-teal-500/60 focus:outline-none" />
                  </div>
                  <div>
                    <label className="block text-[10px] uppercase tracking-wider text-zinc-500 mb-1.5">Timeout (min)</label>
                    <input type="number" value={selected.timeout_minutes} min={5} max={60}
                      onChange={(e) => updateAgent(selected.id, { timeout_minutes: parseInt(e.target.value) || 10 })}
                      className="w-full px-2 py-2 rounded-lg bg-zinc-800/60 ring-1 ring-zinc-700 text-xs text-zinc-200 focus:ring-teal-500/60 focus:outline-none" />
                  </div>
                </div>

                {/* Tools */}
                <div>
                  <label className="block text-[10px] uppercase tracking-wider text-zinc-500 mb-2">Available Tools</label>
                  <div className="flex flex-wrap gap-1.5">
                    {AVAILABLE_TOOLS.map((tool) => {
                      const active = selected.tools.includes(tool);
                      return (
                        <button key={tool} onClick={() => toggleTool(selected.id, tool)}
                          className={`px-2.5 py-1 rounded text-xs font-mono transition-colors ${active ? "bg-teal-500/15 text-teal-400 ring-1 ring-teal-500/30" : "bg-zinc-800/40 text-zinc-600 ring-1 ring-zinc-800 hover:text-zinc-400"}`}>
                          {tool}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Parallel + Retry */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex items-center justify-between py-2">
                    <div>
                      <span className="text-xs text-zinc-300">Parallel</span>
                      <p className="text-[10px] text-zinc-600">Runs alongside other agents</p>
                    </div>
                    <button onClick={() => updateAgent(selected.id, { parallel: !selected.parallel })}
                      className={`w-9 h-5 rounded-full transition-colors relative ${selected.parallel ? "bg-teal-500" : "bg-zinc-700"}`}>
                      <div className={`absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform ${selected.parallel ? "translate-x-4" : "translate-x-0.5"}`} />
                    </button>
                  </div>
                  <div>
                    <label className="block text-[10px] uppercase tracking-wider text-zinc-500 mb-1.5">On Timeout</label>
                    <select value={selected.retry_strategy}
                      onChange={(e) => updateAgent(selected.id, { retry_strategy: e.target.value as AgentDef["retry_strategy"] })}
                      className="w-full px-2 py-2 rounded-lg bg-zinc-800/60 ring-1 ring-zinc-700 text-xs text-zinc-200 focus:ring-teal-500/60 focus:outline-none appearance-none">
                      <option value="simplified_prompt">Re-dispatch with simpler prompt</option>
                      <option value="same_prompt">Retry same prompt</option>
                      <option value="skip">Skip agent</option>
                    </select>
                  </div>
                </div>

                {/* I/O Files */}
                <div className="grid grid-cols-2 gap-4 pt-2 border-t border-zinc-800/60">
                  <div>
                    <label className="block text-[10px] uppercase tracking-wider text-zinc-500 mb-2">Reads From</label>
                    <div className="space-y-1">
                      {selected.input_files.map((f, i) => (
                        <div key={i} className="flex items-center gap-2">
                          <span className="text-[10px] text-zinc-600">←</span>
                          <span className="text-xs font-mono text-zinc-400">{f}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div>
                    <label className="block text-[10px] uppercase tracking-wider text-zinc-500 mb-2">Writes To</label>
                    <div className="space-y-1">
                      {selected.output_files.map((f, i) => (
                        <div key={i} className="flex items-center gap-2">
                          <span className="text-[10px] text-teal-600">→</span>
                          <span className="text-xs font-mono text-teal-400/70">{f}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Quality Gate */}
                {config.steps[selected.step]?.gate_criteria.length > 0 && (
                  <div className="pt-2 border-t border-zinc-800/60">
                    <label className="block text-[10px] uppercase tracking-wider text-zinc-500 mb-2">Quality Gate — {config.steps[selected.step].name}</label>
                    <div className="space-y-1">
                      {config.steps[selected.step].gate_criteria.map((c, i) => (
                        <div key={i} className="flex items-center gap-2 text-xs text-zinc-400">
                          <span className="text-amber-500/60">◆</span>
                          <span>{c}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="h-full flex items-center justify-center text-zinc-600 text-sm">
                Select an agent to configure
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
                <label className="block text-[10px] uppercase tracking-wider text-zinc-500 mb-2">Default Sector</label>
                <select value={config.command.default_sector}
                  onChange={(e) => updateCommand("default_sector", e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-zinc-800/60 ring-1 ring-zinc-700 text-sm text-zinc-200 focus:ring-teal-500/60 focus:outline-none appearance-none">
                  {["Alternative Asset Management", "Banking & Financial Services", "Insurance", "Fintech", "Real Estate", "Technology", "Healthcare", "Energy", "Consumer", "Industrials"].map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>

              <div className="flex items-center justify-between py-2">
                <div>
                  <span className="text-sm text-zinc-300">Auto Mode</span>
                  <p className="text-xs text-zinc-600">Quality gates validated automatically — no manual approval</p>
                </div>
                <button onClick={() => updateCommand("auto_mode", !config.command.auto_mode)}
                  className={`w-10 h-5 rounded-full transition-colors relative ${config.command.auto_mode ? "bg-teal-500" : "bg-zinc-700"}`}>
                  <div className={`absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform ${config.command.auto_mode ? "translate-x-5" : "translate-x-0.5"}`} />
                </button>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-[10px] uppercase tracking-wider text-zinc-500 mb-2">Max Retries per Agent</label>
                  <p className="text-[10px] text-zinc-600 mb-2">How many times to retry a failed/timed-out agent</p>
                  <input type="number" value={config.command.max_retries}
                    onChange={(e) => updateCommand("max_retries", parseInt(e.target.value) || 2)}
                    min={0} max={5}
                    className="w-full px-3 py-2 rounded-lg bg-zinc-800/60 ring-1 ring-zinc-700 text-sm text-zinc-200 focus:ring-teal-500/60 focus:outline-none" />
                </div>
                <div>
                  <label className="block text-[10px] uppercase tracking-wider text-zinc-500 mb-2">Firms per Data Tier</label>
                  <p className="text-[10px] text-zinc-600 mb-2">Universe splits into ceil(N/{`{tier_size}`}) parallel collectors</p>
                  <input type="number" value={config.command.tier_size}
                    onChange={(e) => updateCommand("tier_size", parseInt(e.target.value) || 9)}
                    min={3} max={15}
                    className="w-full px-3 py-2 rounded-lg bg-zinc-800/60 ring-1 ring-zinc-700 text-sm text-zinc-200 focus:ring-teal-500/60 focus:outline-none" />
                </div>
              </div>
              <div>
                <label className="block text-[10px] uppercase tracking-wider text-zinc-500 mb-2">Base Run (Previous Date)</label>
                <p className="text-[10px] text-zinc-600 mb-2">Previous run date for iterative refinement</p>
                <input type="text" value={config.command.base_run ?? ""}
                  onChange={(e) => updateCommand("base_run", e.target.value || null as unknown as string)}
                  placeholder="YYYY-MM-DD"
                  className="w-full px-3 py-2 rounded-lg bg-zinc-800/60 ring-1 ring-zinc-700 text-sm text-zinc-200 placeholder-zinc-600 focus:ring-teal-500/60 focus:outline-none" />
              </div>

              {/* Tone Configuration */}
              <div className="space-y-4 pt-2 border-t border-zinc-800/60">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <label className="text-[10px] uppercase tracking-wider text-zinc-500">Tone Configuration</label>
                    {config.command.tone_profile.source === "extracted" ? (
                      <span className="text-[10px] px-2 py-0.5 rounded bg-teal-500/10 text-teal-400 ring-1 ring-teal-500/30">
                        Extracted from {config.command.tone_profile.reference_files.length} file{config.command.tone_profile.reference_files.length !== 1 ? "s" : ""}
                      </span>
                    ) : (
                      <span className="text-[10px] px-2 py-0.5 rounded bg-zinc-800 text-zinc-500 ring-1 ring-zinc-700">
                        Default
                      </span>
                    )}
                  </div>
                  {config.command.tone_profile.source !== "default" && (
                    <button
                      onClick={() => updateCommand("tone_profile", DEFAULT_TONE_PROFILE)}
                      className="text-[10px] text-zinc-500 hover:text-zinc-300 transition-colors"
                    >
                      Reset to Default
                    </button>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[10px] uppercase tracking-wider text-zinc-500 mb-1.5">Formality</label>
                    <select
                      value={config.command.tone_profile.formality}
                      onChange={(e) => updateToneProfile({ formality: e.target.value as ToneProfile["formality"] })}
                      className="w-full px-2 py-2 rounded-lg bg-zinc-800/60 ring-1 ring-zinc-700 text-xs text-zinc-200 focus:ring-teal-500/60 focus:outline-none appearance-none"
                    >
                      <option value="academic">academic</option>
                      <option value="professional">professional</option>
                      <option value="conversational">conversational</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-[10px] uppercase tracking-wider text-zinc-500 mb-1.5">Voice</label>
                    <select
                      value={config.command.tone_profile.voice}
                      onChange={(e) => updateToneProfile({ voice: e.target.value as ToneProfile["voice"] })}
                      className="w-full px-2 py-2 rounded-lg bg-zinc-800/60 ring-1 ring-zinc-700 text-xs text-zinc-200 focus:ring-teal-500/60 focus:outline-none appearance-none"
                    >
                      <option value="active">active</option>
                      <option value="passive">passive</option>
                      <option value="mixed">mixed</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-[10px] uppercase tracking-wider text-zinc-500 mb-1.5">Sentence Style</label>
                    <select
                      value={config.command.tone_profile.sentence_style}
                      onChange={(e) => updateToneProfile({ sentence_style: e.target.value as ToneProfile["sentence_style"] })}
                      className="w-full px-2 py-2 rounded-lg bg-zinc-800/60 ring-1 ring-zinc-700 text-xs text-zinc-200 focus:ring-teal-500/60 focus:outline-none appearance-none"
                    >
                      <option value="concise">concise</option>
                      <option value="elaborate">elaborate</option>
                      <option value="mixed">mixed</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-[10px] uppercase tracking-wider text-zinc-500 mb-1.5">Hedging</label>
                    <select
                      value={config.command.tone_profile.hedging}
                      onChange={(e) => updateToneProfile({ hedging: e.target.value as ToneProfile["hedging"] })}
                      className="w-full px-2 py-2 rounded-lg bg-zinc-800/60 ring-1 ring-zinc-700 text-xs text-zinc-200 focus:ring-teal-500/60 focus:outline-none appearance-none"
                    >
                      <option value="explicit">explicit</option>
                      <option value="moderate">moderate</option>
                      <option value="minimal">minimal</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-[10px] uppercase tracking-wider text-zinc-500 mb-1.5">Data Presentation</label>
                    <select
                      value={config.command.tone_profile.data_presentation}
                      onChange={(e) => updateToneProfile({ data_presentation: e.target.value as ToneProfile["data_presentation"] })}
                      className="w-full px-2 py-2 rounded-lg bg-zinc-800/60 ring-1 ring-zinc-700 text-xs text-zinc-200 focus:ring-teal-500/60 focus:outline-none appearance-none"
                    >
                      <option value="tables-first">tables-first</option>
                      <option value="narrative-first">narrative-first</option>
                      <option value="integrated">integrated</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-[10px] uppercase tracking-wider text-zinc-500 mb-1.5">Terminology</label>
                    <select
                      value={config.command.tone_profile.terminology}
                      onChange={(e) => updateToneProfile({ terminology: e.target.value as ToneProfile["terminology"] })}
                      className="w-full px-2 py-2 rounded-lg bg-zinc-800/60 ring-1 ring-zinc-700 text-xs text-zinc-200 focus:ring-teal-500/60 focus:outline-none appearance-none"
                    >
                      <option value="technical">technical</option>
                      <option value="accessible">accessible</option>
                      <option value="mixed">mixed</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-[10px] uppercase tracking-wider text-zinc-500 mb-1.5">Nuances</label>
                  <textarea
                    value={config.command.tone_profile.nuances}
                    onChange={(e) => updateToneProfile({ nuances: e.target.value })}
                    rows={4}
                    className="w-full px-3 py-2 rounded-lg bg-zinc-800/60 ring-1 ring-zinc-700 text-xs text-zinc-300 focus:ring-teal-500/60 focus:outline-none resize-y font-mono leading-relaxed"
                  />
                </div>
              </div>
            </div>

            {/* Pipeline summary */}
            <div className="pt-6 border-t border-zinc-800/80">
              <h3 className="text-xs uppercase tracking-wider text-zinc-500 mb-3">Pipeline Summary</h3>
              <div className="grid grid-cols-4 gap-3 text-center">
                <div className="bg-zinc-800/40 rounded-lg px-3 py-4">
                  <div className="text-2xl font-bold text-zinc-100">{config.agents.length}</div>
                  <div className="text-[10px] text-zinc-500 mt-1">Agents</div>
                </div>
                <div className="bg-zinc-800/40 rounded-lg px-3 py-4">
                  <div className="text-2xl font-bold text-zinc-100">{config.steps.length}</div>
                  <div className="text-[10px] text-zinc-500 mt-1">Steps</div>
                </div>
                <div className="bg-zinc-800/40 rounded-lg px-3 py-4">
                  <div className="text-2xl font-bold text-violet-400">{config.agents.filter((a) => a.model.includes("opus")).length}</div>
                  <div className="text-[10px] text-zinc-500 mt-1">Opus</div>
                </div>
                <div className="bg-zinc-800/40 rounded-lg px-3 py-4">
                  <div className="text-2xl font-bold text-blue-400">{config.agents.filter((a) => a.model.includes("sonnet")).length}</div>
                  <div className="text-[10px] text-zinc-500 mt-1">Sonnet</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
