import { Product } from '@/lib/types';
import { PaintBucket20Regular } from '@fluentui/react-icons';
import React from 'react';

interface ChatProductCardProps {
  product: Product;
  onAddToCart?: (product: Product) => void;
}

export const ChatProductCard: React.FC<ChatProductCardProps> = ({
  product,
  onAddToCart
}) => {
  const hasImage = product.image && product.image.startsWith('http');

  return (
    <div className="flex gap-3 p-3 bg-card border rounded-lg hover:shadow-sm transition-shadow">
      <div className="w-16 h-16 flex-shrink-0 rounded-lg overflow-hidden bg-muted flex items-center justify-center">
        {hasImage ? (
          <img
            src={product.image}
            alt={product.title}
            className="w-full h-full object-cover"
            onError={(e) => {
              const target = e.target as HTMLImageElement;
              target.style.display = 'none';
              if (target.nextElementSibling) {
                (target.nextElementSibling as HTMLElement).style.display = 'flex';
              }
            }}
          />
        ) : null}
        <div className={`items-center justify-center ${hasImage ? 'hidden' : 'flex'}`}>
          <PaintBucket20Regular className="h-6 w-6 text-muted-foreground" />
        </div>
      </div>
      
      <div className="flex-1 min-w-0">
        <h4 className="font-medium text-sm text-foreground leading-tight">
          {product.title}
        </h4>
        {product.description && (
          <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">
            {product.description}
          </p>
        )}
        <div className="flex items-center gap-2 mt-1">
          <span className="text-sm font-semibold text-foreground">
            ${product.price?.toFixed(2) ?? '—'}
          </span>
          {product.originalPrice && product.originalPrice > product.price && (
            <span className="text-xs text-muted-foreground line-through">
              ${product.originalPrice.toFixed(2)}
            </span>
          )}
          {product.rating > 0 && (
            <span className="text-xs text-muted-foreground">
              ★ {product.rating}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
