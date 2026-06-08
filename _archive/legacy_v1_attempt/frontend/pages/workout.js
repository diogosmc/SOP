import { renderWorkoutModule } from '../modules/workout/index.js';

export async function renderWorkoutPage(container) {
  container.innerHTML = `
    <div class="page-header">
      <h1>Workout</h1>
      <p>Training plans and sessions</p>
    </div>
    <div id="workout-module"></div>
  `;
  await renderWorkoutModule(document.getElementById('workout-module'));
}
