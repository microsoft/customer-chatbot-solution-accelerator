import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
// import { Button } from '@/components/ui/button';
import { formatTimestamp } from '@/lib/api';
import { detectContentType, parseOrdersFromText, parseProductsFromText } from '@/lib/textParsers';
import { ChatMessage, Product } from '@/lib/types';
import { cn } from '@/lib/utils';
// import { Pause20Filled, Speaker220Filled, Speaker220Regular } from '@fluentui/react-icons';
import { memo } from 'react';
import { ChatOrderCard } from './ChatOrderCard';
import { ChatProductCard } from './ChatProductCard';
import { ProductRecommendation } from './ProductRecommendation';

interface EnhancedChatMessageBubbleProps {
  message: ChatMessage;
  isTyping?: boolean;
  onAddToCart?: (product: Product) => void;
  voiceMessageKey?: string;
  onPlayAssistantMessage?: (message: ChatMessage, voiceMessageKey: string) => void;
  isAssistantMessagePlaying?: boolean;
  hasBeenSpoken?: boolean;
}

export const EnhancedChatMessageBubble = memo(({ 
  message, 
  isTyping, 
  onAddToCart,
  voiceMessageKey,
  onPlayAssistantMessage,
  isAssistantMessagePlaying = false,
  hasBeenSpoken = false,
}: EnhancedChatMessageBubbleProps) => {
  const isUser = message.sender === 'user';
  const isAssistant = message.sender === 'assistant';

  // Check if message contains product recommendations (legacy)
  const hasProductRecommendations = message.recommendedProducts && message.recommendedProducts.length > 0;

  // Parse content for structured data
  const contentType = detectContentType(message.content);
  const parsedOrdersData = contentType === 'orders' ? parseOrdersFromText(message.content) : { orders: [], introText: '' };
  const parsedProductsData = contentType === 'products' ? parseProductsFromText(message.content) : { products: [], introText: '', outroText: '' };


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
          {parsedProductsData.introText && (
            <p className="whitespace-pre-wrap">
              {parsedProductsData.introText}
            </p>
          )}
          {parsedProductsData.products.map((product) => (
            <ChatProductCard
              key={product.id}
              product={product}
              onAddToCart={onAddToCart}
            />
          ))}
          {parsedProductsData.outroText && (
            <p className="whitespace-pre-wrap mt-2">
              {parsedProductsData.outroText}
            </p>
          )}
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
      "group flex gap-3 max-w-full",
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
          <div className="flex items-center gap-2 px-1">
            <span className="text-xs text-muted-foreground">
              {formatTimestamp(message.timestamp)}
            </span>
            {/* {isAssistant && onPlayAssistantMessage && voiceMessageKey && message.content?.trim() && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className={cn(
                  'h-6 w-6 p-0 rounded-full text-muted-foreground hover:text-foreground transition-colors',
                  isAssistantMessagePlaying && 'text-primary',
                )}
                onClick={() => onPlayAssistantMessage(message, voiceMessageKey)}
                aria-label={isAssistantMessagePlaying ? 'Pause' : 'Play'}
                title={isAssistantMessagePlaying ? 'Pause' : 'Play'}
              >
                {isAssistantMessagePlaying ? (
                  <Pause20Filled className="h-3.5 w-3.5" />
                ) : (
                  hasBeenSpoken ? <Speaker220Filled className="h-3.5 w-3.5" /> : <Speaker220Regular className="h-3.5 w-3.5" />
                )}
              </Button>
            )} */}
          </div>
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
