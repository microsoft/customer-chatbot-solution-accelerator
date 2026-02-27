import { FluentProvider } from '@fluentui/react-components';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createRoot } from 'react-dom/client';
import { ErrorBoundary } from "react-error-boundary";
import { Provider } from 'react-redux';

import { Toaster } from '@/components/ui/sonner';
import { AuthProvider } from '@/contexts/AuthContext';
import { ThemeProvider, useTheme } from '@/contexts/ThemeContext';
import { store } from '@/store';
import App from './App.tsx';
import { ErrorFallback } from './ErrorFallback.tsx';

import "./index.css";
import "./main.css";
import "./styles/coral.css";
import "./styles/theme.css";

const queryClient = new QueryClient()

const ThemedFluentProvider = ({ children }: { children: React.ReactNode }) => {
  const { theme } = useTheme();
  return (
    <FluentProvider theme={theme}>
      {children}
    </FluentProvider>
  );
};

createRoot(document.getElementById('root')!).render(
  <ErrorBoundary FallbackComponent={ErrorFallback}>
    <QueryClientProvider client={queryClient}>
      <Provider store={store}>
        <ThemeProvider>
          <ThemedFluentProvider>
            <AuthProvider>
              <App />
              <Toaster />
            </AuthProvider>
          </ThemedFluentProvider>
        </ThemeProvider>
      </Provider>
    </QueryClientProvider>
  </ErrorBoundary>
)
