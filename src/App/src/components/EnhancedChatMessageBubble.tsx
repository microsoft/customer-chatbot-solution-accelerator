import React, { memo } from 'react';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { ChatMessage, Product } from '@/lib/types';
import { cn } from '@/lib/utils';
import { ProductRecommendation } from './ProductRecommendation';
import { formatTimestamp } from '@/lib/api';

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

  // Check if message contains product recommendations
  const hasProductRecommendations = message.recommendedProducts && message.recommendedProducts.length > 0;

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
        "flex flex-col gap-1 max-w-[80%]",
        isUser ? "items-end" : "items-start"
      )}>
        {/* Message Content */}
        <div className={cn(
          "rounded-2xl px-4 py-2.5 text-sm leading-relaxed",
          isUser ? (
            "bg-primary text-primary-foreground rounded-br-md"
          ) : (
            "bg-muted text-muted-foreground rounded-bl-md border"
          ),
          isTyping && "animate-pulse"
        )}>
          {isTyping ? (
            <div className="flex items-center gap-1">
              <span className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          ) : (
            <p className="whitespace-pre-wrap break-words">
              {message.content}
            </p>
          )}
        </div>

        {/* Product Recommendations */}
        {!isTyping && hasProductRecommendations && onAddToCart && (
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
        )}
        
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
