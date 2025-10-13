import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { Theme } from '@fluentui/react-components';
import { coralLightTheme, coralDarkTheme, createThemeStyles } from '../theme/coralTheme';

type ThemeMode = 'light' | 'dark';

interface ThemeContextType {
  theme: Theme;
  themeMode: ThemeMode;
  toggleTheme: () => void;
  setTheme: (mode: ThemeMode) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

interface ThemeProviderProps {
  children: ReactNode;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  // Initialize theme from localStorage or default to dark (matching Figma)
  const [themeMode, setThemeMode] = useState<ThemeMode>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('coral-theme-mode');
      return (saved as ThemeMode) || 'dark';
    }
    return 'dark';
  });

  const theme = themeMode === 'light' ? coralLightTheme : coralDarkTheme;

  // Apply theme styles to CSS custom properties
  useEffect(() => {
    const root = document.documentElement;
    const body = document.body;
    const themeStyles = createThemeStyles(theme);
    
    // Set Fluent UI theme tokens
    Object.entries(themeStyles).forEach(([property, value]) => {
      root.style.setProperty(property, value);
    });

    // Set custom theme variables
    if (themeMode === 'dark') {
      root.style.setProperty('--coral-bg-primary', '#1a1a1a');
      root.style.setProperty('--coral-bg-secondary', '#262626');
      root.style.setProperty('--coral-bg-tertiary', '#333333');
      root.style.setProperty('--coral-text-primary', '#ffffff');
      root.style.setProperty('--coral-text-secondary', '#e6e6e6');
      root.style.setProperty('--coral-text-muted', '#cccccc');
    } else {
      root.style.setProperty('--coral-bg-primary', '#ffffff');
      root.style.setProperty('--coral-bg-secondary', '#f8f9fa');
      root.style.setProperty('--coral-bg-tertiary', '#e9ecef');
      root.style.setProperty('--coral-text-primary', '#212529');
      root.style.setProperty('--coral-text-secondary', '#495057');
      root.style.setProperty('--coral-text-muted', '#6c757d');
    }

    // Set data attribute for CSS selectors
    root.setAttribute('data-theme', themeMode);
    
    // Update both html and body classes for global styling
    root.className = root.className.replace(/theme-\w+/g, '');
    root.classList.add(`theme-${themeMode}`);
    
    body.className = body.className.replace(/theme-\w+/g, '');
    body.classList.add(`theme-${themeMode}`);
    
    // Set background directly on body to ensure it covers everything
    body.style.backgroundColor = themeMode === 'dark' ? '#1a1a1a' : '#ffffff';
    body.style.color = themeMode === 'dark' ? '#ffffff' : '#212529';
  }, [theme, themeMode]);

  // Save theme preference to localStorage
  useEffect(() => {
    localStorage.setItem('coral-theme-mode', themeMode);
  }, [themeMode]);

  const toggleTheme = () => {
    setThemeMode(prev => prev === 'light' ? 'dark' : 'light');
  };

  const setTheme = (mode: ThemeMode) => {
    setThemeMode(mode);
  };

  const value: ThemeContextType = {
    theme,
    themeMode,
    toggleTheme,
    setTheme,
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};
