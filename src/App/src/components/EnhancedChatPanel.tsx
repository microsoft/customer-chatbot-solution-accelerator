import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import { useAutoScroll } from '@/hooks/useAutoScroll';
import { useDebounce } from '@/hooks/useDebounce';
import { ChatMessage, Product } from '@/lib/types';
import { cn } from '@/lib/utils';
import { Add20Regular } from '@fluentui/react-icons';
import { PaperPlaneRight } from '@phosphor-icons/react';
import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { EnhancedChatMessageBubble } from './EnhancedChatMessageBubble';

interface EnhancedChatPanelProps {
  messages: ChatMessage[];
  onSendMessage: (content: string) => void;
  onNewChat: () => void;
  isTyping: boolean;
  onAddToCart?: (product: Product) => void;
  className?: string;
  isLoading?: boolean;
}

export const EnhancedChatPanel = ({
  messages,
  onSendMessage,
  onNewChat,
  isTyping,
  onAddToCart,
  className,
  isLoading = false,
}: EnhancedChatPanelProps) => {
  const [inputValue, setInputValue] = useState('');
  const debouncedInputValue = useDebounce(inputValue, 120);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const isInputDisabled = useMemo(
    () => isTyping || isLoading,
    [isTyping, isLoading],
  );

  const handleSend = useCallback(() => {
    if (inputValue.trim()) {
      onSendMessage(inputValue.trim());
      setInputValue('');
      setTimeout(() => {
        inputRef.current?.focus();
      }, 0);
    }
  }, [inputValue, onSendMessage]);

  const handleKeyPress = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }, [handleSend]);

  useAutoScroll(messagesEndRef, [messages, isTyping]);

  useEffect(() => {
    if (!isTyping && !isLoading && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isTyping, isLoading]);

  return (
    <div className={cn("flex flex-col h-full bg-background", className)}>
      {/* Scrollable Chat Content Area - Takes remaining space */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <ScrollArea className="flex-1 h-full">
          <div className="p-6 space-y-6">
            {/* Loading State - Show skeleton when loading chat history */}
            {isLoading && messages.length === 0 ? (
              <div className="space-y-4">
                {/* Loading skeleton for messages */}
                <div className="flex gap-3 justify-start">
                  <Skeleton className="w-8 h-8 rounded-full flex-shrink-0" />
                  <div className="space-y-2 flex-1 max-w-[80%]">
                    <Skeleton className="h-16 w-full rounded-2xl" />
                  </div>
                </div>
                <div className="flex gap-3 justify-end">
                  <div className="space-y-2 flex-1 max-w-[80%] flex flex-col items-end">
                    <Skeleton className="h-12 w-3/4 rounded-2xl" />
                  </div>
                  <Skeleton className="w-8 h-8 rounded-full flex-shrink-0" />
                </div>
                <div className="flex gap-3 justify-start">
                  <Skeleton className="w-8 h-8 rounded-full flex-shrink-0" />
                  <div className="space-y-2 flex-1 max-w-[80%]">
                    <Skeleton className="h-20 w-full rounded-2xl" />
                  </div>
                </div>
              </div>
            ) : (
              <>
                {/* Welcome Message - Only show when no messages and not loading */}
                {messages.length === 0 && !isTyping && !isLoading && (
              <div className="flex flex-col items-center justify-center text-center space-y-6 h-full min-h-[400px]">
                {/* AI Assistant Icon */}
                <img 
                  src="/contoso-ai-icon.png" 
                  alt="AI Assistant" 
                  className="w-16 h-16"
                />
                
                {/* Welcome Text */}
                <div className="space-y-2">
                  <h2 className="text-xl font-semibold text-foreground">
                    Hey! I'm here to help.
                  </h2>
                  <p className="text-muted-foreground max-w-sm">
                    Ask me about returns & exchanges, warranties, or general product advice.
                  </p>
                </div>
                
                {/* Quick Start Hint */}
                <div className="text-xs text-muted-foreground">
                  Click the plus icon to start a new chat anytime
                </div>
              </div>
            )}

            {/* Chat Messages */}
            {messages.map((message) => (
              <EnhancedChatMessageBubble
                key={message.id}
                message={message}
                onAddToCart={onAddToCart}
              />
            ))}
            
            {/* Typing Indicator - Only show when AI is actively responding */}
            {isTyping && !isLoading && (
              <EnhancedChatMessageBubble
                message={{
                  id: 'typing',
                  content: '',
                  sender: 'assistant',
                  timestamp: new Date().toISOString()
                }}
                isTyping={true}
              />
            )}
              </>
            )}
            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>
      </div>

      {/* Fixed Input Footer */}
      <div className="flex-shrink-0 border-t bg-background p-4 space-y-3">
        {/* Input Field */}
        <div className="flex-1 relative">
          <Input
            ref={inputRef}
            placeholder="Ask a question"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyPress}
            className="pr-16 resize-none min-h-[40px]"
            disabled={isInputDisabled}
          />
          <div className="absolute right-1 top-1/2 transform -translate-y-1/2 flex gap-1">
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0"
              title="Start new chat"
              onClick={onNewChat}
              disabled={isInputDisabled}
            >
              <Add20Regular className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0"
              title="Send message"
              onClick={handleSend}
              disabled={!debouncedInputValue.trim() || isInputDisabled}
            >
              <PaperPlaneRight className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Disclaimer */}
        <p className="text-xs text-muted-foreground text-center">
          AI-generated content may be incorrect
        </p>
      </div>
    </div>
  );
};
