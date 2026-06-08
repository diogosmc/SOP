import {
  createHabit,
  deleteHabit,
  listHabits,
  updateHabit,
} from "../services/api.js";
import {
  filterHabitsClient,
  HABIT_ACTIVE_OPTIONS,
  HABIT_TYPES,
  habitFormToPayload,
  typeIcon,
  typeLabel,
} from "../modules/habits.js";
import { renderLoading } from "../components/loading.js";

const PAGE_SIZE = 20;

/** @returns {HTMLElement} */
export function renderHabitsPage() {
  const page = document.createElement("section");
  page.className = "page page--habits";
  page.innerHTML = `
    <div class="page__intro page__intro--row">
      <div>
        <h2 class="page__heading">Hábitos</h2>
        <p class="page__description">Acompanhe rotinas positivas e evite padrões negativos.</p>
      </div>
      <button type="button" class="btn btn--primary" data-action="new-habit">
        Novo hábito
      </button>
    </div>
    <div class="habits-toolbar">
      <label class="field field--search">
        <span class="field__label">Buscar</span>
        <input type="search" class="field__input" placeholder="Nome, descrição ou frequência..." data-filter="search" />
      </label>
      <label class="field">
        <span class="field__label">Tipo</span>
        <select class="field__input" data-filter="type">
          <option value="">Todos</option>
          ${HABIT_TYPES.map((t) => `<option value="${t.value}">${t.label}</option>`).join("")}
        </select>
      </label>
      <label class="field">
        <span class="field__label">Status</span>
        <select class="field__input" data-filter="active">
          ${HABIT_ACTIVE_OPTIONS.map((o) => `<option value="${o.value}">${o.label}</option>`).join("")}
        </select>
      </label>
    </div>
    <div class="habits-meta" data-role="meta"></div>
    <div class="habits-list" data-role="list"></div>
    <div class="habits-footer" data-role="footer"></div>
    <div class="modal-backdrop" data-role="modal-backdrop" hidden></div>
    <div class="modal" data-role="modal" hidden aria-modal="true" role="dialog" aria-labelledby="habit-modal-title">
      <div class="modal__panel">
        <header class="modal__header">
          <h3 id="habit-modal-title" class="modal__title" data-role="modal-title">Novo hábito</h3>
          <button type="button" class="btn btn--ghost btn--icon" data-action="close-modal" aria-label="Fechar">✕</button>
        </header>
        <form class="modal__body habit-form" data-role="habit-form">
          <label class="field">
            <span class="field__label">Nome *</span>
            <input type="text" name="name" class="field__input" required maxlength="255" />
          </label>
          <label class="field">
            <span class="field__label">Descrição</span>
            <textarea name="description" class="field__input field__input--textarea" rows="3"></textarea>
          </label>
          <div class="field-row">
            <label class="field">
              <span class="field__label">Tipo *</span>
              <select name="type" class="field__input" required>
                ${HABIT_TYPES.map((t) => `<option value="${t.value}">${t.label}</option>`).join("")}
              </select>
            </label>
            <label class="field">
              <span class="field__label">Frequência</span>
              <input type="text" name="frequency" class="field__input" maxlength="50" placeholder="Ex: diário, semanal" />
            </label>
          </div>
          <label class="field field--checkbox">
            <input type="checkbox" name="active" checked />
            <span>Hábito ativo</span>
          </label>
          <p class="form-error" data-role="form-error" hidden></p>
          <footer class="modal__footer">
            <button type="button" class="btn btn--ghost" data-action="close-modal">Cancelar</button>
            <button type="submit" class="btn btn--primary" data-role="submit-btn">Salvar</button>
          </footer>
        </form>
      </div>
    </div>
  `;

  initHabitsPage(page);
  return page;
}

/** @param {HTMLElement} page */
function initHabitsPage(page) {
  const state = {
    habits: [],
    page: 1,
    total: 0,
    pages: 1,
    typeFilter: "",
    activeFilter: "",
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
  const form = page.querySelector('[data-role="habit-form"]');
  const formError = page.querySelector('[data-role="form-error"]');
  const modalTitle = page.querySelector('[data-role="modal-title"]');
  const submitBtn = page.querySelector('[data-role="submit-btn"]');

  /** @param {boolean} [append] */
  async function fetchHabits(append = false) {
    if (append) {
      state.loadingMore = true;
    } else {
      state.loading = true;
      state.error = null;
    }
    render();

    const params = { page: state.page, page_size: PAGE_SIZE };
    if (state.typeFilter) params.type = state.typeFilter;
    if (state.activeFilter === "true") params.active = true;
    if (state.activeFilter === "false") params.active = false;

    const result = await listHabits(params);

    if (append) state.loadingMore = false;
    else state.loading = false;

    if (!result.ok) {
      state.error = result.error || "Não foi possível carregar hábitos";
      if (!append) state.habits = [];
      render();
      return;
    }

    const data = result.data || {};
    const items = data.items || [];
    state.total = data.total ?? items.length;
    state.pages = data.pages ?? 1;
    state.habits = append ? [...state.habits, ...items] : items;
    render();
  }

  function resetAndFetch() {
    state.page = 1;
    fetchHabits(false);
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
    const filtered = filterHabitsClient(state.habits, { search: state.search });
    metaEl.textContent = `${filtered.length} exibido(s) · ${state.total} no total`;
  }

  function renderList() {
    if (!listEl) return;
    listEl.innerHTML = "";

    if (state.loading) {
      listEl.appendChild(renderLoading("Carregando hábitos..."));
      return;
    }

    if (state.error && state.habits.length === 0) {
      listEl.appendChild(renderErrorState(state.error, resetAndFetch));
      return;
    }

    const filtered = filterHabitsClient(state.habits, { search: state.search });

    if (filtered.length === 0) {
      listEl.appendChild(renderEmptyState());
      return;
    }

    const grid = document.createElement("div");
    grid.className = "habit-grid";
    filtered.forEach((habit) => grid.appendChild(renderHabitCard(habit)));
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
        fetchHabits(true);
      });
      footerEl.appendChild(btn);
    }
  }

  /** @param {object} habit */
  function renderHabitCard(habit) {
    const card = document.createElement("article");
    card.className = `habit-card habit-card--${habit.type}${habit.active ? "" : " habit-card--inactive"}`;
    card.dataset.habitId = habit.id;

    card.innerHTML = `
      <header class="habit-card__head">
        <span class="habit-card__type habit-card__type--${habit.type}">
          <span class="habit-card__type-icon">${typeIcon(habit.type)}</span>
          ${typeLabel(habit.type)}
        </span>
        <span class="habit-card__active-badge ${habit.active ? "habit-card__active-badge--on" : "habit-card__active-badge--off"}">
          ${habit.active ? "Ativo" : "Inativo"}
        </span>
      </header>
      <h3 class="habit-card__name">${escapeHtml(habit.name)}</h3>
      ${habit.description ? `<p class="habit-card__desc">${escapeHtml(habit.description)}</p>` : ""}
      <dl class="habit-card__meta">
        ${habit.frequency ? `<div><dt>Frequência</dt><dd>${escapeHtml(habit.frequency)}</dd></div>` : ""}
        <div><dt>Streak atual</dt><dd class="habit-card__streak">${habit.streak_current ?? 0} dias</dd></div>
        <div><dt>Melhor streak</dt><dd class="habit-card__streak habit-card__streak--best">${habit.streak_best ?? 0} dias</dd></div>
      </dl>
      <footer class="habit-card__actions">
        <button type="button" class="btn btn--ghost btn--sm" data-action="toggle" data-id="${habit.id}">
          ${habit.active ? "Desativar" : "Ativar"}
        </button>
        <button type="button" class="btn btn--ghost btn--sm" data-action="edit" data-id="${habit.id}">Editar</button>
        <button type="button" class="btn btn--ghost btn--sm btn--danger" data-action="delete" data-id="${habit.id}">Excluir</button>
      </footer>
    `;

    return card;
  }

  function openModal(mode, habit = null) {
    state.editingId = mode === "edit" && habit ? habit.id : null;
    modalTitle.textContent = mode === "edit" ? "Editar hábito" : "Novo hábito";
    submitBtn.textContent = mode === "edit" ? "Atualizar" : "Criar";
    formError.hidden = true;
    formError.textContent = "";

    /** @type {HTMLFormElement} */
    const formEl = form;
    formEl.name.value = habit?.name || "";
    formEl.description.value = habit?.description || "";
    formEl.type.value = habit?.type || "positive";
    formEl.frequency.value = habit?.frequency || "";
    formEl.active.checked = habit ? habit.active : true;

    modal.hidden = false;
    backdrop.hidden = false;
    formEl.name.focus();
  }

  function closeModal() {
    modal.hidden = true;
    backdrop.hidden = true;
    state.editingId = null;
    form.reset();
    form.active.checked = true;
  }

  page.querySelector('[data-action="new-habit"]')?.addEventListener("click", () => openModal("create"));

  page.querySelectorAll('[data-action="close-modal"]').forEach((btn) => {
    btn.addEventListener("click", closeModal);
  });

  backdrop?.addEventListener("click", closeModal);

  page.querySelector('[data-filter="search"]')?.addEventListener("input", (event) => {
    state.search = /** @type {HTMLInputElement} */ (event.target).value;
    render();
  });

  page.querySelector('[data-filter="type"]')?.addEventListener("change", (event) => {
    state.typeFilter = /** @type {HTMLSelectElement} */ (event.target).value;
    resetAndFetch();
  });

  page.querySelector('[data-filter="active"]')?.addEventListener("change", (event) => {
    state.activeFilter = /** @type {HTMLSelectElement} */ (event.target).value;
    resetAndFetch();
  });

  listEl?.addEventListener("click", async (event) => {
    const target = /** @type {HTMLElement} */ (event.target);
    const action = target.closest("[data-action]")?.getAttribute("data-action");
    const id = target.closest("[data-id]")?.getAttribute("data-id");
    if (!action || !id) return;

    if (action === "edit") {
      const habit = state.habits.find((item) => item.id === id);
      if (habit) openModal("edit", habit);
      return;
    }

    if (action === "toggle") {
      const habit = state.habits.find((item) => item.id === id);
      if (!habit) return;
      const result = await updateHabit(id, { active: !habit.active });
      if (!result.ok) {
        alert(result.error || "Falha ao alterar status do hábito");
        return;
      }
      const idx = state.habits.findIndex((item) => item.id === id);
      if (idx >= 0) state.habits[idx] = result.data;
      render();
      return;
    }

    if (action === "delete") {
      const habit = state.habits.find((item) => item.id === id);
      const name = habit?.name || "este hábito";
      if (!window.confirm(`Excluir "${name}"? Esta ação não pode ser desfeita.`)) return;

      const result = await deleteHabit(id);
      if (!result.ok) {
        alert(result.error || "Falha ao excluir hábito");
        return;
      }
      state.habits = state.habits.filter((item) => item.id !== id);
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
      name: formEl.name.value,
      description: formEl.description.value,
      type: formEl.type.value,
      frequency: formEl.frequency.value,
      active: formEl.active.checked,
    };

    if (!formData.name.trim()) {
      formError.textContent = "Informe um nome.";
      formError.hidden = false;
      return;
    }

    state.saving = true;
    submitBtn.disabled = true;
    submitBtn.textContent = "Salvando...";
    formError.hidden = true;

    const payload = habitFormToPayload(formData);
    const result = state.editingId
      ? await updateHabit(state.editingId, payload)
      : await createHabit(payload);

    state.saving = false;
    submitBtn.disabled = false;
    submitBtn.textContent = state.editingId ? "Atualizar" : "Criar";

    if (!result.ok) {
      formError.textContent = result.error || "Falha ao salvar hábito";
      formError.hidden = false;
      return;
    }

    closeModal();
    resetAndFetch();
  });

  fetchHabits(false);
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
    <div class="empty-state__icon">↻</div>
    <h3 class="empty-state__title">Nenhum hábito por aqui</h3>
    <p class="empty-state__text">Crie seu primeiro hábito ou ajuste os filtros para ver outros resultados.</p>
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
