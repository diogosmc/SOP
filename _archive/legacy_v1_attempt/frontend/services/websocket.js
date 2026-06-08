import { showToast } from './api.js';

let socket = null;
let reconnectTimer = null;
const listeners = new Map();

function getWsUrl() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}/ws/chat`;
}

export function connectWebSocket() {
  if (socket?.readyState === WebSocket.OPEN) return socket;

  socket = new WebSocket(getWsUrl());

  socket.onopen = () => {
    emit('connected', null);
  };

  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      emit(data.type || 'message', data);
    } catch {
      emit('message', { content: event.data });
    }
  };

  socket.onclose = () => {
    emit('disconnected', null);
    reconnectTimer = setTimeout(connectWebSocket, 3000);
  };

  socket.onerror = () => {
    showToast('WebSocket connection error', 'error');
  };

  return socket;
}

export function disconnectWebSocket() {
  if (reconnectTimer) clearTimeout(reconnectTimer);
  if (socket) {
    socket.close();
    socket = null;
  }
}

export function sendMessage(payload) {
  if (socket?.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify(payload));
  }
}

export function on(event, callback) {
  if (!listeners.has(event)) listeners.set(event, new Set());
  listeners.get(event).add(callback);
  return () => listeners.get(event)?.delete(callback);
}

function emit(event, data) {
  listeners.get(event)?.forEach((cb) => cb(data));
}
