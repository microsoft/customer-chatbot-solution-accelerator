import { EnhancedChatPanel } from '@/components/EnhancedChatPanel';
import { ChatMessage, Product } from '@/lib/types';
import { Button } from '@fluentui/react-components';
import { Edit20Regular } from '@fluentui/react-icons';
import React, { useEffect } from 'react';
import PanelRight from './PanelRight';
import PanelRightToolbar from './PanelRightToolbar';
import eventBus from './eventbus';

interface ChatSidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
  messages?: ChatMessage[];
  onSendMessage?: (content: string) => void;
  onVoiceMessage?: (text: string, role: 'user' | 'assistant') => void;
  onNewChat?: () => void;
  isTyping?: boolean;
  isLoading?: boolean;
  onAddToCart?: (product: Product) => void;
}

export const ChatSidebar: React.FC<ChatSidebarProps> = ({
  isOpen = true,
  onClose,
  messages = [],
  onSendMessage,
  onVoiceMessage,
  onNewChat,
  isTyping = false,
  isLoading = false,
  onAddToCart
}) => {
  // Sync the panel state with the isOpen prop
  useEffect(() => {
    if (isOpen) {
      eventBus.emit("setActivePanel", "first");
    } else {
      eventBus.emit("setActivePanel", null);
    }
  }, [isOpen]);

  return (
    <PanelRight 
      panelType="first"
      panelWidth={380}
      panelResize={true}
      defaultClosed={!isOpen}
    >
      <PanelRightToolbar
        panelTitle="Chat"
      >
        <Button
          appearance="subtle"
          icon={<Edit20Regular />}
          onClick={onNewChat || (() => {})}
          aria-label="Start new chat"
          title="Start new chat"
          disabled={isTyping || isLoading}
        />
      </PanelRightToolbar>
      
      <div className="h-full">
        <EnhancedChatPanel
          messages={messages}
          onSendMessage={onSendMessage || (() => {})}
          onVoiceMessage={onVoiceMessage}
          isTyping={isTyping}
          isLoading={isLoading}
          isOpen={isOpen}
          onClose={onClose || (() => {})}
          onAddToCart={onAddToCart}
          className="h-full"
        />
      </div>
    </PanelRight>
  );
};