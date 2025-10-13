import React from 'react';
import { ShoppingCart, Star } from '@phosphor-icons/react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Product } from '@/lib/types';

interface ProductRecommendationProps {
  product: Product;
  onAddToCart: (product: Product) => void;
  compact?: boolean;
}

export const ProductRecommendation: React.FC<ProductRecommendationProps> = ({
  product,
  onAddToCart,
  compact = false
}) => {
  const hasDiscount = product.originalPrice && product.originalPrice > product.price;
  const discountPercent = hasDiscount 
    ? Math.round(((product.originalPrice! - product.price) / product.originalPrice!) * 100)
    : 0;

  if (compact) {
    return (
      <div className="flex items-center gap-3 p-3 bg-muted/50 rounded-lg border">
        <div className="w-12 h-12 rounded-lg overflow-hidden flex-shrink-0">
          <img
            src={product.image}
            alt={product.title}
            className="w-full h-full object-cover"
          />
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="font-medium text-sm truncate">{product.title}</h4>
          <div className="flex items-center gap-2 mt-1">
            <span className="font-semibold text-sm">${product.price}</span>
            {hasDiscount && (
              <span className="text-xs text-muted-foreground line-through">
                ${product.originalPrice}
              </span>
            )}
          </div>
        </div>
        <Button
          size="sm"
          onClick={() => onAddToCart(product)}
          disabled={!product.inStock}
          className="flex-shrink-0"
        >
          <ShoppingCart className="w-4 h-4 mr-1" />
          Add
        </Button>
      </div>
    );
  }

  return (
    <Card className="w-full max-w-sm">
      <div className="relative aspect-square overflow-hidden">
        <img
          src={product.image}
          alt={product.title}
          className="h-full w-full object-cover"
          loading="lazy"
        />
        {hasDiscount && (
          <Badge 
            variant="destructive" 
            className="absolute left-2 top-2 px-2 py-1 text-xs font-semibold"
          >
            -{discountPercent}%
          </Badge>
        )}
        {!product.inStock && (
          <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
            <Badge variant="secondary" className="text-sm font-medium">
              Out of Stock
            </Badge>
          </div>
        )}
      </div>
      
      <CardContent className="p-4">
        <div className="mb-2">
          <h3 className="font-medium text-foreground line-clamp-2">
            {product.title}
          </h3>
          <p className="text-sm text-muted-foreground mt-1">
            {product.category}
          </p>
        </div>

        <div className="flex items-center gap-1 mb-3">
          <div className="flex items-center gap-1">
            <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
            <span className="text-sm font-medium">{product.rating}</span>
          </div>
          <span className="text-sm text-muted-foreground">
            ({product.reviewCount} reviews)
          </span>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-lg text-foreground">
              ${product.price}
            </span>
            {hasDiscount && (
              <span className="text-sm text-muted-foreground line-through">
                ${product.originalPrice}
              </span>
            )}
          </div>
          
          <Button
            size="sm"
            onClick={() => onAddToCart(product)}
            disabled={!product.inStock}
            className="gap-2"
          >
            <ShoppingCart className="w-4 h-4" />
            Add
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};
