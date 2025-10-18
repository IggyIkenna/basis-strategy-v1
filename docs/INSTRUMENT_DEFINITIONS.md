# Instrument Definitions - Canonical Position Key Format

**Last Updated**: October 16, 2025

## Purpose

This document defines the **canonical format** for all instrument/position identifiers used throughout the Basis Strategy system. All components, documentation, and configuration must use this standard format consistently.

## Canonical Format

```
venue:position_type:symbol
```

### Format Components

1. **venue**: The trading venue or protocol where the position exists
2. **position_type**: The type of position (balance, lending, derivative, etc.)
3. **symbol**: The asset symbol or instrument identifier

### Delimiter

The colon `:` character is the **mandatory** delimiter between components. This enables simple and consistent parsing across the system.

## Position Types

| Position Type | Description | Used For | Examples |
|---------------|-------------|----------|----------|
| `BaseToken` | Native balance at a venue | Wallet balances, CEX spot balances | `wallet:BaseToken:USDT`, `binance:BaseToken:BTC` |
| `aToken` | Lending supply position (AAVE) | AAVE supplied assets | `aave_v3:aToken:aUSDT`, `aave_v3:aToken:aWETH` |
| `debtToken` | Lending borrow position (AAVE) | AAVE borrowed assets | `aave_v3:debtToken:debtETH`, `aave_v3:debtToken:debtUSDT` |
| `LST` | Liquid Staking Token position | Staked assets via liquid staking protocols | `etherfi:LST:weETH`, `lido:LST:stETH` |
| `Perp` | Perpetual futures position | CEX perpetual contracts | `binance:Perp:BTCUSDT`, `bybit:Perp:ETHUSDT` |

### Position Type Details

#### BaseToken
- **Definition**: Raw balance of a token at a venue
- **Usage**: Represents actual token holdings in wallets or exchange accounts
- **Settlement**: Direct 1:1 with underlying asset
- **Examples**:
  - `wallet:BaseToken:ETH` - ETH in on-chain wallet
  - `binance:BaseToken:USDT` - USDT balance on Binance
  - `wallet:BaseToken:USDT` - USDT in on-chain wallet (initial capital)

#### aToken
- **Definition**: Interest-bearing token received when supplying assets to lending protocols
- **Usage**: AAVE aTokens that accrue interest over time
- **Settlement**: Convertible to underlying asset via protocol rules
- **Examples**:
  - `aave_v3:aToken:aUSDT` - AAVE V3 supplied USDT (earns interest)
  - `aave_v3:aToken:aWETH` - AAVE V3 supplied WETH (earns interest)

#### debtToken
- **Definition**: Debt token representing borrowed assets from lending protocols
- **Usage**: AAVE debt positions that accrue interest over time
- **Settlement**: Must be repaid to protocol
- **Examples**:
  - `aave_v3:debtToken:debtETH` - AAVE V3 borrowed ETH (accrues interest)
  - `aave_v3:debtToken:debtUSDT` - AAVE V3 borrowed USDT (accrues interest)

#### Perp
- **Definition**: Perpetual futures contract on centralized exchanges
- **Usage**: Leveraged long/short positions that pay/receive funding
- **Settlement**: Cash-settled based on mark price, funding every 8 hours
- **Examples**:
  - `binance:Perp:BTCUSDT` - Binance BTC perpetual (USDT-margined)
  - `bybit:Perp:ETHUSDT` - Bybit ETH perpetual (USDT-margined)
  - `okx:Perp:BTCUSDT` - OKX BTC perpetual (USDT-margined)

## Venues

| Venue | Type | Description | Position Types Supported |
|-------|------|-------------|-------------------------|
| `wallet` | On-chain | On-chain wallet managed by Alchemy | `BaseToken` |
| `binance` | CEX | Binance centralized exchange | `BaseToken`, `Perp` |
| `bybit` | CEX | Bybit centralized exchange | `BaseToken`, `Perp` |
| `okx` | CEX | OKX centralized exchange | `BaseToken`, `Perp` |
| `aave` | DeFi | AAVE lending protocol (legacy) | `aToken`, `debtToken` |
| `aave_v3` | DeFi | AAVE V3 lending protocol | `aToken`, `debtToken` |
| `etherfi` | DeFi | EtherFi liquid staking protocol | `aToken` (for weETH) |
| `lido` | DeFi | Lido liquid staking protocol | `aToken` (for stETH) |
| `morpho` | DeFi | Morpho lending protocol | `aToken`, `debtToken` |
| `alchemy` | Service | Blockchain API provider for transfers | N/A (transfer only) |

### Venue Details

#### wallet
- **Type**: On-chain wallet
- **Management**: Controlled via Alchemy API
- **Position Types**: `BaseToken` only
- **Usage**: Initial capital, on-chain token balances
- **Examples**:
  - `wallet:BaseToken:ETH`
  - `wallet:BaseToken:USDT`

#### binance / bybit / okx
- **Type**: Centralized Exchange (CEX)
- **Position Types**: `BaseToken` (spot balances), `Perp` (perpetual futures)
- **Usage**: Spot trading, perpetual futures, funding rate collection
- **Funding**: Perpetual positions settle funding every 8 hours at 0/8/16 UTC
- **Examples**:
  - `binance:BaseToken:USDT` - USDT balance on Binance
  - `binance:BaseToken:BTC` - BTC spot balance on Binance
  - `binance:Perp:BTCUSDT` - BTC perpetual position on Binance

#### aave / aave_v3
- **Type**: Decentralized lending protocol
- **Position Types**: `aToken` (supplied), `debtToken` (borrowed)
- **Usage**: Lending, borrowing, leveraged positions
- **Interest**: Accrues continuously based on utilization rates
- **Examples**:
  - `aave_v3:aToken:aUSDT` - Supplied USDT earning interest
  - `aave_v3:debtToken:debtETH` - Borrowed ETH accruing interest

#### etherfi / lido
- **Type**: Liquid staking protocol
- **Position Types**: `aToken` (for LST positions)
- **Usage**: ETH staking with liquid staking tokens
- **Rewards**: Staking rewards accrue automatically
- **Examples**:
  - `etherfi:aToken:weETH` - Staked ETH via EtherFi (wrapped eETH)
  - `lido:aToken:stETH` - Staked ETH via Lido

#### morpho
- **Type**: Decentralized lending optimizer
- **Position Types**: `aToken` (supplied), `debtToken` (borrowed)
- **Usage**: Optimized lending rates on top of AAVE/Compound
- **Examples**:
  - `morpho:aToken:aUSDT` - Supplied USDT via Morpho
  - `morpho:debtToken:debtETH` - Borrowed ETH via Morpho

#### alchemy
- **Type**: Blockchain API service provider
- **Position Types**: None (transfer operations only)
- **Usage**: Execute on-chain transfers between wallet and protocols
- **Note**: Doesn't hold positions, only facilitates transfers

## Symbols

Symbols vary by strategy mode and venue. Below are the valid symbols per strategy mode:

### Pure Lending Mode

| Position Key | Description |
|--------------|-------------|
| `wallet:BaseToken:USDT` | Initial capital in wallet |
| `aave_v3:aToken:aUSDT` | USDT supplied to AAVE |

### BTC Basis Mode

| Position Key | Description |
|--------------|-------------|
| `wallet:BaseToken:USDT` | Initial capital in wallet |
| `binance:BaseToken:USDT` | USDT balance on Binance |
| `binance:BaseToken:BTC` | BTC spot balance on Binance |
| `binance:Perp:BTCUSDT` | BTC perpetual on Binance |
| `bybit:BaseToken:USDT` | USDT balance on Bybit |
| `bybit:Perp:BTCUSDT` | BTC perpetual on Bybit |
| `okx:BaseToken:USDT` | USDT balance on OKX |
| `okx:Perp:BTCUSDT` | BTC perpetual on OKX |

### ETH Basis Mode

| Position Key | Description |
|--------------|-------------|
| `wallet:BaseToken:USDT` | Initial capital in wallet |
| `binance:BaseToken:USDT` | USDT balance on Binance |
| `binance:BaseToken:ETH` | ETH spot balance on Binance |
| `binance:Perp:ETHUSDT` | ETH perpetual on Binance |
| `bybit:BaseToken:USDT` | USDT balance on Bybit |
| `bybit:Perp:ETHUSDT` | ETH perpetual on Bybit |
| `okx:BaseToken:USDT` | USDT balance on OKX |
| `okx:Perp:ETHUSDT` | ETH perpetual on OKX |

### ETH Staking Only Mode

| Position Key | Description |
|--------------|-------------|
| `wallet:BaseToken:ETH` | Initial capital in wallet |
| `etherfi:aToken:weETH` | Staked ETH via EtherFi |

### ETH Leveraged Mode

| Position Key | Description |
|--------------|-------------|
| `wallet:BaseToken:ETH` | Initial capital in wallet |
| `etherfi:aToken:weETH` | Staked ETH via EtherFi |
| `aave_v3:aToken:aWETH` | WETH supplied to AAVE |
| `aave_v3:debtToken:debtETH` | ETH borrowed from AAVE |
| `binance:BaseToken:USDT` | USDT balance on Binance |
| `binance:Perp:ETHUSDT` | ETH perpetual on Binance (hedge) |
| `bybit:BaseToken:USDT` | USDT balance on Bybit |
| `bybit:Perp:ETHUSDT` | ETH perpetual on Bybit (hedge) |
| `okx:BaseToken:USDT` | USDT balance on OKX |
| `okx:Perp:ETHUSDT` | ETH perpetual on OKX (hedge) |

### USDT Market Neutral Mode

| Position Key | Description |
|--------------|-------------|
| `wallet:BaseToken:USDT` | Initial capital in wallet |
| `aave_v3:aToken:aUSDT` | USDT supplied to AAVE |
| `aave_v3:debtToken:debtUSDT` | USDT borrowed from AAVE |
| `binance:BaseToken:USDT` | USDT balance on Binance |
| `binance:BaseToken:BTC` | BTC spot balance on Binance |
| `binance:Perp:BTCUSDT` | BTC perpetual on Binance |
| `bybit:BaseToken:USDT` | USDT balance on Bybit |
| `bybit:Perp:BTCUSDT` | BTC perpetual on Bybit |
| `okx:BaseToken:USDT` | USDT balance on OKX |
| `okx:Perp:BTCUSDT` | BTC perpetual on OKX |

## Position Subscription Architecture

### Config-Driven Instrument Universe

All components share a unified instrument universe defined in `component_config.position_monitor.position_subscriptions`:

```yaml
component_config:
  position_monitor:
    position_subscriptions:
   - "wallet:BaseToken:ETH"      # Entry/exit position
   - "etherfi:LST:weETH"          # Staking position
   - "wallet:BaseToken:EIGEN"     # Dust positions
   - "instadapp:BaseToken:WETH"   # Flash loan intermediary
```

All components (Strategy, Position Monitor, Risk Monitor, Execution Manager, PnL Monitor, Results Store, Position Update Handler) subscribe to this same list.

### Strategy Access Pattern

Strategies query available instruments during initialization:

```python
position_config = config.get('component_config', {}).get('position_monitor', {})
self.available_instruments = position_config.get('position_subscriptions', [])

# Validate required instruments are available
if self.staking_instrument not in self.available_instruments:
    raise ValueError(f"Required instrument {self.staking_instrument} not in config")
```

### Venue-Instrument Validation

Venues define canonical instruments in `configs/venues/*.yaml`:

```yaml
# configs/venues/etherfi.yaml
canonical_instruments:
 - "etherfi:LST:weETH"
```

Pydantic models enforce venue-instrument mappings to prevent querying instruments that don't exist on a venue.

### USDT Market Neutral (No Leverage) Mode

| Position Key | Description |
|--------------|-------------|
| `wallet:BaseToken:USDT` | Initial capital in wallet |
| `aave_v3:aToken:aUSDT` | USDT supplied to AAVE (no borrowing) |
| `binance:BaseToken:USDT` | USDT balance on Binance |
| `binance:BaseToken:BTC` | BTC spot balance on Binance |
| `binance:Perp:BTCUSDT` | BTC perpetual on Binance |
| `bybit:BaseToken:USDT` | USDT balance on Bybit |
| `bybit:Perp:BTCUSDT` | BTC perpetual on Bybit |
| `okx:BaseToken:USDT` | USDT balance on OKX |
| `okx:Perp:BTCUSDT` | BTC perpetual on OKX |

### ML BTC Directional (USDT Margin) Mode

| Position Key | Description |
|--------------|-------------|
| `binance:BaseToken:USDT` | USDT balance on Binance |
| `binance:Perp:BTCUSDT` | BTC perpetual on Binance |
| `bybit:BaseToken:USDT` | USDT balance on Bybit |
| `bybit:Perp:BTCUSDT` | BTC perpetual on Bybit |
| `okx:BaseToken:USDT` | USDT balance on OKX |
| `okx:Perp:BTCUSDT` | BTC perpetual on OKX |

### ML BTC Directional (BTC Margin) Mode

| Position Key | Description |
|--------------|-------------|
| `binance:BaseToken:BTC` | BTC balance on Binance |
| `binance:Perp:BTCUSDT` | BTC perpetual on Binance |
| `bybit:BaseToken:BTC` | BTC balance on Bybit |
| `bybit:Perp:BTCUSDT` | BTC perpetual on Bybit |
| `okx:BaseToken:BTC` | BTC balance on OKX |
| `okx:Perp:BTCUSDT` | BTC perpetual on OKX |

## Parsing Rules

### Standard Parsing
```python
# Parse position key
venue, position_type, symbol = position_key.split(':')

# Example: "binance:Perp:BTCUSDT"
# venue = "binance"
# position_type = "Perp"
# symbol = "BTCUSDT"
```

### Construction
```python
# Construct position key
position_key = f"{venue}:{position_type}:{symbol}"

# Example
venue = "aave_v3"
position_type = "aToken"
symbol = "aUSDT"
position_key = "aave_v3:aToken:aUSDT"
```

### Validation
```python
# Validate format
def is_valid_position_key(position_key: str) -> bool:
    parts = position_key.split(':')
    if len(parts) != 3:
        return False
    venue, position_type, symbol = parts
    if not venue or not position_type or not symbol:
        return False
    return True
```

## Usage in Configuration

Position keys are declared in the `component_config.position_monitor.position_subscriptions` section of mode configuration files:

```yaml
component_config:
  position_monitor:
    position_subscriptions:
      - "wallet:BaseToken:USDT"
      - "binance:BaseToken:USDT"
      - "binance:BaseToken:BTC"
      - "binance:Perp:BTCUSDT"
      - "aave_v3:aToken:aUSDT"
      - "aave_v3:debtToken:debtETH"
```

**Key Requirements**:
- All positions must be pre-declared in `position_subscriptions`
- Position keys must follow exact canonical format
- Any position delta referencing an undeclared position will raise an error
- Live mode filters out any undeclared positions returned by venue APIs

## Usage in Code

### Component State
```python
# Position Monitor
self.simulated_positions: Dict[str, float] = {
    "wallet:BaseToken:USDT": 100000.0,
    "binance:BaseToken:BTC": 1.5,
    "binance:Perp:BTCUSDT": -1.0
}

# Exposure Monitor
exposure_by_position = {
    "binance:BaseToken:BTC": {"usd_value": 75000.0, "quantity": 1.5},
    "binance:Perp:BTCUSDT": {"usd_value": -50000.0, "quantity": -1.0}
}
```

### Position Deltas
```python
# Trade execution delta
{
    "position_key": "binance:BaseToken:BTC",
    "delta_amount": 0.5,
    "source": "trade",
    "price": 50000.0,
    "fee": 25.0
}

# Funding settlement delta
{
    "position_key": "binance:BaseToken:USDT",
    "delta_amount": -5.0,
    "source": "funding_settlement",
    "metadata": {
        "perp_position": "binance:Perp:BTCUSDT",
        "position_size": -1.0
    }
}
```

### Position Queries
```python
# Query specific position
btc_balance = position_monitor.simulated_positions.get("binance:BaseToken:BTC", 0.0)

# Filter positions by venue
binance_positions = {
    k: v for k, v in positions.items() 
    if k.startswith("binance:")
}

# Filter positions by position_type
perp_positions = {
    k: v for k, v in positions.items() 
    if ":Perp:" in k
}

# Extract components
for position_key, amount in positions.items():
    venue, position_type, symbol = position_key.split(':')
    if position_type == "Perp":
        # Process perpetual position
        pass
```

## Anti-Patterns (DO NOT USE)

The following patterns are **NOT** valid and must be avoided:

### Dot Notation
```python
# ❌ WRONG - Dot notation
"wallet.USDT"
"binance.BTC"
"aave.aUSDT"

# ✅ CORRECT - Colon delimiter
"wallet:BaseToken:USDT"
"binance:BaseToken:BTC"
"aave_v3:aToken:aUSDT"
```

### Missing Position Type
```python
# ❌ WRONG - Missing position_type
"wallet:USDT"
"binance:BTC"
"aave:aUSDT"

# ✅ CORRECT - All three components
"wallet:BaseToken:USDT"
"binance:BaseToken:BTC"
"aave_v3:aToken:aUSDT"
```

### Alternative Names
```python
# ❌ WRONG - Using alternative terminology
instrument_id = "binance:BaseToken:BTC"
instrument_key = "wallet:BaseToken:USDT"
position_id = "aave_v3:aToken:aUSDT"

# ✅ CORRECT - Always use position_key
position_key = "binance:BaseToken:BTC"
position_key = "wallet:BaseToken:USDT"
position_key = "aave_v3:aToken:aUSDT"
```

### Wrong Delimiters
```python
# ❌ WRONG - Other delimiters
"binance_BTC_USDT"
"binance/Perp/BTCUSDT"
"binance.Perp.BTCUSDT"

# ✅ CORRECT - Colon only
"binance:Perp:BTCUSDT"
```


## Instrument Type Classification

For PnL aggregation, reporting, plotting, equity calculation, and LTV calculation, instruments are classified by type:

### Position Type to Instrument Type Mapping

| Position Type | Instrument Type | Description |
|---------------|-----------------|-------------|
| `BaseToken` | `asset` | Native token balances (USDT, ETH, BTC) |
| `aToken` | `asset` | AAVE supplied tokens earning interest (aUSDT, aETH) |
| `LST` | `asset` | Liquid staking tokens (stETH, weETH) |
| `debtToken` | `debt` | AAVE borrowed tokens accruing interest (debtUSDT, debtETH) |
| `Perp` | `derivative` | Perpetual futures positions (BTC-PERP, ETH-PERP) |

### Type Definitions

- **Asset**: Instruments representing owned value
  - `BaseToken`: Native tokens (USDT, ETH, BTC)
  - `aToken`: AAVE supplied tokens (aUSDT, aETH)
  - `LST`: Liquid staking tokens (stETH, weETH)

- **Debt**: Instruments representing borrowed value
  - `debtToken`: AAVE borrowed tokens (debtUSDT, debtETH)

- **Derivative**: Instruments representing synthetic positions
  - `Perp`: Perpetual futures positions (BTC-PERP, ETH-PERP)

### Type Mapping Function

```python
def get_instrument_type(position_key: str) -> str:
    """
    Get instrument type classification from position key.
    
    Maps position types to instrument classifications:
    - BaseToken, aToken, LST → 'asset'
    - debtToken → 'debt'
    - Perp → 'derivative'
    
    Args:
        position_key: Position key in format venue:position_type:symbol
        
    Returns:
        Instrument type: 'asset', 'debt', 'derivative', or 'unknown'
    """
    parts = position_key.split(':')
    if len(parts) != 3:
        return 'unknown'
    
    venue, position_type, symbol = parts
    
    type_mapping = {
        'BaseToken': 'asset',
        'aToken': 'asset',
        'LST': 'asset',
        'debtToken': 'debt',
        'Perp': 'derivative'
    }
    
    return type_mapping.get(position_type, 'unknown')
```

### Usage Examples

- **PnL Aggregation**: Sum PnL by instrument type
- **Equity Calculation**: Assets - Debts + Derivative Value
- **LTV Calculation**: Total Debt / Total Assets
- **Reporting**: Group positions by type for clarity

## Migration Guide

### From Old Formats

If you find code using deprecated formats, convert as follows:

| Old Format | New Format |
|------------|------------|
| `wallet.USDT` | `wallet:BaseToken:USDT` |
| `binance.BTC` | `binance:BaseToken:BTC` |
| `aave.aUSDT` | `aave_v3:aToken:aUSDT` |
| `instrument_id` | `position_key` |
| `instrument_key` | `position_key` |
| `position_id` | `position_key` |

### Code Changes
```python
# OLD
instrument_id = "binance:BaseToken:BTC"
venue, symbol = instrument_id.split(':')

# NEW
position_key = "binance:BaseToken:BTC"
venue, position_type, symbol = position_key.split(':')
```

## Data Provider Integration

### Position Key to Data Key Mapping

The system uses standardized conversion from position keys to data provider keys:

#### BaseToken → Prices
```
wallet:BaseToken:BTC → data['market_data']['prices']['BTC']
wallet:BaseToken:ETH → data['market_data']['prices']['ETH']
wallet:BaseToken:USDT → data['market_data']['prices']['USDT'] = 1.0
```

#### Perp → Perp Prices & Funding Rates
```
binance:Perp:BTCUSDT → data['protocol_data']['perp_prices']['BTC_binance']
binance:Perp:BTCUSDT → data['market_data']['funding_rates']['BTC_binance']
bybit:Perp:ETHUSDT → data['protocol_data']['perp_prices']['ETH_bybit']
```

#### LST → Oracle Prices
```
etherfi:LST:weETH → data['protocol_data']['oracle_prices']['weETH/USD']
etherfi:LST:weETH → data['protocol_data']['oracle_prices']['weETH/ETH']
lido:LST:wstETH → data['protocol_data']['oracle_prices']['wstETH/USD']
```

#### aToken/debtToken → AAVE Indexes
```
aave_v3:aToken:aUSDT → data['protocol_data']['aave_indexes']['aUSDT']
aave_v3:debtToken:debtWETH → data['protocol_data']['aave_indexes']['debtWETH']
```

### Conversion Rate Standards

All conversion rates use BASE/QUOTE format:
- **BASE**: Asset being priced (left side)
- **QUOTE**: Currency it's priced in (right side)
- **Value**: Amount of QUOTE per 1 unit of BASE

Example: `weETH/ETH = 1.05` means 1 weETH = 1.05 ETH

### Validation Rules

1. All data keys must correspond to instruments in INSTRUMENTS registry
2. Venue-specific keys must have venue in venue configs
3. Uppercase format mandatory for all asset symbols
4. Conversion rates must use BASE/QUOTE format

## Related Documentation

- **[Position Monitor Specification](specs/01_POSITION_MONITOR.md)** - Component that tracks all positions using these keys
- **[Configuration Guide](specs/19_CONFIGURATION.md)** - How to configure position_subscriptions
- **[Reference Architecture](REFERENCE_ARCHITECTURE_CANONICAL.md)** - System-wide architectural principles
- **[Component Specs Index](COMPONENT_SPECS_INDEX.md)** - All component specifications

## Quality Gates

The system enforces position key format compliance through:

1. **Configuration Validation**: Position subscriptions must match format
2. **Runtime Validation**: Position deltas with invalid keys raise errors
3. **Code Scanning**: Quality gates scan for deprecated patterns
4. **Test Coverage**: All tests must use canonical format

### Validation Scripts

- **`scripts/scan_instrument_key_inconsistencies.py`**: Scans entire codebase for deprecated patterns
- **`scripts/quality_gates/validate_position_key_format.py`**: Validates position key format compliance
- **`tests/quality_gates/run_quality_gates.py`**: Runs all quality gate validations

### Common Issues and Solutions

**Issue**: Using deprecated variable names (`instrument_id`, `instrument_key`, `position_id`)
**Solution**: Replace with `position_key` throughout codebase

**Issue**: Dot notation in position keys (`wallet.USDT`, `binance.BTC`)
**Solution**: Use colon delimiter (`wallet:BaseToken:USDT`, `binance:BaseToken:BTC`)

**Issue**: Missing position_type in keys (`binance:USDT`, `aave:aUSDT`)
**Solution**: Add position_type (`binance:BaseToken:USDT`, `aave_v3:aToken:aUSDT`)

**Issue**: Underscore format (`binance_BTC_USDT`)
**Solution**: Use canonical format (`binance:Perp:BTCUSDT`)

## Summary

- **Format**: `venue:position_type:symbol`
- **Delimiter**: Colon `:` (mandatory)
- **Variable Name**: Always `position_key` (never `instrument_id`, `instrument_key`, `position_id`)
- **Pre-Declaration**: All positions must be declared in `position_subscriptions`
- **Consistency**: Same format across configuration, code, documentation, and tests
- **No Exceptions**: Format is mandatory system-wide

This canonical format ensures consistent, parseable, and maintainable position tracking across the entire Basis Strategy system.


