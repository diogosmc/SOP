import {
  createTask,
  deleteTask,
  listTasks,
  updateTask,
} from "../services/api.js";
import {
  filterTasksClient,
  priorityLabel,
  statusLabel,
  TASK_PRIORITIES,
  TASK_STATUSES,
  taskFormToPayload,
  formatDueDate,
  toDatetimeLocalValue,
} from "../modules/tasks.js";
import { renderLoading } from "../components/loading.js";

const PAGE_SIZE = 20;

/** @returns {HTMLElement} */
export function renderTasksPage() {
  const page = document.createElement("section");
  page.className = "page page--tasks";
  page.innerHTML = `
    <div class="page__intro page__intro--row">
      <div>
        <h2 class="page__heading">Tarefas</h2>
        <p class="page__description">Organize pendências, prioridades e prazos.</p>
      </div>
      <button type="button" class="btn btn--primary" data-action="new-task">
        Nova tarefa
      </button>
    </div>
    <div class="tasks-toolbar">
      <label class="field field--search">
        <span class="field__label">Buscar</span>
        <input type="search" class="field__input" placeholder="Título, descrição ou categoria..." data-filter="search" />
      </label>
      <label class="field">
        <span class="field__label">Status</span>
        <select class="field__input" data-filter="status">
          <option value="">Todos</option>
          ${TASK_STATUSES.map((s) => `<option value="${s.value}">${s.label}</option>`).join("")}
        </select>
      </label>
      <label class="field">
        <span class="field__label">Prioridade</span>
        <select class="field__input" data-filter="priority">
          <option value="">Todas</option>
          ${TASK_PRIORITIES.map((p) => `<option value="${p.value}">${p.label}</option>`).join("")}
        </select>
      </label>
    </div>
    <div class="tasks-meta" data-role="meta"></div>
    <div class="tasks-list" data-role="list"></div>
    <div class="tasks-footer" data-role="footer"></div>
    <div class="modal-backdrop" data-role="modal-backdrop" hidden></div>
    <div class="modal" data-role="modal" hidden aria-modal="true" role="dialog" aria-labelledby="task-modal-title">
      <div class="modal__panel">
        <header class="modal__header">
          <h3 id="task-modal-title" class="modal__title" data-role="modal-title">Nova tarefa</h3>
          <button type="button" class="btn btn--ghost btn--icon" data-action="close-modal" aria-label="Fechar">✕</button>
        </header>
        <form class="modal__body task-form" data-role="task-form">
          <label class="field">
            <span class="field__label">Título *</span>
            <input type="text" name="title" class="field__input" required maxlength="500" />
          </label>
          <label class="field">
            <span class="field__label">Descrição</span>
            <textarea name="description" class="field__input field__input--textarea" rows="3"></textarea>
          </label>
          <div class="field-row">
            <label class="field">
              <span class="field__label">Status</span>
              <select name="status" class="field__input">
                ${TASK_STATUSES.map((s) => `<option value="${s.value}">${s.label}</option>`).join("")}
              </select>
            </label>
            <label class="field">
              <span class="field__label">Prioridade</span>
              <select name="priority" class="field__input">
                ${TASK_PRIORITIES.map((p) => `<option value="${p.value}">${p.label}</option>`).join("")}
              </select>
            </label>
          </div>
          <div class="field-row">
            <label class="field">
              <span class="field__label">Prazo</span>
              <input type="datetime-local" name="due_date" class="field__input" />
            </label>
            <label class="field">
              <span class="field__label">Categoria</span>
              <input type="text" name="category" class="field__input" maxlength="100" />
            </label>
          </div>
          <p class="form-error" data-role="form-error" hidden></p>
          <footer class="modal__footer">
            <button type="button" class="btn btn--ghost" data-action="close-modal">Cancelar</button>
            <button type="submit" class="btn btn--primary" data-role="submit-btn">Salvar</button>
          </footer>
        </form>
      </div>
    </div>
  `;

  initTasksPage(page);
  return page;
}

/** @param {HTMLElement} page */
function initTasksPage(page) {
  /** @type {{ tasks: object[], page: number, total: number, pages: number, statusFilter: string, priorityFilter: string, search: string, loading: boolean, loadingMore: boolean, error: string|null, editingId: string|null, saving: boolean }} */
  const state = {
    tasks: [],
    page: 1,
    total: 0,
    pages: 1,
    statusFilter: "",
    priorityFilter: "",
    search: "",
    loading: true,
    loadingMore: false,
    error: null,
    editingId: null,
    saving: false,
  };

  const listEl = page.querySelector('[data-role="list"]');
  const metaEl = page.querySelector('[data-role="meta"]');
  const footerEl = page.querySelector('[data-role="footer"]');
  const modal = page.querySelector('[data-role="modal"]');
  const backdrop = page.querySelector('[data-role="modal-backdrop"]');
  const form = page.querySelector('[data-role="task-form"]');
  const formError = page.querySelector('[data-role="form-error"]');
  const modalTitle = page.querySelector('[data-role="modal-title"]');
  const submitBtn = page.querySelector('[data-role="submit-btn"]');

  /** @param {boolean} [append] */
  async function fetchTasks(append = false) {
    if (append) {
      state.loadingMore = true;
    } else {
      state.loading = true;
      state.error = null;
    }
    render();

    const params = { page: state.page, page_size: PAGE_SIZE };
    if (state.statusFilter) params.status = state.statusFilter;

    const result = await listTasks(params);

    if (append) state.loadingMore = false;
    else state.loading = false;

    if (!result.ok) {
      state.error = result.error || "Não foi possível carregar tarefas";
      if (!append) state.tasks = [];
      render();
      return;
    }

    const data = result.data || {};
    const items = data.items || [];
    state.total = data.total ?? items.length;
    state.pages = data.pages ?? 1;
    state.tasks = append ? [...state.tasks, ...items] : items;
    render();
  }

  function resetAndFetch() {
    state.page = 1;
    fetchTasks(false);
  }

  function render() {
    renderMeta();
    renderList();
    renderFooter();
  }

  function renderMeta() {
    if (!metaEl) return;
    if (state.loading) {
      metaEl.textContent = "";
      return;
    }
    const filtered = filterTasksClient(state.tasks, {
      search: state.search,
      priority: state.priorityFilter,
    });
    metaEl.textContent = `${filtered.length} exibida(s) · ${state.total} no total`;
  }

  function renderList() {
    if (!listEl) return;
    listEl.innerHTML = "";

    if (state.loading) {
      listEl.appendChild(renderLoading("Carregando tarefas..."));
      return;
    }

    if (state.error && state.tasks.length === 0) {
      listEl.appendChild(renderErrorState(state.error, resetAndFetch));
      return;
    }

    const filtered = filterTasksClient(state.tasks, {
      search: state.search,
      priority: state.priorityFilter,
    });

    if (filtered.length === 0) {
      listEl.appendChild(renderEmptyState());
      return;
    }

    const grid = document.createElement("div");
    grid.className = "task-grid";
    filtered.forEach((task) => grid.appendChild(renderTaskCard(task)));
    listEl.appendChild(grid);
  }

  function renderFooter() {
    if (!footerEl) return;
    footerEl.innerHTML = "";

    if (state.loading || state.error) return;

    const hasMore = state.page < state.pages;
    if (hasMore) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "btn btn--secondary btn--block";
      btn.textContent = state.loadingMore ? "Carregando..." : "Carregar mais";
      btn.disabled = state.loadingMore;
      btn.addEventListener("click", () => {
        state.page += 1;
        fetchTasks(true);
      });
      footerEl.appendChild(btn);
    }
  }

  /** @param {object} task */
  function renderTaskCard(task) {
    const card = document.createElement("article");
    card.className = `task-card task-card--${task.status} task-card--priority-${task.priority}`;
    card.dataset.taskId = task.id;

    const isCompleted = task.status === "completed";

    card.innerHTML = `
      <header class="task-card__head">
        <span class="task-card__status-badge task-card__status-badge--${task.status}">${statusLabel(task.status)}</span>
        <span class="task-card__priority task-card__priority--${task.priority}">${priorityLabel(task.priority)}</span>
      </header>
      <h3 class="task-card__title">${escapeHtml(task.title)}</h3>
      ${task.description ? `<p class="task-card__desc">${escapeHtml(task.description)}</p>` : ""}
      <dl class="task-card__meta">
        ${task.category ? `<div><dt>Categoria</dt><dd>${escapeHtml(task.category)}</dd></div>` : ""}
        <div><dt>Prazo</dt><dd>${formatDueDate(task.due_date)}</dd></div>
      </dl>
      <footer class="task-card__actions">
        ${
          !isCompleted
            ? `<button type="button" class="btn btn--ghost btn--sm" data-action="complete" data-id="${task.id}">Concluir</button>`
            : ""
        }
        <button type="button" class="btn btn--ghost btn--sm" data-action="edit" data-id="${task.id}">Editar</button>
        <button type="button" class="btn btn--ghost btn--sm btn--danger" data-action="delete" data-id="${task.id}">Excluir</button>
      </footer>
    `;

    return card;
  }

  function openModal(mode, task = null) {
    state.editingId = mode === "edit" && task ? task.id : null;
    modalTitle.textContent = mode === "edit" ? "Editar tarefa" : "Nova tarefa";
    submitBtn.textContent = mode === "edit" ? "Atualizar" : "Criar";
    formError.hidden = true;
    formError.textContent = "";

    /** @type {HTMLFormElement} */
    const formEl = form;
    formEl.title.value = task?.title || "";
    formEl.description.value = task?.description || "";
    formEl.status.value = task?.status || "pending";
    formEl.priority.value = task?.priority || "medium";
    formEl.due_date.value = toDatetimeLocalValue(task?.due_date);
    formEl.category.value = task?.category || "";

    modal.hidden = false;
    backdrop.hidden = false;
    formEl.title.focus();
  }

  function closeModal() {
    modal.hidden = true;
    backdrop.hidden = true;
    state.editingId = null;
    form.reset();
  }

  page.querySelector('[data-action="new-task"]')?.addEventListener("click", () => openModal("create"));

  page.querySelectorAll('[data-action="close-modal"]').forEach((btn) => {
    btn.addEventListener("click", closeModal);
  });

  backdrop?.addEventListener("click", closeModal);

  page.querySelector('[data-filter="search"]')?.addEventListener("input", (event) => {
    state.search = /** @type {HTMLInputElement} */ (event.target).value;
    render();
  });

  page.querySelector('[data-filter="status"]')?.addEventListener("change", (event) => {
    state.statusFilter = /** @type {HTMLSelectElement} */ (event.target).value;
    resetAndFetch();
  });

  page.querySelector('[data-filter="priority"]')?.addEventListener("change", (event) => {
    state.priorityFilter = /** @type {HTMLSelectElement} */ (event.target).value;
    render();
  });

  listEl?.addEventListener("click", async (event) => {
    const target = /** @type {HTMLElement} */ (event.target);
    const action = target.closest("[data-action]")?.getAttribute("data-action");
    const id = target.closest("[data-id]")?.getAttribute("data-id");
    if (!action || !id) return;

    if (action === "edit") {
      const task = state.tasks.find((item) => item.id === id);
      if (task) openModal("edit", task);
      return;
    }

    if (action === "complete") {
      const result = await updateTask(id, { status: "completed" });
      if (!result.ok) {
        alert(result.error || "Falha ao concluir tarefa");
        return;
      }
      const idx = state.tasks.findIndex((item) => item.id === id);
      if (idx >= 0) state.tasks[idx] = result.data;
      render();
      return;
    }

    if (action === "delete") {
      const task = state.tasks.find((item) => item.id === id);
      const name = task?.title || "esta tarefa";
      if (!window.confirm(`Excluir "${name}"? Esta ação não pode ser desfeita.`)) return;

      const result = await deleteTask(id);
      if (!result.ok) {
        alert(result.error || "Falha ao excluir tarefa");
        return;
      }
      state.tasks = state.tasks.filter((item) => item.id !== id);
      state.total = Math.max(0, state.total - 1);
      render();
    }
  });

  form?.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (state.saving) return;

    /** @type {HTMLFormElement} */
    const formEl = form;
    const formData = {
      title: formEl.title.value,
      description: formEl.description.value,
      status: formEl.status.value,
      priority: formEl.priority.value,
      due_date: formEl.due_date.value,
      category: formEl.category.value,
    };

    if (!formData.title.trim()) {
      formError.textContent = "Informe um título.";
      formError.hidden = false;
      return;
    }

    state.saving = true;
    submitBtn.disabled = true;
    submitBtn.textContent = "Salvando...";
    formError.hidden = true;

    const payload = taskFormToPayload(formData);
    const result = state.editingId
      ? await updateTask(state.editingId, payload)
      : await createTask(payload);

    state.saving = false;
    submitBtn.disabled = false;
    submitBtn.textContent = state.editingId ? "Atualizar" : "Criar";

    if (!result.ok) {
      formError.textContent = result.error || "Falha ao salvar tarefa";
      formError.hidden = false;
      return;
    }

    closeModal();
    resetAndFetch();
  });

  fetchTasks(false);
}

/** @param {string} message @param {() => void} onRetry */
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
    <div class="empty-state__icon">☑</div>
    <h3 class="empty-state__title">Nenhuma tarefa por aqui</h3>
    <p class="empty-state__text">Crie sua primeira tarefa ou ajuste os filtros para ver outros resultados.</p>
  `;
  return wrap;
}

/** @param {string} text */
function escapeHtml(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
