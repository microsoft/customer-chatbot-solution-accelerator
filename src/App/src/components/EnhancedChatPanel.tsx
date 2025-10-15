import React, { useState, useRef, useEffect } from 'react';
import { PaperPlaneRight, Microphone } from '@phosphor-icons/react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { EnhancedChatMessageBubble } from './EnhancedChatMessageBubble';
import { ChatMessage, Product } from '@/lib/types';
import { cn } from '@/lib/utils';

interface EnhancedChatPanelProps {
  messages: ChatMessage[];
  onSendMessage: (content: string) => void;
  onNewChat: () => void;
  isTyping: boolean;
  isOpen: boolean;
  onClose: () => void;
  onAddToCart?: (product: Product) => void;
  className?: string;
}

export const EnhancedChatPanel = ({
  messages,
  onSendMessage,
  onNewChat,
  isTyping,
  isOpen,
  onClose,
  onAddToCart,
  className
}: EnhancedChatPanelProps) => {
  const [inputValue, setInputValue] = useState('');
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const handleSend = () => {
    if (inputValue.trim()) {
      onSendMessage(inputValue.trim());
      setInputValue('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  return (
    <div className={cn("flex flex-col h-full bg-background", className)}>
      {/* Chat Content Area */}
      <div className="flex-1 flex flex-col">
        <ScrollArea className="flex-1 p-6" ref={scrollAreaRef}>
          <div className="space-y-6">
            {/* Welcome Message - Only show when no messages */}
            {messages.length === 0 && !isTyping && (
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
                    Ask me about returns & exchanges, warranties, order status, or general product advice.
                  </p>
                </div>
                
                {/* Quick Start Hint */}
                <div className="text-xs text-muted-foreground">
                  Click the microphone icon to start a new chat anytime
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
            
            {/* Typing Indicator */}
            {isTyping && (
              <EnhancedChatMessageBubble
                message={{
                  id: 'typing',
                  content: '',
                  sender: 'assistant',
                  timestamp: new Date()
                }}
                isTyping={true}
              />
            )}
            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>
      </div>

      {/* Input Area */}
      <div className="p-4 space-y-3">
        {/* Input Field */}
        <div className="flex-1 relative">
          <Input
            placeholder="Ask a question"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyPress}
            className="pr-16 resize-none min-h-[40px]"
            disabled={isTyping}
          />
          <div className="absolute right-1 top-1/2 transform -translate-y-1/2 flex gap-1">
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0"
              title="Start new chat"
              onClick={onNewChat}
              disabled={isTyping}
            >
              <Microphone className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0"
              title="Send message"
              onClick={handleSend}
              disabled={!inputValue.trim() || isTyping}
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
