import {
  createNote,
  deleteNote,
  indexNote,
  listNotes,
  searchNotes,
  searchSemanticNotes,
  updateNote,
} from "../services/api.js";
import {
  escapeHtml,
  excerpt,
  formatNoteDate,
  formatSimilarity,
  noteFormToPayload,
  renderMarkdown,
  tagsToInput,
} from "../modules/notes.js";
import { renderLoading } from "../components/loading.js";

const PAGE_SIZE = 20;

/** @returns {HTMLElement} */
export function renderNotesPage() {
  const page = document.createElement("section");
  page.className = "page page--notes";
  page.innerHTML = `
    <div class="page__intro page__intro--row">
      <div>
        <h2 class="page__heading">Notas</h2>
        <p class="page__description">Escreva, organize e busque conhecimento com Markdown e RAG.</p>
      </div>
      <button type="button" class="btn btn--primary" data-action="new-note">Nova nota</button>
    </div>
    <div class="notes-layout">
      <aside class="notes-sidebar">
        <div class="notes-sidebar__filters">
          <label class="field field--search">
            <span class="field__label">Buscar</span>
            <input type="search" class="field__input" placeholder="Título ou conteúdo..." data-filter="search" />
          </label>
          <label class="field">
            <span class="field__label">Tag</span>
            <input type="text" class="field__input" placeholder="Ex: estudo" data-filter="tag" />
          </label>
          <div class="field-row">
            <label class="field">
              <span class="field__label">Favorito</span>
              <select class="field__input" data-filter="favorite">
                <option value="">Todos</option>
                <option value="true">Favoritas</option>
                <option value="false">Não favoritas</option>
              </select>
            </label>
            <label class="field">
              <span class="field__label">Arquivo</span>
              <select class="field__input" data-filter="archived">
                <option value="">Todos</option>
                <option value="false">Ativas</option>
                <option value="true">Arquivadas</option>
              </select>
            </label>
          </div>
        </div>
        <div class="notes-sidebar__meta" data-role="list-meta"></div>
        <div class="notes-sidebar__list" data-role="note-list"></div>
        <div class="notes-sidebar__footer" data-role="list-footer"></div>
      </aside>
      <div class="notes-main">
        <div class="notes-editor" data-role="editor-panel">
          <div class="notes-editor__empty" data-role="editor-empty">
            <div class="empty-state">
              <div class="empty-state__icon">✎</div>
              <h3 class="empty-state__title">Selecione ou crie uma nota</h3>
              <p class="empty-state__text">Escolha uma nota na lista ou clique em Nova nota para começar.</p>
            </div>
          </div>
          <div class="notes-editor__form" data-role="editor-form" hidden>
            <header class="notes-editor__head">
              <input type="text" class="notes-editor__title" data-field="title" placeholder="Título da nota" maxlength="500" />
              <div class="notes-editor__badges" data-role="editor-badges"></div>
            </header>
            <label class="field">
              <span class="field__label">Tags (separadas por vírgula)</span>
              <input type="text" class="field__input" data-field="tags" placeholder="trabalho, ideias, estudo" />
            </label>
            <div class="notes-editor__tabs">
              <button type="button" class="notes-tab notes-tab--active" data-tab="edit">Editar</button>
              <button type="button" class="notes-tab" data-tab="preview">Preview</button>
            </div>
            <div class="notes-editor__pane notes-editor__pane--edit" data-pane="edit">
              <textarea class="notes-editor__content" data-field="content" rows="14" placeholder="# Título&#10;&#10;Escreva em **Markdown** simples...&#10;&#10;- item 1&#10;- item 2"></textarea>
            </div>
            <div class="notes-editor__pane notes-editor__pane--preview" data-pane="preview" hidden>
              <article class="md-preview" data-role="preview"></article>
            </div>
            <p class="form-error" data-role="editor-error" hidden></p>
            <footer class="notes-editor__actions">
              <button type="button" class="btn btn--primary" data-action="save-note">Salvar</button>
              <button type="button" class="btn btn--ghost" data-action="toggle-favorite">☆ Favoritar</button>
              <button type="button" class="btn btn--ghost" data-action="toggle-archive">Arquivar</button>
              <button type="button" class="btn btn--ghost" data-action="index-note">Indexar para IA</button>
              <button type="button" class="btn btn--ghost btn--danger" data-action="delete-note">Excluir</button>
            </footer>
            <p class="notes-editor__status" data-role="editor-status"></p>
          </div>
        </div>
        <section class="notes-semantic">
          <header class="notes-semantic__head">
            <h3 class="notes-semantic__title">Busca semântica (RAG)</h3>
            <p class="notes-semantic__desc">Encontre trechos relevantes nas notas indexadas.</p>
          </header>
          <form class="notes-semantic__form" data-role="semantic-form">
            <input type="text" class="field__input" data-field="semantic-query" placeholder="Ex: o que anotei sobre medicina?" required />
            <button type="submit" class="btn btn--secondary">Buscar</button>
          </form>
          <div class="notes-semantic__results" data-role="semantic-results"></div>
        </section>
      </div>
    </div>
    <div class="modal-backdrop" data-role="modal-backdrop" hidden></div>
    <div class="modal" data-role="modal" hidden aria-modal="true" role="dialog" aria-labelledby="note-modal-title">
      <div class="modal__panel modal__panel--wide">
        <header class="modal__header">
          <h3 id="note-modal-title" class="modal__title">Nova nota</h3>
          <button type="button" class="btn btn--ghost btn--icon" data-action="close-modal" aria-label="Fechar">✕</button>
        </header>
        <form class="modal__body" data-role="modal-form">
          <label class="field">
            <span class="field__label">Título *</span>
            <input type="text" name="title" class="field__input" required maxlength="500" />
          </label>
          <label class="field">
            <span class="field__label">Tags</span>
            <input type="text" name="tags" class="field__input" placeholder="tag1, tag2" />
          </label>
          <label class="field">
            <span class="field__label">Conteúdo (Markdown)</span>
            <textarea name="content" class="field__input field__input--textarea" rows="8"></textarea>
          </label>
          <p class="form-error" data-role="modal-error" hidden></p>
          <footer class="modal__footer">
            <button type="button" class="btn btn--ghost" data-action="close-modal">Cancelar</button>
            <button type="submit" class="btn btn--primary">Criar</button>
          </footer>
        </form>
      </div>
    </div>
  `;

  initNotesPage(page);
  return page;
}

/** @param {HTMLElement} page */
function initNotesPage(page) {
  const state = {
    notes: [],
    page: 1,
    total: 0,
    pages: 1,
    search: "",
    tagFilter: "",
    favoriteFilter: "",
    archivedFilter: "",
    loading: true,
    loadingMore: false,
    error: null,
    selectedId: null,
    isNew: false,
    draft: null,
    saving: false,
    indexing: false,
    activeTab: "edit",
    semanticLoading: false,
    semanticResults: null,
    semanticError: null,
  };

  const listEl = page.querySelector('[data-role="note-list"]');
  const listMetaEl = page.querySelector('[data-role="list-meta"]');
  const listFooterEl = page.querySelector('[data-role="list-footer"]');
  const editorEmpty = page.querySelector('[data-role="editor-empty"]');
  const editorForm = page.querySelector('[data-role="editor-form"]');
  const editorError = page.querySelector('[data-role="editor-error"]');
  const editorStatus = page.querySelector('[data-role="editor-status"]');
  const editorBadges = page.querySelector('[data-role="editor-badges"]');
  const previewEl = page.querySelector('[data-role="preview"]');
  const semanticResultsEl = page.querySelector('[data-role="semantic-results"]');
  const modal = page.querySelector('[data-role="modal"]');
  const backdrop = page.querySelector('[data-role="modal-backdrop"]');
  const modalForm = page.querySelector('[data-role="modal-form"]');
  const modalError = page.querySelector('[data-role="modal-error"]');

  function getDraftFromForm() {
    return {
      title: page.querySelector('[data-field="title"]')?.value || "",
      tags: page.querySelector('[data-field="tags"]')?.value || "",
      content: page.querySelector('[data-field="content"]')?.value || "",
      favorite: state.draft?.favorite || false,
      archived: state.draft?.archived || false,
    };
  }

  function applyDraftToForm() {
    if (!state.draft) return;
    const titleEl = page.querySelector('[data-field="title"]');
    const tagsEl = page.querySelector('[data-field="tags"]');
    const contentEl = page.querySelector('[data-field="content"]');
    if (titleEl) titleEl.value = state.draft.title || "";
    if (tagsEl) tagsEl.value = tagsToInput(state.draft.tags);
    if (contentEl) contentEl.value = state.draft.content || "";
    renderEditorBadges();
    updatePreview();
    updateActionLabels();
  }

  function renderEditorBadges() {
    if (!editorBadges || !state.draft) return;
    const badges = [];
    if (state.draft.favorite) badges.push('<span class="note-badge note-badge--favorite">★ Favorita</span>');
    if (state.draft.archived) badges.push('<span class="note-badge note-badge--archived">Arquivada</span>');
    editorBadges.innerHTML = badges.join("");
  }

  function updateActionLabels() {
    const favBtn = page.querySelector('[data-action="toggle-favorite"]');
    const archBtn = page.querySelector('[data-action="toggle-archive"]');
    if (favBtn && state.draft) {
      favBtn.textContent = state.draft.favorite ? "★ Desfavoritar" : "☆ Favoritar";
    }
    if (archBtn && state.draft) {
      archBtn.textContent = state.draft.archived ? "Desarquivar" : "Arquivar";
    }
  }

  function updatePreview() {
    if (!previewEl) return;
    const content = page.querySelector('[data-field="content"]')?.value || "";
    previewEl.innerHTML = renderMarkdown(content);
  }

  function showEditor(show) {
    if (editorEmpty) editorEmpty.hidden = show;
    if (editorForm) editorForm.hidden = !show;
  }

  function selectNote(note) {
    state.selectedId = note?.id || null;
    state.isNew = false;
    state.draft = note
      ? {
          title: note.title,
          content: note.content || "",
          tags: note.tags || [],
          favorite: note.favorite,
          archived: note.archived,
        }
      : null;
    editorError.hidden = true;
    editorStatus.textContent = note ? `Atualizado ${formatNoteDate(note.updated_at)}` : "";
    showEditor(Boolean(note));
    applyDraftToForm();
    renderNoteList();
  }

  function startNewNote() {
    state.selectedId = null;
    state.isNew = true;
    state.draft = { title: "", content: "", tags: [], favorite: false, archived: false };
    editorError.hidden = true;
    editorStatus.textContent = "Nova nota — salve para persistir";
    showEditor(true);
    applyDraftToForm();
    page.querySelector('[data-field="title"]')?.focus();
    renderNoteList();
  }

  /** @param {boolean} [append] */
  async function fetchNotes(append = false) {
    if (append) state.loadingMore = true;
    else {
      state.loading = true;
      state.error = null;
    }
    renderNoteList();

    const textQuery = state.search.trim();
    let result;

    if (textQuery) {
      result = await searchNotes(textQuery, { page: state.page, page_size: PAGE_SIZE });
    } else {
      const params = { page: state.page, page_size: PAGE_SIZE };
      if (state.tagFilter.trim()) params.tag = state.tagFilter.trim();
      if (state.favoriteFilter === "true") params.favorite = true;
      if (state.favoriteFilter === "false") params.favorite = false;
      if (state.archivedFilter === "true") params.archived = true;
      if (state.archivedFilter === "false") params.archived = false;
      result = await listNotes(params);
    }

    if (append) state.loadingMore = false;
    else state.loading = false;

    if (!result.ok) {
      state.error = result.error || "Não foi possível carregar notas";
      if (!append) state.notes = [];
      renderNoteList();
      return;
    }

    const data = result.data || {};
    let items = data.items || [];

    if (textQuery) {
      items = applyClientFilters(items);
    }

    state.total = textQuery ? items.length : data.total ?? items.length;
    state.pages = textQuery ? 1 : data.pages ?? 1;
    state.notes = append ? [...state.notes, ...items] : items;
    renderNoteList();
  }

  /** @param {object[]} items */
  function applyClientFilters(items) {
    let result = [...items];
    const tag = state.tagFilter.trim().toLowerCase();
    if (tag) {
      result = result.filter((note) =>
        (note.tags || []).some((t) => String(t).toLowerCase().includes(tag))
      );
    }
    if (state.favoriteFilter === "true") result = result.filter((n) => n.favorite);
    if (state.favoriteFilter === "false") result = result.filter((n) => !n.favorite);
    if (state.archivedFilter === "true") result = result.filter((n) => n.archived);
    if (state.archivedFilter === "false") result = result.filter((n) => !n.archived);
    return result;
  }

  function resetAndFetch() {
    state.page = 1;
    fetchNotes(false);
  }

  function renderNoteList() {
    if (listMetaEl) {
      listMetaEl.textContent = state.loading ? "" : `${state.notes.length} nota(s)`;
    }

    if (!listEl) return;
    listEl.innerHTML = "";

    if (state.loading) {
      listEl.appendChild(renderLoading("Carregando notas..."));
      renderListFooter();
      return;
    }

    if (state.error && state.notes.length === 0) {
      listEl.appendChild(renderErrorState(state.error, resetAndFetch));
      renderListFooter();
      return;
    }

    if (state.notes.length === 0) {
      listEl.appendChild(renderEmptyListState());
      renderListFooter();
      return;
    }

    state.notes.forEach((note) => {
      const item = document.createElement("button");
      item.type = "button";
      item.className = `note-list-item${state.selectedId === note.id ? " note-list-item--active" : ""}${note.archived ? " note-list-item--archived" : ""}`;
      item.dataset.noteId = note.id;
      item.innerHTML = `
        <span class="note-list-item__title">
          ${note.favorite ? '<span class="note-list-item__star">★</span>' : ""}
          ${escapeHtml(note.title)}
        </span>
        <span class="note-list-item__excerpt">${escapeHtml(excerpt(note.content))}</span>
        ${note.tags?.length ? `<span class="note-list-item__tags">${note.tags.map((t) => `<span class="note-tag">${escapeHtml(t)}</span>`).join("")}</span>` : ""}
      `;
      item.addEventListener("click", () => selectNote(note));
      listEl.appendChild(item);
    });

    renderListFooter();
  }

  function renderListFooter() {
    if (!listFooterEl) return;
    listFooterEl.innerHTML = "";
    if (state.loading || state.error || state.search.trim()) return;

    const hasMore = state.page < state.pages;
    if (hasMore) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "btn btn--secondary btn--block btn--sm";
      btn.textContent = state.loadingMore ? "Carregando..." : "Carregar mais";
      btn.disabled = state.loadingMore;
      btn.addEventListener("click", () => {
        state.page += 1;
        fetchNotes(true);
      });
      listFooterEl.appendChild(btn);
    }
  }

  function setActiveTab(tab) {
    state.activeTab = tab;
    page.querySelectorAll(".notes-tab").forEach((el) => {
      el.classList.toggle("notes-tab--active", el.getAttribute("data-tab") === tab);
    });
    page.querySelector('[data-pane="edit"]').hidden = tab !== "edit";
    page.querySelector('[data-pane="preview"]').hidden = tab !== "preview";
    if (tab === "preview") updatePreview();
  }

  function openModal() {
    modal.hidden = false;
    backdrop.hidden = false;
    modalError.hidden = true;
    modalForm.reset();
    modalForm.querySelector('[name="title"]')?.focus();
  }

  function closeModal() {
    modal.hidden = true;
    backdrop.hidden = true;
  }

  async function saveNote() {
    if (state.saving || !state.draft) return;

    const formValues = getDraftFromForm();
    if (!formValues.title.trim()) {
      editorError.textContent = "Informe um título.";
      editorError.hidden = false;
      return;
    }

    state.saving = true;
    editorError.hidden = true;
    const saveBtn = page.querySelector('[data-action="save-note"]');
    if (saveBtn) {
      saveBtn.disabled = true;
      saveBtn.textContent = "Salvando...";
    }

    const payload = noteFormToPayload({
      ...formValues,
      favorite: state.draft.favorite,
      archived: state.draft.archived,
    });

    const result = state.isNew || !state.selectedId
      ? await createNote(payload)
      : await updateNote(state.selectedId, payload);

    state.saving = false;
    if (saveBtn) {
      saveBtn.disabled = false;
      saveBtn.textContent = "Salvar";
    }

    if (!result.ok) {
      editorError.textContent = result.error || "Falha ao salvar nota";
      editorError.hidden = false;
      return;
    }

    state.isNew = false;
    state.selectedId = result.data.id;
    state.draft = {
      title: result.data.title,
      content: result.data.content || "",
      tags: result.data.tags || [],
      favorite: result.data.favorite,
      archived: result.data.archived,
    };
    editorStatus.textContent = `Salvo ${formatNoteDate(result.data.updated_at)}`;
    applyDraftToForm();
    resetAndFetch();
  }

  async function toggleFavorite() {
    if (!state.selectedId || state.isNew) return;
    const next = !state.draft?.favorite;
    const result = await updateNote(state.selectedId, { favorite: next });
    if (!result.ok) {
      alert(result.error || "Falha ao atualizar favorito");
      return;
    }
    state.draft.favorite = result.data.favorite;
    applyDraftToForm();
    const idx = state.notes.findIndex((n) => n.id === state.selectedId);
    if (idx >= 0) state.notes[idx] = result.data;
    renderNoteList();
  }

  async function toggleArchive() {
    if (!state.selectedId || state.isNew) return;
    const next = !state.draft?.archived;
    const result = await updateNote(state.selectedId, { archived: next });
    if (!result.ok) {
      alert(result.error || "Falha ao arquivar nota");
      return;
    }
    state.draft.archived = result.data.archived;
    applyDraftToForm();
    resetAndFetch();
  }

  async function handleIndexNote() {
    if (!state.selectedId || state.isNew) {
      alert("Salve a nota antes de indexar.");
      return;
    }
    if (state.indexing) return;

    state.indexing = true;
    const btn = page.querySelector('[data-action="index-note"]');
    if (btn) {
      btn.disabled = true;
      btn.textContent = "Indexando...";
    }

    const result = await indexNote(state.selectedId);

    state.indexing = false;
    if (btn) {
      btn.disabled = false;
      btn.textContent = "Indexar para IA";
    }

    if (!result.ok) {
      alert(result.error || "Falha ao indexar nota");
      return;
    }

    editorStatus.textContent = `Indexado: ${result.data.chunks_indexed} chunk(s)`;
  }

  async function handleDeleteNote() {
    if (!state.selectedId || state.isNew) return;
    const title = state.draft?.title || "esta nota";
    if (!window.confirm(`Excluir "${title}"? Esta ação não pode ser desfeita.`)) return;

    const result = await deleteNote(state.selectedId);
    if (!result.ok) {
      alert(result.error || "Falha ao excluir nota");
      return;
    }

    state.selectedId = null;
    state.draft = null;
    showEditor(false);
    resetAndFetch();
  }

  function renderSemanticResults() {
    if (!semanticResultsEl) return;
    semanticResultsEl.innerHTML = "";

    if (state.semanticLoading) {
      semanticResultsEl.appendChild(renderLoading("Buscando trechos relevantes..."));
      return;
    }

    if (state.semanticError) {
      const err = document.createElement("div");
      err.className = "notes-semantic__error";
      err.textContent = state.semanticError;
      semanticResultsEl.appendChild(err);
      return;
    }

    if (!state.semanticResults) return;

    if (state.semanticResults.length === 0) {
      semanticResultsEl.innerHTML = '<p class="notes-semantic__empty">Nenhum trecho relevante encontrado. Indexe suas notas primeiro.</p>';
      return;
    }

    state.semanticResults.forEach((chunk, index) => {
      const card = document.createElement("article");
      card.className = "semantic-result";
      card.innerHTML = `
        <header class="semantic-result__head">
          <span class="semantic-result__rank">#${index + 1}</span>
          <span class="semantic-result__score">${formatSimilarity(chunk.similarity)} similar</span>
        </header>
        <p class="semantic-result__content">${escapeHtml(chunk.content)}</p>
        <footer class="semantic-result__meta">Fonte: ${chunk.source_type} · ${chunk.source_id}</footer>
      `;
      semanticResultsEl.appendChild(card);
    });
  }

  page.querySelector('[data-action="new-note"]')?.addEventListener("click", openModal);

  page.querySelectorAll('[data-action="close-modal"]').forEach((btn) => {
    btn.addEventListener("click", closeModal);
  });
  backdrop?.addEventListener("click", closeModal);

  page.querySelector('[data-filter="search"]')?.addEventListener("input", (event) => {
    state.search = /** @type {HTMLInputElement} */ (event.target).value;
    resetAndFetch();
  });

  page.querySelector('[data-filter="tag"]')?.addEventListener("input", (event) => {
    state.tagFilter = /** @type {HTMLInputElement} */ (event.target).value;
    resetAndFetch();
  });

  page.querySelector('[data-filter="favorite"]')?.addEventListener("change", (event) => {
    state.favoriteFilter = /** @type {HTMLSelectElement} */ (event.target).value;
    resetAndFetch();
  });

  page.querySelector('[data-filter="archived"]')?.addEventListener("change", (event) => {
    state.archivedFilter = /** @type {HTMLSelectElement} */ (event.target).value;
    resetAndFetch();
  });

  page.querySelectorAll(".notes-tab").forEach((tab) => {
    tab.addEventListener("click", () => setActiveTab(tab.getAttribute("data-tab") || "edit"));
  });

  page.querySelector('[data-field="content"]')?.addEventListener("input", () => {
    if (state.activeTab === "preview") updatePreview();
  });

  page.querySelector('[data-action="save-note"]')?.addEventListener("click", saveNote);
  page.querySelector('[data-action="toggle-favorite"]')?.addEventListener("click", toggleFavorite);
  page.querySelector('[data-action="toggle-archive"]')?.addEventListener("click", toggleArchive);
  page.querySelector('[data-action="index-note"]')?.addEventListener("click", handleIndexNote);
  page.querySelector('[data-action="delete-note"]')?.addEventListener("click", handleDeleteNote);

  modalForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    /** @type {HTMLFormElement} */
    const form = modalForm;
    const payload = noteFormToPayload({
      title: form.title.value,
      tags: form.tags.value,
      content: form.content.value,
      favorite: false,
      archived: false,
    });

    if (!payload.title) {
      modalError.textContent = "Informe um título.";
      modalError.hidden = false;
      return;
    }

    const result = await createNote(payload);
    if (!result.ok) {
      modalError.textContent = result.error || "Falha ao criar nota";
      modalError.hidden = false;
      return;
    }

    closeModal();
    await fetchNotes(false);
    selectNote(result.data);
  });

  page.querySelector('[data-role="semantic-form"]')?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const input = page.querySelector('[data-field="semantic-query"]');
    const query = input?.value.trim();
    if (!query) return;

    state.semanticLoading = true;
    state.semanticError = null;
    state.semanticResults = null;
    renderSemanticResults();

    const result = await searchSemanticNotes(query, 5);

    state.semanticLoading = false;
    if (!result.ok) {
      state.semanticError = result.error || "Falha na busca semântica";
      renderSemanticResults();
      return;
    }

    state.semanticResults = result.data || [];
    renderSemanticResults();
  });

  fetchNotes(false);
}

/** @param {string} message @param {() => void} onRetry */
function renderErrorState(message, onRetry) {
  const wrap = document.createElement("div");
  wrap.className = "empty-state empty-state--error empty-state--compact";
  wrap.innerHTML = `
    <div class="empty-state__icon">⚠</div>
    <h3 class="empty-state__title">Erro ao carregar</h3>
    <p class="empty-state__text">${escapeHtml(message)}</p>
  `;
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "btn btn--secondary btn--sm";
  btn.textContent = "Tentar novamente";
  btn.addEventListener("click", onRetry);
  wrap.appendChild(btn);
  return wrap;
}

function renderEmptyListState() {
  const wrap = document.createElement("div");
  wrap.className = "empty-state empty-state--compact";
  wrap.innerHTML = `
    <div class="empty-state__icon">✎</div>
    <h3 class="empty-state__title">Nenhuma nota</h3>
    <p class="empty-state__text">Crie uma nota ou ajuste os filtros.</p>
  `;
  return wrap;
}
