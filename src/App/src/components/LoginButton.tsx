import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';
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
    // Better initials logic for email addresses
    let initials = "U"; // Default fallback
    
    if (user.name && user.name.includes("@")) {
      // For email addresses like "john.doe@contoso.com"
      const emailPrefix = user.name.split("@")[0];
      const parts = emailPrefix.split(".");
      if (parts.length >= 2) {
        initials = (parts[0][0] + parts[1][0]).toUpperCase();
      } else {
        initials = emailPrefix.substring(0, 2).toUpperCase();
      }
    } else if (user.name) {
      // For regular names like "John Doe"
      initials = user.name
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2);
    }

    return (
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="small"
          onClick={logout}
          className="transition-all duration-200 hover:bg-accent p-1"
          title={`Sign out ${user.name.includes("@") ? user.name.split("@")[0] : user.name} (${user.email})`}
        >
          <Avatar className="w-8 h-8">
            <AvatarImage src={undefined} alt={user.name} />
            <AvatarFallback className="bg-primary text-primary-foreground text-sm">
              {initials}
            </AvatarFallback>
          </Avatar>
        </Button>
      </div>
    );
  }

  // If Identity Provider is configured but user is not authenticated, show login button
  if (isIdentityProviderConfigured && !isAuthenticated) {
    return (
      <Button
        variant="default"
        size="small"
        onClick={() => {
          // Use frontend's Easy Auth login endpoint
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

  // If Identity Provider is not configured, show disabled button
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
