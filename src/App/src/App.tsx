import { AppHeader } from '@/components/Layout/AppHeader';
import { ChatSidebar } from '@/components/Layout/ChatSidebar';
import eventBus from '@/components/Layout/eventbus';
import { MainContent } from '@/components/Layout/MainContent';
import { ProductGrid } from '@/components/ProductGrid';
import { useAuth } from '@/contexts/AuthContext';
import { useChatApi } from '@/hooks/useChatApi';
import { useChatHistorySave } from '@/hooks/useChatHistorySave';
import {
    addToCart,
    checkoutCart,
    getCart,
    getProducts,
    removeFromCart,
    updateCartItem,
} from '@/lib/api';
import { filterProducts, sortProducts } from '@/lib/data';
import { Product, SortBy } from '@/lib/types';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import {
    selectChatMessages,
    selectCurrentSessionId,
    selectGeneratingResponse,
    selectIsChatOpen,
    selectIsFetchingConvMessages,
} from '@/store/selectors';
import { setChatOpen } from '@/store/slices/appSlice';
import { fetchChatHistory } from '@/store/slices/chatHistorySlice';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { toast } from 'sonner';

function App() {
  const dispatch = useAppDispatch();
  const { isAuthenticated } = useAuth();
  const { sendMessage, startNewConversation, fetchMessages } = useChatApi();

  const currentSessionId = useAppSelector(selectCurrentSessionId);
  const chatMessages = useAppSelector(selectChatMessages);
  const generatingResponse = useAppSelector(selectGeneratingResponse);
  const isChatOpen = useAppSelector(selectIsChatOpen);
  const isFetchingConvMessages = useAppSelector(selectIsFetchingConvMessages);

  useChatHistorySave(currentSessionId);

  const { data: products = [], isLoading: productsLoading, error: productsError } = useQuery({
    queryKey: ['products'],
    queryFn: getProducts,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });

  const { data: cartItems = [], refetch: refetchCart } = useQuery({
    queryKey: ['cart'],
    queryFn: getCart,
    enabled: false,
    staleTime: 30 * 1000,
    refetchOnWindowFocus: false,
    refetchOnMount: false,
  });

  const [searchQuery] = useState('');
  const [selectedCategory] = useState('All');
  const [sortBy] = useState<SortBy>('name');

  useEffect(() => {
    const handlePanelChange = (panelType: string | null) => {
      dispatch(setChatOpen(panelType === 'first'));
    };

    eventBus.on('setActivePanel', handlePanelChange);

    return () => {
      eventBus.off('setActivePanel', handlePanelChange);
    };
  }, [dispatch]);

  useEffect(() => {
    if (isAuthenticated) {
      dispatch(fetchChatHistory());
    }
  }, [dispatch, isAuthenticated]);

  useEffect(() => {
    if (isAuthenticated && currentSessionId) {
      fetchMessages(currentSessionId).catch(() => {
        toast.error('Failed to load chat history');
      });
    }
  }, [isAuthenticated, currentSessionId, fetchMessages]);

  const isLoading = productsLoading;

  const filteredProducts = useMemo(() => {
    const filters = {
      category: selectedCategory,
      minPrice: 0,
      maxPrice: 1000,
      minRating: 0,
      inStockOnly: false,
    };

    const filtered = filterProducts(products, searchQuery, filters);
    return sortProducts(filtered, sortBy);
  }, [products, searchQuery, selectedCategory, sortBy]);

  const addToCartMutation = useMutation({
    mutationFn: ({ productId, quantity }: { productId: string; quantity: number }) =>
      addToCart(productId, quantity),
    onSuccess: () => {
      refetchCart();
      toast.success('Product added to cart!');
    },
    onError: () => {
      toast.error('Failed to add product to cart');
    },
  });

  const handleAddToCart = useCallback((product: Product) => {
    addToCartMutation.mutate({ productId: product.id, quantity: 1 });
  }, [addToCartMutation]);

  const handleUpdateCartQuantity = useCallback((productId: string, quantity: number) => {
    if (quantity === 0) {
      removeFromCart(productId)
        .then(() => {
          refetchCart();
          toast.success('Item removed from cart');
        })
        .catch(() => {
          toast.error('Failed to remove item from cart');
        });
      return;
    }

    updateCartItem(productId, quantity)
      .then(() => {
        refetchCart();
        toast.success('Cart updated');
      })
      .catch(() => {
        toast.error('Failed to update cart');
      });
  }, [refetchCart]);

  const handleRemoveFromCart = useCallback((productId: string) => {
    removeFromCart(productId)
      .then(() => {
        refetchCart();
        toast.success('Item removed from cart');
      })
      .catch(() => {
        toast.error('Failed to remove item from cart');
      });
  }, [refetchCart]);

  const handleCheckout = useCallback(() => {
    if (cartItems.length === 0) {
      toast.error('Your cart is empty');
      return;
    }

    checkoutCart()
      .then((orderData) => {
        refetchCart();
        toast.success(`Order #${orderData.order_number} created successfully! Total: $${orderData.total.toFixed(2)}`);
      })
      .catch(() => {
        toast.error('Failed to complete checkout');
      });
  }, [cartItems.length, refetchCart]);

  const handleSendMessage = useCallback(async (content: string) => {
    try {
      await sendMessage(content);
    } catch {
      toast.error('Failed to send message');
    }
  }, [sendMessage]);

  const handleNewChat = useCallback(async () => {
    try {
      const sessionId = await startNewConversation();
      await fetchMessages(sessionId);
      dispatch(setChatOpen(true));
    } catch {
      toast.error('Failed to create new chat session');
    }
  }, [dispatch, fetchMessages, startNewConversation]);

  const toggleChat = useCallback(() => {
    const newChatState = !isChatOpen;
    dispatch(setChatOpen(newChatState));

    if (newChatState) {
      eventBus.emit('setActivePanel', 'first');
      if (currentSessionId) {
        fetchMessages(currentSessionId).catch(() => {
          toast.error('Failed to refresh chat');
        });
      }
      return;
    }

    eventBus.emit('setActivePanel', null);
  }, [currentSessionId, dispatch, fetchMessages, isChatOpen]);

  const handleCartOpen = useCallback(() => {
    refetchCart();
  }, [refetchCart]);

  return (
    <div className="h-screen bg-background overflow-hidden">
      <AppHeader
        isChatOpen={isChatOpen}
        cartItems={cartItems}
        onUpdateQuantity={handleUpdateCartQuantity}
        onRemoveItem={handleRemoveFromCart}
        onCheckout={handleCheckout}
        onCartOpen={handleCartOpen}
        onChatToggle={toggleChat}
      />

      <div className="flex h-[calc(100vh-4rem)]">
        <div className={`flex-1 transition-all duration-300 ease-in-out ${isChatOpen ? 'mr-0' : ''}`}>
          <MainContent products={filteredProducts} isLoading={isLoading} onAddToCart={handleAddToCart}>
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
              <ProductGrid products={filteredProducts} isLoading={isLoading} onAddToCart={handleAddToCart} />
            )}
          </MainContent>
        </div>

        <ChatSidebar
          isOpen={isChatOpen}
          messages={chatMessages}
          onSendMessage={handleSendMessage}
          onNewChat={handleNewChat}
          isTyping={generatingResponse}
          isLoading={isFetchingConvMessages}
          onAddToCart={handleAddToCart}
        />
      </div>
    </div>
  );
}

export default App;
