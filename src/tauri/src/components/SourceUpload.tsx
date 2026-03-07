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
        <label className="block text-xs text-gray-500">
          Tone Reference (optional)
        </label>
        {extractionStatus === "extracting" && (
          <span className="flex items-center gap-1.5 text-[10px] text-gray-400">
            <span className="w-1.5 h-1.5 rounded-full bg-gray-400 animate-pulse" />
            Extracting...
          </span>
        )}
        {extractionStatus === "done" && (
          <span className="flex items-center gap-1.5 text-[10px] text-emerald-600">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            Custom tone captured
          </span>
        )}
        {extractionStatus === "error" && (
          <span className="flex items-center gap-1.5 text-[10px] text-red-600">
            <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
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
        <div className="rounded-lg border border-gray-200 bg-gray-50 px-4 py-3 space-y-2">
          {files.map((filePath, i) => {
            const filename = filePath.split("/").pop() ?? filePath;
            return (
              <div key={i} className="flex items-center justify-between">
                <div className="min-w-0 flex-1">
                  <p className="text-xs font-mono text-gray-700 truncate">{filename}</p>
                </div>
                <button
                  onClick={() => handleRemoveFile(i)}
                  className="ml-2 text-xs text-gray-400 hover:text-red-500 transition-colors shrink-0 px-2 py-2"
                >
                  Clear
                </button>
              </div>
            );
          })}
          {files.length < 3 && (
            <button
              onClick={handleAddFiles}
              className="w-full mt-1 px-3 py-1.5 rounded-md text-xs font-medium text-[#0068ff] border border-blue-200 hover:bg-blue-50 transition-colors"
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
      <label className="block text-xs text-gray-500">
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
          ? "border-[#0068ff] bg-blue-50"
          : selectedPath
          ? "border-emerald-400 bg-emerald-50"
          : "border-gray-300 bg-gray-50"
        }
      `}
    >
      {selectedPath ? (
        <div className="flex items-center justify-between">
          <div className="min-w-0 flex-1">
            <p className="text-sm text-emerald-600">{label}</p>
            <p className="text-xs text-gray-500 font-mono mt-0.5 truncate">{selectedPath}</p>
          </div>
          <button onClick={onClear} className="ml-2 text-xs text-gray-400 hover:text-red-500 transition-colors shrink-0 px-2 py-2">
            Clear
          </button>
        </div>
      ) : (
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-700">{label}</p>
            <p className="text-xs text-gray-400 mt-0.5">{sublabel}</p>
          </div>
          <button
            onClick={onBrowse}
            className="ml-3 px-3 py-1.5 rounded-md text-xs font-medium text-[#0068ff] border border-blue-200 hover:bg-blue-50 transition-colors shrink-0"
          >
            Browse
          </button>
        </div>
      )}
    </div>
  );
}
