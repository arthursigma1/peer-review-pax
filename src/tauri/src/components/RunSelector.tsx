interface RunSelectorProps {
  runs: string[];
  value: string | null | undefined;
  onChange: (run: string) => void;
  className?: string;
}

export function RunSelector({ runs, value, onChange, className }: RunSelectorProps) {
  return (
    <select
      aria-label="Select analysis run"
      value={value || ""}
      onChange={(e) => onChange(e.target.value)}
      className={className ?? "w-full px-2 py-1.5 rounded bg-gray-50 border border-gray-200 text-xs text-gray-700 font-mono focus:ring-2 focus:ring-[#0068ff]/40 focus:border-[#0068ff] focus:outline-none appearance-none"}
    >
      {runs.map((r) => (
        <option key={r} value={r}>{r}</option>
      ))}
    </select>
  );
}
