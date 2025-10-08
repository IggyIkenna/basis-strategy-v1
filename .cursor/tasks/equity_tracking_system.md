# Equity Tracking System

## Overview
Implement comprehensive equity tracking system that accurately calculates equity in share class currency across all venues and strategy modes, enabling proper target position calculation and rebalancing decisions.

## Core Requirements

### Equity Definition
**Equity = Assets - Debt (in share class currency)**
- **Assets**: Tokens on actual wallets (not locked in smart contracts)
- **Debt**: Borrowed amounts across all venues
- **Exclusions**: Futures positions (tracked separately for hedging)
- **Currency**: Always calculated in share class currency (USDT or ETH)

### Asset Tracking
**Include in Equity Calculation**:
- **AAVE**: aTokens (aUSDT, aETH) - these represent lent assets
- **Lending Protocols**: Debt tokens (variableDebtUSDT, variableDebtETH)
- **Staking**: LST tokens (wstETH, weETH) - these represent staked assets
- **CEX**: Spot balances and margin balances
- **On-chain Wallets**: Native tokens (ETH, USDT, etc.)

**Exclude from Equity Calculation**:
- **Locked Assets**: ETH stuck at EtherFi (not in wallet)
- **Futures Positions**: Perp positions (tracked separately for hedging)
- **Pending Transactions**: Unconfirmed transactions

### Debt Tracking
**Include in Equity Calculation**:
- **AAVE**: Variable debt tokens (variableDebtUSDT, variableDebtETH)
- **CEX**: Borrowed amounts (if any)
- **Flash Loans**: Outstanding flash loan amounts

## Implementation Architecture

### Equity Calculator
Create `backend/src/basis_strategy_v1/core/equity/equity_calculator.py`:

```python
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from decimal import Decimal
import asyncio

class AssetPosition(BaseModel):
    """Individual asset position"""
    asset: str
    amount: Decimal
    venue: str
    locked: bool = False
    value_usd: Optional[Decimal] = None

class DebtPosition(BaseModel):
    """Individual debt position"""
    asset: str
    amount: Decimal
    venue: str
    value_usd: Optional[Decimal] = None

class EquitySnapshot(BaseModel):
    """Complete equity snapshot"""
    timestamp: float
    share_class: str
    total_equity: Decimal
    assets: List[AssetPosition]
    debts: List[DebtPosition]
    equity_by_venue: Dict[str, Decimal]
    equity_by_asset: Dict[str, Decimal]

class EquityCalculator:
    """Calculates equity across all venues and assets"""
    
    def __init__(self, venue_interfaces: Dict[str, Any], price_provider):
        self.venue_interfaces = venue_interfaces
        self.price_provider = price_provider
        self.share_class = None  # Set by strategy
    
    async def calculate_equity(self, share_class: str) -> EquitySnapshot:
        """Calculate complete equity snapshot"""
        self.share_class = share_class
        
        # Gather all positions across venues
        assets, debts = await self._gather_all_positions()
        
        # Calculate USD values
        await self._calculate_usd_values(assets, debts)
        
        # Calculate equity by venue and asset
        equity_by_venue = self._calculate_equity_by_venue(assets, debts)
        equity_by_asset = self._calculate_equity_by_asset(assets, debts)
        
        # Calculate total equity
        total_equity = sum(pos.value_usd for pos in assets) - sum(pos.value_usd for pos in debts)
        
        return EquitySnapshot(
            timestamp=asyncio.get_event_loop().time(),
            share_class=share_class,
            total_equity=total_equity,
            assets=assets,
            debts=debts,
            equity_by_venue=equity_by_venue,
            equity_by_asset=equity_by_asset
        )
    
    async def _gather_all_positions(self) -> tuple[List[AssetPosition], List[DebtPosition]]:
        """Gather all asset and debt positions across venues"""
        assets = []
        debts = []
        
        # Gather positions from each venue
        for venue_name, venue_interface in self.venue_interfaces.items():
            venue_assets, venue_debts = await self._get_venue_positions(venue_name, venue_interface)
            assets.extend(venue_assets)
            debts.extend(venue_debts)
        
        return assets, debts
    
    async def _get_venue_positions(self, venue_name: str, venue_interface) -> tuple[List[AssetPosition], List[DebtPosition]]:
        """Get positions from specific venue"""
        assets = []
        debts = []
        
        if venue_name in ['aave', 'lido', 'etherfi']:
            # DeFi venues
            assets, debts = await self._get_defi_positions(venue_name, venue_interface)
        elif venue_name in ['binance', 'bybit', 'okx']:
            # CEX venues
            assets, debts = await self._get_cex_positions(venue_name, venue_interface)
        elif venue_name == 'alchemy':
            # On-chain wallet
            assets = await self._get_wallet_positions(venue_interface)
        
        return assets, debts
    
    async def _get_defi_positions(self, venue_name: str, venue_interface) -> tuple[List[AssetPosition], List[DebtPosition]]:
        """Get positions from DeFi venues"""
        assets = []
        debts = []
        
        if venue_name == 'aave':
            # Get aTokens (lent assets)
            a_tokens = await venue_interface.get_a_tokens()
            for token, amount in a_tokens.items():
                assets.append(AssetPosition(
                    asset=token,
                    amount=amount,
                    venue=venue_name,
                    locked=False
                ))
            
            # Get debt tokens (borrowed assets)
            debt_tokens = await venue_interface.get_debt_tokens()
            for token, amount in debt_tokens.items():
                debts.append(DebtPosition(
                    asset=token,
                    amount=amount,
                    venue=venue_name
                ))
        
        elif venue_name in ['lido', 'etherfi']:
            # Get LST tokens (staked assets)
            lst_balance = await venue_interface.get_lst_balance()
            if lst_balance > 0:
                assets.append(AssetPosition(
                    asset=venue_interface.get_lst_token(),
                    amount=lst_balance,
                    venue=venue_name,
                    locked=False
                ))
        
        return assets, debts
    
    async def _get_cex_positions(self, venue_name: str, venue_interface) -> tuple[List[AssetPosition], List[DebtPosition]]:
        """Get positions from CEX venues"""
        assets = []
        debts = []
        
        # Get spot balances
        spot_balances = await venue_interface.get_spot_balances()
        for asset, amount in spot_balances.items():
            if amount > 0:
                assets.append(AssetPosition(
                    asset=asset,
                    amount=amount,
                    venue=venue_name,
                    locked=False
                ))
        
        # Get margin balances (if any)
        margin_info = await venue_interface.get_margin_info()
        if margin_info.get('borrowed_amount', 0) > 0:
            debts.append(DebtPosition(
                asset=margin_info['borrowed_asset'],
                amount=margin_info['borrowed_amount'],
                venue=venue_name
            ))
        
        return assets, debts
    
    async def _get_wallet_positions(self, venue_interface) -> List[AssetPosition]:
        """Get positions from on-chain wallet"""
        assets = []
        
        # Get native token balances
        balances = await venue_interface.get_balances()
        for asset, amount in balances.items():
            if amount > 0:
                assets.append(AssetPosition(
                    asset=asset,
                    amount=amount,
                    venue='alchemy',
                    locked=False
                ))
        
        return assets
    
    async def _calculate_usd_values(self, assets: List[AssetPosition], debts: List[DebtPosition]):
        """Calculate USD values for all positions"""
        # Get prices for all unique assets
        all_assets = set(pos.asset for pos in assets + debts)
        prices = await self.price_provider.get_prices(list(all_assets))
        
        # Calculate USD values
        for position in assets + debts:
            if position.asset in prices:
                position.value_usd = position.amount * prices[position.asset]
    
    def _calculate_equity_by_venue(self, assets: List[AssetPosition], debts: List[DebtPosition]) -> Dict[str, Decimal]:
        """Calculate equity by venue"""
        equity_by_venue = {}
        
        for venue in set(pos.venue for pos in assets + debts):
            venue_assets = sum(pos.value_usd for pos in assets if pos.venue == venue)
            venue_debts = sum(pos.value_usd for pos in debts if pos.venue == venue)
            equity_by_venue[venue] = venue_assets - venue_debts
        
        return equity_by_venue
    
    def _calculate_equity_by_asset(self, assets: List[AssetPosition], debts: List[DebtPosition]) -> Dict[str, Decimal]:
        """Calculate equity by asset"""
        equity_by_asset = {}
        
        for asset in set(pos.asset for pos in assets + debts):
            asset_assets = sum(pos.value_usd for pos in assets if pos.asset == asset)
            asset_debts = sum(pos.value_usd for pos in debts if pos.asset == asset)
            equity_by_asset[asset] = asset_assets - asset_debts
        
        return equity_by_asset
```

### Price Provider
Create `backend/src/basis_strategy_v1/core/pricing/price_provider.py`:

```python
from typing import Dict, List
import asyncio
from decimal import Decimal

class PriceProvider:
    """Provides real-time pricing for all assets"""
    
    def __init__(self, venue_interfaces: Dict[str, Any]):
        self.venue_interfaces = venue_interfaces
        self.price_cache = {}
        self.cache_ttl = 30  # 30 seconds
    
    async def get_prices(self, assets: List[str]) -> Dict[str, Decimal]:
        """Get prices for multiple assets"""
        prices = {}
        
        # Check cache first
        current_time = asyncio.get_event_loop().time()
        for asset in assets:
            if asset in self.price_cache:
                cached_price, timestamp = self.price_cache[asset]
                if current_time - timestamp < self.cache_ttl:
                    prices[asset] = cached_price
        
        # Get missing prices
        missing_assets = [asset for asset in assets if asset not in prices]
        if missing_assets:
            new_prices = await self._fetch_prices(missing_assets)
            prices.update(new_prices)
            
            # Update cache
            for asset, price in new_prices.items():
                self.price_cache[asset] = (price, current_time)
        
        return prices
    
    async def _fetch_prices(self, assets: List[str]) -> Dict[str, Decimal]:
        """Fetch prices from venues"""
        prices = {}
        
        # Try CEX venues first (most reliable)
        for venue_name in ['binance', 'bybit', 'okx']:
            if venue_name in self.venue_interfaces:
                try:
                    venue_prices = await self.venue_interfaces[venue_name].get_prices(assets)
                    prices.update(venue_prices)
                    break
                except Exception as e:
                    print(f"Failed to get prices from {venue_name}: {e}")
                    continue
        
        # Fallback to on-chain pricing if needed
        if len(prices) < len(assets):
            missing_assets = [asset for asset in assets if asset not in prices]
            try:
                onchain_prices = await self.venue_interfaces['alchemy'].get_prices(missing_assets)
                prices.update(onchain_prices)
            except Exception as e:
                print(f"Failed to get on-chain prices: {e}")
        
        return prices
```

### Equity Monitor
Create `backend/src/basis_strategy_v1/core/equity/equity_monitor.py`:

```python
import asyncio
from typing import Dict, List, Callable, Optional
from .equity_calculator import EquityCalculator, EquitySnapshot

class EquityMonitor:
    """Monitors equity changes and triggers callbacks"""
    
    def __init__(self, equity_calculator: EquityCalculator, update_interval: float = 60.0):
        self.equity_calculator = equity_calculator
        self.update_interval = update_interval
        self.callbacks: List[Callable[[EquitySnapshot], None]] = []
        self.running = False
        self.last_snapshot: Optional[EquitySnapshot] = None
    
    def add_callback(self, callback: Callable[[EquitySnapshot], None]):
        """Add callback for equity changes"""
        self.callbacks.append(callback)
    
    async def start_monitoring(self, share_class: str):
        """Start monitoring equity changes"""
        self.running = True
        
        while self.running:
            try:
                snapshot = await self.equity_calculator.calculate_equity(share_class)
                
                # Check if equity changed significantly
                if self._equity_changed(snapshot):
                    for callback in self.callbacks:
                        try:
                            callback(snapshot)
                        except Exception as e:
                            print(f"Error in equity callback: {e}")
                
                self.last_snapshot = snapshot
                
            except Exception as e:
                print(f"Error calculating equity: {e}")
            
            await asyncio.sleep(self.update_interval)
    
    def stop_monitoring(self):
        """Stop monitoring equity changes"""
        self.running = False
    
    def _equity_changed(self, snapshot: EquitySnapshot) -> bool:
        """Check if equity changed significantly"""
        if not self.last_snapshot:
            return True
        
        # Check if total equity changed by more than 0.1%
        equity_change = abs(snapshot.total_equity - self.last_snapshot.total_equity)
        equity_threshold = self.last_snapshot.total_equity * Decimal('0.001')
        
        return equity_change > equity_threshold
```

## Integration with Strategy Manager

### Strategy Manager Integration
Update base strategy manager to use equity calculator:

```python
class BaseStrategyManager(ABC):
    """Base strategy manager with equity tracking"""
    
    def __init__(self, config: Dict[str, Any], risk_monitor, position_monitor, equity_calculator):
        self.config = config
        self.risk_monitor = risk_monitor
        self.position_monitor = position_monitor
        self.equity_calculator = equity_calculator
        self.share_class = config['share_class']
        self.asset = config['asset']
    
    async def get_current_equity(self) -> Decimal:
        """Get current equity in share class currency"""
        snapshot = await self.equity_calculator.calculate_equity(self.share_class)
        return snapshot.total_equity
    
    async def get_equity_by_venue(self) -> Dict[str, Decimal]:
        """Get equity breakdown by venue"""
        snapshot = await self.equity_calculator.calculate_equity(self.share_class)
        return snapshot.equity_by_venue
    
    async def get_equity_by_asset(self) -> Dict[str, Decimal]:
        """Get equity breakdown by asset"""
        snapshot = await self.equity_calculator.calculate_equity(self.share_class)
        return snapshot.equity_by_asset
```

## Testing Requirements
- **MANDATORY**: 80% unit test coverage for equity calculation
- Test equity calculation accuracy across all venues
- Test price provider fallback logic
- Test equity monitoring and callbacks
- Test edge cases (zero balances, negative equity, etc.)

## Configuration
- Equity calculation parameters in strategy configs
- Price provider settings
- Monitoring intervals
- Equity change thresholds
