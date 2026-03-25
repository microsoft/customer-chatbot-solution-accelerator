import { Button } from '@/components/ui/button';
import { Product } from '@/lib/types';
import { Heart, ShoppingCart } from '@phosphor-icons/react';
import React from 'react';

interface ChatProductCardProps {
  product: Product;
  onAddToCart?: (product: Product) => void;
}

export const ChatProductCard: React.FC<ChatProductCardProps> = ({
  product,
  onAddToCart
}) => {
  return (
    <div className="flex items-center gap-3 p-3 bg-card border rounded-lg" style={{ overflowWrap: 'normal', wordBreak: 'normal' }}>
      {/* Color Swatch / Product Image */}
      <div className="w-12 h-12 overflow-hidden flex-shrink-0 rounded">
        <img
          src={product.image}
          alt={product.title}
          className="w-full h-full object-cover"
          onError={(e) => {
            // Fallback to a color placeholder if image fails to load
            const target = e.target as HTMLImageElement;
            target.style.display = 'none';
            target.parentElement!.style.backgroundColor = '#e5e7eb';
          }}
        />
      </div>
      
      {/* Product Details */}
      <div className="flex-1 min-w-0">
        <h3 className="font-semibold text-sm text-foreground truncate">
          {product.title}
        </h3>
        <p className="text-xs text-muted-foreground mt-0.5 line-clamp-1">
          {product.description}
        </p>
        <span className="text-xs font-medium text-foreground mt-1 block">
          ${product.price.toFixed(2)} USD
        </span>
      </div>
      
      {/* Action Icons */}
      <div className="flex gap-1">
        <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
          <Heart className="h-4 w-4" />
        </Button>
        {onAddToCart && (
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0"
            onClick={() => onAddToCart(product)}
            disabled={!product.inStock}
          >
            <ShoppingCart className="h-4 w-4" />
          </Button>
        )}
      </div>
    </div>
  );
};
