import { renderTasksModule } from '../modules/tasks/index.js';

export async function renderTasksPage(container) {
  container.innerHTML = `
    <div class="page-header">
      <h1>Tasks</h1>
      <p>Manage your tasks and priorities</p>
    </div>
    <div id="tasks-module"></div>
  `;
  await renderTasksModule(document.getElementById('tasks-module'));
}
