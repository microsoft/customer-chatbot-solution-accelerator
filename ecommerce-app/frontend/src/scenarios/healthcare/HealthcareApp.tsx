import { ProductCardSkeleton } from '@/components/ProductCardSkeleton';
import { api } from '@/lib/api';
import { Product } from '@/lib/types';
import { HealthcareServiceCard } from '@/scenarios/healthcare/HealthcareServiceCard';
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
    <div className="h-full overflow-auto bg-background">
      <div className="max-w-6xl mx-auto px-6 lg:px-10 py-10 lg:py-14">
        <p className="text-muted-foreground text-base leading-relaxed max-w-2xl mb-4">
          Browse departments and clinical programs. Use the chat assistant to ask about visiting hours,
          billing, or scheduling.
        </p>
        {error ? (
          <p className="text-destructive">Unable to load care services.</p>
        ) : (
          <div>
            {isLoading
              ? Array.from({ length: 3 }).map((_, i) => (
                  <div key={i} className="py-14 border-b border-border">
                    <ProductCardSkeleton />
                  </div>
                ))
              : services.map((service) => (
                  <HealthcareServiceCard key={service.id} product={service} />
                ))}
          </div>
        )}
      </div>
    </div>
  );
}
