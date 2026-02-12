import React from 'react';
import { Button, Text } from '@fluentui/react-components';
import { ChatCircle } from '@phosphor-icons/react';
import { LoginButton } from '@/components/LoginButton';
import { ThemeToggle } from '@/components/ThemeToggle';
import { CartDrawer } from '@/components/CartDrawer';

interface AppHeaderProps {
  isChatOpen?: boolean;
  cartItems?: any[];
  onUpdateQuantity?: (id: string, quantity: number) => void;
  onRemoveItem?: (id: string) => void;
  onCheckout?: () => void;
  onCartOpen?: () => void;
  onChatToggle?: () => void;
}

export const AppHeader: React.FC<AppHeaderProps> = ({
  isChatOpen = false,
  cartItems = [],
  onUpdateQuantity,
  onRemoveItem,
  onCheckout,
  onCartOpen,
  onChatToggle
}) => {

  return (
    <header className="sticky top-0 z-40 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="w-full px-6 py-4">
        <div className="flex items-center justify-between w-full">
          {/* Left side - Brand */}
          <div className="flex items-center gap-2 header-brand">
            <img 
              src="/contoso-icon.png" 
              alt="Contoso" 
              className="w-6 h-6"
            />
            <Text size={500} weight="semibold" className="text-foreground">
              Contoso
            </Text>
          </div>
          
          {/* Center - Empty space for even distribution */}
          <div className="flex-1"></div>
          
          {/* Right side - Actions */}
          <div className="flex items-center gap-4">
            {/* Chat Toggle Button */}
            <Button
              appearance={isChatOpen ? "primary" : "subtle"}
              icon={<ChatCircle className="w-4 h-4" />}
              onClick={() => {
                if (onChatToggle) {
                  onChatToggle();
                }
              }}
              size="small"
              className="transition-all duration-200"
            >
              <span className="hidden sm:inline">
                {isChatOpen ? 'Close Chat' : 'Open Chat'}
              </span>
            </Button>
            
            {/* Theme Toggle */}
            <ThemeToggle />
            
            {/* Cart */}
            <CartDrawer
              cartItems={cartItems}
              onUpdateQuantity={onUpdateQuantity || (() => {})}
              onRemoveItem={onRemoveItem || (() => {})}
              onCheckout={onCheckout || (() => {})}
              onCartOpen={onCartOpen}
            />
            
            {/* Login */}
            <LoginButton />
          </div>
        </div>
      </div>
    </header>
  );
};
