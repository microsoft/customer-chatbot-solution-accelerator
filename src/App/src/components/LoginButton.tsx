import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';
import { User, SignOut, Spinner } from '@phosphor-icons/react';
import { LoginForm } from './LoginForm';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';

export function LoginButton() {
  const { user, isLoading, login, logout, isAuthenticated } = useAuth();
  const [isLoginOpen, setIsLoginOpen] = useState(false);

  const handleLogin = async (email: string, password: string) => {
    try {
      await login(email, password);
      setIsLoginOpen(false);
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  };

  const handleDirectLogin = async () => {
    console.log('🔥 BUTTON CLICKED!');
    try {
      console.log('🎯 Direct login button clicked');
      console.log('🔍 Auth context state:', { user, isLoading, isAuthenticated });
      await login();
    } catch (error) {
      console.error('Direct login failed:', error);
    }
  };

  if (isLoading) {
    return (
      <Button variant="outline" size="small" disabled className="transition-all duration-200">
        <Spinner className="w-5 h-5 animate-spin" />
      </Button>
    );
  }

  if (isAuthenticated && user) {
    return (
      <Button variant="outline" size="small" onClick={logout} className="transition-all duration-200 hover:bg-accent" title={`Logout ${user.name}`}>
        <User className="w-5 h-5" />
      </Button>
    );
  }

  return (
    <Button variant="default" size="small" onClick={handleDirectLogin} className="transition-all duration-200" title="Login">
      <User className="w-5 h-5" />
    </Button>
  );
}
