import { renderHabitsModule } from '../modules/habits/index.js';

export async function renderHabitsPage(container) {
  container.innerHTML = `
    <div class="page-header">
      <h1>Habits</h1>
      <p>Track streaks and daily consistency</p>
    </div>
    <div id="habits-module"></div>
  `;
  await renderHabitsModule(document.getElementById('habits-module'));
}
