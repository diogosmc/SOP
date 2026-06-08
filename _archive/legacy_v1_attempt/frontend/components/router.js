import { renderSidebar } from './sidebar.js';
import { renderHeader } from './header.js';
import { getMe } from '../services/api.js';

import { renderDashboard } from '../pages/dashboard.js';
import { renderTasksPage } from '../pages/tasks.js';
import { renderHabitsPage } from '../pages/habits.js';
import { renderNotesPage } from '../pages/notes.js';
import { renderFinancePage } from '../pages/finance.js';
import { renderStudyPage } from '../pages/study.js';
import { renderWorkoutPage } from '../pages/workout.js';
import { renderChatPage } from '../pages/chat.js';
import { renderMemoriesPage } from '../pages/memories.js';
import { renderReportsPage } from '../pages/reports.js';
import { renderAnalyticsPage } from '../pages/analytics.js';
import { renderSettingsPage } from '../pages/settings.js';
import { renderLoginPage } from '../pages/login.js';

const routes = {
  dashboard: renderDashboard,
  tasks: renderTasksPage,
  habits: renderHabitsPage,
  notes: renderNotesPage,
  finance: renderFinancePage,
  study: renderStudyPage,
  workout: renderWorkoutPage,
  chat: renderChatPage,
  memories: renderMemoriesPage,
  reports: renderReportsPage,
  analytics: renderAnalyticsPage,
  settings: renderSettingsPage,
  login: renderLoginPage,
};

let currentUser = null;

export function getCurrentUser() {
  return currentUser;
}

export function setCurrentUser(user) {
  currentUser = user;
}

export function navigate(path) {
  window.location.hash = `#/${path}`;
}

function getPath() {
  const hash = window.location.hash.slice(2) || 'dashboard';
  return hash.split('?')[0];
}

async function renderRoute() {
  const path = getPath();
  const content = document.getElementById('content');
  const app = document.getElementById('app');

  if (path === 'login') {
    app.style.display = 'block';
    document.getElementById('sidebar').style.display = 'none';
    document.querySelector('.main-wrapper').style.marginLeft = '0';
    renderHeader('login', null);
    await routes.login(content);
    return;
  }

  document.getElementById('sidebar').style.display = '';
  document.querySelector('.main-wrapper').style.marginLeft = '';

  try {
    if (!currentUser) {
      currentUser = await getMe();
    }
  } catch {
    navigate('login');
    return;
  }

  renderSidebar(path);
  renderHeader(path, currentUser);

  const render = routes[path] || routes.dashboard;
  content.innerHTML = '<div class="empty-state">Loading…</div>';
  try {
    await render(content);
  } catch (err) {
    content.innerHTML = `<div class="empty-state">Error: ${err.message}</div>`;
  }
}

export function initRouter() {
  window.addEventListener('hashchange', renderRoute);
  renderRoute();
}
