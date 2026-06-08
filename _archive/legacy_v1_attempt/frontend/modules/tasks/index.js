import { api, showToast } from '../../services/api.js';

function statusBadge(status) {
  const map = {
    pending: 'badge-pending',
    in_progress: 'badge-active',
    completed: 'badge-done',
  };
  return `<span class="badge ${map[status] || 'badge-pending'}">${status}</span>`;
}

function showModal(title, fields, onSubmit) {
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay';
  overlay.innerHTML = `
    <div class="modal">
      <div class="modal-header">
        <h2>${title}</h2>
        <button class="btn btn-ghost btn-icon" type="button" data-close>✕</button>
      </div>
      <form id="modal-form">
        ${fields}
        <div style="display:flex;gap:8px;margin-top:20px;justify-content:flex-end">
          <button class="btn btn-secondary" type="button" data-close>Cancel</button>
          <button class="btn btn-primary" type="submit">Save</button>
        </div>
      </form>
    </div>
  `;
  document.body.appendChild(overlay);
  overlay.querySelectorAll('[data-close]').forEach((el) =>
    el.addEventListener('click', () => overlay.remove())
  );
  overlay.querySelector('#modal-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    await onSubmit(new FormData(e.target));
    overlay.remove();
  });
}

export async function renderTasksModule(container) {
  async function load() {
    const data = await api('/tasks?page_size=50');
    const items = data?.items || [];

    container.innerHTML = `
      <div style="display:flex;justify-content:flex-end;margin-bottom:16px">
        <button class="btn btn-primary" id="add-task" type="button">+ New Task</button>
      </div>
      <div class="card table-wrap">
        ${
          items.length
            ? `<table>
            <thead><tr><th>Title</th><th>Status</th><th>Priority</th><th>Due</th><th></th></tr></thead>
            <tbody>${items
              .map(
                (t) => `<tr data-id="${t.id}">
              <td>${t.title}</td>
              <td>${statusBadge(t.status)}</td>
              <td>${t.priority}</td>
              <td>${t.due_date ? new Date(t.due_date).toLocaleDateString() : '—'}</td>
              <td style="white-space:nowrap">
                <button class="btn btn-ghost btn-sm edit-task" data-id="${t.id}">Edit</button>
                <button class="btn btn-danger btn-sm delete-task" data-id="${t.id}">Delete</button>
              </td>
            </tr>`
              )
              .join('')}</tbody></table>`
            : '<div class="empty-state">No tasks yet</div>'
        }
      </div>
    `;

    document.getElementById('add-task')?.addEventListener('click', () => {
      showModal(
        'New Task',
        `
        <div class="form-group"><label>Title</label><input class="form-control" name="title" required /></div>
        <div class="form-group"><label>Description</label><textarea class="form-control" name="description"></textarea></div>
        <div class="form-group"><label>Priority</label>
          <select class="form-control" name="priority">
            <option value="low">Low</option>
            <option value="medium" selected>Medium</option>
            <option value="high">High</option>
          </select>
        </div>`,
        async (fd) => {
          await api('/tasks', {
            method: 'POST',
            body: {
              title: fd.get('title'),
              description: fd.get('description') || null,
              priority: fd.get('priority'),
            },
          });
          showToast('Task created');
          load();
        }
      );
    });

    container.querySelectorAll('.delete-task').forEach((btn) => {
      btn.addEventListener('click', async () => {
        if (!confirm('Delete this task?')) return;
        await api(`/tasks/${btn.dataset.id}`, { method: 'DELETE' });
        showToast('Task deleted');
        load();
      });
    });

    container.querySelectorAll('.edit-task').forEach((btn) => {
      btn.addEventListener('click', async () => {
        const task = items.find((t) => t.id === btn.dataset.id);
        showModal(
          'Edit Task',
          `
          <div class="form-group"><label>Title</label><input class="form-control" name="title" value="${task.title}" required /></div>
          <div class="form-group"><label>Status</label>
            <select class="form-control" name="status">
              <option value="pending"${task.status === 'pending' ? ' selected' : ''}>Pending</option>
              <option value="in_progress"${task.status === 'in_progress' ? ' selected' : ''}>In Progress</option>
              <option value="completed"${task.status === 'completed' ? ' selected' : ''}>Completed</option>
            </select>
          </div>`,
          async (fd) => {
            await api(`/tasks/${task.id}`, {
              method: 'PATCH',
              body: { title: fd.get('title'), status: fd.get('status') },
            });
            showToast('Task updated');
            load();
          }
        );
      });
    });
  }

  try {
    await load();
  } catch (err) {
    container.innerHTML = `<div class="empty-state">${err.message}</div>`;
  }
}
