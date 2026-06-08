import { api } from '../services/api.js';

export async function renderReportsPage(container) {
  let reports = [];
  try {
    reports = (await api('/reports')) || [];
  } catch {
    reports = [];
  }

  container.innerHTML = `
    <div class="page-header">
      <h1>Reports</h1>
      <p>Daily and weekly summaries</p>
    </div>
    ${
      Array.isArray(reports) && reports.length
        ? `<div class="table-wrap card"><table>
            <thead><tr><th>Title</th><th>Type</th><th>Date</th></tr></thead>
            <tbody>${reports
              .map(
                (r) => `<tr>
              <td>${r.title || 'Report'}</td>
              <td>${r.report_type || r.type || '—'}</td>
              <td>${r.created_at ? new Date(r.created_at).toLocaleDateString() : '—'}</td>
            </tr>`
              )
              .join('')}</tbody></table></div>`
        : '<div class="card empty-state">No reports generated yet.</div>'
    }
  `;
}
