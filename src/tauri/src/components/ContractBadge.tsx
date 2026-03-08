import { useState, useEffect, useRef } from "react";
import { invoke } from "@tauri-apps/api/core";

interface ContractResult {
  passed: boolean;
  message: string;
}

interface ContractBadgeProps {
  runDir: string | null;
}

type ValidationState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "pass"; message: string }
  | { status: "fail"; message: string };

function parseErrorMessage(message: string): { summary: string; detail: string } {
  const lines = message.split("\n").map((l) => l.trim()).filter((l) => l.length > 0);
  if (lines.length === 0) return { summary: "Validation failed", detail: message };

  // Python tracebacks: the actual error is the LAST line(s)
  // Look for "Error:" or "Exception:" pattern in the last lines
  const lastLine = lines[lines.length - 1];
  const errorLine = lines.findLast((l) =>
    /Error:|Exception:|ValueError|FileNotFoundError|Missing/.test(l)
  );

  const summary = errorLine ?? lastLine;
  // Clean up: remove Python class prefix like "ValueError: " → just the message
  const cleaned = summary.replace(/^[\w.]*(?:Error|Exception):\s*/, "");
  return { summary: cleaned || summary, detail: message };
}

export function ContractBadge({ runDir }: ContractBadgeProps) {
  const [state, setState] = useState<ValidationState>({ status: "idle" });
  const [tooltipVisible, setTooltipVisible] = useState(false);
  const lastValidatedDir = useRef<string | null>(null);

  useEffect(() => {
    if (!runDir) {
      setState({ status: "idle" });
      lastValidatedDir.current = null;
      return;
    }

    // Cache: skip if we already validated this directory
    if (lastValidatedDir.current === runDir) return;

    lastValidatedDir.current = runDir;
    setState({ status: "loading" });

    invoke<ContractResult>("validate_contract", { runDir })
      .then((result) => {
        if (result.passed) {
          setState({ status: "pass", message: result.message });
        } else {
          setState({ status: "fail", message: result.message });
        }
      })
      .catch((err: unknown) => {
        const errMsg =
          typeof err === "string"
            ? err
            : err instanceof Error
            ? err.message
            : "Validation error";
        setState({ status: "fail", message: errMsg });
      });
  }, [runDir]);

  if (state.status === "idle") return null;

  if (state.status === "loading") {
    return (
      <span className="inline-flex items-center text-[11px] text-gray-400 font-mono select-none">
        Validating...
      </span>
    );
  }

  if (state.status === "pass") {
    return (
      <span
        className="inline-flex items-center gap-1 px-2 py-0.5 rounded border text-[11px] font-mono
          bg-emerald-50 border-emerald-200 text-emerald-700 select-none whitespace-nowrap"
        title={state.message || "All contract checks passed"}
      >
        <span className="text-emerald-500 leading-none">●</span>
        Contract PASS
      </span>
    );
  }

  // fail state
  const { summary: errorSummary } = parseErrorMessage(state.message);

  return (
    <span className="relative inline-flex items-center select-none">
      <span
        className="inline-flex items-center gap-1 px-2 py-0.5 rounded border text-[11px] font-mono
          bg-red-50 border-red-200 text-red-700 cursor-default whitespace-nowrap"
        onMouseEnter={() => setTooltipVisible(true)}
        onMouseLeave={() => setTooltipVisible(false)}
      >
        <span className="text-red-500 leading-none">●</span>
        Contract FAIL
      </span>

      {tooltipVisible && (
        <span
          className="absolute bottom-full right-0 mb-1.5 z-50
            bg-gray-900 text-gray-100 text-[11px] font-mono leading-relaxed
            rounded-md px-3 py-2.5 shadow-lg
            whitespace-pre-wrap break-words pointer-events-none"
          style={{ minWidth: "280px", maxWidth: "480px" }}
        >
          {errorSummary}
        </span>
      )}
    </span>
  );
}
