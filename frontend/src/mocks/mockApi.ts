// Mock API service for development and testing
// Uses static JSON files to simulate backend responses

import {
    BacktestConfig,
    BacktestResponse,
    BacktestResult,
    BacktestStatus,
    CapitalResponse,
    ChartsResponse,
    DepositRequest,
    DetailedHealthStatus,
    EventLogResponse,
    HealthStatus,
    LivePerformance,
    LiveTradingConfig,
    LiveTradingResponse,
    LiveTradingStatus,
    LoginRequest,
    LoginResponse,
    Mode,
    PositionSnapshot,
    PositionUpdate,
    ResultSummary,
    Strategy,
    User,
    WithdrawRequest
} from '../types';

// Import mock data
import loginError from './data/auth/login-error.json';
import loginSuccess from './data/auth/login-success.json';
import backtestEvents from './data/backtest/events.json';
import backtestResult from './data/backtest/result.json';
import livePerformance from './data/live/performance.json';
import liveStatus from './data/live/status.json';
import strategyModes from './data/strategies/modes.json';

export class MockApiService {
    private mockDelay: number = 300; // Simulate network delay
    private requestCounter: number = 0;

    private async delay(): Promise<void> {
        return new Promise(resolve => setTimeout(resolve, this.mockDelay));
    }

    private generateRequestId(): string {
        return `mock-${Date.now()}-${++this.requestCounter}`;
    }

    // Authentication API
    async login(request: LoginRequest): Promise<LoginResponse> {
        await this.delay();

        if (request.username === 'admin' && request.password === 'Admin123') {
            return {
                access_token: loginSuccess.access_token,
                token_type: loginSuccess.token_type,
                expires_in: loginSuccess.expires_in
            };
        }

        throw new ApiError({
            message: loginError.message,
            status: loginError.status,
            correlation_id: loginError.correlation_id
        });
    }

    async logout(): Promise<{ message: string }> {
        await this.delay();
        return { message: 'Logged out successfully' };
    }

    async getCurrentUser(): Promise<User> {
        await this.delay();
        return {
            username: loginSuccess.user.username,
            email: loginSuccess.user.email,
            role: loginSuccess.user.role,
            authenticated: true
        };
    }

    // Backtest API
    async runBacktest(config: BacktestConfig): Promise<BacktestResponse> {
        await this.delay();
        return {
            request_id: this.generateRequestId(),
            message: 'Backtest started successfully'
        };
    }

    async getBacktestStatus(id: string): Promise<BacktestStatus> {
        await this.delay();
        return {
            request_id: id,
            status: 'completed',
            progress: 100,
            started_at: new Date(Date.now() - 3600000).toISOString(),
            completed_at: new Date().toISOString()
        };
    }

    async getBacktestResult(id: string): Promise<BacktestResult> {
        await this.delay();
        return {
            ...backtestResult,
            request_id: id
        };
    }

    async cancelBacktest(id: string): Promise<void> {
        await this.delay();
        return;
    }

    // Results API
    async getResults(): Promise<ResultSummary[]> {
        await this.delay();
        return [
            {
                id: 'mock-backtest-001',
                strategy_name: 'usdt_pure_lending_usdt',
                start_date: '2024-01-01T00:00:00Z',
                end_date: '2024-12-31T23:59:59Z',
                initial_capital: 100000,
                final_value: 125430.50,
                total_return: 0.2543,
                created_at: '2024-01-15T10:30:00Z',
                status: 'completed'
            },
            {
                id: 'mock-backtest-002',
                strategy_name: 'usdt_basis_trading_usdt',
                start_date: '2024-01-01T00:00:00Z',
                end_date: '2024-06-30T23:59:59Z',
                initial_capital: 50000,
                final_value: 67500.25,
                total_return: 0.35,
                created_at: '2024-01-10T14:20:00Z',
                status: 'completed'
            }
        ];
    }

    async getResult(id: string): Promise<BacktestResult> {
        await this.delay();
        return {
            ...backtestResult,
            request_id: id
        };
    }

    async getResultEvents(id: string, page: number = 1, limit: number = 100): Promise<EventLogResponse> {
        await this.delay();

        // Simulate pagination
        const startIndex = (page - 1) * limit;
        const endIndex = startIndex + limit;
        const paginatedEvents = backtestEvents.events.slice(startIndex, endIndex);

        return {
            events: paginatedEvents,
            pagination: {
                page,
                limit,
                total: backtestEvents.events.length,
                total_pages: Math.ceil(backtestEvents.events.length / limit)
            }
        };
    }

    async downloadResult(id: string): Promise<Blob> {
        await this.delay();
        // Create a mock ZIP file blob
        const mockZipContent = 'PK\x03\x04\x14\x00\x00\x00\x08\x00mock-zip-content';
        return new Blob([mockZipContent], { type: 'application/zip' });
    }

    // Live Trading API
    async startLiveTrading(config: LiveTradingConfig): Promise<LiveTradingResponse> {
        await this.delay();
        return {
            strategy_id: this.generateRequestId(),
            message: 'Live trading started successfully'
        };
    }

    async getLiveStatus(id: string): Promise<LiveTradingStatus> {
        await this.delay();
        return {
            ...liveStatus,
            strategy_id: id
        };
    }

    async getLivePerformance(id: string): Promise<LivePerformance> {
        await this.delay();
        return {
            ...livePerformance,
            strategy_id: id
        };
    }

    async stopLiveTrading(id: string): Promise<void> {
        await this.delay();
        return;
    }

    async emergencyStopLiveTrading(id: string): Promise<void> {
        await this.delay();
        return;
    }

    async triggerRebalance(): Promise<void> {
        await this.delay();
        return;
    }

    // Strategy API
    async getStrategies(): Promise<Strategy[]> {
        await this.delay();
        return [
            {
                name: 'usdt_pure_lending',
                description: 'Pure lending strategy across multiple DeFi protocols',
                share_classes: ['usdt'],
                modes: ['usdt_pure_lending_usdt']
            },
            {
                name: 'usdt_basis_trading',
                description: 'Basis trading strategy using funding rate arbitrage',
                share_classes: ['usdt'],
                modes: ['usdt_basis_trading_usdt']
            },
            {
                name: 'eth_leveraged_staking',
                description: 'Leveraged staking strategy with optional hedging',
                share_classes: ['eth'],
                modes: ['eth_leveraged_staking_eth']
            }
        ];
    }

    async getStrategy(name: string): Promise<Strategy> {
        await this.delay();
        const strategies = await this.getStrategies();
        const strategy = strategies.find(s => s.name === name);
        if (!strategy) {
            throw new ApiError({
                message: 'Strategy not found',
                status: 404
            });
        }
        return strategy;
    }

    async getModes(shareClass?: string): Promise<Mode[]> {
        await this.delay();
        let modes = strategyModes;

        if (shareClass) {
            modes = modes.filter(mode => mode.share_class === shareClass);
        }

        return modes;
    }

    async getMode(name: string): Promise<Mode> {
        await this.delay();
        const mode = strategyModes.find(m => m.name === name);
        if (!mode) {
            throw new ApiError({
                message: 'Mode not found',
                status: 404
            });
        }
        return mode;
    }

    // Capital Management API
    async depositCapital(request: DepositRequest): Promise<CapitalResponse> {
        await this.delay();
        return {
            transaction_id: this.generateRequestId(),
            amount: request.amount,
            status: 'pending',
            message: 'Deposit request submitted successfully'
        };
    }

    async withdrawCapital(request: WithdrawRequest): Promise<CapitalResponse> {
        await this.delay();
        return {
            transaction_id: this.generateRequestId(),
            amount: request.amount,
            status: 'pending',
            message: 'Withdrawal request submitted successfully'
        };
    }

    // Position Management API
    async getCurrentPositions(): Promise<PositionSnapshot> {
        await this.delay();
        return {
            timestamp: new Date().toISOString(),
            total_value: 100125.50,
            positions: liveStatus.active_positions
        };
    }

    async updatePosition(update: PositionUpdate): Promise<{ message: string }> {
        await this.delay();
        return { message: 'Position updated successfully' };
    }

    // Health API
    async getHealth(): Promise<HealthStatus> {
        await this.delay();
        return {
            status: 'healthy',
            timestamp: new Date().toISOString(),
            service: 'basis-strategy-v1',
            execution_mode: 'backtest',
            uptime_seconds: 3600,
            system: {
                cpu_percent: 15.2,
                memory_percent: 45.8,
                memory_available_gb: 8.5
            }
        };
    }

    async getDetailedHealth(): Promise<DetailedHealthStatus> {
        await this.delay();
        return {
            status: 'healthy',
            timestamp: new Date().toISOString(),
            service: 'basis-strategy-v1',
            execution_mode: 'backtest',
            components: {
                position_monitor: {
                    status: 'healthy',
                    error_code: null,
                    readiness_checks: {
                        initialized: true
                    }
                },
                data_provider: {
                    status: 'healthy',
                    error_code: null,
                    readiness_checks: {
                        initialized: true,
                        data_loaded: true
                    }
                },
                execution_engine: {
                    status: 'healthy',
                    error_code: null,
                    readiness_checks: {
                        initialized: true
                    }
                },
                risk_manager: {
                    status: 'healthy',
                    error_code: null,
                    readiness_checks: {
                        initialized: true
                    }
                },
                pnl_calculator: {
                    status: 'healthy',
                    error_code: null,
                    readiness_checks: {
                        initialized: true
                    }
                }
            },
            summary: {
                total_components: 5,
                healthy_components: 5,
                unhealthy_components: 0
            }
        };
    }

    // Charts API
    async getCharts(requestId: string): Promise<ChartsResponse> {
        await this.delay();
        return {
            request_id: requestId,
            charts: backtestResult.chart_links
        };
    }
}

export default MockApiService;
