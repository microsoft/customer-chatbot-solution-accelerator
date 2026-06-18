import { memo } from 'react';
import { Product } from '@/lib/types';
import { resolveBankingProductMeta } from '@/scenarios/banking/bankingProductMeta';

interface BankingProductCardProps {
  product: Product;
}

export const BankingProductCard = memo(({ product }: BankingProductCardProps) => {
  const meta = resolveBankingProductMeta(product);

  return (
    <article className="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.15fr)] gap-8 lg:gap-14 py-14 border-b border-border/80 last:border-b-0 items-center">
      <div className="space-y-5 order-1">
        <span className="inline-block text-xs font-semibold uppercase tracking-widest text-primary">
          {product.category}
        </span>
        <h2 className="text-3xl lg:text-4xl font-semibold text-foreground leading-tight">
          {product.title}
        </h2>
        {product.description ? (
          <p className="text-base text-muted-foreground leading-relaxed max-w-xl">
            {product.description}
          </p>
        ) : null}
        <div className="space-y-2 pt-2">
          <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Highlights
          </p>
          <ul className="flex flex-wrap gap-2">
            {meta.highlights.map((item) => (
              <li
                key={item}
                className="text-sm text-foreground px-3 py-1.5 rounded-full border border-border bg-muted/40"
              >
                {item}
              </li>
            ))}
          </ul>
        </div>
      </div>
      <div className="relative order-2 w-full min-h-[260px] sm:min-h-[320px] lg:min-h-[380px]">
        <div
          className="absolute inset-y-6 left-6 right-0 rounded-2xl border border-border/60 bg-muted/30 shadow-sm rotate-[-2deg]"
          aria-hidden
        />
        <div
          className="absolute inset-y-3 left-3 right-3 rounded-2xl border border-border/70 bg-muted/50 shadow-md rotate-[1deg]"
          aria-hidden
        />
        <div className="relative h-full min-h-[260px] sm:min-h-[320px] lg:min-h-[380px] rounded-2xl border border-border bg-card shadow-xl overflow-hidden">
          <img
            src={meta.image}
            alt={product.title}
            className="w-full h-full min-h-[260px] sm:min-h-[320px] lg:min-h-[380px] object-contain bg-gradient-to-br from-muted/20 to-muted/60 p-6"
            loading="lazy"
          />
        </div>
      </div>
    </article>
  );
});
