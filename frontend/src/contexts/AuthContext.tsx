// Authentication context for JWT token management

import { jwtDecode } from 'jwt-decode';
import React, { createContext, ReactNode, useContext, useEffect, useState } from 'react';
import { apiClient } from '../services/api';
import { User } from '../types';

interface AuthContextType {
  user: User | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initializeAuth = async () => {
      // Skip authentication in development if VITE_SKIP_AUTH is true
      if (import.meta.env.VITE_SKIP_AUTH === 'true') {
        setUser({
          id: 'dev-user',
          username: 'developer',
          email: 'dev@example.com',
          role: 'admin'
        });
        setLoading(false);
        return;
      }

      const token = localStorage.getItem('token');
      if (token) {
        try {
          const decoded = jwtDecode(token) as any;
          if (decoded.exp * 1000 > Date.now()) {
            // Token is valid, get user info
            try {
              const userInfo = await apiClient.getCurrentUser();
              setUser(userInfo);
            } catch (error) {
              // Token might be invalid, clear it
              localStorage.removeItem('token');
            }
          } else {
            // Token expired, clear it
            localStorage.removeItem('token');
          }
        } catch (error) {
          // Invalid token, clear it
          localStorage.removeItem('token');
        }
      }
      setLoading(false);
    };

    initializeAuth();
  }, []);

  const login = async (username: string, password: string) => {
    setLoading(true);
    try {
      const response = await apiClient.login({ username, password });
      localStorage.setItem('token', response.access_token);

      // Get user info after successful login
      const userInfo = await apiClient.getCurrentUser();
      setUser(userInfo);
    } catch (error) {
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      await apiClient.logout();
    } catch (error) {
      // Even if logout fails on server, clear local state
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('token');
      setUser(null);
    }
  };

  const value: AuthContextType = {
    user,
    login,
    logout,
    isAuthenticated: !!user,
    loading,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

