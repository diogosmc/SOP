/** @typedef {'pending'|'in_progress'|'completed'|'cancelled'} TaskStatus */
/** @typedef {'low'|'medium'|'high'} TaskPriority */

export const TASK_STATUSES = [
  { value: "pending", label: "Pendente" },
  { value: "in_progress", label: "Em progresso" },
  { value: "completed", label: "Concluída" },
  { value: "cancelled", label: "Cancelada" },
];

export const TASK_PRIORITIES = [
  { value: "low", label: "Baixa" },
  { value: "medium", label: "Média" },
  { value: "high", label: "Alta" },
];

/** @param {TaskStatus} status */
export function statusLabel(status) {
  return TASK_STATUSES.find((item) => item.value === status)?.label || status;
}

/** @param {TaskPriority} priority */
export function priorityLabel(priority) {
  return TASK_PRIORITIES.find((item) => item.value === priority)?.label || priority;
}

/** @param {string|null|undefined} iso */
export function formatDueDate(iso) {
  if (!iso) return "—";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleString("pt-BR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** @param {string|null|undefined} iso */
export function toDatetimeLocalValue(iso) {
  if (!iso) return "";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  const pad = (n) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

/** @param {string} value */
export function fromDatetimeLocalValue(value) {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return date.toISOString();
}

/**
 * @param {object[]} tasks
 * @param {object} filters
 */
export function filterTasksClient(tasks, filters) {
  let result = [...tasks];
  const search = (filters.search || "").trim().toLowerCase();
  const priority = filters.priority || "";

  if (priority) {
    result = result.filter((task) => task.priority === priority);
  }

  if (search) {
    result = result.filter((task) => {
      const haystack = [task.title, task.description, task.category]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      return haystack.includes(search);
    });
  }

  return result;
}

/** @param {object} form */
export function taskFormToPayload(form) {
  const payload = {
    title: form.title.trim(),
    description: form.description.trim() || null,
    status: form.status,
    priority: form.priority,
    category: form.category.trim() || null,
    due_date: fromDatetimeLocalValue(form.due_date),
  };
  if (!payload.description) delete payload.description;
  if (!payload.category) delete payload.category;
  if (!payload.due_date) payload.due_date = null;
  return payload;
}
