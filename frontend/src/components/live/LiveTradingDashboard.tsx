// Main live trading dashboard page

import React, { useState, useEffect } from 'react';
import { LiveTradingPanel } from './LiveTradingPanel';
import { CapitalManagement } from './CapitalManagement';
import { StatusMonitor } from './StatusMonitor';
import { LivePerformanceDashboard } from './LivePerformanceDashboard';
import { apiClient } from '../../services/api';
import { LiveTradingStatus } from '../../types';

export const LiveTradingDashboard: React.FC = () => {
  const [liveStatus, setLiveStatus] = useState<LiveTradingStatus | null>(null);
  const [loading, setLoading] = useState(true);

  // Check for existing live trading session
  useEffect(() => {
    const checkLiveStatus = async () => {
      try {
        // In a real implementation, we would check for active sessions
        // For now, we'll assume no active session
        setLiveStatus(null);
      } catch (error) {
        console.error('Failed to check live status:', error);
      } finally {
        setLoading(false);
      }
    };

    checkLiveStatus();
  }, []);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
          <div className="space-y-6">
            <div className="h-64 bg-gray-200 rounded-lg"></div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="h-64 bg-gray-200 rounded-lg"></div>
              <div className="h-64 bg-gray-200 rounded-lg"></div>
            </div>
            <div className="h-96 bg-gray-200 rounded-lg"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Live Trading Dashboard</h1>
        <p className="text-gray-600">Monitor and control live trading operations</p>
      </div>
      
      <div className="space-y-6">
        <LiveTradingPanel />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <CapitalManagement />
          <StatusMonitor />
        </div>
        <LivePerformanceDashboard requestId={liveStatus?.request_id} />
      </div>
    </div>
  );
};

