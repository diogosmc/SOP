/** @typedef {'online' | 'offline' | 'loading' | 'unknown'} ServiceStatus */

/**
 * @typedef {Object} AppState
 * @property {boolean} authEnabled
 * @property {boolean} authChecked
 * @property {{ id: string, name: string, email: string, is_admin: boolean }|null} user
 * @property {string} route
 * @property {boolean} sidebarOpen
 * @property {ServiceStatus} apiStatus
 * @property {ServiceStatus} databaseStatus
 * @property {ServiceStatus} redisStatus
 * @property {ServiceStatus} ollamaStatus
 * @property {number|null} memoryCount
 * @property {number|null} pendingReminders
 * @property {boolean} loadingHealth
 * @property {string|null} lastError
 */

/** @type {AppState} */
export const state = {
  route: "/dashboard",
  sidebarOpen: false,
  apiStatus: "unknown",
  databaseStatus: "unknown",
  redisStatus: "unknown",
  ollamaStatus: "unknown",
  memoryCount: null,
  pendingReminders: null,
  loadingHealth: false,
  lastError: null,
  authEnabled: false,
  authChecked: false,
  user: null,
};

const listeners = new Set();

/** @param {Partial<AppState>} patch */
export function setState(patch) {
  Object.assign(state, patch);
  listeners.forEach((listener) => listener(state));
}

/** @param {(state: AppState) => void} listener */
export function subscribe(listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function getPageTitle(route) {
  const titles = {
    "/": "Dashboard",
    "/dashboard": "Dashboard",
    "/tasks": "Tarefas",
    "/habits": "Hábitos",
    "/notes": "Notas",
    "/finance": "Finanças",
    "/study": "Estudos",
    "/workout": "Treino",
    "/reports": "Relatórios",
    "/analytics": "Analytics",
    "/chat": "Chat",
    "/memories": "Memórias",
    "/reminders": "Lembretes",
    "/login": "Login",
    "/settings": "Configurações",
  };
  return titles[route] || "COPILOTO";
}
