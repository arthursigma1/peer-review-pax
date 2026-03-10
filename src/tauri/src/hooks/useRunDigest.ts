import { useState, useEffect } from "react";
import { invoke } from "@tauri-apps/api/core";

export interface DriverDigest {
  id: string;
  name: string;
  rho: number;
  classification: string;
}

export interface RunDigest {
  peers_total: number | null;
  metrics_total: number | null;
  drivers: DriverDigest[];
  stable_drivers_count: number | null;
  plays_total: number;
  anti_patterns_total: number;
  play_assessments_total: number;
  play_assessments_high: number;
  top_principles: string[];
  has_report: boolean;
}

export function useRunDigest(ticker: string | null, runDate: string | null): RunDigest | null {
  const [digest, setDigest] = useState<RunDigest | null>(null);

  useEffect(() => {
    if (!ticker || !runDate) { setDigest(null); return; }
    invoke<RunDigest>("read_run_digest", { ticker, runDate })
      .then((d) => { console.log("[useRunDigest] got digest", d); setDigest(d); })
      .catch((e) => { console.error("[useRunDigest] failed", e); setDigest(null); });
  }, [ticker, runDate]);

  return digest;
}
