# Execution Venue Integration

## Overview
Implement comprehensive venue integration for all strategy modes, including CEX venues, DeFi protocols, and infrastructure services with proper atomic transaction support.

## Venue Requirements by Strategy Mode

### CEX Venues (Binance, Bybit, OKX)
**Required for**: BTC Basis, ETH Basis, USDT Market Neutral modes

**Implementation**:
- Spot trading interfaces
- Perpetual futures trading
- Account management and margin monitoring
- Position tracking and PnL calculation

**Key Features**:
- **Spot Trades**: Binance preferred (unless atomic on-chain transaction requires DEX)
- **Perp Shorts**: Distributed based on `hedge_allocation` ratios
- **Allocation Logic**: `hedge_allocation_binance: 0.4`, `hedge_allocation_bybit: 0.3`, `hedge_allocation_okx: 0.3`

### DeFi Venues

#### AAVE V3
**Required for**: Pure Lending, ETH Leveraged, USDT Market Neutral modes

**Implementation**:
- Lending/borrowing interfaces
- Collateral management
- Health factor monitoring
- Flash loan integration

#### Lido/EtherFi
**Required for**: ETH Staking Only, ETH Leveraged, USDT Market Neutral modes

**Implementation**:
- Staking/unstaking interfaces
- LST token management
- Rewards tracking
- **LST Selection**: Based on `lst_type` config (wstETH for Lido, weETH for EtherFi)

#### Morpho
**Required for**: ETH Leveraged, USDT Market Neutral modes (flash loans)

**Implementation**:
- Flash loan interfaces
- Integration with Instadapp middleware
- Atomic transaction support

### Infrastructure Services

#### Alchemy
**Required for**: All strategies

**Implementation**:
- Web3 wallet management
- Transaction broadcasting
- On-chain data access
- Gas optimization

#### Instadapp
**Required for**: ETH Leveraged, USDT Market Neutral modes

**Implementation**:
- Atomic transaction middleware
- Multi-step operation orchestration
- Flash loan coordination
- **Note**: Not a venue per se, but middleware for execution primitives

#### Uniswap
**Required for**: All strategies (when atomic on-chain transactions needed)

**Implementation**:
- DEX swap interfaces
- Atomic transaction support
- Liquidity provision (if needed)

## Implementation Architecture

### Venue Interface Standardization
Create base interfaces for all venue types:

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Any
from pydantic import BaseModel

class VenueConfig(BaseModel):
    """Standardized venue configuration"""
    venue_name: str
    api_key: str
    secret_key: str
    testnet: bool = False
    additional_params: Dict[str, Any] = {}

class BaseVenueInterface(ABC):
    """Base interface for all venue types"""
    
    def __init__(self, config: VenueConfig):
        self.config = config
        self.venue_name = config.venue_name
    
    @abstractmethod
    def get_balance(self, asset: str) -> float:
        """Get balance for specific asset"""
        pass
    
    @abstractmethod
    def get_positions(self) -> Dict[str, Any]:
        """Get current positions"""
        pass
    
    @abstractmethod
    def execute_trade(self, trade_params: Dict[str, Any]) -> str:
        """Execute trade and return transaction ID"""
        pass

class CEXInterface(BaseVenueInterface):
    """Interface for CEX venues"""
    
    @abstractmethod
    def get_margin_info(self) -> Dict[str, float]:
        """Get margin information"""
        pass
    
    @abstractmethod
    def get_funding_rates(self, symbol: str) -> float:
        """Get current funding rate"""
        pass

class DeFiInterface(BaseVenueInterface):
    """Interface for DeFi venues"""
    
    @abstractmethod
    def get_health_factor(self) -> float:
        """Get health factor (for lending protocols)"""
        pass
    
    @abstractmethod
    def get_ltv(self) -> float:
        """Get loan-to-value ratio"""
        pass
```

### Venue Factory
Create `backend/src/basis_strategy_v1/core/venues/venue_factory.py`:

```python
from typing import Dict, Any
from .interfaces.base_venue_interface import BaseVenueInterface
from .interfaces.cex_interfaces import BinanceInterface, BybitInterface, OKXInterface
from .interfaces.defi_interfaces import AAVEInterface, LidoInterface, EtherFiInterface, MorphoInterface
from .interfaces.infrastructure_interfaces import AlchemyInterface, UniswapInterface, InstadappInterface

class VenueFactory:
    """Factory for creating venue interfaces based on strategy requirements"""
    
    VENUE_MAP = {
        'binance': BinanceInterface,
        'bybit': BybitInterface,
        'okx': OKXInterface,
        'aave': AAVEInterface,
        'lido': LidoInterface,
        'etherfi': EtherFiInterface,
        'morpho': MorphoInterface,
        'alchemy': AlchemyInterface,
        'uniswap': UniswapInterface,
        'instadapp': InstadappInterface,
    }
    
    @classmethod
    def create_venue(cls, venue_name: str, config: Dict[str, Any]) -> BaseVenueInterface:
        """Create venue interface based on name"""
        venue_class = cls.VENUE_MAP.get(venue_name)
        if not venue_class:
            raise ValueError(f"Unknown venue: {venue_name}")
        return venue_class(config)
    
    @classmethod
    def get_required_venues(cls, strategy_mode: str) -> List[str]:
        """Get list of required venues for strategy mode"""
        venue_requirements = {
            'pure_lending': ['aave', 'alchemy'],
            'btc_basis': ['binance', 'bybit', 'okx', 'alchemy'],
            'eth_basis': ['binance', 'bybit', 'okx', 'alchemy'],
            'eth_staking_only': ['lido', 'etherfi', 'alchemy'],
            'eth_leveraged': ['lido', 'etherfi', 'aave', 'morpho', 'alchemy', 'instadapp'],
            'usdt_market_neutral_no_leverage': ['lido', 'etherfi', 'binance', 'bybit', 'okx', 'alchemy'],
            'usdt_market_neutral': ['lido', 'etherfi', 'aave', 'morpho', 'binance', 'bybit', 'okx', 'alchemy', 'instadapp'],
        }
        return venue_requirements.get(strategy_mode, [])
```

### Execution Manager Integration
Update execution manager to handle venue-specific execution:

```python
class ExecutionManager:
    """Manages execution across multiple venues"""
    
    def __init__(self, strategy_mode: str, venue_configs: Dict[str, Dict[str, Any]]):
        self.strategy_mode = strategy_mode
        self.venues = {}
        self._initialize_venues(venue_configs)
    
    def _initialize_venues(self, venue_configs: Dict[str, Dict[str, Any]]):
        """Initialize required venues for strategy mode"""
        required_venues = VenueFactory.get_required_venues(self.strategy_mode)
        for venue_name in required_venues:
            if venue_name in venue_configs:
                self.venues[venue_name] = VenueFactory.create_venue(venue_name, venue_configs[venue_name])
    
    def execute_instructions(self, instructions: List[Dict[str, Any]]) -> List[str]:
        """Execute list of instructions across appropriate venues"""
        results = []
        for instruction in instructions:
            venue_name = instruction['venue']
            if venue_name in self.venues:
                result = self.venues[venue_name].execute_trade(instruction)
                results.append(result)
        return results
```

## Specific Venue Implementations

### CEX Venues
**Binance Interface**:
- Spot trading API
- Futures trading API
- Account management
- WebSocket for real-time data

**Bybit Interface**:
- Unified trading API
- Position management
- Risk management

**OKX Interface**:
- REST API integration
- WebSocket for market data
- Account and position management

### DeFi Venues
**AAVE V3 Interface**:
- Lending pool interactions
- Collateral management
- Health factor monitoring
- Flash loan support

**Lido Interface**:
- ETH staking
- wstETH token management
- Rewards tracking

**EtherFi Interface**:
- ETH staking
- weETH token management
- EIGEN rewards handling

**Morpho Interface**:
- Flash loan execution
- Integration with Instadapp
- Atomic transaction support

### Infrastructure Services
**Alchemy Interface**:
- Web3 provider
- Transaction broadcasting
- Gas estimation
- Block data access

**Instadapp Interface**:
- Atomic transaction orchestration
- Multi-step operation management
- Flash loan coordination

**Uniswap Interface**:
- DEX swap execution
- Liquidity provision
- Atomic transaction support

## Testing Requirements
- **MANDATORY**: 80% unit test coverage for all venue interfaces
- Test venue-specific error handling
- Test atomic transaction coordination
- Test venue failover and retry logic
- Test configuration validation

## Configuration Management
- Venue configurations in `configs/venues/`
- Strategy-specific venue requirements
- Environment-specific settings (testnet/mainnet)
- API key management and rotation

## Error Handling
- Venue-specific error handling
- Retry logic with exponential backoff
- Circuit breaker patterns
- Fallback venue selection
- Transaction failure recovery
