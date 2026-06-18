import React from 'react';
import { Text } from '@fluentui/react-components';
import { LoginButton } from '@/components/LoginButton';
import { ThemeToggle } from '@/components/ThemeToggle';
import { hostAppTitle } from '@/lib/hostConfig';

export const AppHeader: React.FC = () => {
  const title = hostAppTitle();

  return (
    <header className="sticky top-0 z-40 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="w-full px-6 py-4">
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-2 header-brand">
            <img 
              src="/contoso-icon.png" 
              alt={title}
              className="w-6 h-6"
            />
            <Text size={500} weight="semibold" className="text-foreground">
              {title}
            </Text>
          </div>
          
          <div className="flex-1"></div>
          
          <div className="flex items-center gap-4">
            <ThemeToggle />
            <LoginButton />
          </div>
        </div>
      </div>
    </header>
  );
};
