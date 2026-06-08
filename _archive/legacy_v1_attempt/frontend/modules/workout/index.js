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

export async function renderWorkoutModule(container) {
  let plans = [];
  try {
    const data = await api('/workout/plans?page_size=50');
    plans = data?.items || data || [];
  } catch {
    plans = [];
  }

  container.innerHTML = `
    <div style="display:flex;justify-content:flex-end;margin-bottom:16px">
      <button class="btn btn-primary" id="add-plan" type="button">+ New Plan</button>
    </div>
    <div class="page-grid cols-2">
      ${plans
        .map(
          (p) => `
        <div class="card">
          <div style="display:flex;justify-content:space-between">
            <div>
              <div style="font-weight:600;font-size:15px">${p.name}</div>
              <div style="color:var(--text-secondary);font-size:13px;margin-top:4px">${p.description || ''}</div>
            </div>
            ${p.is_active ? '<span class="badge badge-active">Active</span>' : ''}
          </div>
          <div style="margin-top:16px;display:flex;gap:8px">
            <button class="btn btn-primary btn-sm log-session" data-id="${p.id}">Log Session</button>
            <button class="btn btn-danger btn-sm delete-plan" data-id="${p.id}">Delete</button>
          </div>
        </div>`
        )
        .join('') || '<div class="card empty-state">No workout plans yet</div>'}
    </div>`;

  document.getElementById('add-plan')?.addEventListener('click', () => {
    showModal(
      'New Workout Plan',
      `<div class="form-group"><label>Name (A/B/C…)</label><input class="form-control" name="name" maxlength="10" required /></div>
       <div class="form-group"><label>Description</label><textarea class="form-control" name="description"></textarea></div>`,
      async (fd) => {
        await api('/workout/plans', {
          method: 'POST',
          body: { name: fd.get('name'), description: fd.get('description') || null },
        });
        showToast('Plan created');
        renderWorkoutModule(container);
      }
    );
  });

  container.querySelectorAll('.delete-plan').forEach((btn) => {
    btn.addEventListener('click', async () => {
      if (!confirm('Delete plan?')) return;
      await api(`/workout/plans/${btn.dataset.id}`, { method: 'DELETE' });
      showToast('Plan deleted');
      renderWorkoutModule(container);
    });
  });

  container.querySelectorAll('.log-session').forEach((btn) => {
    btn.addEventListener('click', () => {
      showModal(
        'Log Session',
        `<div class="form-group"><label>Duration (minutes)</label><input class="form-control" name="duration_minutes" type="number" min="1" required /></div>
         <div class="form-group"><label>Notes</label><textarea class="form-control" name="notes"></textarea></div>`,
        async (fd) => {
          await api('/workout/sessions', {
            method: 'POST',
            body: {
              plan_id: btn.dataset.id,
              session_date: new Date().toISOString().slice(0, 10),
              duration_minutes: parseInt(fd.get('duration_minutes'), 10),
              notes: fd.get('notes') || null,
            },
          });
          showToast('Session logged');
        }
      );
    });
  });
}
