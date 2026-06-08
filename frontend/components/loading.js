/** @param {string} [message] */
export function renderLoading(message = "Carregando...") {
  const wrap = document.createElement("div");
  wrap.className = "loading";
  wrap.innerHTML = `
    <div class="loading__spinner" aria-hidden="true"></div>
    <p class="loading__text">${message}</p>
  `;
  wrap.setAttribute("role", "status");
  wrap.setAttribute("aria-live", "polite");
  return wrap;
}
