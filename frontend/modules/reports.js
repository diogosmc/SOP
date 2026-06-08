export function escapeHtml(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/** @param {string|null|undefined} iso */
export function formatDateBR(iso) {
  if (!iso) return "—";
  const date = new Date(`${iso}T12:00:00`);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleDateString("pt-BR");
}

/** @param {number|null|undefined} value */
export function formatScore(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "—";
  return `${Number(value).toLocaleString("pt-BR")}/100`;
}

/** @param {Array<{date: string, value: number}>} rows */
export function chartLabels(rows) {
  return rows.map((r) => formatDateBR(r.date));
}

/** @param {Array<{date: string, value: number}>} rows */
export function chartValues(rows) {
  return rows.map((r) => Number(r.value) || 0);
}

export const TASK_STATUS_LABELS = {
  pending: "Pendentes",
  in_progress: "Em progresso",
  completed: "Concluídas",
  cancelled: "Canceladas",
};
