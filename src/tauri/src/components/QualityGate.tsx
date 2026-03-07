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
        className="w-full max-w-lg mx-4 rounded-xl border border-blue-200 bg-white shadow-2xl"
      >
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
            <h2 id="quality-gate-title" className="text-lg font-semibold text-gray-900">
              Quality Gate Review
            </h2>
          </div>
          <p className="mt-1 text-sm text-gray-500">
            <span className="text-[#0068ff]">{stepName}</span> has completed.
            Review the results before proceeding.
          </p>
        </div>

        {gate.results.length > 0 && (
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-xs text-gray-500 mb-3">
              Gate Criteria
            </h3>
            <div className="space-y-2">
              {gate.results.map((result, i) => (
                <div
                  key={i}
                  className="flex items-start gap-2 text-sm"
                >
                  <span className={result.passed ? "text-emerald-600" : "text-red-600"}>
                    {result.passed ? "+" : "-"}
                  </span>
                  <div>
                    <span className="text-gray-700">{result.criterion}</span>
                    {result.detail && (
                      <p className="text-xs text-gray-400 mt-0.5">
                        {result.detail}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="px-6 py-4 border-b border-gray-200">
          <label htmlFor="gate-notes" className="block text-xs text-gray-500 mb-2">
            Notes (optional)
          </label>
          <textarea
            id="gate-notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Add feedback or instructions for the next step..."
            className="w-full px-3 py-2 rounded-md bg-gray-50 border border-gray-200 text-sm text-gray-700 placeholder:text-gray-400 focus:ring-2 focus:ring-[#0068ff]/40 focus:border-[#0068ff] focus:outline-none resize-none"
            rows={3}
          />
        </div>

        <div className="px-6 py-4 flex items-center justify-end gap-3">
          <button
            onClick={() => onReject(notes)}
            className="px-4 py-2 rounded-md text-sm font-medium text-red-600 border border-red-200 hover:bg-red-50 transition-colors"
          >
            Reject & Re-run
          </button>
          <button
            onClick={() => onApprove(notes)}
            className="px-4 py-2 rounded-md text-sm font-medium text-white bg-[#0068ff] hover:bg-[#0055d4] transition-colors"
          >
            Approve & Continue
          </button>
        </div>
      </div>
    </div>
  );
}
