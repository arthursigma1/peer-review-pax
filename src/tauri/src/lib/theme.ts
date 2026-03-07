/**
 * Design tokens — single source of truth for the dashboard palette.
 * Used by Terminal.tsx (xterm theme), ResultsBrowser.tsx (iframe CSS),
 * and as reference for Tailwind classes throughout the UI.
 *
 * Contrast ratios on --surface-base (#09090b):
 *   --text-primary   (#f4f4f5)  ~18.5:1   WCAG AAA
 *   --text-secondary  (#a1a1aa)  ~6.2:1    WCAG AAA (normal text)
 *   --text-muted      (#71717a)  ~4.0:1    WCAG AA  (large text only, >=18px)
 *   --accent          (#2dd4bf)  ~10.5:1   WCAG AAA
 */

export const palette = {
  // Surfaces
  surface: {
    base: "#09090b",      // zinc-950
    raised: "#18181b",    // zinc-900
    overlay: "#27272a",   // zinc-800
    border: "#3f3f46",    // zinc-700
    borderSubtle: "#27272a33",
  },

  // Text hierarchy (all pass WCAG AA on surface.base)
  text: {
    primary: "#f4f4f5",   // zinc-100 — headings, labels
    secondary: "#a1a1aa", // zinc-400 — descriptions, meta
    muted: "#71717a",     // zinc-500 — large-text-only hints (>=18px)
  },

  // Accent (teal)
  accent: {
    base: "#2dd4bf",      // teal-400
    hover: "#5eead4",     // teal-300
    dim: "#2dd4bf26",     // teal-400/15
    ring: "#2dd4bf66",    // teal-400/40
  },

  // Status
  status: {
    success: "#4ade80",   // emerald-400
    warning: "#facc15",   // yellow-400
    error: "#f87171",     // red-400
    info: "#60a5fa",      // blue-400
  },
} as const;

/**
 * Shared status Tailwind class maps — used by AgentCard, StepCard dot indicators, etc.
 * Covers both agent statuses (idle/running/complete/failed)
 * and step statuses (pending/running/complete/failed).
 */
export const STATUS_TEXT: Record<string, string> = {
  idle: "text-zinc-500",
  pending: "text-zinc-500",
  running: "text-teal-400",
  complete: "text-emerald-400",
  failed: "text-red-400",
};

export const STATUS_DOT: Record<string, string> = {
  idle: "bg-zinc-600",
  pending: "bg-zinc-600",
  running: "bg-teal-400",
  complete: "bg-emerald-400",
  failed: "bg-red-400",
};

/** xterm.js terminal theme — derived from palette tokens */
export const terminalTheme = {
  background: "#0c0c0c",
  foreground: palette.text.secondary,
  cursor: palette.accent.base,
  selectionBackground: palette.accent.dim,
  black: palette.surface.raised,
  red: palette.status.error,
  green: palette.status.success,
  yellow: palette.status.warning,
  blue: palette.status.info,
  magenta: "#c084fc",
  cyan: palette.accent.base,
  white: palette.text.secondary,
  brightBlack: palette.text.muted,
  brightRed: "#fca5a5",
  brightGreen: "#86efac",
  brightYellow: "#fde68a",
  brightBlue: "#93c5fd",
  brightMagenta: "#d8b4fe",
  brightCyan: palette.accent.hover,
  brightWhite: "#fafafa",
} as const;

/** Shared CSS for iframe viewers — uses palette tokens for consistency */
export const viewerBaseCSS = `
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: ${palette.surface.base}; color: ${palette.text.secondary};
  font-size: 13px; line-height: 1.5; padding: 16px;
}
table { border-collapse: collapse; width: 100%; margin-bottom: 12px; }
thead th {
  background: ${palette.surface.raised}; color: ${palette.accent.base}; font-weight: 600;
  text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;
  padding: 10px 12px; text-align: left;
  border-bottom: 2px solid ${palette.accent.dim};
  position: sticky; top: 0; z-index: 1;
}
tbody tr { border-bottom: 1px solid ${palette.surface.overlay}; }
tbody tr:hover { background: ${palette.surface.raised}; }
tbody tr:nth-child(even) { background: #111114; }
tbody tr:nth-child(even):hover { background: ${palette.surface.raised}; }
th {
  color: ${palette.text.secondary}; font-weight: 500; padding: 8px 12px;
  text-align: left; white-space: nowrap; vertical-align: top;
  background: #141418; min-width: 120px;
}
td { padding: 8px 12px; vertical-align: top; max-width: 600px; word-wrap: break-word; }
td table { margin: 4px 0; font-size: 12px; }
td table th { font-size: 11px; padding: 4px 8px; min-width: 80px; }
td table td { padding: 4px 8px; }
.null { color: ${palette.text.muted}; font-style: italic; }
.truncated { color: ${palette.accent.base}; font-style: italic; text-align: center; padding: 12px; }
.nested-json {
  background: ${palette.surface.raised}; color: ${palette.text.secondary}; padding: 8px; border-radius: 4px;
  font-size: 11px; max-height: 200px; overflow: auto; white-space: pre-wrap; word-break: break-word;
}`;

export const markdownViewerCSS = `
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: Georgia, "Times New Roman", serif;
  background: ${palette.surface.base}; color: ${palette.text.secondary}; padding: 24px 32px;
  font-size: 14px; line-height: 1.7; max-width: 800px;
}
h1, h2, h3, h4 { font-family: -apple-system, BlinkMacSystemFont, sans-serif; color: ${palette.text.primary}; margin: 1.5em 0 0.5em; }
h1 { font-size: 1.6em; border-bottom: 1px solid ${palette.surface.overlay}; padding-bottom: 0.3em; }
h2 { font-size: 1.3em; color: ${palette.accent.base}; }
h3 { font-size: 1.1em; color: ${palette.text.secondary}; }
p { margin: 0.6em 0; }
ul, ol { margin: 0.5em 0 0.5em 1.5em; }
li { margin: 0.3em 0; }
code { background: ${palette.surface.raised}; color: ${palette.accent.base}; padding: 2px 6px; border-radius: 3px; font-size: 0.9em; }
pre { background: ${palette.surface.raised}; padding: 12px 16px; border-radius: 6px; overflow-x: auto; margin: 1em 0; }
pre code { background: none; padding: 0; }
blockquote { border-left: 3px solid ${palette.accent.base}; padding-left: 16px; color: ${palette.text.secondary}; margin: 1em 0; }
strong { color: ${palette.text.primary}; }
table { border-collapse: collapse; margin: 1em 0; width: 100%; }
table th, table td { border: 1px solid ${palette.surface.overlay}; padding: 8px 12px; text-align: left; }
table th { background: ${palette.surface.raised}; color: ${palette.accent.base}; }
hr { border: none; border-top: 1px solid ${palette.surface.overlay}; margin: 2em 0; }`;
