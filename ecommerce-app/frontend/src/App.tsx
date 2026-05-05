import { AppHeader } from '@/components/Layout/AppHeader';
import { MainContent } from '@/components/Layout/MainContent';
import { ProductGrid } from '@/components/ProductGrid';
import { addToCart, checkoutCart, getCart, removeFromCart, updateCartItem, getProducts } from '@/lib/api';
import { filterProducts, sortProducts } from '@/lib/data';
import { Product, SortBy } from '@/lib/types';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useMemo, useState } from 'react';
import { toast } from 'sonner';

function App() {
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

  const isLoading = productsLoading;

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

  const handleAddToCart = (product: Product) => {
    addToCartMutation.mutate({ productId: product.id, quantity: 1 });
  };

  const handleUpdateCartQuantity = (productId: string, quantity: number) => {
    if (quantity === 0) {
      handleRemoveFromCart(productId);
      return;
    }

    updateCartItem(productId, quantity).then(() => {
      refetchCart();
      toast.success('Cart updated');
    }).catch(() => {
      toast.error('Failed to update cart');
    });
  };

  const handleRemoveFromCart = (productId: string) => {
    removeFromCart(productId).then(() => {
      refetchCart();
      toast.success('Item removed from cart');
    }).catch(() => {
      toast.error('Failed to remove item from cart');
    });
  };

  const handleCheckout = () => {
    if (cartItems.length === 0) {
      toast.error('Your cart is empty');
      return;
    }

    checkoutCart().then((orderData) => {
      refetchCart();
      toast.success(`Order #${orderData.order_number} created successfully! Total: $${orderData.total.toFixed(2)}`);
    }).catch(() => {
      toast.error('Failed to complete checkout');
    });
  };

  const handleCartOpen = () => {
    refetchCart();
  };

  return (
    <div className="h-screen bg-background overflow-hidden">
      <AppHeader
        cartItems={cartItems}
        onUpdateQuantity={handleUpdateCartQuantity}
        onRemoveItem={handleRemoveFromCart}
        onCheckout={handleCheckout}
        onCartOpen={handleCartOpen}
      />

      <div className="flex h-[calc(100vh-4rem)]">
        <div className="flex-1">
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
                    type="button"
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
      </div>
    </div>
  );
}

export default App;
