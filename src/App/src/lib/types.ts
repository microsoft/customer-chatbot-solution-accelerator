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
  description?: string;
}

export interface Order {
  orderNumber: string;
  status: string;
  orderDate: string;
  items: OrderItem[];
  subtotal: number;
  tax: number;
  total: number;
  shippingAddress: string;
}

export interface OrderItem {
  name: string;
  quantity: number;
  unitPrice: number;
  totalPrice: number;
}

export interface CartItem {
  product: Product;
  quantity: number;
}

export interface ChatMessage {
  id: string;
  content: string;
  sender: 'user' | 'assistant' | 'error' | 'chart';
  timestamp: string;
  typing?: boolean;
  recommendedProducts?: Product[];
  parsedOrders?: Order[];
  parsedProducts?: Product[];
}

export interface FilterOptions {
  category: string;
  minPrice: number;
  maxPrice: number;
  minRating: number;
  inStockOnly: boolean;
}

export interface SortOption {
  value: string;
  label: string;
}

export type SortBy = 'name' | 'price-asc' | 'price-desc' | 'rating' | 'newest';

export interface AppState {
  products: Product[];
  filteredProducts: Product[];
  cart: CartItem[];
  chatMessages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  searchQuery: string;
  filters: FilterOptions;
  sortBy: SortBy;
  isChatOpen: boolean;
  isTyping: boolean;
}