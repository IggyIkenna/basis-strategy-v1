// Constants and configuration values

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
  POSITIONS: {
    CURRENT: '/positions/current',
    UPDATE: '/positions/update',
  },
  AUTH: {
    LOGIN: '/auth/login',
    LOGOUT: '/auth/logout',
    ME: '/auth/me',
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
  MIN_USERNAME_LENGTH: 3,
} as const;

export const STRATEGY_NAMES = [
  'usdt_market_neutral',
  'btc_basis',
  'eth_basis',
  'eth_leveraged',
  'pure_lending',
  'eth_staking_only',
  'usdt_market_neutral_no_leverage'
] as const;

export const CHART_TYPES = [
  'equity_curve',
  'drawdown',
  'pnl_attribution',
  'component_performance',
  'fee_breakdown',
  'ltv_ratio',
  'balance_by_venue',
  'balance_by_token',
  'margin_health',
  'exposure'
] as const;

export const EVENT_TYPES = [
  'ORDER_FILLED',
  'POSITION_UPDATE',
  'REBALANCE',
  'DEPOSIT',
  'WITHDRAWAL',
  'RISK_ALERT',
  'SYSTEM_EVENT',
  'ERROR'
] as const;

export const COMPONENT_NAMES = [
  'position_monitor',
  'exposure_monitor',
  'risk_monitor',
  'pnl_calculator',
  'strategy_manager',
  'execution_manager',
  'event_logger',
  'data_provider'
] as const;

export const VENUE_NAMES = [
  'binance',
  'bybit',
  'okx',
  'aave_v3',
  'lido',
  'etherfi',
  'morpho',
  'instadapp'
] as const;

export const TOKEN_NAMES = [
  'ETH',
  'USDT',
  'BTC',
  'weETH',
  'stETH',
  'eETH',
  'aUSDT',
  'aETH'
] as const;

export const ERROR_CODES = {
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  STRATEGY_NOT_FOUND: 'STRATEGY_NOT_FOUND',
  BACKTEST_NOT_FOUND: 'BACKTEST_NOT_FOUND',
  LIVE_TRADING_NOT_FOUND: 'LIVE_TRADING_NOT_FOUND',
  INSUFFICIENT_CAPITAL: 'INSUFFICIENT_CAPITAL',
  VENUE_UNAVAILABLE: 'VENUE_UNAVAILABLE',
  SYSTEM_ERROR: 'SYSTEM_ERROR',
  RATE_LIMIT_EXCEEDED: 'RATE_LIMIT_EXCEEDED',
  AUTHENTICATION_ERROR: 'AUTHENTICATION_ERROR',
  AUTHORIZATION_ERROR: 'AUTHORIZATION_ERROR',
} as const;

export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  RATE_LIMITED: 429,
  INTERNAL_SERVER_ERROR: 500,
  SERVICE_UNAVAILABLE: 503,
} as const;

export const UI_CONSTANTS = {
  MAX_EVENTS_PER_PAGE: 100,
  MAX_RESULTS_PER_PAGE: 1000,
  CHART_HEIGHT: 400,
  MODAL_MAX_WIDTH: '90vw',
  MODAL_MAX_HEIGHT: '90vh',
  TOAST_DURATION: 5000,
  DEBOUNCE_DELAY: 300,
} as const;

