import axios from 'axios';

let widgetApiBaseOverride: string | null = null;

export function setWidgetApiBaseOverride(url: string | null) {
  widgetApiBaseOverride = url ? url.trim().replace(/\/$/, '') : null;
}

function isLoopbackApiUrl(url: string): boolean {
  return /^https?:\/\/(127\.0\.0\.1|localhost)(:\d+)?\/?$/i.test(url.trim());
}

function inferChatAzureApiBase(hostname: string): string {
  if (!hostname.endsWith('.azurewebsites.net')) return '';
  if (!hostname.startsWith('app-chat-')) return '';
  return `https://api-chat-${hostname.slice('app-chat-'.length)}`;
}

export const getApiBaseUrl = (): string => {
  if (widgetApiBaseOverride) {
    return widgetApiBaseOverride;
  }
  if (typeof window !== 'undefined') {
    const fromRuntime = String(
      (window as any).__RUNTIME_CONFIG__?.VITE_API_BASE_URL ?? ''
    ).trim();
    if (fromRuntime) return fromRuntime;
    const host = window.location.hostname;
    const fromBuild = String(import.meta.env.VITE_API_BASE_URL ?? '').trim();
    const onAzureFe =
      host.endsWith('.azurewebsites.net') &&
      host !== 'localhost' &&
      host !== '127.0.0.1';
    if (fromBuild && !(onAzureFe && isLoopbackApiUrl(fromBuild))) {
      return fromBuild;
    }
    const inferred = inferChatAzureApiBase(host);
    if (inferred) return inferred;
    if (import.meta.env.DEV) {
      return fromBuild || 'http://localhost:8000';
    }
    return '';
  }
  const fromBuild = String(import.meta.env.VITE_API_BASE_URL ?? '').trim();
  if (fromBuild) return fromBuild;
  return import.meta.env.DEV ? 'http://localhost:8000' : '';
};

export const api = axios.create({
  baseURL: '',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000,
  withCredentials: true,
});

let cachedEasyAuthHeaders: Record<string, string> | null = null;

export const setEasyAuthHeaders = (headers: Record<string, string> | null) => {
  cachedEasyAuthHeaders = headers;
};

api.interceptors.request.use((config) => {
  const base = getApiBaseUrl();
  config.baseURL = base || '';
  return config;
});

api.interceptors.request.use(
  (config) => {
    if (cachedEasyAuthHeaders && config.headers) {
      Object.keys(cachedEasyAuthHeaders).forEach(key => {
        if (config.headers) {
          config.headers[key] = cachedEasyAuthHeaders![key];
        }
      });
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // If we get a 302 redirect, it means we need to authenticate
    // Don't automatically redirect here, let the UI handle it
    return Promise.reject(error);
  }
);

// Types
export interface Product {
  id: string;
  title: string;
  price: number;
  originalPrice?: number;
  rating: number;
  reviewCount: number;
  image: string;
  category: string;
  inStock: boolean;
  description: string;
}

export interface ChatMessage {
  id: string;
  content: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
}

// Timestamp utility functions
export const parseTimestamp = (timestamp: string | Date | number): Date => {
  if (timestamp instanceof Date) {
    return timestamp;
  }
  
  if (typeof timestamp === 'number') {
    return new Date(timestamp);
  }
  
  if (typeof timestamp === 'string') {
    // Handle ISO strings - let Date constructor handle timezone conversion
    return new Date(timestamp);
  }
  
  return new Date();
};

export const formatTimestamp = (timestamp: Date): string => {
  // Use user's local timezone for display
  return timestamp.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
    timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone
  });
};

export const createTimestamp = (): Date => {
  return new Date();
};

export interface VoiceLiveConfig {
  enabled: boolean;
  mode: string;
  model: string;
  voice: string;
  transcribe_model: string;
  instructions: string;
}

// API Functions
export const getChatHistory = async (sessionId?: string): Promise<ChatMessage[]> => {
  try {
    if (sessionId) {
      const response = await api.get(`/api/chat/sessions/${sessionId}`);
      const messages = response.data.messages || [];
      
      return messages.map((msg: any) => ({
        id: msg.id,
        content: msg.content,
        sender: msg.sender || msg.message_type,
        timestamp: parseTimestamp(msg.timestamp || msg.created_at)
      }));
    } else {
      const response = await api.get('/api/chat/history');
      
      return response.data.map((msg: any) => ({
        id: msg.id,
        content: msg.content,
        sender: msg.sender || msg.message_type,
        timestamp: parseTimestamp(msg.timestamp || msg.created_at)
      }));
    }
  } catch (error: any) {
    return [];
  }
};

export const sendMessageToChat = async (message: string, sessionId?: string): Promise<ChatMessage> => {
  try {
    const payload: any = { content: message, message_type: 'user' };
    if (sessionId) {
      payload.session_id = sessionId;
    }
    const response = await api.post('/api/chat/message', payload);
    return {
      id: response.data.id,
      content: response.data.content,
      sender: response.data.sender || response.data.message_type,
      timestamp: parseTimestamp(response.data.timestamp || response.data.created_at)
    };
  } catch (error) {
    throw error;
  }
};

export const createNewChatSession = async (): Promise<{ session_id: string; session_name: string; created_at: string }> => {
  try {
    const response = await api.post('/api/chat/sessions/new');
    return response.data.data;
  } catch (error) {
    throw error;
  }
};

const CHAT_SESSION_KEY = 'current_chat_session_id';

export const saveCurrentSessionId = (sessionId: string): void => {
  try {
    localStorage.setItem(CHAT_SESSION_KEY, sessionId);
  } catch (error) {
    // Silently fail if localStorage is not available
  }
};

export const getCurrentSessionId = (): string | null => {
  try {
    return localStorage.getItem(CHAT_SESSION_KEY);
  } catch (error) {
    return null;
  }
};

export const clearCurrentSessionId = (): void => {
  try {
    localStorage.removeItem(CHAT_SESSION_KEY);
  } catch (error) {
    // Silently fail if localStorage is not available
  }
};

export const getVoiceLiveConfig = async (): Promise<VoiceLiveConfig> => {
  const response = await api.get('/api/voice/config');
  return response.data as VoiceLiveConfig;
};

export type ChatConfig = {
  scenario: string;
  welcomeTitle: string;
  welcomeSubtitle: string;
  welcomeHint: string;
  complianceBanner: string;
  agentConfigured: boolean;
};

export const getChatConfig = async (): Promise<ChatConfig> => {
  const response = await api.get('/api/chat/config');
  return response.data as ChatConfig;
};

/** Save a voice message to the chat session (Cosmos DB) without triggering Foundry agents. */
export const saveVoiceMessage = async (
  sessionId: string,
  content: string,
  sender: 'user' | 'assistant',
): Promise<void> => {
  try {
    await api.post('/api/chat/save-voice-message', {
      session_id: sessionId,
      content,
      message_type: sender,
    });
  } catch {
    // Non-critical — if save fails, message still shows in UI
  }
};