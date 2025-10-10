// Status monitor component for real-time system health and metrics

import React, { useState, useEffect } from 'react';
import { apiClient } from '../../services/api';
import { DetailedHealthStatus, ComponentHealth } from '../../types';
import { formatUptime, formatPercentage } from '../../utils/formatters';
import { POLLING_INTERVALS } from '../../utils/constants';

interface StatusMonitorProps {
  className?: string;
}

export const StatusMonitor: React.FC<StatusMonitorProps> = ({ className = '' }) => {
  const [healthStatus, setHealthStatus] = useState<DetailedHealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Polling for health status updates
  useEffect(() => {
    const fetchHealthStatus = async () => {
      try {
        const status = await apiClient.getDetailedHealth();
        setHealthStatus(status);
        setError(null);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch health status');
      } finally {
        setLoading(false);
      }
    };

    // Initial fetch
    fetchHealthStatus();

    // Set up polling
    const interval = setInterval(fetchHealthStatus, POLLING_INTERVALS.HEALTH_CHECK);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-600 bg-green-100';
      case 'warning': return 'text-yellow-600 bg-yellow-100';
      case 'critical': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getComponentStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return (
          <svg className="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
        );
      case 'warning':
        return (
          <svg className="h-5 w-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        );
      case 'critical':
        return (
          <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
        );
      default:
        return (
          <svg className="h-5 w-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
          </svg>
        );
    }
  };

  const getSystemMetricColor = (value: number, thresholds: { warning: number; critical: number }) => {
    if (value >= thresholds.critical) return 'text-red-600';
    if (value >= thresholds.warning) return 'text-yellow-600';
    return 'text-green-600';
  };

  if (loading) {
    return (
      <div className={`bg-white shadow rounded-lg ${className}`}>
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">System Status</h3>
        </div>
        <div className="p-6">
          <div className="animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
            <div className="h-4 bg-gray-200 rounded w-2/3"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white shadow rounded-lg ${className}`}>
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">System Status</h3>
          <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(healthStatus?.status || 'unknown')}`}>
            {healthStatus?.status.toUpperCase() || 'UNKNOWN'}
          </div>
        </div>
        <p className="text-sm text-gray-500">Real-time system health and performance metrics</p>
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

        {healthStatus && (
          <div className="space-y-6">
            {/* System Information */}
            <div>
              <h4 className="text-sm font-medium text-gray-900 mb-3">System Information</h4>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-gray-50 rounded-lg p-3">
                  <div className="text-sm text-gray-500">Version</div>
                  <div className="text-lg font-semibold text-gray-900">{healthStatus.version}</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <div className="text-sm text-gray-500">Uptime</div>
                  <div className="text-lg font-semibold text-gray-900">{formatUptime(healthStatus.uptime)}</div>
                </div>
              </div>
            </div>

            {/* System Metrics */}
            <div>
              <h4 className="text-sm font-medium text-gray-900 mb-3">System Metrics</h4>
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-gray-50 rounded-lg p-3">
                  <div className="text-sm text-gray-500">CPU Usage</div>
                  <div className={`text-lg font-semibold ${getSystemMetricColor(healthStatus.system_info.cpu_usage, { warning: 70, critical: 90 })}`}>
                    {formatPercentage(healthStatus.system_info.cpu_usage / 100)}
                  </div>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <div className="text-sm text-gray-500">Memory Usage</div>
                  <div className={`text-lg font-semibold ${getSystemMetricColor(healthStatus.system_info.memory_usage, { warning: 80, critical: 95 })}`}>
                    {formatPercentage(healthStatus.system_info.memory_usage / 100)}
                  </div>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <div className="text-sm text-gray-500">Disk Usage</div>
                  <div className={`text-lg font-semibold ${getSystemMetricColor(healthStatus.system_info.disk_usage, { warning: 85, critical: 95 })}`}>
                    {formatPercentage(healthStatus.system_info.disk_usage / 100)}
                  </div>
                </div>
              </div>
            </div>

            {/* Component Health */}
            <div>
              <h4 className="text-sm font-medium text-gray-900 mb-3">Component Health</h4>
              <div className="space-y-2">
                {healthStatus.components.map((component: ComponentHealth) => (
                  <div key={component.component} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center">
                      {getComponentStatusIcon(component.status)}
                      <div className="ml-3">
                        <div className="text-sm font-medium text-gray-900">
                          {component.component.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </div>
                        {component.message && (
                          <div className="text-xs text-gray-500">{component.message}</div>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center">
                      <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(component.status)}`}>
                        {component.status.toUpperCase()}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Last Updated */}
            <div className="text-xs text-gray-500 text-center">
              Last updated: {new Date(healthStatus.timestamp).toLocaleString()}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
