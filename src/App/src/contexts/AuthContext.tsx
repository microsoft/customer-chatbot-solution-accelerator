import { api, setEasyAuthHeaders } from '@/lib/api';
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

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isIdentityProviderConfigured, setIsIdentityProviderConfigured] = useState(false);

  useEffect(() => {
    let isAuthenticating = false;
    let authCheckTimeout: ReturnType<typeof setTimeout> | null = null;

    const initializeAuth = async () => {
      // Prevent concurrent auth requests
      if (isAuthenticating) {
        return;
      }

      isAuthenticating = true;

      try {
        // First, try to get Easy Auth headers from frontend
        let easyAuthHeaders: Record<string, string> | null = null;
        try {
          const authResponse = await fetch('/.auth/me', { 
            method: 'GET',
            credentials: 'include'
          });
          
          if (authResponse.ok) {
            const authData = await authResponse.json();
            if (authData && authData.length > 0) {
              const userData = authData[0];
              const claims = userData.user_claims;
              
              // Extract user info from claims
              const userId = claims.find(c => c.typ === 'http://schemas.microsoft.com/identity/claims/objectidentifier')?.val;
              const userName = claims.find(c => c.typ === 'name')?.val;
              const email = claims.find(c => c.typ === 'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress')?.val;
              const preferredUsername = claims.find(c => c.typ === 'preferred_username')?.val;
              
              // Create Easy Auth headers in the format backend expects
              // The x-ms-client-principal must be base64-encoded JSON (same format Azure Easy Auth uses)
              const claimsObject = claims.reduce((acc: Record<string, string>, claim: { typ: string; val: string }) => {
                // Map common claim types to simpler keys
                if (claim.typ === 'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress') {
                  acc['email'] = claim.val;
                } else if (claim.typ === 'preferred_username') {
                  acc['preferred_username'] = claim.val;
                } else if (claim.typ === 'http://schemas.microsoft.com/identity/claims/objectidentifier') {
                  acc['oid'] = claim.val;
                } else if (claim.typ === 'name') {
                  acc['name'] = claim.val;
                } else {
                  // Use the last segment of the claim type as key
                  const shortKey = claim.typ.split('/').pop() || claim.typ;
                  acc[shortKey] = claim.val;
                }
                return acc;
              }, {});
              
              const clientPrincipalB64 = btoa(JSON.stringify(claimsObject));
              
              easyAuthHeaders = {
                'x-ms-client-principal-id': userId,
                'x-ms-client-principal-name': userName || email || preferredUsername,
                'x-ms-client-principal-idp': userData.provider_name,
                'x-ms-token-aad-id-token': userData.id_token,
                'x-ms-client-principal': clientPrincipalB64
              };
              
              // Store headers globally so they're sent with ALL API requests
              setEasyAuthHeaders(easyAuthHeaders);
            }
          }
        } catch {
          // Frontend Easy Auth not available
        }
        
        // Now get user info from backend (headers will be auto-added by interceptor)
        const response = await api.get('/api/auth/me');
        setUser(response.data);
        
        // Determine if Identity Provider is configured
        const isIdentityProviderConfigured = !response.data.is_guest || response.data.is_authenticated || !!easyAuthHeaders;
        
        setIsIdentityProviderConfigured(isIdentityProviderConfigured);
        
        // If user is not authenticated, schedule one retry after 3 seconds
        // This helps catch cases where Easy Auth completes after page load
        if (!response.data.is_authenticated && !user) {
          authCheckTimeout = setTimeout(() => {
            //initializeAuth();
          }, 3000);
        }
        
      } catch (error: any) {
        // If we get a 302 redirect, it means Easy Auth is configured but user is not authenticated
        if (error.response?.status === 302) {
          setIsIdentityProviderConfigured(true); // Easy Auth is working, just need to login
          setUser(null);
        } else {
          // Other errors - assume Easy Auth is not configured
          setUser(null);
          setIsIdentityProviderConfigured(false);
        }
      } finally {
        setIsLoading(false);
        isAuthenticating = false;
      }
    };

    initializeAuth();
    
    // Listen for page visibility changes (when user comes back from login redirect)
    // Only trigger if user was previously not authenticated
    const handleVisibilityChange = () => {
      if (!document.hidden && !user) {
        //initializeAuth();
      }
    };
    
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      if (authCheckTimeout) {
        clearTimeout(authCheckTimeout);
      }
    };
  }, []);

  const login = () => {
    // Use frontend's Easy Auth login endpoint
    window.location.href = '/.auth/login/aad';
  };

  const logout = () => {
    // Clear cached auth headers
    setEasyAuthHeaders(null);
    
    // Use frontend's Easy Auth logout endpoint
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
