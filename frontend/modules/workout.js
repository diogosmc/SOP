export const WORKOUT_OBJECTIVES = [
  { value: "hypertrophy", label: "Hipertrofia" },
  { value: "fat_loss", label: "Emagrecimento" },
  { value: "strength", label: "Força" },
  { value: "health", label: "Saúde" },
  { value: "other", label: "Outro" },
];

export const EXERCISE_TYPES = [
  { value: "strength", label: "Força" },
  { value: "cardio", label: "Cardio" },
  { value: "mobility", label: "Mobilidade" },
  { value: "functional", label: "Funcional" },
];

export const DISCLAIMER =
  "Use este módulo para organização. Para orientação profissional, consulte um educador físico ou profissional de saúde.";

/** @param {string} value */
export function objectiveLabel(value) {
  return WORKOUT_OBJECTIVES.find((o) => o.value === value)?.label || value;
}

/** @param {string} text */
export function escapeHtml(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/** @param {number|string|null|undefined} value */
export function formatKg(value) {
  const num = Number(value);
  if (Number.isNaN(num)) return "—";
  return `${num.toLocaleString("pt-BR")} kg`;
}

/** @param {string|null|undefined} iso */
export function formatDateBR(iso) {
  if (!iso) return "—";
  const date = new Date(`${iso}T12:00:00`);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleDateString("pt-BR");
}

/** @param {number|string|null|undefined} value */
export function formatVolume(value) {
  const num = Number(value);
  if (Number.isNaN(num)) return "—";
  return `${num.toLocaleString("pt-BR")} kg·rep`;
}

/** @param {Array<object>} points */
export function maxLoadByDate(points) {
  const map = new Map();
  points.forEach((p) => {
    const key = p.date;
    const load = Number(p.load_kg) || 0;
    map.set(key, Math.max(map.get(key) || 0, load));
  });
  return [...map.entries()].sort((a, b) => a[0].localeCompare(b[0]));
}
