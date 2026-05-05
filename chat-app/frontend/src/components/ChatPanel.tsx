import React, { useState, useRef, useEffect } from 'react';
import { PaperPlaneRight, Paperclip, X, Plus } from '@phosphor-icons/react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { ChatMessageBubble } from './ChatMessageBubble';
import { ChatMessage } from '@/lib/types';
import { cn } from '@/lib/utils';

interface ChatPanelProps {
  messages: ChatMessage[];
  onSendMessage: (content: string) => void;
  onNewChat: () => void;
  isTyping: boolean;
  isOpen: boolean;
  onClose: () => void;
  className?: string;
}

export const ChatPanel = ({
  messages,
  onSendMessage,
  onNewChat,
  isTyping,
  isOpen,
  onClose,
  className
}: ChatPanelProps) => {
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
    <Card className={cn(
      "flex flex-col h-full",
      className
    )}>
      <CardHeader className="flex-row items-center justify-between space-y-0 py-4 px-4 border-b">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <span className="font-semibold text-foreground">Shopping Assistant</span>
          </div>
          <Badge variant="outline" className="text-xs">
            Online
          </Badge>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={onClose}
          className="h-8 w-8 p-0 lg:hidden"
        >
          <X className="h-4 w-4" />
        </Button>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col p-0">
        <ScrollArea className="flex-1 p-4" ref={scrollAreaRef}>
          <div className="space-y-4">
            {messages.map((message) => (
              <ChatMessageBubble
                key={message.id}
                message={message}
              />
            ))}
            {isTyping && (
              <ChatMessageBubble
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

        <div className="border-t p-4">
          <div className="flex items-end gap-2">
            <div className="flex-1 relative">
              <Input
                placeholder="Ask about products, get recommendations..."
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyPress}
                className="pr-20 resize-none min-h-[40px]"
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
                  <Plus className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0"
                  title="Attach file"
                >
                  <Paperclip className="h-4 w-4" />
                </Button>
              </div>
            </div>
            <Button
              onClick={handleSend}
              disabled={!inputValue.trim() || isTyping}
              size="sm"
              className="h-10 px-3"
            >
              <PaperPlaneRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};