import { api } from '../services/api.js';

export async function renderDashboard(container) {
  let health = {};
  try {
    health = (await fetch('/api/v1/health').then((r) => r.json())).data || {};
  } catch {
    health = {};
  }

  let taskCount = 0;
  let habitCount = 0;
  try {
    const tasks = await api('/tasks?page_size=1');
    taskCount = tasks?.total ?? tasks?.items?.length ?? 0;
    const habits = await api('/habits?page_size=1');
    habitCount = habits?.total ?? habits?.items?.length ?? 0;
  } catch {
    /* modules may not be available yet */
  }

  container.innerHTML = `
    <div class="page-header">
      <h1>Dashboard</h1>
      <p>Your personal command center</p>
    </div>
    <div class="page-grid cols-3">
      <div class="card">
        <div class="card-title">Tasks</div>
        <div class="stat-value">${taskCount}</div>
      </div>
      <div class="card">
        <div class="card-title">Active Habits</div>
        <div class="stat-value">${habitCount}</div>
      </div>
      <div class="card">
        <div class="card-title">System</div>
        <div style="margin-top:8px;font-size:13px;color:var(--text-secondary)">
          <div>API: ${health.api ? '✓' : '—'}</div>
          <div>Database: ${health.database ? '✓' : '—'}</div>
          <div>Redis: ${health.redis ? '✓' : '—'}</div>
          <div>Ollama: ${health.ollama ? '✓' : '—'}</div>
        </div>
      </div>
    </div>
  `;
}
