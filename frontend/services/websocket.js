/**
 * WebSocket client prepared for /ws/chat (not fully integrated in Fase 14).
 */
export class ChatWebSocket {
  /** @param {string} [url] */
  constructor(url) {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    this.url = url || `${protocol}//${host}/ws/chat`;
    /** @type {WebSocket|null} */
    this.socket = null;
    /** @type {Set<(event: MessageEvent) => void>} */
    this.listeners = new Set();
  }

  connect() {
    if (this.socket?.readyState === WebSocket.OPEN) {
      return this.socket;
    }

    this.socket = new WebSocket(this.url);

    this.socket.addEventListener("message", (event) => {
      this.listeners.forEach((listener) => listener(event));
    });

    this.socket.addEventListener("error", () => {
      console.warn("[COPILOTO] WebSocket error — chat integration pending");
    });

    return this.socket;
  }

  /** @param {(event: MessageEvent) => void} listener */
  onMessage(listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  /** @param {object} payload */
  send(payload) {
    if (this.socket?.readyState !== WebSocket.OPEN) {
      throw new Error("WebSocket não conectado");
    }
    this.socket.send(JSON.stringify(payload));
  }

  disconnect() {
    this.socket?.close();
    this.socket = null;
  }
}

export const chatSocket = new ChatWebSocket();
