const API_BASE = '/api/v1';

let refreshPromise = null;

async function tryRefresh() {
  if (!refreshPromise) {
    refreshPromise = fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      credentials: 'include',
    }).finally(() => {
      refreshPromise = null;
    });
  }
  const res = await refreshPromise;
  return res.ok;
}

export async function api(path, options = {}) {
  const { method = 'GET', body, headers = {}, raw = false } = options;

  const config = {
    method,
    credentials: 'include',
    headers: {
      ...headers,
    },
  };

  if (body !== undefined) {
    config.headers['Content-Type'] = 'application/json';
    config.body = JSON.stringify(body);
  }

  let response = await fetch(`${API_BASE}${path}`, config);

  if (response.status === 401 && !path.startsWith('/auth/')) {
    const refreshed = await tryRefresh();
    if (refreshed) {
      response = await fetch(`${API_BASE}${path}`, config);
    }
  }

  if (raw) return response;

  const data = await response.json().catch(() => ({}));

  if (!response.ok || data.success === false) {
    const message = data.error?.message || data.detail || `Request failed (${response.status})`;
    throw new Error(message);
  }

  return data.data;
}

export async function login(email, password) {
  return api('/auth/login', { method: 'POST', body: { email, password } });
}

export async function logout() {
  return api('/auth/logout', { method: 'POST' });
}

export async function getMe() {
  return api('/auth/me');
}

export function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast${type === 'error' ? ' error' : ''}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}
