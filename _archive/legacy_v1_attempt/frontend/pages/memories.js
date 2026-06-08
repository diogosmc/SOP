import { api } from '../services/api.js';

export async function renderMemoriesPage(container) {
  let memories = [];
  try {
    const data = await api('/memories?page_size=50');
    memories = data?.items || data || [];
  } catch {
    memories = [];
  }

  container.innerHTML = `
    <div class="page-header">
      <h1>Memories</h1>
      <p>What COPILOTO remembers about you</p>
    </div>
    ${
      memories.length
        ? `<div class="page-grid cols-2">${memories
            .map(
              (m) => `
          <div class="card">
            <div style="font-weight:600;margin-bottom:8px">${m.title || m.category || 'Memory'}</div>
            <p style="color:var(--text-secondary);font-size:13px">${m.content || m.summary || ''}</p>
          </div>`
            )
            .join('')}</div>`
        : '<div class="card empty-state">No memories yet. Chat with COPILOTO to build your knowledge graph.</div>'
    }
  `;
}
