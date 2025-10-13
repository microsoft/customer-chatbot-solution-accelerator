import React, { useState, useEffect, useMemo } from 'react';
import { ChatCircle, List } from '@phosphor-icons/react';
import { Button } from '@/components/ui/button';
import { useIsMobile } from '@/hooks/use-mobile';
import { ProductCard } from '@/components/ProductCard';
import { ProductCardSkeleton, ProductGridSkeleton } from '@/components/ProductCardSkeleton';
import { ProductFilters } from '@/components/ProductFilters';
import { ChatPanel } from '@/components/ChatPanel';
import { CartDrawer } from '@/components/CartDrawer';
import { LoginButton } from '@/components/LoginButton';
import { ThemeToggle } from '@/components/ThemeToggle';
import { AppShell } from '@/components/Layout/AppShell';
import { AppHeader } from '@/components/Layout/AppHeader';
import { MainContent } from '@/components/Layout/MainContent';
import { ChatSidebar } from '@/components/Layout/ChatSidebar';
import { ProductGrid } from '@/components/ProductGrid';
import { Product, CartItem, ChatMessage, SortBy } from '@/lib/types';
import { mockProducts, initialChatMessages, sortProducts, filterProducts } from '@/lib/data';
import { toast } from 'sonner';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getProducts, getChatHistory, sendMessageToChat, createNewChatSession, addToCart, getCart, updateCartItem, removeFromCart, checkoutCart } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';

function App() {
  const isMobile = useIsMobile();
  const queryClient = useQueryClient();
  const { isAuthenticated, user } = useAuth();
  
  // API Queries
  const { data: products = mockProducts, isLoading: productsLoading, error: productsError } = useQuery({
    queryKey: ['products'],
    queryFn: getProducts,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
  });

  // Debug logging
  console.log('Products query state:', { products, productsLoading, productsError });
  console.log('Products length:', products?.length);
  console.log('Is loading:', productsLoading);

  // Manual test of API using proper configuration
  useEffect(() => {
    const testAPI = async () => {
      try {
        console.log('Testing API with proper configuration...');
        // Use the same API configuration as the rest of the app
        const apiUrl = window.APP_CONFIG?.API_BASE_URL || import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
        const fullUrl = `${apiUrl}/api/products`;
        console.log('Testing API URL:', fullUrl);
        
        const response = await fetch(fullUrl);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log('Direct API test result:', data);
      } catch (error) {
        console.error('Direct API test error:', error);
      }
    };
    testAPI();
  }, []);

  const { data: cartItems = [], refetch: refetchCart } = useQuery({
    queryKey: ['cart'],
    queryFn: getCart,
  });

  // Debug cart loading
  console.log('Cart items from API:', cartItems);
  console.log('Cart items length:', cartItems?.length);

  const { data: chatMessages = initialChatMessages, refetch: refetchChat } = useQuery({
    queryKey: ['chat'],
    queryFn: getChatHistory,
  });

  // Local state
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [sortBy, setSortBy] = useState<SortBy>('name');
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [isCartOpen, setIsCartOpen] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);

  const isLoading = productsLoading;

  // Filter and sort products
  const filteredProducts = useMemo(() => {
    const filters = {
      category: selectedCategory,
      minPrice: 0,
      maxPrice: 1000,
      minRating: 0,
      inStockOnly: false
    };
    
    const filtered = filterProducts(products, searchQuery, filters);
    return sortProducts(filtered, sortBy);
  }, [products, searchQuery, selectedCategory, sortBy]);

  // Cart mutations
  const addToCartMutation = useMutation({
    mutationFn: ({ productId, quantity }: { productId: string; quantity: number }) => 
      addToCart(productId, quantity),
    onSuccess: () => {
      refetchCart();
      toast.success('Product added to cart!');
    },
    onError: (error) => {
      toast.error('Failed to add product to cart');
      console.error('Add to cart error:', error);
    },
  });

  // Cart functions
  const handleAddToCart = (product: Product) => {
    addToCartMutation.mutate({ productId: product.id, quantity: 1 });
  };

  const handleUpdateCartQuantity = (productId: string, quantity: number) => {
    if (quantity === 0) {
      handleRemoveFromCart(productId);
      return;
    }
    
    // Update cart via API
    updateCartItem(productId, quantity).then(() => {
      refetchCart();
      toast.success('Cart updated');
    }).catch((error) => {
      console.error('Error updating cart:', error);
      toast.error('Failed to update cart');
    });
  };

  const handleRemoveFromCart = (productId: string) => {
    // Remove from cart via API
    removeFromCart(productId).then(() => {
      refetchCart();
      toast.success('Item removed from cart');
    }).catch((error) => {
      console.error('Error removing from cart:', error);
      toast.error('Failed to remove item from cart');
    });
  };

  const handleCheckout = () => {
    if (cartItems.length === 0) {
      toast.error('Your cart is empty');
      return;
    }

    checkoutCart().then((orderData) => {
      refetchCart(); // Refresh cart to show it's empty
      toast.success(`Order #${orderData.order_number} created successfully! Total: $${orderData.total.toFixed(2)}`);
    }).catch((error) => {
      console.error('Error during checkout:', error);
      toast.error('Failed to complete checkout');
    });
  };

  // Chat mutations
  const sendMessageMutation = useMutation({
    mutationFn: ({ message, sessionId }: { message: string; sessionId?: string }) => 
      sendMessageToChat(message, sessionId),
    onSuccess: (newMessage) => {
      queryClient.setQueryData(['chat'], (old: ChatMessage[] = []) => [...old, newMessage]);
      setIsTyping(false);
    },
    onError: (error) => {
      toast.error('Failed to send message');
      console.error('Send message error:', error);
      setIsTyping(false);
    },
  });

  const createNewSessionMutation = useMutation({
    mutationFn: createNewChatSession,
    onSuccess: (sessionData) => {
      setCurrentSessionId(sessionData.session_id);
      queryClient.setQueryData(['chat'], []);
      toast.success(`New chat started: ${sessionData.session_name}`);
    },
    onError: (error) => {
      toast.error('Failed to create new chat session');
      console.error('Create new session error:', error);
    },
  });


  // Chat functions
  const handleSendMessage = async (content: string) => {
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      content,
      sender: 'user',
      timestamp: new Date()
    };

    // Add user message immediately
    queryClient.setQueryData(['chat'], (old: ChatMessage[] = []) => [...old, userMessage]);
    setIsTyping(true);
    
    // Send to API with current session ID
    sendMessageMutation.mutate({ message: content, sessionId: currentSessionId || undefined });
  };

  const handleNewChat = () => {
    // Create a new chat session
    createNewSessionMutation.mutate();
  };

  const toggleChat = () => {
    setIsChatOpen(!isChatOpen);
  };

  return (
    <div className="h-screen bg-background overflow-hidden">
      {/* Top Header */}
      <AppHeader
        isChatOpen={isChatOpen}
        cartItems={cartItems}
        onUpdateQuantity={handleUpdateCartQuantity}
        onRemoveItem={handleRemoveFromCart}
        onCheckout={handleCheckout}
      />
      
      <div className="flex h-[calc(100vh-4rem)]">
        {/* Products Panel - responsive width based on chat state */}
        <div className={`flex-1 transition-all duration-300 ease-in-out ${isChatOpen ? 'mr-0' : ''}`}>
          <MainContent
            products={filteredProducts}
            isLoading={isLoading}
            onAddToCart={handleAddToCart}
          >
            <ProductGrid
              products={filteredProducts}
              isLoading={isLoading}
              onAddToCart={handleAddToCart}
            />
          </MainContent>
        </div>
        
        {/* Chat Sidebar - Coral UI Panel */}
        <ChatSidebar
          isOpen={isChatOpen}
          onClose={() => setIsChatOpen(false)}
          messages={chatMessages}
          onSendMessage={handleSendMessage}
          onNewChat={handleNewChat}
          isTyping={isTyping}
          onAddToCart={handleAddToCart}
        />
      </div>
    </div>
  );
}

export default App;