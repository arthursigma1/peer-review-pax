import { invoke } from "@tauri-apps/api/core";
import type { RunDigest } from "../hooks/useRunDigest";

const CLASSIFICATION_LABEL: Record<string, { label: string; color: string }> = {
  stable_value_driver:     { label: "Stable",    color: "bg-emerald-100 text-emerald-700" },
  multiple_specific_driver:{ label: "Multiple-specific", color: "bg-blue-100 text-blue-700" },
  moderate_signal:         { label: "Moderate",  color: "bg-amber-100 text-amber-700" },
  contextual_driver:       { label: "Contextual",color: "bg-purple-100 text-purple-700" },
  not_a_driver:            { label: "Weak",      color: "bg-gray-100 text-gray-500" },
};

interface Props {
  digest: RunDigest;
  ticker: string;
  runDate: string;
}

export function RunDigestPanel({ digest, ticker, runDate }: Props) {
  const openReport = async () => {
    try {
      await invoke("open_in_browser", { ticker, runDate });
    } catch {
      // fallback silently
    }
  };

  return (
    <div className="h-full overflow-y-auto px-5 py-4 space-y-5 text-sm">
      {/* Headline stats */}
      <div className="flex items-center gap-6 flex-wrap">
        {digest.peers_total != null && (
          <Stat label="Peers" value={String(digest.peers_total)} />
        )}
        {digest.metrics_total != null && (
          <Stat label="Metrics" value={String(digest.metrics_total)} />
        )}
        {digest.plays_total > 0 && (
          <Stat label="Plays" value={String(digest.plays_total)} />
        )}
        {digest.anti_patterns_total > 0 && (
          <Stat label="Anti-patterns" value={String(digest.anti_patterns_total)} />
        )}
        {digest.play_assessments_total > 0 && (
          <Stat
            label="Target assessments"
            value={`${digest.play_assessments_total} (${digest.play_assessments_high} high)`}
          />
        )}
        {digest.has_report && (
          <button
            onClick={openReport}
            className="ml-auto px-3 py-1 rounded text-xs font-medium bg-[#0068ff] text-white hover:bg-[#0055d4] transition-colors"
          >
            Open Report ↗
          </button>
        )}
      </div>

      {/* Value drivers table */}
      {digest.drivers.length > 0 && (
        <section>
          <h3 className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-2">
            Value Drivers
          </h3>
          <table className="w-full text-xs">
            <thead>
              <tr className="text-gray-400 text-[10px] border-b border-gray-100">
                <th className="text-left pb-1.5 font-medium w-16">Rank</th>
                <th className="text-left pb-1.5 font-medium">Driver</th>
                <th className="text-right pb-1.5 font-medium w-16">ρ avg</th>
                <th className="text-right pb-1.5 font-medium w-32">Classification</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {digest.drivers.map((d, i) => {
                const cls = CLASSIFICATION_LABEL[d.classification] ?? { label: d.classification, color: "bg-gray-100 text-gray-500" };
                return (
                  <tr key={d.id} className="hover:bg-gray-50/50">
                    <td className="py-1.5 text-gray-400 font-mono">{d.id}</td>
                    <td className="py-1.5 text-gray-800 font-medium">{d.name}</td>
                    <td className="py-1.5 text-right font-mono text-gray-700">{d.rho.toFixed(2)}</td>
                    <td className="py-1.5 text-right">
                      <span className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-medium ${cls.color}`}>
                        {cls.label}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </section>
      )}

      {/* Target Company Lens — Board Level principles */}
      {digest.top_principles.length > 0 && (
        <section>
          <h3 className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-2">
            Target Company Lens — Board Level
          </h3>
          <ol className="space-y-2.5">
            {digest.top_principles.map((p, i) => (
              <li key={i} className="flex gap-2.5">
                <span className="shrink-0 w-4 h-4 mt-0.5 rounded-full bg-gray-100 text-gray-500 text-[10px] font-mono flex items-center justify-center">
                  {i + 1}
                </span>
                <p className="text-gray-700 leading-snug text-xs">{p}</p>
              </li>
            ))}
          </ol>
        </section>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-[10px] text-gray-400 uppercase tracking-wider">{label}</span>
      <span className="text-lg font-semibold text-gray-900 leading-none font-mono">{value}</span>
    </div>
  );
}
