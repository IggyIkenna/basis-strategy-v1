# Testing Position Monitor Event Logging

**Purpose**: Verify that Position Monitor logs initial capital and position delta events correctly

**Last Updated**: October 16, 2025

## Overview

The Position Monitor now logs detailed events for:
1. **Initial Capital Application**: When backtest starts with initial capital
2. **Position Delta Events**: Every position change (trades, settlements, etc.)

All events are logged via the structured logger with rich metadata for debugging and monitoring.

## Quick Start

### Option 1: Run Test Script (Easiest)

```bash
# From project root
./test_initial_capital_logging.sh
```

This script will:
- Suppress quality gates automatically
- Start backend in backtest mode
- Run a minimal pure lending backtest (1 day)
- Show you where to find the logs

### Option 2: Manual Testing

```bash
# Step 1: Start backend with quality gates suppressed
SKIP_QUALITY_GATES=true ./platform.sh backtest

# Step 2: In another terminal, run a backtest
curl -X POST "http://localhost:8001/api/v1/backtest/" \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_name": "pure_lending_usdt",
    "share_class": "USDT",
    "initial_capital": 100000,
    "start_date": "2024-05-12T00:00:00Z",
    "end_date": "2024-05-13T00:00:00Z"
  }'

# Step 3: Check logs for events
tail -f backend/logs/api.log | grep -E "(initial_capital|position_delta)"
```

## Event Log Structure

### Initial Capital Event

```json
{
  "timestamp": "2024-05-12T00:00:00",
  "level": "INFO",
  "component": "position_monitor",
  "event_type": "initial_capital_applied",
  "message": "Initial capital applied: 100000 USDT",
  "metadata": {
    "amount": 100000,
    "share_class": "USDT",
    "position_key": "wallet:BaseToken:USDT",
    "timestamp": "2024-05-12T00:00:00Z"
  }
}
```

### Position Delta Event

```json
{
  "timestamp": "2024-05-12T00:00:00",
  "level": "INFO",
  "component": "position_monitor",
  "event_type": "position_delta_applied",
  "message": "Position delta applied: wallet:BaseToken:USDT",
  "metadata": {
    "position_key": "wallet:BaseToken:USDT",
    "delta_amount": 100000.0,
    "source": "initial_capital",
    "old_amount": 0.0,
    "new_amount": 100000.0,
    "price": null,
    "fee": null,
    "timestamp": "2024-05-12T00:00:00Z"
  }
}
```

## What to Look For

### 1. Initial Capital Application (First Event)

**Expected**: At the very first timestep of the backtest, you should see:
- Event type: `initial_capital_applied`
- Amount: 100,000 USDT (or whatever you specified)
- Position key: `wallet:BaseToken:USDT` (for USDT share class)
- Position key: `wallet:BaseToken:ETH` (for ETH share class)

### 2. Position Delta for Initial Capital

**Expected**: Immediately after initial capital event:
- Event type: `position_delta_applied`
- Delta amount: +100,000
- Source: `initial_capital`
- Old amount: 0
- New amount: 100,000

### 3. Subsequent Position Deltas

**Expected**: As strategy executes trades/settlements:
- Event type: `position_delta_applied`
- Source: `trade`, `transfer`, `funding_settlement`, `seasonal_rewards`, etc.
- Includes execution price and fees when applicable

## Log Locations

### Current Implementation

Logs currently go to **stdout** via structlog, which means:
- **Non-Docker**: `backend/logs/api.log` (captured by platform.sh)
- **Docker**: `docker compose logs backend`

### Filtering Logs

```bash
# Show only position monitor events
tail -f backend/logs/api.log | grep '"component":"position_monitor"'

# Show only initial capital events
tail -f backend/logs/api.log | grep '"event_type":"initial_capital_applied"'

# Show only position delta events
tail -f backend/logs/api.log | grep '"event_type":"position_delta_applied"'

# Show all position events (both types)
tail -f backend/logs/api.log | grep -E '(initial_capital_applied|position_delta_applied)'
```

### Future: Component-Specific Log Files

According to the Position Monitor spec (docs/specs/01_POSITION_MONITOR.md), component-specific logs should eventually be written to:
- `logs/events/position_monitor_events.jsonl`

This would require configuring a file handler for the structlog logger, which is currently configured to write to stdout only.

## Troubleshooting

### Issue: No logs appearing

**Check**:
1. Backend is running: `curl http://localhost:8001/health/`
2. Backtest completed: Check API response
3. Log level is INFO or DEBUG: Check `BASIS_LOG_LEVEL` in env.dev

**Solution**:
```bash
# Restart backend with DEBUG logging
BASIS_LOG_LEVEL=DEBUG SKIP_QUALITY_GATES=true ./platform.sh backtest
```

### Issue: Events not showing in grep

**Reason**: Logs are buffered and may not appear immediately

**Solution**:
```bash
# Use unbuffered output
tail -f backend/logs/api.log | grep --line-buffered "position_monitor"
```

### Issue: Backend fails to start

**Reason**: Quality gates failing or missing data

**Solution**:
```bash
# Check quality gate errors
python3 scripts/run_quality_gates.py --category configuration

# Or skip quality gates entirely
SKIP_QUALITY_GATES=true ./platform.sh backtest
```

## Quality Gate Toggle

### Usage

```bash
# Skip quality gates (development/testing)
SKIP_QUALITY_GATES=true ./platform.sh backtest

# Run with quality gates (default, production)
./platform.sh backtest

# Set for entire session
export SKIP_QUALITY_GATES=true
./platform.sh backtest
```

### When to Skip Quality Gates

**Skip for**:
- Local development and testing
- Quick iteration cycles
- When you know quality gates will fail temporarily

**Don't skip for**:
- Production deployments
- CI/CD pipelines
- Final testing before merge

### Environment Variable

| Variable | Values | Default | Description |
|----------|--------|---------|-------------|
| `SKIP_QUALITY_GATES` | `true` / `false` | `false` | Skip quality gate validation if `true` |

## Testing Different Share Classes

### USDT Share Class (Default)

```bash
curl -X POST "http://localhost:8001/api/v1/backtest/" \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_name": "pure_lending_usdt",
    "share_class": "USDT",
    "initial_capital": 100000
  }'
```

**Expected**: `position_key: wallet:BaseToken:USDT`

### ETH Share Class

```bash
curl -X POST "http://localhost:8001/api/v1/backtest/" \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_name": "eth_staking_only",
    "share_class": "ETH",
    "initial_capital": 100
  }'
```

**Expected**: `position_key: wallet:BaseToken:ETH`

## Architecture Notes

### Event Flow

```
EventDrivenStrategyEngine
  ↓ (timestamp, 'position_refresh')
PositionUpdateHandler.update_state()
  ↓
PositionMonitor.update_state(timestamp, 'position_refresh')
  ↓
_query_venue_balances(timestamp)
  ↓ (if backtest mode and no positions)
_generate_initial_capital_deltas()
  ↓
_apply_position_deltas(timestamp, deltas)
  ↓
structured_logger.info("Initial capital applied", event_type="initial_capital_applied")
structured_logger.info("Position delta applied", event_type="position_delta_applied")
```

### Logging Architecture

- **Standard Logger**: Python's `logging` module for debug messages
- **Structured Logger**: `structlog` for structured JSON events
- **Component-Specific**: Each component has its own structured logger instance
- **Event Logger**: Centralized event logging for business events

### Canonical Sources

- **Position Monitor Spec**: docs/specs/01_POSITION_MONITOR.md
- **Reference Architecture**: docs/REFERENCE_ARCHITECTURE_CANONICAL.md
- **Event Logger Spec**: docs/specs/08_EVENT_LOGGER.md
- **Workflow Guide**: docs/WORKFLOW_GUIDE.md

## Next Steps

1. **Verify Events**: Run test script and confirm events appear in logs
2. **Test Different Strategies**: Try BTC basis, ETH leveraged, etc.
3. **Monitor Production**: Use these events for production monitoring
4. **File-Based Logging** (Future): Configure file handlers for component-specific log files

---

**Status**: ✅ Implemented and ready for testing
**Last Updated**: October 16, 2025


