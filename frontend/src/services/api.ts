// Centralized API client with retry logic and error handling

import { 
  ApiResponse, 
  // ApiError, 
  LoginRequest, 
  LoginResponse, 
  User,
  BacktestConfig,
  BacktestResponse,
  BacktestStatus,
  BacktestResult,
  ResultSummary,
  EventLogResponse,
  LiveTradingConfig,
  LiveTradingResponse,
  LiveTradingStatus,
  LivePerformance,
  Strategy,
  Mode,
  HealthStatus,
  DetailedHealthStatus,
  DepositRequest,
  WithdrawRequest,
  CapitalResponse,
  PositionSnapshot,
  PositionUpdate,
  ChartsResponse
} from '../types';

// Local ApiError interface
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

  // Authentication API
  async login(request: LoginRequest): Promise<LoginResponse> {
    return this.makeRequest<LoginResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async logout(): Promise<{ message: string }> {
    return this.makeRequest<{ message: string }>('/auth/logout', {
      method: 'POST',
    });
  }

  async getCurrentUser(): Promise<User> {
    return this.makeRequest<User>('/auth/me');
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
  async depositCapital(request: DepositRequest): Promise<CapitalResponse> {
    return this.makeRequest<CapitalResponse>('/capital/deposit', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async withdrawCapital(request: WithdrawRequest): Promise<CapitalResponse> {
    return this.makeRequest<CapitalResponse>('/capital/withdraw', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Position Management API
  async getCurrentPositions(): Promise<PositionSnapshot> {
    return this.makeRequest<PositionSnapshot>('/positions/current');
  }

  async updatePosition(update: PositionUpdate): Promise<{ message: string }> {
    return this.makeRequest<{ message: string }>('/positions/update', {
      method: 'POST',
      body: JSON.stringify(update),
    });
  }

  // Health API
  async getHealth(): Promise<HealthStatus> {
    return this.makeRequest<HealthStatus>('/health');
  }

  async getDetailedHealth(): Promise<DetailedHealthStatus> {
    return this.makeRequest<DetailedHealthStatus>('/health/detailed');
  }

  // Charts API
  async getCharts(requestId: string): Promise<ChartsResponse> {
    return this.makeRequest<ChartsResponse>(`/results/${requestId}/charts`);
  }
}

// Mock API client for development/testing
export class MockApiClient extends ApiClient {
  private mockDelay: number = 500; // Simulate network delay

  private async mockDelay(): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, this.mockDelay));
  }

  async login(request: LoginRequest): Promise<LoginResponse> {
    await this.mockDelay();
    
    if (request.username === 'admin' && request.password === 'admin123') {
      return {
        access_token: 'mock-jwt-token-' + Date.now(),
        token_type: 'bearer',
        expires_in: 1800
      };
    }
    
    throw new ApiError({
      message: 'Invalid credentials',
      status: 401
    });
  }

  async getCurrentUser(): Promise<User> {
    await this.mockDelay();
    return {
      username: 'admin',
      authenticated: true
    };
  }

  async getHealth(): Promise<HealthStatus> {
    await this.mockDelay();
    return {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      version: '1.0.0',
      uptime: 3600
    };
  }

  async getDetailedHealth(): Promise<DetailedHealthStatus> {
    await this.mockDelay();
    return {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      version: '1.0.0',
      uptime: 3600,
      components: [
        {
          component: 'position_monitor',
          status: 'healthy',
          last_update: new Date().toISOString()
        },
        {
          component: 'data_provider',
          status: 'healthy',
          last_update: new Date().toISOString()
        }
      ],
      system_info: {
        cpu_usage: 15.2,
        memory_usage: 45.8,
        disk_usage: 23.1
      }
    };
  }

  async getStrategies(): Promise<Strategy[]> {
    await this.mockDelay();
    return [
      {
        name: 'usdt_market_neutral',
        description: 'USDT Market Neutral Strategy',
        share_classes: ['usdt'],
        modes: ['usdt_market_neutral']
      },
      {
        name: 'btc_basis',
        description: 'BTC Basis Trading Strategy',
        share_classes: ['usdt'],
        modes: ['btc_basis']
      }
    ];
  }

  async getModes(shareClass?: string): Promise<Mode[]> {
    await this.mockDelay();
    return [
      {
        name: 'usdt_market_neutral',
        description: 'Market neutral strategy with lending and staking',
        share_class: 'usdt',
        strategy_name: 'usdt_market_neutral',
        estimated_apy: 0.25,
        risk_level: 'high',
        complexity: 'complex',
        parameters: [
          {
            name: 'target_apy',
            type: 'number',
            label: 'Target APY',
            description: 'Target annual percentage yield',
            required: true,
            default_value: 0.25,
            min_value: 0.05,
            max_value: 0.50,
            step: 0.01
          }
        ]
      }
    ];
  }

  async runBacktest(config: BacktestConfig): Promise<BacktestResponse> {
    await this.mockDelay();
    return {
      request_id: 'mock-backtest-' + Date.now(),
      message: 'Backtest started successfully'
    };
  }

  async getBacktestStatus(id: string): Promise<BacktestStatus> {
    await this.mockDelay();
    return {
      request_id: id,
      status: 'completed',
      progress: 100,
      started_at: new Date(Date.now() - 3600000).toISOString(),
      completed_at: new Date().toISOString()
    };
  }

  async getBacktestResult(id: string): Promise<BacktestResult> {
    await this.mockDelay();
    return {
      request_id: id,
      strategy_name: 'usdt_market_neutral',
      start_date: '2024-01-01T00:00:00Z',
      end_date: '2024-01-31T23:59:59Z',
      initial_capital: 100000,
      final_value: 105250,
      total_return: 0.0525,
      annualized_return: 0.68,
      sharpe_ratio: 1.85,
      max_drawdown: 0.023,
      total_trades: 45,
      total_fees: 125.50,
      metrics_summary: {
        win_rate: 0.65,
        profit_factor: 1.8,
        average_trade: 116.67
      },
      chart_links: {
        equity_curve: '/charts/equity_curve.html',
        drawdown: '/charts/drawdown.html',
        pnl_attribution: '/charts/pnl_attribution.html'
      }
    };
  }
}

// Export the appropriate client based on environment variable
export const apiClient = import.meta.env.VITE_API_MODE === 'mock'
  ? new MockApiClient()
  : new ApiClient();

export default apiClient;
