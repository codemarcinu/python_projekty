import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Mock WebSocket
class MockWebSocket {
  onopen: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: ((error: any) => void) | null = null;
  readyState = WebSocket.OPEN;

  constructor() {
    setTimeout(() => this.onopen?.(), 0);
  }

  send(data: string) {
    // Mock implementation
  }

  close() {
    this.readyState = WebSocket.CLOSED;
    this.onclose?.();
  }
}

vi.stubGlobal('WebSocket', MockWebSocket);

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn()
};

vi.stubGlobal('localStorage', localStorageMock);

// Mock fetch
const fetchMock = vi.fn();
vi.stubGlobal('fetch', fetchMock);

// Reset all mocks before each test
beforeEach(() => {
  vi.clearAllMocks();
}); 