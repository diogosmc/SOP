import {
  Chart,
  LineController,
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
} from "chart.js";
import {
  addWorkoutPlanExercise,
  addWorkoutSetLog,
  createWorkoutExercise,
  createWorkoutLog,
  createWorkoutPlan,
  deleteWorkoutExercise,
  deleteWorkoutLog,
  deleteWorkoutPlan,
  deleteWorkoutPlanExercise,
  getWorkoutPlan,
  getWorkoutProfile,
  getWorkoutProgression,
  getWorkoutSummary,
  listWorkoutExercises,
  listWorkoutLogs,
  listWorkoutPlans,
  updateWorkoutExercise,
  updateWorkoutPlan,
  upsertWorkoutProfile,
} from "../services/api.js";
import {
  DISCLAIMER,
  EXERCISE_TYPES,
  escapeHtml,
  formatDateBR,
  formatKg,
  formatVolume,
  maxLoadByDate,
  WORKOUT_OBJECTIVES,
} from "../modules/workout.js";
import { renderLoading } from "../components/loading.js";

Chart.register(LineController, LineElement, PointElement, CategoryScale, LinearScale, Tooltip, Legend);

/** @returns {HTMLElement} */
export function renderWorkoutPage() {
  const page = document.createElement("section");
  page.className = "page page--workout";
  page.innerHTML = `
    <div class="page__intro page__intro--row">
      <div>
        <h2 class="page__heading">Treino</h2>
        <p class="page__description">Organize planos, registre sessões e acompanhe sua evolução.</p>
      </div>
      <div class="workout-intro-actions">
        <button type="button" class="btn btn--secondary" data-action="new-exercise">Novo exercício</button>
        <button type="button" class="btn btn--secondary" data-action="new-plan">Novo plano</button>
        <button type="button" class="btn btn--primary" data-action="new-log">Registrar treino</button>
      </div>
    </div>
    <p class="workout-disclaimer">${escapeHtml(DISCLAIMER)}</p>
    <div class="workout-summary card-grid" data-role="summary"></div>
    <div class="workout-layout">
      <section class="workout-panel">
        <h3 class="workout-panel__title">Perfil físico</h3>
        <form class="workout-profile-form" data-role="profile-form">
          <div class="field-row">
            <label class="field"><span class="field__label">Altura (cm)</span><input type="number" name="height_cm" class="field__input" min="0" step="0.1" /></label>
            <label class="field"><span class="field__label">Peso (kg)</span><input type="number" name="weight_kg" class="field__input" min="0" step="0.1" /></label>
            <label class="field"><span class="field__label">Objetivo</span>
              <select name="objective" class="field__input">
                <option value="">—</option>
                ${WORKOUT_OBJECTIVES.map((o) => `<option value="${o.value}">${o.label}</option>`).join("")}
              </select>
            </label>
          </div>
          <label class="field"><span class="field__label">Observações</span><textarea name="notes" class="field__input field__input--textarea" rows="2"></textarea></label>
          <button type="submit" class="btn btn--primary btn--sm">Salvar perfil</button>
          <p class="form-error" data-role="profile-error" hidden></p>
        </form>
      </section>
      <section class="workout-panel workout-panel--wide">
        <div class="workout-panel__head">
          <h3 class="workout-panel__title">Progressão de carga</h3>
          <select class="field__input workout-progression-select" data-role="progression-exercise"><option value="">Selecione exercício</option></select>
        </div>
        <div class="workout-chart-wrap">
          <canvas data-role="progression-chart" height="200"></canvas>
        </div>
      </section>
    </div>
    <div class="workout-columns">
      <section class="workout-panel">
        <h3 class="workout-panel__title">Exercícios</h3>
        <div data-role="exercises-list"></div>
      </section>
      <section class="workout-panel">
        <h3 class="workout-panel__title">Planos</h3>
        <div data-role="plans-list"></div>
        <div class="workout-plan-detail" data-role="plan-detail" hidden></div>
      </section>
    </div>
    <section class="workout-panel">
      <h3 class="workout-panel__title">Histórico de treinos</h3>
      <div data-role="logs-list"></div>
    </section>
    <div class="modal-backdrop" data-role="modal-backdrop" hidden></div>
    <div class="modal" data-role="modal" hidden aria-modal="true" role="dialog">
      <div class="modal__panel modal__panel--wide">
        <header class="modal__header">
          <h3 class="modal__title" data-role="modal-title">Formulário</h3>
          <button type="button" class="btn btn--ghost btn--icon" data-action="close-modal">✕</button>
        </header>
        <div class="modal__body" data-role="modal-body"></div>
      </div>
    </div>
  `;
  initWorkoutPage(page);
  return page;
}

/** @param {HTMLElement} page */
function initWorkoutPage(page) {
  /** @type {Chart|null} */
  let chart = null;

  const state = {
    loading: true,
    error: null,
    summary: null,
    profile: null,
    exercises: [],
    plans: [],
    logs: [],
    progression: [],
    selectedPlanId: null,
    selectedPlanDetail: null,
    activeLogId: null,
    modalMode: null,
    editingId: null,
  };

  const summaryEl = page.querySelector('[data-role="summary"]');
  const exercisesEl = page.querySelector('[data-role="exercises-list"]');
  const plansEl = page.querySelector('[data-role="plans-list"]');
  const planDetailEl = page.querySelector('[data-role="plan-detail"]');
  const logsEl = page.querySelector('[data-role="logs-list"]');
  const profileForm = page.querySelector('[data-role="profile-form"]');
  const profileError = page.querySelector('[data-role="profile-error"]');
  const progressionSelect = page.querySelector('[data-role="progression-exercise"]');
  const chartCanvas = page.querySelector('[data-role="progression-chart"]');
  const modal = page.querySelector('[data-role="modal"]');
  const backdrop = page.querySelector('[data-role="modal-backdrop"]');
  const modalTitle = page.querySelector('[data-role="modal-title"]');
  const modalBody = page.querySelector('[data-role="modal-body"]');

  async function loadAll() {
    state.loading = true;
    state.error = null;
    renderAll();

    const [summary, profile, exercises, plans, logs] = await Promise.all([
      getWorkoutSummary(),
      getWorkoutProfile(),
      listWorkoutExercises({ page_size: 100 }),
      listWorkoutPlans({ page_size: 50 }),
      listWorkoutLogs({ page_size: 50 }),
    ]);

    state.loading = false;

    if (!summary.ok && !exercises.ok && !plans.ok && !logs.ok) {
      state.error = summary.error || exercises.error || "Não foi possível conectar ao módulo de treino";
    }

    state.summary = summary.ok ? summary.data : null;
    if (profile.ok) state.profile = profile.data;
    state.exercises = exercises.ok ? exercises.data?.items || [] : [];
    state.plans = plans.ok ? plans.data?.items || [] : [];
    state.logs = logs.ok ? logs.data?.items || [] : [];

    fillProfileForm();
    updateProgressionSelect();
    await loadProgression();
    renderAll();
  }

  function fillProfileForm() {
    if (!profileForm) return;
    const p = state.profile;
    profileForm.height_cm.value = p?.height_cm ?? "";
    profileForm.weight_kg.value = p?.weight_kg ?? "";
    profileForm.objective.value = p?.objective ?? "";
    profileForm.notes.value = p?.notes ?? "";
  }

  function updateProgressionSelect() {
    if (!progressionSelect) return;
    const current = progressionSelect.value;
    progressionSelect.innerHTML =
      `<option value="">Selecione exercício</option>` +
      state.exercises.map((e) => `<option value="${e.id}">${escapeHtml(e.name)}</option>`).join("");
    if (current && state.exercises.some((e) => e.id === current)) {
      progressionSelect.value = current;
    }
  }

  async function loadProgression() {
    const exerciseId = progressionSelect?.value;
    const params = exerciseId ? { exercise_id: exerciseId } : {};
    const result = await getWorkoutProgression(params);
    state.progression = result.ok ? result.data || [] : [];
    renderChart();
  }

  function renderChart() {
    if (!chartCanvas) return;
    const points = maxLoadByDate(state.progression);
    const labels = points.map(([d]) => formatDateBR(d));
    const data = points.map(([, load]) => load);

    if (chart) {
      chart.destroy();
      chart = null;
    }

    if (!points.length) return;

    chart = new Chart(chartCanvas, {
      type: "line",
      data: {
        labels,
        datasets: [
          {
            label: "Carga máxima (kg)",
            data,
            borderColor: "#8b5cf6",
            backgroundColor: "rgba(139, 92, 246, 0.15)",
            tension: 0.3,
            fill: true,
          },
        ],
      },
      options: {
        responsive: true,
        plugins: { legend: { labels: { color: "#a1a1aa" } } },
        scales: {
          x: { ticks: { color: "#71717a" }, grid: { color: "rgba(255,255,255,0.06)" } },
          y: { ticks: { color: "#71717a" }, grid: { color: "rgba(255,255,255,0.06)" } },
        },
      },
    });
  }

  function renderAll() {
    renderSummary();
    renderExercises();
    renderPlans();
    renderLogs();
  }

  function renderSummary() {
    if (!summaryEl) return;
    if (state.loading) {
      summaryEl.innerHTML = "";
      summaryEl.appendChild(renderLoading("Carregando resumo..."));
      return;
    }
    if (state.error && !state.summary) {
      summaryEl.innerHTML = `<div class="empty-state empty-state--error empty-state--compact"><p>${escapeHtml(state.error)}</p><button type="button" class="btn btn--secondary btn--sm" data-action="retry">Tentar novamente</button></div>`;
      summaryEl.querySelector('[data-action="retry"]')?.addEventListener("click", loadAll);
      return;
    }
    const s = state.summary;
    const cards = [
      { t: "Treinos na semana", v: s?.workouts_this_week ?? "—", i: "🏋" },
      { t: "Volume semanal", v: s ? formatVolume(s.total_volume_week) : "—", i: "📊" },
      { t: "Último treino", v: formatDateBR(s?.last_workout_date), i: "📅" },
      { t: "Plano ativo", v: s?.active_plan || "Nenhum", i: "📋" },
    ];
    summaryEl.innerHTML = "";
    cards.forEach((c) => {
      const el = document.createElement("article");
      el.className = "card workout-card";
      el.innerHTML = `<div class="card__head"><span class="card__icon">${c.i}</span><h4 class="card__title">${escapeHtml(String(c.t))}</h4></div><p class="card__value">${escapeHtml(String(c.v))}</p>`;
      summaryEl.appendChild(el);
    });
  }

  function renderExercises() {
    if (!exercisesEl) return;
    if (state.loading) {
      exercisesEl.innerHTML = "";
      exercisesEl.appendChild(renderLoading("Carregando exercícios..."));
      return;
    }
    if (!state.exercises.length) {
      exercisesEl.innerHTML = `<div class="empty-state empty-state--compact"><p>Nenhum exercício cadastrado.</p></div>`;
      return;
    }
    exercisesEl.innerHTML = state.exercises
      .map(
        (e) => `
      <article class="workout-item" data-id="${e.id}">
        <div class="workout-item__body">
          <strong>${escapeHtml(e.name)}</strong>
          <span class="workout-item__meta">${escapeHtml(e.muscle_group || "—")} · ${escapeHtml(e.exercise_type)}</span>
        </div>
        <div class="workout-item__actions">
          ${e.user_id ? `<button type="button" class="btn btn--ghost btn--sm" data-action="edit-exercise" data-id="${e.id}">Editar</button>
          <button type="button" class="btn btn--ghost btn--sm btn--danger" data-action="delete-exercise" data-id="${e.id}">Excluir</button>` : `<span class="workout-item__badge">Global</span>`}
        </div>
      </article>`
      )
      .join("");
  }

  function renderPlans() {
    if (!plansEl) return;
    if (state.loading) {
      plansEl.innerHTML = "";
      plansEl.appendChild(renderLoading("Carregando planos..."));
      return;
    }
    if (!state.plans.length) {
      plansEl.innerHTML = `<div class="empty-state empty-state--compact"><p>Nenhum plano criado.</p></div>`;
      if (planDetailEl) planDetailEl.hidden = true;
      return;
    }
    plansEl.innerHTML = state.plans
      .map(
        (p) => `
      <article class="workout-item ${state.selectedPlanId === p.id ? "workout-item--active" : ""}" data-id="${p.id}">
        <div class="workout-item__body">
          <strong>${escapeHtml(p.name)}</strong>
          <span class="workout-item__meta">${p.active ? "Ativo" : "Inativo"}${p.objective ? ` · ${escapeHtml(p.objective)}` : ""}</span>
        </div>
        <div class="workout-item__actions">
          <button type="button" class="btn btn--ghost btn--sm" data-action="view-plan" data-id="${p.id}">Ver</button>
          <button type="button" class="btn btn--ghost btn--sm" data-action="edit-plan" data-id="${p.id}">Editar</button>
          <button type="button" class="btn btn--ghost btn--sm btn--danger" data-action="delete-plan" data-id="${p.id}">Excluir</button>
        </div>
      </article>`
      )
      .join("");
    renderPlanDetail();
  }

  function renderPlanDetail() {
    if (!planDetailEl) return;
    const detail = state.selectedPlanDetail;
    if (!detail) {
      planDetailEl.hidden = true;
      return;
    }
    planDetailEl.hidden = false;
    const exercises = detail.exercises || [];
    planDetailEl.innerHTML = `
      <h4>${escapeHtml(detail.name)} — exercícios</h4>
      <button type="button" class="btn btn--secondary btn--sm" data-action="add-plan-exercise">+ Exercício ao plano</button>
      <ul class="workout-plan-exercises">
        ${exercises.length ? exercises.map((pe) => `
          <li>
            <span>${escapeHtml(pe.exercise_name || "Exercício")} · ${escapeHtml(pe.day_label || "—")} · ${pe.sets || "—"}x${escapeHtml(pe.reps || "—")} ${pe.target_load_kg ? `@ ${formatKg(pe.target_load_kg)}` : ""}</span>
            <button type="button" class="btn btn--ghost btn--sm btn--danger" data-action="remove-plan-exercise" data-pe-id="${pe.id}">Remover</button>
          </li>`).join("") : "<li>Nenhum exercício no plano.</li>"}
      </ul>
    `;
  }

  function renderLogs() {
    if (!logsEl) return;
    if (state.loading) {
      logsEl.innerHTML = "";
      logsEl.appendChild(renderLoading("Carregando histórico..."));
      return;
    }
    if (!state.logs.length) {
      logsEl.innerHTML = `<div class="empty-state empty-state--compact"><p>Nenhum treino registrado.</p></div>`;
      return;
    }
    logsEl.innerHTML = state.logs
      .map(
        (log) => `
      <article class="workout-log-card">
        <div class="workout-log-card__head">
          <strong>${formatDateBR(log.date)}</strong>
          <span>${log.duration_minutes ? `${log.duration_minutes} min` : "—"} · ${log.completed ? "Concluído" : "Parcial"}</span>
        </div>
        <p class="workout-log-card__notes">${escapeHtml(log.notes || "")}</p>
        <div class="workout-log-card__actions">
          <button type="button" class="btn btn--ghost btn--sm" data-action="add-set" data-id="${log.id}">+ Série</button>
          <button type="button" class="btn btn--ghost btn--sm btn--danger" data-action="delete-log" data-id="${log.id}">Excluir</button>
        </div>
      </article>`
      )
      .join("");
  }

  function openModal(title) {
    if (modalTitle) modalTitle.textContent = title;
    if (modal) modal.hidden = false;
    if (backdrop) backdrop.hidden = false;
  }

  function closeModal() {
    if (modal) modal.hidden = true;
    if (backdrop) backdrop.hidden = true;
    if (modalBody) modalBody.innerHTML = "";
    state.modalMode = null;
    state.editingId = null;
  }

  function showExerciseModal(mode, exercise = null) {
    state.modalMode = mode;
    state.editingId = exercise?.id || null;
    if (!modalBody) return;
    modalBody.innerHTML = `
      <form data-role="modal-form">
        <label class="field"><span class="field__label">Nome *</span><input name="name" class="field__input" required value="${escapeHtml(exercise?.name || "")}" /></label>
        <label class="field"><span class="field__label">Grupo muscular</span><input name="muscle_group" class="field__input" value="${escapeHtml(exercise?.muscle_group || "")}" /></label>
        <label class="field"><span class="field__label">Tipo</span>
          <select name="exercise_type" class="field__input">
            ${EXERCISE_TYPES.map((t) => `<option value="${t.value}" ${exercise?.exercise_type === t.value ? "selected" : ""}>${t.label}</option>`).join("")}
          </select>
        </label>
        <label class="field"><span class="field__label">Instruções</span><textarea name="instructions" class="field__input field__input--textarea" rows="2">${escapeHtml(exercise?.instructions || "")}</textarea></label>
        <p class="form-error" data-role="modal-error" hidden></p>
        <footer class="modal__footer"><button type="button" class="btn btn--ghost" data-action="close-modal">Cancelar</button><button type="submit" class="btn btn--primary">Salvar</button></footer>
      </form>`;
    openModal(mode === "edit" ? "Editar exercício" : "Novo exercício");
  }

  function showPlanModal(mode, plan = null) {
    state.modalMode = mode;
    state.editingId = plan?.id || null;
    if (!modalBody) return;
    modalBody.innerHTML = `
      <form data-role="modal-form" data-form="plan">
        <label class="field"><span class="field__label">Nome *</span><input name="name" class="field__input" required value="${escapeHtml(plan?.name || "")}" /></label>
        <label class="field"><span class="field__label">Descrição</span><textarea name="description" class="field__input field__input--textarea" rows="2">${escapeHtml(plan?.description || "")}</textarea></label>
        <label class="field"><span class="field__label">Objetivo</span><input name="objective" class="field__input" value="${escapeHtml(plan?.objective || "")}" /></label>
        <label class="field field--checkbox"><input type="checkbox" name="active" ${plan ? (plan.active ? "checked" : "") : "checked"} /><span>Plano ativo</span></label>
        <p class="form-error" data-role="modal-error" hidden></p>
        <footer class="modal__footer"><button type="button" class="btn btn--ghost" data-action="close-modal">Cancelar</button><button type="submit" class="btn btn--primary">Salvar</button></footer>
      </form>`;
    openModal(mode === "edit" ? "Editar plano" : "Novo plano");
  }

  function showLogModal() {
    state.modalMode = "log";
    const today = new Date().toISOString().slice(0, 10);
    if (!modalBody) return;
    modalBody.innerHTML = `
      <form data-role="modal-form" data-form="log">
        <label class="field"><span class="field__label">Data *</span><input type="date" name="date" class="field__input" required value="${today}" /></label>
        <label class="field"><span class="field__label">Plano</span>
          <select name="plan_id" class="field__input"><option value="">—</option>${state.plans.map((p) => `<option value="${p.id}">${escapeHtml(p.name)}</option>`).join("")}</select>
        </label>
        <label class="field"><span class="field__label">Duração (min)</span><input type="number" name="duration_minutes" class="field__input" min="1" max="600" /></label>
        <label class="field"><span class="field__label">Observações</span><textarea name="notes" class="field__input field__input--textarea" rows="2"></textarea></label>
        <label class="field field--checkbox"><input type="checkbox" name="completed" checked /><span>Treino concluído</span></label>
        <p class="form-error" data-role="modal-error" hidden></p>
        <footer class="modal__footer"><button type="button" class="btn btn--ghost" data-action="close-modal">Cancelar</button><button type="submit" class="btn btn--primary">Registrar</button></footer>
      </form>`;
    openModal("Registrar treino");
  }

  function showSetModal(logId) {
    state.modalMode = "set";
    state.activeLogId = logId;
    if (!modalBody) return;
    modalBody.innerHTML = `
      <form data-role="modal-form" data-form="set">
        <label class="field"><span class="field__label">Exercício *</span>
          <select name="exercise_id" class="field__input" required><option value="">—</option>${state.exercises.map((e) => `<option value="${e.id}">${escapeHtml(e.name)}</option>`).join("")}</select>
        </label>
        <div class="field-row">
          <label class="field"><span class="field__label">Série #</span><input type="number" name="set_number" class="field__input" min="1" value="1" required /></label>
          <label class="field"><span class="field__label">Reps</span><input type="number" name="reps" class="field__input" min="0" value="10" required /></label>
          <label class="field"><span class="field__label">Carga (kg)</span><input type="number" name="load_kg" class="field__input" min="0" step="0.5" /></label>
        </div>
        <label class="field"><span class="field__label">Observações</span><input name="notes" class="field__input" /></label>
        <p class="form-error" data-role="modal-error" hidden></p>
        <footer class="modal__footer"><button type="button" class="btn btn--ghost" data-action="close-modal">Cancelar</button><button type="submit" class="btn btn--primary">Salvar série</button></footer>
      </form>`;
    openModal("Registrar série");
  }

  function showAddPlanExerciseModal() {
    if (!state.selectedPlanId || !modalBody) return;
    state.modalMode = "plan-exercise";
    modalBody.innerHTML = `
      <form data-role="modal-form" data-form="plan-exercise">
        <label class="field"><span class="field__label">Exercício *</span>
          <select name="exercise_id" class="field__input" required><option value="">—</option>${state.exercises.map((e) => `<option value="${e.id}">${escapeHtml(e.name)}</option>`).join("")}</select>
        </label>
        <div class="field-row">
          <label class="field"><span class="field__label">Dia</span><input name="day_label" class="field__input" placeholder="A, B, Seg..." /></label>
          <label class="field"><span class="field__label">Séries</span><input type="number" name="sets" class="field__input" min="1" /></label>
          <label class="field"><span class="field__label">Reps</span><input name="reps" class="field__input" placeholder="8-12" /></label>
        </div>
        <div class="field-row">
          <label class="field"><span class="field__label">Carga alvo (kg)</span><input type="number" name="target_load_kg" class="field__input" min="0" step="0.5" /></label>
          <label class="field"><span class="field__label">Descanso (s)</span><input type="number" name="rest_seconds" class="field__input" min="0" /></label>
          <label class="field"><span class="field__label">Ordem</span><input type="number" name="order_index" class="field__input" value="0" /></label>
        </div>
        <p class="form-error" data-role="modal-error" hidden></p>
        <footer class="modal__footer"><button type="button" class="btn btn--ghost" data-action="close-modal">Cancelar</button><button type="submit" class="btn btn--primary">Adicionar</button></footer>
      </form>`;
    openModal("Adicionar exercício ao plano");
  }

  page.querySelector('[data-action="new-exercise"]')?.addEventListener("click", () => showExerciseModal("create"));
  page.querySelector('[data-action="new-plan"]')?.addEventListener("click", () => showPlanModal("create"));
  page.querySelector('[data-action="new-log"]')?.addEventListener("click", showLogModal);
  page.querySelectorAll('[data-action="close-modal"]').forEach((btn) => btn.addEventListener("click", closeModal));
  backdrop?.addEventListener("click", closeModal);
  progressionSelect?.addEventListener("change", loadProgression);

  profileForm?.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    if (profileError) profileError.hidden = true;
    const fd = new FormData(profileForm);
    const payload = {
      height_cm: fd.get("height_cm") ? String(fd.get("height_cm")) : null,
      weight_kg: fd.get("weight_kg") ? String(fd.get("weight_kg")) : null,
      objective: fd.get("objective") || null,
      notes: fd.get("notes") || null,
    };
    const result = await upsertWorkoutProfile(payload);
    if (!result.ok) {
      if (profileError) {
        profileError.textContent = result.error || "Erro ao salvar perfil";
        profileError.hidden = false;
      }
      return;
    }
    state.profile = result.data;
  });

  page.addEventListener("click", async (ev) => {
    const target = ev.target;
    if (!(target instanceof HTMLElement)) return;
    const action = target.getAttribute("data-action");
    const id = target.getAttribute("data-id");

    if (action === "edit-exercise" && id) {
      const exercise = state.exercises.find((e) => e.id === id);
      if (exercise) showExerciseModal("edit", exercise);
    }
    if (action === "delete-exercise" && id) {
      if (!confirm("Excluir este exercício?")) return;
      await deleteWorkoutExercise(id);
      loadAll();
    }
    if (action === "view-plan" && id) {
      state.selectedPlanId = id;
      const detail = await getWorkoutPlan(id);
      state.selectedPlanDetail = detail.ok ? detail.data : null;
      renderPlans();
    }
    if (action === "edit-plan" && id) {
      const plan = state.plans.find((p) => p.id === id);
      if (plan) showPlanModal("edit", plan);
    }
    if (action === "delete-plan" && id) {
      if (!confirm("Excluir este plano?")) return;
      await deleteWorkoutPlan(id);
      if (state.selectedPlanId === id) {
        state.selectedPlanId = null;
        state.selectedPlanDetail = null;
      }
      loadAll();
    }
    if (action === "add-plan-exercise") showAddPlanExerciseModal();
    if (action === "remove-plan-exercise") {
      const peId = target.getAttribute("data-pe-id");
      if (!peId || !state.selectedPlanId || !confirm("Remover exercício do plano?")) return;
      await deleteWorkoutPlanExercise(state.selectedPlanId, peId);
      const detail = await getWorkoutPlan(state.selectedPlanId);
      state.selectedPlanDetail = detail.ok ? detail.data : null;
      renderPlanDetail();
    }
    if (action === "add-set" && id) showSetModal(id);
    if (action === "delete-log" && id) {
      if (!confirm("Excluir este treino?")) return;
      await deleteWorkoutLog(id);
      loadAll();
    }
  });

  modalBody?.addEventListener("submit", async (ev) => {
    const form = ev.target;
    if (!(form instanceof HTMLFormElement) || !form.matches('[data-role="modal-form"]')) return;
    ev.preventDefault();
    const errEl = form.querySelector('[data-role="modal-error"]');
    if (errEl) errEl.hidden = true;
    const fd = new FormData(form);
    const formType = form.getAttribute("data-form");

    if (!formType && (state.modalMode === "create" || state.modalMode === "edit")) {
      const payload = {
        name: fd.get("name"),
        muscle_group: fd.get("muscle_group") || null,
        exercise_type: fd.get("exercise_type"),
        instructions: fd.get("instructions") || null,
      };
      const result =
        state.modalMode === "edit" && state.editingId
          ? await updateWorkoutExercise(state.editingId, payload)
          : await createWorkoutExercise(payload);
      if (!result.ok) {
        if (errEl) {
          errEl.textContent = result.error || "Erro ao salvar";
          errEl.hidden = false;
        }
        return;
      }
      closeModal();
      loadAll();
      return;
    }

    if (formType === "plan") {
      const payload = {
        name: fd.get("name"),
        description: fd.get("description") || null,
        objective: fd.get("objective") || null,
        active: fd.has("active"),
      };
      const result =
        state.modalMode === "edit" && state.editingId
          ? await updateWorkoutPlan(state.editingId, payload)
          : await createWorkoutPlan(payload);
      if (!result.ok) {
        if (errEl) {
          errEl.textContent = result.error || "Erro ao salvar plano";
          errEl.hidden = false;
        }
        return;
      }
      closeModal();
      loadAll();
      return;
    }

    if (formType === "log") {
      const payload = {
        date: fd.get("date"),
        plan_id: fd.get("plan_id") || null,
        duration_minutes: fd.get("duration_minutes") ? Number(fd.get("duration_minutes")) : null,
        notes: fd.get("notes") || null,
        completed: fd.has("completed"),
      };
      const result = await createWorkoutLog(payload);
      if (!result.ok) {
        if (errEl) {
          errEl.textContent = result.error || "Erro ao registrar treino";
          errEl.hidden = false;
        }
        return;
      }
      closeModal();
      loadAll();
      return;
    }

    if (formType === "set" && state.activeLogId) {
      const payload = {
        exercise_id: fd.get("exercise_id"),
        set_number: Number(fd.get("set_number")),
        reps: Number(fd.get("reps")),
        load_kg: fd.get("load_kg") ? String(fd.get("load_kg")) : null,
        notes: fd.get("notes") || null,
      };
      const result = await addWorkoutSetLog(state.activeLogId, payload);
      if (!result.ok) {
        if (errEl) {
          errEl.textContent = result.error || "Erro ao registrar série";
          errEl.hidden = false;
        }
        return;
      }
      closeModal();
      loadAll();
      return;
    }

    if (formType === "plan-exercise" && state.selectedPlanId) {
      const payload = {
        exercise_id: fd.get("exercise_id"),
        day_label: fd.get("day_label") || null,
        sets: fd.get("sets") ? Number(fd.get("sets")) : null,
        reps: fd.get("reps") || null,
        target_load_kg: fd.get("target_load_kg") ? String(fd.get("target_load_kg")) : null,
        rest_seconds: fd.get("rest_seconds") ? Number(fd.get("rest_seconds")) : null,
        order_index: Number(fd.get("order_index") || 0),
      };
      const result = await addWorkoutPlanExercise(state.selectedPlanId, payload);
      if (!result.ok) {
        if (errEl) {
          errEl.textContent = result.error || "Erro ao adicionar exercício";
          errEl.hidden = false;
        }
        return;
      }
      closeModal();
      const detail = await getWorkoutPlan(state.selectedPlanId);
      state.selectedPlanDetail = detail.ok ? detail.data : null;
      renderPlanDetail();
    }
  });

  loadAll();
}
