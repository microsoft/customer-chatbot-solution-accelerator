import { Product, ChatMessage, SortBy } from './types';

export const mockProducts: Product[] = [
  {
    id: '1',
    title: 'Modern Minimalist Desk Lamp',
    price: 89.99,
    originalPrice: 129.99,
    rating: 4.5,
    reviewCount: 128,
    image: 'https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=400&h=400&fit=crop',
    category: 'Lighting',
    inStock: true,
    description: 'Sleek LED desk lamp with adjustable brightness and USB charging port'
  },
  {
    id: '2',
    title: 'Ergonomic Office Chair',
    price: 299.99,
    rating: 4.8,
    reviewCount: 89,
    image: 'https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=400&h=400&fit=crop',
    category: 'Furniture',
    inStock: true,
    description: 'Premium ergonomic chair with lumbar support and adjustable height'
  },
  {
    id: '3',
    title: 'Wireless Noise-Canceling Headphones',
    price: 179.99,
    originalPrice: 249.99,
    rating: 4.7,
    reviewCount: 456,
    image: 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&h=400&fit=crop',
    category: 'Electronics',
    inStock: true,
    description: 'Premium wireless headphones with active noise cancellation'
  },
  {
    id: '4',
    title: 'Stainless Steel Water Bottle',
    price: 29.99,
    originalPrice: 39.99,
    rating: 4.6,
    reviewCount: 142,
    image: 'https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=400&h=400&fit=crop',
    category: 'Kitchen',
    inStock: true,
    description: 'Insulated stainless steel water bottle keeps drinks cold for 24hrs or hot for 12hrs'
  },
  {
    id: '5',
    title: 'Smart Fitness Watch',
    price: 199.99,
    rating: 4.6,
    reviewCount: 234,
    image: 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&h=400&fit=crop',
    category: 'Electronics',
    inStock: false,
    description: 'Advanced fitness tracking with heart rate monitoring and GPS'
  },
  {
    id: '6',
    title: 'Succulent Plant Collection',
    price: 49.99,
    rating: 4.4,
    reviewCount: 91,
    image: 'https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=400&h=400&fit=crop',
    category: 'Plants',
    inStock: true,
    description: 'Set of 3 low-maintenance succulent plants in decorative pots'
  },
  {
    id: '7',
    title: 'Premium Leather Wallet',
    price: 79.99,
    originalPrice: 99.99,
    rating: 4.9,
    reviewCount: 156,
    image: 'https://images.unsplash.com/photo-1627123424574-724758594e93?w=400&h=400&fit=crop',
    category: 'Accessories',
    inStock: true,
    description: 'Handcrafted genuine leather wallet with RFID blocking technology'
  },
  {
    id: '8',
    title: 'Bamboo Cutting Board Set',
    price: 59.99,
    rating: 4.2,
    reviewCount: 78,
    image: 'https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=400&h=400&fit=crop',
    category: 'Kitchen',
    inStock: true,
    description: 'Sustainable bamboo cutting boards in 3 different sizes'
  },
  {
    id: '9',
    title: 'Wireless Bluetooth Speaker',
    price: 69.99,
    originalPrice: 89.99,
    rating: 4.3,
    reviewCount: 187,
    image: 'https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=400&h=400&fit=crop',
    category: 'Electronics',
    inStock: true,
    description: 'Portable waterproof speaker with rich bass and 12-hour battery life'
  }
];

export const initialChatMessages: ChatMessage[] = [
  {
    id: '1',
    content: "Hi there! I'm Cora, your personal shopping assistant. I'm here to help you discover the best deals, find exactly what you're looking for, and make your shopping experience smooth and enjoyable. Just tell me what you need—I've got you covered!",
    sender: 'assistant',
    timestamp: new Date(Date.now() - 300000) // 5 minutes ago
  }
];

export const sortOptions = [
  { value: 'name', label: 'Name (A-Z)' },
  { value: 'price-asc', label: 'Price: Low to High' },
  { value: 'price-desc', label: 'Price: High to Low' },
  { value: 'rating', label: 'Highest Rated' },
  { value: 'newest', label: 'Newest First' }
];

export const categories = ['All', 'Electronics', 'Furniture', 'Kitchen', 'Lighting', 'Plants', 'Accessories'];

export function sortProducts(products: Product[], sortBy: SortBy): Product[] {
  return [...products].sort((a, b) => {
    switch (sortBy) {
      case 'name':
        return a.title.localeCompare(b.title);
      case 'price-asc':
        return a.price - b.price;
      case 'price-desc':
        return b.price - a.price;
      case 'rating':
        return b.rating - a.rating;
      case 'newest':
        return b.id.localeCompare(a.id); // Assuming higher IDs are newer
      default:
        return 0;
    }
  });
}

export function filterProducts(products: Product[], searchQuery: string, filters: any): Product[] {
  return products.filter(product => {
    const matchesSearch = product.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         product.category.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesCategory = filters.category === 'All' || product.category === filters.category;
    const matchesPrice = product.price >= filters.minPrice && product.price <= filters.maxPrice;
    const matchesRating = product.rating >= filters.minRating;
    const matchesStock = !filters.inStockOnly || product.inStock;

    return matchesSearch && matchesCategory && matchesPrice && matchesRating && matchesStock;
  });
}