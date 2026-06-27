import { ChatSidebar } from '@/components/Layout/ChatSidebar';
import { LoginButton } from '@/components/LoginButton';
import { Button } from '@/components/ui/button';
import { Toaster } from '@/components/ui/sonner';
import { useAuth } from '@/contexts/AuthContext';
import { ThemeProvider, useTheme, type ThemeMode } from '@/contexts/ThemeContext';
import { FluentProvider } from '@fluentui/react-components';
import {
  clearCurrentSessionId,
  createNewChatSession,
  createTimestamp,
  getChatHistory,
  getCurrentSessionId,
  saveCurrentSessionId,
  saveVoiceMessage,
  sendMessageToChat,
} from '@/lib/api';
import { createVoiceChatMessage } from '@/lib/chatMessageUtils';
import { ChatMessage } from '@/lib/types';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { MessageCircle } from 'lucide-react';
import { useEffect, useLayoutEffect, useRef, useState, type ReactNode } from 'react';
import { toast } from 'sonner';

export type WidgetAppProps = {
  theme?: 'light' | 'dark';
};

function ThemedFluentProvider({ children }: { children: ReactNode }) {
  const { theme } = useTheme();
  return <FluentProvider theme={theme}>{children}</FluentProvider>;
}

export function WidgetApp({ theme = 'dark' }: WidgetAppProps) {
  const themeMode: ThemeMode = theme === 'light' ? 'light' : 'dark';
  const rootRef = useRef<HTMLDivElement>(null);
  const [themeSurface, setThemeSurface] = useState<HTMLElement | null>(null);
  useLayoutEffect(() => {
    if (rootRef.current) {
      setThemeSurface(rootRef.current);
    }
  }, []);
  const queryClient = useQueryClient();
  const { isAuthenticated } = useAuth();
  const [panelOpen, setPanelOpen] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(() =>
    getCurrentSessionId(),
  );
  const { data: chatMessages = [], refetch: refetchChat, isLoading: chatLoading, isFetching: chatFetching } = useQuery({
    queryKey: ['chat', currentSessionId],
    queryFn: () => getChatHistory(currentSessionId || undefined),
    enabled: false,
    staleTime: 0,
    refetchOnWindowFocus: false,
  });
  const [isTyping, setIsTyping] = useState(false);

  useEffect(() => {
    if (currentSessionId) {
      saveCurrentSessionId(currentSessionId);
    }
  }, [currentSessionId]);

  useEffect(() => {
    if (isAuthenticated && currentSessionId) {
      refetchChat();
    }
  }, [isAuthenticated, currentSessionId, refetchChat]);

  const sendMessageMutation = useMutation({
    mutationFn: ({ message, sessionId }: { message: string; sessionId?: string }) =>
      sendMessageToChat(message, sessionId),
    onSuccess: (newMessage, variables) => {
      const targetSessionId = variables.sessionId;
      if (!targetSessionId) {
        setIsTyping(false);
        return;
      }
      queryClient.setQueryData(['chat', targetSessionId], (old: ChatMessage[] = []) => [...old, newMessage]);
      setIsTyping(false);
    },
    onError: () => {
      toast.error('Failed to send message');
      setIsTyping(false);
    },
  });

  const createNewSessionMutation = useMutation({
    mutationFn: createNewChatSession,
    onSuccess: (sessionData) => {
      queryClient.cancelQueries({ queryKey: ['chat'] });
      queryClient.removeQueries({ queryKey: ['chat'] });
      clearCurrentSessionId();
      setCurrentSessionId(sessionData.session_id);
      queryClient.setQueryData(['chat', sessionData.session_id], []);
    },
    onError: () => {
      toast.error('Failed to create new chat session');
    },
  });

  const voiceMessageQueueRef = useRef<Promise<void>>(Promise.resolve());

  const handleVoiceMessage = (text: string, role: 'user' | 'assistant', recommendedProducts?: ChatMessage['recommendedProducts']) => {
    voiceMessageQueueRef.current = voiceMessageQueueRef.current
      .catch(() => {})
      .then(async () => {
        let sessionId = currentSessionId || getCurrentSessionId();
        if (!sessionId && role === 'user') {
          try {
            const sessionData = await createNewChatSession();
            sessionId = sessionData.session_id;
            setCurrentSessionId(sessionId);
            saveCurrentSessionId(sessionId);
          } catch {
            toast.error('Failed to start chat session');
            return;
          }
        }
        if (!sessionId) {
          return;
        }
        const msg = createVoiceChatMessage(text, role, recommendedProducts);
        queryClient.setQueryData(['chat', sessionId], (old: ChatMessage[] = []) => [...old, msg]);
        if (role === 'assistant') {
          setIsTyping(false);
        }
        await saveVoiceMessage(sessionId, text, role);
      });
  };

  const handleSendMessage = async (content: string) => {
    if (!currentSessionId) {
      try {
        const sessionData = await createNewChatSession();
        setCurrentSessionId(sessionData.session_id);
        saveCurrentSessionId(sessionData.session_id);
        const userMessage: ChatMessage = {
          id: `user-${Date.now()}`,
          content,
          sender: 'user',
          timestamp: createTimestamp(),
        };
        queryClient.setQueryData(['chat', sessionData.session_id], [userMessage]);
        setIsTyping(true);
        sendMessageMutation.mutate({ message: content, sessionId: sessionData.session_id });
      } catch {
        toast.error('Failed to start chat session');
      }
      return;
    }
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      content,
      sender: 'user',
      timestamp: createTimestamp(),
    };
    queryClient.setQueryData(['chat', currentSessionId], (old: ChatMessage[] = []) => [...old, userMessage]);
    setIsTyping(true);
    sendMessageMutation.mutate({ message: content, sessionId: currentSessionId });
  };

  const handleNewChat = () => {
    setIsTyping(false);
    createNewSessionMutation.mutate();
  };

  useEffect(() => {
    if (currentSessionId) {
      refetchChat();
    }
  }, [currentSessionId, refetchChat]);

  return (
    <ThemeProvider embedTheme themeSurface={themeSurface} initialThemeMode={themeMode}>
      <ThemedFluentProvider>
        <div ref={rootRef} className="pointer-events-auto text-foreground">
          <div className="fixed bottom-4 right-4 z-[2147483646] flex flex-col items-end gap-2">
            {panelOpen ? (
              <div className="flex h-[min(85vh,640px)] w-[min(100vw-2rem,420px)] flex-col overflow-hidden rounded-lg border border-border bg-background shadow-xl">
                <div className="flex items-center justify-between gap-2 border-b border-border px-3 py-2">
                  <span className="text-sm font-semibold">Chat</span>
                  <div className="flex items-center gap-1">
                    <LoginButton showGuestActions compact />
                    <Button type="button" variant="ghost" size="sm" onClick={() => setPanelOpen(false)}>
                      Close
                    </Button>
                  </div>
                </div>
                <div className="min-h-0 flex-1">
                  <ChatSidebar
                    key={currentSessionId ?? 'new-conversation'}
                    isOpen
                    onClose={() => setPanelOpen(false)}
                    messages={chatMessages || []}
                    onSendMessage={handleSendMessage}
                    onVoiceMessage={handleVoiceMessage}
                    onNewChat={handleNewChat}
                    isTyping={isTyping}
                    isLoading={chatLoading || chatFetching}
                  />
                </div>
              </div>
            ) : null}
            <Button
              type="button"
              size="icon"
              className="h-14 w-14 rounded-full shadow-lg"
              onClick={() => setPanelOpen((o) => !o)}
              aria-label={panelOpen ? 'Close chat' : 'Open chat'}
            >
              <MessageCircle className="h-7 w-7" />
            </Button>
          </div>
        </div>
        <Toaster />
      </ThemedFluentProvider>
    </ThemeProvider>
  );
}
