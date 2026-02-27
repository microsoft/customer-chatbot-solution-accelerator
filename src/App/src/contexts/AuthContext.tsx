import { api, setEasyAuthHeaders } from '@/lib/utils/httpClient';
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

const CLAIM_TYPE_MAP: Record<string, string> = {
  'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress': 'email',
  'http://schemas.microsoft.com/identity/claims/objectidentifier': 'oid',
  'preferred_username': 'preferred_username',
  'name': 'name',
};

async function fetchEasyAuthHeaders(): Promise<Record<string, string> | null> {
  try {
    const response = await fetch('/.auth/me', { 
      credentials: 'include',
      redirect: 'manual'  // Don't follow redirects - prevents CORS error on unauthenticated redirect
    });
    
    if (!response.ok || response.type === 'opaqueredirect') return null;
    
    const authData = await response.json();
    if (!authData?.length) return null;
    
    const { user_claims: claims, provider_name, id_token } = authData[0];
    
    const claimsObject = claims.reduce((acc: Record<string, string>, { typ, val }: { typ: string; val: string }) => {
      acc[CLAIM_TYPE_MAP[typ] || typ.split('/').pop() || typ] = val;
      return acc;
    }, {});
    
    return {
      'x-ms-client-principal-id': claimsObject.oid,
      'x-ms-client-principal-name': claimsObject.name || claimsObject.email || claimsObject.preferred_username,
      'x-ms-client-principal-idp': provider_name,
      'x-ms-token-aad-id-token': id_token,
      'x-ms-client-principal': btoa(JSON.stringify(claimsObject)),
    };
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isIdentityProviderConfigured, setIsIdentityProviderConfigured] = useState(false);

  useEffect(() => {
    let isAuthenticating = false;
    let isMounted = true;
    let retryCount = 0;
    let retryTimeoutId: ReturnType<typeof setTimeout> | null = null;
    const MAX_RETRIES = 3;
    const RETRY_DELAY = 1000;

    const initializeAuth = async (isRetry = false) => {
      if (isAuthenticating || !isMounted) return;

      isAuthenticating = true;
      if (!isRetry) retryCount = 0;

      try {
        const easyAuthHeaders = await fetchEasyAuthHeaders();
        if (easyAuthHeaders) {
          setEasyAuthHeaders(easyAuthHeaders);
        }
        
        const response = await api.get('/api/auth/me');
        
        if (response.data.is_guest && easyAuthHeaders && retryCount < MAX_RETRIES) {
          retryCount++;
          retryTimeoutId = setTimeout(() => {
            isAuthenticating = false;
            initializeAuth(true);
          }, RETRY_DELAY);
          return;
        }
        
        if (!isMounted) return;
        
        setUser(response.data);
        setIsIdentityProviderConfigured(
          !response.data.is_guest || response.data.is_authenticated || !!easyAuthHeaders
        );
        setIsLoading(false);
        isAuthenticating = false;
        
      } catch (error: any) {
        if (!isMounted) return;
        
        setIsIdentityProviderConfigured(error.response?.status === 302);
        setUser(null);
        setIsLoading(false);
        isAuthenticating = false;
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

  const login = () => {
    window.location.href = '/.auth/login/aad';
  };

  const logout = () => {
    setEasyAuthHeaders(null);
    
    window.location.href = '/.auth/logout';
  };

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
