import { logout } from '../services/api.js';
import { setCurrentUser, navigate } from './router.js';

const PAGE_TITLES = {
  dashboard: 'Dashboard',
  tasks: 'Tasks',
  habits: 'Habits',
  notes: 'Notes',
  finance: 'Finance',
  study: 'Study',
  workout: 'Workout',
  chat: 'Chat',
  memories: 'Memories',
  reports: 'Reports',
  analytics: 'Analytics',
  settings: 'Settings',
  login: 'Login',
};

export function renderHeader(path, user) {
  const header = document.getElementById('header');
  const title = PAGE_TITLES[path] || 'COPILOTO';

  header.innerHTML = `
    <div class="header-left">
      <button class="btn btn-ghost btn-icon" id="mobile-menu" type="button">☰</button>
      <span class="header-title">${title}</span>
    </div>
    <div class="header-actions">
      ${user ? `<span style="color:var(--text-secondary);font-size:13px">${user.full_name || user.email}</span>` : ''}
      ${
        user
          ? '<button class="btn btn-ghost btn-sm" id="logout-btn" type="button">Logout</button>'
          : ''
      }
    </div>
  `;

  document.getElementById('mobile-menu')?.addEventListener('click', () => {
    document.getElementById('sidebar')?.classList.toggle('open');
  });

  document.getElementById('logout-btn')?.addEventListener('click', async () => {
    await logout();
    setCurrentUser(null);
    navigate('login');
  });
}
