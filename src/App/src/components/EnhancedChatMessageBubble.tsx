import { ChatMessageContent } from '@/components/chat/ChatMessageContent';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { formatTimestamp } from '@/lib/api';
import { ChatMessage, Product } from '@/lib/types';
import { cn } from '@/lib/utils';
import { memo } from 'react';

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
          <ChatMessageContent message={message} isTyping={isTyping} onAddToCart={onAddToCart} />
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

EnhancedChatMessageBubble.displayName = 'EnhancedChatMessageBubble';
