import { api, setApiBearerToken } from '@/lib/api';
import { isWidgetEmbedded, resolveAuthOrigin } from '@/lib/embedContext';
import { createContext, ReactNode, useContext, useEffect, useState } from 'react';

export interface User {
  id: string;
  name: string;
  email: string;
  roles: string[];
  is_authenticated: boolean;
  is_guest?: boolean;
}

export interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: () => void;
  logout: () => void;
  isAuthenticated: boolean;
  isIdentityProviderConfigured: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const AUTH_REDIRECT_KEY = 'ccsa_easyauth_redirect';

type EasyAuthProbe = {
  token: string | null;
  providerConfigured: boolean;
  needsLoginRedirect: boolean;
};

function easyAuthMeUrl(): string {
  if (isWidgetEmbedded()) {
    return '/.auth/me';
  }
  const authBase = resolveAuthOrigin();
  return authBase ? `${authBase}/.auth/me` : '/.auth/me';
}

function easyAuthLoginUrl(): string {
  if (isWidgetEmbedded()) {
    return '/.auth/login/aad';
  }
  const authBase = resolveAuthOrigin();
  return authBase ? `${authBase}/.auth/login/aad` : '/.auth/login/aad';
}

function easyAuthLogoutUrl(): string {
  if (isWidgetEmbedded()) {
    return '/.auth/logout';
  }
  const authBase = resolveAuthOrigin();
  return authBase ? `${authBase}/.auth/logout` : '/.auth/logout';
}

function loginRedirectAlreadyAttempted(): boolean {
  try {
    return sessionStorage.getItem(AUTH_REDIRECT_KEY) === '1';
  } catch {
    return false;
  }
}

function markLoginRedirectAttempted(): void {
  try {
    sessionStorage.setItem(AUTH_REDIRECT_KEY, '1');
  } catch {
  }
}

function clearLoginRedirectAttempted(): void {
  try {
    sessionStorage.removeItem(AUTH_REDIRECT_KEY);
  } catch {
  }
}

async function probeEasyAuth(): Promise<EasyAuthProbe> {
  try {
    const response = await fetch(easyAuthMeUrl(), {
      credentials: 'include',
      redirect: 'manual',
    });

    if (response.type === 'opaqueredirect') {
      return { token: null, providerConfigured: true, needsLoginRedirect: true };
    }

    if (response.status === 401 || response.status === 403) {
      return { token: null, providerConfigured: true, needsLoginRedirect: true };
    }

    if (!response.ok) {
      return { token: null, providerConfigured: false, needsLoginRedirect: false };
    }

    const authData = await response.json();
    if (!authData?.length) {
      return { token: null, providerConfigured: true, needsLoginRedirect: true };
    }

    const idToken = String(authData[0]?.id_token ?? '').trim();
    if (!idToken) {
      return { token: null, providerConfigured: true, needsLoginRedirect: true };
    }

    return {
      token: idToken,
      providerConfigured: true,
      needsLoginRedirect: false,
    };
  } catch {
    return { token: null, providerConfigured: isWidgetEmbedded(), needsLoginRedirect: false };
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isIdentityProviderConfigured, setIsIdentityProviderConfigured] = useState(false);

  const login = () => {
    markLoginRedirectAttempted();
    window.location.href = easyAuthLoginUrl();
  };

  const logout = () => {
    setApiBearerToken(null);
    clearLoginRedirectAttempted();
    window.location.href = easyAuthLogoutUrl();
  };

  useEffect(() => {
    let isAuthenticating = false;
    let isMounted = true;
    let retryCount = 0;
    let retryTimeoutId: ReturnType<typeof setTimeout> | null = null;
    const MAX_RETRIES = 3;
    const RETRY_DELAY = 1000;

    const finishLoading = () => {
      if (!isMounted) return;
      setIsLoading(false);
      isAuthenticating = false;
    };

    const initializeAuth = async (isRetry = false) => {
      if (isAuthenticating || !isMounted) return;

      isAuthenticating = true;
      if (!isRetry) retryCount = 0;

      let providerConfigured = false;
      try {
        const authProbe = await probeEasyAuth();
        providerConfigured = authProbe.providerConfigured;

        const bearerToken = authProbe.token;
        if (bearerToken) {
          setApiBearerToken(bearerToken);
          clearLoginRedirectAttempted();
        } else {
          setApiBearerToken(null);
        }

        const response = await api.get('/api/auth/me');

        if (
          response.data.is_guest &&
          bearerToken &&
          retryCount < MAX_RETRIES
        ) {
          retryCount++;
          retryTimeoutId = setTimeout(() => {
            isAuthenticating = false;
            initializeAuth(true);
          }, RETRY_DELAY);
          isAuthenticating = false;
          return;
        }

        if (!isMounted) return;

        setUser(response.data);
        setIsIdentityProviderConfigured(
          providerConfigured ||
            !response.data.is_guest ||
            response.data.is_authenticated
        );
        finishLoading();
      } catch (error: any) {
        if (!isMounted) return;

        setIsIdentityProviderConfigured(
          providerConfigured || error.response?.status === 302
        );
        setUser(null);
        finishLoading();
      }
    };

    initializeAuth();

    const handleVisibilityChange = () => {
      if (!document.hidden) initializeAuth();
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      isMounted = false;
      if (retryTimeoutId) clearTimeout(retryTimeoutId);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  const value: AuthContextType = {
    user,
    isLoading,
    login,
    logout,
    isAuthenticated: !!user && !user.is_guest,
    isIdentityProviderConfigured,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
