import { FigmaProductCard } from '@/components/FigmaProductCard';
import { ProductCardSkeleton } from '@/components/ProductCardSkeleton';
import { api } from '@/lib/api';
import { Product } from '@/lib/types';
import { useQuery } from '@tanstack/react-query';

async function getServices(): Promise<Product[]> {
  const response = await api.get('/api/services/');
  return response.data;
}

export function HealthcareApp() {
  const { data: services = [], isLoading, error } = useQuery({
    queryKey: ['services'],
    queryFn: getServices,
    staleTime: 5 * 60 * 1000,
  });

  return (
    <div className="h-full overflow-auto p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Care Services</h1>
          <p className="text-muted-foreground mt-1">
            Browse departments and clinical programs. Use the chat assistant to ask about visiting hours, billing, or scheduling.
          </p>
        </div>
        {error ? (
          <p className="text-destructive">Unable to load services.</p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {isLoading
              ? Array.from({ length: 6 }).map((_, i) => <ProductCardSkeleton key={i} />)
              : services.map((service) => (
                  <FigmaProductCard key={service.id} product={service} />
                ))}
          </div>
        )}
      </div>
    </div>
  );
}
