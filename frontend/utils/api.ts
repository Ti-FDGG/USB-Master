/**
 * API 客户端工具
 */
import axios from 'axios';

// 创建 axios 实例
const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error) => {
    console.error('API Error:', error);
    if (error.response) {
      return Promise.reject(error.response.data || error);
    }
    return Promise.reject(error);
  }
);

export default api;

// WebSocket 连接工具
export class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private listeners: Map<string, Set<(data: any) => void>> = new Map();
  private isManualDisconnect = false;
  private reconnectTimer: NodeJS.Timeout | null = null;

  constructor(url: string) {
    this.url = url.startsWith('ws://') || url.startsWith('wss://') ? url : `ws://localhost:8000${url}`;
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        // 如果已有连接，先关闭
        if (this.ws) {
          this.ws.close();
        }

        this.isManualDisconnect = false;
        this.ws = new WebSocket(this.url);

        const timeout = setTimeout(() => {
          if (this.ws && this.ws.readyState !== WebSocket.OPEN) {
            this.ws.close();
            reject(new Error('WebSocket connection timeout'));
          }
        }, 10000); // 10秒超时

        this.ws.onopen = () => {
          clearTimeout(timeout);
          console.log('WebSocket connected to', this.url);
          this.reconnectAttempts = 0;
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            this.emit(data.type || 'message', data);
          } catch (e) {
            console.warn('Failed to parse WebSocket message:', e);
            this.emit('message', event.data);
          }
        };

        this.ws.onerror = (error) => {
          clearTimeout(timeout);
          console.error('WebSocket error:', error);
          // 只有在非手动断开时才拒绝Promise
          if (!this.isManualDisconnect) {
            reject(new Error('WebSocket connection failed'));
          }
        };

        this.ws.onclose = (event) => {
          clearTimeout(timeout);
          console.log('WebSocket closed', event.code, event.reason);
          this.ws = null;
          
          // 只有在非手动断开且连接异常关闭时才尝试重连
          if (!this.isManualDisconnect && event.code !== 1000) {
            this.attemptReconnect();
          }
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  private attemptReconnect() {
    if (this.isManualDisconnect) {
      return;
    }

    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * this.reconnectAttempts;
      console.log(`Attempting to reconnect in ${delay}ms (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
      
      this.reconnectTimer = setTimeout(() => {
        if (!this.isManualDisconnect) {
          this.connect().catch((error) => {
            console.error('Reconnection failed:', error);
            // 继续尝试重连
            if (this.reconnectAttempts < this.maxReconnectAttempts) {
              this.attemptReconnect();
            } else {
              console.error('Max reconnection attempts reached');
            }
          });
        }
      }, delay);
    } else {
      console.error('Max reconnection attempts reached. Please refresh the page.');
    }
  }

  on(event: string, callback: (data: any) => void) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback);
  }

  off(event: string, callback: (data: any) => void) {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      callbacks.delete(callback);
    }
  }

  private emit(event: string, data: any) {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      callbacks.forEach(callback => callback(data));
    }
  }

  send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(typeof data === 'string' ? data : JSON.stringify(data));
    }
  }

  disconnect() {
    this.isManualDisconnect = true;
    
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    
    if (this.ws) {
      this.ws.close(1000, 'Manual disconnect');
      this.ws = null;
    }
    
    this.listeners.clear();
    this.reconnectAttempts = 0;
  }
}

