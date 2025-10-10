# Task 28: Live Trading UI Implementation

**Priority**: HIGH  
**Estimated Time**: 6-8 hours  
**Dependencies**: Task 27 (Authentication System)  
**Day**: 6 (Frontend & Live Mode Completion)

## Overview
Implement the live trading UI components for starting/stopping live trading, monitoring status, and managing capital deposits/withdrawals.

## Requirements

### Live Trading UI Components
- **LiveTradingPanel.tsx** - Main live trading control panel
- **CapitalManagement.tsx** - Deposit/withdraw functionality
- **StatusMonitor.tsx** - Real-time status display and health monitoring
- **LivePerformanceDashboard.tsx** - Live performance metrics and charts

### Live Trading Features
- Start/stop live trading with confirmation dialogs
- Real-time status monitoring with 60-second polling
- Capital deposit/withdraw requests with rebalancing triggers
- Live performance metrics display
- Health monitoring with component status
- Emergency stop functionality
- Manual rebalancing triggers

## Implementation Details

### LiveTradingPanel.tsx
```typescript
// frontend/src/components/live/LiveTradingPanel.tsx
import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Play, Square, AlertTriangle, RefreshCw } from 'lucide-react';

interface LiveTradingStatus {
  is_running: boolean;
  request_id: string;
  strategy_name: string;
  start_time: string;
  current_capital: number;
  total_pnl: number;
  health_status: 'healthy' | 'warning' | 'critical';
}

export const LiveTradingPanel: React.FC = () => {
  const [status, setStatus] = useState<LiveTradingStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { user } = useAuth();

  useEffect(() => {
    if (user) {
      fetchLiveStatus();
      const interval = setInterval(fetchLiveStatus, 60000); // 60 seconds
      return () => clearInterval(interval);
    }
  }, [user]);

  const fetchLiveStatus = async () => {
    try {
      const response = await fetch('/api/v1/live/status/current');
      if (response.ok) {
        const data = await response.json();
        setStatus(data);
      }
    } catch (err) {
      console.error('Failed to fetch live status:', err);
    }
  };

  const startLiveTrading = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await fetch('/api/v1/live/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          strategy_name: 'btc_basis',
          initial_capital: 10000,
          share_class: 'usdt'
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to start live trading');
      }

      await fetchLiveStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const stopLiveTrading = async () => {
    if (!status?.request_id) return;
    
    setLoading(true);
    setError('');
    
    try {
      const response = await fetch(`/api/v1/live/stop/${status.request_id}`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error('Failed to stop live trading');
      }

      await fetchLiveStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const emergencyStop = async () => {
    if (!status?.request_id) return;
    
    if (!confirm('Are you sure you want to emergency stop? This will close all positions immediately.')) {
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      const response = await fetch(`/api/v1/live/emergency-stop/${status.request_id}`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error('Failed to emergency stop');
      }

      await fetchLiveStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const triggerRebalance = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await fetch('/api/v1/live/rebalance', {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error('Failed to trigger rebalance');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Live Trading Controls</h2>
        
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        <div className="flex space-x-4">
          {!status?.is_running ? (
            <button
              onClick={startLiveTrading}
              disabled={loading}
              className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
            >
              <Play className="w-4 h-4 mr-2" />
              {loading ? 'Starting...' : 'Start Live Trading'}
            </button>
          ) : (
            <>
              <button
                onClick={stopLiveTrading}
                disabled={loading}
                className="flex items-center px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700 disabled:opacity-50"
              >
                <Square className="w-4 h-4 mr-2" />
                {loading ? 'Stopping...' : 'Stop Trading'}
              </button>
              
              <button
                onClick={emergencyStop}
                disabled={loading}
                className="flex items-center px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50"
              >
                <AlertTriangle className="w-4 h-4 mr-2" />
                Emergency Stop
              </button>
              
              <button
                onClick={triggerRebalance}
                disabled={loading}
                className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Trigger Rebalance
              </button>
            </>
          )}
        </div>
      </div>

      {status && (
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Live Trading Status</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-gray-500">Status</p>
              <p className={`text-lg font-medium ${
                status.is_running ? 'text-green-600' : 'text-gray-600'
              }`}>
                {status.is_running ? 'Running' : 'Stopped'}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Strategy</p>
              <p className="text-lg font-medium text-gray-900">{status.strategy_name}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Health</p>
              <p className={`text-lg font-medium ${
                status.health_status === 'healthy' ? 'text-green-600' :
                status.health_status === 'warning' ? 'text-yellow-600' : 'text-red-600'
              }`}>
                {status.health_status}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
```

### CapitalManagement.tsx
```typescript
// frontend/src/components/live/CapitalManagement.tsx
import React, { useState } from 'react';
import { Plus, Minus } from 'lucide-react';

interface CapitalRequest {
  amount: number;
  type: 'deposit' | 'withdraw';
}

export const CapitalManagement: React.FC = () => {
  const [amount, setAmount] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleDeposit = async () => {
    if (!amount || parseFloat(amount) <= 0) {
      setError('Please enter a valid amount');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await fetch('/api/v1/capital/deposit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount: parseFloat(amount) }),
      });

      if (!response.ok) {
        throw new Error('Failed to process deposit');
      }

      setSuccess('Deposit request submitted successfully');
      setAmount('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const handleWithdraw = async () => {
    if (!amount || parseFloat(amount) <= 0) {
      setError('Please enter a valid amount');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await fetch('/api/v1/capital/withdraw', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount: parseFloat(amount) }),
      });

      if (!response.ok) {
        throw new Error('Failed to process withdrawal');
      }

      setSuccess('Withdrawal request submitted successfully');
      setAmount('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h2 className="text-lg font-medium text-gray-900 mb-4">Capital Management</h2>
      
      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      {success && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-md">
          <p className="text-green-800">{success}</p>
        </div>
      )}

      <div className="space-y-4">
        <div>
          <label htmlFor="amount" className="block text-sm font-medium text-gray-700">
            Amount (USDT)
          </label>
          <input
            type="number"
            id="amount"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            placeholder="Enter amount"
            min="0"
            step="0.01"
          />
        </div>

        <div className="flex space-x-4">
          <button
            onClick={handleDeposit}
            disabled={loading}
            className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
          >
            <Plus className="w-4 h-4 mr-2" />
            {loading ? 'Processing...' : 'Deposit'}
          </button>
          
          <button
            onClick={handleWithdraw}
            disabled={loading}
            className="flex items-center px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50"
          >
            <Minus className="w-4 h-4 mr-2" />
            {loading ? 'Processing...' : 'Withdraw'}
          </button>
        </div>
      </div>
    </div>
  );
};
```

### StatusMonitor.tsx
```typescript
// frontend/src/components/live/StatusMonitor.tsx
import React, { useState, useEffect } from 'react';
import { Activity, AlertCircle, CheckCircle, XCircle } from 'lucide-react';

interface ComponentHealth {
  component: string;
  status: 'healthy' | 'warning' | 'critical';
  last_update: string;
  message?: string;
}

interface LiveStatus {
  is_running: boolean;
  request_id: string;
  strategy_name: string;
  start_time: string;
  current_capital: number;
  total_pnl: number;
  health_status: 'healthy' | 'warning' | 'critical';
  component_health: ComponentHealth[];
}

export const StatusMonitor: React.FC = () => {
  const [status, setStatus] = useState<LiveStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 60000); // 60 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchStatus = async () => {
    try {
      const response = await fetch('/api/v1/live/status/current');
      if (response.ok) {
        const data = await response.json();
        setStatus(data);
      }
    } catch (err) {
      console.error('Failed to fetch status:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'warning':
        return <AlertCircle className="w-5 h-5 text-yellow-500" />;
      case 'critical':
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return <Activity className="w-5 h-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'text-green-600';
      case 'warning':
        return 'text-yellow-600';
      case 'critical':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  if (loading) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            <div className="h-3 bg-gray-200 rounded"></div>
            <div className="h-3 bg-gray-200 rounded"></div>
            <div className="h-3 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h2 className="text-lg font-medium text-gray-900 mb-4">System Status</h2>
      
      {status && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-500">Overall Status</p>
              <div className="flex items-center space-x-2">
                {getStatusIcon(status.health_status)}
                <p className={`text-lg font-medium ${getStatusColor(status.health_status)}`}>
                  {status.health_status}
                </p>
              </div>
            </div>
            <div>
              <p className="text-sm text-gray-500">Current Capital</p>
              <p className="text-lg font-medium text-gray-900">
                ${status.current_capital.toLocaleString()}
              </p>
            </div>
          </div>

          <div>
            <h3 className="text-md font-medium text-gray-900 mb-2">Component Health</h3>
            <div className="space-y-2">
              {status.component_health.map((component) => (
                <div key={component.component} className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                  <div className="flex items-center space-x-3">
                    {getStatusIcon(component.status)}
                    <span className="font-medium text-gray-900">{component.component}</span>
                  </div>
                  <div className="text-right">
                    <p className={`text-sm ${getStatusColor(component.status)}`}>
                      {component.status}
                    </p>
                    {component.message && (
                      <p className="text-xs text-gray-500">{component.message}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
```

## Success Criteria
- [ ] Live trading start/stop functionality working
- [ ] Real-time status monitoring with 60-second polling
- [ ] Capital deposit/withdraw requests with confirmation
- [ ] Emergency stop functionality with confirmation dialog
- [ ] Manual rebalancing trigger
- [ ] Component health monitoring display
- [ ] Loading states and error handling
- [ ] Responsive design for mobile and desktop

## Testing Requirements
- [ ] Unit tests for all live trading components
- [ ] Integration tests for API interactions
- [ ] E2E tests for complete live trading workflow
- [ ] Error handling tests for network failures

## Files to Create/Modify
- `frontend/src/components/live/LiveTradingPanel.tsx` - New live trading control panel
- `frontend/src/components/live/CapitalManagement.tsx` - New capital management component
- `frontend/src/components/live/StatusMonitor.tsx` - New status monitoring component
- `frontend/src/components/live/LivePerformanceDashboard.tsx` - New performance dashboard
- `frontend/src/App.tsx` - Add live trading routes and navigation
- `backend/src/basis_strategy_v1/api/routes/capital.py` - New capital management endpoints

## Notes
- Real-time updates use 60-second polling (not WebSocket for MVP)
- All API calls include proper error handling and loading states
- Confirmation dialogs for destructive actions (stop, emergency stop)
- Responsive design works on mobile and desktop
- Integration with existing authentication system

