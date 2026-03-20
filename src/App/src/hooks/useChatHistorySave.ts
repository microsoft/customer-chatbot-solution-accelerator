import { saveCurrentSessionId } from '@/lib/api';
import { useEffect } from 'react';

export const useChatHistorySave = (sessionId: string | null) => {
  useEffect(() => {
    if (sessionId) {
      saveCurrentSessionId(sessionId);
    }
  }, [sessionId]);
};
