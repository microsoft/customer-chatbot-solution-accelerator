import React from 'react';
import { Button } from '@fluentui/react-components';
import { WeatherSunny20Regular, WeatherMoon20Regular } from '@fluentui/react-icons';
import { useTheme } from '@/contexts/ThemeContext';

export const ThemeToggle: React.FC = () => {
  const { themeMode, toggleTheme } = useTheme();

  return (
    <Button
      appearance="subtle"
      icon={themeMode === 'light' ? <WeatherMoon20Regular /> : <WeatherSunny20Regular />}
      onClick={toggleTheme}
      size="small"
      title={`Switch to ${themeMode === 'light' ? 'dark' : 'light'} theme`}
      aria-label={`Switch to ${themeMode === 'light' ? 'dark' : 'light'} theme`}
      className="transition-all duration-200 hover:bg-accent"
    />
  );
};
