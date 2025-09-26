import React from 'react';
import { Text } from '@fluentui/react-components';
import { ProductFilters } from '@/components/ProductFilters';
import { ProductGrid } from '@/components/ProductGrid';
import { Product, SortBy } from '@/lib/types';

interface MainContentProps {
  children?: React.ReactNode;
  // Product-related props
  products?: Product[];
  isLoading?: boolean;
  searchQuery?: string;
  onSearchChange?: (query: string) => void;
  sortBy?: SortBy;
  onSortChange?: (sort: SortBy) => void;
  selectedCategory?: string;
  onCategoryChange?: (category: string) => void;
  onAddToCart?: (product: Product) => void;
}

export const MainContent: React.FC<MainContentProps> = ({
  children,
  products = [],
  isLoading = false,
  searchQuery = '',
  onSearchChange,
  sortBy = 'name',
  onSortChange,
  selectedCategory = 'All',
  onCategoryChange,
  onAddToCart
}) => {
  return (
    <div className="h-full flex flex-col">
      {/* Products Header */}
      <div className="border-b p-4 pt-6">
        <div className="flex items-center justify-between mb-4">
          <Text size={500} weight="semibold">Products</Text>
          <Text size={300} className="text-muted-foreground">
            Showing {products.length} results
          </Text>
        </div>
        <ProductFilters
          searchQuery={searchQuery}
          onSearchChange={onSearchChange || (() => {})}
          sortBy={sortBy}
          onSortChange={onSortChange || (() => {})}
          selectedCategory={selectedCategory}
          onCategoryChange={onCategoryChange || (() => {})}
          resultCount={products.length}
          isLoading={isLoading}
        />
      </div>
      
      {/* Products Content */}
      <div className="flex-1 overflow-auto p-4">
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
