import { useState } from "react";
import { open } from "@tauri-apps/plugin-dialog";

interface ToneUploadProps {
  files: string[];
  onFilesChanged: (files: string[]) => void;
  extractionStatus: "idle" | "extracting" | "done" | "error";
}

export function ToneUpload({ files, onFilesChanged, extractionStatus }: ToneUploadProps) {
  const handleAddFiles = async () => {
    const selected = await open({
      multiple: true,
      filters: [{ name: "Documents", extensions: ["pdf", "docx", "txt", "md"] }],
    });
    if (!selected) return;
    const picked = Array.isArray(selected) ? selected : [selected];
    const merged = [...files, ...picked].slice(0, 3);
    onFilesChanged(merged);
  };

  const handleRemoveFile = (index: number) => {
    const updated = files.filter((_, i) => i !== index);
    onFilesChanged(updated);
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <label className="block text-xs uppercase tracking-wider text-zinc-400">
          Tone Reference (optional)
        </label>
        {extractionStatus === "extracting" && (
          <span className="flex items-center gap-1.5 text-[10px] text-zinc-400">
            <span className="w-1.5 h-1.5 rounded-full bg-zinc-400 animate-pulse" />
            Extracting...
          </span>
        )}
        {extractionStatus === "done" && (
          <span className="flex items-center gap-1.5 text-[10px] text-emerald-400">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            Custom tone captured
          </span>
        )}
        {extractionStatus === "error" && (
          <span className="flex items-center gap-1.5 text-[10px] text-red-400">
            <span className="w-1.5 h-1.5 rounded-full bg-red-400" />
            Extraction failed
          </span>
        )}
      </div>

      {files.length === 0 ? (
        <DropZone
          label="Drop PDF, DOCX, or text files"
          sublabel="Reports, memos, or writing samples"
          selectedPath={null}
          onDrop={(e) => {
            e.preventDefault();
            const droppedFiles = e.dataTransfer.files;
            if (droppedFiles.length > 0) {
              const paths = Array.from(droppedFiles)
                .map((f) => (f as any).path as string)
                .filter(Boolean)
                .slice(0, 3);
              if (paths.length > 0) onFilesChanged(paths);
            }
          }}
          onBrowse={handleAddFiles}
          onClear={() => {}}
        />
      ) : (
        <div className="rounded-lg border border-zinc-700 bg-zinc-800/30 px-4 py-3 space-y-2">
          {files.map((filePath, i) => {
            const filename = filePath.split("/").pop() ?? filePath;
            return (
              <div key={i} className="flex items-center justify-between">
                <div className="min-w-0 flex-1">
                  <p className="text-xs font-mono text-zinc-300 truncate">{filename}</p>
                </div>
                <button
                  onClick={() => handleRemoveFile(i)}
                  className="ml-2 text-xs text-zinc-500 hover:text-red-400 transition-colors shrink-0 px-2 py-2"
                >
                  Clear
                </button>
              </div>
            );
          })}
          {files.length < 3 && (
            <button
              onClick={handleAddFiles}
              className="w-full mt-1 px-3 py-1.5 rounded-md text-xs font-medium text-teal-400 ring-1 ring-teal-500/30 hover:bg-teal-500/10 transition-colors"
            >
              Add File ({files.length}/3)
            </button>
          )}
        </div>
      )}
    </div>
  );
}

interface SourcePaths {
  sellSide: string | null;
  consulting: string | null;
}

interface SourceUploadProps {
  sources: SourcePaths;
  onSourcesChanged: (sources: SourcePaths) => void;
}

export type { SourcePaths };

export function SourceUpload({ sources, onSourcesChanged }: SourceUploadProps) {
  const handlePickFolder = async (type: "sellSide" | "consulting") => {
    const selected = await open({
      directory: true,
      multiple: false,
      title: type === "sellSide" ? "Select Sell-Side Research Folder" : "Select Consulting Research Folder",
    });
    if (selected) {
      onSourcesChanged({ ...sources, [type]: selected as string });
    }
  };

  const handleDrop = (e: React.DragEvent, type: "sellSide" | "consulting") => {
    e.preventDefault();
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      const path = (files[0] as any).path;
      if (path) {
        const dir = path.substring(0, path.lastIndexOf("/"));
        onSourcesChanged({ ...sources, [type]: dir });
      }
    }
  };

  return (
    <div className="space-y-3">
      <label className="block text-xs uppercase tracking-wider text-zinc-400">
        Supplemental Sources (optional)
      </label>

      <DropZone
        label="Sell-Side Research"
        sublabel="Equity research, broker reports, analyst notes"
        selectedPath={sources.sellSide}
        onDrop={(e) => handleDrop(e, "sellSide")}
        onBrowse={() => handlePickFolder("sellSide")}
        onClear={() => onSourcesChanged({ ...sources, sellSide: null })}
      />

      <DropZone
        label="Consulting & Industry Research"
        sublabel="McKinsey, BCG, Bain, Preqin, industry reports"
        selectedPath={sources.consulting}
        onDrop={(e) => handleDrop(e, "consulting")}
        onBrowse={() => handlePickFolder("consulting")}
        onClear={() => onSourcesChanged({ ...sources, consulting: null })}
      />
    </div>
  );
}

function DropZone({
  label,
  sublabel,
  selectedPath,
  onDrop,
  onBrowse,
  onClear,
}: {
  label: string;
  sublabel: string;
  selectedPath: string | null;
  onDrop: (e: React.DragEvent) => void;
  onBrowse: () => void;
  onClear: () => void;
}) {
  const [dragOver, setDragOver] = useState(false);

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => { setDragOver(false); onDrop(e); }}
      className={`
        relative px-4 py-4 rounded-lg border-2 border-dashed transition-all
        ${dragOver
          ? "border-teal-400 bg-teal-500/5"
          : selectedPath
          ? "border-emerald-500/40 bg-emerald-500/5"
          : "border-zinc-700 bg-zinc-800/30"
        }
      `}
    >
      {selectedPath ? (
        <div className="flex items-center justify-between">
          <div className="min-w-0 flex-1">
            <p className="text-sm text-emerald-400">{label}</p>
            <p className="text-xs text-zinc-500 font-mono mt-0.5 truncate">{selectedPath}</p>
          </div>
          <button onClick={onClear} className="ml-2 text-xs text-zinc-500 hover:text-red-400 transition-colors shrink-0 px-2 py-2">
            Clear
          </button>
        </div>
      ) : (
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-zinc-300">{label}</p>
            <p className="text-xs text-zinc-500 mt-0.5">{sublabel}</p>
          </div>
          <button
            onClick={onBrowse}
            className="ml-3 px-3 py-1.5 rounded-md text-xs font-medium text-teal-400 ring-1 ring-teal-500/30 hover:bg-teal-500/10 transition-colors shrink-0"
          >
            Browse
          </button>
        </div>
      )}
    </div>
  );
}
