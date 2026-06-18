import { MainContent } from '@/components/Layout/MainContent';
import { ProductGrid } from '@/components/ProductGrid';
import { addToCart, getProducts } from '@/lib/api';
import { filterProducts, sortProducts } from '@/lib/data';
import { Product, SortBy } from '@/lib/types';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useMemo, useState } from 'react';
import { toast } from 'sonner';

export function EcommerceApp() {
  const { data: products = [], isLoading: productsLoading, error: productsError } = useQuery({
    queryKey: ['products'],
    queryFn: getProducts,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });

  const addToCartMutation = useMutation({
    mutationFn: ({ productId, quantity }: { productId: string; quantity: number }) =>
      addToCart(productId, quantity),
    onSuccess: () => {
      toast.success('Product added to cart!');
    },
    onError: () => {
      toast.error('Failed to add product to cart');
    },
  });

  const [searchQuery] = useState('');
  const [selectedCategory] = useState('All');
  const [sortBy] = useState<SortBy>('name');

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

  const handleAddToCart = (product: Product) => {
    addToCartMutation.mutate({ productId: product.id, quantity: 1 });
  };

  return (
    <MainContent products={filteredProducts} isLoading={productsLoading} onAddToCart={handleAddToCart}>
      {productsError ? (
        <div className="flex items-center justify-center h-full p-8">
          <div className="max-w-md text-center">
            <h2 className="text-2xl font-bold text-foreground mb-2">Failed to Load Products</h2>
            <p className="text-muted-foreground mb-4">
              {productsError instanceof Error ? productsError.message : 'Unable to connect to the backend API'}
            </p>
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg"
            >
              Retry
            </button>
          </div>
        </div>
      ) : (
        <ProductGrid products={filteredProducts} isLoading={productsLoading} onAddToCart={handleAddToCart} />
      )}
    </MainContent>
  );
}
