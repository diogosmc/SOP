/** @param {{ navigate: (route: string) => void, state: import('./state.js').AppState }} ctx */
export function renderSidebar({ navigate, state }) {
  const nav = document.createElement("nav");
  nav.className = "sidebar__inner";

  nav.innerHTML = `
    <div class="sidebar__brand">
      <div class="sidebar__logo" aria-hidden="true">◆</div>
      <div>
        <p class="sidebar__title">COPILOTO</p>
        <p class="sidebar__subtitle">Seu OS pessoal</p>
      </div>
    </div>
  `;

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
    if (state.route === item.route || (state.route === "/" && item.route === "/dashboard")) {
      btn.classList.add("sidebar__link--active");
    }
    btn.innerHTML = `<span class="sidebar__icon" aria-hidden="true">${item.icon}</span><span>${item.label}</span>`;
    btn.addEventListener("click", () => navigate(item.route));
    li.appendChild(btn);
    list.appendChild(li);
  });

  nav.appendChild(list);

  const footer = document.createElement("div");
  footer.className = "sidebar__footer";
  footer.innerHTML = `<p class="sidebar__version">V1.0 · COPILOTO</p>`;
  nav.appendChild(footer);

  return nav;
}
