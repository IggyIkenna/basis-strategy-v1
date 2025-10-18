# Utility Manager Component Specification

**Last Reviewed**: October 16, 2025

## Purpose
Provide centralized utility methods for conversions, calculations, and data transformations used across all components.

## 📚 **Canonical Sources**

**This component spec aligns with canonical architectural principles**:
- **Instrument Definitions**: [../INSTRUMENT_DEFINITIONS.md](../INSTRUMENT_DEFINITIONS.md) - Canonical position key format (`venue:position_type:symbol`)
- **Architectural Principles**: [../REFERENCE_ARCHITECTURE_CANONICAL.md](../REFERENCE_ARCHITECTURE_CANONICAL.md) - Core principles including config-driven architecture
- **Strategy Specifications**: [../MODES.md](../MODES.md) - Strategy mode definitions
- **Configuration Guide**: [19_CONFIGURATION.md](19_CONFIGURATION.md) - Complete config schemas
- **Component Index**: [../COMPONENT_SPECS_INDEX.md](../COMPONENT_SPECS_INDEX.md) - All 20 components (11 core + 9 supporting)

## Responsibilities
1. **Funding Rate Calculations**: Calculate funding payments for perpetual positions
2. **Staking Reward Calculations**: Calculate staking rewards for LST positions
3. **Token Conversions**: Convert between aTokens, debtTokens, and base tokens
4. **Price Data Access**: Provide centralized access to market prices
5. **Index Data Access**: Provide access to AAVE supply/borrow indexes
6. **Rate Data Access**: Provide access to funding rates and staking APRs

## State
- `config`: Dict - Strategy configuration (reference, never modified)
- `data_provider`: BaseDataProvider - Reference for market data queries

## Component References (Set at Init)
The following are set once during initialization and NEVER passed as runtime parameters:

- `config`: Dict (reference, never modified)
- `data_provider`: BaseDataProvider (reference for market data, funding rates, etc.)

These references are stored in `__init__` and used throughout component lifecycle.
Components NEVER receive these as method parameters during runtime.

## Public Methods

### `get_instrument_type(position_key: str) -> str`

**Purpose**: Get instrument type classification from position key for PnL aggregation, reporting, plotting, equity calculation, and LTV calculation.

**Parameters**:
- `position_key`: Position key in format "venue:position_type:symbol" (e.g., "binance:BaseToken:BTC")

**Returns**: Instrument type classification:
- `'asset'`: BaseToken, aToken, LST positions (owned value)
- `'debt'`: debtToken positions (borrowed value)  
- `'derivative'`: Perp positions (synthetic positions)
- `'unknown'`: Invalid or unrecognized position key

**Implementation**:
```python
def get_instrument_type(self, position_key: str) -> str:
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

**Usage Examples**:
- `get_instrument_type("binance:BaseToken:BTC")` → `'asset'`
- `get_instrument_type("aave_v3:aToken:aUSDT")` → `'asset'`
- `get_instrument_type("etherfi:LST:weETH")` → `'asset'`
- `get_instrument_type("aave_v3:debtToken:debtETH")` → `'debt'`
- `get_instrument_type("binance:Perp:BTCUSDT")` → `'derivative'`

### `calculate_funding_payment(position_key: str, position_size: float, timestamp: pd.Timestamp) -> float`

**Purpose**: Calculate funding payment for perpetual position.

**Parameters**:
- `position_key`: Position key in format "venue:Perp:symbol" (e.g., "binance:Perp:BTCUSDT")
- `position_size`: Position size in base units (negative = short, positive = long)
- `timestamp`: Current timestamp for funding rate lookup

**Returns**: Funding payment in USDT (positive = receive, negative = pay)

**Implementation**:
```python
def calculate_funding_payment(
    self, 
    position_key: str,
    position_size: float,
    timestamp: pd.Timestamp
) -> float:
    """
    Calculate funding payment for perp position.
    
    Args:
        position_key: e.g., "binance:Perp:BTCUSDT"
        position_size: Position size in base units (negative = short)
        timestamp: Current timestamp
        
    Returns:
        Funding payment in USDT (positive = receive, negative = pay)
    """
    # Extract venue and symbol
    parts = position_key.split(':')
    venue = parts[0]
    symbol = parts[2]
    
    # Get funding rate from data provider
    funding_rate = self._get_funding_rate(venue, symbol, timestamp)
    
    # Get mark price from data provider
    mark_price = self._get_mark_price(venue, symbol, timestamp)
    
    # Calculate position notional
    position_notional = abs(position_size) * mark_price
    
    # Calculate funding payment
    # Short position: receive if rate > 0, pay if rate < 0
    # Long position: pay if rate > 0, receive if rate < 0
    if position_size < 0:  # Short
        funding_payment = position_notional * funding_rate
    else:  # Long
        funding_payment = -position_notional * funding_rate
    
    return funding_payment
```

**Usage**: Called by Position Monitor during funding settlement generation in backtest mode.

### `calculate_staking_rewards(position_key: str, position_size: float, timestamp: pd.Timestamp) -> Dict[str, float]`

**Purpose**: Calculate staking rewards for LST position including seasonal distributions.

**Parameters**:
- `position_key`: Position key in format "venue:aToken:symbol" (e.g., "etherfi:aToken:weETH")
- `position_size`: Position size in token units
- `timestamp`: Current timestamp for reward rate lookup

**Returns**: Dict mapping reward token to amount (e.g., {'EIGEN': 0.1, 'ETHFI': 0.05})

**Implementation**:
```python
def calculate_staking_rewards(
    self,
    position_key: str,
    position_size: float,
    timestamp: pd.Timestamp
) -> Dict[str, float]:
    """
    Calculate staking rewards for LST position including seasonal distributions.
    
    Args:
        position_key: e.g., "etherfi:aToken:weETH"
        position_size: Position size in token units
        timestamp: Current timestamp
        
    Returns:
        Dict mapping reward token to amount (e.g., {'EIGEN': 0.1, 'ETHFI': 0.05})
    """
    # Extract venue and token
    parts = position_key.split(':')
    venue = parts[0]
    token = parts[2]
    
    # Get base staking yield
    annual_apr = self._get_staking_apr(venue, token, timestamp)
    base_yield = position_size * (annual_apr / 365.0)  # Daily yield
    
    # Get seasonal rewards from data provider
    seasonal_rewards = self._get_seasonal_rewards(venue, token, timestamp, position_size)
    
    # Combine base yield and seasonal rewards
    total_rewards = {'base_yield': base_yield}
    total_rewards.update(seasonal_rewards)
    
    return total_rewards
```

**Usage**: Called by Position Monitor during seasonal rewards settlement generation in backtest mode. Returns Dict with reward tokens (EIGEN, ETHFI, etc.) and amounts for distribution to wallet positions.

### `convert_atoken_to_base(atoken_amount: float, token: str, timestamp: pd.Timestamp) -> float`

**Purpose**: Convert aToken amount to base token amount using AAVE supply index.

**Parameters**:
- `atoken_amount`: Amount in aToken units
- `token`: Base token symbol (e.g., "WETH")
- `timestamp`: Current timestamp for index lookup

**Returns**: Amount in base token units

**Implementation**:
```python
def convert_atoken_to_base(
    self,
    atoken_amount: float,
    token: str,
    timestamp: pd.Timestamp
) -> float:
    """
    Convert aToken amount to base token amount using supply index.
    
    Example: aWETH -> WETH
    """
    supply_index = self._get_aave_supply_index(token, timestamp)
    return atoken_amount / supply_index
```

**Usage**: Called by Exposure Monitor for aToken position conversions.

### `convert_base_to_atoken(base_amount: float, token: str, timestamp: pd.Timestamp) -> float`

**Purpose**: Convert base token amount to aToken amount using AAVE supply index.

**Parameters**:
- `base_amount`: Amount in base token units
- `token`: Base token symbol (e.g., "WETH")
- `timestamp`: Current timestamp for index lookup

**Returns**: Amount in aToken units

**Implementation**:
```python
def convert_base_to_atoken(
    self,
    base_amount: float,
    token: str,
    timestamp: pd.Timestamp
) -> float:
    """
    Convert base token amount to aToken amount using supply index.
    
    Example: WETH -> aWETH
    """
    supply_index = self._get_aave_supply_index(token, timestamp)
    return base_amount * supply_index
```

**Usage**: Called by Exposure Monitor for base token to aToken conversions.

### `convert_debt_to_base(debt_amount: float, token: str, timestamp: pd.Timestamp) -> float`

**Purpose**: Convert debtToken amount to base token amount using AAVE borrow index.

**Parameters**:
- `debt_amount`: Amount in debtToken units
- `token`: Base token symbol (e.g., "USDT")
- `timestamp`: Current timestamp for index lookup

**Returns**: Amount in base token units

**Implementation**:
```python
def convert_debt_to_base(
    self,
    debt_amount: float,
    token: str,
    timestamp: pd.Timestamp
) -> float:
    """
    Convert debtToken amount to base token amount using borrow index.
    
    Example: debtUSDT -> USDT
    """
    borrow_index = self._get_aave_borrow_index(token, timestamp)
    return debt_amount / borrow_index
```

**Usage**: Called by Exposure Monitor for debtToken position conversions.

## Private Helper Methods

### `_get_funding_rate(venue: str, symbol: str, timestamp: pd.Timestamp) -> float`

**Purpose**: Get funding rate from data provider.

**Implementation**:
```python
def _get_funding_rate(self, venue: str, symbol: str, timestamp: pd.Timestamp) -> float:
    """Get funding rate from data provider."""
    data = self.data_provider.get_data(timestamp)
    funding_rates = data['market_data']['rates']['funding']
    
    # Look up funding rate for venue:symbol
    rate_key = f"{venue}:{symbol}"
    if rate_key not in funding_rates:
        raise ValueError(f"Funding rate not found for {rate_key}")
    
    return funding_rates[rate_key]
```

### `_get_mark_price(venue: str, symbol: str, timestamp: pd.Timestamp) -> float`

**Purpose**: Get mark price from data provider.

**Implementation**:
```python
def _get_mark_price(self, venue: str, symbol: str, timestamp: pd.Timestamp) -> float:
    """Get mark price from data provider."""
    data = self.data_provider.get_data(timestamp)
    prices = data['market_data']['prices']
    
    # Look up mark price
    price_key = f"{venue}:{symbol}"
    if price_key not in prices:
        raise ValueError(f"Price not found for {price_key}")
    
    return prices[price_key]
```

### `_get_staking_apr(venue: str, token: str, timestamp: pd.Timestamp) -> float`

**Purpose**: Get staking APR from data provider or config.

**Implementation**:
```python
def _get_staking_apr(self, venue: str, token: str, timestamp: pd.Timestamp) -> float:
    """Get staking APR from data provider or config."""
    data = self.data_provider.get_data(timestamp)
    staking_data = data.get('staking_data', {})
    apr_data = staking_data.get('apr', {})
    
    # Look up APR for venue:token
    apr_key = f"{venue}:{token}"
    if apr_key in apr_data:
        return apr_data[apr_key]
    
    # Fallback to config if not in data provider
    staking_config = self.config.get('staking_rates', {})
    if apr_key in staking_config:
        return staking_config[apr_key]
    
    raise ValueError(f"Staking APR not found for {apr_key}")
```

### `_get_aave_supply_index(token: str, timestamp: pd.Timestamp) -> float`

**Purpose**: Get AAVE supply index from data provider.

**Implementation**:
```python
def _get_aave_supply_index(self, token: str, timestamp: pd.Timestamp) -> float:
    """Get AAVE supply index from data provider."""
    data = self.data_provider.get_data(timestamp)
    protocol_data = data.get('protocol_data', {})
    aave_indexes = protocol_data.get('aave_indexes', {})
    
    supply_key = f"supply:{token}"
    if supply_key not in aave_indexes:
        raise ValueError(f"Supply index not found for {token}")
    
    return aave_indexes[supply_key]
```

### `_get_aave_borrow_index(token: str, timestamp: pd.Timestamp) -> float`

**Purpose**: Get AAVE borrow index from data provider.

**Implementation**:
```python
def _get_aave_borrow_index(self, token: str, timestamp: pd.Timestamp) -> float:
    """Get AAVE borrow index from data provider."""
    data = self.data_provider.get_data(timestamp)
    protocol_data = data.get('protocol_data', {})
    aave_indexes = protocol_data.get('aave_indexes', {})
    
    borrow_key = f"borrow:{token}"
    if borrow_key not in aave_indexes:
        raise ValueError(f"Borrow index not found for {token}")
    
    return aave_indexes[borrow_key]
```

## Error Handling

### Missing Data Errors
```python
# Missing funding rate
if rate_key not in funding_rates:
    raise ValueError(f"Funding rate not found for {rate_key}")

# Missing price data
if price_key not in prices:
    raise ValueError(f"Price not found for {price_key}")

# Missing staking APR
if apr_key not in apr_data and apr_key not in staking_config:
    raise ValueError(f"Staking APR not found for {apr_key}")
```

## Testing Approach

### Unit Tests
- Test funding payment calculations (short vs long positions)
- Test staking reward calculations (weekly vs daily)
- Test aToken/debtToken conversions
- Test error handling for missing data

### Integration Tests
- Test integration with data provider
- Test integration with Position Monitor
- Test integration with Exposure Monitor

## Related Components

- **Position Monitor** (01): Uses funding/rewards calculations for settlements
- **Exposure Monitor** (02): Uses token conversions for exposure calculations
- **Data Provider** (09): Provides market data, rates, and indexes

## References

- [01_POSITION_MONITOR.md](01_POSITION_MONITOR.md) - Position Monitor spec with utility manager integration details
- [09_DATA_PROVIDER.md](09_DATA_PROVIDER.md) - Data Provider spec
- [WORKFLOW_GUIDE.md](../WORKFLOW_GUIDE.md) - Complete workflow guide including utility manager usage

