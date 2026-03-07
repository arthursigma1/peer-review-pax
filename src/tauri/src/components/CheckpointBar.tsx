import { useState } from "react";
import type { Checkpoint } from "../types/pipeline";

interface CheckpointBarProps {
  checkpoint: Checkpoint;
}

const STATUS_STYLES: Record<string, string> = {
  pending: "border-dashed border-zinc-700 text-zinc-500",
  scanning: "border-teal-400 text-teal-300 animate-pulse",
  passed: "border-emerald-500 text-emerald-400",
  blocked: "border-red-500 text-red-400",
  retrying: "border-amber-500 text-amber-400",
};

const STATUS_ICONS: Record<string, string> = {
  pending: "\u25CB",   // ○
  scanning: "\u25CE",  // ◎
  passed: "\u2713",    // ✓
  blocked: "\u2717",   // ✗
  retrying: "\u21BB",  // ↻
};

export function CheckpointBar({ checkpoint }: CheckpointBarProps) {
  const [expanded, setExpanded] = useState(false);

  const style = STATUS_STYLES[checkpoint.status] || STATUS_STYLES.pending;
  const icon = STATUS_ICONS[checkpoint.status] || STATUS_ICONS.pending;

  return (
    <div className="mx-4 my-1">
      <button
        onClick={() => setExpanded(!expanded)}
        className={`w-full flex items-center gap-2 px-3 py-1.5 rounded border ${style} bg-zinc-900/50 text-xs transition-all hover:bg-zinc-800/60`}
      >
        <span className="font-mono text-[10px] opacity-70">{icon}</span>
        <span className="font-mono text-[10px]">{checkpoint.id}</span>
        <span className="truncate">{checkpoint.name}</span>
        {checkpoint.summary && checkpoint.status === "passed" && (
          <span className="ml-auto text-[10px] opacity-70">
            {checkpoint.summary.grounded}/{checkpoint.summary.total}
          </span>
        )}
        {checkpoint.status === "blocked" && checkpoint.summary && (
          <span className="ml-auto text-[10px] text-red-400">
            {checkpoint.summary.ungrounded + checkpoint.summary.fabricated} blocked
          </span>
        )}
        {checkpoint.status === "retrying" && (
          <span className="ml-auto text-[10px]">
            retry {checkpoint.retryCount}/2
          </span>
        )}
      </button>

      {expanded && (
        <div className="mt-1 mx-1 p-3 rounded bg-zinc-900/80 border border-zinc-800 text-xs space-y-2">
          {checkpoint.summary ? (
            <>
              <div className="grid grid-cols-5 gap-2 text-center">
                <div>
                  <div className="text-emerald-400 font-mono">{checkpoint.summary.grounded}</div>
                  <div className="text-[9px] text-zinc-600">Grounded</div>
                </div>
                <div>
                  <div className="text-blue-400 font-mono">{checkpoint.summary.inferred}</div>
                  <div className="text-[9px] text-zinc-600">Inferred</div>
                </div>
                <div>
                  <div className="text-amber-400 font-mono">{checkpoint.summary.weakEvidence}</div>
                  <div className="text-[9px] text-zinc-600">Weak</div>
                </div>
                <div>
                  <div className="text-red-400 font-mono">{checkpoint.summary.ungrounded}</div>
                  <div className="text-[9px] text-zinc-600">Ungrounded</div>
                </div>
                <div>
                  <div className="text-red-500 font-mono">{checkpoint.summary.fabricated}</div>
                  <div className="text-[9px] text-zinc-600">Fabricated</div>
                </div>
              </div>

              {checkpoint.blockedClaims.length > 0 && (
                <div className="pt-2 border-t border-zinc-800 space-y-1.5">
                  <div className="text-[10px] uppercase tracking-wider text-zinc-500">Blocked Claims</div>
                  {checkpoint.blockedClaims.map((claim) => (
                    <div key={claim.claimId} className="p-2 rounded bg-red-500/5 border border-red-500/20">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-mono text-red-400 text-[10px]">{claim.claimId}</span>
                        <span className="text-[9px] px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-500">{claim.dimension}</span>
                      </div>
                      <p className="text-zinc-400 text-[11px] leading-relaxed">{claim.claimText}</p>
                      <p className="text-zinc-500 text-[10px] mt-1 italic">{claim.requiredFix}</p>
                    </div>
                  ))}
                </div>
              )}
            </>
          ) : (
            <div className="text-zinc-600 text-center py-2">
              {checkpoint.status === "pending" ? "Checkpoint not yet reached" : "Scanning claims..."}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
