/**
 * @param {{ title: string, value?: string, subtitle?: string, status?: import('../state.js').ServiceStatus, icon?: string }} props
 */
export function createCard({ title, value, subtitle, status, icon }) {
  const card = document.createElement("article");
  card.className = "card";
  if (status) card.classList.add(`card--${status}`);

  card.innerHTML = `
    <div class="card__head">
      ${icon ? `<span class="card__icon" aria-hidden="true">${icon}</span>` : ""}
      <h3 class="card__title">${title}</h3>
      ${status ? `<span class="card__badge card__badge--${status}">${statusLabel(status)}</span>` : ""}
    </div>
    ${value !== undefined ? `<p class="card__value">${value}</p>` : ""}
    ${subtitle ? `<p class="card__subtitle">${subtitle}</p>` : ""}
  `;

  return card;
}

/** @param {import('../state.js').ServiceStatus} status */
function statusLabel(status) {
  return { online: "Online", offline: "Offline", loading: "...", unknown: "—" }[status];
}

/** @param {string} label @param {string} route @param {string} icon */
export function createShortcutCard(label, route, icon) {
  const card = document.createElement("button");
  card.type = "button";
  card.className = "card card--shortcut";
  card.innerHTML = `
    <span class="card__icon" aria-hidden="true">${icon}</span>
    <span class="card__title">${label}</span>
    <span class="card__subtitle">Abrir módulo</span>
  `;
  card.addEventListener("click", () => {
    window.location.hash = route;
  });
  return card;
}
