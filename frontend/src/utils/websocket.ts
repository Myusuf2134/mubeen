// Shared WebSocket URL helper — resolves to backend, not Vite dev server.

export function getWebSocketBase(): string {
  return import.meta.env.VITE_WS_BASE ?? 'ws://localhost:8000';
}
