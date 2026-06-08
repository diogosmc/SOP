import { Chart, registerables } from 'chart.js';
import { api } from '../services/api.js';

Chart.register(...registerables);

export async function renderAnalyticsPage(container) {
  container.innerHTML = `
    <div class="page-header">
      <h1>Analytics</h1>
      <p>Cross-module insights and trends</p>
    </div>
    <div class="page-grid cols-2">
      <div class="card">
        <div class="card-title">Task Completion</div>
        <div class="chart-container"><canvas id="analytics-tasks-chart"></canvas></div>
      </div>
      <div class="card">
        <div class="card-title">Habit Consistency</div>
        <div class="chart-container"><canvas id="analytics-habits-chart"></canvas></div>
      </div>
    </div>
  `;

  let taskData = [0, 0, 0];
  let habitData = [0, 0, 0, 0, 0, 0, 0];

  try {
    const analytics = await api('/analytics/overview');
    if (analytics?.tasks) taskData = analytics.tasks;
    if (analytics?.habits) habitData = analytics.habits;
  } catch {
    try {
      const tasks = await api('/tasks?page_size=100');
      const items = tasks?.items || [];
      taskData = [
        items.filter((t) => t.status === 'pending').length,
        items.filter((t) => t.status === 'in_progress').length,
        items.filter((t) => t.status === 'completed').length,
      ];
    } catch {
      /* fallback zeros */
    }
  }

  new Chart(document.getElementById('analytics-tasks-chart'), {
    type: 'doughnut',
    data: {
      labels: ['Pending', 'In Progress', 'Completed'],
      datasets: [
        {
          data: taskData,
          backgroundColor: ['#eab308', '#6366f1', '#22c55e'],
          borderWidth: 0,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { labels: { color: '#a1a1aa' } } },
    },
  });

  new Chart(document.getElementById('analytics-habits-chart'), {
    type: 'bar',
    data: {
      labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
      datasets: [
        {
          label: 'Completed',
          data: habitData,
          backgroundColor: '#6366f1',
          borderRadius: 4,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { labels: { color: '#a1a1aa' } } },
      scales: {
        x: { ticks: { color: '#71717a' }, grid: { color: '#27272a' } },
        y: { ticks: { color: '#71717a' }, grid: { color: '#27272a' } },
      },
    },
  });
}
