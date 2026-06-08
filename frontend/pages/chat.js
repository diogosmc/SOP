/** @returns {HTMLElement} */
export function renderChatPage() {
  const page = document.createElement("section");
  page.className = "page page--chat";
  page.innerHTML = `
    <div class="page__intro">
      <h2 class="page__heading">Chat</h2>
      <p class="page__description">Interface de conversa com o Copiloto — integração WebSocket na próxima fase.</p>
    </div>
    <div class="chat-skeleton">
      <div class="chat-skeleton__messages">
        <div class="chat-bubble chat-bubble--assistant">
          <p>Olá! Sou o Copiloto. Em breve você poderá conversar comigo aqui em tempo real.</p>
        </div>
        <div class="chat-bubble chat-bubble--user">
          <p>Quero organizar meu dia e revisar minhas metas.</p>
        </div>
        <div class="chat-bubble chat-bubble--assistant chat-bubble--muted">
          <p>Streaming via <code>/ws/chat</code> será conectado na Fase 15+.</p>
        </div>
      </div>
      <form class="chat-skeleton__composer" aria-label="Composer de chat (desabilitado)">
        <input type="text" placeholder="Digite sua mensagem..." disabled />
        <button type="button" disabled>Enviar</button>
      </form>
    </div>
  `;
  return page;
}
