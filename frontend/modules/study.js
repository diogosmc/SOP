export const TOPIC_STATUSES = [
  { value: "not_started", label: "Não iniciado", cls: "topic-status--not-started" },
  { value: "in_progress", label: "Em progresso", cls: "topic-status--in-progress" },
  { value: "review", label: "Revisão", cls: "topic-status--review" },
  { value: "mastered", label: "Dominado", cls: "topic-status--mastered" },
];

export const REVIEW_RATINGS = [
  { value: "again", label: "De novo", cls: "rating--again" },
  { value: "hard", label: "Difícil", cls: "rating--hard" },
  { value: "good", label: "Bom", cls: "rating--good" },
  { value: "easy", label: "Fácil", cls: "rating--easy" },
];

export const SUBJECT_COLORS = ["#8b5cf6", "#3b82f6", "#22c55e", "#f59e0b", "#ef4444", "#ec4899"];

/** @param {string} status */
export function statusLabel(status) {
  return TOPIC_STATUSES.find((s) => s.value === status)?.label || status;
}

/** @param {string} status */
export function statusClass(status) {
  return TOPIC_STATUSES.find((s) => s.value === status)?.cls || "";
}

/** @param {string} text */
export function escapeHtml(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/** @param {number} n */
export function formatMinutes(n) {
  if (n == null || Number.isNaN(Number(n))) return "0 min";
  return `${n} min`;
}
