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

export async function renderStudyModule(container) {
  let subjects = [];
  try {
    const data = await api('/study/subjects?page_size=50');
    subjects = data?.items || data || [];
  } catch {
    subjects = [];
  }

  container.innerHTML = `
    <div style="display:flex;justify-content:flex-end;margin-bottom:16px">
      <button class="btn btn-primary" id="add-subject" type="button">+ New Subject</button>
    </div>
    <div class="page-grid cols-2">
      ${subjects
        .map(
          (s) => `
        <div class="card">
          <div style="font-weight:600;font-size:15px">${s.name}</div>
          <div style="margin-top:12px;display:flex;gap:8px">
            <button class="btn btn-ghost btn-sm add-topic" data-id="${s.id}">+ Topic</button>
            <button class="btn btn-danger btn-sm delete-subject" data-id="${s.id}">Delete</button>
          </div>
        </div>`
        )
        .join('') || '<div class="card empty-state">No study subjects yet</div>'}
    </div>`;

  document.getElementById('add-subject')?.addEventListener('click', () => {
    showModal(
      'New Subject',
      `<div class="form-group"><label>Name</label><input class="form-control" name="name" required /></div>`,
      async (fd) => {
        await api('/study/subjects', { method: 'POST', body: { name: fd.get('name') } });
        showToast('Subject created');
        renderStudyModule(container);
      }
    );
  });

  container.querySelectorAll('.delete-subject').forEach((btn) => {
    btn.addEventListener('click', async () => {
      if (!confirm('Delete subject?')) return;
      await api(`/study/subjects/${btn.dataset.id}`, { method: 'DELETE' });
      showToast('Subject deleted');
      renderStudyModule(container);
    });
  });

  container.querySelectorAll('.add-topic').forEach((btn) => {
    btn.addEventListener('click', () => {
      showModal(
        'New Topic',
        `<div class="form-group"><label>Title</label><input class="form-control" name="title" required /></div>`,
        async (fd) => {
          await api('/study/topics', {
            method: 'POST',
            body: { title: fd.get('title'), subject_id: btn.dataset.id },
          });
          showToast('Topic created');
        }
      );
    });
  });
}
