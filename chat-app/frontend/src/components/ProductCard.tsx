import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Product } from '@/lib/types';
import { ShoppingCart, Star } from '@phosphor-icons/react';
import { memo } from 'react';

interface ProductCardProps {
  product: Product;
  onAddToCart: (product: Product) => void;
}

export const ProductCard = memo(({ product, onAddToCart }: ProductCardProps) => {
  const hasDiscount = product.originalPrice && product.originalPrice > product.price;
  const discountPercent = hasDiscount 
    ? Math.round(((product.originalPrice! - product.price) / product.originalPrice!) * 100)
    : 0;

  return (
    <Card className="group relative overflow-hidden transition-all duration-300 hover:shadow-xl hover:shadow-primary/5 hover:-translate-y-1 border border-border/50">
      <div className="relative aspect-square overflow-hidden bg-muted/30">
        <img
          src={product.image}
          alt={product.title}
          className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-110"
          loading="lazy"
        />
        {hasDiscount && (
          <Badge 
            variant="destructive" 
            className="absolute left-3 top-3 px-2.5 py-1 text-xs font-semibold shadow-lg"
          >
            -{discountPercent}%
          </Badge>
        )}
        {!product.inStock && (
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center">
            <Badge variant="secondary" className="text-sm font-medium shadow-lg">
              Out of Stock
            </Badge>
          </div>
        )}
        {/* Gradient overlay on hover for better aesthetics */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
      </div>
      
      <CardContent className="p-4 space-y-3">
        {/* Title and Category */}
        <div className="space-y-1">
          <h3 className="font-semibold text-foreground line-clamp-2 leading-snug group-hover:text-primary transition-colors min-h-[2.5rem]">
            {product.title}
          </h3>
          <p className="text-sm text-muted-foreground">
            {product.category}
          </p>
        </div>

        {/* Rating */}
        <div className="flex items-center gap-1.5">
          <div className="flex items-center gap-1">
            <Star className="w-4 h-4 fill-yellow-400 text-yellow-400 drop-shadow-sm" />
            <span className="text-sm font-semibold text-foreground">{product.rating}</span>
          </div>
          <span className="text-xs text-muted-foreground">
            ({product.reviewCount})
          </span>
        </div>

        {/* Price and Button */}
        <div className="flex items-center justify-between pt-1">
          <div className="flex flex-col gap-0.5">
            <span className="font-bold text-xl text-foreground">
              ${product.price.toFixed(2)}
            </span>
            {hasDiscount && (
              <span className="text-xs text-muted-foreground line-through">
                ${product.originalPrice!.toFixed(2)}
              </span>
            )}
          </div>
          
          <Button
            size="sm"
            onClick={() => onAddToCart(product)}
            disabled={!product.inStock}
            className="gap-2 transition-all duration-300 hover:gap-3 hover:shadow-md shadow-sm"
          >
            <ShoppingCart className="w-4 h-4" />
            <span className="font-medium">Add</span>
          </Button>
        </div>
      </CardContent>
    </Card>
  );
});

ProductCard.displayName = 'ProductCard';