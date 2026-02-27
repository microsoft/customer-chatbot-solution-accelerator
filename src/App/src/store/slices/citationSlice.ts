import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface CitationSliceState {
  isPanelOpen: boolean;
  selectedCitationId: string | null;
  byMessageId: Record<string, string[]>;
}

const initialState: CitationSliceState = {
  isPanelOpen: false,
  selectedCitationId: null,
  byMessageId: {},
};

const citationSlice = createSlice({
  name: 'citation',
  initialState,
  reducers: {
    openCitationPanel: (state, action: PayloadAction<string | null>) => {
      state.isPanelOpen = true;
      state.selectedCitationId = action.payload;
    },
    closeCitationPanel: (state) => {
      state.isPanelOpen = false;
      state.selectedCitationId = null;
    },
    setMessageCitations: (state, action: PayloadAction<{ messageId: string; citations: string[] }>) => {
      state.byMessageId[action.payload.messageId] = action.payload.citations;
    },
    clearCitations: () => initialState,
  },
});

export const { openCitationPanel, closeCitationPanel, setMessageCitations, clearCitations } = citationSlice.actions;
export default citationSlice.reducer;
