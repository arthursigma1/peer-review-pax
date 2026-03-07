import { AGENT_NAMES } from "../types/pipeline";
import type { StepStatus, AgentStatus, CheckpointStatus } from "../types/pipeline";

interface ParsedLine {
  type: "step_start" | "step_complete" | "agent_start" | "agent_complete" | "gate" | "log" | "error" | "checkpoint";
  stepIndex?: number;
  agentId?: string;
  checkpointId?: string;
  checkpointStatus?: CheckpointStatus;
  claimsPassed?: number;
  claimsTotal?: number;
  claimsUngrounded?: number;
  claimsFabricated?: number;
  retryAttempt?: number;
  message: string;
}

const STEP_PATTERNS = [
  /Step (\d) of 5.*?["""](.+?)["""]/,
  /(?:Map the Industry|Gather Data|Find What Drives Value|Deep-Dive Peers|Build the Playbook)/,
  /Quality Gate (\d)/,
];

const STEP_NAME_TO_INDEX: Record<string, number> = {
  "map the industry": 0,
  "gather data": 1,
  "find what drives value": 2,
  "deep-dive peers": 3,
  "build the playbook": 4,
};

export function parseCLILine(line: string): ParsedLine {
  // Check for claim audit lines (prefix guard — avoids 4 regex attempts on common log lines)
  if (line.includes("[CLAIM-AUDIT]")) {
    const cpScanMatch = line.match(/\[CLAIM-AUDIT\] (CP-\d) scanning/);
    if (cpScanMatch) {
      return { type: "checkpoint", checkpointId: cpScanMatch[1], checkpointStatus: "scanning", message: line };
    }

    const cpPassedMatch = line.match(/\[CLAIM-AUDIT\] (CP-\d) PASSED \((\d+)\/(\d+) claims?\)/);
    if (cpPassedMatch) {
      return {
        type: "checkpoint", checkpointId: cpPassedMatch[1], checkpointStatus: "passed",
        claimsPassed: parseInt(cpPassedMatch[2]), claimsTotal: parseInt(cpPassedMatch[3]),
        message: line,
      };
    }

    const cpBlockedMatch = line.match(/\[CLAIM-AUDIT\] (CP-\d) BLOCKED \((\d+) ungrounded, (\d+) fabricated\)/);
    if (cpBlockedMatch) {
      return {
        type: "checkpoint", checkpointId: cpBlockedMatch[1], checkpointStatus: "blocked",
        claimsUngrounded: parseInt(cpBlockedMatch[2]), claimsFabricated: parseInt(cpBlockedMatch[3]),
        message: line,
      };
    }

    const cpRetryMatch = line.match(/\[CLAIM-AUDIT\] (CP-\d) retrying \(attempt (\d+)\/2\)/);
    if (cpRetryMatch) {
      return { type: "checkpoint", checkpointId: cpRetryMatch[1], checkpointStatus: "retrying",
        retryAttempt: parseInt(cpRetryMatch[2]), message: line };
    }
  }

  // Check for step start
  for (const pattern of STEP_PATTERNS) {
    const match = line.match(pattern);
    if (match) {
      const stepName = (match[2] || match[0]).toLowerCase();
      const index = STEP_NAME_TO_INDEX[stepName] ?? parseInt(match[1] || "0") - 1;
      if (line.includes("complete") || line.includes("done")) {
        return { type: "step_complete", stepIndex: index, message: line };
      }
      if (line.includes("Quality Gate")) {
        return { type: "gate", stepIndex: parseInt(match[1]) - 1, message: line };
      }
      return { type: "step_start", stepIndex: index, message: line };
    }
  }

  // Check for agent references
  for (const [agentId] of Object.entries(AGENT_NAMES)) {
    if (line.includes(agentId)) {
      if (line.includes("spawning") || line.includes("Spawning") || line.includes("dispatching")) {
        return { type: "agent_start", agentId, message: line };
      }
      if (line.includes("completed") || line.includes("finished") || line.includes("done")) {
        return { type: "agent_complete", agentId, message: line };
      }
    }
  }

  // Check for errors
  if (line.toLowerCase().includes("error") || line.toLowerCase().includes("failed")) {
    return { type: "error", message: line };
  }

  return { type: "log", message: line };
}

export function inferStepStatus(logs: string[]): StepStatus {
  const lastRelevant = [...logs].reverse().find(
    (l) => l.includes("complete") || l.includes("failed") || l.includes("running") || l.includes("start")
  );
  if (!lastRelevant) return "pending";
  if (lastRelevant.includes("failed")) return "failed";
  if (lastRelevant.includes("complete")) return "complete";
  return "running";
}

export function inferAgentStatus(logs: string[]): AgentStatus {
  if (logs.length === 0) return "idle";
  const last = logs[logs.length - 1];
  if (last.includes("failed")) return "failed";
  if (last.includes("complete") || last.includes("finished")) return "complete";
  return "running";
}

export function formatElapsed(ms: number): string {
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  if (hours > 0) return `${hours}h ${minutes % 60}m`;
  if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
  return `${seconds}s`;
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
