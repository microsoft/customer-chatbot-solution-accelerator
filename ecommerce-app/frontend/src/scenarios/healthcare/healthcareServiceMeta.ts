import { Product } from '@/lib/types';

export type HealthcareServiceMeta = {
  image: string;
  highlights: string[];
};

export const HEALTHCARE_SERVICE_META: Record<string, HealthcareServiceMeta> = {
  'HC-0001': {
    image: '/healthcare/primary-care.svg',
    highlights: ['Preventive care', 'Chronic condition management', 'Board-certified physicians'],
  },
  'HC-0002': {
    image: '/healthcare/radiology.svg',
    highlights: ['X-ray, MRI, CT, ultrasound', 'Same-week scheduling', 'On-site imaging'],
  },
  'HC-0003': {
    image: '/healthcare/cardiology.svg',
    highlights: ['Heart health evaluations', 'Stress testing', 'Specialist consultations'],
  },
  'HC-0004': {
    image: '/healthcare/laboratory.svg',
    highlights: ['On-site blood work', 'Diagnostic testing', 'Results in patient portal'],
  },
  'HC-0005': {
    image: '/healthcare/physical-therapy.svg',
    highlights: ['Post-surgery recovery', 'Injury rehabilitation', 'Licensed therapists'],
  },
  'HC-0006': {
    image: '/healthcare/urgent-care.svg',
    highlights: ['Walk-in care', 'Seven days a week', 'Non-emergency treatment'],
  },
  'HC-0007': {
    image: '/healthcare/pediatrics.svg',
    highlights: ['Well-child visits', 'Immunizations', 'Pediatric referrals'],
  },
  'HC-0008': {
    image: '/healthcare/womens-health.svg',
    highlights: ['OB/GYN services', 'Prenatal care', 'Women wellness programs'],
  },
};

const HEALTHCARE_SERVICE_BY_TITLE: Record<string, string> = {
  'Primary Care': 'HC-0001',
  'Radiology & Imaging': 'HC-0002',
  'Cardiology': 'HC-0003',
  'Laboratory Services': 'HC-0004',
  'Physical Therapy': 'HC-0005',
  'Urgent Care': 'HC-0006',
  'Pediatrics': 'HC-0007',
  "Women's Health": 'HC-0008',
};

function resolveHealthcareServiceKey(product: Product): string {
  const id = (product.id || '').trim();
  if (HEALTHCARE_SERVICE_META[id]) {
    return id;
  }
  const upperId = id.toUpperCase();
  if (HEALTHCARE_SERVICE_META[upperId]) {
    return upperId;
  }
  const byTitle = HEALTHCARE_SERVICE_BY_TITLE[product.title?.trim() ?? ''];
  if (byTitle) {
    return byTitle;
  }
  return id;
}

export function resolveHealthcareServiceMeta(product: Product): HealthcareServiceMeta {
  const key = resolveHealthcareServiceKey(product);
  const byId = HEALTHCARE_SERVICE_META[key];
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
    image: product.image?.startsWith('/healthcare/') ? product.image : '/healthcare/primary-care.svg',
    highlights,
  };
}
