import React from 'react';
import { ShoppingCart, Heart } from '@phosphor-icons/react';
import { Button } from '@/components/ui/button';
import { Product } from '@/lib/types';

interface ChatProductCardProps {
  product: Product;
  onAddToCart?: (product: Product) => void;
}

export const ChatProductCard: React.FC<ChatProductCardProps> = ({
  product,
  onAddToCart
}) => {
  return (
    <div className="flex items-center gap-4 p-4 bg-card border">
      {/* Color Swatch / Product Image */}
      <div className="w-16 h-16 overflow-hidden flex-shrink-0">
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
        <h3 className="font-bold text-lg text-foreground">
          {product.title}
        </h3>
        <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
          {product.description}
        </p>
        <span className="text-sm text-muted-foreground mt-2 block">
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
