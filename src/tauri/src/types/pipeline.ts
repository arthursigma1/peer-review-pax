export type StepStatus = "pending" | "running" | "complete" | "failed";
export type AgentStatus = "idle" | "running" | "complete" | "failed";
export type GateStatus = "pending" | "awaiting_review" | "approved" | "rejected";

export interface PipelineStep {
  index: number;
  id: string;
  name: string;
  description: string;
  status: StepStatus;
  agents: PipelineAgent[];
  gate: QualityGate | null;
  startedAt: number | null;
  completedAt: number | null;
}

export interface PipelineAgent {
  id: string;
  name: string;
  friendlyName: string;
  status: AgentStatus;
  outputFile: string | null;
  logs: string[];
  startedAt: number | null;
  completedAt: number | null;
}

export interface QualityGate {
  stepIndex: number;
  status: GateStatus;
  criteria: string[];
  results: GateResult[];
  notes: string;
}

export interface GateResult {
  criterion: string;
  passed: boolean;
  detail: string;
}

export type CheckpointStatus = "pending" | "scanning" | "passed" | "blocked" | "retrying";

export interface ClaimSummary {
  total: number;
  grounded: number;
  inferred: number;
  weakEvidence: number;
  ungrounded: number;
  fabricated: number;
}

export interface BlockedClaim {
  claimId: string;
  claimText: string;
  verdict: "UNGROUNDED" | "FABRICATED";
  dimension: string;
  reasoning: string;
  requiredFix: string;
}

export interface Checkpoint {
  id: string;
  name: string;
  afterStep: number;
  status: CheckpointStatus;
  summary: ClaimSummary | null;
  blockedClaims: BlockedClaim[];
  retryCount: number;
}

export interface OutputFile {
  filename: string;
  path: string;
  size: number;
  modified: number;
  file_type: string;
  folder: string;
}

export const FOLDER_LABELS: Record<string, string> = {
  "1-universe": "Universe & Sources",
  "2-data": "Data Collection",
  "3-analysis": "Statistical Analysis",
  "4-deep-dives": "Deep-Dive Profiles",
  "5-playbook": "PAX Memo & Report",
  "6-review": "Review",
};

export interface ToneProfile {
  source: "default" | "extracted";
  reference_files: string[];
  formality: "academic" | "professional" | "conversational";
  voice: "active" | "passive" | "mixed";
  sentence_style: "concise" | "elaborate" | "mixed";
  hedging: "explicit" | "moderate" | "minimal";
  data_presentation: "tables-first" | "narrative-first" | "integrated";
  terminology: "technical" | "accessible" | "mixed";
  nuances: string;
}

export const DEFAULT_TONE_PROFILE: ToneProfile = {
  source: "default",
  reference_files: [],
  formality: "academic",
  voice: "active",
  sentence_style: "concise",
  hedging: "explicit",
  data_presentation: "tables-first",
  terminology: "technical",
  nuances: "Lead with evidence before conclusions. Every claim cites a source ID. Use Oxford commas. Qualify correlation-based findings with statistical confidence. Avoid marketing language — prefer 'the data suggest' over 'clearly demonstrates'. Section headers are descriptive, not clever. Footnotes for methodological caveats.",
};

export interface PipelineConfig {
  ticker: string;
  sector: string;
  autoMode: boolean;
  sellSideDir: string | null;
  consultingDir: string | null;
  referencePeers: string | null;
  toneProfile: ToneProfile;
}

export const INITIAL_CHECKPOINTS: Omit<Checkpoint, "status" | "summary" | "blockedClaims" | "retryCount">[] = [
  { id: "CP-1", name: "Post-Data Fact Check", afterStep: 1 },
  { id: "CP-2", name: "Post-Deep-Dive Fact Check", afterStep: 3 },
  { id: "CP-3", name: "Post-Playbook Fact Check", afterStep: 4 },
];

export const PIPELINE_STEPS: Omit<PipelineStep, "status" | "agents" | "gate" | "startedAt" | "completedAt">[] = [
  {
    index: 0,
    id: "map-industry",
    name: "Map the Industry",
    description: "Identify peers, catalog sources, define metrics",
  },
  {
    index: 1,
    id: "gather-data",
    name: "Gather Data",
    description: "Collect quantitative data and extract strategies",
  },
  {
    index: 2,
    id: "find-drivers",
    name: "Find What Drives Value",
    description: "Standardize, correlate, rank drivers",
  },
  {
    index: 3,
    id: "deep-dive",
    name: "Deep-Dive Peers",
    description: "Platform profiles and asset class analysis",
  },
  {
    index: 4,
    id: "build-playbook",
    name: "Build the Playbook",
    description: "Synthesize the PAX-first playbook, target lens, and decision memo",
  },
  {
    index: 5,
    id: "review-analysis",
    name: "Review Analysis",
    description: "Deploy review agents to identify improvements",
  },
];

