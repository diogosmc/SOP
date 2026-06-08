const NAV_ITEMS = [
  { path: 'dashboard', label: 'Dashboard', icon: '◫' },
  { path: 'tasks', label: 'Tasks', icon: '☑' },
  { path: 'habits', label: 'Habits', icon: '↻' },
  { path: 'notes', label: 'Notes', icon: '✎' },
  { path: 'finance', label: 'Finance', icon: '$' },
  { path: 'study', label: 'Study', icon: '📖' },
  { path: 'workout', label: 'Workout', icon: '⚡' },
  { path: 'chat', label: 'Chat', icon: '💬' },
  { path: 'memories', label: 'Memories', icon: '🧠' },
  { path: 'reports', label: 'Reports', icon: '📊' },
  { path: 'analytics', label: 'Analytics', icon: '📈' },
  { path: 'settings', label: 'Settings', icon: '⚙' },
];

export function renderSidebar(currentPath) {
  const sidebar = document.getElementById('sidebar');
  sidebar.innerHTML = `
    <div class="sidebar-brand">
      <div class="logo">C</div>
      <span>COPILOTO</span>
    </div>
    <nav class="sidebar-nav">
      ${NAV_ITEMS.map(
        (item) => `
        <a href="#/${item.path}" class="nav-item${currentPath === item.path ? ' active' : ''}" data-path="${item.path}">
          <span class="icon">${item.icon}</span>
          <span class="nav-label">${item.label}</span>
        </a>`
      ).join('')}
    </nav>
    <div class="sidebar-footer">
      <button class="nav-item" id="sidebar-toggle" type="button">
        <span class="icon">☰</span>
        <span class="nav-label">Collapse</span>
      </button>
    </div>
  `;

  document.getElementById('sidebar-toggle')?.addEventListener('click', () => {
    sidebar.classList.toggle('collapsed');
  });
}

export { NAV_ITEMS };
