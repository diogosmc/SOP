import { getCurrentUser } from '../components/router.js';

export async function renderSettingsPage(container) {
  const user = getCurrentUser();

  container.innerHTML = `
    <div class="page-header">
      <h1>Settings</h1>
      <p>Account and preferences</p>
    </div>
    <div class="card" style="max-width:480px">
      <div class="form-group">
        <label>Email</label>
        <input class="form-control" value="${user?.email || ''}" disabled />
      </div>
      <div class="form-group">
        <label>Full Name</label>
        <input class="form-control" value="${user?.full_name || ''}" disabled />
      </div>
      <div class="form-group">
        <label>Theme</label>
        <input class="form-control" value="Dark (default)" disabled />
      </div>
    </div>
  `;
}
