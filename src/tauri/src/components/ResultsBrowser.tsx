import { useState, useEffect } from "react";
import { invoke } from "@tauri-apps/api/core";
import type { OutputFile } from "../types/pipeline";
import { FOLDER_LABELS } from "../types/pipeline";
import { formatFileSize } from "../lib/cli";

interface ResultsBrowserProps {
  files: OutputFile[];
  ticker: string;
  onStartReview?: () => void;
  isReviewRunning?: boolean;
  runs?: string[];
  selectedRun?: string | null;
  onSelectRun?: (run: string) => void;
}

const FILE_ICONS: Record<string, string> = {
  json: "{ }",
  md: "M",
  html: "</>",
};

const JSON_TABLE_CSS = `
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: #0c0c0f; color: #d4d4d8; padding: 16px;
  font-size: 13px; line-height: 1.5;
}
table { border-collapse: collapse; width: 100%; margin-bottom: 12px; }
thead th {
  background: #1a1a2e; color: #5eead4; font-weight: 600;
  text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;
  padding: 10px 12px; text-align: left;
  border-bottom: 2px solid #2dd4bf33;
  position: sticky; top: 0; z-index: 1;
}
tbody tr { border-bottom: 1px solid #27272a; }
tbody tr:hover { background: #18181b; }
tbody tr:nth-child(even) { background: #111114; }
tbody tr:nth-child(even):hover { background: #18181b; }
th {
  color: #a1a1aa; font-weight: 500; padding: 8px 12px;
  text-align: left; white-space: nowrap; vertical-align: top;
  background: #141418; min-width: 120px;
}
td { padding: 8px 12px; vertical-align: top; max-width: 600px; word-wrap: break-word; }
td table { margin: 4px 0; font-size: 12px; }
td table th { font-size: 11px; padding: 4px 8px; min-width: 80px; }
td table td { padding: 4px 8px; }
.null { color: #52525b; font-style: italic; }
.truncated { color: #5eead4; font-style: italic; text-align: center; padding: 12px; }
.nested-json {
  background: #18181b; color: #a1a1aa; padding: 8px; border-radius: 4px;
  font-size: 11px; max-height: 200px; overflow: auto; white-space: pre-wrap; word-break: break-word;
}`;

const MD_VIEWER_CSS = `
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: Georgia, "Times New Roman", serif;
  background: #0c0c0f; color: #d4d4d8; padding: 24px 32px;
  font-size: 14px; line-height: 1.7; max-width: 800px;
}
h1, h2, h3, h4 { font-family: -apple-system, BlinkMacSystemFont, sans-serif; color: #f4f4f5; margin: 1.5em 0 0.5em; }
h1 { font-size: 1.6em; border-bottom: 1px solid #27272a; padding-bottom: 0.3em; }
h2 { font-size: 1.3em; color: #5eead4; }
h3 { font-size: 1.1em; color: #a1a1aa; }
p { margin: 0.6em 0; }
ul, ol { margin: 0.5em 0 0.5em 1.5em; }
li { margin: 0.3em 0; }
code { background: #1a1a2e; color: #5eead4; padding: 2px 6px; border-radius: 3px; font-size: 0.9em; }
pre { background: #1a1a2e; padding: 12px 16px; border-radius: 6px; overflow-x: auto; margin: 1em 0; }
pre code { background: none; padding: 0; }
blockquote { border-left: 3px solid #5eead4; padding-left: 16px; color: #a1a1aa; margin: 1em 0; }
strong { color: #f4f4f5; }
table { border-collapse: collapse; margin: 1em 0; width: 100%; }
table th, table td { border: 1px solid #27272a; padding: 8px 12px; text-align: left; }
table th { background: #1a1a2e; color: #5eead4; }
hr { border: none; border-top: 1px solid #27272a; margin: 2em 0; }`;

function markdownToHtml(md: string): string {
  let html = md
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    // Headers
    .replace(/^#### (.+)$/gm, "<h4>$1</h4>")
    .replace(/^### (.+)$/gm, "<h3>$1</h3>")
    .replace(/^## (.+)$/gm, "<h2>$1</h2>")
    .replace(/^# (.+)$/gm, "<h1>$1</h1>")
    // Bold & italic
    .replace(/\*\*\*(.+?)\*\*\*/g, "<strong><em>$1</em></strong>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    // Code blocks
    .replace(/```[\w]*\n([\s\S]*?)```/g, "<pre><code>$1</code></pre>")
    // Inline code
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    // Blockquotes
    .replace(/^&gt; (.+)$/gm, "<blockquote>$1</blockquote>")
    // Horizontal rules
    .replace(/^---$/gm, "<hr>")
    // Unordered lists
    .replace(/^- (.+)$/gm, "<li>$1</li>")
    // Paragraphs (lines not already wrapped)
    .replace(/^(?!<[hluopb]|<li|<hr|<pre|<block)(.+)$/gm, "<p>$1</p>");
  // Wrap consecutive <li> in <ul>
  html = html.replace(/(<li>[\s\S]*?<\/li>)(?:\s*(?=<li>))?/g, "$1");
  html = html.replace(/(?:<li>[\s\S]*?<\/li>\s*)+/g, (match) => `<ul>${match}</ul>`);
  return html;
}

export function ResultsBrowser({ files, ticker: _ticker, onStartReview, isReviewRunning, runs, selectedRun, onSelectRun }: ResultsBrowserProps) {
  const [selectedFile, setSelectedFile] = useState<OutputFile | null>(null);
  const [content, setContent] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState<string>("");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [editMode, setEditMode] = useState(false);
  const [editContent, setEditContent] = useState("");
  const [saving, setSaving] = useState(false);
  const [collapsedFolders, setCollapsedFolders] = useState<Set<string>>(new Set());

  const htmlReport = files.find((f) => f.filename === "final_report.html");

  // Group files by folder
  const grouped = files.reduce<Record<string, OutputFile[]>>((acc, f) => {
    const key = f.folder || "root";
    if (!acc[key]) acc[key] = [];
    acc[key].push(f);
    return acc;
  }, {});
  const folderOrder = Object.keys(grouped).sort();

  useEffect(() => {
    if (!htmlReport) { setSummary(""); return; }
    invoke<string>("read_html_summary", { path: htmlReport.path })
      .then(setSummary)
      .catch(() => setSummary(""));
  }, [htmlReport?.path]);

  useEffect(() => {
    if (!selectedFile) return;
    setEditMode(false);
    if (selectedFile.file_type === "html") {
      setContent("");
      setLoading(false);
      return;
    }
    setLoading(true);
    if (selectedFile.file_type === "json") {
      invoke<string>("read_json_as_table", { path: selectedFile.path })
        .then(setContent)
        .catch(() => setContent("[Error reading file]"))
        .finally(() => setLoading(false));
    } else {
      invoke<string>("read_output_file", { path: selectedFile.path })
        .then(setContent)
        .catch(() => setContent("[Error reading file]"))
        .finally(() => setLoading(false));
    }
  }, [selectedFile]);

  const handleOpenInBrowser = () => {
    if (htmlReport) {
      invoke("open_in_browser", { path: htmlReport.path }).catch(console.error);
    }
  };

  const handleEdit = () => {
    setEditContent(content);
    setEditMode(true);
  };

  const handleSave = async () => {
    if (!selectedFile) return;
    setSaving(true);
    try {
      await invoke("write_output_file", { path: selectedFile.path, content: editContent });
      setContent(editContent);
      setEditMode(false);
    } catch (err) {
      console.error("Failed to save:", err);
    } finally {
      setSaving(false);
    }
  };

  const toggleFolder = (folder: string) => {
    setCollapsedFolders((prev) => {
      const next = new Set(prev);
      if (next.has(folder)) next.delete(folder);
      else next.add(folder);
      return next;
    });
  };

  return (
    <div className="flex h-full">
      {/* Left: collapsible file list */}
      <div className={`border-r border-zinc-800/80 flex flex-col transition-all duration-200 ${sidebarOpen ? "w-72" : "w-10"}`}>
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
            {/* Run selector */}
            {runs && runs.length > 0 && (
              <div className="px-3 py-2 border-b border-zinc-800/80">
                <select
                  value={selectedRun || ""}
                  onChange={(e) => onSelectRun?.(e.target.value)}
                  className="w-full px-2 py-1.5 rounded bg-zinc-800/60 ring-1 ring-zinc-700 text-xs text-zinc-300 font-mono focus:ring-teal-500/60 focus:outline-none appearance-none"
                >
                  {runs.map((r) => (
                    <option key={r} value={r}>{r}</option>
                  ))}
                </select>
              </div>
            )}

            <div className="flex-1 overflow-y-auto px-2 py-2 space-y-0.5">
              {files.length === 0 ? (
                <div className="text-center text-zinc-600 text-sm py-8">
                  No output files yet
                </div>
              ) : (
                folderOrder.map((folder) => (
                  <div key={folder}>
                    <button
                      onClick={() => toggleFolder(folder)}
                      className="w-full text-left px-2 py-1.5 text-[10px] uppercase tracking-wider text-zinc-500 hover:text-zinc-300 flex items-center gap-1.5 mt-2 first:mt-0"
                    >
                      <span>{collapsedFolders.has(folder) ? "▸" : "▾"}</span>
                      <span>{FOLDER_LABELS[folder] || folder}</span>
                      <span className="text-zinc-700 ml-auto">{grouped[folder].length}</span>
                    </button>
                    {!collapsedFolders.has(folder) && grouped[folder].map((file) => (
                      <button
                        key={file.path}
                        onClick={() => setSelectedFile(file)}
                        className={`
                          w-full text-left px-3 py-1.5 rounded-md text-sm transition-colors ml-1
                          ${selectedFile?.path === file.path
                            ? "bg-teal-500/15 ring-1 ring-teal-500/30 text-zinc-100"
                            : "hover:bg-zinc-800/60 text-zinc-400"
                          }
                        `}
                      >
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] font-mono text-teal-500 w-5 text-center shrink-0">
                            {FILE_ICONS[file.file_type] || "?"}
                          </span>
                          <span className="truncate flex-1 font-mono text-xs">{file.filename}</span>
                          <span className="text-[10px] text-zinc-600 shrink-0">{formatFileSize(file.size)}</span>
                        </div>
                      </button>
                    ))}
                  </div>
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
        {/* Executive summary banner */}
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
              <div className="flex items-center gap-2 min-w-0">
                <span className="text-[10px] text-zinc-600 shrink-0">{FOLDER_LABELS[selectedFile.folder] || selectedFile.folder}</span>
                <span className="text-zinc-700">/</span>
                <span className="text-xs font-mono text-zinc-400 truncate">{selectedFile.filename}</span>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                {selectedFile.file_type === "md" && !editMode && (
                  <button onClick={handleEdit} className="text-xs text-teal-400 hover:text-teal-300 px-2 py-1 rounded hover:bg-teal-500/10">
                    Edit
                  </button>
                )}
                {editMode && (
                  <>
                    <button
                      onClick={handleSave}
                      disabled={saving}
                      className="text-xs text-teal-400 hover:text-teal-300 px-2 py-1 rounded hover:bg-teal-500/10"
                    >
                      {saving ? "Saving..." : "Save"}
                    </button>
                    <button
                      onClick={() => setEditMode(false)}
                      className="text-xs text-zinc-500 hover:text-zinc-300 px-2 py-1"
                    >
                      Cancel
                    </button>
                  </>
                )}
                <button onClick={() => setSelectedFile(null)} className="text-xs text-zinc-600 hover:text-zinc-300">
                  Close
                </button>
              </div>
            </div>
            <div className="flex-1 overflow-auto">
              {loading ? (
                <div className="text-zinc-600 text-sm p-4">Loading...</div>
              ) : selectedFile.file_type === "html" ? (
                <iframe
                  src={`vdafile://localhost${selectedFile.path}`}
                  className="w-full h-full border-0 rounded bg-white"
                  title={selectedFile.filename}
                />
              ) : selectedFile.file_type === "json" ? (
                <iframe
                  srcDoc={`<!DOCTYPE html><html><head><style>${JSON_TABLE_CSS}</style></head><body>${content}</body></html>`}
                  className="w-full h-full border-0 rounded"
                  title={selectedFile.filename}
                />
              ) : selectedFile.file_type === "md" && editMode ? (
                <div className="flex h-full">
                  <textarea
                    value={editContent}
                    onChange={(e) => setEditContent(e.target.value)}
                    className="w-1/2 h-full bg-zinc-900 text-zinc-300 font-mono text-xs p-4 resize-none border-r border-zinc-800 focus:outline-none"
                    spellCheck={false}
                  />
                  <iframe
                    srcDoc={`<!DOCTYPE html><html><head><style>${MD_VIEWER_CSS}</style></head><body>${markdownToHtml(editContent)}</body></html>`}
                    className="w-1/2 h-full border-0"
                    title="Preview"
                  />
                </div>
              ) : selectedFile.file_type === "md" ? (
                <iframe
                  srcDoc={`<!DOCTYPE html><html><head><style>${MD_VIEWER_CSS}</style></head><body>${markdownToHtml(content)}</body></html>`}
                  className="w-full h-full border-0 rounded"
                  title={selectedFile.filename}
                />
              ) : (
                <pre className="text-xs text-zinc-400 font-mono whitespace-pre-wrap break-words p-4">
                  {content.slice(0, 50000)}
                  {content.length > 50000 && "\n\n[Truncated...]"}
                </pre>
              )}
            </div>
          </div>
        )}

        {htmlReport && !selectedFile && !summary && (
          <div className="flex-1 flex items-center justify-center text-zinc-600 text-sm">
            Select a file to preview, or open the full report in your browser
          </div>
        )}
      </div>
    </div>
  );
}
