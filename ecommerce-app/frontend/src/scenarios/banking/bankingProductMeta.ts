import { Product } from '@/lib/types';

export type BankingProductMeta = {
  image: string;
  highlights: string[];
};

export const BANKING_PRODUCT_META: Record<string, BankingProductMeta> = {
  'BK-0001': {
    image: '/banking/checking.svg',
    highlights: ['No monthly fee with direct deposit', 'Mobile check deposit', 'Bill pay included'],
  },
  'BK-0002': {
    image: '/banking/savings.svg',
    highlights: ['Competitive APY', 'No minimum balance for existing customers', 'FDIC insured'],
  },
  'BK-0003': {
    image: '/banking/credit-card.svg',
    highlights: ['2x points on travel and dining', 'No foreign transaction fees', 'Platinum rewards tier'],
  },
  'BK-0004': {
    image: '/banking/mortgage.svg',
    highlights: ['Fixed-rate options', 'Down payment assistance programs', 'First-time buyer support'],
  },
  'BK-0005': {
    image: '/banking/business.svg',
    highlights: ['Business debit cards', 'ACH origination', 'Accounting tool integrations'],
  },
  'BK-0006': {
    image: '/banking/cd.svg',
    highlights: ['Terms from 6 to 60 months', 'Tiered rates for higher balances', 'Guaranteed fixed rate'],
  },
  'BK-0007': {
    image: '/banking/student.svg',
    highlights: ['No maintenance fee for students', 'Valid student ID required', 'Digital banking tools'],
  },
  'BK-0008': {
    image: '/banking/investment.svg',
    highlights: ['Guided portfolios', 'Retirement planning', 'Fiduciary advisors'],
  },
};

const BANKING_PRODUCT_BY_TITLE: Record<string, string> = {
  'Everyday Checking': 'BK-0001',
  'High-Yield Savings': 'BK-0002',
  'Platinum Rewards Credit Card': 'BK-0003',
  'First-Time Homebuyer Mortgage': 'BK-0004',
  'Small Business Checking': 'BK-0005',
  'Certificate of Deposit': 'BK-0006',
  'Student Checking': 'BK-0007',
  'Investment Advisory': 'BK-0008',
};

function resolveBankingProductKey(product: Product): string {
  const id = (product.id || '').trim();
  if (BANKING_PRODUCT_META[id]) {
    return id;
  }
  const upperId = id.toUpperCase();
  if (BANKING_PRODUCT_META[upperId]) {
    return upperId;
  }
  const byTitle = BANKING_PRODUCT_BY_TITLE[product.title?.trim() ?? ''];
  if (byTitle) {
    return byTitle;
  }
  return id;
}

export function resolveBankingProductMeta(product: Product): BankingProductMeta {
  const key = resolveBankingProductKey(product);
  const byId = BANKING_PRODUCT_META[key];
  if (byId) {
    return byId;
  }
  const highlights =
    product.tags?.length > 0
      ? product.tags
      : product.description
        ? [product.description]
        : [product.category];
  return {
    image: product.image?.startsWith('/banking/') ? product.image : '/banking/checking.svg',
    highlights,
  };
}

export function resolveBankingProductImage(product: Product): string {
  return resolveBankingProductMeta(product).image;
}
