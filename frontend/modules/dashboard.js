import { getFinanceSummary, getStudySummary, getWorkoutSummary, getReportInsights } from "../services/api.js";

/**
 * Load dashboard summary endpoints in a single batch.
 * @param {{ start: string, end: string }} month
 */
export async function loadDashboardSummaries(month) {
  const [financeSummary, studySummary, workoutSummary, reportInsights] = await Promise.all([
    getFinanceSummary({ start_date: month.start, end_date: month.end }),
    getStudySummary(),
    getWorkoutSummary(),
    getReportInsights(),
  ]);
  return { financeSummary, studySummary, workoutSummary, reportInsights };
}

/**
 * @param {HTMLElement} grid
 */
export function renderDashboardSkeleton(grid) {
  grid.innerHTML = "";
  grid.className = "card-grid card-grid--skeleton";
  for (let i = 0; i < 8; i += 1) {
    const card = document.createElement("div");
    card.className = "skeleton-card";
    card.innerHTML = `
      <div class="skeleton-card__icon skeleton-pulse"></div>
      <div class="skeleton-card__line skeleton-pulse"></div>
      <div class="skeleton-card__line skeleton-card__line--short skeleton-pulse"></div>
    `;
    grid.appendChild(card);
  }
}
