/** @param {{ navigate: (route: string) => void, state: import('./state.js').AppState, onToggleCollapse?: () => void }} ctx */
export function renderSidebar({ navigate, state, onToggleCollapse }) {
  const nav = document.createElement("nav");
  nav.className = "sidebar__inner";

  const brand = document.createElement("div");
  brand.className = "sidebar__brand";
  brand.innerHTML = `
    <div class="sidebar__logo" aria-hidden="true">◆</div>
    <div class="sidebar__brand-text">
      <p class="sidebar__title">COPILOTO</p>
      <p class="sidebar__subtitle">Seu OS pessoal</p>
    </div>
    <button type="button" class="sidebar__collapse-btn" aria-label="${state.sidebarCollapsed ? "Expandir menu" : "Recolher menu"}" title="${state.sidebarCollapsed ? "Expandir" : "Recolher"}">${state.sidebarCollapsed ? "»" : "«"}</button>
  `;
  brand.querySelector(".sidebar__collapse-btn")?.addEventListener("click", () => {
    onToggleCollapse?.();
  });
  nav.appendChild(brand);

  const items = [
    { route: "/dashboard", label: "Dashboard", icon: "▣" },
    { route: "/tasks", label: "Tarefas", icon: "☑" },
    { route: "/habits", label: "Hábitos", icon: "↻" },
    { route: "/notes", label: "Notas", icon: "✎" },
    { route: "/finance", label: "Finanças", icon: "💰" },
    { route: "/study", label: "Estudos", icon: "📚" },
    { route: "/workout", label: "Treino", icon: "🏋" },
    { route: "/chat", label: "Chat", icon: "💬" },
    { route: "/memories", label: "Memórias", icon: "🧠" },
    { route: "/reminders", label: "Lembretes", icon: "⏰" },
    { route: "/reports", label: "Relatórios", icon: "📊" },
    { route: "/analytics", label: "Analytics", icon: "📈" },
    { route: "/settings", label: "Configurações", icon: "⚙" },
  ];

  const list = document.createElement("ul");
  list.className = "sidebar__nav";

  items.forEach((item) => {
    const li = document.createElement("li");
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "sidebar__link";
    btn.title = item.label;
    if (state.route === item.route || (state.route === "/" && item.route === "/dashboard")) {
      btn.classList.add("sidebar__link--active");
    }
    btn.innerHTML = `<span class="sidebar__icon" aria-hidden="true">${item.icon}</span><span class="sidebar__label">${item.label}</span>`;
    btn.addEventListener("click", () => navigate(item.route));
    li.appendChild(btn);
    list.appendChild(li);
  });

  nav.appendChild(list);

  const footer = document.createElement("div");
  footer.className = "sidebar__footer";
  footer.innerHTML = `<p class="sidebar__version">V1.0.1</p>`;
  nav.appendChild(footer);

  return nav;
}
