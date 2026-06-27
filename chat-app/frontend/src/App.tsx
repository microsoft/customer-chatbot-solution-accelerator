import { AppHeader } from '@/components/Layout/AppHeader';
import { ChatSidebar } from '@/components/Layout/ChatSidebar';
import { clearCurrentSessionId, createNewChatSession, createTimestamp, getChatHistory, getCurrentSessionId, saveCurrentSessionId, saveVoiceMessage, sendMessageToChat } from '@/lib/api';
import { createVoiceChatMessage } from '@/lib/chatMessageUtils';
import { ChatMessage } from '@/lib/types';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useRef, useState } from 'react';
import { toast } from 'sonner';

function App() {
  const queryClient = useQueryClient();

  const [currentSessionId, setCurrentSessionId] = useState<string | null>(() => getCurrentSessionId());

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
    if (!currentSessionId) {
      return;
    }
    if (queryClient.getQueryData(['chat', currentSessionId]) !== undefined) {
      return;
    }
    refetchChat();
  }, [currentSessionId, queryClient, refetchChat]);

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
      .catch(() => { })
      .then(async () => {
        let sessionId = currentSessionId || getCurrentSessionId();

        if (!sessionId && role === 'user') {
          try {
            const sessionData = await createNewChatSession();
            sessionId = sessionData.session_id;
            const msg = createVoiceChatMessage(text, role, recommendedProducts);
            queryClient.setQueryData(['chat', sessionId], [msg]);
            setCurrentSessionId(sessionId);
            saveCurrentSessionId(sessionId);
          } catch {
            toast.error('Failed to start chat session');
            return;
          }
          await saveVoiceMessage(sessionId, text, role);
          return;
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
        const userMessage: ChatMessage = {
          id: `user-${Date.now()}`,
          content,
          sender: 'user',
          timestamp: createTimestamp()
        };

        queryClient.setQueryData(['chat', sessionData.session_id], [userMessage]);
        setCurrentSessionId(sessionData.session_id);
        saveCurrentSessionId(sessionData.session_id);
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
      timestamp: createTimestamp()
    };

    queryClient.setQueryData(['chat', currentSessionId], (old: ChatMessage[] = []) => [...old, userMessage]);
    setIsTyping(true);

    sendMessageMutation.mutate({ message: content, sessionId: currentSessionId });
  };

  const handleNewChat = () => {
    setIsTyping(false);
    createNewSessionMutation.mutate();
  };

  return (
    <div className="h-screen bg-background overflow-hidden flex flex-col">
      <AppHeader />

      <div className="flex-1 min-h-0 flex justify-center">
        <div className="w-full max-w-3xl min-h-0 flex flex-col border-x border-border/60 bg-background">
          <ChatSidebar
            key={currentSessionId ?? 'new-conversation'}
            isOpen={true}
            onClose={() => {}}
            messages={chatMessages || []}
            onSendMessage={handleSendMessage}
            onVoiceMessage={handleVoiceMessage}
            onNewChat={handleNewChat}
            isTyping={isTyping}
            isLoading={chatLoading || chatFetching}
          />
        </div>
      </div>
    </div>
  );
}

export default App;
