# Mock Data for Frontend Development

This directory contains mock data and services for frontend development without requiring a running backend.

## Overview

The mock system provides:
- **Realistic data**: Based on actual backend response formats
- **Complete coverage**: All API endpoints supported
- **Large scale testing**: Event logs with 1000+ events for virtualization
- **Edge cases**: Error responses, empty states, loading states
- **Visual variety**: Different chart types, metric ranges, PnL scenarios

## Usage

### Enable Mock Mode

Set the environment variable to enable mock mode:

```bash
# Development with mocks (no backend needed)
VITE_USE_MOCK_API=true npm run dev

# Development with real backend
VITE_USE_MOCK_API=false npm run dev

# Or set in .env.development
VITE_USE_MOCK_API=true
```

### Mock Data Structure

```
src/mocks/
├── data/
│   ├── backtest/
│   │   ├── result.json          # Complete backtest result with metrics
│   │   ├── events.json          # Event log data (sample of 1000 events)
│   │   └── charts.json          # Chart HTML snippets
│   ├── live/
│   │   ├── status.json          # Live trading status
│   │   ├── performance.json     # Live performance metrics
│   │   └── strategies.json      # Running strategies list
│   ├── strategies/
│   │   ├── modes.json           # Available strategy modes
│   │   └── details.json         # Mode details by name
│   └── auth/
│       ├── login-success.json   # Successful login response
│       └── login-error.json     # Failed login response
├── mockApi.ts                   # Mock API service implementation
└── README.md                    # This file
```

## Available Mock Endpoints

### Authentication
- `POST /auth/login` - User authentication
- `POST /auth/logout` - User logout
- `GET /auth/me` - Get current user

**Mock Credentials:**
- Username: `admin`
- Password: `Admin123`

### Backtest
- `POST /backtest/run` - Start backtest execution
- `GET /backtest/{id}/status` - Get backtest status
- `GET /backtest/{id}/result` - Get backtest results
- `DELETE /backtest/{id}` - Cancel backtest

### Results
- `GET /results/` - List all results
- `GET /results/{id}` - Get specific result
- `GET /results/{id}/events` - Get event log with pagination
- `GET /results/{id}/download` - Download ZIP file

### Live Trading
- `POST /live/start` - Start live trading
- `GET /live/status/{id}` - Get live trading status
- `GET /live/performance/{id}` - Get performance metrics
- `POST /live/stop/{id}` - Stop live trading
- `POST /live/emergency-stop/{id}` - Emergency stop
- `POST /live/rebalance` - Manual rebalancing

### Strategies
- `GET /strategies/` - List available strategies
- `GET /strategies/{name}` - Get strategy details
- `GET /strategies/modes/` - List available modes
- `GET /strategies/modes/{name}` - Get mode configuration

### Capital Management
- `POST /capital/deposit` - Deposit funds
- `POST /capital/withdraw` - Withdraw funds

### Health
- `GET /health` - Fast health check
- `GET /health/detailed` - Comprehensive health status

### Charts
- `GET /results/{id}/charts` - Get chart links

## Mock Data Characteristics

### Backtest Results
- **Complete metrics**: 12 performance metrics including Sharpe ratio, max drawdown, etc.
- **13 charts**: Equity curve, PnL attribution, component performance, etc.
- **Realistic values**: Based on actual DeFi yield ranges
- **Multiple scenarios**: Different APY ranges and risk levels

### Event Logs
- **1000+ events**: For testing virtualization performance
- **Event types**: Position updates, trade executions, PnL updates, risk checks
- **Pagination**: Full pagination support with realistic page sizes
- **Rich data**: Balance snapshots, trade details, risk metrics

### Strategy Modes
- **All 7 modes**: Complete coverage of all strategy modes
- **Parameter validation**: Realistic parameter ranges and types
- **Share class filtering**: USDT and ETH share classes
- **Complexity levels**: Simple, medium, and complex strategies

### Live Trading
- **Real-time data**: Status updates, performance metrics
- **Position tracking**: Active positions across multiple venues
- **Risk monitoring**: Real-time risk metrics and health factors
- **Performance attribution**: Component and venue-level performance

## Adding New Mock Data

### 1. Create JSON Data File

Add your mock data to the appropriate directory:

```json
// src/mocks/data/your-endpoint/response.json
{
  "field1": "value1",
  "field2": "value2"
}
```

### 2. Update Mock API Service

Add the endpoint to `mockApi.ts`:

```typescript
async yourEndpoint(): Promise<YourResponseType> {
  await this.delay();
  return yourMockData;
}
```

### 3. Import Mock Data

Import your mock data at the top of `mockApi.ts`:

```typescript
import yourMockData from './data/your-endpoint/response.json';
```

### 4. Test the Endpoint

Verify the mock endpoint works:

```bash
VITE_USE_MOCK_API=true npm run dev
```

## Benefits

### Development Workflow
- **No backend dependency**: Frontend developers can work independently
- **Fast iteration**: No need to wait for backend changes
- **Consistent data**: Predictable responses for UI testing
- **Edge case testing**: Easy to test error states and edge cases

### Testing
- **Unit tests**: Mock data for component testing
- **Integration tests**: Full API simulation
- **Performance testing**: Large datasets for virtualization testing
- **Error handling**: Various error scenarios

### UI Development
- **Visual preview**: See how UI looks with realistic data
- **Responsive testing**: Test with different data sizes
- **Loading states**: Simulate network delays
- **Error states**: Test error handling and recovery

## Network Simulation

The mock API includes realistic network delays:
- **Default delay**: 300ms to simulate network latency
- **Configurable**: Adjust `mockDelay` in `MockApiService`
- **Realistic**: Mimics real API response times

## Data Updates

When backend API changes:
1. Update corresponding mock data files
2. Update TypeScript interfaces in `types/index.ts`
3. Update mock API service methods
4. Test with mock mode enabled

## Troubleshooting

### Mock Mode Not Working
- Check `VITE_USE_MOCK_API=true` is set
- Verify environment variable is loaded: `console.log(import.meta.env.VITE_USE_MOCK_API)`
- Check browser console for import errors

### Missing Endpoints
- Add endpoint to `MockApiService` class
- Create corresponding mock data file
- Import and use mock data in the method

### Type Errors
- Update TypeScript interfaces in `types/index.ts`
- Ensure mock data matches interface definitions
- Check for missing required fields

## Performance Notes

- **Initial load**: Mock data is bundled with the app (small impact)
- **Memory usage**: JSON data is loaded once and reused
- **Network simulation**: Delays are configurable for testing
- **Large datasets**: Event logs support 1000+ events efficiently
