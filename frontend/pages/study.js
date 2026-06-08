import {
  createFlashcard,
  createStudySession,
  createStudySubject,
  createStudyTopic,
  deleteFlashcard,
  deleteStudySubject,
  deleteStudyTopic,
  generateTopicAIPlan,
  getStudySummary,
  listFlashcards,
  listStudySubjects,
  listStudyTopics,
  reviewFlashcard,
  updateStudySubject,
  updateStudyTopic,
} from "../services/api.js";
import {
  escapeHtml,
  formatMinutes,
  REVIEW_RATINGS,
  statusClass,
  statusLabel,
  SUBJECT_COLORS,
  TOPIC_STATUSES,
} from "../modules/study.js";
import { renderLoading } from "../components/loading.js";

/** @returns {HTMLElement} */
export function renderStudyPage() {
  const page = document.createElement("section");
  page.className = "page page--study";
  page.innerHTML = `
    <div class="page__intro page__intro--row">
      <div>
        <h2 class="page__heading">Estudos</h2>
        <p class="page__description">Matérias, tópicos, flashcards e plano com IA — estilo ENEM.</p>
      </div>
      <div class="study-intro-actions">
        <button type="button" class="btn btn--secondary" data-action="new-subject">Nova matéria</button>
        <button type="button" class="btn btn--primary" data-action="new-topic">Novo tópico</button>
      </div>
    </div>
    <div class="study-summary card-grid" data-role="summary"></div>
    <div class="study-layout">
      <aside class="study-panel">
        <h3 class="study-panel__title">Matérias</h3>
        <div data-role="subjects-list"></div>
      </aside>
      <section class="study-panel study-panel--wide">
        <div class="study-panel__head">
          <h3 class="study-panel__title">Tópicos</h3>
          <div class="study-filters">
            <select class="field__input" data-filter="subject_id"><option value="">Todas matérias</option></select>
            <select class="field__input" data-filter="status">
              <option value="">Todos status</option>
              ${TOPIC_STATUSES.map((s) => `<option value="${s.value}">${s.label}</option>`).join("")}
            </select>
            <select class="field__input" data-filter="difficulty">
              <option value="">Dificuldade</option>
              ${[1, 2, 3, 4, 5].map((d) => `<option value="${d}">${d}</option>`).join("")}
            </select>
          </div>
        </div>
        <div data-role="topics-list"></div>
        <div class="study-ai-plan" data-role="ai-plan" hidden>
          <h4>Plano gerado pela IA</h4>
          <pre class="study-ai-plan__content" data-role="ai-plan-content"></pre>
        </div>
      </section>
    </div>
    <section class="study-panel study-flashcards">
      <div class="study-panel__head">
        <h3 class="study-panel__title">Revisão de flashcards</h3>
        <button type="button" class="btn btn--ghost btn--sm" data-action="new-flashcard">+ Flashcard</button>
      </div>
      <div class="flashcard-review" data-role="flashcard-review"></div>
    </section>
    <section class="study-panel">
      <h3 class="study-panel__title">Registrar sessão</h3>
      <form class="study-session-form" data-role="session-form">
        <div class="field-row">
          <label class="field"><span class="field__label">Matéria</span><select name="subject_id" class="field__input" data-role="session-subject"><option value="">—</option></select></label>
          <label class="field"><span class="field__label">Tópico</span><select name="topic_id" class="field__input" data-role="session-topic"><option value="">—</option></select></label>
          <label class="field"><span class="field__label">Minutos</span><input type="number" name="duration_minutes" class="field__input" min="1" max="600" value="25" required /></label>
          <label class="field"><span class="field__label">Técnica</span><input type="text" name="technique" class="field__input" placeholder="Pomodoro, mapa mental..." /></label>
        </div>
        <button type="submit" class="btn btn--primary">Registrar sessão</button>
        <p class="form-error" data-role="session-error" hidden></p>
      </form>
    </section>
    <div class="modal-backdrop" data-role="modal-backdrop" hidden></div>
    <div class="modal" data-role="modal" hidden>
      <div class="modal__panel modal__panel--wide">
        <header class="modal__header">
          <h3 class="modal__title" data-role="modal-title">Formulário</h3>
          <button type="button" class="btn btn--ghost btn--icon" data-action="close-modal">✕</button>
        </header>
        <div class="modal__body" data-role="modal-body"></div>
      </div>
    </div>
  `;
  initStudyPage(page);
  return page;
}

/** @param {HTMLElement} page */
function initStudyPage(page) {
  const state = {
    summary: null,
    subjects: [],
    topics: [],
    flashcards: [],
    reviewIndex: 0,
    reviewFlipped: false,
    selectedTopicId: null,
    loading: true,
    error: null,
    filters: { subject_id: "", status: "", difficulty: "" },
    modalMode: null,
    editingId: null,
  };

  const summaryEl = page.querySelector('[data-role="summary"]');
  const subjectsEl = page.querySelector('[data-role="subjects-list"]');
  const topicsEl = page.querySelector('[data-role="topics-list"]');
  const flashcardEl = page.querySelector('[data-role="flashcard-review"]');
  const aiPlanEl = page.querySelector('[data-role="ai-plan"]');
  const aiPlanContent = page.querySelector('[data-role="ai-plan-content"]');
  const modal = page.querySelector('[data-role="modal"]');
  const backdrop = page.querySelector('[data-role="modal-backdrop"]');
  const modalBody = page.querySelector('[data-role="modal-body"]');
  const modalTitle = page.querySelector('[data-role="modal-title"]');

  async function loadAll() {
    state.loading = true;
    state.error = null;
    render();

    const topicParams = {};
    if (state.filters.subject_id) topicParams.subject_id = state.filters.subject_id;
    if (state.filters.status) topicParams.status = state.filters.status;
    if (state.filters.difficulty) topicParams.difficulty = state.filters.difficulty;

    const [summaryRes, subjectsRes, topicsRes, cardsRes] = await Promise.all([
      getStudySummary(),
      listStudySubjects({ page_size: 100 }),
      listStudyTopics({ page_size: 100, ...topicParams }),
      listFlashcards({ page_size: 100, due_only: true }),
    ]);

    state.loading = false;
    if (!summaryRes.ok && !subjectsRes.ok) {
      state.error = summaryRes.error || subjectsRes.error || "Falha ao carregar estudos";
      render();
      return;
    }

    state.summary = summaryRes.ok ? summaryRes.data : null;
    state.subjects = subjectsRes.ok ? subjectsRes.data?.items || [] : [];
    state.topics = topicsRes.ok ? topicsRes.data?.items || [] : [];
    state.flashcards = cardsRes.ok ? cardsRes.data?.items || [] : [];
    state.reviewIndex = 0;
    state.reviewFlipped = false;
    populateFilterSelects();
    render();
  }

  function populateFilterSelects() {
    const subjectFilter = page.querySelector('[data-filter="subject_id"]');
    const sessionSubject = page.querySelector('[data-role="session-subject"]');
    const sessionTopic = page.querySelector('[data-role="session-topic"]');
    const options = state.subjects
      .map((s) => `<option value="${s.id}">${escapeHtml(s.name)}</option>`)
      .join("");
    if (subjectFilter) {
      const current = subjectFilter.value;
      subjectFilter.innerHTML = `<option value="">Todas matérias</option>${options}`;
      subjectFilter.value = current;
    }
    if (sessionSubject) {
      sessionSubject.innerHTML = `<option value="">—</option>${options}`;
    }
    if (sessionTopic) {
      sessionTopic.innerHTML = `<option value="">—</option>${state.topics.map((t) => `<option value="${t.id}">${escapeHtml(t.title)}</option>`).join("")}`;
    }
  }

  function renderSummary() {
    if (!summaryEl) return;
    summaryEl.innerHTML = "";
    if (state.loading) {
      summaryEl.appendChild(renderLoading("Carregando resumo..."));
      return;
    }
    if (state.error && !state.summary) {
      summaryEl.innerHTML = `<div class="empty-state empty-state--error empty-state--compact"><p>${escapeHtml(state.error)}</p><button type="button" class="btn btn--secondary btn--sm" data-action="retry">Tentar novamente</button></div>`;
      summaryEl.querySelector('[data-action="retry"]')?.addEventListener("click", loadAll);
      return;
    }
    const s = state.summary || {};
    const cards = [
      { t: "Matérias", v: s.total_subjects ?? 0, i: "📚" },
      { t: "Em progresso", v: s.topics_in_progress ?? 0, i: "▶" },
      { t: "Dominados", v: s.topics_mastered ?? 0, i: "✓" },
      { t: "Flashcards due", v: s.flashcards_due ?? 0, i: "🃏" },
      { t: "Min hoje", v: formatMinutes(s.minutes_studied_today), i: "⏱" },
      { t: "Min semana", v: formatMinutes(s.minutes_studied_week), i: "📅" },
    ];
    cards.forEach((c) => {
      const el = document.createElement("article");
      el.className = "card study-summary-card";
      el.innerHTML = `<div class="card__head"><span class="card__icon">${c.i}</span><h4 class="card__title">${c.t}</h4></div><p class="card__value">${c.v}</p>`;
      summaryEl.appendChild(el);
    });
  }

  function renderSubjects() {
    if (!subjectsEl) return;
    subjectsEl.innerHTML = "";
    if (state.loading) return;
    if (!state.subjects.length) {
      subjectsEl.innerHTML = `<p class="study-empty">Nenhuma matéria cadastrada.</p>`;
      return;
    }
    state.subjects.forEach((subject) => {
      const item = document.createElement("div");
      item.className = "study-subject-item";
      item.innerHTML = `
        <span class="study-subject-item__dot" style="background:${subject.color || "#8b5cf6"}"></span>
        <div class="study-subject-item__body">
          <strong>${escapeHtml(subject.name)}</strong>
          ${subject.description ? `<p>${escapeHtml(subject.description)}</p>` : ""}
        </div>
        <div class="study-subject-item__actions">
          <button type="button" class="btn btn--ghost btn--sm" data-action="edit-subject" data-id="${subject.id}">Editar</button>
          <button type="button" class="btn btn--ghost btn--sm btn--danger" data-action="delete-subject" data-id="${subject.id}">Excluir</button>
        </div>
      `;
      subjectsEl.appendChild(item);
    });
  }

  function renderTopics() {
    if (!topicsEl) return;
    topicsEl.innerHTML = "";
    if (state.loading) {
      topicsEl.appendChild(renderLoading("Carregando tópicos..."));
      return;
    }
    if (!state.topics.length) {
      topicsEl.innerHTML = `<div class="empty-state empty-state--compact"><p>Nenhum tópico encontrado.</p></div>`;
      return;
    }
    state.topics.forEach((topic) => {
      const card = document.createElement("article");
      card.className = "study-topic-card";
      card.innerHTML = `
        <header class="study-topic-card__head">
          <h4>${escapeHtml(topic.title)}</h4>
          <span class="topic-status ${statusClass(topic.status)}">${statusLabel(topic.status)}</span>
        </header>
        ${topic.content ? `<p class="study-topic-card__content">${escapeHtml(topic.content.slice(0, 200))}${topic.content.length > 200 ? "…" : ""}</p>` : ""}
        <footer class="study-topic-card__meta">Dificuldade ${topic.difficulty}/5</footer>
        <div class="study-topic-card__actions">
          <button type="button" class="btn btn--ghost btn--sm" data-action="edit-topic" data-id="${topic.id}">Editar</button>
          <button type="button" class="btn btn--ghost btn--sm" data-action="ai-plan" data-id="${topic.id}">Plano IA</button>
          <button type="button" class="btn btn--ghost btn--sm btn--danger" data-action="delete-topic" data-id="${topic.id}">Excluir</button>
        </div>
      `;
      topicsEl.appendChild(card);
    });
  }

  function renderFlashcards() {
    if (!flashcardEl) return;
    flashcardEl.innerHTML = "";
    if (state.loading) return;
    if (!state.flashcards.length) {
      flashcardEl.innerHTML = `<div class="empty-state empty-state--compact"><p>Nenhum flashcard para revisar agora. 🎉</p></div>`;
      return;
    }
    const card = state.flashcards[state.reviewIndex];
    if (!card) return;

    const wrap = document.createElement("div");
    wrap.className = "flashcard-ui";
    wrap.innerHTML = `
      <p class="flashcard-ui__counter">${state.reviewIndex + 1} / ${state.flashcards.length}</p>
      <button type="button" class="flashcard-ui__card ${state.reviewFlipped ? "flashcard-ui__card--flipped" : ""}" data-action="flip">
        <div class="flashcard-ui__face flashcard-ui__face--front">${escapeHtml(card.front)}</div>
        <div class="flashcard-ui__face flashcard-ui__face--back">${escapeHtml(card.back)}</div>
      </button>
      <p class="flashcard-ui__hint">${state.reviewFlipped ? "Como foi?" : "Toque para ver o verso"}</p>
      <div class="flashcard-ui__ratings" ${state.reviewFlipped ? "" : "hidden"}>
        ${REVIEW_RATINGS.map((r) => `<button type="button" class="btn btn--ghost btn--sm ${r.cls}" data-action="rate" data-rating="${r.value}" data-id="${card.id}">${r.label}</button>`).join("")}
      </div>
    `;
    flashcardEl.appendChild(wrap);
  }

  function render() {
    renderSummary();
    renderSubjects();
    renderTopics();
    renderFlashcards();
  }

  function openModal(title, html, onSubmit) {
    modalTitle.textContent = title;
    modalBody.innerHTML = html;
    modal.hidden = false;
    backdrop.hidden = false;
    const form = modalBody.querySelector("form");
    form?.addEventListener("submit", onSubmit, { once: true });
  }

  function closeModal() {
    modal.hidden = true;
    backdrop.hidden = true;
    state.editingId = null;
  }

  page.querySelector('[data-action="new-subject"]')?.addEventListener("click", () => {
    const colorOptions = SUBJECT_COLORS.map((c) => `<option value="${c}">${c}</option>`).join("");
    openModal(
      "Nova matéria",
      `<form data-role="modal-form">
        <label class="field"><span class="field__label">Nome *</span><input name="name" class="field__input" required /></label>
        <label class="field"><span class="field__label">Descrição</span><textarea name="description" class="field__input field__input--textarea" rows="2"></textarea></label>
        <label class="field"><span class="field__label">Cor</span><select name="color" class="field__input">${colorOptions}</select></label>
        <footer class="modal__footer"><button type="button" class="btn btn--ghost" data-action="close-modal">Cancelar</button><button type="submit" class="btn btn--primary">Salvar</button></footer>
      </form>`,
      async (e) => {
        e.preventDefault();
        const fd = new FormData(e.target);
        const result = await createStudySubject({
          name: String(fd.get("name")),
          description: String(fd.get("description") || "") || null,
          color: String(fd.get("color")),
        });
        if (!result.ok) { alert(result.error); return; }
        closeModal();
        loadAll();
      }
    );
    modalBody.querySelectorAll('[data-action="close-modal"]').forEach((b) => b.addEventListener("click", closeModal));
  });

  page.querySelector('[data-action="new-topic"]')?.addEventListener("click", () => showTopicModal());
  page.querySelector('[data-action="new-flashcard"]')?.addEventListener("click", () => showFlashcardModal());
  page.querySelectorAll('[data-action="close-modal"]').forEach((b) => b.addEventListener("click", closeModal));
  backdrop?.addEventListener("click", closeModal);

  function showTopicModal(topic = null) {
    const subjectOptions = state.subjects.map((s) => `<option value="${s.id}" ${topic?.subject_id === s.id ? "selected" : ""}>${escapeHtml(s.name)}</option>`).join("");
    openModal(
      topic ? "Editar tópico" : "Novo tópico",
      `<form>
        <label class="field"><span class="field__label">Matéria *</span><select name="subject_id" class="field__input" required>${subjectOptions}</select></label>
        <label class="field"><span class="field__label">Título *</span><input name="title" class="field__input" required value="${topic ? escapeHtml(topic.title) : ""}" /></label>
        <label class="field"><span class="field__label">Conteúdo</span><textarea name="content" class="field__input field__input--textarea" rows="4">${topic?.content ? escapeHtml(topic.content) : ""}</textarea></label>
        <div class="field-row">
          <label class="field"><span class="field__label">Status</span><select name="status" class="field__input">${TOPIC_STATUSES.map((s) => `<option value="${s.value}" ${topic?.status === s.value ? "selected" : ""}>${s.label}</option>`).join("")}</select></label>
          <label class="field"><span class="field__label">Dificuldade</span><select name="difficulty" class="field__input">${[1,2,3,4,5].map((d) => `<option value="${d}" ${topic?.difficulty === d ? "selected" : ""}>${d}</option>`).join("")}</select></label>
        </div>
        <footer class="modal__footer"><button type="button" class="btn btn--ghost" data-action="close-modal">Cancelar</button><button type="submit" class="btn btn--primary">Salvar</button></footer>
      </form>`,
      async (e) => {
        e.preventDefault();
        const fd = new FormData(e.target);
        const payload = {
          subject_id: String(fd.get("subject_id")),
          title: String(fd.get("title")),
          content: String(fd.get("content") || "") || null,
          status: String(fd.get("status")),
          difficulty: Number(fd.get("difficulty")),
        };
        const result = topic ? await updateStudyTopic(topic.id, payload) : await createStudyTopic(payload);
        if (!result.ok) { alert(result.error); return; }
        closeModal();
        loadAll();
      }
    );
    modalBody.querySelectorAll('[data-action="close-modal"]').forEach((b) => b.addEventListener("click", closeModal));
  }

  function showFlashcardModal() {
    const topicOptions = state.topics.map((t) => `<option value="${t.id}">${escapeHtml(t.title)}</option>`).join("");
    if (!topicOptions) { alert("Crie um tópico primeiro."); return; }
    openModal(
      "Novo flashcard",
      `<form>
        <label class="field"><span class="field__label">Tópico *</span><select name="topic_id" class="field__input" required>${topicOptions}</select></label>
        <label class="field"><span class="field__label">Frente *</span><textarea name="front" class="field__input field__input--textarea" required rows="2"></textarea></label>
        <label class="field"><span class="field__label">Verso *</span><textarea name="back" class="field__input field__input--textarea" required rows="2"></textarea></label>
        <footer class="modal__footer"><button type="button" class="btn btn--ghost" data-action="close-modal">Cancelar</button><button type="submit" class="btn btn--primary">Criar</button></footer>
      </form>`,
      async (e) => {
        e.preventDefault();
        const fd = new FormData(e.target);
        const result = await createFlashcard({
          topic_id: String(fd.get("topic_id")),
          front: String(fd.get("front")),
          back: String(fd.get("back")),
        });
        if (!result.ok) { alert(result.error); return; }
        closeModal();
        loadAll();
      }
    );
    modalBody.querySelectorAll('[data-action="close-modal"]').forEach((b) => b.addEventListener("click", closeModal));
  }

  page.querySelectorAll("[data-filter]").forEach((el) => {
    el.addEventListener("change", () => {
      state.filters.subject_id = page.querySelector('[data-filter="subject_id"]')?.value || "";
      state.filters.status = page.querySelector('[data-filter="status"]')?.value || "";
      state.filters.difficulty = page.querySelector('[data-filter="difficulty"]')?.value || "";
      loadAll();
    });
  });

  subjectsEl?.addEventListener("click", async (e) => {
    const t = /** @type {HTMLElement} */ (e.target);
    const action = t.closest("[data-action]")?.getAttribute("data-action");
    const id = t.closest("[data-id]")?.getAttribute("data-id");
    if (!action || !id) return;
    const subject = state.subjects.find((s) => s.id === id);
    if (action === "edit-subject" && subject) {
      openModal("Editar matéria", `<form>
        <label class="field"><span class="field__label">Nome</span><input name="name" class="field__input" value="${escapeHtml(subject.name)}" required /></label>
        <label class="field"><span class="field__label">Descrição</span><textarea name="description" class="field__input field__input--textarea" rows="2">${subject.description ? escapeHtml(subject.description) : ""}</textarea></label>
        <footer class="modal__footer"><button type="button" class="btn btn--ghost" data-action="close-modal">Cancelar</button><button type="submit" class="btn btn--primary">Salvar</button></footer>
      </form>`, async (ev) => {
        ev.preventDefault();
        const fd = new FormData(ev.target);
        const result = await updateStudySubject(id, { name: String(fd.get("name")), description: String(fd.get("description") || "") || null });
        if (!result.ok) { alert(result.error); return; }
        closeModal(); loadAll();
      });
      modalBody.querySelectorAll('[data-action="close-modal"]').forEach((b) => b.addEventListener("click", closeModal));
    }
    if (action === "delete-subject") {
      if (!window.confirm(`Excluir matéria "${subject?.name}"?`)) return;
      const result = await deleteStudySubject(id);
      if (!result.ok) alert(result.error);
      else loadAll();
    }
  });

  topicsEl?.addEventListener("click", async (e) => {
    const t = /** @type {HTMLElement} */ (e.target);
    const action = t.closest("[data-action]")?.getAttribute("data-action");
    const id = t.closest("[data-id]")?.getAttribute("data-id");
    if (!action || !id) return;
    const topic = state.topics.find((item) => item.id === id);
    if (action === "edit-topic" && topic) showTopicModal(topic);
    if (action === "delete-topic") {
      if (!window.confirm(`Excluir tópico "${topic?.title}"?`)) return;
      const result = await deleteStudyTopic(id);
      if (!result.ok) alert(result.error);
      else loadAll();
    }
    if (action === "ai-plan") {
      if (aiPlanEl) aiPlanEl.hidden = false;
      if (aiPlanContent) aiPlanContent.textContent = "Gerando plano...";
      const result = await generateTopicAIPlan(id);
      if (!result.ok) {
        if (aiPlanContent) aiPlanContent.textContent = result.error || "IA indisponível";
        return;
      }
      if (aiPlanContent) aiPlanContent.textContent = result.data.plan;
    }
  });

  flashcardEl?.addEventListener("click", async (e) => {
    const t = /** @type {HTMLElement} */ (e.target);
    const action = t.closest("[data-action]")?.getAttribute("data-action");
    if (action === "flip") {
      state.reviewFlipped = !state.reviewFlipped;
      renderFlashcards();
      return;
    }
    if (action === "rate") {
      const rating = t.getAttribute("data-rating");
      const id = t.getAttribute("data-id");
      if (!rating || !id) return;
      const result = await reviewFlashcard(id, rating);
      if (!result.ok) { alert(result.error); return; }
      state.flashcards.splice(state.reviewIndex, 1);
      if (state.reviewIndex >= state.flashcards.length) state.reviewIndex = 0;
      state.reviewFlipped = false;
      renderFlashcards();
      getStudySummary().then((r) => { if (r.ok) { state.summary = r.data; renderSummary(); } });
    }
  });

  page.querySelector('[data-role="session-form"]')?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const form = /** @type {HTMLFormElement} */ (e.target);
    const errEl = page.querySelector('[data-role="session-error"]');
    const payload = {
      duration_minutes: Number(form.duration_minutes.value),
      technique: form.technique.value || null,
      notes: null,
    };
    if (form.subject_id.value) payload.subject_id = form.subject_id.value;
    if (form.topic_id.value) payload.topic_id = form.topic_id.value;
    const result = await createStudySession(payload);
    if (!result.ok) {
      if (errEl) { errEl.textContent = result.error || "Erro"; errEl.hidden = false; }
      return;
    }
    if (errEl) errEl.hidden = true;
    form.reset();
    form.duration_minutes.value = "25";
    loadAll();
  });

  loadAll();
}
