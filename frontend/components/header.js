import { setState } from "../state.js";
import { getPageTitle } from "../state.js";
import { logout } from "../services/api.js";
import { navigate } from "../router.js";
import { userLabel } from "../modules/auth.js";

/** @param {{ state: import('../state.js').AppState }} ctx */
export function renderHeader({ state }) {
  const header = document.createElement("div");
  header.className = "header__inner";

  const left = document.createElement("div");
  left.className = "header__left";

  const menuBtn = document.createElement("button");
  menuBtn.type = "button";
  menuBtn.className = "header__menu-btn";
  menuBtn.setAttribute("aria-label", "Abrir menu");
  menuBtn.textContent = "☰";
  menuBtn.addEventListener("click", () => {
    setState({ sidebarOpen: !state.sidebarOpen });
    const sidebar = document.getElementById("sidebar-root");
    const overlay = document.getElementById("sidebar-overlay");
    sidebar?.classList.toggle("sidebar--open", state.sidebarOpen);
    if (overlay) overlay.hidden = !state.sidebarOpen;
  });

  const title = document.createElement("h1");
  title.className = "header__title";
  title.textContent = getPageTitle(state.route);

  left.append(menuBtn, title);

  const right = document.createElement("div");
  right.className = "header__right";

  const userBadge = document.createElement("span");
  userBadge.className = "header__user";
  userBadge.textContent = state.authEnabled ? userLabel(state.user) : "Modo local";

  const clock = document.createElement("time");
  clock.className = "header__clock";
  clock.dateTime = new Date().toISOString();
  clock.textContent = formatDateTime(new Date());

  const statuses = document.createElement("div");
  statuses.className = "header__status-group";
  statuses.innerHTML = `
    ${statusPill("API", state.apiStatus)}
    ${statusPill("Ollama", state.ollamaStatus)}
    ${statusPill("DB", state.databaseStatus)}
    ${statusPill("Redis", state.redisStatus)}
  `;

  if (state.authEnabled && state.user) {
    const logoutBtn = document.createElement("button");
    logoutBtn.type = "button";
    logoutBtn.className = "btn btn--ghost btn--sm header__logout";
    logoutBtn.textContent = "Sair";
    logoutBtn.addEventListener("click", async () => {
      await logout();
      setState({ user: null });
      navigate("/login");
    });
    right.append(userBadge, logoutBtn, clock, statuses);
  } else {
    right.append(userBadge, clock, statuses);
  }

  header.append(left, right);

  return header;
}

/** @param {Date} date */
function formatDateTime(date) {
  return date.toLocaleString("pt-BR", {
    weekday: "short",
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** @param {string} label @param {import('../state.js').ServiceStatus} status */
function statusPill(label, status) {
  const labelText = {
    online: "online",
    offline: "offline",
    loading: "...",
    unknown: "?",
  }[status];
  return `<span class="status-pill status-pill--${status}" title="${label}">${label}: ${labelText}</span>`;
}
