import { state, setState, getPageTitle } from "./state.js";
import { renderSidebar } from "./components/sidebar.js";
import { renderHeader } from "./components/header.js";
import { renderDashboard } from "./pages/dashboard.js";
import { renderChatPage } from "./pages/chat.js";
import { renderSettingsPage } from "./pages/settings.js";
import { renderTasksPage } from "./pages/tasks.js";
import { renderHabitsPage } from "./pages/habits.js";
import { renderLoginPage } from "./pages/login.js";
import { renderPlaceholderPage } from "./pages/placeholder.js";
import { renderLoading } from "./components/loading.js";
import { getAuthBootstrapAvailable, getAuthMe } from "./services/api.js";

const STATIC_ROUTES = {
  "/": renderDashboard,
  "/dashboard": renderDashboard,
  "/tasks": renderTasksPage,
  "/habits": renderHabitsPage,
  "/chat": renderChatPage,
  "/memories": () => renderPlaceholderPage("Memórias"),
  "/reminders": () => renderPlaceholderPage("Lembretes"),
  "/login": renderLoginPage,
  "/settings": renderSettingsPage,
};

const LAZY_ROUTES = {
  "/notes": () => import("./pages/notes.js").then((m) => m.renderNotesPage),
  "/finance": () => import("./pages/finance.js").then((m) => m.renderFinancePage),
  "/study": () => import("./pages/study.js").then((m) => m.renderStudyPage),
  "/workout": () => import("./pages/workout.js").then((m) => m.renderWorkoutPage),
  "/reports": () => import("./pages/reports.js").then((m) => m.renderReportsPage),
  "/analytics": () => import("./pages/analytics.js").then((m) => m.renderAnalyticsPage),
};

function normalizeHash() {
  const hash = window.location.hash.replace(/^#/, "") || "/dashboard";
  return hash.startsWith("/") ? hash : `/${hash}`;
}

function navigate(route) {
  const normalized = route.startsWith("/") ? route : `/${route}`;
  if (window.location.hash !== `#${normalized}`) {
    window.location.hash = normalized;
    return;
  }
  setState({ route: normalized });
  renderCurrentPage();
  updateChrome();
}

async function renderCurrentPage() {
  const content = document.getElementById("content-root");
  if (!content) return;

  const route = state.route;
  const lazyLoader = LAZY_ROUTES[route];

  if (lazyLoader) {
    content.innerHTML = "";
    content.appendChild(renderLoading("Carregando página..."));
    try {
      const renderer = await lazyLoader();
      content.innerHTML = "";
      content.appendChild(renderer());
    } catch {
      content.innerHTML = "";
      content.appendChild(renderPlaceholderPage("Erro ao carregar página"));
    }
    return;
  }

  const renderer = STATIC_ROUTES[route] || STATIC_ROUTES["/dashboard"];
  content.innerHTML = "";
  content.appendChild(renderer());
}

function updateChrome() {
  const sidebarRoot = document.getElementById("sidebar-root");
  const headerRoot = document.getElementById("header-root");
  if (sidebarRoot) {
    sidebarRoot.innerHTML = "";
    sidebarRoot.appendChild(renderSidebar({ navigate, state }));
  }
  if (headerRoot) {
    headerRoot.innerHTML = "";
    headerRoot.appendChild(renderHeader({ state }));
  }
  document.title = `${getPageTitle(state.route)} · COPILOTO`;
}

function closeSidebarOnMobile() {
  if (window.innerWidth <= 768) {
    setState({ sidebarOpen: false });
    updateSidebarVisibility();
  }
}

export function initRouter() {
  window.addEventListener("hashchange", () => {
    setState({ route: normalizeHash() });
    renderCurrentPage();
    updateChrome();
    closeSidebarOnMobile();
  });

  bootstrapAuth().then(() => {
    const route = normalizeHash();
    if (state.authEnabled && !state.user && route !== "/login") {
      window.location.hash = "#/login";
      return;
    }
    setState({ route: normalizeHash() });
    renderCurrentPage();
    updateChrome();
  });
}

async function bootstrapAuth() {
  const setup = await getAuthBootstrapAvailable();
  const authEnabled = setup.ok ? Boolean(setup.data?.auth_enabled) : false;
  setState({ authEnabled, authChecked: true });

  if (!authEnabled) {
    setState({ user: null });
    return;
  }

  const me = await getAuthMe();
  if (me.ok) {
    setState({ user: me.data });
  } else {
    setState({ user: null });
  }
}

export function updateSidebarVisibility() {
  const sidebar = document.getElementById("sidebar-root");
  const overlay = document.getElementById("sidebar-overlay");
  if (!sidebar || !overlay) return;

  sidebar.classList.toggle("sidebar--open", state.sidebarOpen);
  overlay.hidden = !state.sidebarOpen;
}

export { navigate, updateChrome };
