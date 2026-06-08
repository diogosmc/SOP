import { connectWebSocket, on, sendMessage } from '../services/websocket.js';

export async function renderChatPage(container) {
  container.innerHTML = `
    <div class="page-header">
      <h1>Chat</h1>
      <p>Talk to your COPILOTO assistant</p>
    </div>
    <div class="card" style="display:flex;flex-direction:column;height:calc(100vh - 180px)">
      <div id="chat-messages" style="flex:1;overflow-y:auto;padding:8px;display:flex;flex-direction:column;gap:12px"></div>
      <form id="chat-form" style="display:flex;gap:8px;margin-top:12px;border-top:1px solid var(--border-subtle);padding-top:12px">
        <input class="form-control" id="chat-input" placeholder="Type a message…" autocomplete="off" />
        <button class="btn btn-primary" type="submit">Send</button>
      </form>
    </div>
  `;

  const messagesEl = document.getElementById('chat-messages');
  const form = document.getElementById('chat-form');
  const input = document.getElementById('chat-input');

  function appendMessage(role, content) {
    const div = document.createElement('div');
    div.style.cssText = `padding:10px 14px;border-radius:var(--radius-md);max-width:80%;font-size:14px;${
      role === 'user'
        ? 'align-self:flex-end;background:var(--accent-muted);color:var(--accent-hover)'
        : 'align-self:flex-start;background:var(--bg-elevated)'
    }`;
    div.textContent = content;
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  connectWebSocket();
  on('message', (data) => {
    if (data.content) appendMessage('assistant', data.content);
  });

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text) return;
    appendMessage('user', text);
    sendMessage({ type: 'chat', content: text });
    input.value = '';
  });
}
