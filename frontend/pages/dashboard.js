import { createCard, createShortcutCard } from "../components/card.js";
import {
  getAiHealth,
  getDetailedHealth,
  getMemoryCount,
  getPendingReminders,
  listTasks,
  listHabits,
  listNotes,
} from "../services/api.js";
import { loadDashboardSummaries, renderDashboardSkeleton } from "../modules/dashboard.js";
import { currentMonthRange, formatBRL } from "../modules/finance.js";
import { formatMinutes } from "../modules/study.js";
import { formatDateBR, formatVolume } from "../modules/workout.js";
import { setState } from "../state.js";
import { updateChrome } from "../router.js";

/** @returns {HTMLElement} */
export function renderDashboard() {
  const page = document.createElement("section");
  page.className = "page page--dashboard";

  const intro = document.createElement("div");
  intro.className = "page__intro";
  intro.innerHTML = `
    <h2 class="page__heading">Visão geral</h2>
    <p class="page__description">Status do sistema e atalhos para os módulos do COPILOTO.</p>
  `;
  page.appendChild(intro);

  const grid = document.createElement("div");
  grid.className = "card-grid";
  renderDashboardSkeleton(grid);
  page.appendChild(grid);

  loadDashboardData(grid);

  return page;
}

/** @param {HTMLElement} grid */
async function loadDashboardData(grid) {
  setState({ loadingHealth: true, lastError: null });
  updateChrome();

  const month = currentMonthRange();
  const [
    detailedHealth,
    aiHealth,
    memories,
    reminders,
    pendingTasks,
    completedTasks,
    activeHabits,
    positiveHabits,
    negativeHabits,
    allNotes,
    favoriteNotes,
    archivedNotes,
    summaries,
  ] = await Promise.all([
    getDetailedHealth(),
    getAiHealth(),
    getMemoryCount(),
    getPendingReminders(),
    listTasks({ page: 1, page_size: 1, status: "pending" }),
    listTasks({ page: 1, page_size: 1, status: "completed" }),
    listHabits({ page: 1, page_size: 1, active: true }),
    listHabits({ page: 1, page_size: 1, type: "positive" }),
    listHabits({ page: 1, page_size: 1, type: "negative" }),
    listNotes({ page: 1, page_size: 1 }),
    listNotes({ page: 1, page_size: 1, favorite: true }),
    listNotes({ page: 1, page_size: 1, archived: true }),
    loadDashboardSummaries(month),
  ]);

  const { financeSummary, studySummary, workoutSummary, reportInsights } = summaries;

  const apiStatus = detailedHealth.ok ? "online" : "offline";
  const databaseStatus =
    detailedHealth.ok && detailedHealth.data?.database ? "online" : "offline";
  const redisStatus =
    detailedHealth.ok && detailedHealth.data?.redis ? "online" : "offline";
  const ollamaStatus = aiHealth.ok && aiHealth.data?.ollama ? "online" : "offline";
  const ollamaSubtitle = (() => {
    if (ollamaStatus === "online") {
      const names = aiHealth.data?.models || [];
      const missing = aiHealth.data?.missing_models || [];
      const base = `${names.length} modelos`;
      return missing.length ? `${base} · faltando: ${missing.join(", ")}` : base;
    }
    if (aiHealth.status === 404) {
      return aiHealth.error || "Rota AI Health não encontrada no backend.";
    }
    if (aiHealth.ok && aiHealth.data?.ollama === false) {
      return aiHealth.data?.error || "Ollama inacessível em " + (aiHealth.data?.base_url || "localhost:11434");
    }
    return aiHealth.error || "IA local indisponível";
  })();

  const memoryCount = memories.ok && memories.data ? memories.data.total : null;
  const pendingReminders = reminders.ok && reminders.data ? reminders.data.total : null;
  const tasksPending =
    pendingTasks.ok && pendingTasks.data ? pendingTasks.data.total : null;
  const tasksCompleted =
    completedTasks.ok && completedTasks.data ? completedTasks.data.total : null;
  const habitsActive =
    activeHabits.ok && activeHabits.data ? activeHabits.data.total : null;
  const habitsPositive =
    positiveHabits.ok && positiveHabits.data ? positiveHabits.data.total : null;
  const habitsNegative =
    negativeHabits.ok && negativeHabits.data ? negativeHabits.data.total : null;
  const notesTotal = allNotes.ok && allNotes.data ? allNotes.data.total : null;
  const notesFavorites =
    favoriteNotes.ok && favoriteNotes.data ? favoriteNotes.data.total : null;
  const notesArchived =
    archivedNotes.ok && archivedNotes.data ? archivedNotes.data.total : null;
  const finance = financeSummary.ok ? financeSummary.data : null;
  const study = studySummary.ok ? studySummary.data : null;
  const workout = workoutSummary.ok ? workoutSummary.data : null;

  const errors = [detailedHealth, aiHealth]
    .filter((r) => !r.ok)
    .map((r) => r.error)
    .filter(Boolean);

  setState({
    apiStatus,
    databaseStatus,
    redisStatus,
    ollamaStatus,
    memoryCount,
    pendingReminders,
    tasksPending,
    tasksCompleted,
    habitsActive,
    habitsPositive,
    habitsNegative,
    notesTotal,
    notesFavorites,
    notesArchived,
    financeBalance: finance ? Number(finance.balance) : null,
    loadingHealth: false,
    lastError: errors[0] || null,
  });
  updateChrome();

  grid.className = "card-grid";
  grid.innerHTML = "";

  grid.append(
    createCard({
      title: "API",
      value: apiStatus === "online" ? "Respondendo" : "Indisponível",
      subtitle: detailedHealth.ok ? "Serviço copiloto ativo" : detailedHealth.error || "Sem conexão",
      status: apiStatus,
      icon: "⚡",
    }),
    createCard({
      title: "Database",
      value: databaseStatus === "online" ? "Conectado" : "Offline",
      subtitle: "PostgreSQL + pgvector",
      status: databaseStatus,
      icon: "🗄",
    }),
    createCard({
      title: "Redis",
      value: redisStatus === "online" ? "Conectado" : "Offline",
      subtitle: "Cache e filas",
      status: redisStatus,
      icon: "◉",
    }),
    createCard({
      title: "Ollama",
      value: ollamaStatus === "online" ? "Online" : "Offline",
      subtitle: ollamaSubtitle,
      status: ollamaStatus,
      icon: "🤖",
    }),
    createCard({
      title: "Memórias",
      value: memoryCount !== null ? String(memoryCount) : "—",
      subtitle: memories.ok ? "Total registrado" : memories.error || "Endpoint indisponível",
      icon: "🧠",
    }),
    createCard({
      title: "Lembretes pendentes",
      value: pendingReminders !== null ? String(pendingReminders) : "—",
      subtitle: reminders.ok ? "Aguardando envio" : reminders.error || "Endpoint indisponível",
      icon: "⏰",
    }),
    createCard({
      title: "Tarefas pendentes",
      value: tasksPending !== null ? String(tasksPending) : "—",
      subtitle: pendingTasks.ok ? "Aguardando conclusão" : pendingTasks.error || "Endpoint indisponível",
      icon: "☑",
    }),
    createCard({
      title: "Tarefas concluídas",
      value: tasksCompleted !== null ? String(tasksCompleted) : "—",
      subtitle: completedTasks.ok ? "Finalizadas" : completedTasks.error || "Endpoint indisponível",
      icon: "✓",
    }),
    createCard({
      title: "Hábitos ativos",
      value: habitsActive !== null ? String(habitsActive) : "—",
      subtitle: activeHabits.ok ? "Em acompanhamento" : activeHabits.error || "Endpoint indisponível",
      icon: "↻",
    }),
    createCard({
      title: "Hábitos positivos",
      value: habitsPositive !== null ? String(habitsPositive) : "—",
      subtitle: positiveHabits.ok ? "Construir rotinas" : positiveHabits.error || "Endpoint indisponível",
      icon: "↑",
    }),
    createCard({
      title: "Hábitos negativos",
      value: habitsNegative !== null ? String(habitsNegative) : "—",
      subtitle: negativeHabits.ok ? "Evitar padrões" : negativeHabits.error || "Endpoint indisponível",
      icon: "↓",
    }),
    createCard({
      title: "Notas",
      value: notesTotal !== null ? String(notesTotal) : "—",
      subtitle: allNotes.ok ? "Total registrado" : allNotes.error || "Endpoint indisponível",
      icon: "✎",
    }),
    createCard({
      title: "Notas favoritas",
      value: notesFavorites !== null ? String(notesFavorites) : "—",
      subtitle: favoriteNotes.ok ? "Marcadas com ★" : favoriteNotes.error || "Endpoint indisponível",
      icon: "★",
    }),
    createCard({
      title: "Notas arquivadas",
      value: notesArchived !== null ? String(notesArchived) : "—",
      subtitle: archivedNotes.ok ? "Fora da lista ativa" : archivedNotes.error || "Endpoint indisponível",
      icon: "📁",
    }),
    createCard({
      title: "Receitas (mês)",
      value: finance ? formatBRL(finance.income) : "—",
      subtitle: financeSummary.ok ? "Período atual" : financeSummary.error || "Finanças indisponível",
      icon: "↑",
    }),
    createCard({
      title: "Despesas (mês)",
      value: finance ? formatBRL(finance.expense) : "—",
      subtitle: financeSummary.ok ? "Período atual" : financeSummary.error || "Finanças indisponível",
      icon: "↓",
    }),
    createCard({
      title: "Saldo (mês)",
      value: finance ? formatBRL(finance.balance) : "—",
      subtitle: financeSummary.ok ? `${finance.transactions_count} transações` : financeSummary.error || "Finanças indisponível",
      icon: "💰",
    }),
    createCard({
      title: "Tópicos em progresso",
      value: study ? String(study.topics_in_progress) : "—",
      subtitle: studySummary.ok ? `${study.total_subjects} matérias` : studySummary.error || "Estudos indisponível",
      icon: "📚",
    }),
    createCard({
      title: "Flashcards p/ revisar",
      value: study ? String(study.flashcards_due) : "—",
      subtitle: studySummary.ok ? "Revisão espaçada" : studySummary.error || "Estudos indisponível",
      icon: "🃏",
    }),
    createCard({
      title: "Estudo hoje",
      value: study ? formatMinutes(study.minutes_studied_today) : "—",
      subtitle: studySummary.ok ? `${formatMinutes(study.minutes_studied_week)} na semana` : studySummary.error || "Estudos indisponível",
      icon: "⏱",
    }),
    createCard({
      title: "Treinos na semana",
      value: workout ? String(workout.workouts_this_week) : "—",
      subtitle: workoutSummary.ok ? formatVolume(workout.total_volume_week) : workoutSummary.error || "Treino indisponível",
      icon: "🏋",
    }),
    createCard({
      title: "Último treino",
      value: workout ? formatDateBR(workout.last_workout_date) : "—",
      subtitle: workoutSummary.ok ? (workout.active_plan || "Sem plano ativo") : workoutSummary.error || "Treino indisponível",
      icon: "📅",
    })
  );

  if (errors.length) {
    const alert = document.createElement("div");
    alert.className = "alert alert--warning";
    alert.innerHTML = `<strong>Backend parcialmente indisponível.</strong> A interface continua funcional. ${errors[0]}`;
    grid.parentElement?.insertBefore(alert, grid);
  }

  const insightsTitle = document.createElement("h3");
  insightsTitle.className = "section-title";
  insightsTitle.textContent = "Insights";
  grid.parentElement?.appendChild(insightsTitle);

  const insightsBox = document.createElement("section");
  insightsBox.className = "dashboard-insights reports-panel";
  if (reportInsights.ok && reportInsights.data?.insights?.length) {
    insightsBox.innerHTML = `<ul class="reports-insights">${reportInsights.data.insights
      .slice(0, 4)
      .map((item) => `<li>${item.replace(/</g, "&lt;")}</li>`)
      .join("")}</ul>`;
  } else {
    insightsBox.innerHTML = `<p class="dashboard-insights__empty">${reportInsights.error || "Insights indisponíveis no momento."}</p>`;
  }
  grid.parentElement?.appendChild(insightsBox);

  const shortcutsTitle = document.createElement("h3");
  shortcutsTitle.className = "section-title";
  shortcutsTitle.textContent = "Atalhos";
  grid.parentElement?.appendChild(shortcutsTitle);

  const shortcuts = document.createElement("div");
  shortcuts.className = "card-grid card-grid--shortcuts";
  shortcuts.append(
    createShortcutCard("Chat", "/chat", "💬"),
    createShortcutCard("Notas", "/notes", "✎"),
    createShortcutCard("Tarefas", "/tasks", "☑"),
    createShortcutCard("Finanças", "/finance", "💰"),
    createShortcutCard("Estudos", "/study", "📚"),
    createShortcutCard("Treino", "/workout", "🏋"),
    createShortcutCard("Relatórios", "/reports", "📊"),
    createShortcutCard("Analytics", "/analytics", "📈"),
    createShortcutCard("Memórias", "/memories", "🧠")
  );
  grid.parentElement?.appendChild(shortcuts);
}
