import { createErrorResponse, retryRequest } from '@/lib/utils/apiUtils';
import { api, httpClient, setEasyAuthHeaders } from '@/lib/utils/httpClient';
import { createUserMessage, toChatMessage } from '@/lib/utils/messageUtils';

export { api, setEasyAuthHeaders };

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
  sender: 'user' | 'assistant' | 'error' | 'chart';
  timestamp: string;
}

export const parseTimestamp = (timestamp: string | Date | number): Date => {
  if (timestamp instanceof Date) {
    return timestamp;
  }
  
  if (typeof timestamp === 'number') {
    return new Date(timestamp);
  }
  
  if (typeof timestamp === 'string') {
    return new Date(timestamp);
  }
  
  return new Date();
};

export const formatTimestamp = (timestamp: string | Date | number): string => {
  return parseTimestamp(timestamp).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
    timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone
  });
};

export const createTimestamp = (): string => {
  return new Date().toISOString();
};

export interface ChatSessionSummary {
  id: string;
  session_name: string;
  message_count: number;
  last_message_at?: string;
  is_active?: boolean;
  created_at?: string;
}

export interface CartItem {
  product: Product;
  quantity: number;
}

export const getProducts = async (): Promise<Product[]> => {
  try {
    const response = await httpClient.get<any[]>('/api/products/');
    
    if (!response || !Array.isArray(response)) {
      throw new Error('Invalid response format from API');
    }
    
    const transformedData = response.map((product: any) => ({
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
  } catch (error) {
    const normalized = createErrorResponse(500, 'Failed to fetch products', error);
    throw new Error(normalized.message);
  }
};

export const getChatHistory = async (sessionId?: string): Promise<ChatMessage[]> => {
  try {
    if (sessionId) {
      const response = await httpClient.get<{ messages?: any[] }>(`/api/chat/sessions/${sessionId}`);
      const messages = response.messages || [];
      
      return messages.map(toChatMessage);
    } else {
      const response = await httpClient.get<any[]>('/api/chat/history');
      return response.map(toChatMessage);
    }
  } catch {
    return [];
  }
};

export const sendMessageToChat = async (message: string, sessionId?: string): Promise<ChatMessage> => {
  try {
    const payload: any = { content: message, message_type: 'user' };
    if (sessionId) {
      payload.session_id = sessionId;
    }
    const response = await retryRequest(() => httpClient.post<any>('/api/chat/message', payload), 2, 300);
    return toChatMessage(response);
  } catch (error) {
    throw error;
  }
};

export const createNewChatSession = async (): Promise<{ session_id: string; session_name: string; created_at: string }> => {
  try {
    const response = await httpClient.post<{ data: { session_id: string; session_name: string; created_at: string } }>('/api/chat/sessions/new');
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const getChatSessions = async (): Promise<ChatSessionSummary[]> => {
  try {
    return await httpClient.get<ChatSessionSummary[]>('/api/chat/sessions');
  } catch {
    return [];
  }
};

export const renameChatSession = async (sessionId: string, name: string): Promise<void> => {
  await httpClient.put(`/api/chat/sessions/${sessionId}`, { session_name: name });
};

export const deleteChatSession = async (sessionId: string): Promise<void> => {
  await httpClient.delete(`/api/chat/sessions/${sessionId}`);
};

const CHAT_SESSION_KEY = 'current_chat_session_id';

export const saveCurrentSessionId = (sessionId: string): void => {
  try {
    localStorage.setItem(CHAT_SESSION_KEY, sessionId);
  } catch {
  }
};

export const getCurrentSessionId = (): string | null => {
  try {
    return localStorage.getItem(CHAT_SESSION_KEY);
  } catch {
    return null;
  }
};

export const clearCurrentSessionId = (): void => {
  try {
    localStorage.removeItem(CHAT_SESSION_KEY);
  } catch {
  }
};


export const addToCart = async (productId: string, quantity: number = 1): Promise<void> => {
  try {
    await httpClient.post('/api/cart/add', { product_id: productId, quantity });
  } catch (error) {
    throw error;
  }
};

export const getCart = async (): Promise<CartItem[]> => {
  try {
    const response = await httpClient.get<any>('/api/cart/');
    
    const cart = response;
    if (!cart || !cart.items) {
      return [];
    }
    
    const transformedItems = cart.items.map((item: any) => ({
      product: {
        id: item.product_id,
        title: item.product_title,
        price: item.product_price,
        image: item.product_image,
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
    await httpClient.put('/api/cart/update', undefined, { params: { product_id: productId, quantity } });
  } catch (error) {
    throw error;
  }
};

export const removeFromCart = async (productId: string): Promise<void> => {
  try {
    await httpClient.delete(`/api/cart/${productId}`);
  } catch (error) {
    throw error;
  }
};

export const checkoutCart = async (): Promise<{ order_id: string; order_number: string; total: number; status: string }> => {
  try {
    const response = await httpClient.post<{ data: { order_id: string; order_number: string; total: number; status: string } }>('/api/cart/checkout');
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const createLocalUserMessage = createUserMessage;