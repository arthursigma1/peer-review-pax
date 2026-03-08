import { useEffect, useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import type { OutputFile } from "../types/pipeline";

interface AnalysisInsightsProps {
  files: OutputFile[];
}

interface CorrelationsMetadata {
  methodology?: {
    method?: string;
    consistent_sub_sample_n?: number;
    full_sample_n_by_multiple?: Record<string, number>;
    multiple_testing_correction?: string;
    total_correlations_computed?: number;
  };
}

interface DriverRankingMetadata {
  total_drivers_ranked?: number;
}

interface DriverEntry {
  correlation_classification?: string;
  confidence_class?: string;
}

interface DriverRanking {
  metadata?: DriverRankingMetadata;
  drivers?: DriverEntry[];
}

interface StatisticsMetadata {
  discovery_method?: string;
  discovery_q?: number;
  n_effective?: number;
  temporal_depth?: {
    target_range?: string;
    mandatory_years?: number;
    firms_with_multi_year?: number;
  };
  ci_method?: string;
  minimum_sample_rule?: {
    ranking_threshold?: number;
    reporting_threshold?: number;
  };
  sensitivity_protocol?: string[];
}

interface ConfidenceStats {
  maxN: number | null;
  totalCorrelations: number | null;
  correction: string | null;
  stableDrivers: number;
  multipleSpecificDrivers: number;
  contextualDrivers: number;
  unsupportedDrivers: number;
  totalRanked: number | null;
}

interface AuditData {
  checkpoint: string;
  verdict: "PASSED" | "BLOCKED" | string;
  summary?:
    | {
        total_claims?: number;
        grounded?: number;
        inferred?: number;
        weak_evidence?: number;
        ungrounded?: number;
        fabricated?: number;
      }
    | string;
  claims_audited?: number;
  claims_passed?: number;
  claims_flagged?: number;
  inferred_claims?: unknown[];
  blocked_claims?: unknown[];
  statistics?: {
    total_claims_audited?: number;
    passed?: number;
    blocked?: number;
  };
}

interface CheckpointResult {
  id: string;
  verdict: "PASSED" | "BLOCKED" | "UNKNOWN";
  passed: number;
  total: number;
  hasInferred: boolean;
}

function findFile(files: OutputFile[], folder: string, filename: string): OutputFile | undefined {
  return files.find((f) => f.folder === folder && f.filename === filename);
}

async function readJson<T>(path: string): Promise<T | null> {
  try {
    const raw = await invoke<string>("read_output_file", { path });
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

function classificationCounts(drivers: DriverEntry[]): Record<string, number> {
  const counts: Record<string, number> = {
    stable_value_driver: 0,
    multiple_specific_driver: 0,
    contextual_driver: 0,
    unsupported: 0,
    moderate_signal: 0,
    not_a_driver: 0,
    other: 0,
  };

  for (const driver of drivers) {
    const classification = driver.correlation_classification ?? "";
    if (classification in counts) {
      counts[classification] += 1;
    } else {
      counts.other += 1;
    }
  }

  return counts;
}

function formatDiscoveryMethod(sm: StatisticsMetadata): string | null {
  if (sm.discovery_method === "bh_fdr_q_0.10") {
    return "BH FDR q=0.10";
  }
  return sm.discovery_method ?? null;
}

function getAuditTotals(audit: AuditData): { passed: number; total: number; hasInferred: boolean } {
  if (audit.summary && typeof audit.summary !== "string") {
    const total = audit.summary.total_claims ?? 0;
    const blocked = (audit.summary.ungrounded ?? 0) + (audit.summary.fabricated ?? 0);
    return {
      passed: Math.max(total - blocked, 0),
      total,
      hasInferred: (audit.summary.inferred ?? 0) > 0,
    };
  }

  let passed = audit.claims_passed ?? audit.statistics?.passed ?? 0;
  let total = audit.claims_audited ?? audit.statistics?.total_claims_audited ?? 0;
  if (total === 0 && audit.claims_flagged !== undefined && passed !== 0) {
    total = passed + audit.claims_flagged;
  }

  return {
    passed,
    total,
    hasInferred: Array.isArray(audit.inferred_claims) && audit.inferred_claims.length > 0,
  };
}

interface ConfidencePillProps {
  label: string;
  value: string | number | null;
}

function ConfidencePill({ label, value }: ConfidencePillProps) {
  if (value === null || value === undefined) return null;
  return (
    <span className="inline-flex items-baseline gap-1 text-[11px] text-gray-500 whitespace-nowrap">
      <span className="font-mono text-gray-800">{value}</span>
      <span>{label}</span>
    </span>
  );
}

interface DriverBarProps {
  stable: number;
  multipleSpecific: number;
  contextual: number;
  unsupported: number;
}

function DriverBar({ stable, multipleSpecific, contextual, unsupported }: DriverBarProps) {
  const total = stable + multipleSpecific + contextual + unsupported;
  if (total === 0) return null;

  const pct = (n: number) => `${((n / total) * 100).toFixed(1)}%`;

  return (
    <div className="flex items-center gap-3">
      <div className="flex h-2 rounded overflow-hidden flex-1 min-w-0 bg-gray-100">
        {stable > 0 && (
          <div
            className="bg-emerald-500 h-full"
            style={{ width: pct(stable) }}
            title={`Stable value drivers: ${stable}`}
          />
        )}
        {multipleSpecific > 0 && (
          <div
            className="bg-blue-400 h-full"
            style={{ width: pct(multipleSpecific) }}
            title={`Multiple-specific drivers: ${multipleSpecific}`}
          />
        )}
        {contextual > 0 && (
          <div
            className="bg-amber-400 h-full"
            style={{ width: pct(contextual) }}
            title={`Contextual drivers: ${contextual}`}
          />
        )}
        {unsupported > 0 && (
          <div
            className="bg-gray-300 h-full"
            style={{ width: pct(unsupported) }}
            title={`Unsupported or weak drivers: ${unsupported}`}
          />
        )}
      </div>
      <div className="flex items-center gap-2 shrink-0">
        {stable > 0 && (
          <span className="inline-flex items-center gap-1 text-[10px] text-gray-500">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block" />
            {stable} stable
          </span>
        )}
        {multipleSpecific > 0 && (
          <span className="inline-flex items-center gap-1 text-[10px] text-gray-500">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-400 inline-block" />
            {multipleSpecific} specific
          </span>
        )}
        {contextual > 0 && (
          <span className="inline-flex items-center gap-1 text-[10px] text-gray-500">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 inline-block" />
            {contextual} contextual
          </span>
        )}
        {unsupported > 0 && (
          <span className="inline-flex items-center gap-1 text-[10px] text-gray-500">
            <span className="w-1.5 h-1.5 rounded-full bg-gray-300 inline-block" />
            {unsupported} weak
          </span>
        )}
      </div>
    </div>
  );
}

interface CheckpointBadgeProps {
  cp: CheckpointResult;
}

function CheckpointBadge({ cp }: CheckpointBadgeProps) {
  const isBlocked = cp.verdict === "BLOCKED";
  const hasInferred = cp.hasInferred && !isBlocked;

  let colorClass: string;
  if (isBlocked) {
    colorClass = "border-red-300 bg-red-50 text-red-700";
  } else if (hasInferred) {
    colorClass = "border-amber-300 bg-amber-50 text-amber-700";
  } else {
    colorClass = "border-emerald-300 bg-emerald-50 text-emerald-700";
  }

  const checkMark = isBlocked ? "\u2717" : "\u2713";

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded border text-[11px] ${colorClass}`}
      title={
        isBlocked
          ? `${cp.id}: BLOCKED`
          : hasInferred
          ? `${cp.id}: passed with inferred claims`
          : `${cp.id}: passed`
      }
    >
      <span>{checkMark}</span>
      <span className="font-mono">{cp.id}</span>
      {cp.total > 0 && <span className="text-current/70">{cp.passed}/{cp.total}</span>}
    </span>
  );
}

export function AnalysisInsights({ files }: AnalysisInsightsProps) {
  const [loading, setLoading] = useState(true);
  const [confidence, setConfidence] = useState<ConfidenceStats | null>(null);
  const [checkpoints, setCheckpoints] = useState<CheckpointResult[]>([]);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);

      const statsMeta = findFile(files, "3-analysis", "statistics_metadata.json");
      const correlationsFile = findFile(files, "3-analysis", "correlations.json");
      const driverFile = findFile(files, "3-analysis", "driver_ranking.json");

      const stats: ConfidenceStats = {
        maxN: null,
        totalCorrelations: null,
        correction: null,
        stableDrivers: 0,
        multipleSpecificDrivers: 0,
        contextualDrivers: 0,
        unsupportedDrivers: 0,
        totalRanked: null,
      };

      if (statsMeta) {
        const sm = await readJson<StatisticsMetadata>(statsMeta.path);
        if (sm && sm.n_effective !== undefined) {
          stats.maxN = sm.n_effective;
          stats.correction = formatDiscoveryMethod(sm);
        }
      }

      if (correlationsFile) {
        const correlations = await readJson<CorrelationsMetadata>(correlationsFile.path);
        const meta = correlations?.methodology;
        if (meta) {
          if (meta.total_correlations_computed !== undefined) {
            stats.totalCorrelations = meta.total_correlations_computed;
          }
          if (stats.correction === null && meta.multiple_testing_correction) {
            stats.correction = meta.multiple_testing_correction
              .replace("Benjamini-Hochberg FDR at ", "BH FDR ")
              .replace("Benjamini-Hochberg ", "BH ");
          }
        }
      }

      if (driverFile) {
        const ranking = await readJson<DriverRanking>(driverFile.path);
        if (ranking) {
          stats.totalRanked = ranking.metadata?.total_drivers_ranked ?? null;
          if (ranking.drivers) {
            const counts = classificationCounts(ranking.drivers);
            stats.stableDrivers = counts.stable_value_driver ?? 0;
            stats.multipleSpecificDrivers = counts.multiple_specific_driver ?? 0;
            stats.contextualDrivers = (counts.contextual_driver ?? 0) + (counts.moderate_signal ?? 0);
            stats.unsupportedDrivers =
              (counts.unsupported ?? 0) + (counts.not_a_driver ?? 0) + (counts.other ?? 0);
          }
        }
      }

      if (!cancelled) {
        const hasAnyData =
          stats.maxN !== null || stats.totalCorrelations !== null || stats.totalRanked !== null;
        setConfidence(hasAnyData ? stats : null);
      }

      const cpDefs: Array<{ id: string; folder: string; filename: string }> = [
        { id: "CP-1", folder: "2-data", filename: "audit_cp1_data.json" },
        { id: "CP-2", folder: "4-deep-dives", filename: "audit_cp2_deep_dives.json" },
        { id: "CP-3", folder: "5-playbook", filename: "audit_cp3_playbook.json" },
      ];

      const cpResults: CheckpointResult[] = [];
      for (const def of cpDefs) {
        const file = findFile(files, def.folder, def.filename);
        if (!file) continue;

        const audit = await readJson<AuditData>(file.path);
        if (!audit) continue;

        const verdict =
          audit.verdict === "PASSED" || audit.verdict === "BLOCKED" ? audit.verdict : "UNKNOWN";
        const { passed, total, hasInferred } = getAuditTotals(audit);
        cpResults.push({ id: def.id, verdict, passed, total, hasInferred });
      }

      if (!cancelled) {
        setCheckpoints(cpResults);
        setLoading(false);
      }
    }

    load().catch(() => {
      if (!cancelled) setLoading(false);
    });

    return () => {
      cancelled = true;
    };
  }, [files]);

  if (loading || (confidence === null && checkpoints.length === 0)) {
    return null;
  }

  const hasDriverBar =
    confidence !== null &&
    (confidence.stableDrivers +
      confidence.multipleSpecificDrivers +
      confidence.contextualDrivers +
      confidence.unsupportedDrivers) >
      0;

  return (
    <div className="px-6 py-4 border-b border-gray-200 space-y-3">
      {confidence !== null && (
        <div>
          <div className="flex items-center gap-1 mb-1.5">
            <span className="text-[10px] text-gray-400 uppercase tracking-wider font-medium">
              Statistical Confidence
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
            {confidence.maxN !== null && (
              <ConfidencePill value={`N = ${confidence.maxN}`} label="firms (max sample)" />
            )}
            {confidence.totalCorrelations !== null && (
              <ConfidencePill value={confidence.totalCorrelations} label="correlations" />
            )}
            {confidence.correction !== null && (
              <ConfidencePill value={confidence.correction} label="" />
            )}
            {confidence.stableDrivers > 0 && (
              <ConfidencePill value={confidence.stableDrivers} label="stable drivers" />
            )}
            {confidence.totalRanked !== null && (
              <ConfidencePill value={confidence.totalRanked} label="ranked" />
            )}
          </div>

          {hasDriverBar && (
            <div className="mt-2">
              <DriverBar
                stable={confidence.stableDrivers}
                multipleSpecific={confidence.multipleSpecificDrivers}
                contextual={confidence.contextualDrivers}
                unsupported={confidence.unsupportedDrivers}
              />
            </div>
          )}
        </div>
      )}

      {checkpoints.length > 0 && (
        <div>
          <div className="flex items-center gap-1 mb-1.5">
            <span className="text-[10px] text-gray-400 uppercase tracking-wider font-medium">
              Claim Audits
            </span>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {checkpoints.map((cp) => (
              <CheckpointBadge key={cp.id} cp={cp} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
