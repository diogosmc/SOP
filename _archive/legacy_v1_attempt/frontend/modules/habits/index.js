import { api, showToast } from '../../services/api.js';

function showModal(title, fields, onSubmit) {
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay';
  overlay.innerHTML = `
    <div class="modal">
      <div class="modal-header"><h2>${title}</h2><button class="btn btn-ghost btn-icon" type="button" data-close>✕</button></div>
      <form id="modal-form">${fields}
        <div style="display:flex;gap:8px;margin-top:20px;justify-content:flex-end">
          <button class="btn btn-secondary" type="button" data-close>Cancel</button>
          <button class="btn btn-primary" type="submit">Save</button>
        </div>
      </form>
    </div>`;
  document.body.appendChild(overlay);
  overlay.querySelectorAll('[data-close]').forEach((el) => el.addEventListener('click', () => overlay.remove()));
  overlay.querySelector('#modal-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    await onSubmit(new FormData(e.target));
    overlay.remove();
  });
}

export async function renderHabitsModule(container) {
  async function load() {
    const data = await api('/habits?page_size=50');
    const items = data?.items || [];

    container.innerHTML = `
      <div style="display:flex;justify-content:flex-end;margin-bottom:16px">
        <button class="btn btn-primary" id="add-habit" type="button">+ New Habit</button>
      </div>
      <div class="page-grid cols-2">
        ${items
          .map(
            (h) => `
          <div class="card">
            <div style="display:flex;justify-content:space-between;align-items:start">
              <div>
                <div style="font-weight:600;font-size:15px">${h.name}</div>
                <div style="color:var(--text-secondary);font-size:13px;margin-top:4px">${h.description || ''}</div>
              </div>
              <span class="badge badge-active">${h.current_streak}🔥</span>
            </div>
            <div style="margin-top:16px;display:flex;gap:8px">
              <button class="btn btn-primary btn-sm log-habit" data-id="${h.id}">Log Today</button>
              <button class="btn btn-ghost btn-sm delete-habit" data-id="${h.id}">Delete</button>
            </div>
          </div>`
          )
          .join('') || '<div class="card empty-state">No habits yet</div>'}
      </div>`;

    document.getElementById('add-habit')?.addEventListener('click', () => {
      showModal(
        'New Habit',
        `<div class="form-group"><label>Name</label><input class="form-control" name="name" required /></div>
         <div class="form-group"><label>Description</label><textarea class="form-control" name="description"></textarea></div>`,
        async (fd) => {
          await api('/habits', { method: 'POST', body: { name: fd.get('name'), description: fd.get('description') || null } });
          showToast('Habit created');
          load();
        }
      );
    });

    container.querySelectorAll('.log-habit').forEach((btn) => {
      btn.addEventListener('click', async () => {
        await api(`/habits/${btn.dataset.id}/log`, { method: 'POST', body: { completed: true } });
        showToast('Habit logged!');
        load();
      });
    });

    container.querySelectorAll('.delete-habit').forEach((btn) => {
      btn.addEventListener('click', async () => {
        if (!confirm('Delete this habit?')) return;
        await api(`/habits/${btn.dataset.id}`, { method: 'DELETE' });
        showToast('Habit deleted');
        load();
      });
    });
  }

  try {
    await load();
  } catch (err) {
    container.innerHTML = `<div class="empty-state">${err.message}</div>`;
  }
}
