import { createTimestamp, parseTimestamp } from '@/lib/api';
import { detectContentType, parseProductsFromText } from '@/lib/textParsers';
import { ChatMessage, Product } from '@/lib/types';

function normalizeProduct(raw: Record<string, unknown>): Product | null {
  const title = String(raw.title ?? '').trim();
  if (!title) {
    return null;
  }

  const priceValue = raw.price;
  const price =
    typeof priceValue === 'number'
      ? priceValue
      : parseFloat(String(priceValue ?? '0').replace(/,/g, '')) || 0;

  return {
    id: String(raw.id ?? `product-${title.toLowerCase().replace(/\s+/g, '-')}`),
    title,
    price,
    originalPrice:
      typeof raw.originalPrice === 'number'
        ? raw.originalPrice
        : raw.originalPrice
          ? parseFloat(String(raw.originalPrice).replace(/,/g, ''))
          : undefined,
    rating: typeof raw.rating === 'number' ? raw.rating : parseFloat(String(raw.rating ?? '4.5')) || 4.5,
    reviewCount:
      typeof raw.reviewCount === 'number'
        ? raw.reviewCount
        : parseInt(String(raw.reviewCount ?? '0'), 10) || 0,
    image: String(raw.image ?? ''),
    category: String(raw.category ?? 'Paint Shades'),
    inStock: raw.inStock !== false,
    description: raw.description ? String(raw.description) : undefined,
  };
}

export function normalizeProducts(raw: unknown): Product[] {
  if (!Array.isArray(raw)) {
    return [];
  }
  return raw
    .map((item) => (item && typeof item === 'object' ? normalizeProduct(item as Record<string, unknown>) : null))
    .filter((item): item is Product => item !== null);
}

export function mapApiChatMessage(msg: Record<string, unknown>): ChatMessage {
  const metadata =
    msg.metadata && typeof msg.metadata === 'object'
      ? (msg.metadata as Record<string, unknown>)
      : undefined;
  const recommendedProducts = normalizeProducts(
    msg.recommendedProducts ?? metadata?.recommendedProducts,
  );

  return withParsedProducts({
    id: String(msg.id ?? `msg-${Date.now()}`),
    content: String(msg.content ?? ''),
    sender: (msg.sender === 'user' ? 'user' : 'assistant') as ChatMessage['sender'],
    timestamp: parseTimestamp(
      (msg.timestamp as string | Date | undefined) ?? (msg.created_at as string | Date | undefined),
    ),
    recommendedProducts: recommendedProducts.length ? recommendedProducts : undefined,
  });
}

export function withParsedProducts(message: ChatMessage): ChatMessage {
  if (message.recommendedProducts?.length || message.sender !== 'assistant') {
    return message;
  }
  if (detectContentType(message.content) !== 'products') {
    return message;
  }
  const { products } = parseProductsFromText(message.content);
  if (!products.length) {
    return message;
  }
  return { ...message, recommendedProducts: products };
}

export function createVoiceChatMessage(
  text: string,
  role: 'user' | 'assistant',
  recommendedProducts?: Product[],
): ChatMessage {
  return withParsedProducts({
    id: `voice-${role}-${Date.now()}`,
    content: text,
    sender: role,
    timestamp: createTimestamp(),
    recommendedProducts: recommendedProducts?.length ? recommendedProducts : undefined,
  });
}
