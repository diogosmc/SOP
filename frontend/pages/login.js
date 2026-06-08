import { bootstrapAdmin, getAuthBootstrapAvailable, login } from "../services/api.js";
import { navigate } from "../router.js";
import { setState } from "../state.js";

/** @returns {HTMLElement} */
export function renderLoginPage() {
  const page = document.createElement("section");
  page.className = "page page--login";
  page.innerHTML = `
    <div class="login-card">
      <h2 class="login-card__title">Entrar no COPILOTO</h2>
      <p class="login-card__subtitle">Autenticação local com cookies seguros.</p>
      <form class="login-form" data-role="login-form">
        <label class="field">
          <span class="field__label">E-mail</span>
          <input type="email" name="email" class="field__input" required autocomplete="username" />
        </label>
        <label class="field">
          <span class="field__label">Senha</span>
          <input type="password" name="password" class="field__input" required autocomplete="current-password" />
        </label>
        <p class="form-error" data-role="login-error" hidden></p>
        <button type="submit" class="btn btn--primary btn--block">Entrar</button>
      </form>
      <div class="login-bootstrap" data-role="bootstrap" hidden>
        <hr class="login-divider" />
        <h3>Primeiro acesso</h3>
        <p class="login-card__hint">Nenhum administrador configurado. Crie a conta inicial.</p>
        <form class="login-form" data-role="bootstrap-form">
          <label class="field"><span class="field__label">Nome</span><input name="name" class="field__input" required /></label>
          <label class="field"><span class="field__label">E-mail</span><input type="email" name="email" class="field__input" required /></label>
          <label class="field"><span class="field__label">Senha (mín. 8)</span><input type="password" name="password" class="field__input" required minlength="8" /></label>
          <p class="form-error" data-role="bootstrap-error" hidden></p>
          <button type="submit" class="btn btn--secondary btn--block">Criar admin</button>
        </form>
      </div>
    </div>
  `;
  initLoginPage(page);
  return page;
}

/** @param {HTMLElement} page */
function initLoginPage(page) {
  const loginForm = page.querySelector('[data-role="login-form"]');
  const bootstrapWrap = page.querySelector('[data-role="bootstrap"]');
  const bootstrapForm = page.querySelector('[data-role="bootstrap-form"]');
  const loginError = page.querySelector('[data-role="login-error"]');
  const bootstrapError = page.querySelector('[data-role="bootstrap-error"]');

  getAuthBootstrapAvailable().then((result) => {
    if (result.ok && result.data?.available && bootstrapWrap) {
      bootstrapWrap.hidden = false;
    }
    if (result.ok && result.data) {
      setState({ authEnabled: result.data.auth_enabled });
    }
  });

  loginForm?.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    if (loginError) loginError.hidden = true;
    const fd = new FormData(loginForm);
    const result = await login({
      email: String(fd.get("email")),
      password: String(fd.get("password")),
    });
    if (!result.ok) {
      if (loginError) {
        loginError.textContent = result.error || "Falha no login";
        loginError.hidden = false;
      }
      return;
    }
    setState({ user: result.data?.user || null, authChecked: true });
    navigate("/dashboard");
  });

  bootstrapForm?.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    if (bootstrapError) bootstrapError.hidden = true;
    const fd = new FormData(bootstrapForm);
    const result = await bootstrapAdmin({
      name: String(fd.get("name")),
      email: String(fd.get("email")),
      password: String(fd.get("password")),
    });
    if (!result.ok) {
      if (bootstrapError) {
        bootstrapError.textContent = result.error || "Falha ao criar admin";
        bootstrapError.hidden = false;
      }
      return;
    }
    setState({ user: result.data?.user || null, authChecked: true });
    navigate("/dashboard");
  });
}
