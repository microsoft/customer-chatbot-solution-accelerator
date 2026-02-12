import axios from 'axios';

const getApiBaseUrl = (): string => {
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

export interface CartItem {
  product: Product;
  quantity: number;
}

// API Functions
export const getProducts = async (): Promise<Product[]> => {
  try {
    const response = await api.get('/api/products/');
    
    // Check if response has data
    if (!response.data || !Array.isArray(response.data)) {
      throw new Error('Invalid response format from API');
    }
    
    // Transform the data to match frontend interface
    const transformedData = response.data.map((product: any) => ({
      id: product.id,
      title: product.title,
      price: product.price,
      originalPrice: product.original_price || undefined,
      rating: product.rating,
      reviewCount: product.review_count,
      image: product.image,
      category: product.category,
      inStock: product.in_stock,
      description: product.description || ''
    }));
    
    return transformedData;
  } catch (error: any) {
    throw new Error(`Failed to fetch products: ${error.message || 'Unknown error'}`);
  }
};

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


export const addToCart = async (productId: string, quantity: number = 1): Promise<void> => {
  try {
    await api.post('/api/cart/add', { product_id: productId, quantity });
  } catch (error) {
    throw error;
  }
};

export const getCart = async (): Promise<CartItem[]> => {
  try {
    const response = await api.get('/api/cart/');
    
    // Backend returns Cart object with items array, frontend expects CartItem array
    const cart = response.data;
    if (!cart || !cart.items) {
      return [];
    }
    
    // Transform backend CartItem format to frontend CartItem format
    const transformedItems = cart.items.map((item: any) => ({
      product: {
        id: item.product_id,
        title: item.product_title,
        price: item.product_price,
        image: item.product_image,
        // Add default values for missing fields
        originalPrice: undefined,
        rating: 4.0,
        reviewCount: 0,
        category: 'Unknown',
        inStock: true,
        description: ''
      },
      quantity: item.quantity
    }));
    
    return transformedItems;
  } catch (error) {
    return [];
  }
};

export const updateCartItem = async (productId: string, quantity: number): Promise<void> => {
  try {
    await api.put(`/api/cart/update?product_id=${productId}&quantity=${quantity}`);
  } catch (error) {
    throw error;
  }
};

export const removeFromCart = async (productId: string): Promise<void> => {
  try {
    await api.delete(`/api/cart/${productId}`);
  } catch (error) {
    throw error;
  }
};

export const checkoutCart = async (): Promise<{ order_id: string; order_number: string; total: number; status: string }> => {
  try {
    const response = await api.post('/api/cart/checkout');
    return response.data.data;
  } catch (error) {
    throw error;
  }
};