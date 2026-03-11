import { useState, useEffect } from "react";
import { invoke } from "@tauri-apps/api/core";
import type { ToneProfile } from "../types/pipeline";
import { DEFAULT_TONE_PROFILE, INITIAL_CHECKPOINTS } from "../types/pipeline";

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
  evidence_mode: "legacy" | "incremental";
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
      instructions: "Catalog all publicly listed alternative asset managers globally with PAX relevance in mind. Target ~25 firms. Classify each as pure-play-alt (>=90% revenue from alts), majority-alt (60-89%), or partial-alt. Also assign preliminary archetype tags (north_star_peer, near_peer, adjacent_peer, anti_pattern_peer) plus scale bucket, geography bucket, and business-model notes relevant to PAX. Record both total AUM and FEAUM when available. Use regulatory filings and primary disclosures first. Record null with missing_reason for unavailable data and never estimate.",
      step: 0, parallel: true, model: "claude-sonnet-4-6", temperature: 0.2, max_output_tokens: 16000, timeout_minutes: 15,
      tools: ["WebSearch", "Read", "Write"],
      input_files: ["company_context.json"],
      output_files: ["1-universe/peer_universe.json"],
      retry_strategy: "simplified_prompt",
    },
    {
      id: "source-mapper", name: "Source Cataloger",
      role: "Catalogs public data sources per firm — filings, transcripts, research reports — with bias tags",
      instructions: "Catalog sources for qualitative peers using an explicit source hierarchy: (1) filings / annual reports / investor presentations, (2) earnings transcripts / management commentary, (3) reputable media / analyst coverage, (4) job postings or vendor PRs as supporting evidence only. Assign PS-VD-NNN IDs, bias tags, and track_affinity tags (quantitative, qualitative, both). Flag low-trust operational evidence explicitly so downstream agents do not promote it to fact.",
      step: 0, parallel: true, model: "claude-sonnet-4-6", temperature: 0.2, max_output_tokens: 16000, timeout_minutes: 15,
      tools: ["WebSearch", "Read", "Write"],
      input_files: ["company_context.json"],
      output_files: ["1-universe/source_catalog.json"],
      retry_strategy: "simplified_prompt",
    },
    {
      id: "metric-architect", name: "Metrics Designer",
      role: "Defines the metric taxonomy — driver candidates, valuation multiples, and contextual metrics",
      instructions: "Define the PAX-first metric taxonomy. Seed the initial candidate set from docs/pax-peer-assessment-framework.md, especially the PAX business-spec hypotheses around EPS / DE-share, FEAUM, AUM mix, TAM / market growth / market share, business efficiency, technology and data platforms, and market-structure context. Treat those as required starting hypotheses to test, not as confirmed truths: they may be classified as formal_ranking_eligible, contextual_only, or unsupported, but they may not be silently omitted without explanation. Include driver families for earnings, scale, mix/diversification, efficiency, and Operational Feasibility and Scalable Infrastructure. For each metric, assign MET-VD-NNN, unit, calculation notes, eligibility_class (formal_ranking_eligible, contextual_only, unsupported), coverage expectations, comparability caveats, and any mechanical_overlap_risk against valuation multiples. Required alt-manager operational metrics include Headcount_to_FEAUM, FEAUM_per_Employee, Compensation_and_Benefits_to_FEAUM, G&A_to_FEAUM, OpEx_Growth_minus_Fee_Revenue_Growth, Constant_Currency_Revenue_Growth, Integration_Costs_to_Revenue, CapEx_to_FEAUM, and Technology_Platform_Maturity (qualitative ordinal 0-3: standard vendor / proprietary platform / ML-AI integrated / commercialized product — collected for all firms regardless of capex disclosure). Valuation multiples remain P/FRE, P/DE, and EV/FEAUM.",
      step: 0, parallel: true, model: "claude-sonnet-4-6", temperature: 0.1, max_output_tokens: 12000, timeout_minutes: 10,
      tools: ["Read", "Write"],
      input_files: ["company_context.json", "docs/pax-peer-assessment-framework.md"],
      output_files: ["1-universe/metric_taxonomy.json"],
      retry_strategy: "same_prompt",
    },
    {
      id: "data-collector-t1", name: "Data Collector (Tier 1)",
      role: "Extracts quantitative data for top ~9 firms by AUM",
      instructions: "Extract FY1, FY2, and multi-year historical data for firms ranked 1-9 by AUM. Primary sources are filings, annual reports, investor presentations, and earnings supplements. Supplemental files take priority over web search. For each data point capture firm_id, metric_id, value, period, currency, source_id, confidence, reporting basis, and comparability notes. For cross-border firms compute the raw inputs needed for reported_usd_growth, local_currency_growth, constant_currency_growth, fx_delta, and fx_material_flag. Do not estimate missing quantitative values. If a valuation multiple cannot be computed, record null and the blocking reason explicitly.",
      step: 1, parallel: true, model: "claude-sonnet-4-6", temperature: 0.1, max_output_tokens: 16000, timeout_minutes: 20,
      tools: ["WebSearch", "Read", "Write"],
      input_files: ["1-universe/peer_universe.json", "1-universe/metric_taxonomy.json"],
      output_files: ["2-data/quantitative_tier1.json"],
      retry_strategy: "simplified_prompt",
    },
    {
      id: "data-collector-t2", name: "Data Collector (Tier 2)",
      role: "Extracts quantitative data for mid-tier ~9 firms",
      instructions: "Same PAX-first quantitative contract as Tier 1, but for firms ranked 10-18 by AUM. Preserve explicit comparability notes, FX inputs, and valuation-multiple missing reasons rather than smoothing gaps.",
      step: 1, parallel: true, model: "claude-sonnet-4-6", temperature: 0.1, max_output_tokens: 16000, timeout_minutes: 20,
      tools: ["WebSearch", "Read", "Write"],
      input_files: ["1-universe/peer_universe.json", "1-universe/metric_taxonomy.json"],
      output_files: ["2-data/quantitative_tier2.json"],
      retry_strategy: "simplified_prompt",
    },
    {
      id: "data-collector-t3", name: "Data Collector (Tier 3)",
      role: "Extracts quantitative data for remaining smaller firms",
      instructions: "Same PAX-first quantitative contract as Tier 1, but for firms ranked 19+ by AUM. Preserve explicit comparability notes, FX inputs, and valuation-multiple missing reasons rather than smoothing gaps.",
      step: 1, parallel: true, model: "claude-sonnet-4-6", temperature: 0.1, max_output_tokens: 16000, timeout_minutes: 20,
      tools: ["WebSearch", "Read", "Write"],
      input_files: ["1-universe/peer_universe.json", "1-universe/metric_taxonomy.json"],
      output_files: ["2-data/quantitative_tier3.json"],
      retry_strategy: "simplified_prompt",
    },
    {
      id: "strategy-extractor", name: "Strategy Researcher",
      role: "Extracts qualitative strategy profiles and catalogs strategic actions for all peer firms",
      instructions: "For each qualitative peer, extract a source-based strategic profile using docs/pax-peer-strategy-ontology.md as the minimum business-model decomposition grid, including the technology_capability dimension (proprietary_platform, commercialized_data_product, ml_integrated, standard_vendor). `strategy_profiles.json` must be a bare JSON array matching the repository contract exactly: each profile object uses `firm_id`, `firm_ticker`, optional `archetype` / `archetype_secondary`, `ontology_mapping`, `contextual_market_factors`, `stated_strategic_priorities`, `source_ids`, and `missing_dimensions`. Do not wrap the file in `metadata`, `profiles`, or a nested `profile` object. Map the peer across geographic reach, business focus, asset focus, asset class and investment strategies, sector orientation, origination engine, fund type, capital source, distribution strategy, client segment, growth agenda, share class, technology capability, and any additional criteria that materially shape transferability. Do not force-fit weak evidence; use null plus missing_reason when needed, and add new categories only when repeated evidence requires it. Then catalog concrete strategic actions from the prior 2-3 years in `strategic_actions.json` as a root object `{ \"actions\": [...] }` with ACT-VD-NNN IDs, using action_type values including technology-operations and technology-investment. For every firm, explicitly sweep for technology actions (proprietary platforms, AI/ML integration, commercialized data products, digital distribution, operational automation); if none found, record no_tech_action_found: true. For every action, run a parallel search for hidden execution work: systems integration, reporting and data-stack upgrades, controls or reconciliation changes, fund admin or servicing changes, compliance / treasury / risk infrastructure, org redesign, hiring needs, and geographic integration complexity. Every operational prerequisite must carry evidence_class, source_bias_tag, confidence_level, and stated_or_inferred. Profiles remain peer-evidence-first and must not use PAX as the baseline.",
      step: 1, parallel: true, model: "claude-opus-4-6", temperature: 0.3, max_output_tokens: 64000, timeout_minutes: 35,
      tools: ["WebSearch", "Read", "Write", "Agent"],
      input_files: ["1-universe/source_catalog.json", "docs/pax-peer-assessment-framework.md", "docs/pax-peer-strategy-ontology.md"],
      output_files: ["2-data/strategy_profiles.json", "2-data/strategic_actions.json"],
      retry_strategy: "simplified_prompt",
    },
    {
      id: "statistical-analyst", name: "Statistical Analyst",
      role: "Standardizes data, runs Spearman correlations, bootstrap CIs, ranks value drivers",
      instructions: "Sequential tasks: (1) Standardize data using local-currency-first growth logic, explicit FX fields, fiscal-year alignment, FRE definition reconciliation, coverage grading, comparability grading, and mechanical-overlap flags. (2) Run Spearman rank correlations for each eligible driver vs each valuation multiple. Use permutation-based p-values where feasible; only use asymptotic t-approximation with explicit disclosure when permutation is infeasible. (3) Apply one governance framework everywhere: BH FDR q=0.10 as primary discovery standard, Bonferroni as confirmatory badge only, confidence labels {high, moderate, directional, unsupported}, and stable-driver rule stable_v1_two_of_three. (4) Run the sensitivity protocol: leave-one-out, matched-sample view, archetype-stratified view, coverage/comparability review, mechanical-overlap disclosure, and confounding checks where conceptually required. (5) Write statistics_metadata.json capturing the exact statistical contract and ensure every headline driver carries coverage_quality, comparability_quality, mechanical_overlap_flag, independence_flag, p_value_method, and confirmatory_badge. Do not call a driver stable unless it satisfies stable_v1_two_of_three.",
      step: 2, parallel: false, model: "claude-opus-4-6", temperature: 0.1, max_output_tokens: 32000, timeout_minutes: 25,
      tools: ["Read", "Write", "Bash"],
      input_files: ["2-data/quantitative_data.json", "1-universe/metric_taxonomy.json"],
      output_files: ["3-analysis/standardized_data.json", "3-analysis/correlations.json", "3-analysis/statistical_methodology.md", "3-analysis/statistics_metadata.json", "3-analysis/driver_ranking.json"],
      retry_strategy: "same_prompt",
    },
    {
      id: "convergence-analyst", name: "Convergence Analyst",
      role: "Merges quantitative and qualitative tracks — selects final 9-12 peer set for deep-dives",
      instructions: "Select the final deep-dive set using PAX-aware convergence rules. Score firms on quantitative relevance, qualitative instructiveness, source coverage, and archetype value for PAX. Require explicit peer archetypes (north_star_peer, near_peer, adjacent_peer, anti_pattern_peer), matched-sample logic, and transferability notes. Mega-cap firms may not dominate selection mechanically; disclose when a firm informs inspiration but not near-term transferability. If a firm lacks valuation multiples, it may still be included qualitatively, but its rationale must clearly say it did not participate in the correlation evidence.",
      step: 2, parallel: false, model: "claude-opus-4-6", temperature: 0.2, max_output_tokens: 12000, timeout_minutes: 10,
      tools: ["Read", "Write"],
      input_files: ["3-analysis/driver_ranking.json", "2-data/strategic_actions.json", "1-universe/source_catalog.json"],
      output_files: ["3-analysis/final_peer_set.json"],
      retry_strategy: "same_prompt",
    },
    {
      id: "platform-analyst", name: "Platform Profiler",
      role: "Produces platform-level deep-dives — identity, strategy, actions, driver performance, value narrative, transferable insights",
      instructions: "For each firm in the final set, produce a platform profile that remains peer-evidence-first but is transferability-aware. Required sections: identity and scale, archetype assignment, strategic agenda, key actions with operational prerequisites, driver performance using the current stable-driver rule, value-creation narrative with hedged language where needed, technology as enabler of value drivers (for each firm's documented tech investments, trace the specific causal chain: what system/capability was built → what operational change it produced → which ranked driver it plausibly moved. Do not list generic labels like 'digital transformation' — name the actual capability and the actual metric. The best alt-asset managers are doing things with technology far beyond basic automation; discover what those are from the evidence. Use hedged language for all causal claims), and transferability signals documenting what is informative, what is structurally non-transferable, what is inspiration only, and what is a warning for PAX. Keep self-contained and do not turn the profile into a PAX recommendation.",
      step: 3, parallel: true, model: "claude-opus-4-6", temperature: 0.3, max_output_tokens: 32000, timeout_minutes: 20,
      tools: ["WebSearch", "Read", "Write", "Agent"],
      input_files: ["3-analysis/final_peer_set.json", "3-analysis/driver_ranking.json", "2-data/strategy_profiles.json", "2-data/strategic_actions.json"],
      output_files: ["4-deep-dives/platform_profiles.json"],
      retry_strategy: "simplified_prompt",
    },
    {
      id: "vertical-analyst", name: "Sector Specialist",
      role: "Conducts asset-class deep-dives across 5 verticals with reference firms",
      instructions: "Deep-dive the alt-manager verticals through strategy sub-types, not monolithic asset classes. Use docs/pax-peer-strategy-ontology.md as the minimum decomposition grid and docs/pax-peer-assessment-framework.md as the business framing for what the deep-dive should explain. `asset_class_analysis.json` must be a root object `{ \"strategy_subtype_analyses\": [...] }` where every entry conforms to the repository contract: `vertical`, `strategy_sub_type`, `thematic_focus`, `economic_model`, `value_creation_mechanics`, `fee_model`, `operating_model`, `tech_data_reporting_requirements`, `scaling_constraints`, `margin_sensitivities`, and `pax_transferability_barriers`. Do not emit legacy `verticals` wrappers, best-in-class profile trees, or metadata-only summaries in place of the subtype analysis list. For each vertical, segment by strategy_sub_type, thematic_focus, and economic_model, then map the combinations of business-model choices that appear associated with KPI outcomes. Do not collapse the analysis below the ontology baseline without explicit disclosure. Document value-creation mechanics, fee model, operating model, tech/data/reporting requirements, scaling constraints, margin sensitivities, and transferability barriers for PAX. Ground all claims in specific peer actions and keep credit, PE, infrastructure, real estate, and solutions broken into the sub-types that actually matter for transferability.",
      step: 3, parallel: true, model: "claude-opus-4-6", temperature: 0.3, max_output_tokens: 48000, timeout_minutes: 30,
      tools: ["WebSearch", "Read", "Write"],
      input_files: ["3-analysis/driver_ranking.json", "2-data/strategic_actions.json", "docs/pax-peer-assessment-framework.md", "docs/pax-peer-strategy-ontology.md"],
      output_files: ["4-deep-dives/asset_class_analysis.json"],
      retry_strategy: "simplified_prompt",
    },
    {
      id: "playbook-synthesizer", name: "Insight Synthesizer",
      role: "Builds the PAX-first interpretation layer — value principles, platform playbook, and asset-class playbooks",
      instructions: "Sequential outputs: (1) Value Principles — for each headline driver, state the exact statistical status using the repository contract, disclose mechanical overlap and confounding where relevant, and add PAX relevance plus driver decomposition logic. Respect docs/pax-peer-assessment-framework.md as the business brief: keep the synthesis useful for both platform and BU readers, and preserve the distinction between reinforce current strategies, bring additional angles and opportunities, and suggest new initiatives. (2) Platform Playbook — emit a root object `{ \"driver_playbooks\": [...] }` and no top-level metadata wrapper. Each driver block must contain `driver_id`, `plays`, and `anti_patterns`. Each PLAY-* or ANTI-* entry must use only the contract fields `Play_ID` or `Anti_ID`, `What_Was_Done`, `Observed_Metric_Impact`, `Why_It_Worked`, `PAX_Relevance`, `Preconditions`, `Operational_And_Tech_Prerequisites`, `Execution_Burden`, `Time_To_Build`, `Margin_Risk`, `Failure_Modes_And_Margin_Destroyers`, `Transferability_Constraints`, `Archetype_Relevance`, `Evidence_Strength`, and `Recommendation_For_PAX`; do not emit legacy snake_case fields or decorative metadata. After driver-organized plays, include an Emerging Themes section (THEME-NNN) for actions without ranked drivers — technology/AI minimum 1, maximum 5 themes, hedged language only. (3) Asset Class Playbooks — emit a root object `{ \"vertical_playbooks\": [...] }` with the same play-entry contract, organized by vertical and strategy sub-type using docs/pax-peer-strategy-ontology.md as the minimum decomposition baseline. Include per-vertical Emerging Themes where evidence exists. Do not call a driver stable unless stable_v1_two_of_three is satisfied. Every recommendation must explicitly state why it matters for PAX, what would have to be true, why it may fail, and whether it is near_term_feasible, medium_term_feasible, or aspirational.",
      step: 4, parallel: false, model: "claude-opus-4-6", temperature: 0.3, max_output_tokens: 32000, timeout_minutes: 20,
      tools: ["Read", "Write", "Bash"],
      input_files: ["company_context.json", "docs/pax-peer-assessment-framework.md", "docs/pax-peer-strategy-ontology.md", "3-analysis/driver_ranking.json", "3-analysis/final_peer_set.json", "3-analysis/statistical_methodology.md", "3-analysis/statistics_metadata.json", "4-deep-dives/platform_profiles.json", "4-deep-dives/asset_class_analysis.json"],
      output_files: ["5-playbook/value_principles.md", "5-playbook/platform_playbook.json", "5-playbook/asset_class_playbooks.json"],
      retry_strategy: "same_prompt",
    },
    {
      id: "report-builder", name: "Report Composer",
      role: "Generates the default final output: a PAX decision memo with embedded peer evidence",
      instructions: "Produce a single self-contained HTML report and a report_metadata.json file. The default report mode is pax_decision_memo, not a neutral menu. Align the narrative to docs/pax-peer-assessment-framework.md: start from peer prioritization and deep-dives, then convert that evidence into lessons learned and opportunities for PAX. Required sections: (1) decision summary for PAX, (2) statistical governance box, (3) what the peer evidence says, (4) what is actually transferable to PAX, (5) ranked strategic implications for Patria, (6) driver decomposition bridges for FEAUM, FRE Margin, and EPS, (7) archetype-specific lessons, (8) execution and margin-risk register, (9) governance cascade, and (10) appendix with methodology and limitations. Make the final synthesis useful for both platform and BU readers, and preserve the buckets reinforce current strategies, bring additional angles and opportunities, and suggest new initiatives where they help readability. The report must consume audit_cp3_playbook.json and preserve all hedging requirements for inferred claims. It may not upgrade unsupported or directional evidence into stable conclusions. If target_company_lens.json exists, incorporate its Strategic Guidance as a dedicated chapter. Styling remains institutional and light-theme.",
      step: 4, parallel: true, model: "claude-opus-4-6", temperature: 0.2, max_output_tokens: 32000, timeout_minutes: 15,
      tools: ["Read", "Write", "Bash"],
      input_files: ["docs/pax-peer-assessment-framework.md", "docs/pax-peer-strategy-ontology.md", "5-playbook/value_principles.md", "5-playbook/platform_playbook.json", "5-playbook/asset_class_playbooks.json", "4-deep-dives/platform_profiles.json", "3-analysis/statistical_methodology.md", "3-analysis/statistics_metadata.json", "3-analysis/driver_ranking.json", "5-playbook/audit_cp3_playbook.json"],
      output_files: ["5-playbook/report_metadata.json", "5-playbook/final_report.html"],
      retry_strategy: "same_prompt",
    },
    {
      id: "target-lens", name: "Target Company Lens",
      role: "Produces the PAX decision layer — ranked implications, feasibility scoring, and governance-ready guidance",
      instructions: "For every PLAY-* and ANTI-* entry, create the formal PAX decision layer. `target_company_lens.json` must conform exactly to the repository contract: top-level keys are `target_company`, `target_ticker`, `ranked_recommendations`, `decision_risks`, and `governance_cascade`. Do not emit legacy `metadata`, `play_assessments`, or `strategic_guidance` wrappers. Use docs/pax-peer-assessment-framework.md to keep the output useful at two levels: platform / PHL guidance and BU / asset-class guidance. Score each item on scale fit, geography fit, client/distribution fit, balance-sheet fit, regulatory fit, operating-model fit, tech readiness, data/reporting readiness, time-to-build, capital intensity, margin-risk, and execution complexity. Then produce ranked recommendations that keep two layers separate: (1) the peer-derived `strategic_principle` about what seems to create value and (2) the `implementation_pathway` by which PAX could pursue it. Every recommendation object must state `play_id`, `priority_rank`, `applicability`, `strategic_principle`, `rationale`, `adaptation_notes`, `why_this_matters_for_pax`, `what_must_be_true`, `why_this_may_fail_for_pax`, `implementation_pathway`, and `feasibility_horizon`. Where appropriate, classify implications into reinforce current strategies, bring additional angles and opportunities, and suggest new initiatives. Consume audit_cp3_playbook.json and never restate inferred operational claims as hard facts. Use peer archetypes to penalize mechanically non-transferable mega-cap lessons.",
      step: 4, parallel: true, model: "claude-opus-4-6", temperature: 0.3, max_output_tokens: 32000, timeout_minutes: 20,
      tools: ["Read", "Write", "Bash"],
      input_files: ["company_context.json", "docs/pax-peer-assessment-framework.md", "docs/pax-peer-strategy-ontology.md", "3-analysis/final_peer_set.json", "3-analysis/driver_ranking.json", "3-analysis/statistics_metadata.json", "5-playbook/platform_playbook.json", "5-playbook/asset_class_playbooks.json", "5-playbook/audit_cp3_playbook.json", "4-deep-dives/platform_profiles.json"],
      output_files: ["5-playbook/target_company_lens.json"],
      retry_strategy: "same_prompt",
    },
    {
      id: "claim-auditor-cp1", name: "Fact Checker (CP-1)",
      role: "Post-data verification — checks quantitative data claims against source evidence. Blocks invalid premises and misleading context.",
      instructions: "Checkpoint CP-1: Post-Data Fact Check. Read 2-data/quantitative_data.json and cross-reference against 1-universe/source_catalog.json and tier files. Audit focus: invalid_premises (data points without source support), misleading_context (values taken out of context or misattributed). Consulting source enforcement: verify that no quantitative tier data cites PS-VD-9xx sources as the primary basis for any firm-specific metric value. Enumerate every factual claim exhaustively; do not sample. For each claim produce a structured verdict (grounded/inferred/ungrounded/fabricated). Hard-block on ungrounded or fabricated data points.",
      step: -1, parallel: false, model: "claude-opus-4-6", temperature: 0.0, max_output_tokens: 16000, timeout_minutes: 10,
      tools: ["Read", "Grep", "Glob"],
      input_files: ["2-data/quantitative_data.json", "2-data/quantitative_tier1.json", "2-data/quantitative_tier2.json", "2-data/quantitative_tier3.json", "1-universe/source_catalog.json"],
      output_files: ["2-data/audit_cp1_data.json"],
      retry_strategy: "simplified_prompt",
    },
    {
      id: "claim-auditor-cp2", name: "Fact Checker (CP-2)",
      role: "Post-deep-dive verification — the CRITICAL checkpoint. All 4 audit dimensions active plus operational prerequisite evidence validation.",
      instructions: "Checkpoint CP-2: Post-Deep-Dive Fact Check. Read 4-deep-dives/platform_profiles.json and 4-deep-dives/asset_class_analysis.json. Cross-reference against 3-analysis/driver_ranking.json, 2-data/strategic_actions.json, 2-data/strategy_profiles.json. All 4 audit dimensions active: invalid_premises, misleading_context, sycophantic_fabrication, confidence_miscalibration. Additional checks: operational_prerequisite_evidence (block any prerequisite based solely on job postings or vendor PRs), consulting_source_enforcement (block firm-specific claims solely backed by PS-VD-9xx sources). Verify technology-as-enabler claims use hedged language (appears to, coincided with, may have enabled). Enumerate every claim exhaustively. Hard-block on ungrounded, fabricated, or unsupported-but-stated-as-fact claims.",
      step: -1, parallel: false, model: "claude-opus-4-6", temperature: 0.0, max_output_tokens: 32000, timeout_minutes: 15,
      tools: ["Read", "Grep", "Glob"],
      input_files: ["4-deep-dives/platform_profiles.json", "4-deep-dives/asset_class_analysis.json", "3-analysis/driver_ranking.json", "2-data/strategic_actions.json", "2-data/strategy_profiles.json"],
      output_files: ["4-deep-dives/audit_cp2_deep_dives.json"],
      retry_strategy: "simplified_prompt",
    },
    {
      id: "claim-auditor-cp3", name: "Fact Checker (CP-3)",
      role: "Post-playbook verification — validates play completeness, emerging themes hedging, and evidence strength before report generation.",
      instructions: "Checkpoint CP-3: Post-Playbook Fact Check. Read 5-playbook/platform_playbook.json and 5-playbook/asset_class_playbooks.json. Cross-reference against 4-deep-dives/platform_profiles.json, 4-deep-dives/asset_class_analysis.json, 3-analysis/driver_ranking.json. Audit focus: sycophantic_fabrication, confidence_miscalibration, mandatory_field_completeness. Block any PLAY-NNN or ANTI-NNN lacking Operational_And_Tech_Prerequisites, Failure_Modes_And_Margin_Destroyers, or Evidence_Strength. Block any THEME-NNN lacking theme_name, actions, firms_involved, What_Is_Observed, Why_It_May_Matter, Coverage_Gap, Evidence_Strength, or source_citations. Block any THEME-NNN that asserts causal impact on valuation instead of using hedged language. Consulting source enforcement: verify no PLAY-NNN uses PS-VD-9xx as sole evidence for a firm-specific claim. For PAX runs, use docs/pax-peer-assessment-framework.md and docs/pax-peer-strategy-ontology.md as spec references to catch omission of required hypothesis families.",
      step: -1, parallel: false, model: "claude-opus-4-6", temperature: 0.0, max_output_tokens: 32000, timeout_minutes: 15,
      tools: ["Read", "Grep", "Glob"],
      input_files: ["5-playbook/platform_playbook.json", "5-playbook/asset_class_playbooks.json", "4-deep-dives/platform_profiles.json", "4-deep-dives/asset_class_analysis.json", "3-analysis/driver_ranking.json", "docs/pax-peer-assessment-framework.md", "docs/pax-peer-strategy-ontology.md"],
      output_files: ["5-playbook/audit_cp3_playbook.json"],
      retry_strategy: "simplified_prompt",
    },
    {
      id: "methodology-reviewer", name: "Methodology Reviewer",
      role: "Reviews statistical methodology, data coverage, metric selection, and peer selection logic",
      instructions: "Read the authoritative PAX-first methodology plus all pipeline outputs. Produce a repository drift audit focused on spec drift between methodology, agent behavior, schemas, metadata, and outputs. Identify gaps in statistical governance, data coverage, metric selection, operational-feasibility capture, peer archetyping, transferability logic, and report-contract compliance. For each finding provide file/location, what the methodology requires, what the implementation or output does, why it matters, severity, and the exact fix.",
      step: 5, parallel: true, model: "claude-opus-4-6", temperature: 0.3, max_output_tokens: 16000, timeout_minutes: 15,
      tools: ["Read", "Write", "Glob"],
      input_files: ["docs/pax-first-valuation-driver-methodology.md", "3-analysis/statistical_methodology.md", "3-analysis/statistics_metadata.json", "3-analysis/correlations.json", "3-analysis/driver_ranking.json", "3-analysis/final_peer_set.json", "5-playbook/report_metadata.json", "5-playbook/target_company_lens.json"],
      output_files: ["6-review/methodology_review.md"],
      retry_strategy: "same_prompt",
    },
    {
      id: "results-reviewer", name: "Results Reviewer",
      role: "Reviews final report for missed insights, weak conclusions, and untapped analytical angles",
      instructions: "Read the final PAX decision memo and all supporting data. Identify missed insights, weak or overconfident conclusions, transferability mistakes, execution-realism gaps, margin-risk blind spots, and any place where north-star peers overwhelm PAX-relevant interpretation. Produce a structured improvement report that focuses on whether the output is materially useful for Patria rather than generically interesting.",
      step: 5, parallel: true, model: "claude-opus-4-6", temperature: 0.4, max_output_tokens: 16000, timeout_minutes: 15,
      tools: ["Read", "Write"],
      input_files: ["5-playbook/final_report.html", "5-playbook/report_metadata.json", "5-playbook/target_company_lens.json", "3-analysis/correlations.json", "4-deep-dives/platform_profiles.json"],
      output_files: ["6-review/results_review.md"],
      retry_strategy: "same_prompt",
    },
  ],
  steps: [
    { index: 0, name: "Map the Industry", folder: "1-universe", agents: ["universe-scout", "source-mapper", "metric-architect"], gate_criteria: ["Universe >= 20 firms", "Metric taxonomy complete and includes operational scalability family", "Preliminary peer archetypes assigned", "Source coverage >= 3 per qualitative peer"] },
    { index: 1, name: "Gather Data", folder: "2-data", agents: ["data-collector-t1", "data-collector-t2", "data-collector-t3", "strategy-extractor"], gate_criteria: ["Metric coverage >= 60% for >= 80% of firms", "Valuation-multiple gaps disclosed explicitly", "Operational prerequisites carry evidence_class and stated_or_inferred tags", ">= 2 actions per qualitative peer"] },
    { index: 2, name: "Find What Drives Value", folder: "3-analysis", agents: ["statistical-analyst", "convergence-analyst"], gate_criteria: ["statistics_metadata.json written", "Stable-driver claims follow stable_v1_two_of_three", "Matched-sample and archetype views documented", "Final peer set is 9-12 firms with archetype rationale"] },
    { index: 3, name: "Deep-Dive Peers", folder: "4-deep-dives", agents: ["platform-analyst", "vertical-analyst"], gate_criteria: ["All final set firms profiled", "Verticals segmented by strategy sub-type", "Insights cite specific source IDs", "Transferability barriers documented without turning peer evidence into advice"] },
    { index: 4, name: "Build the Playbook", folder: "5-playbook", agents: ["playbook-synthesizer", "report-builder", "target-lens"], gate_criteria: ["PAX-first report contract satisfied", "report_metadata.json agrees with statistics_metadata.json", "Every play includes PAX relevance and execution realism fields", "Target company lens produced", "Anti-patterns identify concrete destruction mechanisms"] },
    { index: 5, name: "Review Analysis", folder: "6-review", agents: ["methodology-reviewer", "results-reviewer"], gate_criteria: ["Both review reports produced", "Findings categorized by severity"] },
  ],
  command: {
    default_sector: "Alternative Asset Management",
    auto_mode: false,
    evidence_mode: "legacy",
    max_retries: 2,
    tier_size: 9,
    base_run: null,
    tone_profile: DEFAULT_TONE_PROFILE,
  },
};

const STEP_COLORS = [
  "text-cyan-700 bg-cyan-50 border border-cyan-200",
  "text-blue-700 bg-blue-50 border border-blue-200",
  "text-violet-700 bg-violet-50 border border-violet-200",
  "text-amber-700 bg-amber-50 border border-amber-200",
  "text-emerald-700 bg-emerald-50 border border-emerald-200",
  "text-rose-700 bg-rose-50 border border-rose-200",
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
  const [configSource, setConfigSource] = useState<"default" | "file">("default");

  useEffect(() => {
    invoke<string>("get_project_root").then((root) => {
      invoke<string>("read_output_file", { path: `${root}/.claude/agent_config.json` })
        .then((content) => {
          const parsed = JSON.parse(content) as Partial<AgentConfig>;
          setConfig({
            ...DEFAULT_CONFIG,
            ...parsed,
            command: { ...DEFAULT_CONFIG.command, ...(parsed.command ?? {}) },
            agents: parsed.agents ?? DEFAULT_CONFIG.agents,
            steps: parsed.steps ?? DEFAULT_CONFIG.steps,
          });
          setConfigSource("file");
        })
        .catch(() => { setConfigSource("default"); });
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
      setConfigSource("file");
    } catch (err) {
      console.error("Failed to save config:", err);
    }
  };

  const selected = config.agents.find((a) => a.id === selectedAgent);

  return (
    <div className="h-full flex flex-col">
      {/* Tab bar */}
      <div className="flex items-center justify-between px-5 py-2 border-b border-gray-200 shrink-0">
        <div className="flex items-center gap-1">
          {(["pipeline", "command"] as const).map((t) => (
            <button key={t} onClick={() => setTab(t)}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${tab === t ? "bg-gray-100 text-gray-900" : "text-gray-400 hover:text-gray-700"}`}
            >
              {t === "pipeline" ? "Pipeline & Agents" : "Command Config"}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-[9px] px-2 py-0.5 rounded font-mono ${configSource === "file" ? "bg-emerald-50 text-emerald-600 border border-emerald-200" : "bg-gray-50 text-gray-400 border border-gray-200"}`}
            title={configSource === "file" ? "Pipeline reads this config from .claude/agent_config.json" : "Using defaults — save to connect to pipeline"}
          >
            {configSource === "file" ? "synced with pipeline" : "defaults (not saved)"}
          </span>
          <button onClick={() => { setConfig(DEFAULT_CONFIG); setDirty(true); setConfigSource("default"); }}
            className="px-3 py-1.5 rounded-md text-xs text-gray-400 hover:text-gray-700 transition-colors">
            Reset
          </button>
          <button onClick={handleSave} disabled={!dirty}
            className={`px-4 py-1.5 rounded-md text-xs font-medium transition-colors ${dirty ? "bg-blue-50 text-[#0068ff] border border-blue-200 hover:bg-blue-100" : "text-gray-400 cursor-default"}`}>
            {dirty ? "Save Config" : "Saved"}
          </button>
        </div>
      </div>

      {tab === "pipeline" && (
        <div className="flex-1 flex min-h-0">
          {/* Left: Pipeline flow */}
          <div className="w-80 border-r border-gray-200 overflow-y-auto p-4 space-y-3 shrink-0">
            <h3 className="text-xs text-gray-400 mb-3">Pipeline Steps</h3>
            {config.steps.map((step) => {
              const stepAgents = config.agents.filter((a) => a.step === step.index);
              const color = STEP_COLORS[step.index];
              return (
                <div key={step.index} className="space-y-1">
                  <div className={`px-3 py-2 rounded-md ${color}`}>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-mono opacity-60">S{step.index + 1}</span>
                      <span className="text-xs font-medium">{step.name}</span>
                      {stepAgents.some((a) => a.parallel) && (
                        <span className="text-[9px] px-1.5 py-0.5 rounded bg-gray-100 text-gray-500 ml-auto">parallel</span>
                      )}
                    </div>
                    <div className="text-[10px] opacity-50 mt-0.5 font-mono">→ {step.folder}/</div>
                  </div>
                  <div className="pl-4 space-y-0.5">
                    {stepAgents.map((agent) => (
                      <button key={agent.id} onClick={() => setSelectedAgent(agent.id)}
                        className={`w-full text-left px-3 py-1.5 rounded text-xs transition-colors flex items-center gap-2 ${selectedAgent === agent.id ? "bg-gray-100 text-gray-900" : "text-gray-500 hover:bg-gray-50 hover:text-gray-700"}`}
                      >
                        <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${agent.model.includes("opus") ? "bg-violet-400" : agent.model.includes("haiku") ? "bg-green-400" : "bg-blue-400"}`} />
                        <span className="truncate">{agent.name}</span>
                        {agent.parallel && <span className="text-[8px] text-gray-400 ml-auto shrink-0">∥</span>}
                      </button>
                    ))}
                  </div>
                  {/* Checkpoint indicators */}
                  {INITIAL_CHECKPOINTS.filter((cp) => cp.afterStep === step.index).map((cp) => (
                    <button key={cp.id} onClick={() => {
                        const cpAgentMap: Record<string, string> = { "CP-1": "claim-auditor-cp1", "CP-2": "claim-auditor-cp2", "CP-3": "claim-auditor-cp3" };
                        setSelectedAgent(cpAgentMap[cp.id] ?? "claim-auditor-cp1");
                      }}
                      className={`ml-4 my-1 w-[calc(100%-1rem)] text-left flex items-center gap-2 px-3 py-1 rounded border border-dashed transition-colors text-[10px] ${(() => { const cpAgentMap: Record<string, string> = { "CP-1": "claim-auditor-cp1", "CP-2": "claim-auditor-cp2", "CP-3": "claim-auditor-cp3" }; return selectedAgent === cpAgentMap[cp.id]; })() ? "border-emerald-400 bg-emerald-100 text-emerald-700" : "border-emerald-200 bg-emerald-50 text-emerald-600 hover:bg-emerald-100"}`}
                    >
                      <span>&#x1F6E1;</span>
                      <span className="font-mono">{cp.id}</span>
                      <span className="text-gray-400">{cp.name}</span>
                      <span className="ml-auto text-gray-400 text-[9px]">Opus</span>
                    </button>
                  ))}
                  {step.index < config.steps.length - 1 && (
                    <div className="flex justify-center py-1"><span className="text-gray-300 text-xs">↓</span></div>
                  )}
                </div>
              );
            })}
            {/* Verification agents (step=-1) */}
            {(() => {
              const verificationAgents = config.agents.filter((a) => a.step === -1);
              if (verificationAgents.length === 0) return null;
              return (
                <div className="space-y-1 pt-2 border-t border-gray-200">
                  <div className="px-3 py-2 rounded-md border text-emerald-600 bg-emerald-100 border-emerald-200">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-mono opacity-60">&#x1F6E1;</span>
                      <span className="text-xs font-medium">Claim Verification</span>
                    </div>
                    <div className="text-[10px] opacity-50 mt-0.5 font-mono">{INITIAL_CHECKPOINTS.map((cp) => cp.id).join(", ")}</div>
                  </div>
                  <div className="pl-4 space-y-0.5">
                    {verificationAgents.map((agent) => (
                      <button key={agent.id} onClick={() => setSelectedAgent(agent.id)}
                        className={`w-full text-left px-3 py-1.5 rounded text-xs transition-colors flex items-center gap-2 ${selectedAgent === agent.id ? "bg-gray-100 text-gray-900" : "text-gray-500 hover:bg-gray-50 hover:text-gray-700"}`}
                      >
                        <span className="w-1.5 h-1.5 rounded-full shrink-0 bg-violet-400" />
                        <span className="truncate">{agent.name}</span>
                      </button>
                    ))}
                  </div>
                </div>
              );
            })()}
            {/* Model legend */}
            <div className="pt-4 border-t border-gray-200 space-y-1.5">
              <h4 className="text-[10px] text-gray-500">Model Legend</h4>
              {MODELS.map((m) => (
                <div key={m.id} className="flex items-center gap-2 text-[10px]">
                  <span className={`w-1.5 h-1.5 rounded-full ${m.id.includes("opus") ? "bg-violet-400" : m.id.includes("haiku") ? "bg-green-400" : "bg-blue-400"}`} />
                  <span className="text-gray-500">{m.label}</span>
                  <span className="text-gray-400">— {m.desc}</span>
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
                    <h2 className="text-lg font-semibold text-gray-900">{selected.name}</h2>
                    <span className={`text-[10px] px-2 py-0.5 rounded ${selected.step === -1 ? "text-emerald-600 bg-emerald-100 border border-emerald-200" : STEP_COLORS[selected.step]}`}>
                      {selected.step === -1 ? "Claim Verification" : config.steps[selected.step]?.name}
                    </span>
                  </div>
                  <p className="text-xs text-gray-400 font-mono">{selected.id}</p>
                </div>

                {/* Name + Role */}
                <div className="grid grid-cols-[1fr_2fr] gap-4">
                  <div>
                    <label htmlFor="agent-name" className="block text-[10px] text-gray-500 mb-1.5">Display Name</label>
                    <input id="agent-name" type="text" value={selected.name}
                      onChange={(e) => updateAgent(selected.id, { name: e.target.value })}
                      className="w-full px-3 py-2 rounded-md bg-gray-50 border border-gray-200 text-sm text-gray-800 focus:ring-2 focus:ring-[#0068ff]/40 focus:border-[#0068ff] focus:outline-none" />
                  </div>
                  <div>
                    <label htmlFor="agent-role" className="block text-[10px] text-gray-500 mb-1.5">Role Summary</label>
                    <input id="agent-role" type="text" value={selected.role}
                      onChange={(e) => updateAgent(selected.id, { role: e.target.value })}
                      className="w-full px-3 py-2 rounded-md bg-gray-50 border border-gray-200 text-sm text-gray-800 focus:ring-2 focus:ring-[#0068ff]/40 focus:border-[#0068ff] focus:outline-none" />
                  </div>
                </div>

                {/* Instructions */}
                <div>
                  <label htmlFor="agent-instructions" className="block text-[10px] text-gray-500 mb-1.5">Agent Instructions</label>
                  <textarea id="agent-instructions" value={selected.instructions}
                    onChange={(e) => updateAgent(selected.id, { instructions: e.target.value })}
                    rows={5}
                    className="w-full px-3 py-2 rounded-md bg-gray-50 border border-gray-200 text-xs text-gray-700 focus:ring-2 focus:ring-[#0068ff]/40 focus:border-[#0068ff] focus:outline-none resize-y font-mono leading-relaxed" />
                </div>

                {/* Model + Temperature + Tokens + Timeout */}
                <div className="grid grid-cols-4 gap-3">
                  <div>
                    <label htmlFor="agent-model" className="block text-[10px] text-gray-500 mb-1.5">Model</label>
                    <select id="agent-model" value={selected.model}
                      onChange={(e) => updateAgent(selected.id, { model: e.target.value })}
                      className="w-full px-2 py-2 rounded-md bg-gray-50 border border-gray-200 text-xs text-gray-800 focus:ring-2 focus:ring-[#0068ff]/40 focus:border-[#0068ff] focus:outline-none appearance-none">
                      {MODELS.map((m) => (
                        <option key={m.id} value={m.id}>{m.label}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label htmlFor="agent-temp" className="block text-[10px] text-gray-500 mb-1.5">Temperature</label>
                    <input id="agent-temp" type="number" value={selected.temperature} step={0.1} min={0} max={1}
                      onChange={(e) => updateAgent(selected.id, { temperature: parseFloat(e.target.value) || 0 })}
                      className="w-full px-2 py-2 rounded-md bg-gray-50 border border-gray-200 text-xs text-gray-800 focus:ring-2 focus:ring-[#0068ff]/40 focus:border-[#0068ff] focus:outline-none" />
                  </div>
                  <div>
                    <label htmlFor="agent-tokens" className="block text-[10px] text-gray-500 mb-1.5">Max Tokens</label>
                    <input id="agent-tokens" type="number" value={selected.max_output_tokens} step={4000} min={4000} max={64000}
                      onChange={(e) => updateAgent(selected.id, { max_output_tokens: parseInt(e.target.value) || 16000 })}
                      className="w-full px-2 py-2 rounded-md bg-gray-50 border border-gray-200 text-xs text-gray-800 focus:ring-2 focus:ring-[#0068ff]/40 focus:border-[#0068ff] focus:outline-none" />
                  </div>
                  <div>
                    <label htmlFor="agent-timeout" className="block text-[10px] text-gray-500 mb-1.5">Timeout (min)</label>
                    <input id="agent-timeout" type="number" value={selected.timeout_minutes} min={5} max={60}
                      onChange={(e) => updateAgent(selected.id, { timeout_minutes: parseInt(e.target.value) || 10 })}
                      className="w-full px-2 py-2 rounded-md bg-gray-50 border border-gray-200 text-xs text-gray-800 focus:ring-2 focus:ring-[#0068ff]/40 focus:border-[#0068ff] focus:outline-none" />
                  </div>
                </div>

                {/* Tools */}
                <div>
                  <label className="block text-[10px] text-gray-500 mb-2">Available Tools</label>
                  <div className="flex flex-wrap gap-1.5">
                    {AVAILABLE_TOOLS.map((tool) => {
                      const active = selected.tools.includes(tool);
                      return (
                        <button key={tool} onClick={() => toggleTool(selected.id, tool)}
                          className={`px-2.5 py-1 rounded text-xs font-mono transition-colors ${active ? "bg-blue-50 text-[#0068ff] border border-blue-200" : "bg-gray-50 text-gray-400 border border-gray-200 hover:text-gray-500"}`}>
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
                      <span id="parallel-label" className="text-xs text-gray-700">Parallel</span>
                      <p className="text-[10px] text-gray-500">Runs alongside other agents</p>
                    </div>
                    <button role="switch" aria-checked={selected.parallel} aria-labelledby="parallel-label"
                      onClick={() => updateAgent(selected.id, { parallel: !selected.parallel })}
                      className="p-3 -m-3 cursor-pointer">
                      <div className={`w-9 h-5 rounded-full transition-colors relative ${selected.parallel ? "bg-[#0068ff]" : "bg-gray-300"}`}>
                        <div className={`absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform ${selected.parallel ? "translate-x-4" : "translate-x-0.5"}`} />
                      </div>
                    </button>
                  </div>
                  <div>
                    <label htmlFor="agent-retry" className="block text-[10px] text-gray-500 mb-1.5">On Timeout</label>
                    <select id="agent-retry" value={selected.retry_strategy}
                      onChange={(e) => updateAgent(selected.id, { retry_strategy: e.target.value as AgentDef["retry_strategy"] })}
                      className="w-full px-2 py-2 rounded-md bg-gray-50 border border-gray-200 text-xs text-gray-800 focus:ring-2 focus:ring-[#0068ff]/40 focus:border-[#0068ff] focus:outline-none appearance-none">
                      <option value="simplified_prompt">Re-dispatch with simpler prompt</option>
                      <option value="same_prompt">Retry same prompt</option>
                      <option value="skip">Skip agent</option>
                    </select>
                  </div>
                </div>

                {/* I/O Files */}
                <div className="grid grid-cols-2 gap-4 pt-2 border-t border-gray-200">
                  <div>
                    <label className="block text-[10px] text-gray-500 mb-2">Reads From</label>
                    <div className="space-y-1">
                      {selected.input_files.map((f, i) => (
                        <div key={i} className="flex items-center gap-2">
                          <span className="text-[10px] text-gray-500">←</span>
                          <span className="text-xs font-mono text-gray-500">{f}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div>
                    <label className="block text-[10px] text-gray-500 mb-2">Writes To</label>
                    <div className="space-y-1">
                      {selected.output_files.map((f, i) => (
                        <div key={i} className="flex items-center gap-2">
                          <span className="text-[10px] text-[#0055d4]">→</span>
                          <span className="text-xs font-mono text-[#0068ff]/70">{f}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Quality Gate */}
                {selected.step !== -1 && config.steps[selected.step]?.gate_criteria.length > 0 && (
                  <div className="pt-2 border-t border-gray-200">
                    <label className="block text-[10px] text-gray-500 mb-2">Quality Gate — {config.steps[selected.step].name}</label>
                    <div className="space-y-1">
                      {config.steps[selected.step].gate_criteria.map((c, i) => (
                        <div key={i} className="flex items-center gap-2 text-xs text-gray-500">
                          <span className="text-amber-600/60">◆</span>
                          <span>{c}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="h-full flex items-center justify-center text-gray-400 text-sm">
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
              <h2 className="text-lg font-semibold text-gray-900 mb-1">Slash Command Configuration</h2>
              <p className="text-sm text-gray-400">
                Parameters for <code className="text-[#0068ff] bg-gray-50 px-1.5 py-0.5 rounded text-xs">/valuation-driver TICKER</code>
              </p>
            </div>

            <div className="space-y-5">
              <div>
                <label htmlFor="cmd-sector" className="block text-[10px] text-gray-500 mb-2">Default Sector</label>
                <select id="cmd-sector" value={config.command.default_sector}
                  onChange={(e) => updateCommand("default_sector", e.target.value)}
                  className="w-full px-3 py-2 rounded-md bg-gray-50 border border-gray-200 text-sm text-gray-800 focus:ring-2 focus:ring-[#0068ff]/40 focus:border-[#0068ff] focus:outline-none appearance-none">
                  {["Alternative Asset Management", "Banking & Financial Services", "Insurance", "Fintech", "Real Estate", "Technology", "Healthcare", "Energy", "Consumer", "Industrials"].map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>

              <div className="flex items-center justify-between py-2">
                <div>
                  <span id="cmd-auto-label" className="text-sm text-gray-700">Auto Mode</span>
                  <p className="text-xs text-gray-400">Quality gates validated automatically — no manual approval</p>
                </div>
                <button role="switch" aria-checked={config.command.auto_mode} aria-labelledby="cmd-auto-label"
                  onClick={() => updateCommand("auto_mode", !config.command.auto_mode)}
                  className="p-3 -m-3 cursor-pointer">
                  <div className={`w-10 h-5 rounded-full transition-colors relative ${config.command.auto_mode ? "bg-[#0068ff]" : "bg-gray-300"}`}>
                    <div className={`absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform ${config.command.auto_mode ? "translate-x-5" : "translate-x-0.5"}`} />
                  </div>
                </button>
              </div>

              <div>
                <label htmlFor="cmd-evidence-mode" className="block text-[10px] text-gray-500 mb-2">Evidence Mode</label>
                <p className="text-[10px] text-gray-500 mb-2">`incremental` reuses the canonical evidence store and only plans recrawls for gaps</p>
                <select id="cmd-evidence-mode" value={config.command.evidence_mode}
                  onChange={(e) => updateCommand("evidence_mode", e.target.value as "legacy" | "incremental")}
                  className="w-full px-3 py-2 rounded-md bg-gray-50 border border-gray-200 text-sm text-gray-800 focus:ring-2 focus:ring-[#0068ff]/40 focus:border-[#0068ff] focus:outline-none appearance-none">
                  <option value="legacy">legacy</option>
                  <option value="incremental">incremental</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="cmd-retries" className="block text-[10px] text-gray-500 mb-2">Max Retries per Agent</label>
                  <p className="text-[10px] text-gray-500 mb-2">How many times to retry a failed/timed-out agent</p>
                  <input id="cmd-retries" type="number" value={config.command.max_retries}
                    onChange={(e) => updateCommand("max_retries", parseInt(e.target.value) || 2)}
                    min={0} max={5}
                    className="w-full px-3 py-2 rounded-md bg-gray-50 border border-gray-200 text-sm text-gray-800 focus:ring-2 focus:ring-[#0068ff]/40 focus:border-[#0068ff] focus:outline-none" />
                </div>
                <div>
                  <label htmlFor="cmd-tier-size" className="block text-[10px] text-gray-500 mb-2">Firms per Data Tier</label>
                  <p className="text-[10px] text-gray-500 mb-2">Universe splits into ceil(N/{`{tier_size}`}) parallel collectors</p>
                  <input id="cmd-tier-size" type="number" value={config.command.tier_size}
                    onChange={(e) => updateCommand("tier_size", parseInt(e.target.value) || 9)}
                    min={3} max={15}
                    className="w-full px-3 py-2 rounded-md bg-gray-50 border border-gray-200 text-sm text-gray-800 focus:ring-2 focus:ring-[#0068ff]/40 focus:border-[#0068ff] focus:outline-none" />
                </div>
              </div>
              <div>
                <label htmlFor="cmd-base-run" className="block text-[10px] text-gray-500 mb-2">Base Run (Previous Date)</label>
                <p className="text-[10px] text-gray-500 mb-2">Previous run date for iterative refinement</p>
                <input id="cmd-base-run" type="text" value={config.command.base_run ?? ""}
                  onChange={(e) => updateCommand("base_run", e.target.value || null as unknown as string)}
                  placeholder="YYYY-MM-DD"
                  className="w-full px-3 py-2 rounded-md bg-gray-50 border border-gray-200 text-sm text-gray-800 placeholder-gray-300 focus:ring-2 focus:ring-[#0068ff]/40 focus:border-[#0068ff] focus:outline-none" />
              </div>

              {/* Tone Configuration */}
              <div className="space-y-4 pt-2 border-t border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <label className="text-[10px] text-gray-500">Tone Configuration</label>
                    {config.command.tone_profile.source === "extracted" ? (
                      <span className="text-[10px] px-2 py-0.5 rounded bg-blue-50 text-[#0068ff] border border-blue-200">
                        Extracted from {config.command.tone_profile.reference_files.length} file{config.command.tone_profile.reference_files.length !== 1 ? "s" : ""}
                      </span>
                    ) : (
                      <span className="text-[10px] px-2 py-0.5 rounded bg-gray-50 text-gray-400 border border-gray-200">
                        Default
                      </span>
                    )}
                  </div>
                  {config.command.tone_profile.source !== "default" && (
                    <button
                      onClick={() => updateCommand("tone_profile", DEFAULT_TONE_PROFILE)}
                      className="text-[10px] text-gray-500 hover:text-gray-700 transition-colors"
                    >
                      Reset to Default
                    </button>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label htmlFor="tone-formality" className="block text-[10px] text-gray-500 mb-1.5">Formality</label>
                    <select id="tone-formality"
                      value={config.command.tone_profile.formality}
                      onChange={(e) => updateToneProfile({ formality: e.target.value as ToneProfile["formality"] })}
                      className="w-full px-2 py-2 rounded-md bg-gray-50 border border-gray-200 text-xs text-gray-800 focus:ring-2 focus:ring-[#0068ff]/40 focus:border-[#0068ff] focus:outline-none appearance-none"
                    >
                      <option value="academic">academic</option>
                      <option value="professional">professional</option>
                      <option value="conversational">conversational</option>
                    </select>
                  </div>
                  <div>
                    <label htmlFor="tone-voice" className="block text-[10px] text-gray-500 mb-1.5">Voice</label>
                    <select id="tone-voice"
                      value={config.command.tone_profile.voice}
                      onChange={(e) => updateToneProfile({ voice: e.target.value as ToneProfile["voice"] })}
                      className="w-full px-2 py-2 rounded-md bg-gray-50 border border-gray-200 text-xs text-gray-800 focus:ring-2 focus:ring-[#0068ff]/40 focus:border-[#0068ff] focus:outline-none appearance-none"
                    >
                      <option value="active">active</option>
                      <option value="passive">passive</option>
                      <option value="mixed">mixed</option>
                    </select>
                  </div>
                  <div>
                    <label htmlFor="tone-sentence" className="block text-[10px] text-gray-500 mb-1.5">Sentence Style</label>
                    <select id="tone-sentence"
                      value={config.command.tone_profile.sentence_style}
                      onChange={(e) => updateToneProfile({ sentence_style: e.target.value as ToneProfile["sentence_style"] })}
                      className="w-full px-2 py-2 rounded-md bg-gray-50 border border-gray-200 text-xs text-gray-800 focus:ring-2 focus:ring-[#0068ff]/40 focus:border-[#0068ff] focus:outline-none appearance-none"
                    >
                      <option value="concise">concise</option>
                      <option value="elaborate">elaborate</option>
                      <option value="mixed">mixed</option>
                    </select>
                  </div>
                  <div>
                    <label htmlFor="tone-hedging" className="block text-[10px] text-gray-500 mb-1.5">Hedging</label>
                    <select id="tone-hedging"
                      value={config.command.tone_profile.hedging}
                      onChange={(e) => updateToneProfile({ hedging: e.target.value as ToneProfile["hedging"] })}
                      className="w-full px-2 py-2 rounded-md bg-gray-50 border border-gray-200 text-xs text-gray-800 focus:ring-2 focus:ring-[#0068ff]/40 focus:border-[#0068ff] focus:outline-none appearance-none"
                    >
                      <option value="explicit">explicit</option>
                      <option value="moderate">moderate</option>
                      <option value="minimal">minimal</option>
                    </select>
                  </div>
                  <div>
                    <label htmlFor="tone-data" className="block text-[10px] text-gray-500 mb-1.5">Data Presentation</label>
                    <select id="tone-data"
                      value={config.command.tone_profile.data_presentation}
                      onChange={(e) => updateToneProfile({ data_presentation: e.target.value as ToneProfile["data_presentation"] })}
                      className="w-full px-2 py-2 rounded-md bg-gray-50 border border-gray-200 text-xs text-gray-800 focus:ring-2 focus:ring-[#0068ff]/40 focus:border-[#0068ff] focus:outline-none appearance-none"
                    >
                      <option value="tables-first">tables-first</option>
                      <option value="narrative-first">narrative-first</option>
                      <option value="integrated">integrated</option>
                    </select>
                  </div>
                  <div>
                    <label htmlFor="tone-terminology" className="block text-[10px] text-gray-500 mb-1.5">Terminology</label>
                    <select id="tone-terminology"
                      value={config.command.tone_profile.terminology}
                      onChange={(e) => updateToneProfile({ terminology: e.target.value as ToneProfile["terminology"] })}
                      className="w-full px-2 py-2 rounded-md bg-gray-50 border border-gray-200 text-xs text-gray-800 focus:ring-2 focus:ring-[#0068ff]/40 focus:border-[#0068ff] focus:outline-none appearance-none"
                    >
                      <option value="technical">technical</option>
                      <option value="accessible">accessible</option>
                      <option value="mixed">mixed</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label htmlFor="tone-nuances" className="block text-[10px] text-gray-500 mb-1.5">Nuances</label>
                  <textarea
                    id="tone-nuances"
                    value={config.command.tone_profile.nuances}
                    onChange={(e) => updateToneProfile({ nuances: e.target.value })}
                    rows={4}
                    className="w-full px-3 py-2 rounded-md bg-gray-50 border border-gray-200 text-xs text-gray-700 focus:ring-2 focus:ring-[#0068ff]/40 focus:border-[#0068ff] focus:outline-none resize-y font-mono leading-relaxed"
                  />
                </div>
              </div>
            </div>

            {/* Pipeline summary */}
            <div className="pt-6 border-t border-gray-200">
              <h3 className="text-xs text-gray-400 mb-3">Pipeline Summary</h3>
              <div className="grid grid-cols-4 gap-3 text-center">
                <div className="bg-gray-50 rounded-md px-3 py-4">
                  <div className="text-2xl font-bold text-gray-900">{config.agents.length}</div>
                  <div className="text-[10px] text-gray-500 mt-1">Agents</div>
                </div>
                <div className="bg-gray-50 rounded-md px-3 py-4">
                  <div className="text-2xl font-bold text-gray-900">{config.steps.length}</div>
                  <div className="text-[10px] text-gray-500 mt-1">Steps</div>
                </div>
                <div className="bg-gray-50 rounded-md px-3 py-4">
                  <div className="text-2xl font-bold text-violet-400">{config.agents.filter((a) => a.model.includes("opus")).length}</div>
                  <div className="text-[10px] text-gray-500 mt-1">Opus</div>
                </div>
                <div className="bg-gray-50 rounded-md px-3 py-4">
                  <div className="text-2xl font-bold text-blue-400">{config.agents.filter((a) => a.model.includes("sonnet")).length}</div>
                  <div className="text-[10px] text-gray-500 mt-1">Sonnet</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
