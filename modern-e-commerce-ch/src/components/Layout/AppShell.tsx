import React from 'react';
import { AppHeader } from './AppHeader';
import { MainContent } from './MainContent';
import { ChatSidebar } from './ChatSidebar';

interface AppShellProps {
  children?: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-background">
      <AppHeader />
      <div className="flex h-[calc(100vh-4rem)]">
        <MainContent>
          {children}
        </MainContent>
        <ChatSidebar />
      </div>
    </div>
  );
};
