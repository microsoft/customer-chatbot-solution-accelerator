import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface AppSliceState {
  isChatOpen: boolean;
  isAppSpinner: boolean;
  globalError: string | null;
}

const initialState: AppSliceState = {
  isChatOpen: false,
  isAppSpinner: false,
  globalError: null,
};

const appSlice = createSlice({
  name: 'app',
  initialState,
  reducers: {
    setChatOpen: (state, action: PayloadAction<boolean>) => {
      state.isChatOpen = action.payload;
    },
    setAppSpinner: (state, action: PayloadAction<boolean>) => {
      state.isAppSpinner = action.payload;
    },
    setGlobalError: (state, action: PayloadAction<string | null>) => {
      state.globalError = action.payload;
    },
  },
});

export const { setChatOpen, setAppSpinner, setGlobalError } = appSlice.actions;
export default appSlice.reducer;
