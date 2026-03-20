import { RootState } from '@/store';
import { createSelector } from '@reduxjs/toolkit';

export const selectIsChatOpen = (state: RootState) => state.app.isChatOpen;
export const selectAppSpinner = (state: RootState) => state.app.isAppSpinner;

export const selectChatMessages = (state: RootState) => state.chat.messages;
export const selectCurrentSessionId = (state: RootState) => state.chat.currentSessionId;
export const selectGeneratingResponse = (state: RootState) => state.chat.generatingResponse;

export const selectIsFetchingConvMessages = (state: RootState) => state.chatHistory.isFetchingConvMessages;
export const selectChatSessions = (state: RootState) => state.chatHistory.sessions;

export const selectIsInputDisabled = createSelector(
  [selectGeneratingResponse, selectIsFetchingConvMessages],
  (generatingResponse, isFetchingConvMessages) => generatingResponse || isFetchingConvMessages,
);
