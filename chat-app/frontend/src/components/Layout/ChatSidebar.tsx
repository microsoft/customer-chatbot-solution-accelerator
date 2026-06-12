import { EnhancedChatPanel } from '@/components/EnhancedChatPanel';
import { ChatMessage } from '@/lib/types';
import { Button } from '@fluentui/react-components';
import { Add20Regular } from '@fluentui/react-icons';
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
}) => {
  useEffect(() => {
    if (isOpen) {
      eventBus.emit("setActivePanel", "first");
    } else {
      eventBus.emit("setActivePanel", null);
    }
  }, [isOpen]);

  return (
    <div className="w-full h-full min-h-0 flex justify-center">
    <PanelRight 
      panelType="first"
      panelWidth={768}
      panelResize={true}
      defaultClosed={!isOpen}
    >
      <PanelRightToolbar>
        <Button
          appearance="subtle"
          icon={<Add20Regular />}
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
          className="h-full"
        />
      </div>
    </PanelRight>
    </div>
  );
};
