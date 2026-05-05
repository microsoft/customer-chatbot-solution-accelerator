import axios from 'axios';

export const getApiBaseUrl = (): string => {
  if (typeof window !== 'undefined' && (window as any).__RUNTIME_CONFIG__?.VITE_API_BASE_URL) {
    return (window as any).__RUNTIME_CONFIG__.VITE_API_BASE_URL;
  }

  return import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
};

const API_BASE_URL = getApiBaseUrl();

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000, // 60 seconds to handle cold starts
  withCredentials: true, // This is crucial for Easy Auth cookies
});

// Store Easy Auth headers globally
let cachedEasyAuthHeaders: Record<string, string> | null = null;

export const setEasyAuthHeaders = (headers: Record<string, string> | null) => {
  cachedEasyAuthHeaders = headers;
};

// Add request interceptor to handle authentication
api.interceptors.request.use(
  (config) => {
    // Add cached Easy Auth headers to all requests
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

// Add response interceptor to handle authentication redirects
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