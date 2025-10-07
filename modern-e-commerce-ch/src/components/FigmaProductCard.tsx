import React, { memo } from 'react';
import { Product } from '@/lib/types';

interface FigmaProductCardProps {
  product: Product;
  onAddToCart?: (product: Product) => void;
}

export const FigmaProductCard = memo(({ product, onAddToCart }: FigmaProductCardProps) => {
  return (
    <div className="group relative space-y-2">
      {/* Product Image */}
      <div className="relative aspect-square overflow-hidden rounded-lg">
        <img
          src={product.image}
          alt={`${product.title} - ${product.category}`}
          className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
          loading="lazy"
          decoding="async"
        />
      </div>
      
      <div className="space-y-1">
        {/* Product Name */}
        <h3 className="font-medium text-foreground text-sm leading-tight group-hover:text-primary transition-colors">
          {product.title}
        </h3>
        
        {/* Product Description */}
        <p className="text-xs text-muted-foreground leading-relaxed">
          {product.description || `${product.category.toLowerCase()}, modern, clean`}
        </p>
        
        {/* Price */}
        <div className="flex items-center justify-between">
          <span className="font-semibold text-sm text-foreground" aria-label={`Price: ${product.price.toFixed(2)} USD`}>
            {product.price.toFixed(2)} USD
          </span>
        </div>
      </div>
    </div>
  );
});
