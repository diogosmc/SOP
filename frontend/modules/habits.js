export const HABIT_TYPES = [
  { value: "positive", label: "Positivo", icon: "↑" },
  { value: "negative", label: "Negativo", icon: "↓" },
];

export const HABIT_ACTIVE_OPTIONS = [
  { value: "", label: "Todos" },
  { value: "true", label: "Ativos" },
  { value: "false", label: "Inativos" },
];

/** @param {string} type */
export function typeLabel(type) {
  return HABIT_TYPES.find((item) => item.value === type)?.label || type;
}

/** @param {string} type */
export function typeIcon(type) {
  return HABIT_TYPES.find((item) => item.value === type)?.icon || "•";
}

/**
 * @param {object[]} habits
 * @param {object} filters
 */
export function filterHabitsClient(habits, filters) {
  let result = [...habits];
  const search = (filters.search || "").trim().toLowerCase();

  if (search) {
    result = result.filter((habit) => {
      const haystack = [habit.name, habit.description, habit.frequency]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      return haystack.includes(search);
    });
  }

  return result;
}

/** @param {object} form */
export function habitFormToPayload(form) {
  const payload = {
    name: form.name.trim(),
    description: form.description.trim() || null,
    type: form.type,
    frequency: form.frequency.trim() || null,
    active: form.active === true || form.active === "true",
  };
  if (!payload.description) delete payload.description;
  if (!payload.frequency) delete payload.frequency;
  return payload;
}
