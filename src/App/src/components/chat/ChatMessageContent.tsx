import { ChatOrderCard } from '@/components/ChatOrderCard';
import { ChatProductCard } from '@/components/ChatProductCard';
import { ProductRecommendation } from '@/components/ProductRecommendation';
import { detectContentType, parseOrdersFromText, parseProductsFromText } from '@/lib/textParsers';
import { ChatMessage, Product } from '@/lib/types';
import { parseChartContent } from '@/lib/utils/chartUtils';
import { memo, useMemo } from 'react';

interface ChatMessageContentProps {
  message: ChatMessage;
  isTyping?: boolean;
  onAddToCart?: (product: Product) => void;
}

const TypingMessage = memo(() => (
  <div className="flex items-center gap-1">
    <span className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
    <span className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
    <span className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
  </div>
));
TypingMessage.displayName = 'TypingMessage';

const ErrorMessage = memo(({ content }: { content: string }) => (
  <p className="whitespace-pre-wrap text-destructive">{content}</p>
));
ErrorMessage.displayName = 'ErrorMessage';

const ChartMessage = memo(({ content }: { content: string }) => {
  const parsed = parseChartContent(content);

  if (!parsed) {
    return <p className="whitespace-pre-wrap">{content}</p>;
  }

  return (
    <div className="space-y-2">
      <p className="font-medium">{parsed.title}</p>
      <ul className="list-disc list-inside text-sm">
        {parsed.points.map((point) => (
          <li key={`${point.label}-${point.value}`}>{point.label}: {point.value}</li>
        ))}
      </ul>
    </div>
  );
});
ChartMessage.displayName = 'ChartMessage';

const AssistantMessage = memo(({ message, onAddToCart }: { message: ChatMessage; onAddToCart?: (product: Product) => void }) => {
  const contentType = useMemo(() => detectContentType(message.content), [message.content]);
  const parsedOrdersData = useMemo(
    () => (contentType === 'orders' ? parseOrdersFromText(message.content) : { orders: [], introText: '' }),
    [contentType, message.content],
  );
  const parsedProductsData = useMemo(
    () =>
      contentType === 'products'
        ? parseProductsFromText(message.content)
        : { products: [], introText: '', outroText: '' },
    [contentType, message.content],
  );

  const hasProductRecommendations =
    !!message.recommendedProducts && message.recommendedProducts.length > 0;

  if (parsedOrdersData.orders.length > 0) {
    return (
      <div className="space-y-3">
        {parsedOrdersData.introText && <p className="whitespace-pre-wrap">{parsedOrdersData.introText}</p>}
        {parsedOrdersData.orders.map((order) => (
          <ChatOrderCard key={order.orderNumber} order={order} />
        ))}
      </div>
    );
  }

  if (parsedProductsData.products.length > 0) {
    return (
      <div className="space-y-3">
        {parsedProductsData.introText && <p className="whitespace-pre-wrap">{parsedProductsData.introText}</p>}
        {parsedProductsData.products.map((product) => (
          <ChatProductCard key={product.id} product={product} onAddToCart={onAddToCart} />
        ))}
        {parsedProductsData.outroText && (
          <p className="whitespace-pre-wrap mt-2">{parsedProductsData.outroText}</p>
        )}
      </div>
    );
  }

  if (hasProductRecommendations && onAddToCart) {
    return (
      <div className="space-y-2">
        <p className="whitespace-pre-wrap">{message.content}</p>
        <div className="space-y-2 mt-2">
          {message.recommendedProducts!.map((product) => (
            <ProductRecommendation key={product.id} product={product} onAddToCart={onAddToCart} compact />
          ))}
        </div>
      </div>
    );
  }

  return <p className="whitespace-pre-wrap">{message.content}</p>;
});
AssistantMessage.displayName = 'AssistantMessage';

const UserMessage = memo(({ content }: { content: string }) => (
  <p className="whitespace-pre-wrap">{content}</p>
));
UserMessage.displayName = 'UserMessage';

export const ChatMessageContent = memo(({ message, isTyping, onAddToCart }: ChatMessageContentProps) => {
  if (isTyping) {
    return <TypingMessage />;
  }

  if (message.sender === 'error') {
    return <ErrorMessage content={message.content} />;
  }

  if (message.sender === 'chart') {
    return <ChartMessage content={message.content} />;
  }

  if (message.sender === 'user') {
    return <UserMessage content={message.content} />;
  }

  return <AssistantMessage message={message} onAddToCart={onAddToCart} />;
});

ChatMessageContent.displayName = 'ChatMessageContent';
