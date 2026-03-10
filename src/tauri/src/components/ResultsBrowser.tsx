import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { invoke } from "@tauri-apps/api/core";
import type { OutputFile } from "../types/pipeline";
import { FOLDER_LABELS } from "../types/pipeline";
import { formatFileSize } from "../lib/cli";
import { viewerBaseCSS, markdownViewerCSS } from "../lib/theme";
import { AnalysisInsights } from "./AnalysisInsights";
import { DataQualityHeatmap } from "./DataQualityHeatmap";
import { ContractBadge } from "./ContractBadge";
import { RunSelector } from "./RunSelector";


interface ResultsBrowserProps {
  files: OutputFile[];
  ticker: string;
  onStartReview?: () => void;
  isReviewRunning?: boolean;
  runs?: string[];
  selectedRun?: string | null;
  onSelectRun?: (run: string) => void;
  watcherError?: string | null;
}

const FILE_ICONS: Record<string, { icon: string; color: string }> = {
  json: { icon: "{ }", color: "text-blue-500" },
  md: { icon: "M", color: "text-blue-600" },
  html: { icon: "</>", color: "text-amber-500" },
};


function markdownToHtml(md: string): string {
  // Process code blocks first (before escaping)
  const codeBlocks: string[] = [];
  let processed = md.replace(/```[\w]*\n([\s\S]*?)```/g, (_match, code) => {
    codeBlocks.push(code);
    return `%%CODEBLOCK_${codeBlocks.length - 1}%%`;
  });

  // Escape HTML
  processed = processed
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  // Restore code blocks (already escaped inside)
  processed = processed.replace(/%%CODEBLOCK_(\d+)%%/g, (_m, idx) => {
    const code = codeBlocks[parseInt(idx)]
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    return `<pre><code>${code}</code></pre>`;
  });

  // Markdown tables
  processed = processed.replace(
    /^(\|.+\|)\n(\|[\s:|-]+\|)\n((?:\|.+\|\n?)+)/gm,
    (_match, headerRow: string, _separator: string, bodyRows: string) => {
      const headers = headerRow.split("|").filter((c: string) => c.trim()).map((c: string) => `<th>${c.trim()}</th>`).join("");
      const rows = bodyRows.trim().split("\n").map((row: string) => {
        const cells = row.split("|").filter((c: string) => c.trim()).map((c: string) => `<td>${c.trim()}</td>`).join("");
        return `<tr>${cells}</tr>`;
      }).join("");
      return `<table><thead><tr>${headers}</tr></thead><tbody>${rows}</tbody></table>`;
    }
  );

  let html = processed
    // Headers
    .replace(/^#### (.+)$/gm, "<h4>$1</h4>")
    .replace(/^### (.+)$/gm, "<h3>$1</h3>")
    .replace(/^## (.+)$/gm, "<h2>$1</h2>")
    .replace(/^# (.+)$/gm, "<h1>$1</h1>")
    // Bold & italic
    .replace(/\*\*\*(.+?)\*\*\*/g, "<strong><em>$1</em></strong>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    // Inline code
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    // Blockquotes
    .replace(/^&gt; (.+)$/gm, "<blockquote>$1</blockquote>")
    // Horizontal rules
    .replace(/^---$/gm, "<hr>")
    // Ordered lists
    .replace(/^\d+\.\s+(.+)$/gm, "<oli>$1</oli>")
    // Unordered lists
    .replace(/^[-*]\s+(.+)$/gm, "<uli>$1</uli>")
    // Paragraphs (lines not already wrapped in a tag)
    .replace(/^(?!<[hluopbt]|<oli|<uli|<hr|<pre|<block|<table)(.+)$/gm, "<p>$1</p>");

  // Wrap consecutive <uli> in <ul> and <oli> in <ol>
  html = html.replace(/(?:<uli>[\s\S]*?<\/uli>\s*)+/g, (match) =>
    `<ul>${match.replace(/<\/?uli>/g, (t) => t.replace("uli", "li"))}</ul>`
  );
  html = html.replace(/(?:<oli>[\s\S]*?<\/oli>\s*)+/g, (match) =>
    `<ol>${match.replace(/<\/?oli>/g, (t) => t.replace("oli", "li"))}</ol>`
  );

  return html;
}

function highlightInHtml(html: string, query: string): { html: string; count: number } {
  if (!query || query.length < 2) return { html, count: 0 };
  let count = 0;
  const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const regex = new RegExp(escaped, "gi");
  const result = html.replace(
    /(<[^>]*>)|([^<]+)/g,
    (_match, tag: string | undefined, text: string | undefined) => {
      if (tag) return tag;
      if (!text) return "";
      return text.replace(regex, (m: string) => {
        count++;
        return `<mark style="background:#fde68a;padding:0 1px;border-radius:2px">${m}</mark>`;
      });
    }
  );
  return { html: result, count };
}

// Script injected into viewer iframes to enable scroll-to-mark navigation
const MARK_NAV_SCRIPT = `
<script>
(function(){
  var current = -1;
  function go(idx) {
    var marks = document.querySelectorAll('mark');
    if (!marks.length) return;
    if (marks[current]) marks[current].style.background = '#fde68a';
    current = ((idx % marks.length) + marks.length) % marks.length;
    marks[current].style.background = '#f59e0b';
    marks[current].scrollIntoView({ block: 'center', behavior: 'smooth' });
  }
  window.addEventListener('message', function(e) {
    if (e.data && e.data.type === 'scrollToMark') go(e.data.index);
  });
  setTimeout(function(){ if(document.querySelectorAll('mark').length) go(0); }, 50);
})();
</script>`;

function buildViewerSrcDoc(css: string, body: string, includeNavScript: boolean): string {
  return `<!DOCTYPE html><html><head><style>${css}</style></head><body>${body}${includeNavScript ? MARK_NAV_SCRIPT : ""}</body></html>`;
}

export function ResultsBrowser({ files, ticker: _ticker, onStartReview, isReviewRunning, runs, selectedRun, onSelectRun, watcherError }: ResultsBrowserProps) {
  const [selectedFile, setSelectedFile] = useState<OutputFile | null>(null);
  const [content, setContent] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState<string>("");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [editMode, setEditMode] = useState(false);
  const [insightsTab, setInsightsTab] = useState<"summary" | "data-quality">("summary");
  const [editContent, setEditContent] = useState("");
  const [saving, setSaving] = useState(false);
  const [collapsedFolders, setCollapsedFolders] = useState<Set<string>>(new Set());
  const [exporting, setExporting] = useState(false);

  // Search state
  const [fileFilter, setFileFilter] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchMatchCount, setSearchMatchCount] = useState(0);
  const [currentMatchIndex, setCurrentMatchIndex] = useState(0);
  const [globalResults, setGlobalResults] = useState<{ file: OutputFile; snippets: string[] }[]>([]);
  const [globalSearching, setGlobalSearching] = useState(false);
  const viewerIframeRef = useRef<HTMLIFrameElement>(null);
  const preRef = useRef<HTMLPreElement>(null);

  // Memoize highlighting so it doesn't re-run on every render
  const { viewerHtml, matchCount } = useMemo(() => {
    if (!selectedFile || !content || selectedFile.file_type === "html") {
      return { viewerHtml: "", matchCount: 0 };
    }
    if (selectedFile.file_type === "md" && editMode) {
      return { viewerHtml: "", matchCount: 0 };
    }
    let result: { html: string; count: number };
    if (selectedFile.file_type === "json") {
      result = highlightInHtml(content, searchQuery);
    } else if (selectedFile.file_type === "md") {
      result = highlightInHtml(markdownToHtml(content), searchQuery);
    } else {
      const escaped = content.slice(0, 50000)
        .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
      result = highlightInHtml(escaped, searchQuery);
    }
    return { viewerHtml: result.html, matchCount: result.count };
  }, [content, searchQuery, selectedFile, editMode]);

  // Sync derived match count to state (consumed by nav buttons)
  useEffect(() => { setSearchMatchCount(matchCount); }, [matchCount]);

  // Navigate to a specific match index (works for both iframes and pre)
  const navigateToMatch = useCallback((idx: number) => {
    if (searchMatchCount === 0) return;
    const wrapped = ((idx % searchMatchCount) + searchMatchCount) % searchMatchCount;
    setCurrentMatchIndex(wrapped);
    // iframe-based viewers
    if (viewerIframeRef.current?.contentWindow) {
      viewerIframeRef.current.contentWindow.postMessage({ type: "scrollToMark", index: wrapped }, "*");
    }
    // pre-based viewer
    if (preRef.current) {
      const marks = preRef.current.querySelectorAll("mark");
      marks.forEach((m, i) => {
        (m as HTMLElement).style.background = i === wrapped ? "#f59e0b" : "#fde68a";
      });
      marks[wrapped]?.scrollIntoView({ block: "center", behavior: "smooth" });
    }
  }, [searchMatchCount]);

  // Reset match index when search query or match count changes
  useEffect(() => { setCurrentMatchIndex(0); }, [searchQuery, searchMatchCount]);

  // Auto-scroll to first match in <pre> viewer after render
  useEffect(() => {
    if (matchCount > 0 && preRef.current) {
      const first = preRef.current.querySelector("mark");
      if (first) {
        (first as HTMLElement).style.background = "#f59e0b";
        first.scrollIntoView({ block: "center", behavior: "smooth" });
      }
    }
  }, [matchCount]);

  const htmlReport = files.find((f) => f.filename === "final_report.html");
  const hasStatisticsMetadata = files.some(
    (f) => f.folder === "3-analysis" && f.filename === "statistics_metadata.json"
  );
  const hasReportMetadata = files.some(
    (f) => f.folder === "5-playbook" && f.filename === "report_metadata.json"
  );
  const hasPlaybookArtifacts = files.some((f) => f.folder === "5-playbook");

  // Derive run directory from any file path: /path/to/run-dir/step-folder/file.json → /path/to/run-dir
  const runDir = files.length > 0
    ? files[0].path.split("/").slice(0, -2).join("/")
    : null;
  const latestModified = files.length > 0
    ? Math.max(...files.map((f) => f.modified))
    : null;
  const contractMode: "validate" | "legacy" | "hidden" =
    hasStatisticsMetadata && hasReportMetadata
      ? "validate"
      : hasPlaybookArtifacts
      ? "legacy"
      : "hidden";
  const contractValidationKey =
    contractMode === "validate" && runDir && latestModified !== null
      ? `${runDir}:${latestModified}`
      : null;

  // Group files by folder
  const grouped = files.reduce<Record<string, OutputFile[]>>((acc, f) => {
    const key = f.folder || "root";
    if (!acc[key]) acc[key] = [];
    acc[key].push(f);
    return acc;
  }, {});

  // Apply file filter
  const filteredGrouped = fileFilter
    ? Object.fromEntries(
        Object.entries(grouped)
          .map(([folder, folderFiles]) => [
            folder,
            folderFiles.filter((f) => f.filename.toLowerCase().includes(fileFilter.toLowerCase())),
          ])
          .filter(([, folderFiles]) => (folderFiles as OutputFile[]).length > 0)
      )
    : grouped;
  const filteredFolderOrder = Object.keys(filteredGrouped).sort();

  useEffect(() => {
    if (!htmlReport) { setSummary(""); return; }
    invoke<string>("read_html_summary", { path: htmlReport.path })
      .then(setSummary)
      .catch(() => setSummary(""));
  }, [htmlReport?.path]);

  useEffect(() => {
    setSearchQuery("");
    setFileFilter("");
    setSelectedFile(null);
  }, [selectedRun]);

  useEffect(() => {
    if (!selectedFile) return;
    setSearchQuery("");
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

  // Global search across all files when no file is selected
  useEffect(() => {
    if (selectedFile || !searchQuery || searchQuery.length < 2) {
      setGlobalResults([]);
      return;
    }
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      setGlobalSearching(true);
      const results: { file: OutputFile; snippets: string[] }[] = [];
      const q = searchQuery.toLowerCase();
      for (const file of files) {
        if (controller.signal.aborted) break;
        if (file.file_type === "html") continue;
        try {
          const raw = await invoke<string>("read_output_file", { path: file.path });
          const lines = raw.split("\n");
          const snippets = lines
            .filter((line) => line.toLowerCase().includes(q))
            .slice(0, 3)
            .map((line) => {
              const idx = line.toLowerCase().indexOf(q);
              const start = Math.max(0, idx - 60);
              const end = Math.min(line.length, idx + searchQuery.length + 60);
              return (start > 0 ? "..." : "") + line.slice(start, end).trim() + (end < line.length ? "..." : "");
            });
          if (snippets.length > 0) results.push({ file, snippets });
        } catch { /* skip */ }
      }
      if (!controller.signal.aborted) {
        setGlobalResults(results);
        setGlobalSearching(false);
      }
    }, 300);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [searchQuery, selectedFile, files]);

  const handleOpenInBrowser = () => {
    if (htmlReport) {
      invoke("open_in_browser", { path: htmlReport.path }).catch(console.error);
    }
  };

  const handleExportPdf = async () => {
    if (!selectedFile || selectedFile.file_type !== "html") return;
    setExporting(true);
    try {
      await invoke<string>("export_html_to_pdf", { htmlPath: selectedFile.path });
    } catch (err) {
      console.error("PDF export failed:", err);
    } finally {
      setExporting(false);
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
      <div className={`border-r border-gray-200 flex flex-col transition-all duration-200 ${sidebarOpen ? "w-72" : "w-10"}`}>
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          aria-expanded={sidebarOpen}
          aria-label={sidebarOpen ? "Collapse file list" : "Expand file list"}
          className="px-3 py-3 border-b border-gray-200 text-gray-500 hover:text-gray-700 transition-colors flex items-center gap-2"
        >
          <span className="text-xs">{sidebarOpen ? "◂" : "▸"}</span>
          {sidebarOpen && (
            <span className="text-xs">
              Files ({files.length})
            </span>
          )}
        </button>

        {sidebarOpen && (
          <>
            {/* Run selector */}
            {runs && runs.length > 0 && (
              <div className="px-3 py-2 border-b border-gray-200">
                <RunSelector
                  runs={runs}
                  value={selectedRun}
                  onChange={(r) => onSelectRun?.(r)}
                />
              </div>
            )}

            {/* File filter */}
            <div className="px-3 py-1.5 border-b border-gray-200">
              <input
                type="text"
                value={fileFilter}
                onChange={(e) => setFileFilter(e.target.value)}
                placeholder="Filter files..."
                className="w-full px-2.5 py-1.5 rounded bg-gray-50 border border-gray-200 text-xs font-mono text-gray-700 placeholder:text-gray-400 focus:ring-1 focus:ring-[#0068ff]/40 focus:border-[#0068ff] focus:outline-none"
              />
            </div>

            <div className="flex-1 overflow-y-auto px-2 py-2 space-y-0.5">
              {files.length === 0 ? (
                <div className="text-center text-gray-400 text-sm py-8">
                  No output files yet
                </div>
              ) : filteredFolderOrder.length === 0 ? (
                <div className="text-center text-gray-400 text-xs py-8 font-mono">
                  No files match "{fileFilter}"
                </div>
              ) : (
                filteredFolderOrder.map((folder) => (
                  <div key={folder}>
                    <button
                      onClick={() => toggleFolder(folder)}
                      aria-expanded={!collapsedFolders.has(folder)}
                      className="w-full text-left px-2 py-1.5 text-[10px] text-gray-500 hover:text-gray-700 flex items-center gap-1.5 mt-2 first:mt-0"
                    >
                      <span>{collapsedFolders.has(folder) ? "▸" : "▾"}</span>
                      <span>{FOLDER_LABELS[folder] || folder}</span>
                      <span className="text-gray-300 ml-auto">{filteredGrouped[folder].length}</span>
                    </button>
                    {!collapsedFolders.has(folder) && filteredGrouped[folder].map((file) => (
                      <button
                        key={file.path}
                        onClick={() => setSelectedFile(file)}
                        className={`
                          w-full text-left px-3 py-1.5 rounded-md text-sm transition-colors ml-1
                          ${selectedFile?.path === file.path
                            ? "bg-blue-50 border border-blue-200 text-gray-900"
                            : "hover:bg-gray-50 text-gray-600"
                          }
                        `}
                      >
                        <div className="flex items-center gap-2">
                          <span className={`text-[10px] font-mono w-5 text-center shrink-0 ${FILE_ICONS[file.file_type]?.color ?? "text-gray-400"}`}>
                            {FILE_ICONS[file.file_type]?.icon ?? "?"}
                          </span>
                          <span className="truncate flex-1 font-mono text-xs">{file.filename}</span>
                          <span className="text-[10px] text-gray-400 shrink-0">{formatFileSize(file.size)}</span>
                        </div>
                      </button>
                    ))}
                  </div>
                ))
              )}
            </div>

            {/* Actions */}
            <div className="px-3 py-3 border-t border-gray-200 space-y-2">
              {htmlReport && (
                <button
                  onClick={handleOpenInBrowser}
                  className="w-full px-4 py-2 rounded-md text-sm font-medium bg-[#0068ff] text-white hover:bg-[#0055d4] transition-colors"
                >
                  Open Report in Browser
                </button>
              )}
              {onStartReview && (
                <button
                  onClick={onStartReview}
                  disabled={isReviewRunning}
                  className={`w-full px-4 py-2 rounded-md text-sm font-medium border transition-colors ${
                    isReviewRunning
                      ? "border-gray-300 text-gray-400 cursor-not-allowed"
                      : "border-[#0068ff]/30 text-[#0068ff] hover:bg-blue-50"
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
        {/* Watcher error banner */}
        {watcherError && (
          <div role="alert" className="px-4 py-2 bg-red-50 border-b border-red-200 flex items-center gap-2 text-sm text-red-600">
            <span className="shrink-0">File watcher error:</span>
            <span className="truncate text-red-500/70">{watcherError}</span>
          </div>
        )}

        {/* Unified search bar — visible when files exist */}
        {files.length > 0 && (
          <div className="px-4 py-2 border-b border-gray-200 bg-white flex items-center gap-2">
            <svg className="w-3.5 h-3.5 text-gray-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={selectedFile ? "Search in file..." : "Search across all files..."}
              className="flex-1 px-1 py-1 text-xs font-mono text-gray-700 placeholder:text-gray-400 focus:outline-none bg-transparent"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery("")}
                className="text-gray-400 hover:text-gray-600 text-xs px-1"
              >
                ✕
              </button>
            )}
            {selectedFile && searchQuery.length >= 2 && searchMatchCount > 0 && (
              <div className="flex items-center gap-1">
                <span className="text-[10px] text-gray-400 font-mono whitespace-nowrap">
                  {currentMatchIndex + 1}/{searchMatchCount}
                </span>
                <button
                  onClick={() => navigateToMatch(currentMatchIndex - 1)}
                  className="w-5 h-5 flex items-center justify-center rounded text-gray-400 hover:text-gray-600 hover:bg-gray-100 text-xs"
                  title="Previous match"
                >
                  ↑
                </button>
                <button
                  onClick={() => navigateToMatch(currentMatchIndex + 1)}
                  className="w-5 h-5 flex items-center justify-center rounded text-gray-400 hover:text-gray-600 hover:bg-gray-100 text-xs"
                  title="Next match"
                >
                  ↓
                </button>
              </div>
            )}
            {selectedFile && searchQuery.length >= 2 && searchMatchCount === 0 && (
              <span className="text-[10px] text-gray-400 font-mono whitespace-nowrap">
                0 matches
              </span>
            )}
            {!selectedFile && globalSearching && (
              <span className="text-[10px] text-gray-400 font-mono">searching...</span>
            )}
            {!selectedFile && !globalSearching && searchQuery.length >= 2 && (
              <span className="text-[10px] text-gray-400 font-mono whitespace-nowrap">
                {globalResults.length} file{globalResults.length !== 1 ? "s" : ""}
              </span>
            )}
          </div>
        )}

        {/* Global search results */}
        {!selectedFile && searchQuery.length >= 2 && globalResults.length > 0 && (
          <div className="flex-1 overflow-y-auto">
            <div className="px-4 py-3 space-y-2">
              {globalResults.map(({ file, snippets }) => (
                <button
                  key={file.path}
                  onClick={() => { setSelectedFile(file); }}
                  className="w-full text-left px-3 py-2.5 rounded-md border border-gray-200 hover:border-[#0068ff]/40 hover:bg-blue-50/30 transition-colors"
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`text-[10px] font-mono ${FILE_ICONS[file.file_type]?.color ?? "text-gray-400"}`}>
                      {FILE_ICONS[file.file_type]?.icon ?? "?"}
                    </span>
                    <span className="text-xs font-mono text-gray-700">{file.filename}</span>
                    <span className="text-[10px] text-gray-400">{FOLDER_LABELS[file.folder] || file.folder}</span>
                  </div>
                  {snippets.map((s, i) => (
                    <div key={i} className="text-[11px] text-gray-500 font-mono truncate pl-5">
                      {s}
                    </div>
                  ))}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Global search empty state */}
        {!selectedFile && searchQuery.length >= 2 && !globalSearching && globalResults.length === 0 && (
          <div className="flex-1 flex items-center justify-center text-gray-400 text-xs font-mono">
            No matches for "{searchQuery}"
          </div>
        )}

        {/* Insights area: Summary / Data Quality tabs */}
        {!selectedFile && files.length > 0 && !(searchQuery.length >= 2 && globalResults.length > 0) && !(searchQuery.length >= 2 && !globalSearching && globalResults.length === 0) && (
          <>
            {/* Tab bar */}
            <div className="flex items-center justify-between px-6 bg-gray-50/50 border-b border-gray-200">
              <div className="flex items-center gap-0">
                <button
                  onClick={() => setInsightsTab("summary")}
                  className={`px-3 py-2 text-[11px] font-medium border-b-2 transition-colors ${
                    insightsTab === "summary"
                      ? "border-[#0068ff] text-[#0068ff]"
                      : "border-transparent text-gray-500 hover:text-gray-700"
                  }`}
                >
                  Summary
                </button>
                <button
                  onClick={() => setInsightsTab("data-quality")}
                  className={`px-3 py-2 text-[11px] font-medium border-b-2 transition-colors ${
                    insightsTab === "data-quality"
                      ? "border-[#0068ff] text-[#0068ff]"
                      : "border-transparent text-gray-500 hover:text-gray-700"
                  }`}
                >
                  Data Quality
                </button>
              </div>
              <ContractBadge
                runDir={contractMode === "validate" ? runDir : null}
                validationKey={contractValidationKey}
                mode={contractMode}
              />
            </div>

            {/* Tab content */}
            <div className="flex-1 overflow-y-auto">
              {insightsTab === "summary" ? (
                <>
                  {/* Executive summary banner */}
                  {htmlReport && summary && (
                    <div className="px-6 py-5 border-b border-gray-200">
                      <div className="flex items-center justify-between mb-3">
                        <h2 className="text-lg font-semibold text-gray-900">Executive Summary</h2>
                        <button
                          onClick={handleOpenInBrowser}
                          className="px-3 py-1.5 rounded-md text-xs font-medium text-[#0068ff] border border-blue-200 hover:bg-blue-50 transition-colors"
                        >
                          Open Full Report
                        </button>
                      </div>
                      <div className="text-sm text-gray-600 leading-relaxed whitespace-pre-line max-h-96 overflow-y-auto">
                        {summary}
                      </div>
                    </div>
                  )}

                  {/* Statistical confidence + checkpoint trend */}
                  <AnalysisInsights files={files} />

                  {/* No report yet */}
                  {!htmlReport && (
                    <div className="flex-1 flex items-center justify-center text-gray-400 text-sm py-16">
                      Pipeline in progress — final report not yet generated
                    </div>
                  )}
                </>
              ) : (
                <DataQualityHeatmap files={files} />
              )}
            </div>
          </>
        )}

        {/* Empty state: no files at all */}
        {!selectedFile && files.length === 0 && (
          <div className="flex-1 flex items-center justify-center text-gray-400 text-sm">
            Start an analysis to see results here
          </div>
        )}

        {/* File preview */}
        {selectedFile && (
          <div className="flex-1 flex flex-col min-h-0">
            <div className="px-4 py-2 flex items-center justify-between bg-gray-50 border-b border-gray-200">
              <div className="flex items-center gap-2 min-w-0">
                <span className="text-[10px] text-gray-500 shrink-0">{FOLDER_LABELS[selectedFile.folder] || selectedFile.folder}</span>
                <span className="text-gray-300">/</span>
                <span className="text-xs font-mono text-gray-500 truncate">{selectedFile.filename}</span>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                {selectedFile.file_type === "html" && (
                  <button
                    onClick={handleExportPdf}
                    disabled={exporting}
                    className={`text-xs px-3 py-2 rounded transition-colors ${
                      exporting
                        ? "text-gray-400 cursor-not-allowed"
                        : "text-[#0068ff] hover:text-[#0055d4] hover:bg-blue-50"
                    }`}
                  >
                    {exporting ? "Exporting..." : "Export PDF"}
                  </button>
                )}
                {selectedFile.file_type === "md" && !editMode && (
                  <button onClick={handleEdit} className="text-xs text-[#0068ff] hover:text-[#0055d4] px-3 py-2 rounded hover:bg-blue-50">
                    Edit
                  </button>
                )}
                {editMode && (
                  <>
                    <button
                      onClick={handleSave}
                      disabled={saving}
                      className="text-xs text-[#0068ff] hover:text-[#0055d4] px-3 py-2 rounded hover:bg-blue-50"
                    >
                      {saving ? "Saving..." : "Save"}
                    </button>
                    <button
                      onClick={() => setEditMode(false)}
                      className="text-xs text-gray-400 hover:text-gray-700 px-3 py-2"
                    >
                      Cancel
                    </button>
                  </>
                )}
                <button onClick={() => setSelectedFile(null)} className="text-xs text-gray-400 hover:text-gray-700 px-3 py-2">
                  Close
                </button>
              </div>
            </div>
            <div className="flex-1 overflow-auto">
              {loading ? (
                <div className="text-gray-400 text-sm p-4">Loading...</div>
              ) : selectedFile.file_type === "html" ? (
                <iframe
                  src={`vdafile://localhost${selectedFile.path}`}
                  className="w-full h-full border-0 rounded bg-white"
                  title={selectedFile.filename}
                />
              ) : selectedFile.file_type === "json" ? (
                <iframe
                  ref={viewerIframeRef}
                  srcDoc={buildViewerSrcDoc(viewerBaseCSS, viewerHtml, searchQuery.length >= 2)}
                  className="w-full h-full border-0 rounded"
                  title={selectedFile.filename}
                />
              ) : selectedFile.file_type === "md" && editMode ? (
                <div className="flex h-full">
                  <textarea
                    value={editContent}
                    onChange={(e) => setEditContent(e.target.value)}
                    className="w-1/2 h-full bg-gray-50 text-gray-700 font-mono text-xs p-4 resize-none border-r border-gray-200 focus:outline-none"
                    spellCheck={false}
                  />
                  <iframe
                    srcDoc={buildViewerSrcDoc(markdownViewerCSS, markdownToHtml(editContent), false)}
                    className="w-1/2 h-full border-0"
                    title="Preview"
                  />
                </div>
              ) : selectedFile.file_type === "md" ? (
                <iframe
                  ref={viewerIframeRef}
                  srcDoc={buildViewerSrcDoc(markdownViewerCSS, viewerHtml, searchQuery.length >= 2)}
                  className="w-full h-full border-0 rounded"
                  title={selectedFile.filename}
                />
              ) : viewerHtml ? (
                <pre
                  ref={preRef}
                  className="text-xs text-gray-600 font-mono whitespace-pre-wrap break-words p-4"
                  dangerouslySetInnerHTML={{ __html: viewerHtml + (content.length > 50000 ? "\n\n[Truncated...]" : "") }}
                />
              ) : (
                <pre className="text-xs text-gray-600 font-mono whitespace-pre-wrap break-words p-4">
                  {content.slice(0, 50000)}
                  {content.length > 50000 && "\n\n[Truncated...]"}
                </pre>
              )}
            </div>
          </div>
        )}

        {htmlReport && !selectedFile && !summary && (
          <div className="flex-1 flex items-center justify-center text-gray-400 text-sm">
            Select a file to preview, or open the full report in your browser
          </div>
        )}
      </div>
    </div>
  );
}
