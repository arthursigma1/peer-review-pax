import { useState, useEffect, useRef } from "react";
import type { QualityGate as QualityGateType } from "../types/pipeline";
import { PIPELINE_STEPS } from "../types/pipeline";

interface QualityGateProps {
  gate: QualityGateType;
  onApprove: (notes: string) => void;
  onReject: (notes: string) => void;
}

export function QualityGate({ gate, onApprove, onReject }: QualityGateProps) {
  const [notes, setNotes] = useState("");
  const dialogRef = useRef<HTMLDivElement>(null);
  const notesRef = useRef("");
  const stepName = PIPELINE_STEPS[gate.stepIndex]?.name ?? `Step ${gate.stepIndex + 1}`;

  // Keep notes ref in sync for Escape handler
  useEffect(() => { notesRef.current = notes; }, [notes]);

  // Focus trap and Escape key
  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    const getFocusable = () =>
      dialog.querySelectorAll<HTMLElement>(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );

    // Focus first interactive element on mount
    const els = getFocusable();
    if (els.length > 0) els[0].focus();

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        onReject(notesRef.current);
        return;
      }
      if (e.key === "Tab") {
        const focusable = getFocusable();
        if (focusable.length === 0) return;
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [onReject]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="quality-gate-title"
        className="w-full max-w-lg mx-4 rounded-xl ring-1 ring-teal-500/40 bg-zinc-900 shadow-2xl shadow-teal-500/10"
      >
        <div className="px-6 py-4 border-b border-zinc-800">
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
            <h2 id="quality-gate-title" className="text-lg font-semibold text-zinc-100">
              Quality Gate Review
            </h2>
          </div>
          <p className="mt-1 text-sm text-zinc-400">
            <span className="text-teal-400">{stepName}</span> has completed.
            Review the results before proceeding.
          </p>
        </div>

        {gate.results.length > 0 && (
          <div className="px-6 py-4 border-b border-zinc-800">
            <h3 className="text-xs uppercase tracking-wider text-zinc-400 mb-3">
              Gate Criteria
            </h3>
            <div className="space-y-2">
              {gate.results.map((result, i) => (
                <div
                  key={i}
                  className="flex items-start gap-2 text-sm"
                >
                  <span className={result.passed ? "text-emerald-400" : "text-red-400"}>
                    {result.passed ? "+" : "-"}
                  </span>
                  <div>
                    <span className="text-zinc-300">{result.criterion}</span>
                    {result.detail && (
                      <p className="text-xs text-zinc-500 mt-0.5">
                        {result.detail}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="px-6 py-4 border-b border-zinc-800">
          <label htmlFor="gate-notes" className="block text-xs uppercase tracking-wider text-zinc-400 mb-2">
            Notes (optional)
          </label>
          <textarea
            id="gate-notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Add feedback or instructions for the next step..."
            className="w-full px-3 py-2 rounded-md bg-zinc-800 ring-1 ring-zinc-700 text-sm text-zinc-200 placeholder:text-zinc-500 focus:ring-teal-500/60 focus:outline-none resize-none"
            rows={3}
          />
        </div>

        <div className="px-6 py-4 flex items-center justify-end gap-3">
          <button
            onClick={() => onReject(notes)}
            className="px-4 py-2 rounded-md text-sm font-medium text-red-400 ring-1 ring-red-500/30 hover:bg-red-500/10 transition-colors"
          >
            Reject & Re-run
          </button>
          <button
            onClick={() => onApprove(notes)}
            className="px-4 py-2 rounded-md text-sm font-medium text-zinc-900 bg-teal-400 hover:bg-teal-300 transition-colors"
          >
            Approve & Continue
          </button>
        </div>
      </div>
    </div>
  );
}
