import { useAppDispatch } from '@/store/hooks';
import { createConversation, fetchConversationMessages, sendChatMessage } from '@/store/slices/chatSlice';
import { useCallback } from 'react';

export const useChatApi = () => {
  const dispatch = useAppDispatch();

  const sendMessage = useCallback(
    (content: string) => dispatch(sendChatMessage(content)).unwrap(),
    [dispatch],
  );

  const startNewConversation = useCallback(
    () => dispatch(createConversation()).unwrap(),
    [dispatch],
  );

  const fetchMessages = useCallback(
    (sessionId: string) => dispatch(fetchConversationMessages(sessionId)).unwrap(),
    [dispatch],
  );

  return {
    sendMessage,
    startNewConversation,
    fetchMessages,
  };
};
