import appReducer from '@/store/slices/appSlice';
import chatHistoryReducer from '@/store/slices/chatHistorySlice';
import chatReducer from '@/store/slices/chatSlice';
import citationReducer from '@/store/slices/citationSlice';
import { configureStore } from '@reduxjs/toolkit';

export const store = configureStore({
  reducer: {
    app: appReducer,
    chat: chatReducer,
    citation: citationReducer,
    chatHistory: chatHistoryReducer,
  },
  devTools: import.meta.env.DEV,
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
