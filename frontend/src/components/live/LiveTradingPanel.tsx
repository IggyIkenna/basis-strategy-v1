// Live trading panel with start/stop controls and status monitoring

import React, { useState, useEffect } from 'react';
import { apiClient } from '../../services/api';
import { LiveTradingStatus, LiveTradingConfig } from '../../types';
import { formatDateTime, formatCurrency } from '../../utils/formatters';
import { POLLING_INTERVALS } from '../../utils/constants';

interface LiveTradingPanelProps {
  className?: string;
}

export const LiveTradingPanel: React.FC<LiveTradingPanelProps> = ({ className = '' }) => {
  const [status, setStatus] = useState<LiveTradingStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showStartDialog, setShowStartDialog] = useState(false);
  const [showStopDialog, setShowStopDialog] = useState(false);
  const [showEmergencyDialog, setShowEmergencyDialog] = useState(false);

  // Polling for status updates
  useEffect(() => {
    const pollStatus = async () => {
      if (status?.request_id) {
        try {
          const currentStatus = await apiClient.getLiveStatus(status.request_id);
          setStatus(currentStatus);
        } catch (err: any) {
          console.error('Failed to fetch live status:', err);
        }
      }
    };

    const interval = setInterval(pollStatus, POLLING_INTERVALS.LIVE_STATUS);
    return () => clearInterval(interval);
  }, [status?.request_id]);

  const handleStart = async () => {
    setLoading(true);
    setError(null);

    try {
      const config: LiveTradingConfig = {
        strategy_name: 'usdt_market_neutral',
        initial_capital: 100000,
        share_class: 'usdt'
      };

      const response = await apiClient.startLiveTrading(config);
      
      // Fetch initial status
      const initialStatus = await apiClient.getLiveStatus(response.request_id);
      setStatus(initialStatus);
      setShowStartDialog(false);
    } catch (err: any) {
      setError(err.message || 'Failed to start live trading');
    } finally {
      setLoading(false);
    }
  };

  const handleStop = async () => {
    if (!status?.request_id) return;

    setLoading(true);
    setError(null);

    try {
      await apiClient.stopLiveTrading(status.request_id);
      
      // Update status to reflect stopped state
      setStatus(prev => prev ? { ...prev, is_running: false } : null);
      setShowStopDialog(false);
    } catch (err: any) {
      setError(err.message || 'Failed to stop live trading');
    } finally {
      setLoading(false);
    }
  };

  const handleEmergencyStop = async () => {
    if (!status?.request_id) return;

    setLoading(true);
    setError(null);

    try {
      await apiClient.emergencyStopLiveTrading(status.request_id);
      
      // Update status to reflect emergency stop
      setStatus(prev => prev ? { ...prev, is_running: false } : null);
      setShowEmergencyDialog(false);
    } catch (err: any) {
      setError(err.message || 'Failed to emergency stop live trading');
    } finally {
      setLoading(false);
    }
  };

  const handleRebalance = async () => {
    setLoading(true);
    setError(null);

    try {
      await apiClient.triggerRebalance();
    } catch (err: any) {
      setError(err.message || 'Failed to trigger rebalancing');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (healthStatus: string) => {
    switch (healthStatus) {
      case 'healthy': return 'text-green-600 bg-green-100';
      case 'warning': return 'text-yellow-600 bg-yellow-100';
      case 'critical': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <div className={`bg-white shadow rounded-lg ${className}`}>
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-medium text-gray-900">Live Trading Control</h3>
        <p className="text-sm text-gray-500">Start, stop, and monitor live trading operations</p>
      </div>

      <div className="p-6">
        {error && (
          <div className="mb-4 rounded-md bg-red-50 p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error</h3>
                <div className="mt-2 text-sm text-red-700">{error}</div>
              </div>
            </div>
          </div>
        )}

        {/* Status Display */}
        {status && (
          <div className="mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center">
                <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(status.health_status)}`}>
                  {status.health_status.toUpperCase()}
                </div>
              </div>
              <p className="text-sm text-gray-500 mt-1">System Health</p>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-lg font-semibold text-gray-900">
                {formatCurrency(status.current_capital)}
              </div>
              <p className="text-sm text-gray-500">Current Capital</p>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <div className={`text-lg font-semibold ${status.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {formatCurrency(status.total_pnl)}
              </div>
              <p className="text-sm text-gray-500">Total P&L</p>
            </div>
          </div>
        )}

        {/* Control Buttons */}
        <div className="flex flex-wrap gap-3">
          {!status?.is_running ? (
            <button
              onClick={() => setShowStartDialog(true)}
              disabled={loading}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Starting...
                </>
              ) : (
                <>
                  <svg className="-ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1m4 0h1m-6 4h1m4 0h1m6-7a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Start Live Trading
                </>
              )}
            </button>
          ) : (
            <>
              <button
                onClick={() => setShowStopDialog(true)}
                disabled={loading}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-yellow-600 hover:bg-yellow-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <svg className="-ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 10h6v4H9z" />
                </svg>
                Stop Trading
              </button>

              <button
                onClick={() => setShowEmergencyDialog(true)}
                disabled={loading}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <svg className="-ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
                Emergency Stop
              </button>

              <button
                onClick={handleRebalance}
                disabled={loading}
                className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <svg className="-ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Rebalance
              </button>
            </>
          )}
        </div>

        {/* Status Information */}
        {status && (
          <div className="mt-6 text-sm text-gray-500">
            <p>Strategy: <span className="font-medium text-gray-900">{status.strategy_name}</span></p>
            <p>Started: <span className="font-medium text-gray-900">{formatDateTime(status.start_time)}</span></p>
            <p>Request ID: <span className="font-mono text-gray-900">{status.request_id}</span></p>
          </div>
        )}
      </div>

      {/* Start Confirmation Dialog */}
      {showStartDialog && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3 text-center">
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100">
                <svg className="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1m4 0h1m-6 4h1m4 0h1m6-7a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mt-4">Start Live Trading</h3>
              <div className="mt-2 px-7 py-3">
                <p className="text-sm text-gray-500">
                  Are you sure you want to start live trading? This will begin real-time strategy execution with actual capital.
                </p>
              </div>
              <div className="items-center px-4 py-3">
                <button
                  onClick={handleStart}
                  className="px-4 py-2 bg-green-500 text-white text-base font-medium rounded-md w-24 mr-2 hover:bg-green-600 focus:outline-none focus:ring-2 focus:ring-green-300"
                >
                  Start
                </button>
                <button
                  onClick={() => setShowStartDialog(false)}
                  className="px-4 py-2 bg-gray-500 text-white text-base font-medium rounded-md w-24 hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-300"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Stop Confirmation Dialog */}
      {showStopDialog && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3 text-center">
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-yellow-100">
                <svg className="h-6 w-6 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 10h6v4H9z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mt-4">Stop Live Trading</h3>
              <div className="mt-2 px-7 py-3">
                <p className="text-sm text-gray-500">
                  Are you sure you want to stop live trading? This will halt strategy execution but keep positions open.
                </p>
              </div>
              <div className="items-center px-4 py-3">
                <button
                  onClick={handleStop}
                  className="px-4 py-2 bg-yellow-500 text-white text-base font-medium rounded-md w-24 mr-2 hover:bg-yellow-600 focus:outline-none focus:ring-2 focus:ring-yellow-300"
                >
                  Stop
                </button>
                <button
                  onClick={() => setShowStopDialog(false)}
                  className="px-4 py-2 bg-gray-500 text-white text-base font-medium rounded-md w-24 hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-300"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Emergency Stop Confirmation Dialog */}
      {showEmergencyDialog && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3 text-center">
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
                <svg className="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mt-4">Emergency Stop</h3>
              <div className="mt-2 px-7 py-3">
                <p className="text-sm text-gray-500">
                  <strong>WARNING:</strong> This will immediately halt all trading and may close positions aggressively. Use only in emergency situations.
                </p>
              </div>
              <div className="items-center px-4 py-3">
                <button
                  onClick={handleEmergencyStop}
                  className="px-4 py-2 bg-red-500 text-white text-base font-medium rounded-md w-24 mr-2 hover:bg-red-600 focus:outline-none focus:ring-2 focus:ring-red-300"
                >
                  Emergency Stop
                </button>
                <button
                  onClick={() => setShowEmergencyDialog(false)}
                  className="px-4 py-2 bg-gray-500 text-white text-base font-medium rounded-md w-24 hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-300"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
