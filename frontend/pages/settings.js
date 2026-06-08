/** @returns {HTMLElement} */
export function renderSettingsPage() {
  const page = document.createElement("section");
  page.className = "page page--settings";
  page.innerHTML = `
    <div class="page__intro">
      <h2 class="page__heading">Configurações</h2>
      <p class="page__description">Preferências do dashboard — autenticação e perfil virão em fase futura.</p>
    </div>
    <div class="settings-grid">
      <article class="card">
        <h3 class="card__title">API Backend</h3>
        <p class="card__subtitle">Proxy Vite → <code>http://localhost:8000</code></p>
        <p class="card__value card__value--sm">Modo single-user (sem auth frontend)</p>
      </article>
      <article class="card">
        <h3 class="card__title">Aparência</h3>
        <p class="card__subtitle">Dark mode ativo por padrão</p>
        <p class="card__value card__value--sm">Tema claro — em breve</p>
      </article>
      <article class="card">
        <h3 class="card__title">Integrações</h3>
        <p class="card__subtitle">Telegram, Ollama, Scheduler</p>
        <p class="card__value card__value--sm">Configuradas via backend <code>.env</code></p>
      </article>
    </div>
  `;
  return page;
}
