import { renderFinanceModule } from '../modules/finance/index.js';

export async function renderFinancePage(container) {
  container.innerHTML = `
    <div class="page-header">
      <h1>Finance</h1>
      <p>Income, expenses, and goals</p>
    </div>
    <div id="finance-module"></div>
  `;
  await renderFinanceModule(document.getElementById('finance-module'));
}
