import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

export const ProductCardSkeleton = () => {
  return (
    <Card className="overflow-hidden">
      <div className="aspect-square">
        <Skeleton className="h-full w-full" />
      </div>
      <CardContent className="p-4 space-y-3">
        <div className="space-y-2">
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-3 w-1/2" />
        </div>
        <div className="flex items-center gap-2">
          <Skeleton className="h-4 w-16" />
          <Skeleton className="h-3 w-20" />
        </div>
        <div className="flex items-center justify-between">
          <Skeleton className="h-6 w-16" />
          <Skeleton className="h-8 w-16" />
        </div>
      </CardContent>
    </Card>
  );
};

export const ProductGridSkeleton = ({ count = 8 }: { count?: number }) => {
  return (
    <div className="product-grid pb-6">
      {Array.from({ length: count }).map((_, i) => (
        <ProductCardSkeleton key={i} />
      ))}
    </div>
  );
};

// Figma Product Card Skeleton - Matches FigmaProductCard structure
export const FigmaProductCardSkeleton = () => {
  return (
    <div className="group relative space-y-2">
      {/* Product Image - matches aspect-square rounded-lg */}
      <div className="relative aspect-square overflow-hidden rounded-lg">
        <Skeleton className="h-full w-full" />
      </div>
      
      <div className="space-y-1">
        {/* Product Name - text-sm font-medium leading-tight (2 lines) */}
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-2/3" />
        
        {/* Product Description - text-xs leading-relaxed (2 lines) */}
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-3 w-4/5" />
        
        {/* Price - text-sm font-semibold */}
        <div className="flex items-center justify-between pt-1">
          <Skeleton className="h-4 w-20" />
        </div>
      </div>
    </div>
  );
};

export const FigmaProductGridSkeleton = ({ count = 8 }: { count?: number }) => {
  return (
    <div className="product-grid pb-6">
      {Array.from({ length: count }).map((_, i) => (
        <FigmaProductCardSkeleton key={i} />
      ))}
    </div>
  );
};