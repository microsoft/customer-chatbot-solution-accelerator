import axios from 'axios';

// Global token store for Entra ID tokens
let currentIdToken: string | null = null;

// Function to set the current ID token (called by auth context)
export const setCurrentIdToken = (token: string | null) => {
  currentIdToken = token;
};

// API Configuration - Runtime configuration support
declare global {
  interface Window {
    APP_CONFIG?: {
      API_BASE_URL: string;
      ENVIRONMENT: string;
      AZURE_CLIENT_ID?: string;
      AZURE_TENANT_ID?: string;
      AZURE_AUTHORITY?: string;
      REDIRECT_URI?: string;
    };
  }
}

// Get API URL from runtime config (production) or Vite env (development)
const getApiBaseUrl = (): string => {
  let baseUrl: string;
  
  // Check if we're in development mode (Vite dev server)
  const isDevelopment = import.meta.env.DEV;
  
  if (isDevelopment) {
    // In development, prioritize Vite env variable
    baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    console.log('Development mode - Using Vite env API URL:', baseUrl);
  } else if (typeof window !== 'undefined' && window.APP_CONFIG?.API_BASE_URL) {
    // In production, use runtime config
    baseUrl = window.APP_CONFIG.API_BASE_URL;
    console.log('Production mode - Using runtime config API URL:', baseUrl);
  } else {
    // Fallback to Vite env
    baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    console.log('Fallback - Using Vite env API URL:', baseUrl);
  }
  
  // Ensure URL is properly formatted
  // Remove trailing slash if present, then add it back
  baseUrl = baseUrl.replace(/\/$/, '');
  
  // Force HTTPS in production (when not localhost)
  if (baseUrl.includes('azurewebsites.net') && !baseUrl.startsWith('https://')) {
    baseUrl = baseUrl.replace('http://', 'https://');
    console.log('Forced HTTPS for production URL:', baseUrl);
  }
  
  return baseUrl;
};

const API_BASE_URL = getApiBaseUrl();
console.log('Final API Base URL:', API_BASE_URL);

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 20000, // Increased to 20 seconds for chat operations
});

// Add request interceptor to include auth token
api.interceptors.request.use((config) => {
  // Check if we're in local development mode
  // In production, use runtime config; in development, use Vite env
  const getClientId = () => {
    if (typeof window !== 'undefined' && window.APP_CONFIG?.AZURE_CLIENT_ID) {
      return window.APP_CONFIG.AZURE_CLIENT_ID;
    }
    return import.meta.env.VITE_AZURE_CLIENT_ID;
  };
  
  const clientId = getClientId();
  const isLocalDev = !clientId || 
                     clientId === 'local-dev' ||
                     clientId === 'your-client-id-here' ||
                     clientId === '';
  
  // Only add token if no Authorization header is already set
  if (!config.headers.Authorization) {
    if (isLocalDev) {
      // Local dev mode - use mock token
      const token = localStorage.getItem('mock_token');
      console.log('API Request:', config.method?.toUpperCase(), config.url, 'Mock Token:', !!token);
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } else {
      // Entra ID mode - use the stored ID token
      console.log('API Request:', config.method?.toUpperCase(), config.url, 'Entra ID Token:', !!currentIdToken);
      if (currentIdToken) {
        config.headers.Authorization = `Bearer ${currentIdToken}`;
      }
    }
  } else {
    console.log('API Request:', config.method?.toUpperCase(), config.url, 'Auth Header already set:', !!config.headers.Authorization);
  }
  return config;
});

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

export interface CartItem {
  product: Product;
  quantity: number;
}

// API Functions
export const getProducts = async (): Promise<Product[]> => {
  try {
    console.log('Fetching products from API...');
    console.log('API Base URL:', API_BASE_URL);
    console.log('Full request URL:', `${API_BASE_URL}/api/products`);
    
    const response = await api.get('/api/products/');
    console.log('Products fetched successfully:', response.data);
    
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
    
    console.log('Transformed data:', transformedData);
    return transformedData;
  } catch (error: any) {
    console.error('Error fetching products:', error);
    console.error('Error details:', {
      message: error.message,
      code: error.code,
      status: error.response?.status,
      statusText: error.response?.statusText,
      url: error.config?.url
    });
    
    // Only fall back to mock data if it's a network error or API is completely down
    if (error.code === 'ERR_NETWORK' || error.message.includes('Mixed Content')) {
      console.log('Network error detected, falling back to mock data');
      return getMockProducts();
    }
    
    // For other errors, re-throw to let the UI handle it
    throw error;
  }
};

// Mock data as a separate function for better organization
const getMockProducts = (): Product[] => [
  {
    id: "1",
    title: "Modern Minimalist Desk Lamp",
    price: 89.99,
    originalPrice: 129.99,
    rating: 4.5,
    reviewCount: 128,
    image: "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=400&h=400&fit=crop",
    category: "Lighting",
    inStock: true,
    description: "Sleek LED desk lamp with adjustable brightness and USB charging port"
  },
  {
    id: "2",
    title: "Ergonomic Office Chair",
    price: 299.99,
    rating: 4.8,
    reviewCount: 89,
    image: "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=400&h=400&fit=crop",
    category: "Furniture",
    inStock: true,
    description: "Premium ergonomic chair with lumbar support and adjustable height"
  }
];

export const getChatHistory = async (): Promise<ChatMessage[]> => {
  try {
    const response = await api.get('/api/chat/history');
    return response.data;
  } catch (error) {
    console.error('Error fetching chat history:', error);
    return [];
  }
};

export const sendMessageToChat = async (message: string, sessionId?: string): Promise<ChatMessage> => {
  try {
    const payload: any = { content: message };
    if (sessionId) {
      payload.session_id = sessionId;
    }
    const response = await api.post('/api/chat/message', payload);
    return response.data;
  } catch (error) {
    console.error('Error sending message:', error);
    throw error;
  }
};

export const createNewChatSession = async (): Promise<{ session_id: string; session_name: string; created_at: string }> => {
  try {
    const response = await api.post('/api/chat/sessions/new');
    return response.data.data;
  } catch (error) {
    console.error('Error creating new chat session:', error);
    throw error;
  }
};


export const addToCart = async (productId: string, quantity: number = 1): Promise<void> => {
  try {
    console.log('Adding to cart:', { product_id: productId, quantity });
    const response = await api.post('/api/cart/add', { product_id: productId, quantity });
    console.log('Add to cart response:', response.data);
  } catch (error) {
    console.error('Error adding to cart:', error);
    console.error('Error details:', error.response?.data);
    throw error;
  }
};

export const getCart = async (): Promise<CartItem[]> => {
  try {
    const response = await api.get('/api/cart/');
    console.log('Cart response:', response.data);
    
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
    
    console.log('Transformed cart items:', transformedItems);
    return transformedItems;
  } catch (error) {
    console.error('Error fetching cart:', error);
    return [];
  }
};

export const updateCartItem = async (productId: string, quantity: number): Promise<void> => {
  try {
    console.log('Updating cart item:', { productId, quantity });
    await api.put(`/api/cart/update?product_id=${productId}&quantity=${quantity}`);
  } catch (error) {
    console.error('Error updating cart item:', error);
    throw error;
  }
};

export const removeFromCart = async (productId: string): Promise<void> => {
  try {
    console.log('Removing from cart:', { productId });
    await api.delete(`/api/cart/${productId}`);
  } catch (error) {
    console.error('Error removing from cart:', error);
    throw error;
  }
};

export const checkoutCart = async (): Promise<{ order_id: string; order_number: string; total: number; status: string }> => {
  try {
    console.log('Checking out cart...');
    const response = await api.post('/api/cart/checkout');
    console.log('Checkout response:', response.data);
    return response.data.data;
  } catch (error) {
    console.error('Error during checkout:', error);
    throw error;
  }
};