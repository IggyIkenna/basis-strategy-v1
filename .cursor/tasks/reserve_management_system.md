# Reserve Management System

## Overview
Implement comprehensive reserve management system that maintains adequate reserves for fast client withdrawals while optimizing capital allocation across all strategy modes.

## Core Requirements

### Reserve Parameters
- **`reserve_ratio`**: Config parameter for each strategy (e.g., 5% of total capital)
- **Reserve Currency**: Always in share class currency (USDT or ETH)
- **Reserve Monitoring**: Continuous monitoring of reserve levels
- **Reserve Events**: Publish reserve_low events for downstream consumers

### Reserve Management Logic
1. **Fast Withdrawals**: Use available reserves for immediate client redemptions
2. **Reserve Threshold**: If reserve < `reserve_ratio` of total equity, publish reserve_low event
3. **Reserve Replenishment**: Strategies can request fast execution to replenish reserves
4. **Withdrawal Speed Control**: Reserve balance affects fast vs slow unwinding

## Implementation Architecture

### Reserve Manager
Create `backend/src/basis_strategy_v1/core/reserves/reserve_manager.py`:

```python
from typing import Dict, List, Any, Optional, Callable
from pydantic import BaseModel
from decimal import Decimal
import asyncio
from enum import Enum

class ReserveStatus(Enum):
    """Reserve status levels"""
    ADEQUATE = "adequate"
    LOW = "low"
    CRITICAL = "critical"

class ReserveSnapshot(BaseModel):
    """Reserve status snapshot"""
    timestamp: float
    strategy_mode: str
    share_class: str
    total_equity: Decimal
    reserve_balance: Decimal
    reserve_ratio: Decimal
    target_reserve: Decimal
    status: ReserveStatus
    reserve_utilization: Decimal

class ReserveEvent(BaseModel):
    """Reserve-related event"""
    event_type: str  # reserve_low, reserve_critical, reserve_adequate
    strategy_mode: str
    timestamp: float
    reserve_balance: Decimal
    target_reserve: Decimal
    utilization: Decimal

class ReserveManager:
    """Manages reserves across all strategy modes"""
    
    def __init__(self, equity_calculator, venue_interfaces: Dict[str, Any]):
        self.equity_calculator = equity_calculator
        self.venue_interfaces = venue_interfaces
        self.reserve_callbacks: List[Callable[[ReserveEvent], None]] = []
        self.reserve_configs: Dict[str, Dict[str, Any]] = {}
        self.running = False
    
    def add_reserve_callback(self, callback: Callable[[ReserveEvent], None]):
        """Add callback for reserve events"""
        self.reserve_callbacks.append(callback)
    
    def set_reserve_config(self, strategy_mode: str, config: Dict[str, Any]):
        """Set reserve configuration for strategy mode"""
        self.reserve_configs[strategy_mode] = config
    
    async def start_monitoring(self):
        """Start monitoring reserves across all strategies"""
        self.running = True
        
        while self.running:
            try:
                await self._check_all_reserves()
            except Exception as e:
                print(f"Error checking reserves: {e}")
            
            await asyncio.sleep(30)  # Check every 30 seconds
    
    def stop_monitoring(self):
        """Stop monitoring reserves"""
        self.running = False
    
    async def _check_all_reserves(self):
        """Check reserves for all active strategies"""
        for strategy_mode, config in self.reserve_configs.items():
            try:
                snapshot = await self._calculate_reserve_snapshot(strategy_mode, config)
                await self._process_reserve_snapshot(snapshot)
            except Exception as e:
                print(f"Error checking reserves for {strategy_mode}: {e}")
    
    async def _calculate_reserve_snapshot(self, strategy_mode: str, config: Dict[str, Any]) -> ReserveSnapshot:
        """Calculate reserve snapshot for strategy"""
        share_class = config['share_class']
        reserve_ratio = Decimal(str(config.get('reserve_ratio', 0.05)))
        
        # Get current equity
        equity_snapshot = await self.equity_calculator.calculate_equity(share_class)
        total_equity = equity_snapshot.total_equity
        
        # Calculate target reserve
        target_reserve = total_equity * reserve_ratio
        
        # Get current reserve balance
        reserve_balance = await self._get_reserve_balance(share_class)
        
        # Calculate reserve utilization
        reserve_utilization = reserve_balance / target_reserve if target_reserve > 0 else Decimal('0')
        
        # Determine status
        if reserve_utilization >= Decimal('1.0'):
            status = ReserveStatus.ADEQUATE
        elif reserve_utilization >= Decimal('0.5'):
            status = ReserveStatus.LOW
        else:
            status = ReserveStatus.CRITICAL
        
        return ReserveSnapshot(
            timestamp=asyncio.get_event_loop().time(),
            strategy_mode=strategy_mode,
            share_class=share_class,
            total_equity=total_equity,
            reserve_balance=reserve_balance,
            reserve_ratio=reserve_ratio,
            target_reserve=target_reserve,
            status=status,
            reserve_utilization=reserve_utilization
        )
    
    async def _get_reserve_balance(self, share_class: str) -> Decimal:
        """Get current reserve balance in share class currency"""
        # Get balance from on-chain wallet (Alchemy)
        if 'alchemy' in self.venue_interfaces:
            balances = await self.venue_interfaces['alchemy'].get_balances()
            return Decimal(str(balances.get(share_class, 0)))
        
        return Decimal('0')
    
    async def _process_reserve_snapshot(self, snapshot: ReserveSnapshot):
        """Process reserve snapshot and trigger events if needed"""
        # Check if status changed and trigger appropriate events
        if snapshot.status == ReserveStatus.LOW:
            event = ReserveEvent(
                event_type='reserve_low',
                strategy_mode=snapshot.strategy_mode,
                timestamp=snapshot.timestamp,
                reserve_balance=snapshot.reserve_balance,
                target_reserve=snapshot.target_reserve,
                utilization=snapshot.reserve_utilization
            )
            await self._trigger_reserve_event(event)
        
        elif snapshot.status == ReserveStatus.CRITICAL:
            event = ReserveEvent(
                event_type='reserve_critical',
                strategy_mode=snapshot.strategy_mode,
                timestamp=snapshot.timestamp,
                reserve_balance=snapshot.reserve_balance,
                target_reserve=snapshot.target_reserve,
                utilization=snapshot.reserve_utilization
            )
            await self._trigger_reserve_event(event)
    
    async def _trigger_reserve_event(self, event: ReserveEvent):
        """Trigger reserve event callbacks"""
        for callback in self.reserve_callbacks:
            try:
                callback(event)
            except Exception as e:
                print(f"Error in reserve callback: {e}")
    
    async def request_reserve_replenishment(self, strategy_mode: str, amount: Decimal) -> bool:
        """Request reserve replenishment for strategy"""
        try:
            # This would trigger the strategy to execute fast unwinding
            # to replenish reserves
            config = self.reserve_configs.get(strategy_mode)
            if not config:
                return False
            
            # Trigger strategy to execute reserve replenishment
            # This would be handled by the strategy manager
            return True
        except Exception as e:
            print(f"Error requesting reserve replenishment: {e}")
            return False
```

### Reserve Configuration
Add reserve parameters to strategy configs:

```yaml
# Example: configs/modes/pure_lending.yaml
mode: "pure_lending"
# ... existing config ...

# Reserve management
reserve_ratio: 0.05  # 5% of total equity
reserve_currency: "USDT"  # Same as share_class
reserve_monitoring_interval: 30  # seconds
reserve_low_threshold: 0.5  # 50% of target reserve
reserve_critical_threshold: 0.2  # 20% of target reserve
```

### Strategy Integration
Update strategy managers to handle reserve management:

```python
class BaseStrategyManager(ABC):
    """Base strategy manager with reserve management"""
    
    def __init__(self, config: Dict[str, Any], risk_monitor, position_monitor, equity_calculator, reserve_manager):
        self.config = config
        self.risk_monitor = risk_monitor
        self.position_monitor = position_monitor
        self.equity_calculator = equity_calculator
        self.reserve_manager = reserve_manager
        self.share_class = config['share_class']
        self.asset = config['asset']
        
        # Set up reserve monitoring
        self.reserve_manager.set_reserve_config(self.config['mode'], self.config)
        self.reserve_manager.add_reserve_callback(self._handle_reserve_event)
    
    def _handle_reserve_event(self, event: ReserveEvent):
        """Handle reserve events"""
        if event.event_type == 'reserve_low':
            # Trigger fast execution to replenish reserves
            self._request_fast_execution()
        elif event.event_type == 'reserve_critical':
            # Trigger emergency reserve replenishment
            self._request_emergency_execution()
    
    def _request_fast_execution(self):
        """Request fast execution to replenish reserves"""
        # This would trigger the strategy to execute fast unwinding
        # to replenish reserves
        pass
    
    def _request_emergency_execution(self):
        """Request emergency execution to replenish reserves"""
        # This would trigger the strategy to execute emergency unwinding
        # to replenish reserves
        pass
    
    async def check_reserve_adequacy(self) -> bool:
        """Check if reserves are adequate for fast withdrawals"""
        snapshot = await self.reserve_manager._calculate_reserve_snapshot(
            self.config['mode'], self.config
        )
        return snapshot.status == ReserveStatus.ADEQUATE
    
    async def get_reserve_balance(self) -> Decimal:
        """Get current reserve balance"""
        return await self.reserve_manager._get_reserve_balance(self.share_class)
```

### Withdrawal Speed Control
Implement withdrawal speed control based on reserve levels:

```python
class WithdrawalManager:
    """Manages withdrawal speed based on reserve levels"""
    
    def __init__(self, reserve_manager: ReserveManager):
        self.reserve_manager = reserve_manager
        self.withdrawal_speeds: Dict[str, str] = {}  # strategy_mode -> speed
    
    async def get_withdrawal_speed(self, strategy_mode: str) -> str:
        """Get withdrawal speed for strategy based on reserve levels"""
        config = self.reserve_manager.reserve_configs.get(strategy_mode)
        if not config:
            return 'slow'
        
        snapshot = await self.reserve_manager._calculate_reserve_snapshot(strategy_mode, config)
        
        if snapshot.status == ReserveStatus.ADEQUATE:
            return 'fast'
        elif snapshot.status == ReserveStatus.LOW:
            return 'medium'
        else:
            return 'slow'
    
    async def process_withdrawal(self, strategy_mode: str, amount: Decimal) -> Dict[str, Any]:
        """Process withdrawal with appropriate speed"""
        speed = await self.get_withdrawal_speed(strategy_mode)
        
        if speed == 'fast':
            # Use available reserves
            return await self._fast_withdrawal(strategy_mode, amount)
        elif speed == 'medium':
            # Partial reserve usage + some unwinding
            return await self._medium_withdrawal(strategy_mode, amount)
        else:
            # Full unwinding required
            return await self._slow_withdrawal(strategy_mode, amount)
    
    async def _fast_withdrawal(self, strategy_mode: str, amount: Decimal) -> Dict[str, Any]:
        """Fast withdrawal using reserves"""
        # Implementation for fast withdrawal
        pass
    
    async def _medium_withdrawal(self, strategy_mode: str, amount: Decimal) -> Dict[str, Any]:
        """Medium speed withdrawal"""
        # Implementation for medium withdrawal
        pass
    
    async def _slow_withdrawal(self, strategy_mode: str, amount: Decimal) -> Dict[str, Any]:
        """Slow withdrawal requiring unwinding"""
        # Implementation for slow withdrawal
        pass
```

## Event System Integration

### Reserve Events
Integrate with event system for downstream consumers:

```python
class ReserveEventLogger:
    """Logs reserve events for downstream consumers"""
    
    def __init__(self, event_logger):
        self.event_logger = event_logger
    
    def log_reserve_event(self, event: ReserveEvent):
        """Log reserve event"""
        self.event_logger.log_event({
            'type': 'reserve_event',
            'event_type': event.event_type,
            'strategy_mode': event.strategy_mode,
            'timestamp': event.timestamp,
            'reserve_balance': float(event.reserve_balance),
            'target_reserve': float(event.target_reserve),
            'utilization': float(event.utilization)
        })
```

## Testing Requirements
- **MANDATORY**: 80% unit test coverage for reserve management
- Test reserve calculation accuracy
- Test reserve event triggering
- Test withdrawal speed control
- Test reserve replenishment logic
- Test edge cases (zero reserves, negative reserves, etc.)

## Configuration
- Reserve parameters in strategy configs
- Monitoring intervals
- Threshold settings
- Event logging configuration
