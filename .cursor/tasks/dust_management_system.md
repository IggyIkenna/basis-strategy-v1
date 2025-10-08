# Dust Management System

## Overview
Implement dust management system for strategies that receive non-share-class tokens (specifically EIGEN and ETHFI rewards from weETH staking), converting them to share class currency to maintain clean portfolio delta calculations.

## Core Requirements

### Dust Token Identification
**Dust Tokens**: Tokens that are neither:
- Share class currency (USDT or ETH)
- Asset currency (BTC or ETH)
- LST tokens (wstETH, weETH)

**Specific Dust Tokens**:
- **EIGEN**: EigenLayer rewards from weETH staking
- **ETHFI**: EtherFi rewards from weETH staking
- **Other**: Any future reward tokens from staking protocols

### Dust Detection Logic
- **Threshold**: `dust_delta` config parameter (e.g., 0.002 = 20bps of equity)
- **Calculation**: `dust_value > (equity * dust_delta)`
- **Trigger**: Automatic detection when dust exceeds threshold
- **Priority**: Dust selling takes precedence over normal rebalancing

## Implementation Architecture

### Dust Detector
Create `backend/src/basis_strategy_v1/core/dust/dust_detector.py`:

```python
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from decimal import Decimal
import asyncio

class DustToken(BaseModel):
    """Individual dust token"""
    token: str
    amount: Decimal
    value_usd: Decimal
    venue: str
    source: str  # e.g., "weeth_staking_rewards"

class DustSnapshot(BaseModel):
    """Complete dust snapshot"""
    timestamp: float
    strategy_mode: str
    total_dust_value: Decimal
    dust_tokens: List[DustToken]
    equity: Decimal
    dust_ratio: Decimal
    exceeds_threshold: bool

class DustDetector:
    """Detects dust tokens across all venues"""
    
    def __init__(self, equity_calculator, price_provider, venue_interfaces: Dict[str, Any]):
        self.equity_calculator = equity_calculator
        self.price_provider = price_provider
        self.venue_interfaces = venue_interfaces
        self.dust_configs: Dict[str, Dict[str, Any]] = {}
    
    def set_dust_config(self, strategy_mode: str, config: Dict[str, Any]):
        """Set dust configuration for strategy mode"""
        self.dust_configs[strategy_mode] = config
    
    async def detect_dust(self, strategy_mode: str, share_class: str) -> DustSnapshot:
        """Detect dust tokens for strategy"""
        config = self.dust_configs.get(strategy_mode, {})
        dust_delta = Decimal(str(config.get('dust_delta', 0.002)))
        
        # Get current equity
        equity_snapshot = await self.equity_calculator.calculate_equity(share_class)
        equity = equity_snapshot.total_equity
        
        # Get dust tokens
        dust_tokens = await self._get_dust_tokens(strategy_mode, share_class)
        
        # Calculate total dust value
        total_dust_value = sum(token.value_usd for token in dust_tokens)
        
        # Calculate dust ratio
        dust_ratio = total_dust_value / equity if equity > 0 else Decimal('0')
        
        # Check if exceeds threshold
        exceeds_threshold = dust_ratio > dust_delta
        
        return DustSnapshot(
            timestamp=asyncio.get_event_loop().time(),
            strategy_mode=strategy_mode,
            total_dust_value=total_dust_value,
            dust_tokens=dust_tokens,
            equity=equity,
            dust_ratio=dust_ratio,
            exceeds_threshold=exceeds_threshold
        )
    
    async def _get_dust_tokens(self, strategy_mode: str, share_class: str) -> List[DustToken]:
        """Get dust tokens for strategy"""
        dust_tokens = []
        
        # Check if strategy can have dust (staking_enabled: true and lst_type: weeth)
        config = self.dust_configs.get(strategy_mode, {})
        if not (config.get('staking_enabled', False) and config.get('lst_type') == 'weeth'):
            return dust_tokens
        
        # Get dust tokens from EtherFi staking
        if 'etherfi' in self.venue_interfaces:
            etherfi_dust = await self._get_etherfi_dust()
            dust_tokens.extend(etherfi_dust)
        
        # Get dust tokens from on-chain wallet
        if 'alchemy' in self.venue_interfaces:
            wallet_dust = await self._get_wallet_dust(share_class)
            dust_tokens.extend(wallet_dust)
        
        return dust_tokens
    
    async def _get_etherfi_dust(self) -> List[DustToken]:
        """Get dust tokens from EtherFi staking"""
        dust_tokens = []
        
        try:
            # Get EIGEN rewards
            eigen_balance = await self.venue_interfaces['etherfi'].get_eigen_balance()
            if eigen_balance > 0:
                eigen_price = await self.price_provider.get_prices(['EIGEN'])
                eigen_value = eigen_balance * eigen_price.get('EIGEN', Decimal('0'))
                
                dust_tokens.append(DustToken(
                    token='EIGEN',
                    amount=eigen_balance,
                    value_usd=eigen_value,
                    venue='etherfi',
                    source='weeth_staking_rewards'
                ))
            
            # Get ETHFI rewards
            ethfi_balance = await self.venue_interfaces['etherfi'].get_ethfi_balance()
            if ethfi_balance > 0:
                ethfi_price = await self.price_provider.get_prices(['ETHFI'])
                ethfi_value = ethfi_balance * ethfi_price.get('ETHFI', Decimal('0'))
                
                dust_tokens.append(DustToken(
                    token='ETHFI',
                    amount=ethfi_balance,
                    value_usd=ethfi_value,
                    venue='etherfi',
                    source='weeth_staking_rewards'
                ))
        
        except Exception as e:
            print(f"Error getting EtherFi dust: {e}")
        
        return dust_tokens
    
    async def _get_wallet_dust(self, share_class: str) -> List[DustToken]:
        """Get dust tokens from on-chain wallet"""
        dust_tokens = []
        
        try:
            # Get wallet balances
            balances = await self.venue_interfaces['alchemy'].get_balances()
            
            # Define dust tokens
            dust_token_list = ['EIGEN', 'ETHFI']
            
            for token in dust_token_list:
                if token in balances and balances[token] > 0:
                    token_price = await self.price_provider.get_prices([token])
                    token_value = balances[token] * token_price.get(token, Decimal('0'))
                    
                    dust_tokens.append(DustToken(
                        token=token,
                        amount=balances[token],
                        value_usd=token_value,
                        venue='alchemy',
                        source='wallet_balance'
                    ))
        
        except Exception as e:
            print(f"Error getting wallet dust: {e}")
        
        return dust_tokens
```

### Dust Converter
Create `backend/src/basis_strategy_v1/core/dust/dust_converter.py`:

```python
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from decimal import Decimal
import asyncio

class DustConversionInstruction(BaseModel):
    """Instruction for converting dust tokens"""
    token: str
    amount: Decimal
    target_currency: str
    venue: str
    conversion_path: List[str]  # e.g., ["EIGEN", "USDT", "ETH"]
    estimated_output: Decimal
    estimated_fees: Decimal

class DustConverter:
    """Converts dust tokens to share class currency"""
    
    def __init__(self, venue_interfaces: Dict[str, Any], price_provider):
        self.venue_interfaces = venue_interfaces
        self.price_provider = price_provider
    
    async def convert_dust(self, dust_tokens: List[DustToken], target_currency: str) -> List[DustConversionInstruction]:
        """Convert dust tokens to target currency"""
        instructions = []
        
        for dust_token in dust_tokens:
            instruction = await self._create_conversion_instruction(dust_token, target_currency)
            if instruction:
                instructions.append(instruction)
        
        return instructions
    
    async def _create_conversion_instruction(self, dust_token: DustToken, target_currency: str) -> Optional[DustConversionInstruction]:
        """Create conversion instruction for dust token"""
        try:
            # Determine conversion path
            conversion_path = await self._get_conversion_path(dust_token.token, target_currency)
            
            # Estimate output amount
            estimated_output = await self._estimate_conversion_output(
                dust_token.token, dust_token.amount, target_currency
            )
            
            # Estimate fees
            estimated_fees = await self._estimate_conversion_fees(
                dust_token.token, dust_token.amount, target_currency
            )
            
            # Determine best venue for conversion
            venue = await self._get_best_conversion_venue(dust_token.token, target_currency)
            
            return DustConversionInstruction(
                token=dust_token.token,
                amount=dust_token.amount,
                target_currency=target_currency,
                venue=venue,
                conversion_path=conversion_path,
                estimated_output=estimated_output,
                estimated_fees=estimated_fees
            )
        
        except Exception as e:
            print(f"Error creating conversion instruction for {dust_token.token}: {e}")
            return None
    
    async def _get_conversion_path(self, from_token: str, to_token: str) -> List[str]:
        """Get conversion path from dust token to target currency"""
        if from_token == to_token:
            return [from_token]
        
        # For weETH staking strategies, convert to USDT first, then to share class
        if from_token in ['EIGEN', 'ETHFI']:
            if to_token == 'ETH':
                return [from_token, 'USDT', 'ETH']
            else:
                return [from_token, to_token]
        
        return [from_token, to_token]
    
    async def _estimate_conversion_output(self, from_token: str, amount: Decimal, to_token: str) -> Decimal:
        """Estimate conversion output amount"""
        try:
            # Get current prices
            prices = await self.price_provider.get_prices([from_token, to_token])
            
            if from_token in prices and to_token in prices:
                # Direct conversion
                return amount * prices[from_token] / prices[to_token]
            else:
                # Use USDT as intermediate
                usdt_prices = await self.price_provider.get_prices([from_token, 'USDT'])
                if from_token in usdt_prices and 'USDT' in usdt_prices:
                    usdt_amount = amount * usdt_prices[from_token] / usdt_prices['USDT']
                    if to_token == 'ETH':
                        eth_prices = await self.price_provider.get_prices(['USDT', 'ETH'])
                        if 'USDT' in eth_prices and 'ETH' in eth_prices:
                            return usdt_amount * eth_prices['USDT'] / eth_prices['ETH']
                
                return Decimal('0')
        
        except Exception as e:
            print(f"Error estimating conversion output: {e}")
            return Decimal('0')
    
    async def _estimate_conversion_fees(self, from_token: str, amount: Decimal, to_token: str) -> Decimal:
        """Estimate conversion fees"""
        # Simple fee estimation (0.1% for CEX, 0.3% for DEX)
        estimated_fees = amount * Decimal('0.001')  # 0.1%
        return estimated_fees
    
    async def _get_best_conversion_venue(self, from_token: str, to_token: str) -> str:
        """Get best venue for conversion"""
        # Prefer Binance for most conversions
        if from_token in ['EIGEN', 'ETHFI'] and to_token in ['USDT', 'ETH']:
            return 'binance'
        
        # Fallback to Uniswap for on-chain conversions
        return 'uniswap'
```

### Dust Manager
Create `backend/src/basis_strategy_v1/core/dust/dust_manager.py`:

```python
from typing import Dict, List, Any, Optional, Callable
from pydantic import BaseModel
from decimal import Decimal
import asyncio

class DustEvent(BaseModel):
    """Dust-related event"""
    event_type: str  # dust_detected, dust_converted, dust_conversion_failed
    strategy_mode: str
    timestamp: float
    dust_tokens: List[DustToken]
    total_value: Decimal
    conversion_instructions: Optional[List[DustConversionInstruction]] = None

class DustManager:
    """Manages dust detection and conversion"""
    
    def __init__(self, dust_detector: DustDetector, dust_converter: DustConverter):
        self.dust_detector = dust_detector
        self.dust_converter = dust_converter
        self.dust_callbacks: List[Callable[[DustEvent], None]] = []
        self.running = False
    
    def add_dust_callback(self, callback: Callable[[DustEvent], None]):
        """Add callback for dust events"""
        self.dust_callbacks.append(callback)
    
    async def start_monitoring(self):
        """Start monitoring dust across all strategies"""
        self.running = True
        
        while self.running:
            try:
                await self._check_all_dust()
            except Exception as e:
                print(f"Error checking dust: {e}")
            
            await asyncio.sleep(300)  # Check every 5 minutes
    
    def stop_monitoring(self):
        """Stop monitoring dust"""
        self.running = False
    
    async def _check_all_dust(self):
        """Check dust for all active strategies"""
        for strategy_mode, config in self.dust_detector.dust_configs.items():
            try:
                share_class = config['share_class']
                snapshot = await self.dust_detector.detect_dust(strategy_mode, share_class)
                
                if snapshot.exceeds_threshold:
                    await self._process_dust_detection(snapshot)
            
            except Exception as e:
                print(f"Error checking dust for {strategy_mode}: {e}")
    
    async def _process_dust_detection(self, snapshot: DustSnapshot):
        """Process dust detection and create conversion instructions"""
        try:
            # Create conversion instructions
            target_currency = snapshot.strategy_mode.split('_')[0].upper()  # Extract share class
            conversion_instructions = await self.dust_converter.convert_dust(
                snapshot.dust_tokens, target_currency
            )
            
            # Create dust event
            event = DustEvent(
                event_type='dust_detected',
                strategy_mode=snapshot.strategy_mode,
                timestamp=snapshot.timestamp,
                dust_tokens=snapshot.dust_tokens,
                total_value=snapshot.total_dust_value,
                conversion_instructions=conversion_instructions
            )
            
            # Trigger callbacks
            await self._trigger_dust_event(event)
        
        except Exception as e:
            print(f"Error processing dust detection: {e}")
    
    async def _trigger_dust_event(self, event: DustEvent):
        """Trigger dust event callbacks"""
        for callback in self.dust_callbacks:
            try:
                callback(event)
            except Exception as e:
                print(f"Error in dust callback: {e}")
    
    async def execute_dust_conversion(self, strategy_mode: str, instructions: List[DustConversionInstruction]) -> bool:
        """Execute dust conversion instructions"""
        try:
            # This would be handled by the execution manager
            # For now, just log the instructions
            print(f"Executing dust conversion for {strategy_mode}: {instructions}")
            return True
        
        except Exception as e:
            print(f"Error executing dust conversion: {e}")
            return False
```

## Strategy Integration

### Strategy Manager Integration
Update strategy managers to handle dust management:

```python
class BaseStrategyManager(ABC):
    """Base strategy manager with dust management"""
    
    def __init__(self, config: Dict[str, Any], risk_monitor, position_monitor, equity_calculator, dust_manager):
        self.config = config
        self.risk_monitor = risk_monitor
        self.position_monitor = position_monitor
        self.equity_calculator = equity_calculator
        self.dust_manager = dust_manager
        self.share_class = config['share_class']
        self.asset = config['asset']
        
        # Set up dust monitoring
        self.dust_manager.dust_detector.set_dust_config(self.config['mode'], self.config)
        self.dust_manager.add_dust_callback(self._handle_dust_event)
    
    def _handle_dust_event(self, event: DustEvent):
        """Handle dust events"""
        if event.event_type == 'dust_detected':
            # Execute dust conversion
            self._execute_dust_conversion(event.conversion_instructions)
    
    def _execute_dust_conversion(self, instructions: List[DustConversionInstruction]):
        """Execute dust conversion instructions"""
        # This would trigger the execution manager to execute the conversion
        pass
    
    async def check_dust_threshold(self) -> bool:
        """Check if dust exceeds threshold"""
        snapshot = await self.dust_manager.dust_detector.detect_dust(
            self.config['mode'], self.share_class
        )
        return snapshot.exceeds_threshold
```

## Configuration

### Dust Configuration
Add dust parameters to strategy configs:

```yaml
# Example: configs/modes/eth_leveraged.yaml
mode: "eth_leveraged"
# ... existing config ...

# Dust management
dust_delta: 0.002  # 20bps of equity
dust_monitoring_interval: 300  # 5 minutes
dust_conversion_venue: "binance"  # Preferred venue for conversion
dust_conversion_path: ["EIGEN", "USDT", "ETH"]  # Conversion path
```

## Testing Requirements
- **MANDATORY**: 80% unit test coverage for dust management
- Test dust detection accuracy
- Test dust conversion logic
- Test dust event handling
- Test edge cases (zero dust, conversion failures, etc.)

## Event System Integration
- Dust events logged for downstream consumers
- Integration with execution manager for conversion execution
- Monitoring and alerting for dust accumulation
