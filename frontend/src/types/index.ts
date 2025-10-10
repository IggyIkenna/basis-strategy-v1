// TypeScript interfaces for API responses and data structures

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  correlation_id?: string;
  message?: string;
}

export interface ApiError {
  message: string;
  status: number;
  correlation_id?: string;
}

// Authentication Types
export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface User {
  username: string;
  authenticated: boolean;
}

// Backtest Types
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

// Live Trading Types
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

// Strategy Types
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

// Health Types
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

// Capital Management Types
export interface DepositRequest {
  amount: number;
  currency?: string;
  share_class?: string;
  source?: string;
}

export interface WithdrawRequest {
  amount: number;
  currency?: string;
  share_class?: string;
  withdrawal_type?: 'fast' | 'slow';
}

export interface CapitalResponse {
  id: string;
  amount: number;
  currency: string;
  share_class: string;
  status: string;
  new_total_equity: number;
  timestamp: string;
}

// Position Management Types
export interface PositionSnapshot {
  timestamp: string;
  total_equity: number;
  share_class: string;
  positions: {
    wallet: Record<string, number>;
    cex: Record<string, Record<string, Record<string, number>>>;
    defi: Record<string, Record<string, number>>;
  };
  exposure: {
    net_delta_eth: number;
    net_delta_usdt: number;
    lending_exposure: number;
    staking_exposure: number;
  };
}

export interface PositionUpdate {
  venue: string;
  asset: string;
  amount: number;
  position_type: string;
  reason: string;
}

// Chart Types
export interface ChartInfo {
  name: string;
  title: string;
  file_path: string;
  description: string;
}

export interface ChartsResponse {
  request_id: string;
  available_charts: ChartInfo[];
}

// Constants
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

