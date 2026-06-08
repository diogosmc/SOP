export const TRANSACTION_TYPES = [
  { value: "income", label: "Receita" },
  { value: "expense", label: "Despesa" },
];

export const DEFAULT_CATEGORIES = {
  income: ["Salário", "Freelance", "Investimentos", "Outros"],
  expense: ["Alimentação", "Moradia", "Transporte", "Saúde", "Lazer", "Outros"],
};

/** @param {string} type */
export function typeLabel(type) {
  return TRANSACTION_TYPES.find((item) => item.value === type)?.label || type;
}

/** @param {number|string} value */
export function formatBRL(value) {
  const num = Number(value);
  if (Number.isNaN(num)) return "—";
  return num.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

/** @param {string|null|undefined} iso */
export function formatDateBR(iso) {
  if (!iso) return "—";
  const date = new Date(`${iso}T12:00:00`);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleDateString("pt-BR");
}

/** @returns {{ start: string, end: string }} */
export function currentMonthRange() {
  const now = new Date();
  const start = new Date(now.getFullYear(), now.getMonth(), 1);
  const end = new Date(now.getFullYear(), now.getMonth() + 1, 0);
  const toIso = (d) =>
    `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  return { start: toIso(start), end: toIso(end) };
}

/** @param {object} form */
export function transactionFormToPayload(form) {
  return {
    description: form.description.trim(),
    amount: String(form.amount).replace(",", "."),
    type: form.type,
    category: form.category.trim(),
    transaction_date: form.transaction_date,
    notes: form.notes?.trim() || null,
  };
}

/** @param {string} text */
export function escapeHtml(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/** @param {Record<string, unknown>} filters */
export function buildFinanceQuery(filters) {
  const query = {};
  if (filters.page) query.page = filters.page;
  if (filters.page_size) query.page_size = filters.page_size;
  if (filters.type) query.type = filters.type;
  if (filters.category) query.category = filters.category;
  if (filters.start_date) query.start_date = filters.start_date;
  if (filters.end_date) query.end_date = filters.end_date;
  if (filters.search) query.search = filters.search;
  return query;
}
