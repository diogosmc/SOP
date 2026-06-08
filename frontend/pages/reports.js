import {
  getReportDaily,
  getReportInsights,
  getReportWeekly,
  rebuildReportDaily,
} from "../services/api.js";
import { escapeHtml, formatDateBR, formatScore } from "../modules/reports.js";
import { formatBRL } from "../modules/finance.js";
import { renderLoading } from "../components/loading.js";

/** @returns {HTMLElement} */
export function renderReportsPage() {
  const page = document.createElement("section");
  page.className = "page page--reports";
  page.innerHTML = `
    <div class="page__intro page__intro--row">
      <div>
        <h2 class="page__heading">Relatórios</h2>
        <p class="page__description">Resumo diário, revisão semanal e insights automáticos.</p>
      </div>
      <div class="reports-actions">
        <button type="button" class="btn btn--secondary" data-action="rebuild-daily">Reconstruir diário</button>
        <button type="button" class="btn btn--ghost" data-action="refresh">Atualizar</button>
      </div>
    </div>
    <div class="reports-error" data-role="error" hidden></div>
    <div class="reports-daily card-grid" data-role="daily-cards"></div>
    <section class="reports-panel">
      <h3 class="reports-panel__title">Resumo do dia</h3>
      <pre class="reports-summary-text" data-role="daily-summary"></pre>
    </section>
    <div class="reports-columns">
      <section class="reports-panel">
        <h3 class="reports-panel__title">Semana</h3>
        <div data-role="weekly"></div>
      </section>
      <section class="reports-panel">
        <div class="reports-panel__head">
          <h3 class="reports-panel__title">Insights</h3>
          <button type="button" class="btn btn--ghost btn--sm" data-action="ai-insights">Com IA</button>
        </div>
        <ul class="reports-insights" data-role="insights"></ul>
      </section>
    </div>
  `;
  initReportsPage(page);
  return page;
}

/** @param {HTMLElement} page */
function initReportsPage(page) {
  const state = { loading: true, error: null, useAi: false };

  const errorEl = page.querySelector('[data-role="error"]');
  const dailyCards = page.querySelector('[data-role="daily-cards"]');
  const dailySummary = page.querySelector('[data-role="daily-summary"]');
  const weeklyEl = page.querySelector('[data-role="weekly"]');
  const insightsEl = page.querySelector('[data-role="insights"]');

  async function load() {
    state.loading = true;
    state.error = null;
    if (errorEl) errorEl.hidden = true;
    if (dailyCards) {
      dailyCards.innerHTML = "";
      dailyCards.appendChild(renderLoading("Carregando relatórios..."));
    }

    const [daily, weekly, insights] = await Promise.all([
      getReportDaily(),
      getReportWeekly(),
      getReportInsights({ use_ai: state.useAi }),
    ]);

    state.loading = false;

    if (!daily.ok && !weekly.ok) {
      state.error = daily.error || weekly.error || "Relatórios indisponíveis";
      renderError();
      return;
    }

    renderDaily(daily.ok ? daily.data : null);
    renderWeekly(weekly.ok ? weekly.data : null);
    renderInsights(insights.ok ? insights.data : null, insights.error);
  }

  function renderError() {
    if (dailyCards) {
      dailyCards.innerHTML = `<div class="empty-state empty-state--error empty-state--compact"><p>${escapeHtml(state.error || "Erro")}</p><button type="button" class="btn btn--secondary btn--sm" data-action="retry">Tentar novamente</button></div>`;
      dailyCards.querySelector('[data-action="retry"]')?.addEventListener("click", load);
    }
    if (errorEl) {
      errorEl.hidden = false;
      errorEl.className = "alert alert--warning";
      errorEl.textContent = state.error || "Backend indisponível";
    }
  }

  /** @param {object|null} data */
  function renderDaily(data) {
    if (!dailyCards) return;
    if (!data) {
      dailyCards.innerHTML = `<div class="empty-state empty-state--compact"><p>Sem dados diários.</p></div>`;
      return;
    }
    const cards = [
      { t: "Tarefas concluídas", v: String(data.tasks_completed), i: "✓" },
      { t: "Tarefas pendentes", v: String(data.tasks_pending), i: "☑" },
      { t: "Estudo (min)", v: String(data.study_minutes), i: "📚" },
      { t: "Treino", v: data.workout_completed ? "Sim" : "Não", i: "🏋" },
      { t: "Saldo do dia", v: formatBRL(data.balance), i: "💰" },
      { t: "Produtividade", v: formatScore(data.productivity_score), i: "⚡" },
    ];
    dailyCards.innerHTML = "";
    cards.forEach((c) => {
      const el = document.createElement("article");
      el.className = "card reports-card";
      el.innerHTML = `<div class="card__head"><span class="card__icon">${c.i}</span><h4 class="card__title">${escapeHtml(c.t)}</h4></div><p class="card__value">${escapeHtml(c.v)}</p>`;
      dailyCards.appendChild(el);
    });
    if (dailySummary) {
      dailySummary.textContent = data.summary || "Nenhum resumo registrado para hoje.";
    }
  }

  /** @param {object|null} data */
  function renderWeekly(data) {
    if (!weeklyEl) return;
    if (!data) {
      weeklyEl.innerHTML = `<div class="empty-state empty-state--compact"><p>Semana indisponível.</p></div>`;
      return;
    }
    weeklyEl.innerHTML = `
      <p class="reports-week-range">${formatDateBR(data.week_start)} — ${formatDateBR(data.week_end)}</p>
      <ul class="reports-stats">
        <li><strong>${data.tasks_completed}</strong> tarefas concluídas</li>
        <li><strong>${data.study_minutes}</strong> min de estudo</li>
        <li><strong>${data.workouts_completed}</strong> treinos</li>
        <li><strong>${formatBRL(data.finance_balance)}</strong> saldo</li>
        <li>${escapeHtml(data.habits_summary)}</li>
      </ul>
      <div class="reports-lists">
        <div><h4>Vitórias</h4><ul>${(data.wins || []).map((w) => `<li>${escapeHtml(w)}</li>`).join("") || "<li>—</li>"}</ul></div>
        <div><h4>Problemas</h4><ul>${(data.problems || []).map((w) => `<li>${escapeHtml(w)}</li>`).join("") || "<li>—</li>"}</ul></div>
        <div><h4>Recomendações</h4><ul>${(data.recommendations || []).map((w) => `<li>${escapeHtml(w)}</li>`).join("") || "<li>—</li>"}</ul></div>
      </div>
    `;
  }

  /** @param {object|null} data @param {string|null} err */
  function renderInsights(data, err) {
    if (!insightsEl) return;
    if (!data) {
      insightsEl.innerHTML = `<li class="reports-insights__empty">${escapeHtml(err || "Insights indisponíveis")}</li>`;
      return;
    }
    insightsEl.innerHTML = (data.insights || [])
      .map((item) => `<li>${escapeHtml(item)}</li>`)
      .join("");
  }

  page.querySelector('[data-action="refresh"]')?.addEventListener("click", () => {
    state.useAi = false;
    load();
  });

  page.querySelector('[data-action="ai-insights"]')?.addEventListener("click", async () => {
    state.useAi = true;
    const insights = await getReportInsights({ use_ai: true });
    renderInsights(insights.ok ? insights.data : null, insights.error);
  });

  page.querySelector('[data-action="rebuild-daily"]')?.addEventListener("click", async () => {
    const btn = page.querySelector('[data-action="rebuild-daily"]');
    if (btn) btn.disabled = true;
    const result = await rebuildReportDaily();
    if (btn) btn.disabled = false;
    if (!result.ok) {
      alert(result.error || "Falha ao reconstruir diário");
      return;
    }
    renderDaily(result.data?.report || null);
    alert("Diário reconstruído com sucesso.");
  });

  load();
}
