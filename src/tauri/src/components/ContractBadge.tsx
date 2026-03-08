import { useState, useEffect, useRef } from "react";
import { invoke } from "@tauri-apps/api/core";

interface ContractResult {
  passed: boolean;
  message: string;
}

interface ContractBadgeProps {
  runDir: string | null;
  validationKey?: string | null;
  mode?: "validate" | "legacy" | "hidden";
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
  let errorLine: string | undefined;
  for (let i = lines.length - 1; i >= 0; i -= 1) {
    const line = lines[i];
    if (/Error:|Exception:|ValueError|FileNotFoundError|Missing/.test(line)) {
      errorLine = line;
      break;
    }
  }

  const summary = errorLine ?? lastLine;
  // Clean up: remove Python class prefix like "ValueError: " → just the message
  const cleaned = summary.replace(/^[\w.]*(?:Error|Exception):\s*/, "");
  return { summary: cleaned || summary, detail: message };
}

export function ContractBadge({ runDir, validationKey, mode = "validate" }: ContractBadgeProps) {
  const [state, setState] = useState<ValidationState>({ status: "idle" });
  const [tooltipVisible, setTooltipVisible] = useState(false);
  const lastValidatedKey = useRef<string | null>(null);

  useEffect(() => {
    if (mode !== "validate" || !runDir || !validationKey) {
      setState({ status: "idle" });
      lastValidatedKey.current = null;
      return;
    }

    // Cache: skip if we already validated this exact file state
    if (lastValidatedKey.current === validationKey) return;

    lastValidatedKey.current = validationKey;
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
  }, [mode, runDir, validationKey]);

  if (mode === "hidden") return null;

  if (mode === "legacy") {
    return (
      <span
        className="inline-flex items-center gap-1 px-2 py-0.5 rounded border text-[11px] font-mono
          bg-gray-50 border-gray-200 text-gray-500 select-none whitespace-nowrap"
        title="This run predates the enforced contract artifacts and is treated as a legacy run."
      >
        <span className="text-gray-400 leading-none">●</span>
        Legacy Run
      </span>
    );
  }

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
