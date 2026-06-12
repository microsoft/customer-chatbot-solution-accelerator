import React from 'react';
import { Button } from '@fluentui/react-components';
import { ChatCircle, Sun, Moon } from '@phosphor-icons/react';
import { LoginButton } from '@/components/LoginButton';
import { useTheme } from '@/contexts/ThemeContext';

interface BottomNavigationProps {
  onToggleChat?: () => void;
  isChatOpen?: boolean;
}

export const BottomNavigation: React.FC<BottomNavigationProps> = ({
  onToggleChat,
  isChatOpen = false,
}) => {
  const { themeMode, toggleTheme } = useTheme();

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex items-center justify-between px-4 py-2">
        {/* Left side - Brand */}
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 bg-primary rounded flex items-center justify-center">
            <span className="text-white text-xs font-bold">S</span>
          </div>
          <span className="text-sm font-medium text-foreground">ShopChat</span>
        </div>
        
        {/* Right side - All Actions */}
        <div className="flex items-center gap-1">
          {/* Chat Toggle Button */}
          {onToggleChat && (
            <Button
              appearance={isChatOpen ? "primary" : "subtle"}
              icon={<ChatCircle className="w-5 h-5" />}
              onClick={onToggleChat}
              size="small"
              className="transition-all duration-200"
              title={isChatOpen ? 'Close Chat' : 'Open Chat'}
            />
          )}
          
          <Button
            appearance="subtle"
            icon={themeMode === 'light' ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}
            onClick={toggleTheme}
            size="small"
            className="transition-all duration-200 hover:bg-accent"
            title={`Switch to ${themeMode === 'light' ? 'dark' : 'light'} theme`}
          />
          
          {/* Login/User */}
          <LoginButton />
        </div>
      </div>
    </nav>
  );
};
