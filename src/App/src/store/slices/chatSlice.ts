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
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchConversationMessages.pending, (state) => {
        state.error = null;
      })
      .addCase(fetchConversationMessages.fulfilled, (state, action) => {
        state.currentSessionId = action.payload.sessionId;
        state.messages = action.payload.messages;
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

export const { setCurrentSessionId, clearMessages, addLocalUserMessage } = chatSlice.actions;
export default chatSlice.reducer;
