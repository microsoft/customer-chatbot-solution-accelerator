import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useMsal, useIsAuthenticated, MsalProvider } from '@azure/msal-react';
import { PublicClientApplication } from '@azure/msal-browser';
import { api, setCurrentIdToken } from '@/lib/api';
import { createMsalConfig, loginRequest, tokenRequest } from '@/lib/msalConfig';

// Auth types
export interface User {
  id: string;
  name: string;
  email: string;
  roles: string[];
  is_authenticated: boolean;
}

export interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: () => Promise<void>;
  logout: () => Promise<void>;
  isAuthenticated: boolean;
}

// Create auth context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Auth provider component
export function AuthProvider({ children }: { children: ReactNode }) {
  // Create MSAL instance when component mounts (after DOM is ready)
  const [msalInstance, setMsalInstance] = useState<PublicClientApplication | null>(null);
  
  useEffect(() => {
    // Wait a bit for window.APP_CONFIG to be loaded
    const timer = setTimeout(() => {
      const config = createMsalConfig();
      const instance = new PublicClientApplication(config);
      setMsalInstance(instance);
    }, 100);
    
    return () => clearTimeout(timer);
  }, []);
  
  if (!msalInstance) {
    return <div>Loading authentication...</div>;
  }
  
  return (
    <MsalProvider instance={msalInstance}>
      <AuthContextProvider>{children}</AuthContextProvider>
    </MsalProvider>
  );
}

// Internal auth context provider  
function AuthContextProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { instance, accounts } = useMsal();
  const isAuthenticated = useIsAuthenticated();

  // Check if we're in local development mode
  // In production, use runtime config; in development, use Vite env
  const getClientId = () => {
    if (typeof window !== 'undefined' && window.APP_CONFIG?.AZURE_CLIENT_ID) {
      return window.APP_CONFIG.AZURE_CLIENT_ID;
    }
    return import.meta.env.VITE_AZURE_CLIENT_ID;
  };
  
  const clientId = getClientId();
  const isLocalDev = !clientId || 
                     clientId === 'local-dev' ||
                     clientId === 'your-client-id-here' ||
                     clientId === '';

  // Debug logging
  console.log('🔍 Authentication Debug Info:', {
    VITE_AZURE_CLIENT_ID: import.meta.env.VITE_AZURE_CLIENT_ID,
    VITE_AZURE_TENANT_ID: import.meta.env.VITE_AZURE_TENANT_ID,
    VITE_AZURE_AUTHORITY: import.meta.env.VITE_AZURE_AUTHORITY,
    VITE_REDIRECT_URI: import.meta.env.VITE_REDIRECT_URI,
    RUNTIME_CLIENT_ID: typeof window !== 'undefined' && window.APP_CONFIG?.AZURE_CLIENT_ID,
    RUNTIME_TENANT_ID: typeof window !== 'undefined' && window.APP_CONFIG?.AZURE_TENANT_ID,
    RUNTIME_AUTHORITY: typeof window !== 'undefined' && window.APP_CONFIG?.AZURE_AUTHORITY,
    RUNTIME_REDIRECT_URI: typeof window !== 'undefined' && window.APP_CONFIG?.REDIRECT_URI,
    clientId: clientId,
    isLocalDev: isLocalDev,
    isAuthenticated: isAuthenticated,
    accountsLength: accounts.length
  });

  useEffect(() => {
    console.log('🚀 useEffect triggered!', { isLocalDev, isAuthenticated, accountsLength: accounts.length });
    
    const initializeAuth = async () => {
      try {
        console.log('🔄 Auth initialization:', { isLocalDev, isAuthenticated, accountsLength: accounts.length });
        
        // Handle redirect response first
        if (!isLocalDev) {
          try {
            const response = await instance.handleRedirectPromise();
            if (response) {
              console.log('🔄 Redirect response received:', response);
              // User just logged in via redirect
            }
          } catch (error) {
            console.log('⚠️ No redirect response or error:', error);
          }
        }
        
        if (isLocalDev) {
          // Local development mode - use mock authentication
          const token = localStorage.getItem('mock_token');
          console.log('Auth check - token exists:', !!token);
          if (token) {
            try {
              const response = await api.get('/api/auth/me', {
                headers: { Authorization: `Bearer ${token}` }
              });
              console.log('Auth check - user data:', response.data);
              setUser(response.data);
            } catch (error) {
              console.error('Failed to validate mock token:', error);
              localStorage.removeItem('mock_token');
            }
          } else {
            console.log('No token found, user not authenticated');
          }
        } else if (isAuthenticated && accounts.length > 0) {
          // Entra ID authentication
          console.log('🔐 Processing Entra ID authentication...');
          try {
            // Get the ID token from the account (not access token)
            const account = accounts[0];
            const idToken = account.idToken;
            
            if (!idToken) {
              throw new Error('No ID token available');
            }
            
            console.log('🔐 Using ID token for validation:', idToken.substring(0, 50) + '...');
            
            // Store the ID token globally for API calls
            setCurrentIdToken(idToken);
            
            // Send ID token to backend for validation
            const userResponse = await api.get('/api/auth/me', {
              headers: { Authorization: `Bearer ${idToken}` }
            });
            console.log('✅ Backend validated ID token, user data:', userResponse.data);
            setUser(userResponse.data);
          } catch (error) {
            console.error('❌ Failed to validate ID token:', error);
          }
        } else {
          console.log('🔍 No authentication state detected');
        }
      } catch (error) {
        console.error('Auth initialization error:', error);
      } finally {
        setIsLoading(false);
      }
    };

    initializeAuth();
  }, [isAuthenticated, accounts, instance, isLocalDev]);

  const login = async (email?: string, password?: string) => {
    console.log('🎯 LOGIN FUNCTION CALLED!', { email, password, isLocalDev });
    try {
      console.log('🚀 Login attempt:', { isLocalDev, email, password });
      
      if (isLocalDev) {
        console.log('📱 Using mock authentication');
        // Mock login for local development
        if (email && password) {
          const response = await api.post('/api/auth/email-login', {
            email,
            password
          });
          const { access_token, user: userData } = response.data;
          localStorage.setItem('mock_token', access_token);
          setUser(userData);
        } else {
          const response = await api.post('/api/auth/mock-login', {
            username: 'dev@localhost.com',
            name: 'Local Developer'
          });
          const { access_token, user: userData } = response.data;
          localStorage.setItem('mock_token', access_token);
          setUser(userData);
        }
      } else {
        console.log('🔐 Using Entra ID authentication (redirect)');
        try {
          // Use redirect instead of popup to avoid COOP issues
          await instance.loginRedirect(loginRequest);
          // Redirect will handle the rest - user will be set when they return
        } catch (error) {
          console.error('❌ Entra ID login failed:', error);
          throw error;
        }
      }
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  };

  const logout = async () => {
    try {
      if (isLocalDev) {
        // Mock logout
        localStorage.removeItem('mock_token');
        setUser(null);
      } else {
        // Entra ID logout (redirect)
        setCurrentIdToken(null); // Clear the stored token
        const config = createMsalConfig();
        await instance.logoutRedirect({
          postLogoutRedirectUri: config.auth.redirectUri,
        });
        setUser(null);
      }
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const value: AuthContextType = {
    user,
    isLoading,
    login,
    logout,
    isAuthenticated: !!user,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

// Hook to use auth context
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
