/** @param {string} moduleName @returns {HTMLElement} */
export function renderPlaceholderPage(moduleName) {
  const page = document.createElement("section");
  page.className = "page page--placeholder";
  page.innerHTML = `
    <div class="placeholder">
      <div class="placeholder__icon" aria-hidden="true">◌</div>
      <h2 class="placeholder__title">${moduleName}</h2>
      <p class="placeholder__text">Módulo será implementado na próxima fase.</p>
      <p class="placeholder__hint">O backend já expõe endpoints para este módulo.</p>
    </div>
  `;
  return page;
}
