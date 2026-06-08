import { api, showToast } from '../../services/api.js';

function showModal(title, fields, onSubmit) {
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay';
  overlay.innerHTML = `
    <div class="modal" style="max-width:560px">
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

export async function renderNotesModule(container) {
  async function load() {
    const data = await api('/notes?page_size=50');
    const items = data?.items || [];

    container.innerHTML = `
      <div style="display:flex;justify-content:flex-end;margin-bottom:16px">
        <button class="btn btn-primary" id="add-note" type="button">+ New Note</button>
      </div>
      <div class="page-grid cols-2">
        ${items
          .map(
            (n) => `
          <div class="card note-card" data-id="${n.id}" style="cursor:pointer">
            <div style="font-weight:600;margin-bottom:8px">${n.title}</div>
            <p style="color:var(--text-secondary);font-size:13px;overflow:hidden;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical">${n.content || ''}</p>
            ${n.tags?.length ? `<div style="margin-top:8px">${n.tags.map((t) => `<span class="badge badge-active">${t}</span>`).join(' ')}</div>` : ''}
          </div>`
          )
          .join('') || '<div class="card empty-state">No notes yet</div>'}
      </div>`;

    document.getElementById('add-note')?.addEventListener('click', () => {
      showModal(
        'New Note',
        `<div class="form-group"><label>Title</label><input class="form-control" name="title" required /></div>
         <div class="form-group"><label>Content (Markdown)</label><textarea class="form-control" name="content" style="min-height:160px"></textarea></div>
         <div class="form-group"><label>Tags (comma-separated)</label><input class="form-control" name="tags" /></div>`,
        async (fd) => {
          const tags = fd.get('tags') ? String(fd.get('tags')).split(',').map((t) => t.trim()).filter(Boolean) : null;
          await api('/notes', { method: 'POST', body: { title: fd.get('title'), content: fd.get('content') || '', tags } });
          showToast('Note created');
          load();
        }
      );
    });

    container.querySelectorAll('.note-card').forEach((card) => {
      card.addEventListener('click', async () => {
        const note = items.find((n) => n.id === card.dataset.id);
        showModal(
          'Edit Note',
          `<div class="form-group"><label>Title</label><input class="form-control" name="title" value="${note.title.replace(/"/g, '&quot;')}" required /></div>
           <div class="form-group"><label>Content</label><textarea class="form-control" name="content" style="min-height:160px">${note.content || ''}</textarea></div>`,
          async (fd) => {
            await api(`/notes/${note.id}`, { method: 'PATCH', body: { title: fd.get('title'), content: fd.get('content') } });
            showToast('Note updated');
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
