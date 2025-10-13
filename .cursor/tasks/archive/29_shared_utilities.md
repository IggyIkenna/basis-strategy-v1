# Task 29: Shared Utilities Implementation

**Priority**: MEDIUM  
**Estimated Time**: 4-6 hours  
**Dependencies**: None  
**Day**: 6 (Frontend & Live Mode Completion)

## Overview
Implement shared utilities for the frontend including centralized API client, TypeScript interfaces, and utility functions for formatting, validation, and common operations.

## QUALITY GATE
**Quality Gate Script**: `scripts/test_mode_agnostic_design_quality_gates.py`
**Validation**: Shared utilities, centralized functions, mode-agnostic design
**Status**: 🟡 GENERIC

## Requirements

### Shared Utilities Components
- **services/api.ts** - Centralized API client with retry logic and error handling
- **types/*.ts** - TypeScript interfaces for API responses and data structures
- **utils/*.ts** - Utility functions for formatting, validation, and common operations

### API Client Features
- Centralized API calls with consistent error handling
- Retry logic for 503 errors and network failures
- Request/response interceptors for authentication
- Type-safe API calls with TypeScript interfaces
- Loading state management
- Error message standardization

## Implementation Details

### services/api.ts
```typescript
// frontend/src/services/api.ts
import { useAuth } from '../contexts/AuthContext';

interface ApiResponse<T> {
  success: boolean;
  data: T;
  correlation_id?: string;
  message?: string;
}

interface ApiError {
  message: string;
  status: number;
  correlation_id?: string;
}

class ApiClient {
  private baseUrl: string;
  private maxRetries: number = 3;
  private retryDelay: number = 1000;

  constructor(baseUrl: string = '/api/v1') {
    this.baseUrl = baseUrl;
  }

  private async getAuthToken(): Promise<string | null> {
    return localStorage.getItem('token');
  }

  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {},
    retryCount: number = 0
  ): Promise<T> {
    const token = await this.getAuthToken();
    
    const config: RequestInit = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
        ...options.headers,
      },
    };

    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, config);
      
      if (!response.ok) {
        if (response.status === 503 && retryCount < this.maxRetries) {
          // Retry on 503 errors
          await this.delay(this.retryDelay * Math.pow(2, retryCount));
          return this.makeRequest<T>(endpoint, options, retryCount + 1);
        }
        
        const errorData = await response.json().catch(() => ({}));
        throw new ApiError({
          message: errorData.message || `HTTP ${response.status}: ${response.statusText}`,
          status: response.status,
          correlation_id: errorData.correlation_id,
        });
      }

      const data = await response.json();
      return data;
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      
      // Network error - retry if possible
      if (retryCount < this.maxRetries) {
        await this.delay(this.retryDelay * Math.pow(2, retryCount));
        return this.makeRequest<T>(endpoint, options, retryCount + 1);
      }
      
      throw new ApiError({
        message: 'Network error - please check your connection',
        status: 0,
      });
    }
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // Backtest API
  async runBacktest(config: BacktestConfig): Promise<BacktestResponse> {
    return this.makeRequest<BacktestResponse>('/backtest/run', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async getBacktestStatus(id: string): Promise<BacktestStatus> {
    return this.makeRequest<BacktestStatus>(`/backtest/${id}/status`);
  }

  async getBacktestResult(id: string): Promise<BacktestResult> {
    return this.makeRequest<BacktestResult>(`/backtest/${id}/result`);
  }

  async cancelBacktest(id: string): Promise<void> {
    return this.makeRequest<void>(`/backtest/${id}`, {
      method: 'DELETE',
    });
  }

  // Results API
  async getResults(): Promise<ResultSummary[]> {
    return this.makeRequest<ResultSummary[]>('/results/');
  }

  async getResult(id: string): Promise<BacktestResult> {
    return this.makeRequest<BacktestResult>(`/results/${id}`);
  }

  async getResultEvents(id: string, page: number = 1, limit: number = 100): Promise<EventLogResponse> {
    return this.makeRequest<EventLogResponse>(`/results/${id}/events?page=${page}&limit=${limit}`);
  }

  async downloadResult(id: string): Promise<Blob> {
    const response = await fetch(`${this.baseUrl}/results/${id}/download`, {
      headers: {
        Authorization: `Bearer ${await this.getAuthToken()}`,
      },
    });
    
    if (!response.ok) {
      throw new Error('Failed to download result');
    }
    
    return response.blob();
  }

  // Live Trading API
  async startLiveTrading(config: LiveTradingConfig): Promise<LiveTradingResponse> {
    return this.makeRequest<LiveTradingResponse>('/live/start', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async getLiveStatus(id: string): Promise<LiveTradingStatus> {
    return this.makeRequest<LiveTradingStatus>(`/live/status/${id}`);
  }

  async getLivePerformance(id: string): Promise<LivePerformance> {
    return this.makeRequest<LivePerformance>(`/live/performance/${id}`);
  }

  async stopLiveTrading(id: string): Promise<void> {
    return this.makeRequest<void>(`/live/stop/${id}`, {
      method: 'POST',
    });
  }

  async emergencyStopLiveTrading(id: string): Promise<void> {
    return this.makeRequest<void>(`/live/emergency-stop/${id}`, {
      method: 'POST',
    });
  }

  async triggerRebalance(): Promise<void> {
    return this.makeRequest<void>('/live/rebalance', {
      method: 'POST',
    });
  }

  // Strategy API
  async getStrategies(): Promise<Strategy[]> {
    return this.makeRequest<Strategy[]>('/strategies/');
  }

  async getStrategy(name: string): Promise<Strategy> {
    return this.makeRequest<Strategy>(`/strategies/${name}`);
  }

  async getModes(shareClass?: string): Promise<Mode[]> {
    const params = shareClass ? `?share_class=${shareClass}` : '';
    return this.makeRequest<Mode[]>(`/strategies/modes/${params}`);
  }

  async getMode(name: string): Promise<Mode> {
    return this.makeRequest<Mode>(`/strategies/modes/${name}`);
  }

  // Capital Management API
  async depositCapital(amount: number): Promise<void> {
    return this.makeRequest<void>('/capital/deposit', {
      method: 'POST',
      body: JSON.stringify({ amount }),
    });
  }

  async withdrawCapital(amount: number): Promise<void> {
    return this.makeRequest<void>('/capital/withdraw', {
      method: 'POST',
      body: JSON.stringify({ amount }),
    });
  }

  // Health API
  async getHealth(): Promise<HealthStatus> {
    return this.makeRequest<HealthStatus>('/health');
  }

  async getDetailedHealth(): Promise<DetailedHealthStatus> {
    return this.makeRequest<DetailedHealthStatus>('/health/detailed');
  }
}

export const apiClient = new ApiClient();
export default apiClient;
```

### types/index.ts
```typescript
// frontend/src/types/index.ts
export interface BacktestConfig {
  share_class: 'usdt' | 'eth';
  mode_name: string;
  initial_capital: number;
  start_date: string;
  end_date: string;
  strategy_config: Record<string, any>;
}

export interface BacktestResponse {
  request_id: string;
  message: string;
}

export interface BacktestStatus {
  request_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress?: number;
  message?: string;
  started_at?: string;
  completed_at?: string;
}

export interface BacktestResult {
  request_id: string;
  strategy_name: string;
  start_date: string;
  end_date: string;
  initial_capital: number;
  final_value: number;
  total_return: number;
  annualized_return: number;
  sharpe_ratio: number;
  max_drawdown: number;
  total_trades: number;
  total_fees: number;
  equity_curve?: any[];
  metrics_summary: Record<string, any>;
  chart_links: Record<string, string>;
}

export interface ResultSummary {
  id: string;
  strategy_name: string;
  start_date: string;
  end_date: string;
  initial_capital: number;
  final_value: number;
  total_return: number;
  created_at: string;
}

export interface EventLogResponse {
  events: EventLogEntry[];
  total_count: number;
  page: number;
  limit: number;
  has_more: boolean;
}

export interface EventLogEntry {
  timestamp: string;
  event_type: string;
  component: string;
  message: string;
  data?: Record<string, any>;
  balance_snapshot?: Record<string, any>;
}

export interface LiveTradingConfig {
  strategy_name: string;
  initial_capital: number;
  share_class: 'usdt' | 'eth';
}

export interface LiveTradingResponse {
  request_id: string;
  message: string;
}

export interface LiveTradingStatus {
  is_running: boolean;
  request_id: string;
  strategy_name: string;
  start_time: string;
  current_capital: number;
  total_pnl: number;
  health_status: 'healthy' | 'warning' | 'critical';
  component_health: ComponentHealth[];
}

export interface LivePerformance {
  request_id: string;
  current_capital: number;
  total_pnl: number;
  daily_pnl: number;
  total_trades: number;
  win_rate: number;
  sharpe_ratio: number;
  max_drawdown: number;
  last_updated: string;
}

export interface ComponentHealth {
  component: string;
  status: 'healthy' | 'warning' | 'critical';
  last_update: string;
  message?: string;
}

export interface Strategy {
  name: string;
  description: string;
  share_classes: string[];
  modes: string[];
}

export interface Mode {
  name: string;
  description: string;
  share_class: string;
  strategy_name: string;
  estimated_apy: number;
  risk_level: 'low' | 'medium' | 'high';
  complexity: 'simple' | 'medium' | 'complex';
  parameters: ModeParameter[];
}

export interface ModeParameter {
  name: string;
  type: 'number' | 'select' | 'boolean';
  label: string;
  description: string;
  required: boolean;
  default_value?: any;
  min_value?: number;
  max_value?: number;
  step?: number;
  options?: { value: any; label: string }[];
}

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  version: string;
  uptime: number;
}

export interface DetailedHealthStatus extends HealthStatus {
  components: ComponentHealth[];
  system_info: {
    cpu_usage: number;
    memory_usage: number;
    disk_usage: number;
  };
}

export interface ApiError {
  message: string;
  status: number;
  correlation_id?: string;
}
```

### utils/formatters.ts
```typescript
// frontend/src/utils/formatters.ts
import { format, parseISO } from 'date-fns';

export const formatCurrency = (amount: number, currency: string = 'USD'): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
};

export const formatPercentage = (value: number, decimals: number = 2): string => {
  return `${(value * 100).toFixed(decimals)}%`;
};

export const formatNumber = (value: number, decimals: number = 2): string => {
  return value.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
};

export const formatDate = (dateString: string, formatString: string = 'MMM dd, yyyy'): string => {
  try {
    const date = parseISO(dateString);
    return format(date, formatString);
  } catch (error) {
    return dateString;
  }
};

export const formatDateTime = (dateString: string): string => {
  return formatDate(dateString, 'MMM dd, yyyy HH:mm:ss');
};

export const formatRelativeTime = (dateString: string): string => {
  try {
    const date = parseISO(dateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
    
    if (diffInSeconds < 60) {
      return `${diffInSeconds}s ago`;
    } else if (diffInSeconds < 3600) {
      return `${Math.floor(diffInSeconds / 60)}m ago`;
    } else if (diffInSeconds < 86400) {
      return `${Math.floor(diffInSeconds / 3600)}h ago`;
    } else {
      return `${Math.floor(diffInSeconds / 86400)}d ago`;
    }
  } catch (error) {
    return dateString;
  }
};

export const formatFileSize = (bytes: number): string => {
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  if (bytes === 0) return '0 Bytes';
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
};
```

### utils/validators.ts
```typescript
// frontend/src/utils/validators.ts
export const validateEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

export const validatePassword = (password: string): { valid: boolean; message?: string } => {
  if (password.length < 8) {
    return { valid: false, message: 'Password must be at least 8 characters long' };
  }
  if (!/[A-Z]/.test(password)) {
    return { valid: false, message: 'Password must contain at least one uppercase letter' };
  }
  if (!/[a-z]/.test(password)) {
    return { valid: false, message: 'Password must contain at least one lowercase letter' };
  }
  if (!/\d/.test(password)) {
    return { valid: false, message: 'Password must contain at least one number' };
  }
  return { valid: true };
};

export const validateCapitalAmount = (amount: number, min: number = 100, max: number = 1000000): { valid: boolean; message?: string } => {
  if (amount < min) {
    return { valid: false, message: `Minimum capital amount is $${min.toLocaleString()}` };
  }
  if (amount > max) {
    return { valid: false, message: `Maximum capital amount is $${max.toLocaleString()}` };
  }
  return { valid: true };
};

export const validateDateRange = (startDate: string, endDate: string): { valid: boolean; message?: string } => {
  const start = new Date(startDate);
  const end = new Date(endDate);
  const now = new Date();
  
  if (start >= end) {
    return { valid: false, message: 'End date must be after start date' };
  }
  
  if (start >= now) {
    return { valid: false, message: 'Start date must be in the past' };
  }
  
  const daysDiff = (end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24);
  if (daysDiff > 365) {
    return { valid: false, message: 'Date range cannot exceed 1 year' };
  }
  
  return { valid: true };
};

export const validateRequired = (value: any, fieldName: string): { valid: boolean; message?: string } => {
  if (value === null || value === undefined || value === '') {
    return { valid: false, message: `${fieldName} is required` };
  }
  return { valid: true };
};
```

### utils/constants.ts
```typescript
// frontend/src/utils/constants.ts
export const API_ENDPOINTS = {
  BACKTEST: {
    RUN: '/backtest/run',
    STATUS: (id: string) => `/backtest/${id}/status`,
    RESULT: (id: string) => `/backtest/${id}/result`,
    CANCEL: (id: string) => `/backtest/${id}`,
  },
  RESULTS: {
    LIST: '/results/',
    GET: (id: string) => `/results/${id}`,
    EVENTS: (id: string) => `/results/${id}/events`,
    DOWNLOAD: (id: string) => `/results/${id}/download`,
  },
  LIVE: {
    START: '/live/start',
    STATUS: (id: string) => `/live/status/${id}`,
    PERFORMANCE: (id: string) => `/live/performance/${id}`,
    STOP: (id: string) => `/live/stop/${id}`,
    EMERGENCY_STOP: (id: string) => `/live/emergency-stop/${id}`,
    REBALANCE: '/live/rebalance',
  },
  STRATEGIES: {
    LIST: '/strategies/',
    GET: (name: string) => `/strategies/${name}`,
    MODES: '/strategies/modes/',
    MODE: (name: string) => `/strategies/modes/${name}`,
  },
  CAPITAL: {
    DEPOSIT: '/capital/deposit',
    WITHDRAW: '/capital/withdraw',
  },
  HEALTH: {
    BASIC: '/health',
    DETAILED: '/health/detailed',
  },
} as const;

export const SHARE_CLASSES = {
  USDT: 'usdt',
  ETH: 'eth',
} as const;

export const RISK_LEVELS = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
} as const;

export const COMPLEXITY_LEVELS = {
  SIMPLE: 'simple',
  MEDIUM: 'medium',
  COMPLEX: 'complex',
} as const;

export const HEALTH_STATUS = {
  HEALTHY: 'healthy',
  WARNING: 'warning',
  CRITICAL: 'critical',
} as const;

export const BACKTEST_STATUS = {
  PENDING: 'pending',
  RUNNING: 'running',
  COMPLETED: 'completed',
  FAILED: 'failed',
  CANCELLED: 'cancelled',
} as const;

export const POLLING_INTERVALS = {
  LIVE_STATUS: 60000, // 60 seconds
  BACKTEST_STATUS: 5000, // 5 seconds
  HEALTH_CHECK: 30000, // 30 seconds
} as const;

export const VALIDATION_LIMITS = {
  MIN_CAPITAL: 100,
  MAX_CAPITAL: 1000000,
  MAX_DATE_RANGE_DAYS: 365,
  MIN_PASSWORD_LENGTH: 8,
} as const;
```

## Success Criteria
- [ ] Centralized API client with retry logic implemented
- [ ] TypeScript interfaces for all API responses
- [ ] Utility functions for formatting, validation, and constants
- [ ] Error handling with standardized error messages
- [ ] Authentication token management
- [ ] Loading state management
- [ ] Type-safe API calls throughout the application

## Testing Requirements
- [ ] Unit tests for API client methods
- [ ] Unit tests for utility functions
- [ ] Integration tests for API error handling
- [ ] Mock API responses for testing

## Files to Create/Modify
- `frontend/src/services/api.ts` - New centralized API client
- `frontend/src/types/index.ts` - New TypeScript interfaces
- `frontend/src/utils/formatters.ts` - New formatting utilities
- `frontend/src/utils/validators.ts` - New validation utilities
- `frontend/src/utils/constants.ts` - New constants file
- `frontend/src/components/**/*.tsx` - Update all components to use new API client

## Notes
- API client includes automatic retry logic for 503 errors
- All API calls are type-safe with TypeScript interfaces
- Error handling is consistent across all API calls
- Authentication tokens are automatically included in requests
- Utility functions are reusable across all components
- Constants are centralized for easy maintenance


