import { AppHeader } from '@/components/Layout/AppHeader';
import { ChatSidebar } from '@/components/Layout/ChatSidebar';
import { MainContent } from '@/components/Layout/MainContent';
import { ProductGrid } from '@/components/ProductGrid';
import { useAuth } from '@/contexts/AuthContext';
import { useIsMobile } from '@/hooks/use-mobile';
import { addToCart, checkoutCart, clearCurrentSessionId, createNewChatSession, createTimestamp, getCart, getChatHistory, getCurrentSessionId, getProducts, removeFromCart, saveCurrentSessionId, sendMessageToChat, updateCartItem } from '@/lib/api';
import { filterProducts, sortProducts } from '@/lib/data';
import { ChatMessage, Product, SortBy } from '@/lib/types';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useMemo, useState } from 'react';
import { toast } from 'sonner';

function App() {
  const isMobile = useIsMobile();
  const queryClient = useQueryClient();
  const { isAuthenticated, user } = useAuth();
  
  // API Queries
  const { data: products = [], isLoading: productsLoading, error: productsError } = useQuery({
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
        const apiUrl = (window as any).__RUNTIME_CONFIG__?.VITE_API_BASE_URL || import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
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

  const [currentSessionId, setCurrentSessionId] = useState<string | null>(() => getCurrentSessionId());

  const { data: chatMessages = [], refetch: refetchChat, isLoading: chatLoading, isFetching: chatFetching } = useQuery({
    queryKey: ['chat', currentSessionId],
    queryFn: () => getChatHistory(currentSessionId || undefined),
    staleTime: 0,
    refetchOnMount: true,
  });

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [sortBy, setSortBy] = useState<SortBy>('name');
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [isCartOpen, setIsCartOpen] = useState(false);

  useEffect(() => {
    if (currentSessionId) {
      saveCurrentSessionId(currentSessionId);
    }
  }, [currentSessionId]);

  // Refetch chat when authentication completes
  useEffect(() => {
    if (isAuthenticated && currentSessionId) {
      refetchChat();
    }
  }, [isAuthenticated, currentSessionId, refetchChat]);

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
      queryClient.setQueryData(['chat', currentSessionId], (old: ChatMessage[] = []) => [...old, newMessage]);
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
      clearCurrentSessionId();
      setCurrentSessionId(sessionData.session_id);
      queryClient.setQueryData(['chat', sessionData.session_id], []);
      queryClient.invalidateQueries({ queryKey: ['chat'] });
      toast.success(`New chat started: ${sessionData.session_name}`);
    },
    onError: (error) => {
      toast.error('Failed to create new chat session');
      console.error('Create new session error:', error);
    },
  });


  // Chat functions
  const handleSendMessage = async (content: string) => {
    if (!currentSessionId) {
      try {
        const sessionData = await createNewChatSession();
        setCurrentSessionId(sessionData.session_id);
        saveCurrentSessionId(sessionData.session_id);
        
        const userMessage: ChatMessage = {
          id: `user-${Date.now()}`,
          content,
          sender: 'user',
          timestamp: createTimestamp()
        };
        
        queryClient.setQueryData(['chat', sessionData.session_id], [userMessage]);
        setIsTyping(true);
        sendMessageMutation.mutate({ message: content, sessionId: sessionData.session_id });
      } catch (error) {
        console.error('Failed to create session:', error);
        toast.error('Failed to start chat session');
      }
      return;
    }

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      content,
      sender: 'user',
      timestamp: createTimestamp()
    };

    queryClient.setQueryData(['chat', currentSessionId], (old: ChatMessage[] = []) => [...old, userMessage]);
    setIsTyping(true);
    
    sendMessageMutation.mutate({ message: content, sessionId: currentSessionId });
  };

  const handleNewChat = () => {
    createNewSessionMutation.mutate();
  };

  const toggleChat = () => {
    const newChatState = !isChatOpen;
    setIsChatOpen(newChatState);
    if (newChatState && currentSessionId) {
      refetchChat();
    }
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
            {productsError ? (
              <div className="flex items-center justify-center h-full p-8">
                <div className="max-w-md text-center">
                  <div className="text-red-600 text-6xl mb-4">⚠️</div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">Failed to Load Products</h2>
                  <p className="text-gray-600 mb-4">
                    {productsError instanceof Error ? productsError.message : 'Unable to connect to the backend API'}
                  </p>
                  <button
                    onClick={() => window.location.reload()}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  >
                    Retry
                  </button>
                </div>
              </div>
            ) : (
              <ProductGrid
                products={filteredProducts}
                isLoading={isLoading}
                onAddToCart={handleAddToCart}
              />
            )}
          </MainContent>
        </div>
        
        {/* Chat Sidebar - Coral UI Panel */}
        <ChatSidebar
          isOpen={isChatOpen}
          onClose={() => setIsChatOpen(false)}
          messages={chatMessages || []}
          onSendMessage={handleSendMessage}
          onNewChat={handleNewChat}
          isTyping={isTyping || chatLoading || chatFetching}
          onAddToCart={handleAddToCart}
        />
      </div>
    </div>
  );
}

export default App;