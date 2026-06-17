import {
  createNewChatSession,
  getChatHistory,
  getCurrentSessionId,
  saveCurrentSessionId,
  sendMessageToChat,
} from '@/lib/api';
import { ChatMessage } from '@/lib/types';
import { createErrorMessage, createUserMessage } from '@/lib/utils/messageUtils';
import { createAsyncThunk, createSlice, PayloadAction } from '@reduxjs/toolkit';

interface ChatState {
  currentSessionId: string | null;
  messages: ChatMessage[];
  generatingResponse: boolean;
  error: string | null;
}

const initialState: ChatState = {
  currentSessionId: getCurrentSessionId(),
  messages: [],
  generatingResponse: false,
  error: null,
};

export const fetchConversationMessages = createAsyncThunk(
  'chat/fetchConversationMessages',
  async (sessionId: string) => {
    const messages = await getChatHistory(sessionId);
    return { sessionId, messages };
  },
);

export const createConversation = createAsyncThunk(
  'chat/createConversation',
  async () => {
    const sessionData = await createNewChatSession();
    saveCurrentSessionId(sessionData.session_id);
    return sessionData.session_id;
  },
);

export const sendChatMessage = createAsyncThunk(
  'chat/sendChatMessage',
  async (content: string, thunkApi) => {
    const state = thunkApi.getState() as { chat: ChatState };
    let sessionId = state.chat.currentSessionId;

    if (!sessionId) {
      const sessionData = await createNewChatSession();
      sessionId = sessionData.session_id;
      saveCurrentSessionId(sessionId);
      thunkApi.dispatch(setCurrentSessionId(sessionId));
    }

    thunkApi.dispatch(addLocalUserMessage(createUserMessage(content)));

    const assistantMessage = await sendMessageToChat(content, sessionId);
    return { assistantMessage, sessionId };
  },
);

const chatSlice = createSlice({
  name: 'chat',
  initialState,
  reducers: {
    setCurrentSessionId: (state, action: PayloadAction<string | null>) => {
      state.currentSessionId = action.payload;
    },
    clearMessages: (state) => {
      state.messages = [];
    },
    addLocalUserMessage: (state, action: PayloadAction<ChatMessage>) => {
      state.messages.push(action.payload);
    },
    setGeneratingResponse: (state, action: PayloadAction<boolean>) => {
      state.generatingResponse = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchConversationMessages.pending, (state) => {
        state.error = null;
      })
      .addCase(fetchConversationMessages.fulfilled, (state, action) => {
        state.currentSessionId = action.payload.sessionId;
        // Merge server + local optimistic messages so an in-flight save
        // (e.g. voice assistant reply) isn't wiped by a racing fetch.
        // Dedupe by (sender, content) within a short timestamp window since
        // local IDs (user-<ts>, voice-*) never match server-assigned IDs.
        // Match is 1:1 — a single server message consumes only one local
        // duplicate so legitimately repeated messages aren't all filtered.
        const DUP_WINDOW_MS = 60_000;
        const tsOf = (t: string) => {
          const n = new Date(t).getTime();
          return Number.isNaN(n) ? 0 : n;
        };
        const remainingServer = action.payload.messages.map((m) => ({
          msg: m,
          ts: tsOf(m.timestamp),
          consumed: false,
        }));
        const localOnly = state.messages.filter((local) => {
          const localTs = tsOf(local.timestamp);
          const match = remainingServer.find(
            (s) => !s.consumed
              && s.msg.sender === local.sender
              && s.msg.content === local.content
              && Math.abs(s.ts - localTs) < DUP_WINDOW_MS,
          );
          if (match) {
            match.consumed = true;
            return false;
          }
          return true;
        });
        const merged = [...action.payload.messages, ...localOnly];
        merged.sort((a, b) => tsOf(a.timestamp) - tsOf(b.timestamp));
        state.messages = merged;
      })
      .addCase(fetchConversationMessages.rejected, (state) => {
        state.error = 'Failed to fetch messages';
      })
      .addCase(createConversation.pending, (state) => {
        state.error = null;
      })
      .addCase(createConversation.fulfilled, (state, action) => {
        state.currentSessionId = action.payload;
        state.messages = [];
      })
      .addCase(createConversation.rejected, (state) => {
        state.error = 'Failed to create a new chat session';
      })
      .addCase(sendChatMessage.pending, (state) => {
        state.generatingResponse = true;
        state.error = null;
      })
      .addCase(sendChatMessage.fulfilled, (state, action) => {
        state.generatingResponse = false;
        state.currentSessionId = action.payload.sessionId;
        state.messages.push(action.payload.assistantMessage);
      })
      .addCase(sendChatMessage.rejected, (state) => {
        state.generatingResponse = false;
        state.error = 'Failed to send message';
        state.messages.push(createErrorMessage('Failed to send message. Please try again.'));
      });
  },
});

export const { setCurrentSessionId, clearMessages, addLocalUserMessage, setGeneratingResponse } = chatSlice.actions;
export default chatSlice.reducer;
