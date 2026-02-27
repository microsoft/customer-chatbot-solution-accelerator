import { deleteChatSession, getChatSessions, renameChatSession } from '@/lib/api';
import { createAsyncThunk, createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface ChatSessionSummary {
  id: string;
  session_name: string;
  message_count: number;
  last_message_at?: string;
  is_active?: boolean;
  created_at?: string;
}

interface ChatHistoryState {
  sessions: ChatSessionSummary[];
  selectedConversationId: string | null;
  isFetchingConvMessages: boolean;
  isFetchingSessions: boolean;
  isDeletingConversation: boolean;
  isRenamingConversation: boolean;
  error: string | null;
}

const initialState: ChatHistoryState = {
  sessions: [],
  selectedConversationId: null,
  isFetchingConvMessages: false,
  isFetchingSessions: false,
  isDeletingConversation: false,
  isRenamingConversation: false,
  error: null,
};

export const fetchChatHistory = createAsyncThunk('chatHistory/fetchChatHistory', async () => {
  return getChatSessions();
});

export const deleteConversation = createAsyncThunk(
  'chatHistory/deleteConversation',
  async (sessionId: string) => {
    await deleteChatSession(sessionId);
    return sessionId;
  },
);

export const renameConversation = createAsyncThunk(
  'chatHistory/renameConversation',
  async ({ sessionId, name }: { sessionId: string; name: string }) => {
    await renameChatSession(sessionId, name);
    return { sessionId, name };
  },
);

const chatHistorySlice = createSlice({
  name: 'chatHistory',
  initialState,
  reducers: {
    setSelectedConversationId: (state, action: PayloadAction<string | null>) => {
      state.selectedConversationId = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchChatHistory.pending, (state) => {
        state.isFetchingSessions = true;
      })
      .addCase(fetchChatHistory.fulfilled, (state, action) => {
        state.isFetchingSessions = false;
        state.sessions = action.payload;
      })
      .addCase(fetchChatHistory.rejected, (state) => {
        state.isFetchingSessions = false;
        state.error = 'Failed to fetch chat sessions';
      })
      .addCase(deleteConversation.pending, (state) => {
        state.isDeletingConversation = true;
      })
      .addCase(deleteConversation.fulfilled, (state, action) => {
        state.isDeletingConversation = false;
        state.sessions = state.sessions.filter((session) => session.id !== action.payload);
      })
      .addCase(deleteConversation.rejected, (state) => {
        state.isDeletingConversation = false;
        state.error = 'Failed to delete chat session';
      })
      .addCase(renameConversation.pending, (state) => {
        state.isRenamingConversation = true;
      })
      .addCase(renameConversation.fulfilled, (state, action) => {
        state.isRenamingConversation = false;
        const found = state.sessions.find((session) => session.id === action.payload.sessionId);
        if (found) {
          found.session_name = action.payload.name;
        }
      })
      .addCase(renameConversation.rejected, (state) => {
        state.isRenamingConversation = false;
        state.error = 'Failed to rename chat session';
      })
      .addMatcher(
        (action) => action.type === 'chat/fetchConversationMessages/pending',
        (state) => {
          state.isFetchingConvMessages = true;
        },
      )
      .addMatcher(
        (action) =>
          action.type === 'chat/fetchConversationMessages/fulfilled' ||
          action.type === 'chat/fetchConversationMessages/rejected',
        (state) => {
          state.isFetchingConvMessages = false;
        },
      );
  },
});

export const { setSelectedConversationId } = chatHistorySlice.actions;
export default chatHistorySlice.reducer;
