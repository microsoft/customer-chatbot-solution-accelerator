import { ChatMessage } from '@/lib/types';

export const toChatMessage = (message: any): ChatMessage => ({
  id: message.id,
  content: message.content,
  sender: message.sender || message.message_type,
  timestamp: new Date(message.timestamp || message.created_at || Date.now()).toISOString(),
});

export const createUserMessage = (content: string): ChatMessage => ({
  id: `user-${Date.now()}`,
  content,
  sender: 'user',
  timestamp: new Date().toISOString(),
});

export const createErrorMessage = (content: string): ChatMessage => ({
  id: `error-${Date.now()}`,
  content,
  sender: 'error',
  timestamp: new Date().toISOString(),
});
