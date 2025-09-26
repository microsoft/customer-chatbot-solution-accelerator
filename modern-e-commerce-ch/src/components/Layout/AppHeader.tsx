import React from 'react';
import { Button, Text } from '@fluentui/react-components';
import { ChatCircle } from '@phosphor-icons/react';
import { LoginButton } from '@/components/LoginButton';
import { ThemeToggle } from '@/components/ThemeToggle';
import { CartDrawer } from '@/components/CartDrawer';
import { useAuth } from '@/contexts/AuthContext';

interface AppHeaderProps {
  onToggleChat?: () => void;
  isChatOpen?: boolean;
  cartItems?: any[];
  onUpdateQuantity?: (id: string, quantity: number) => void;
  onRemoveItem?: (id: string) => void;
  onCheckout?: () => void;
}

export const AppHeader: React.FC<AppHeaderProps> = ({
  onToggleChat,
  isChatOpen = false,
  cartItems = [],
  onUpdateQuantity,
  onRemoveItem,
  onCheckout
}) => {
  const { isAuthenticated } = useAuth();

  return (
    <header className="sticky top-0 z-40 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Left side - Brand */}
          <div className="flex items-center gap-3 header-brand">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
              <Text size={400} weight="bold" className="text-white">
                S
              </Text>
            </div>
            <Text size={500} weight="semibold" className="text-foreground">
              ShopChat
            </Text>
          </div>
          
          {/* Right side - Actions */}
          <div className="flex items-center gap-3">
            {/* Chat Toggle Button */}
            {onToggleChat && (
              <Button
                appearance={isChatOpen ? "primary" : "subtle"}
                icon={<ChatCircle className="w-4 h-4" />}
                onClick={onToggleChat}
                size="small"
                className="transition-all duration-200"
              >
                <span className="hidden sm:inline">
                  {isChatOpen ? 'Close Chat' : 'Open Chat'}
                </span>
              </Button>
            )}
            
            {/* Theme Toggle */}
            <ThemeToggle />
            
            {/* Cart */}
            <CartDrawer
              cartItems={cartItems}
              onUpdateQuantity={onUpdateQuantity}
              onRemoveItem={onRemoveItem}
              onCheckout={onCheckout}
            />
            
            {/* Login */}
            <LoginButton />
          </div>
        </div>
      </div>
    </header>
  );
};
