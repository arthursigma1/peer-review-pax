import type { PipelineAgent } from "../types/pipeline";

// Maps agent names from Claude CLI output to pipeline step indices and friendly names
const AGENT_MAP: Record<string, { stepIndex: number; friendlyName: string }> = {
  "universe-scout": { stepIndex: 0, friendlyName: "Industry Scanner" },
  "source-mapper": { stepIndex: 0, friendlyName: "Source Cataloger" },
  "metric-architect": { stepIndex: 0, friendlyName: "Metrics Designer" },
  "data-collector-t1": { stepIndex: 1, friendlyName: "Data Collector (Tier 1)" },
  "data-collector-t2": { stepIndex: 1, friendlyName: "Data Collector (Tier 2)" },
  "data-collector-t3": { stepIndex: 1, friendlyName: "Data Collector (Tier 3)" },
  "strategy-extractor": { stepIndex: 1, friendlyName: "Strategy Researcher" },
  "convergence-analyst": { stepIndex: 2, friendlyName: "Convergence Analyst" },
  "platform-analyst": { stepIndex: 3, friendlyName: "Platform Profiler" },
  "vertical-analyst": { stepIndex: 3, friendlyName: "Sector Specialist" },
  "playbook-synthesizer": { stepIndex: 4, friendlyName: "Insight Synthesizer" },
  "report-builder": { stepIndex: 4, friendlyName: "Report Composer" },
  "target-lens": { stepIndex: 4, friendlyName: "Target Company Lens" },
  "claim-auditor": { stepIndex: -1, friendlyName: "Fact Checker" },
  "methodology-reviewer": { stepIndex: 5, friendlyName: "Methodology Reviewer" },
  "results-reviewer": { stepIndex: 5, friendlyName: "Results Reviewer" },
};

// Step keywords mapped to step indices — used to detect step transitions
const STEP_TRIGGERS: { pattern: RegExp; stepIndex: number }[] = [
  { pattern: /Step 1.*Map the Industry|launching Step 1|Map the Industry.*3 parallel/i, stepIndex: 0 },
  { pattern: /Step 2.*Gather Data|launching Step 2/i, stepIndex: 1 },
  { pattern: /Step 3.*Find What Drives|launching Step 3/i, stepIndex: 2 },
  { pattern: /Step 4.*Deep-Dive|launching Step 4/i, stepIndex: 3 },
  { pattern: /Step 5.*Build the Playbook|launching Step 5/i, stepIndex: 4 },
  { pattern: /Step 6.*Review|launching Step 6|review agents/i, stepIndex: 5 },
];

export interface PtyParseEvent {
  type: "agent-spawned" | "agent-complete" | "step-started" | "step-complete" | "quality-gate" | "checkpoint";
  stepIndex: number;
  agent?: PipelineAgent;
  message?: string;
}

// Strip ANSI escape codes for pattern matching
function stripAnsi(text: string): string {
  return text.replace(/\x1b\[[0-9;]*[a-zA-Z]/g, "").replace(/\x1b\][^\x07]*\x07/g, "");
}

/**
 * Parse a chunk of PTY output text and return any detected events.
 *
 * @param raw         Raw PTY output chunk (may contain ANSI codes)
 * @param knownAgents Mutable Set tracking already-seen agents. Keys use the
 *                    composite format `${agentId}:${stepIndex}` so that an
 *                    agent reused across steps (e.g. metric-architect in step 0
 *                    and step 2) generates a fresh spawn event for each step.
 * @param currentStep The pipeline step index currently active, as tracked by
 *                    the caller. Pass -1 when unknown; the parser will fall
 *                    back to AGENT_MAP.stepIndex.
 */
export function parsePtyChunk(raw: string, knownAgents: Set<string>, currentStep: number = -1): PtyParseEvent[] {
  const text = stripAnsi(raw);
  const events: PtyParseEvent[] = [];

  // 1. Detect agent spawns via @agent-name in bottom bar or spawn messages
  const agentMentions = text.match(/@([\w-]+)/g);
  if (agentMentions) {
    for (const match of agentMentions) {
      const agentId = match.slice(1);
      if (!AGENT_MAP[agentId]) continue;

      const info = AGENT_MAP[agentId];
      // Use the caller-supplied step when known; fall back to the map default.
      const effectiveStep = currentStep >= 0 ? currentStep : info.stepIndex;
      const compositeKey = `${agentId}:${effectiveStep}`;

      if (!knownAgents.has(compositeKey)) {
        knownAgents.add(compositeKey);
        events.push({
          type: "agent-spawned",
          stepIndex: effectiveStep,
          agent: {
            id: agentId,
            name: agentId,
            friendlyName: info.friendlyName,
            status: "running",
            outputFile: null,
            logs: [],
            startedAt: Date.now(),
            completedAt: null,
          },
        });
      }
    }
  }

  // 2. Detect agent completions:
  //    - "@agent-name> ... complete" pattern (agent reporting back)
  //    - "Wrote N lines to .../filename.json" pattern
  //    - "agent-name ... completed" or "agent-name ... finished"
  for (const [agentId, info] of Object.entries(AGENT_MAP)) {
    // Resolve the effective step the same way as section 1 so the composite
    // key lookup matches what was inserted during spawn.
    const effectiveStep = currentStep >= 0 ? currentStep : info.stepIndex;
    const compositeKey = `${agentId}:${effectiveStep}`;
    if (!knownAgents.has(compositeKey)) continue;

    // Pattern: @agent-name> ... complete/finished/done
    const completionPattern = new RegExp(
      `@${agentId}[>\\)]\\s*.*(?:complete|finished|done|wrote|created)`,
      "i"
    );
    if (completionPattern.test(text)) {
      events.push({
        type: "agent-complete",
        stepIndex: effectiveStep,
        agent: {
          id: agentId,
          name: agentId,
          friendlyName: info.friendlyName,
          status: "complete",
          outputFile: null,
          logs: [],
          startedAt: null,
          completedAt: Date.now(),
        },
      });
    }
  }

  // 3. Detect file writes — maps output files to agent completions
  const writeMatches = text.matchAll(/(?:Wrote|Writing|Created|Output).*?([\w_-]+\.(?:json|md|html))/gi);
  for (const m of writeMatches) {
    const filename = m[1];
    const fileToAgent: Record<string, string> = {
      "peer_universe.json": "universe-scout",
      "source_catalog.json": "source-mapper",
      "metric_taxonomy.json": "metric-architect",
      "quantitative_tier1.json": "data-collector-t1",
      "quantitative_tier2.json": "data-collector-t2",
      "quantitative_tier3.json": "data-collector-t3",
      "quantitative_data.json": "data-collector-t1", // merged file
      "strategy_profiles.json": "strategy-extractor",
      "strategic_actions.json": "strategy-extractor",
      "standardized_data.json": "metric-architect",
      "correlations.json": "metric-architect",
      "driver_ranking.json": "metric-architect",
      "statistical_methodology.md": "metric-architect",
      "statistics_metadata.json": "metric-architect",
      "final_peer_set.json": "convergence-analyst",
      "platform_profiles.json": "platform-analyst",
      "asset_class_analysis.json": "vertical-analyst",
      "value_principles.md": "playbook-synthesizer",
      "platform_playbook.json": "playbook-synthesizer",
      "asset_class_playbooks.json": "playbook-synthesizer",
      "report_metadata.json": "report-builder",
      "final_report.html": "report-builder",
      "target_company_lens.json": "target-lens",
      "methodology_review.md": "methodology-reviewer",
      "results_review.md": "results-reviewer",
    };
    const agentId = fileToAgent[filename];
    if (agentId) {
      const info = AGENT_MAP[agentId];
      const effectiveStep = currentStep >= 0 ? currentStep : (info?.stepIndex ?? -1);
      const compositeKey = `${agentId}:${effectiveStep}`;
      if (knownAgents.has(compositeKey)) {
        events.push({
          type: "agent-complete",
          stepIndex: effectiveStep,
          agent: {
            id: agentId,
            name: agentId,
            friendlyName: info?.friendlyName ?? agentId,
            status: "complete",
            outputFile: filename,
            logs: [],
            startedAt: null,
            completedAt: Date.now(),
          },
        });
      }
    }
  }

  // 4. Detect step transitions from CLI output
  for (const { pattern, stepIndex } of STEP_TRIGGERS) {
    if (pattern.test(text)) {
      events.push({ type: "step-started", stepIndex });
      break;
    }
  }

  // 5. Detect quality gates
  if (/Quality Gate \d|quality gate/i.test(text)) {
    const gateMatch = text.match(/Gate\s*(\d)/i);
    const gateStep = gateMatch ? parseInt(gateMatch[1]) - 1 : -1;
    events.push({
      type: "quality-gate",
      stepIndex: gateStep,
      message: text.trim().slice(0, 200),
    });
  }

  // 6. Detect checkpoints (claim-auditor)
  //    Matches broad set of patterns emitted by claim-auditor in real CLI output.
  const checkpointTrigger =
    /CLAIM-AUDIT|CP-\d|claim[_\-. ]?audit(?:or)?|Fact[\s-]?Check(?:er|point)?|audit[\s-]?complete|claim[\s-]?verification|Checkpoint\s+CP-\d/i;
  if (checkpointTrigger.test(text)) {
    const cpMatch = text.match(/CP-(\d)/i);
    const cpIndex = cpMatch ? parseInt(cpMatch[1]) : -1;
    // Map CP number to after-step: CP-1 after step 1, CP-2 after step 3, CP-3 after step 4
    const cpToAfterStep: Record<number, number> = { 1: 1, 2: 3, 3: 4 };
    events.push({
      type: "checkpoint",
      stepIndex: cpToAfterStep[cpIndex] ?? -1,
      message: text.trim().slice(0, 200),
    });
  }

  // 7. Detect step completion signals
  //    "Step N complete" or "Quality Gate N passed" or moving to next step
  const stepCompleteMatch = text.match(/Step (\d).*(?:complete|passed|done)/i);
  if (stepCompleteMatch) {
    const stepIdx = parseInt(stepCompleteMatch[1]) - 1;
    events.push({ type: "step-complete", stepIndex: stepIdx });
  }

  return events;
}

/**
 * Get all agents that belong to a given step.
 */
export function getAgentsForStep(stepIndex: number): string[] {
  return Object.entries(AGENT_MAP)
    .filter(([, info]) => info.stepIndex === stepIndex)
    .map(([id]) => id);
}
