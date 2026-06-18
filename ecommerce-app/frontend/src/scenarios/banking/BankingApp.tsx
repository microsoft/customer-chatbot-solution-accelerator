import { ProductCardSkeleton } from '@/components/ProductCardSkeleton';
import { api } from '@/lib/api';
import { Product } from '@/lib/types';
import { BankingProductCard } from '@/scenarios/banking/BankingProductCard';
import { useQuery } from '@tanstack/react-query';

async function getAccounts(): Promise<Product[]> {
  const response = await api.get('/api/accounts/');
  return response.data;
}

export function BankingApp() {
  const { data: accounts = [], isLoading, error } = useQuery({
    queryKey: ['accounts'],
    queryFn: getAccounts,
    staleTime: 5 * 60 * 1000,
  });

  return (
    <div className="h-full overflow-auto bg-background">
      <div className="max-w-6xl mx-auto px-6 lg:px-10 py-10 lg:py-14">
        <p className="text-muted-foreground text-base leading-relaxed max-w-2xl mb-4">
          Explore personal, business, and wealth products. Ask the assistant about fees, digital banking,
          fraud reporting, or which account fits your goals.
        </p>
        {error ? (
          <p className="text-destructive">Unable to load banking products.</p>
        ) : (
          <div>
            {isLoading
              ? Array.from({ length: 3 }).map((_, i) => (
                  <div key={i} className="py-14 border-b border-border">
                    <ProductCardSkeleton />
                  </div>
                ))
              : accounts.map((account) => (
                  <BankingProductCard key={account.id} product={account} />
                ))}
          </div>
        )}
      </div>
    </div>
  );
}
