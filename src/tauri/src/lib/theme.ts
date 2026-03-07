/**
 * Design tokens — single source of truth for the dashboard palette.
 * Light theme, finance-grade. Used by Terminal.tsx (xterm theme),
 * ResultsBrowser.tsx (iframe CSS), and as reference for Tailwind classes.
 *
 * Contrast ratios on --surface-base (#ffffff):
 *   --text-primary   (#1a1a1a)  ~16.6:1   WCAG AAA
 *   --text-secondary  (#6b7280)  ~5.5:1    WCAG AA
 *   --text-muted      (#9ca3af)  ~3.1:1    WCAG AA  (large text only, >=18px)
 *   --primary         (#0068ff)  ~4.6:1    WCAG AA
 */

export const palette = {
  // Surfaces
  surface: {
    base: "#ffffff",
    raised: "#f8f9fa",
    overlay: "#f3f4f6",
    border: "#e0e0e0",
    borderSubtle: "#e0e0e033",
  },

  // Text hierarchy
  text: {
    primary: "#1a1a1a",
    secondary: "#6b7280",
    muted: "#9ca3af",
  },

  // Accent (blue)
  accent: {
    base: "#0068ff",
    hover: "#0055d4",
    dim: "#0068ff15",
    ring: "#0068ff40",
  },

  // Status
  status: {
    success: "#10b981",
    warning: "#d97706",
    error: "#dc2626",
    info: "#0068ff",
  },
} as const;

/**
 * Shared status Tailwind class maps — used by AgentCard, StepCard dot indicators, etc.
 */
export const STATUS_TEXT: Record<string, string> = {
  idle: "text-gray-400",
  pending: "text-gray-400",
  running: "text-blue-600",
  complete: "text-emerald-600",
  failed: "text-red-600",
};

export const STATUS_DOT: Record<string, string> = {
  idle: "bg-gray-300",
  pending: "bg-gray-300",
  running: "bg-[#0068ff]",
  complete: "bg-emerald-500",
  failed: "bg-red-500",
};

/** xterm.js terminal theme — stays dark (standard convention) */
export const terminalTheme = {
  background: "#0c0c0c",
  foreground: "#a1a1aa",
  cursor: "#0068ff",
  selectionBackground: "#0068ff26",
  black: "#18181b",
  red: "#f87171",
  green: "#4ade80",
  yellow: "#facc15",
  blue: "#60a5fa",
  magenta: "#c084fc",
  cyan: "#22d3ee",
  white: "#a1a1aa",
  brightBlack: "#71717a",
  brightRed: "#fca5a5",
  brightGreen: "#86efac",
  brightYellow: "#fde68a",
  brightBlue: "#93c5fd",
  brightMagenta: "#d8b4fe",
  brightCyan: "#67e8f9",
  brightWhite: "#fafafa",
} as const;

/** Shared CSS for iframe viewers — light background with new fonts */
export const viewerBaseCSS = `
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: 'DM Sans', system-ui, sans-serif;
  background: ${palette.surface.base}; color: ${palette.text.secondary};
  font-size: 13px; line-height: 1.5; padding: 16px;
}
table { border-collapse: collapse; width: 100%; margin-bottom: 12px; }
thead th {
  background: ${palette.surface.raised}; color: ${palette.accent.base}; font-weight: 600;
  font-size: 11px; letter-spacing: 0.3px;
  padding: 10px 12px; text-align: left;
  border-bottom: 2px solid ${palette.surface.border};
  position: sticky; top: 0; z-index: 1;
}
tbody tr { border-bottom: 1px solid ${palette.surface.border}; }
tbody tr:hover { background: ${palette.surface.raised}; }
tbody tr:nth-child(even) { background: ${palette.surface.overlay}; }
tbody tr:nth-child(even):hover { background: ${palette.surface.raised}; }
th {
  color: ${palette.text.secondary}; font-weight: 500; padding: 8px 12px;
  text-align: left; white-space: nowrap; vertical-align: top;
  background: ${palette.surface.raised}; min-width: 120px;
}
td { padding: 8px 12px; vertical-align: top; max-width: 600px; word-wrap: break-word; }
td table { margin: 4px 0; font-size: 12px; }
td table th { font-size: 11px; padding: 4px 8px; min-width: 80px; }
td table td { padding: 4px 8px; }
.null { color: ${palette.text.muted}; font-style: italic; }
.truncated { color: ${palette.accent.base}; font-style: italic; text-align: center; padding: 12px; }
.nested-json {
  background: ${palette.surface.overlay}; color: ${palette.text.secondary}; padding: 8px; border-radius: 4px;
  font-size: 11px; max-height: 200px; overflow: auto; white-space: pre-wrap; word-break: break-word;
}`;

export const markdownViewerCSS = `
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: 'DM Sans', system-ui, sans-serif;
  background: ${palette.surface.base}; color: ${palette.text.primary}; padding: 24px 32px;
  font-size: 14px; line-height: 1.7; max-width: 800px;
}
h1, h2, h3, h4 { font-family: 'DM Sans', system-ui, sans-serif; color: ${palette.text.primary}; margin: 1.5em 0 0.5em; }
h1 { font-size: 1.6em; border-bottom: 1px solid ${palette.surface.border}; padding-bottom: 0.3em; }
h2 { font-size: 1.3em; color: ${palette.accent.base}; }
h3 { font-size: 1.1em; color: ${palette.text.secondary}; }
p { margin: 0.6em 0; }
ul, ol { margin: 0.5em 0 0.5em 1.5em; }
li { margin: 0.3em 0; }
code { background: ${palette.surface.overlay}; color: ${palette.accent.base}; padding: 2px 6px; border-radius: 3px; font-size: 0.9em; font-family: 'IBM Plex Mono', monospace; }
pre { background: ${palette.surface.overlay}; padding: 12px 16px; border-radius: 6px; overflow-x: auto; margin: 1em 0; }
pre code { background: none; padding: 0; }
blockquote { border-left: 3px solid ${palette.accent.base}; padding-left: 16px; color: ${palette.text.secondary}; margin: 1em 0; }
strong { color: ${palette.text.primary}; }
table { border-collapse: collapse; margin: 1em 0; width: 100%; }
table th, table td { border: 1px solid ${palette.surface.border}; padding: 8px 12px; text-align: left; }
table th { background: ${palette.surface.raised}; color: ${palette.accent.base}; }
hr { border: none; border-top: 1px solid ${palette.surface.border}; margin: 2em 0; }`;
