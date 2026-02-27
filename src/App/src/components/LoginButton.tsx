import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';
import {
  Menu,
  MenuDivider,
  MenuItem,
  MenuList,
  MenuPopover,
  MenuTrigger,
} from '@fluentui/react-components';
import { Person20Regular, SignOut20Regular } from '@fluentui/react-icons';
import { ShieldWarning, Spinner } from '@phosphor-icons/react';

export function LoginButton() {
  const { user, isLoading, logout, isAuthenticated, isIdentityProviderConfigured } = useAuth();

  if (isLoading) {
    return (
      <Button variant="outline" size="small" disabled className="transition-all duration-200">
        <Spinner className="w-5 h-5 animate-spin" />
      </Button>
    );
  }

  if (isAuthenticated && user) {
    let initials = "U"; // Default fallback
    
    if (user.name && user.name.includes("@")) {
      const emailPrefix = user.name.split("@")[0];
      const parts = emailPrefix.split(".");
      if (parts.length >= 2) {
        initials = (parts[0][0] + parts[1][0]).toUpperCase();
      } else {
        initials = emailPrefix.substring(0, 2).toUpperCase();
      }
    } else if (user.name) {
      initials = user.name
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2);
    }

    return (
      <div className="flex items-center gap-2">
        <Menu>
          <MenuTrigger>
            <Button
              variant="ghost"
              size="small"
              className="transition-all duration-200 hover:bg-accent p-1"
              title={`(${user.email})`}
            >
              <Avatar className="w-8 h-8">
                <AvatarImage src={undefined} alt={user.name} />
                <AvatarFallback className="bg-primary text-primary-foreground text-sm">
                  {initials}
                </AvatarFallback>
              </Avatar>
            </Button>
          </MenuTrigger>
          <MenuPopover>
            <MenuList>
              <MenuItem
                icon={<Person20Regular />}
                disabled
                style={{ cursor: 'default' }}
              >
                <div className="flex flex-col min-w-0 max-w-[220px]">
                  <span className="font-semibold text-sm truncate block">
                    {user.name}
                  </span>
                  <span className="text-xs text-gray-500 truncate block">
                    {user.email}
                  </span>
                </div>
              </MenuItem>
              <MenuDivider />
              <MenuItem
                icon={<SignOut20Regular />}
                onClick={logout}
              >
                Logout
              </MenuItem>
            </MenuList>
          </MenuPopover>
        </Menu>
      </div>
    );
  }

  if (isIdentityProviderConfigured && !isAuthenticated) {
    return (
      <Button
        variant="default"
        size="small"
        onClick={() => {
          window.location.href = '/.auth/login/aad';
        }}
        className="transition-all duration-200 flex items-center gap-2"
        title="Login with Microsoft"
      >
        <ShieldWarning className="w-5 h-5" />
        <span className="hidden sm:inline text-xs">Login</span>
      </Button>
    );
  }

  return (
    <Button
      variant="outline"
      size="small"
      disabled
      className="transition-all duration-200 flex items-center gap-2 opacity-50 cursor-not-allowed"
      title="Enable Identity Provider in Azure Portal to enable authentication"
    >
      <ShieldWarning className="w-5 h-5" />
      <span className="hidden sm:inline text-xs">Enable Identity Provider</span>
    </Button>
  );
}
