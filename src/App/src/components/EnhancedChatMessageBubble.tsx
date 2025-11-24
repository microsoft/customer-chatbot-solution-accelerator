import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { formatTimestamp } from '@/lib/api';
import { detectContentType, parseOrdersFromText, parseProductsFromText } from '@/lib/textParsers';
import { ChatMessage, Product } from '@/lib/types';
import { cn } from '@/lib/utils';
import { memo } from 'react';
import { ChatOrderCard } from './ChatOrderCard';
import { ChatProductCard } from './ChatProductCard';
import { ProductRecommendation } from './ProductRecommendation';

interface EnhancedChatMessageBubbleProps {
  message: ChatMessage;
  isTyping?: boolean;
  onAddToCart?: (product: Product) => void;
}

export const EnhancedChatMessageBubble = memo(({ 
  message, 
  isTyping, 
  onAddToCart 
}: EnhancedChatMessageBubbleProps) => {
  const isUser = message.sender === 'user';
  const isAssistant = message.sender === 'assistant';

  // Check if message contains product recommendations (legacy)
  const hasProductRecommendations = message.recommendedProducts && message.recommendedProducts.length > 0;

  // Parse content for structured data
  const contentType = detectContentType(message.content);
  const parsedOrdersData = contentType === 'orders' ? parseOrdersFromText(message.content) : { orders: [], introText: '' };
  const parsedProductsData = contentType === 'products' ? parseProductsFromText(message.content) : { products: [], introText: '' };


  const renderContent = () => {
    if (isTyping) {
      return (
        <div className="flex items-center gap-1">
          <span className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
          <span className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
          <span className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
        </div>
      );
    }

    // Render parsed orders
    if (parsedOrdersData.orders.length > 0) {
      return (
        <div className="space-y-3">
          {parsedOrdersData.introText && (
            <p className="whitespace-pre-wrap">
              {parsedOrdersData.introText}
            </p>
          )}
          {parsedOrdersData.orders.map((order) => (
            <ChatOrderCard key={order.orderNumber} order={order} />
          ))}
        </div>
      );
    }

    // Render parsed products
    if (parsedProductsData.products.length > 0) {
      return (
        <div className="space-y-3">
          <p className="whitespace-pre-wrap">
            {parsedProductsData.introText}
          </p>
          {parsedProductsData.products.map((product) => (
            <ChatProductCard
              key={product.id}
              product={product}
              onAddToCart={onAddToCart}
            />
          ))}
        </div>
      );
    }

    // Fallback to existing product recommendations
    if (hasProductRecommendations && onAddToCart) {
      return (
        <div className="space-y-2">
          <p className="whitespace-pre-wrap">
            {message.content}
          </p>
          <div className="space-y-2 mt-2">
            {message.recommendedProducts!.map((product) => (
              <ProductRecommendation
                key={product.id}
                product={product}
                onAddToCart={onAddToCart}
                compact={true}
              />
            ))}
          </div>
        </div>
      );
    }

    // Default text content
    return (
      <p className="whitespace-pre-wrap">
        {message.content}
      </p>
    );
  };

  return (
    <div className={cn(
      "flex gap-3 max-w-full",
      isUser ? "justify-end" : "justify-start"
    )}>
      {isAssistant && (
        <Avatar className="w-8 h-8 flex-shrink-0">
          <AvatarImage src="/api/placeholder/32/32" />
          <AvatarFallback className="bg-accent text-accent-foreground text-xs font-medium">
            AI
          </AvatarFallback>
        </Avatar>
      )}
      
      <div className={cn(
        "flex flex-col gap-1 max-w-[80%] min-w-0",
        isUser ? "items-end" : "items-start"
      )}>
        <div 
          className={cn(
            "rounded-2xl px-4 py-2.5 text-sm leading-relaxed",
            isUser ? (
              "bg-primary text-primary-foreground rounded-br-md"
            ) : (
              "bg-muted text-muted-foreground rounded-bl-md border"
            ),
            isTyping && "animate-pulse"
          )}
          style={{ overflowWrap: 'anywhere', wordBreak: 'break-word' }}
        >
          {renderContent()}
        </div>
        
        {!isTyping && (
          <span className="text-xs text-muted-foreground px-1">
            {formatTimestamp(message.timestamp)}
          </span>
        )}
      </div>
      
      {isUser && (
        <Avatar className="w-8 h-8 flex-shrink-0">
          <AvatarFallback className="bg-primary text-primary-foreground text-xs font-medium">
            You
          </AvatarFallback>
        </Avatar>
      )}
    </div>
  );
});
