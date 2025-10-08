# Strategy Manager Refactor

## Overview
Refactor the strategy manager architecture to use inheritance-based strategy modes with standardized wrapper actions, replacing the current complex and disorganized rebalancing system.

## Key Changes

### 1. Remove Complex Components
- **Remove**: `backend/src/basis_strategy_v1/core/rebalancing/transfer_manager.py`
- **Reason**: Too complex and strategy-agnostic generalization is not feasible
- **Replace**: With inheritance-based strategy-specific implementations

### 2. Base Strategy Manager Architecture
Create `backend/src/basis_strategy_v1/core/strategies/base_strategy_manager.py`:

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Any
from pydantic import BaseModel

class StrategyAction(BaseModel):
    """Standardized strategy action wrapper"""
    action_type: str  # entry_full, entry_partial, exit_full, exit_partial, sell_dust
    target_amount: float
    target_currency: str
    instructions: List[Dict[str, Any]]
    atomic: bool = False

class BaseStrategyManager(ABC):
    """Base strategy manager with standardized interface"""
    
    def __init__(self, config: Dict[str, Any], risk_monitor, position_monitor):
        self.config = config
        self.risk_monitor = risk_monitor
        self.position_monitor = position_monitor
        self.share_class = config['share_class']
        self.asset = config['asset']
    
    @abstractmethod
    def calculate_target_position(self, current_equity: float) -> Dict[str, float]:
        """Calculate target position based on current equity"""
        pass
    
    @abstractmethod
    def entry_full(self, equity: float) -> StrategyAction:
        """Enter full position (initial setup or large deposits)"""
        pass
    
    @abstractmethod
    def entry_partial(self, equity_delta: float) -> StrategyAction:
        """Scale up position (small deposits or PnL gains)"""
        pass
    
    @abstractmethod
    def exit_full(self, equity: float) -> StrategyAction:
        """Exit entire position (withdrawals or risk override)"""
        pass
    
    @abstractmethod
    def exit_partial(self, equity_delta: float) -> StrategyAction:
        """Scale down position (small withdrawals or risk reduction)"""
        pass
    
    @abstractmethod
    def sell_dust(self, dust_tokens: Dict[str, float]) -> StrategyAction:
        """Convert non-share-class tokens to share class currency"""
        pass
    
    def get_equity(self) -> float:
        """Get current equity in share class currency"""
        # Assets net of debt, excluding futures positions
        # Only include tokens on actual wallets, not locked in smart contracts
        pass
    
    def should_sell_dust(self, dust_tokens: Dict[str, float]) -> bool:
        """Check if dust tokens exceed threshold"""
        dust_value = sum(self.get_token_value(token, amount) for token, amount in dust_tokens.items())
        equity = self.get_equity()
        return dust_value > (equity * self.config.get('dust_delta', 0.002))
```

### 3. Strategy-Specific Implementations
Create inheritance classes for each strategy mode:

- `backend/src/basis_strategy_v1/core/strategies/pure_lending_strategy.py`
- `backend/src/basis_strategy_v1/core/strategies/btc_basis_strategy_v1.py`
- `backend/src/basis_strategy_v1/core/strategies/eth_basis_strategy_v1.py`
- `backend/src/basis_strategy_v1/core/strategies/eth_staking_only_strategy.py`
- `backend/src/basis_strategy_v1/core/strategies/eth_leveraged_strategy.py`
- `backend/src/basis_strategy_v1/core/strategies/usdt_market_neutral_no_leverage_strategy.py`
- `backend/src/basis_strategy_v1/core/strategies/usdt_market_neutral_strategy.py`

### 4. Strategy Factory
Create `backend/src/basis_strategy_v1/core/strategies/strategy_factory.py`:

```python
from typing import Dict, Any
from .base_strategy_manager import BaseStrategyManager
from .pure_lending_strategy import PureLendingStrategy
from .btc_basis_strategy_v1 import BTCBasisStrategy
# ... import all strategy classes

class StrategyFactory:
    """Factory for creating strategy instances based on mode"""
    
    STRATEGY_MAP = {
        'pure_lending': PureLendingStrategy,
        'btc_basis': BTCBasisStrategy,
        'eth_basis': ETHBasisStrategy,
        'eth_staking_only': ETHStakingOnlyStrategy,
        'eth_leveraged': ETHLeveragedStrategy,
        'usdt_market_neutral_no_leverage': USDTMarketNeutralNoLeverageStrategy,
        'usdt_market_neutral': USDTMarketNeutralStrategy,
    }
    
    @classmethod
    def create_strategy(cls, mode: str, config: Dict[str, Any], risk_monitor, position_monitor) -> BaseStrategyManager:
        """Create strategy instance based on mode"""
        strategy_class = cls.STRATEGY_MAP.get(mode)
        if not strategy_class:
            raise ValueError(f"Unknown strategy mode: {mode}")
        return strategy_class(config, risk_monitor, position_monitor)
```

### 5. API Integration
Update API endpoints to pass strategy mode:

- **Backtest API**: Add `strategy_mode` parameter
- **Live API**: Add `strategy_mode` parameter  
- **Event Engine**: Pass strategy mode through to strategy manager

### 6. Risk Integration
- **Risk Monitor**: Manages venue-specific risks (strategy agnostic)
- **Circuit Breaker**: Risk assessment triggers override actions (bypasses normal rebalancing)
- **Risk Override**: Only tells strategy to reduce position, never to enter desired position

## Implementation Requirements

### Equity Tracking
- Always track equity in share class currency
- Assets net of debt, excluding futures positions
- Only include tokens on actual wallets, not locked in smart contracts
- Use AAVE aTokens and debt tokens, LST tokens, not underlying ETH

### Standardized Actions
All strategies must implement the 5 wrapper actions:
1. `entry_full`: Enter full position (initial setup or large deposits)
2. `entry_partial`: Scale up position (small deposits or PnL gains)
3. `exit_full`: Exit entire position (withdrawals or risk override)
4. `exit_partial`: Scale down position (small withdrawals or risk reduction)
5. `sell_dust`: Convert non-share-class tokens to share class currency

### Fixed Wallet Assumption
- All deposits/withdrawals go to same on-chain wallet
- Makes rebalancing deterministic and predictable
- Enables consistent instruction generation

### Reserve Management
- Add `reserve_ratio` config parameter to all strategies
- Strategies monitor reserves and send fast execution requests when low
- Reserve low events published for downstream consumers

## Testing Requirements
- **MANDATORY**: 80% unit test coverage for all strategy classes
- Test each wrapper action for all strategy modes
- Test equity calculation accuracy
- Test risk override integration
- Test dust detection and selling logic

## Migration Notes
- Remove `transfer_manager.py` completely
- Update all references to use new strategy factory
- Update event engine to use new strategy architecture
- Ensure backward compatibility during transition (if needed)
