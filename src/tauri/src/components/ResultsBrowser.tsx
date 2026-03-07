import { useState, useEffect } from "react";
import { invoke } from "@tauri-apps/api/core";
import type { OutputFile } from "../types/pipeline";
import { formatFileSize } from "../lib/cli";

interface ResultsBrowserProps {
  files: OutputFile[];
  ticker: string;
  onStartReview?: () => void;
  isReviewRunning?: boolean;
}

const FILE_ICONS: Record<string, string> = {
  json: "{ }",
  md: "M",
  html: "</>",
};

export function ResultsBrowser({ files, ticker, onStartReview, isReviewRunning }: ResultsBrowserProps) {
  const [selectedFile, setSelectedFile] = useState<OutputFile | null>(null);
  const [content, setContent] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState<string>("");
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const htmlReport = files.find((f) => f.filename.includes("final_report.html"));

  // Load executive summary when report exists
  useEffect(() => {
    if (!htmlReport) { setSummary(""); return; }
    invoke<string>("read_html_summary", { path: htmlReport.path })
      .then(setSummary)
      .catch(() => setSummary(""));
  }, [htmlReport?.path]);

  useEffect(() => {
    if (!selectedFile) return;
    // HTML files are loaded via vdafile:// protocol — no need to read content
    if (selectedFile.file_type === "html") {
      setContent("");
      setLoading(false);
      return;
    }
    setLoading(true);
    invoke<string>("read_output_file", { path: selectedFile.path })
      .then(setContent)
      .catch(() => setContent("[Error reading file]"))
      .finally(() => setLoading(false));
  }, [selectedFile]);

  const handleOpenInBrowser = () => {
    if (htmlReport) {
      invoke("open_in_browser", { path: htmlReport.path }).catch(console.error);
    }
  };

  return (
    <div className="flex h-full">
      {/* Left: collapsible file list */}
      <div className={`border-r border-zinc-800/80 flex flex-col transition-all duration-200 ${sidebarOpen ? "w-72" : "w-10"}`}>
        {/* Toggle button */}
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="px-3 py-3 border-b border-zinc-800/80 text-zinc-500 hover:text-zinc-300 transition-colors flex items-center gap-2"
        >
          <span className="text-xs">{sidebarOpen ? "◂" : "▸"}</span>
          {sidebarOpen && (
            <span className="text-xs uppercase tracking-wider">
              Files ({files.length})
            </span>
          )}
        </button>

        {sidebarOpen && (
          <>
            <div className="flex-1 overflow-y-auto px-2 py-2 space-y-1">
              {files.length === 0 ? (
                <div className="text-center text-zinc-600 text-sm py-8">
                  No output files yet
                </div>
              ) : (
                files.map((file) => (
                  <button
                    key={file.filename}
                    onClick={() => setSelectedFile(file)}
                    className={`
                      w-full text-left px-3 py-2 rounded-md text-sm transition-colors
                      ${selectedFile?.filename === file.filename
                        ? "bg-teal-500/15 ring-1 ring-teal-500/30 text-zinc-100"
                        : "hover:bg-zinc-800/60 text-zinc-400"
                      }
                    `}
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-mono text-teal-500 w-6 text-center">
                        {FILE_ICONS[file.file_type] || "?"}
                      </span>
                      <span className="truncate flex-1 font-mono text-xs">{file.filename}</span>
                      <span className="text-[10px] text-zinc-600 shrink-0">{formatFileSize(file.size)}</span>
                    </div>
                  </button>
                ))
              )}
            </div>

            {/* Actions */}
            <div className="px-3 py-3 border-t border-zinc-800/80 space-y-2">
              {htmlReport && (
                <button
                  onClick={handleOpenInBrowser}
                  className="w-full px-4 py-2 rounded-md text-sm font-medium bg-teal-500/15 text-teal-400 hover:bg-teal-500/25 transition-colors"
                >
                  Open Report in Browser
                </button>
              )}
              {onStartReview && (
                <button
                  onClick={onStartReview}
                  disabled={isReviewRunning}
                  className={`w-full px-4 py-2 rounded-md text-sm font-medium ring-1 transition-colors ${
                    isReviewRunning
                      ? "ring-zinc-700 text-zinc-600 cursor-not-allowed"
                      : "ring-teal-500/30 text-teal-400 hover:bg-teal-500/10"
                  }`}
                >
                  {isReviewRunning ? "Review Running..." : "Run Review Analysis"}
                </button>
              )}
            </div>
          </>
        )}
      </div>

      {/* Right: content area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Executive summary banner when report exists */}
        {htmlReport && !selectedFile && summary && (
          <div className="px-6 py-5 border-b border-zinc-800/80">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-lg font-semibold text-zinc-100">Executive Summary</h2>
              <button
                onClick={handleOpenInBrowser}
                className="px-3 py-1.5 rounded-md text-xs font-medium text-teal-400 ring-1 ring-teal-500/30 hover:bg-teal-500/10 transition-colors"
              >
                Open Full Report
              </button>
            </div>
            <div className="text-sm text-zinc-400 leading-relaxed whitespace-pre-line max-h-96 overflow-y-auto">
              {summary}
            </div>
          </div>
        )}

        {/* No report yet */}
        {!htmlReport && !selectedFile && (
          <div className="flex-1 flex items-center justify-center text-zinc-600 text-sm">
            {files.length === 0
              ? "Start an analysis to see results here"
              : "Pipeline in progress — final report not yet generated"}
          </div>
        )}

        {/* File preview */}
        {selectedFile && (
          <div className="flex-1 flex flex-col min-h-0">
            <div className="px-4 py-2 flex items-center justify-between bg-zinc-900/50 border-b border-zinc-800/80">
              <span className="text-xs font-mono text-zinc-400 truncate">{selectedFile.filename}</span>
              <button onClick={() => setSelectedFile(null)} className="text-xs text-zinc-600 hover:text-zinc-300">
                Close
              </button>
            </div>
            <div className="flex-1 overflow-auto px-4 py-3">
              {loading ? (
                <div className="text-zinc-600 text-sm">Loading...</div>
              ) : selectedFile.file_type === "html" ? (
                <iframe
                  src={`vdafile://localhost${selectedFile.path}`}
                  className="w-full h-full border-0 rounded bg-white"
                  title={selectedFile.filename}
                />
              ) : (
                <pre className="text-xs text-zinc-400 font-mono whitespace-pre-wrap break-words">
                  {content.slice(0, 50000)}
                  {content.length > 50000 && "\n\n[Truncated...]"}
                </pre>
              )}
            </div>
          </div>
        )}

        {/* Prompt for file selection when report exists but no file selected and no summary yet */}
        {htmlReport && !selectedFile && !summary && (
          <div className="flex-1 flex items-center justify-center text-zinc-600 text-sm">
            Select a file to preview, or open the full report in your browser
          </div>
        )}
      </div>
    </div>
  );
}
