import { useState, useEffect, useRef } from "react";
import { invoke } from "@tauri-apps/api/core";
import type { OutputFile } from "../types/pipeline";

interface DataQualityHeatmapProps {
  files: OutputFile[];
}

// --- JSON shape types ---

interface MetricValue {
  value?: number | string | null;
  unit?: string;
  confidence?: "high" | "medium" | "low" | string;
  status?: "standardized" | "derived" | "estimated" | string;
  source?: string;
  as_of?: string;
}

interface FirmData {
  firm_id: string;
  ticker: string;
  firm_name?: string;
  metrics: Record<string, MetricValue>;
  valuation_multiples?: Record<string, number | null>;
}

interface StandardizedData {
  metadata?: { total_firms?: number; firms?: number };
  firms: FirmData[];
}

// Newer runs may use { matrix: [...] } instead of { firms: [...] }
interface RawStandardizedJson {
  metadata?: Record<string, unknown>;
  firms?: FirmData[];
  matrix?: FirmData[];
}

function normalizeStandardizedData(raw: RawStandardizedJson): StandardizedData {
  const firms = raw.firms ?? raw.matrix ?? [];
  return { metadata: raw.metadata as StandardizedData["metadata"], firms };
}

interface MetricDefinition {
  metric_id: string;
  name: string;
  abbreviation?: string;
  category?: string;
  is_driver_candidate?: boolean;
}

interface MetricTaxonomy {
  metrics: MetricDefinition[];
}

interface PeerEntry {
  firm_id: string;
  firm_name: string;
  ticker: string;
  cautionary_case?: boolean;
  metric_coverage_pct?: number;
  q1_independent_drivers?: string[];
  strategic_actions_count?: number;
}

interface FinalPeerSet {
  final_set: PeerEntry[];
}

// --- Cell color helper ---

function getCellColor(entry: MetricValue | undefined): string {
  if (!entry || entry.value === undefined || entry.value === null) {
    return "bg-gray-200";
  }
  const conf = entry.confidence?.toLowerCase() ?? "";
  const stat = entry.status?.toLowerCase() ?? "";
  if (conf === "low") return "bg-amber-400";
  if (conf === "high" && stat === "standardized") return "bg-emerald-500";
  // If no confidence/status fields at all (newer format), infer from presence of source
  if (!conf && !stat) {
    return entry.source ? "bg-emerald-500" : "bg-[#0068ff]";
  }
  // medium confidence, derived, estimated
  return "bg-[#0068ff]";
}

function formatValue(v: number | string | null | undefined, unit?: string): string {
  if (v === null || v === undefined) return "—";
  if (typeof v === "number") {
    const formatted = Math.abs(v) >= 1000
      ? v.toLocaleString(undefined, { maximumFractionDigits: 0 })
      : v.toLocaleString(undefined, { maximumFractionDigits: 2 });
    return unit ? `${formatted} ${unit}` : formatted;
  }
  return String(v);
}

// --- Tooltip ---

interface TooltipState {
  visible: boolean;
  x: number;
  y: number;
  metricName: string;
  value: string;
  confidence: string;
  status: string;
}

const TOOLTIP_INIT: TooltipState = {
  visible: false,
  x: 0,
  y: 0,
  metricName: "",
  value: "",
  confidence: "",
  status: "",
};

// --- Component ---

export function DataQualityHeatmap({ files }: DataQualityHeatmapProps) {
  const [standardizedData, setStandardizedData] = useState<StandardizedData | null>(null);
  const [taxonomy, setTaxonomy] = useState<MetricTaxonomy | null>(null);
  const [peerSet, setPeerSet] = useState<FinalPeerSet | null>(null);
  const [loading, setLoading] = useState(true);
  const [tooltip, setTooltip] = useState<TooltipState>(TOOLTIP_INIT);
  const containerRef = useRef<HTMLDivElement>(null);

  // Find relevant files from the file list — supports fallback filenames
  const findFile = (folder: string, ...filenames: string[]) =>
    filenames.reduce<OutputFile | null>(
      (found, name) => found ?? files.find((f) => f.folder === folder && f.filename === name) ?? null,
      null
    );

  useEffect(() => {
    const stdFile = findFile("3-analysis", "standardized_data.json", "standardized_matrix.json");
    const taxFile = findFile("1-universe", "metric_taxonomy.json");
    const peerFile = findFile("3-analysis", "final_peer_set.json");

    if (!stdFile) {
      setLoading(false);
      return;
    }

    setLoading(true);

    const reads: Promise<void>[] = [];

    reads.push(
      invoke<string>("read_output_file", { path: stdFile.path })
        .then((raw) => {
          try {
            setStandardizedData(normalizeStandardizedData(JSON.parse(raw)));
          } catch {
            setStandardizedData(null);
          }
        })
        .catch(() => setStandardizedData(null))
    );

    if (taxFile) {
      reads.push(
        invoke<string>("read_output_file", { path: taxFile.path })
          .then((raw) => {
            try {
              setTaxonomy(JSON.parse(raw) as MetricTaxonomy);
            } catch {
              setTaxonomy(null);
            }
          })
          .catch(() => setTaxonomy(null))
      );
    }

    if (peerFile) {
      reads.push(
        invoke<string>("read_output_file", { path: peerFile.path })
          .then((raw) => {
            try {
              setPeerSet(JSON.parse(raw) as FinalPeerSet);
            } catch {
              setPeerSet(null);
            }
          })
          .catch(() => setPeerSet(null))
      );
    }

    Promise.all(reads).finally(() => setLoading(false));
  }, [files.map((f) => f.path).join(",")]);

  // Nothing to show until the main data file exists
  if (loading) {
    return (
      <div className="px-6 py-8 text-sm text-gray-400 font-mono">
        Loading data quality heatmap...
      </div>
    );
  }

  if (!standardizedData || !standardizedData.firms?.length) {
    return null;
  }

  // --- Derive columns: driver-candidate metrics ---

  const allMetricIds = Array.from(
    new Set(standardizedData.firms.flatMap((f) => Object.keys(f.metrics ?? {})))
  );

  // Build a lookup from taxonomy (if available)
  const taxLookup: Record<string, MetricDefinition> = {};
  if (taxonomy?.metrics) {
    for (const m of taxonomy.metrics) {
      taxLookup[m.metric_id] = m;
    }
  }

  // Filter to driver candidates only (or fall back to all if taxonomy absent)
  const driverMetricIds = taxonomy?.metrics
    ? allMetricIds.filter((id) => taxLookup[id]?.is_driver_candidate === true)
    : allMetricIds;

  // Sort columns by metric_id for stable order
  const columns = driverMetricIds.slice().sort();

  // --- Derive rows: firms sorted by coverage % desc, PAX first ---

  function computeCoverage(firm: FirmData, metricIds: string[]): number {
    if (!metricIds.length) return 0;
    const present = metricIds.filter((id) => {
      const entry = firm.metrics?.[id];
      return entry && entry.value !== undefined && entry.value !== null;
    }).length;
    return Math.round((present / metricIds.length) * 100);
  }

  const firmsWithCoverage = standardizedData.firms.map((firm) => ({
    ...firm,
    coverage: computeCoverage(firm, columns),
  }));

  const sortedFirms = firmsWithCoverage.slice().sort((a, b) => {
    // PAX always first
    if (a.ticker === "PAX") return -1;
    if (b.ticker === "PAX") return 1;
    return b.coverage - a.coverage;
  });

  // --- Per-column coverage ---

  const colCoverage: Record<string, number> = {};
  for (const metId of columns) {
    const present = standardizedData.firms.filter((f) => {
      const entry = f.metrics?.[metId];
      return entry && entry.value !== undefined && entry.value !== null;
    }).length;
    colCoverage[metId] = standardizedData.firms.length
      ? Math.round((present / standardizedData.firms.length) * 100)
      : 0;
  }

  // --- Summary stats ---

  const totalFirms = standardizedData.firms.length;
  const totalDriverMetrics = columns.length;
  const avgCoverage =
    sortedFirms.length
      ? Math.round(sortedFirms.reduce((acc, f) => acc + f.coverage, 0) / sortedFirms.length)
      : 0;
  const finalSetCount = peerSet?.final_set?.length ?? 0;

  // --- Final peer set lookup ---

  const finalSetIds = new Set(peerSet?.final_set?.map((p) => p.firm_id) ?? []);
  const cautionaryIds = new Set(
    peerSet?.final_set?.filter((p) => p.cautionary_case).map((p) => p.firm_id) ?? []
  );

  // --- Tooltip handlers ---

  const showTooltip = (
    e: React.MouseEvent,
    metricName: string,
    entry: MetricValue | undefined
  ) => {
    const rect = containerRef.current?.getBoundingClientRect();
    const x = e.clientX - (rect?.left ?? 0);
    const y = e.clientY - (rect?.top ?? 0);
    setTooltip({
      visible: true,
      x,
      y,
      metricName,
      value: entry ? formatValue(entry.value, entry.unit) : "—",
      confidence: entry?.confidence ?? "—",
      status: entry?.status ?? "missing",
    });
  };

  const hideTooltip = () => setTooltip(TOOLTIP_INIT);

  // Column header abbreviation
  const colLabel = (id: string): string => {
    const def = taxLookup[id];
    return def?.abbreviation ?? id;
  };

  const colName = (id: string): string => {
    const def = taxLookup[id];
    return def?.name ?? id;
  };

  return (
    <div ref={containerRef} className="relative px-6 py-5 border-b border-gray-200">
      {/* Section header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-gray-900">Data Quality</h2>
        <span className="text-[10px] text-gray-400 font-mono">firms × driver metrics</span>
      </div>

      {/* Key stats row */}
      <div className="flex items-center gap-4 mb-4 text-[11px] font-mono">
        <span className="text-gray-700">
          <span className="font-semibold text-gray-900">{totalFirms}</span>
          <span className="text-gray-400 ml-1">firms</span>
        </span>
        <span className="text-gray-300">·</span>
        <span className="text-gray-700">
          <span className="font-semibold text-gray-900">{totalDriverMetrics}</span>
          <span className="text-gray-400 ml-1">driver metrics</span>
        </span>
        <span className="text-gray-300">·</span>
        <span className="text-gray-700">
          <span className="font-semibold text-gray-900">{avgCoverage}%</span>
          <span className="text-gray-400 ml-1">avg coverage</span>
        </span>
        {finalSetCount > 0 && (
          <>
            <span className="text-gray-300">·</span>
            <span className="text-gray-700">
              <span className="font-semibold text-gray-900">{finalSetCount}</span>
              <span className="text-gray-400 ml-1">in final peer set</span>
            </span>
          </>
        )}
      </div>

      {/* Peer set badges */}
      {peerSet?.final_set && peerSet.final_set.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-4">
          {peerSet.final_set.map((peer) => {
            const isCautionary = cautionaryIds.has(peer.firm_id);
            return (
              <span
                key={peer.firm_id}
                title={`${peer.firm_name}${isCautionary ? " — cautionary case" : ""}`}
                className={`
                  px-2 py-0.5 rounded text-[10px] font-mono border
                  ${isCautionary
                    ? "border-amber-400 text-amber-700 bg-amber-50"
                    : "border-[#0068ff]/40 text-[#0068ff] bg-blue-50"
                  }
                `}
              >
                {peer.ticker}
              </span>
            );
          })}
        </div>
      )}

      {/* Heatmap grid — horizontally scrollable */}
      {columns.length === 0 ? (
        <div className="text-sm text-gray-400 py-4">
          No driver-candidate metrics found in the taxonomy.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table
            className="border-separate"
            style={{ borderSpacing: 0 }}
            role="grid"
            aria-label="Data quality heatmap"
          >
            <thead>
              <tr>
                {/* Sticky ticker column header */}
                <th
                  className="sticky left-0 z-10 bg-white w-20 min-w-[5rem] pr-2 pb-1 text-left"
                  scope="col"
                >
                  <span className="text-[9px] text-gray-400 font-mono uppercase tracking-wide">
                    Ticker
                  </span>
                </th>
                {/* Metric abbreviation headers */}
                {columns.map((id) => (
                  <th
                    key={id}
                    scope="col"
                    title={colName(id)}
                    className="pb-1 px-px"
                  >
                    <div
                      className="font-mono text-[9px] text-gray-500 text-center leading-tight"
                      style={{ writingMode: "vertical-rl", transform: "rotate(180deg)", height: 52, width: 24 }}
                    >
                      {colLabel(id)}
                    </div>
                  </th>
                ))}
                {/* Coverage % header */}
                <th className="pb-1 pl-2 text-right" scope="col">
                  <span className="text-[9px] text-gray-400 font-mono uppercase tracking-wide">
                    Cov.
                  </span>
                </th>
              </tr>
            </thead>

            <tbody>
              {sortedFirms.map((firm) => {
                const isPax = firm.ticker === "PAX";
                const isInFinalSet = finalSetIds.has(firm.firm_id);
                return (
                  <tr
                    key={firm.firm_id}
                    className={isPax ? "bg-blue-50" : "bg-white"}
                  >
                    {/* Sticky ticker cell */}
                    <td
                      className={`sticky left-0 z-10 pr-2 py-px ${isPax ? "bg-blue-50" : "bg-white"}`}
                    >
                      <span
                        className={`
                          font-mono text-[11px] whitespace-nowrap
                          ${isPax ? "text-[#0068ff] font-semibold" : "text-gray-600"}
                          ${isInFinalSet && !isPax ? "text-gray-800" : ""}
                        `}
                        title={firm.firm_name}
                      >
                        {firm.ticker}
                      </span>
                    </td>

                    {/* Metric cells */}
                    {columns.map((metId) => {
                      const entry = firm.metrics?.[metId];
                      const cellColor = getCellColor(entry);
                      return (
                        <td key={metId} className="px-px py-px">
                          <div
                            className={`
                              rounded-sm cursor-default transition-opacity hover:opacity-70
                              ${cellColor}
                            `}
                            style={{ width: 24, height: 20 }}
                            onMouseEnter={(e) =>
                              showTooltip(e, colName(metId), entry)
                            }
                            onMouseLeave={hideTooltip}
                            role="gridcell"
                            aria-label={`${firm.ticker} · ${colName(metId)}: ${entry ? formatValue(entry.value, entry.unit) : "missing"}`}
                          />
                        </td>
                      );
                    })}

                    {/* Row coverage % */}
                    <td className="pl-2 py-px text-right">
                      <span
                        className={`font-mono text-[10px] ${
                          firm.coverage >= 80
                            ? "text-emerald-600"
                            : firm.coverage >= 50
                            ? "text-amber-600"
                            : "text-red-500"
                        }`}
                      >
                        {firm.coverage}%
                      </span>
                    </td>
                  </tr>
                );
              })}

              {/* Column coverage footer row */}
              <tr>
                <td className={`sticky left-0 z-10 bg-white pt-1 pr-2`}>
                  <span className="font-mono text-[9px] text-gray-400 uppercase tracking-wide">
                    Cov.
                  </span>
                </td>
                {columns.map((metId) => (
                  <td key={metId} className="px-px pt-1 text-center">
                    <span
                      className={`font-mono text-[9px] ${
                        colCoverage[metId] >= 80
                          ? "text-emerald-600"
                          : colCoverage[metId] >= 50
                          ? "text-amber-600"
                          : "text-red-500"
                      }`}
                    >
                      {colCoverage[metId]}%
                    </span>
                  </td>
                ))}
                <td />
              </tr>
            </tbody>
          </table>
        </div>
      )}

      {/* Legend */}
      <div className="flex items-center gap-4 mt-4 text-[10px] font-mono text-gray-500">
        <span className="flex items-center gap-1.5">
          <span className="inline-block w-3 h-3 rounded-sm bg-emerald-500" />
          High confidence
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block w-3 h-3 rounded-sm bg-[#0068ff]" />
          Medium / derived
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block w-3 h-3 rounded-sm bg-amber-400" />
          Low confidence
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block w-3 h-3 rounded-sm bg-gray-200" />
          Missing
        </span>
      </div>

      {/* Tooltip */}
      {tooltip.visible && (
        <div
          className="absolute z-50 pointer-events-none bg-gray-900 text-white rounded-md px-3 py-2 shadow-lg"
          style={{
            left: tooltip.x + 12,
            top: tooltip.y - 8,
            maxWidth: 240,
          }}
        >
          <div className="font-medium text-[11px] leading-snug text-white mb-1">
            {tooltip.metricName}
          </div>
          <div className="text-[10px] font-mono text-gray-300">
            value: <span className="text-white">{tooltip.value}</span>
          </div>
          <div className="text-[10px] font-mono text-gray-300">
            confidence: <span className="text-white">{tooltip.confidence}</span>
          </div>
          <div className="text-[10px] font-mono text-gray-300">
            status: <span className="text-white">{tooltip.status}</span>
          </div>
        </div>
      )}
    </div>
  );
}
