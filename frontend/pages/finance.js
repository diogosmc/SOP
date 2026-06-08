import {
  Chart,
  BarController,
  BarElement,
  CategoryScale,
  LinearScale,
  LineController,
  LineElement,
  PointElement,
  Legend,
  Tooltip,
} from "chart.js";
import {
  createFinanceTransaction,
  deleteFinanceTransaction,
  getFinanceByCategory,
  getFinanceByDay,
  getFinanceSummary,
  listFinanceTransactions,
  updateFinanceTransaction,
} from "../services/api.js";
import {
  currentMonthRange,
  DEFAULT_CATEGORIES,
  escapeHtml,
  formatBRL,
  formatDateBR,
  TRANSACTION_TYPES,
  transactionFormToPayload,
  typeLabel,
} from "../modules/finance.js";
import { renderLoading } from "../components/loading.js";

Chart.register(
  BarController,
  BarElement,
  CategoryScale,
  LinearScale,
  LineController,
  LineElement,
  PointElement,
  Legend,
  Tooltip
);

const PAGE_SIZE = 20;

/** @returns {HTMLElement} */
export function renderFinancePage() {
  const month = currentMonthRange();
  const page = document.createElement("section");
  page.className = "page page--finance";
  page.innerHTML = `
    <div class="page__intro page__intro--row">
      <div>
        <h2 class="page__heading">Finanças</h2>
        <p class="page__description">Receitas, despesas e saldo do período selecionado.</p>
      </div>
      <button type="button" class="btn btn--primary" data-action="new-transaction">Nova transação</button>
    </div>
    <div class="finance-summary card-grid" data-role="summary-cards"></div>
    <div class="finance-toolbar">
      <label class="field field--search">
        <span class="field__label">Buscar</span>
        <input type="search" class="field__input" placeholder="Descrição, categoria..." data-filter="search" />
      </label>
      <label class="field">
        <span class="field__label">Tipo</span>
        <select class="field__input" data-filter="type">
          <option value="">Todos</option>
          ${TRANSACTION_TYPES.map((t) => `<option value="${t.value}">${t.label}</option>`).join("")}
        </select>
      </label>
      <label class="field">
        <span class="field__label">Categoria</span>
        <input type="text" class="field__input" placeholder="Ex: Alimentação" data-filter="category" />
      </label>
      <label class="field">
        <span class="field__label">Início</span>
        <input type="date" class="field__input" data-filter="start_date" value="${month.start}" />
      </label>
      <label class="field">
        <span class="field__label">Fim</span>
        <input type="date" class="field__input" data-filter="end_date" value="${month.end}" />
      </label>
    </div>
    <div class="finance-charts">
      <div class="finance-chart-card">
        <h3 class="finance-chart-card__title">Por categoria</h3>
        <canvas data-role="chart-category" height="220"></canvas>
      </div>
      <div class="finance-chart-card">
        <h3 class="finance-chart-card__title">Por dia</h3>
        <canvas data-role="chart-day" height="220"></canvas>
      </div>
    </div>
    <div class="finance-table-wrap" data-role="table-wrap"></div>
    <div class="finance-footer" data-role="footer"></div>
    <div class="modal-backdrop" data-role="modal-backdrop" hidden></div>
    <div class="modal" data-role="modal" hidden aria-modal="true" role="dialog">
      <div class="modal__panel modal__panel--wide">
        <header class="modal__header">
          <h3 class="modal__title" data-role="modal-title">Nova transação</h3>
          <button type="button" class="btn btn--ghost btn--icon" data-action="close-modal">✕</button>
        </header>
        <form class="modal__body" data-role="tx-form">
          <label class="field">
            <span class="field__label">Descrição *</span>
            <input type="text" name="description" class="field__input" required maxlength="500" />
          </label>
          <div class="field-row">
            <label class="field">
              <span class="field__label">Valor (R$) *</span>
              <input type="number" name="amount" class="field__input" required min="0.01" step="0.01" />
            </label>
            <label class="field">
              <span class="field__label">Tipo *</span>
              <select name="type" class="field__input" data-role="type-select">
                ${TRANSACTION_TYPES.map((t) => `<option value="${t.value}">${t.label}</option>`).join("")}
              </select>
            </label>
          </div>
          <div class="field-row">
            <label class="field">
              <span class="field__label">Categoria *</span>
              <select name="category" class="field__input" data-role="category-select"></select>
            </label>
            <label class="field">
              <span class="field__label">Data *</span>
              <input type="date" name="transaction_date" class="field__input" required />
            </label>
          </div>
          <label class="field">
            <span class="field__label">Observações</span>
            <textarea name="notes" class="field__input field__input--textarea" rows="2"></textarea>
          </label>
          <p class="form-error" data-role="form-error" hidden></p>
          <footer class="modal__footer">
            <button type="button" class="btn btn--ghost" data-action="close-modal">Cancelar</button>
            <button type="submit" class="btn btn--primary">Salvar</button>
          </footer>
        </form>
      </div>
    </div>
  `;

  initFinancePage(page);
  return page;
}

/** @param {HTMLElement} page */
function initFinancePage(page) {
  const state = {
    transactions: [],
    summary: null,
    byCategory: [],
    byDay: [],
    page: 1,
    pages: 1,
    loading: true,
    loadingMore: false,
    error: null,
    editingId: null,
    categoryChart: null,
    dayChart: null,
    filters: getFiltersFromDom(page),
  };

  const summaryEl = page.querySelector('[data-role="summary-cards"]');
  const tableWrap = page.querySelector('[data-role="table-wrap"]');
  const footerEl = page.querySelector('[data-role="footer"]');
  const modal = page.querySelector('[data-role="modal"]');
  const backdrop = page.querySelector('[data-role="modal-backdrop"]');
  const form = page.querySelector('[data-role="tx-form"]');
  const formError = page.querySelector('[data-role="form-error"]');
  const modalTitle = page.querySelector('[data-role="modal-title"]');
  const typeSelect = page.querySelector('[data-role="type-select"]');
  const categorySelect = page.querySelector('[data-role="category-select"]');

  function getFiltersFromDom(root) {
    return {
      search: root.querySelector('[data-filter="search"]')?.value || "",
      type: root.querySelector('[data-filter="type"]')?.value || "",
      category: root.querySelector('[data-filter="category"]')?.value || "",
      start_date: root.querySelector('[data-filter="start_date"]')?.value || "",
      end_date: root.querySelector('[data-filter="end_date"]')?.value || "",
    };
  }

  function filterParams(extra = {}) {
    const f = { ...state.filters, ...extra };
    const params = {};
    if (f.type) params.type = f.type;
    if (f.category.trim()) params.category = f.category.trim();
    if (f.start_date) params.start_date = f.start_date;
    if (f.end_date) params.end_date = f.end_date;
    if (f.search.trim()) params.search = f.search.trim();
    return params;
  }

  function populateCategoryOptions(type, selected = "") {
    if (!categorySelect) return;
    const list = DEFAULT_CATEGORIES[type] || DEFAULT_CATEGORIES.expense;
    categorySelect.innerHTML = list.map((c) => `<option value="${c}">${c}</option>`).join("");
    categorySelect.value = selected || list[0];
  }

  async function loadAll(resetPage = true) {
    if (resetPage) {
      state.page = 1;
      state.loading = true;
      state.error = null;
    } else {
      state.loadingMore = true;
    }
    render();

    const base = filterParams();
    const listParams = { ...base, page: state.page, page_size: PAGE_SIZE };

    const [listRes, summaryRes, catRes, dayRes] = await Promise.all([
      listFinanceTransactions(listParams),
      getFinanceSummary(base),
      getFinanceByCategory(base),
      getFinanceByDay(base),
    ]);

    state.loading = false;
    state.loadingMore = false;

    if (!listRes.ok) {
      state.error = listRes.error || "Não foi possível carregar finanças";
      if (resetPage) {
        state.transactions = [];
        state.summary = null;
        state.byCategory = [];
        state.byDay = [];
      }
      render();
      return;
    }

    const data = listRes.data || {};
    const items = data.items || [];
    state.transactions = resetPage ? items : [...state.transactions, ...items];
    state.pages = data.pages ?? 1;
    state.summary = summaryRes.ok ? summaryRes.data : null;
    state.byCategory = catRes.ok ? catRes.data || [] : [];
    state.byDay = dayRes.ok ? dayRes.data || [] : [];
    render();
  }

  function renderSummaryCards() {
    if (!summaryEl) return;
    summaryEl.innerHTML = "";

    if (state.loading) {
      summaryEl.appendChild(renderLoading("Calculando resumo..."));
      return;
    }

    if (state.error && !state.summary) {
      summaryEl.innerHTML = `<div class="alert alert--warning finance-alert">${escapeHtml(state.error)}</div>`;
      return;
    }

    const s = state.summary || { income: 0, expense: 0, balance: 0, transactions_count: 0 };
    const cards = [
      { title: "Receitas", value: formatBRL(s.income), cls: "finance-card--income", icon: "↑" },
      { title: "Despesas", value: formatBRL(s.expense), cls: "finance-card--expense", icon: "↓" },
      { title: "Saldo", value: formatBRL(s.balance), cls: "finance-card--balance", icon: "=" },
      {
        title: "Transações",
        value: String(s.transactions_count ?? 0),
        cls: "finance-card--count",
        icon: "#",
      },
    ];

    cards.forEach((card) => {
      const el = document.createElement("article");
      el.className = `card finance-card ${card.cls}`;
      el.innerHTML = `
        <div class="card__head"><span class="card__icon">${card.icon}</span><h4 class="card__title">${card.title}</h4></div>
        <p class="card__value">${card.value}</p>
      `;
      summaryEl.appendChild(el);
    });
  }

  function renderCharts() {
    const catCanvas = page.querySelector('[data-role="chart-category"]');
    const dayCanvas = page.querySelector('[data-role="chart-day"]');
    if (!catCanvas || !dayCanvas) return;

    if (state.categoryChart) {
      state.categoryChart.destroy();
      state.categoryChart = null;
    }
    if (state.dayChart) {
      state.dayChart.destroy();
      state.dayChart = null;
    }

    if (state.loading || state.error) return;

    const catLabels = state.byCategory.map((row) => row.category);
    const catExpenses = state.byCategory.map((row) => Number(row.expense));
    const catIncomes = state.byCategory.map((row) => Number(row.income));

    state.categoryChart = new Chart(catCanvas, {
      type: "bar",
      data: {
        labels: catLabels.length ? catLabels : ["Sem dados"],
        datasets: [
          {
            label: "Receitas",
            data: catLabels.length ? catIncomes : [0],
            backgroundColor: "rgba(34, 197, 94, 0.55)",
          },
          {
            label: "Despesas",
            data: catLabels.length ? catExpenses : [0],
            backgroundColor: "rgba(239, 68, 68, 0.55)",
          },
        ],
      },
      options: {
        responsive: true,
        plugins: { legend: { labels: { color: "#cbd5e1" } } },
        scales: {
          x: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(255,255,255,0.05)" } },
          y: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(255,255,255,0.05)" } },
        },
      },
    });

    const dayLabels = state.byDay.map((row) => formatDateBR(row.date));
    state.dayChart = new Chart(dayCanvas, {
      type: "line",
      data: {
        labels: dayLabels.length ? dayLabels : ["Sem dados"],
        datasets: [
          {
            label: "Receitas",
            data: dayLabels.length ? state.byDay.map((r) => Number(r.income)) : [0],
            borderColor: "#4ade80",
            backgroundColor: "rgba(34, 197, 94, 0.15)",
            tension: 0.3,
          },
          {
            label: "Despesas",
            data: dayLabels.length ? state.byDay.map((r) => Number(r.expense)) : [0],
            borderColor: "#f87171",
            backgroundColor: "rgba(239, 68, 68, 0.15)",
            tension: 0.3,
          },
        ],
      },
      options: {
        responsive: true,
        plugins: { legend: { labels: { color: "#cbd5e1" } } },
        scales: {
          x: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(255,255,255,0.05)" } },
          y: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(255,255,255,0.05)" } },
        },
      },
    });
  }

  function renderTable() {
    if (!tableWrap) return;
    tableWrap.innerHTML = "";

    if (state.loading) {
      tableWrap.appendChild(renderLoading("Carregando transações..."));
      return;
    }

    if (state.error && state.transactions.length === 0) {
      tableWrap.appendChild(renderErrorState(state.error, () => loadAll(true)));
      return;
    }

    if (state.transactions.length === 0) {
      tableWrap.appendChild(renderEmptyState());
      return;
    }

    const table = document.createElement("div");
    table.className = "finance-table";
    table.innerHTML = `
      <div class="finance-table__head">
        <span>Data</span><span>Descrição</span><span>Categoria</span><span>Tipo</span><span>Valor</span><span>Ações</span>
      </div>
    `;

    state.transactions.forEach((tx) => {
      const row = document.createElement("div");
      row.className = `finance-table__row finance-table__row--${tx.type}`;
      row.innerHTML = `
        <span data-label="Data">${formatDateBR(tx.transaction_date)}</span>
        <span data-label="Descrição">${escapeHtml(tx.description)}</span>
        <span data-label="Categoria">${escapeHtml(tx.category)}</span>
        <span data-label="Tipo"><span class="tx-type tx-type--${tx.type}">${typeLabel(tx.type)}</span></span>
        <span data-label="Valor" class="tx-amount tx-amount--${tx.type}">${formatBRL(tx.amount)}</span>
        <span class="finance-table__actions" data-label="Ações">
          <button type="button" class="btn btn--ghost btn--sm" data-action="edit" data-id="${tx.id}">Editar</button>
          <button type="button" class="btn btn--ghost btn--sm btn--danger" data-action="delete" data-id="${tx.id}">Excluir</button>
        </span>
      `;
      table.appendChild(row);
    });

    tableWrap.appendChild(table);
  }

  function renderFooter() {
    if (!footerEl) return;
    footerEl.innerHTML = "";
    if (state.loading || state.error) return;
    if (state.page < state.pages) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "btn btn--secondary btn--block";
      btn.textContent = state.loadingMore ? "Carregando..." : "Carregar mais";
      btn.disabled = state.loadingMore;
      btn.addEventListener("click", () => {
        state.page += 1;
        loadAll(false);
      });
      footerEl.appendChild(btn);
    }
  }

  function render() {
    renderSummaryCards();
    renderTable();
    renderFooter();
    renderCharts();
  }

  function openModal(mode, tx = null) {
    state.editingId = mode === "edit" && tx ? tx.id : null;
    modalTitle.textContent = mode === "edit" ? "Editar transação" : "Nova transação";
    formError.hidden = true;
    const type = tx?.type || "expense";
    typeSelect.value = type;
    populateCategoryOptions(type, tx?.category);
    form.description.value = tx?.description || "";
    form.amount.value = tx ? Number(tx.amount) : "";
    form.transaction_date.value = tx?.transaction_date || new Date().toISOString().slice(0, 10);
    form.notes.value = tx?.notes || "";
    modal.hidden = false;
    backdrop.hidden = false;
  }

  function closeModal() {
    modal.hidden = true;
    backdrop.hidden = true;
    state.editingId = null;
    form.reset();
  }

  page.querySelector('[data-action="new-transaction"]')?.addEventListener("click", () => openModal("create"));
  page.querySelectorAll('[data-action="close-modal"]').forEach((btn) => btn.addEventListener("click", closeModal));
  backdrop?.addEventListener("click", closeModal);

  typeSelect?.addEventListener("change", () => populateCategoryOptions(typeSelect.value));

  page.querySelectorAll("[data-filter]").forEach((el) => {
    el.addEventListener("change", () => {
      state.filters = getFiltersFromDom(page);
      loadAll(true);
    });
    if (el.matches('[data-filter="search"]')) {
      el.addEventListener("input", () => {
        state.filters = getFiltersFromDom(page);
        loadAll(true);
      });
    }
  });

  tableWrap?.addEventListener("click", async (event) => {
    const target = /** @type {HTMLElement} */ (event.target);
    const action = target.closest("[data-action]")?.getAttribute("data-action");
    const id = target.closest("[data-id]")?.getAttribute("data-id");
    if (!action || !id) return;

    if (action === "edit") {
      const tx = state.transactions.find((item) => item.id === id);
      if (tx) openModal("edit", tx);
      return;
    }

    if (action === "delete") {
      const tx = state.transactions.find((item) => item.id === id);
      const label = tx?.description || "esta transação";
      if (!window.confirm(`Excluir "${label}"? Esta ação não pode ser desfeita.`)) return;
      const result = await deleteFinanceTransaction(id);
      if (!result.ok) {
        alert(result.error || "Falha ao excluir");
        return;
      }
      loadAll(true);
    }
  });

  form?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = transactionFormToPayload({
      description: form.description.value,
      amount: form.amount.value,
      type: form.type.value,
      category: form.category.value,
      transaction_date: form.transaction_date.value,
      notes: form.notes.value,
    });

    if (!payload.description || !payload.category || !payload.transaction_date) {
      formError.textContent = "Preencha os campos obrigatórios.";
      formError.hidden = false;
      return;
    }

    const result = state.editingId
      ? await updateFinanceTransaction(state.editingId, payload)
      : await createFinanceTransaction(payload);

    if (!result.ok) {
      formError.textContent = result.error || "Falha ao salvar transação";
      formError.hidden = false;
      return;
    }

    closeModal();
    loadAll(true);
  });

  populateCategoryOptions("expense");
  loadAll(true);
}

function renderErrorState(message, onRetry) {
  const wrap = document.createElement("div");
  wrap.className = "empty-state empty-state--error";
  wrap.innerHTML = `
    <div class="empty-state__icon">⚠</div>
    <h3 class="empty-state__title">Erro ao carregar</h3>
    <p class="empty-state__text">${escapeHtml(message)}</p>
  `;
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "btn btn--secondary";
  btn.textContent = "Tentar novamente";
  btn.addEventListener("click", onRetry);
  wrap.appendChild(btn);
  return wrap;
}

function renderEmptyState() {
  const wrap = document.createElement("div");
  wrap.className = "empty-state";
  wrap.innerHTML = `
    <div class="empty-state__icon">💰</div>
    <h3 class="empty-state__title">Nenhuma transação</h3>
    <p class="empty-state__text">Registre receitas e despesas ou ajuste o período dos filtros.</p>
  `;
  return wrap;
}
