import { renderNotesModule } from '../modules/notes/index.js';

export async function renderNotesPage(container) {
  container.innerHTML = `
    <div class="page-header">
      <h1>Notes</h1>
      <p>Markdown notes with tags</p>
    </div>
    <div id="notes-module"></div>
  `;
  await renderNotesModule(document.getElementById('notes-module'));
}
