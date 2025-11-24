import { createRoot } from 'react-dom/client'
import { ErrorBoundary } from "react-error-boundary";
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { FluentProvider } from '@fluentui/react-components'

import App from './App.tsx'
import { ErrorFallback } from './ErrorFallback.tsx'
import { Toaster } from '@/components/ui/sonner'
import { AuthProvider } from '@/contexts/AuthContext'
import { ThemeProvider, useTheme } from '@/contexts/ThemeContext'

import "./main.css"
import "./styles/theme.css"
import "./styles/coral.css"
import "./index.css"

const queryClient = new QueryClient()

// Theme-aware FluentProvider wrapper
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
      <ThemeProvider>
        <ThemedFluentProvider>
          <AuthProvider>
            <App />
            <Toaster />
          </AuthProvider>
        </ThemedFluentProvider>
      </ThemeProvider>
    </QueryClientProvider>
  </ErrorBoundary>
)
