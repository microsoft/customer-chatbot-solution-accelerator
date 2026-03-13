import React from 'react';
import { Text } from '@fluentui/react-components';
import { ProductGrid } from '@/components/ProductGrid';
import { Product } from '@/lib/types';

interface MainContentProps {
  children?: React.ReactNode;
  products?: Product[];
  isLoading?: boolean;
  onAddToCart?: (product: Product) => void;
}

export const MainContent: React.FC<MainContentProps> = ({
  children,
  products = [],
  isLoading = false,
  onAddToCart
}) => {
  return (
    <div className="h-full flex flex-col">
      {/* Products Header - Products title and result count */}
      <div className="p-4 pt-6">
        <div className="flex items-center justify-between">
          <Text size={500} weight="semibold">Products</Text>
          <Text size={300} className="text-muted-foreground">
            Showing {products.length} results
          </Text>
        </div>
      </div>
      
      {/* Products Content */}
      <div className="flex-1 overflow-y-auto p-4 pt-0">
        <div className="max-w-full">
          {children || (
            <ProductGrid
              products={products}
              isLoading={isLoading}
              onAddToCart={onAddToCart || (() => {})}
            />
          )}
        </div>
      </div>
    </div>
  );
};
