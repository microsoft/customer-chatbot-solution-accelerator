import { Configuration, LogLevel } from '@azure/msal-browser';

// Function to get configuration values from runtime config or build-time env
const getConfigValue = (key: 'clientId' | 'authority' | 'redirectUri'): string => {
  // Try runtime config first, then fallback to build-time env
  if (typeof window !== 'undefined' && (window as any).__RUNTIME_CONFIG__) {
    switch (key) {
      case 'clientId':
        return (window as any).__RUNTIME_CONFIG__.VITE_AZURE_CLIENT_ID || import.meta.env.VITE_AZURE_CLIENT_ID || '';
      case 'authority':
        return (window as any).__RUNTIME_CONFIG__.VITE_AZURE_AUTHORITY || import.meta.env.VITE_AZURE_AUTHORITY || '';
      case 'redirectUri':
        return (window as any).__RUNTIME_CONFIG__.VITE_REDIRECT_URI || import.meta.env.VITE_REDIRECT_URI || '';
    }
  }
  
  // Fallback to build-time environment variables
  switch (key) {
    case 'clientId':
      return import.meta.env.VITE_AZURE_CLIENT_ID || '';
    case 'authority':
      return import.meta.env.VITE_AZURE_AUTHORITY || '';
    case 'redirectUri':
      return import.meta.env.VITE_REDIRECT_URI || '';
  }
};

// Function to create MSAL configuration dynamically
export const createMsalConfig = (): Configuration => {
  const clientId = getConfigValue('clientId');
  const authority = getConfigValue('authority');
  const redirectUri = getConfigValue('redirectUri');

  // Debug MSAL configuration
  const isLocalhost = typeof window !== 'undefined' && 
    (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');
  
  console.log('🔧 MSAL Configuration:', {
    environment: isLocalhost ? 'development (localhost)' : 'production',
    clientId: clientId,
    authority: authority,
    redirectUri: redirectUri,
    viteEnv: {
      clientId: import.meta.env.VITE_AZURE_CLIENT_ID,
      authority: import.meta.env.VITE_AZURE_AUTHORITY,
      redirectUri: import.meta.env.VITE_REDIRECT_URI
    }
  });

  return {
    auth: {
      clientId: clientId,
      authority: authority,
      redirectUri: redirectUri,
      postLogoutRedirectUri: redirectUri,
    },
    cache: {
      cacheLocation: 'sessionStorage',
      storeAuthStateInCookie: false,
    },
    system: {
      allowNativeBroker: false, // Disable native broker to avoid CORS issues
      loggerOptions: {
        loggerCallback: (level, message, containsPii) => {
          if (containsPii) return;
          switch (level) {
            case LogLevel.Error:
              console.error(message);
              break;
            case LogLevel.Info:
              console.info(message);
              break;
            case LogLevel.Verbose:
              console.debug(message);
              break;
            case LogLevel.Warning:
              console.warn(message);
              break;
          }
        },
      },
    },
  };
};

// Export the config (will be created at runtime)
export const msalConfig = createMsalConfig();

export const loginRequest = {
  scopes: ['User.Read'],
};

export const tokenRequest = {
  scopes: ['User.Read'],
  forceRefresh: false,
};
