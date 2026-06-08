import { renderStudyModule } from '../modules/study/index.js';

export async function renderStudyPage(container) {
  container.innerHTML = `
    <div class="page-header">
      <h1>Study</h1>
      <p>Subjects, topics, and flashcards</p>
    </div>
    <div id="study-module"></div>
  `;
  await renderStudyModule(document.getElementById('study-module'));
}
