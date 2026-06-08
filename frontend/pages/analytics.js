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
import { getReportAnalytics } from "../services/api.js";
import {
  chartLabels,
  chartValues,
  escapeHtml,
  formatDateBR,
  TASK_STATUS_LABELS,
} from "../modules/reports.js";
import { formatBRL } from "../modules/finance.js";
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

/** @returns {HTMLElement} */
export function renderAnalyticsPage() {
  const page = document.createElement("section");
  page.className = "page page--analytics";
  page.innerHTML = `
    <div class="page__intro">
      <h2 class="page__heading">Analytics</h2>
      <p class="page__description">Visão agregada de produtividade, estudos, treino, finanças e hábitos.</p>
    </div>
    <div class="analytics-summary card-grid" data-role="summary"></div>
    <div class="analytics-charts">
      <div class="analytics-chart-card">
        <h3>Tarefas por status</h3>
        <canvas data-role="chart-tasks" height="220"></canvas>
      </div>
      <div class="analytics-chart-card">
        <h3>Finanças por categoria</h3>
        <canvas data-role="chart-finance" height="220"></canvas>
      </div>
      <div class="analytics-chart-card">
        <h3>Estudo por dia (min)</h3>
        <canvas data-role="chart-study" height="220"></canvas>
      </div>
      <div class="analytics-chart-card">
        <h3>Treinos por dia</h3>
        <canvas data-role="chart-workout" height="220"></canvas>
      </div>
    </div>
    <section class="reports-panel">
      <h3 class="reports-panel__title">Memórias por tipo</h3>
      <div class="analytics-memories" data-role="memories"></div>
    </section>
  `;
  initAnalyticsPage(page);
  return page;
}

/** @param {HTMLElement} page */
function initAnalyticsPage(page) {
  /** @type {Record<string, Chart|null>} */
  const charts = {};

  const summaryEl = page.querySelector('[data-role="summary"]');
  const memoriesEl = page.querySelector('[data-role="memories"]');

  async function load() {
    if (summaryEl) {
      summaryEl.innerHTML = "";
      summaryEl.appendChild(renderLoading("Carregando analytics..."));
    }

    const result = await getReportAnalytics();
    if (!result.ok) {
      if (summaryEl) {
        summaryEl.innerHTML = `<div class="empty-state empty-state--error empty-state--compact"><p>${escapeHtml(result.error || "Analytics indisponível")}</p><button type="button" class="btn btn--secondary btn--sm" data-action="retry">Tentar novamente</button></div>`;
        summaryEl.querySelector('[data-action="retry"]')?.addEventListener("click", load);
      }
      return;
    }

    const data = result.data;
    renderSummary(data);
    renderCharts(data);
    renderMemories(data.memories_by_type || {});
  }

  /** @param {object} data */
  function renderSummary(data) {
    if (!summaryEl) return;
    const habits = data.habits || {};
    const cards = [
      { t: "Período", v: `${formatDateBR(data.period_start)} — ${formatDateBR(data.period_end)}`, i: "📅" },
      { t: "Hábitos ativos", v: String(habits.active ?? "—"), i: "↻" },
      { t: "Positivos", v: String(habits.positive ?? "—"), i: "↑" },
      { t: "Negativos", v: String(habits.negative ?? "—"), i: "↓" },
    ];
    summaryEl.innerHTML = "";
    cards.forEach((c) => {
      const el = document.createElement("article");
      el.className = "card analytics-card";
      el.innerHTML = `<div class="card__head"><span class="card__icon">${c.i}</span><h4 class="card__title">${escapeHtml(c.t)}</h4></div><p class="card__value">${escapeHtml(c.v)}</p>`;
      summaryEl.appendChild(el);
    });
  }

  /** @param {object} data */
  function renderCharts(data) {
    destroyChart("tasks");
    destroyChart("finance");
    destroyChart("study");
    destroyChart("workout");

    const tasksCanvas = page.querySelector('[data-role="chart-tasks"]');
    const financeCanvas = page.querySelector('[data-role="chart-finance"]');
    const studyCanvas = page.querySelector('[data-role="chart-study"]');
    const workoutCanvas = page.querySelector('[data-role="chart-workout"]');

    const status = data.tasks_by_status || {};
    const statusLabels = Object.keys(status).map((k) => TASK_STATUS_LABELS[k] || k);
    const statusValues = Object.values(status).map((v) => Number(v) || 0);

    if (tasksCanvas && statusLabels.length) {
      charts.tasks = new Chart(tasksCanvas, {
        type: "bar",
        data: {
          labels: statusLabels,
          datasets: [{ label: "Tarefas", data: statusValues, backgroundColor: "#8b5cf6" }],
        },
        options: chartOptions(),
      });
    }

    const finance = data.finance_by_category || [];
    if (financeCanvas && finance.length) {
      charts.finance = new Chart(financeCanvas, {
        type: "bar",
        data: {
          labels: finance.map((f) => f.category),
          datasets: [
            {
              label: "Despesas",
              data: finance.map((f) => Number(f.expense) || 0),
              backgroundColor: "#ef4444",
            },
            {
              label: "Receitas",
              data: finance.map((f) => Number(f.income) || 0),
              backgroundColor: "#22c55e",
            },
          ],
        },
        options: chartOptions(true),
      });
    }

    const study = data.study_minutes_by_day || [];
    if (studyCanvas && study.length) {
      charts.study = new Chart(studyCanvas, {
        type: "line",
        data: {
          labels: chartLabels(study),
          datasets: [
            {
              label: "Minutos",
              data: chartValues(study),
              borderColor: "#60a5fa",
              backgroundColor: "rgba(96, 165, 250, 0.15)",
              fill: true,
              tension: 0.3,
            },
          ],
        },
        options: chartOptions(),
      });
    }

    const workouts = data.workouts_by_day || [];
    if (workoutCanvas && workouts.length) {
      charts.workout = new Chart(workoutCanvas, {
        type: "bar",
        data: {
          labels: chartLabels(workouts),
          datasets: [{ label: "Treinos", data: chartValues(workouts), backgroundColor: "#a78bfa" }],
        },
        options: chartOptions(),
      });
    }
  }

  /** @param {Record<string, number>} memories */
  function renderMemories(memories) {
    if (!memoriesEl) return;
    const entries = Object.entries(memories);
    if (!entries.length) {
      memoriesEl.innerHTML = `<p class="analytics-empty">Nenhuma memória registrada.</p>`;
      return;
    }
    memoriesEl.innerHTML = entries
      .map(([type, count]) => `<span class="analytics-tag">${escapeHtml(type)}: <strong>${count}</strong></span>`)
      .join("");
  }

  function destroyChart(key) {
    if (charts[key]) {
      charts[key].destroy();
      charts[key] = null;
    }
  }

  /** @param {boolean} [legend] */
  function chartOptions(legend = false) {
    return {
      responsive: true,
      plugins: {
        legend: { display: legend, labels: { color: "#a1a1aa" } },
        tooltip: {
          callbacks: {
            label(ctx) {
              if (ctx.dataset.label === "Despesas" || ctx.dataset.label === "Receitas") {
                return `${ctx.dataset.label}: ${formatBRL(ctx.raw)}`;
              }
              return `${ctx.dataset.label}: ${ctx.formattedValue}`;
            },
          },
        },
      },
      scales: {
        x: { ticks: { color: "#71717a" }, grid: { color: "rgba(255,255,255,0.06)" } },
        y: { ticks: { color: "#71717a" }, grid: { color: "rgba(255,255,255,0.06)" } },
      },
    };
  }

  load();
}
