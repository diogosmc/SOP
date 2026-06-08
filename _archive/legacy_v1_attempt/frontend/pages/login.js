import { login, showToast } from '../services/api.js';
import { setCurrentUser } from '../components/router.js';

export async function renderLoginPage(container) {
  document.getElementById('app').innerHTML = `
    <div class="login-page">
      <div class="card login-card">
        <h1>COPILOTO</h1>
        <p>Sign in to your personal assistant</p>
        <form id="login-form">
          <div class="form-group">
            <label for="email">Email</label>
            <input class="form-control" id="email" type="email" required autocomplete="email" />
          </div>
          <div class="form-group">
            <label for="password">Password</label>
            <input class="form-control" id="password" type="password" required autocomplete="current-password" />
          </div>
          <button class="btn btn-primary" type="submit" style="width:100%;margin-top:8px">Sign in</button>
        </form>
      </div>
    </div>
  `;

  document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    try {
      const user = await login(email, password);
      setCurrentUser(user);
      location.reload();
    } catch (err) {
      showToast(err.message, 'error');
    }
  });
}
