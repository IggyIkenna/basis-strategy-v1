// Logout button component

import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';

interface LogoutButtonProps {
  className?: string;
  variant?: 'button' | 'link' | 'icon';
  showConfirmation?: boolean;
}

export const LogoutButton: React.FC<LogoutButtonProps> = ({ 
  className = '',
  variant = 'button',
  showConfirmation = true
}) => {
  const [loading, setLoading] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const { logout, user } = useAuth();

  const handleLogout = async () => {
    if (showConfirmation && !showConfirm) {
      setShowConfirm(true);
      return;
    }

    setLoading(true);
    try {
      await logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setLoading(false);
      setShowConfirm(false);
    }
  };

  const handleCancel = () => {
    setShowConfirm(false);
  };

  if (variant === 'icon') {
    return (
      <div className="relative">
        <button
          onClick={handleLogout}
          disabled={loading}
          className={`p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 ${className}`}
          title="Logout"
        >
          {loading ? (
            <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          ) : (
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
          )}
        </button>
        
        {showConfirm && (
          <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-50 border border-gray-200">
            <div className="px-4 py-2 text-sm text-gray-700">
              <p className="font-medium">Confirm Logout</p>
              <p className="text-gray-500">Are you sure you want to logout?</p>
            </div>
            <div className="px-2 py-1">
              <button
                onClick={handleLogout}
                className="w-full text-left px-2 py-1 text-sm text-red-600 hover:bg-red-50 rounded"
              >
                Yes, logout
              </button>
              <button
                onClick={handleCancel}
                className="w-full text-left px-2 py-1 text-sm text-gray-600 hover:bg-gray-50 rounded"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>
    );
  }

  if (variant === 'link') {
    return (
      <button
        onClick={handleLogout}
        disabled={loading}
        className={`text-sm text-gray-500 hover:text-gray-700 focus:outline-none focus:underline ${className}`}
      >
        {loading ? 'Logging out...' : 'Logout'}
      </button>
    );
  }

  return (
    <div className="relative">
      <button
        onClick={handleLogout}
        disabled={loading}
        className={`inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed ${className}`}
      >
        {loading ? (
          <>
            <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Logging out...
          </>
        ) : (
          <>
            <svg className="-ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            Logout
          </>
        )}
      </button>
      
      {showConfirm && (
        <div className="absolute right-0 mt-2 w-64 bg-white rounded-md shadow-lg py-1 z-50 border border-gray-200">
          <div className="px-4 py-3">
            <p className="text-sm font-medium text-gray-900">Confirm Logout</p>
            <p className="text-sm text-gray-500 mt-1">
              Are you sure you want to logout from your account?
            </p>
            {user && (
              <p className="text-xs text-gray-400 mt-1">
                Logged in as: {user.username}
              </p>
            )}
          </div>
          <div className="px-2 py-1 border-t border-gray-100">
            <button
              onClick={handleLogout}
              className="w-full text-left px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded"
            >
              Yes, logout
            </button>
            <button
              onClick={handleCancel}
              className="w-full text-left px-3 py-2 text-sm text-gray-600 hover:bg-gray-50 rounded"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

