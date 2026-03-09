/**
 * Returns today's date as a YYYY-MM-DD string using the local timezone.
 * Uses local-time components (not toISOString) to avoid midnight UTC mismatches
 * for users in negative-offset timezones (e.g. Brazil UTC-3).
 */
export function todayISO(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}
