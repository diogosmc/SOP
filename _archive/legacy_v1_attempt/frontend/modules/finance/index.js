import { Chart, registerables } from 'chart.js';
import { api, showToast } from '../../services/api.js';

Chart.register(...registerables);

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

export async function renderFinanceModule(container) {
  let transactions = [];
  try {
    const data = await api('/finance/transactions?page_size=50');
    transactions = data?.items || data || [];
  } catch {
    transactions = [];
  }

  const income = transactions.filter((t) => t.transaction_type === 'income').reduce((s, t) => s + Number(t.amount), 0);
  const expense = transactions.filter((t) => t.transaction_type === 'expense').reduce((s, t) => s + Number(t.amount), 0);

  container.innerHTML = `
    <div class="page-grid cols-3" style="margin-bottom:16px">
      <div class="card"><div class="card-title">Income</div><div class="stat-value" style="color:var(--success)">R$ ${income.toFixed(2)}</div></div>
      <div class="card"><div class="card-title">Expenses</div><div class="stat-value" style="color:var(--danger)">R$ ${expense.toFixed(2)}</div></div>
      <div class="card"><div class="card-title">Balance</div><div class="stat-value">R$ ${(income - expense).toFixed(2)}</div></div>
    </div>
    <div class="page-grid cols-2" style="margin-bottom:16px">
      <div class="card"><div class="card-title">Overview</div><div class="chart-container"><canvas id="finance-chart"></canvas></div></div>
      <div class="card">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
          <div class="card-title" style="margin:0">Transactions</div>
          <button class="btn btn-primary btn-sm" id="add-transaction" type="button">+ Add</button>
        </div>
        <div class="table-wrap">
          ${
            transactions.length
              ? `<table><thead><tr><th>Description</th><th>Type</th><th>Amount</th></tr></thead>
              <tbody>${transactions
                .map(
                  (t) => `<tr>
                <td>${t.description || '—'}</td>
                <td>${t.transaction_type}</td>
                <td style="color:${t.transaction_type === 'income' ? 'var(--success)' : 'var(--danger)'}">R$ ${Number(t.amount).toFixed(2)}</td>
              </tr>`
                )
                .join('')}</tbody></table>`
              : '<div class="empty-state">No transactions</div>'
          }
        </div>
      </div>
    </div>`;

  new Chart(document.getElementById('finance-chart'), {
    type: 'bar',
    data: {
      labels: ['Income', 'Expenses'],
      datasets: [{ data: [income, expense], backgroundColor: ['#22c55e', '#ef4444'], borderRadius: 6 }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: '#71717a' }, grid: { display: false } },
        y: { ticks: { color: '#71717a' }, grid: { color: '#27272a' } },
      },
    },
  });

  document.getElementById('add-transaction')?.addEventListener('click', () => {
    showModal(
      'New Transaction',
      `<div class="form-group"><label>Description</label><input class="form-control" name="description" /></div>
       <div class="form-group"><label>Type</label>
         <select class="form-control" name="transaction_type"><option value="expense">Expense</option><option value="income">Income</option></select>
       </div>
       <div class="form-group"><label>Amount</label><input class="form-control" name="amount" type="number" step="0.01" min="0" required /></div>
       <div class="form-group"><label>Date</label><input class="form-control" name="transaction_date" type="date" value="${new Date().toISOString().slice(0, 10)}" required /></div>`,
      async (fd) => {
        await api('/finance/transactions', {
          method: 'POST',
          body: {
            description: fd.get('description') || null,
            transaction_type: fd.get('transaction_type'),
            amount: parseFloat(fd.get('amount')),
            transaction_date: fd.get('transaction_date'),
          },
        });
        showToast('Transaction added');
        renderFinanceModule(container);
      }
    );
  });
}
