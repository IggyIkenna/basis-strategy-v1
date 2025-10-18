// Live performance dashboard with real-time metrics and charts

import React, { useState, useEffect } from 'react';
import { apiClient } from '../../services/api';
import { LivePerformance } from '../../types';
import { formatCurrency, formatPercentage, formatDateTime } from '../../utils/formatters';
import { POLLING_INTERVALS, API_ENDPOINTS } from '../../utils/constants';

interface LivePerformanceDashboardProps {
  className?: string;
  requestId?: string;
}

export const LivePerformanceDashboard: React.FC<LivePerformanceDashboardProps> = ({ 
  className = '',
  requestId 
}) => {
  const [performance, setPerformance] = useState<LivePerformance | null>(null);
  const [latestPnl, setLatestPnl] = useState<any>(null);
  const [pnlHistory, setPnlHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Polling for performance updates
  useEffect(() => {
    if (!requestId) {
      setLoading(false);
      return;
    }

    const fetchPerformance = async () => {
      try {
        // Fetch performance data
        const perf = await apiClient.getLivePerformance(requestId);
        setPerformance(perf);
        
        // Fetch latest P&L data (read-only, fast)
        try {
          const pnlResponse = await apiClient.get(API_ENDPOINTS.PNL.LATEST(requestId));
          setLatestPnl(pnlResponse.data);
        } catch (pnlErr) {
          // P&L data might not be available yet, don't fail the whole request
          console.warn('P&L data not available:', pnlErr);
        }
        
        // Fetch P&L history (less frequent)
        try {
          const historyResponse = await apiClient.get(API_ENDPOINTS.PNL.HISTORY(requestId));
          setPnlHistory(historyResponse.data);
        } catch (historyErr) {
          // P&L history might not be available yet, don't fail the whole request
          console.warn('P&L history not available:', historyErr);
        }
        
        setError(null);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch performance data');
      } finally {
        setLoading(false);
      }
    };

    // Initial fetch
    fetchPerformance();

    // Set up polling
    const interval = setInterval(fetchPerformance, POLLING_INTERVALS.LIVE_STATUS);
    return () => clearInterval(interval);
  }, [requestId]);

  const getPnlColor = (value: number) => {
    if (value > 0) return 'text-green-600';
    if (value < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  const getPnlBgColor = (value: number) => {
    if (value > 0) return 'bg-green-50';
    if (value < 0) return 'bg-red-50';
    return 'bg-gray-50';
  };

  if (loading) {
    return (
      <div className={`bg-white shadow rounded-lg ${className}`}>
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Live Performance</h3>
        </div>
        <div className="p-6">
          <div className="animate-pulse">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-20 bg-gray-200 rounded-lg"></div>
              ))}
            </div>
            <div className="h-64 bg-gray-200 rounded-lg"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!requestId) {
    return (
      <div className={`bg-white shadow rounded-lg ${className}`}>
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Live Performance</h3>
        </div>
        <div className="p-6">
          <div className="text-center py-12">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No Live Trading Session</h3>
            <p className="mt-1 text-sm text-gray-500">Start a live trading session to view performance metrics.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white shadow rounded-lg ${className}`}>
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">Live Performance</h3>
          {performance && (
            <div className="text-sm text-gray-500">
              Last updated: {formatDateTime(performance.last_updated)}
            </div>
          )}
        </div>
        <p className="text-sm text-gray-500">Real-time performance metrics and statistics</p>
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

        {performance && (
          <div className="space-y-6">
            {/* Key Metrics Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className={`rounded-lg p-4 ${getPnlBgColor(performance.total_pnl)}`}>
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <svg className="h-6 w-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <div className={`text-lg font-semibold ${getPnlColor(performance.total_pnl)}`}>
                      {formatCurrency(performance.total_pnl)}
                    </div>
                    <div className="text-sm text-gray-500">Total P&L</div>
                  </div>
                </div>
              </div>

              <div className={`rounded-lg p-4 ${getPnlBgColor(performance.daily_pnl)}`}>
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <svg className="h-6 w-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <div className={`text-lg font-semibold ${getPnlColor(performance.daily_pnl)}`}>
                      {formatCurrency(performance.daily_pnl)}
                    </div>
                    <div className="text-sm text-gray-500">Daily P&L</div>
                  </div>
                </div>
              </div>

              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <svg className="h-6 w-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <div className="text-lg font-semibold text-gray-900">
                      {performance.total_trades}
                    </div>
                    <div className="text-sm text-gray-500">Total Trades</div>
                  </div>
                </div>
              </div>

              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <svg className="h-6 w-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <div className="text-lg font-semibold text-gray-900">
                      {formatPercentage(performance.win_rate)}
                    </div>
                    <div className="text-sm text-gray-500">Win Rate</div>
                  </div>
                </div>
              </div>
            </div>

            {/* P&L Data Section */}
            {latestPnl && (
              <div className="bg-blue-50 rounded-lg p-4">
                <h4 className="text-lg font-medium text-blue-900 mb-3">Latest P&L Data</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-blue-700">Balance-based P&L</div>
                    <div className="text-xl font-semibold text-blue-900">
                      {formatCurrency(latestPnl.balance_based?.pnl_cumulative || 0)}
                    </div>
                    <div className="text-sm text-blue-600">
                      {formatPercentage(latestPnl.balance_based?.pnl_pct || 0)} return
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-blue-700">Attribution P&L</div>
                    <div className="text-xl font-semibold text-blue-900">
                      {formatCurrency(latestPnl.attribution?.pnl_cumulative || 0)}
                    </div>
                    <div className="text-sm text-blue-600">
                      Reconciliation: {latestPnl.reconciliation?.passed ? '✅ PASSED' : '⚠️ FAILED'}
                    </div>
                  </div>
                </div>
                {pnlHistory.length > 0 && (
                  <div className="mt-3">
                    <div className="text-sm text-blue-700">P&L History</div>
                    <div className="text-sm text-blue-600">
                      {pnlHistory.length} historical records available
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Performance Statistics */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="text-sm text-gray-500">Sharpe Ratio</div>
                <div className="text-2xl font-semibold text-gray-900">
                  {performance.sharpe_ratio.toFixed(2)}
                </div>
              </div>

              <div className="bg-gray-50 rounded-lg p-4">
                <div className="text-sm text-gray-500">Max Drawdown</div>
                <div className="text-2xl font-semibold text-red-600">
                  {formatPercentage(performance.max_drawdown)}
                </div>
              </div>

              <div className="bg-gray-50 rounded-lg p-4">
                <div className="text-sm text-gray-500">Current Capital</div>
                <div className="text-2xl font-semibold text-gray-900">
                  {formatCurrency(performance.current_capital)}
                </div>
              </div>
            </div>

            {/* Performance Chart Placeholder */}
            <div className="bg-gray-50 rounded-lg p-6">
              <h4 className="text-sm font-medium text-gray-900 mb-4">Performance Chart</h4>
              <div className="h-64 flex items-center justify-center border-2 border-dashed border-gray-300 rounded-lg">
                <div className="text-center">
                  <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  <p className="mt-2 text-sm text-gray-500">Performance chart will be displayed here</p>
                  <p className="text-xs text-gray-400">Integration with existing ChartsGrid component</p>
                </div>
              </div>
            </div>

            {/* Request Information */}
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="text-sm font-medium text-gray-900 mb-2">Session Information</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">Request ID:</span>
                  <span className="ml-2 font-mono text-gray-900">{performance.request_id}</span>
                </div>
                <div>
                  <span className="text-gray-500">Last Updated:</span>
                  <span className="ml-2 text-gray-900">{formatDateTime(performance.last_updated)}</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

