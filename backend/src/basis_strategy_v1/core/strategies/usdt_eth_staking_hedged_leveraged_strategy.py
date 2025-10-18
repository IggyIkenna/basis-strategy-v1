"""
USDT ETH Staking Hedged Leveraged Strategy Implementation

Implements USDT ETH staking hedged leveraged strategy.
Uses unified Order/Trade system for execution.

Reference: docs/STRATEGY_MODES.md - USDT ETH Staking Hedged Leveraged Strategy Mode
Reference: docs/specs/05_STRATEGY_MANAGER.md - Component specification
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
import logging
import pandas as pd

from .base_strategy_manager import BaseStrategyManager
from ...core.models.order import Order, OrderOperation
from ...core.models.venues import Venue
from ...core.models.instruments import validate_instrument_key, get_display_name

logger = logging.getLogger(__name__)


class USDTETHStakingHedgedLeveragedStrategy(BaseStrategyManager):
    """
    USDT ETH Staking Hedged Leveraged Strategy - Market neutral with leverage.
    
    Strategy Overview:
    - Lend USDT on AAVE/Morpho with leverage
    - Stake ETH via liquid staking
    - Use leverage to increase exposure
    - Target APY: 15-30%
    """
    
    def __init__(self, config: Dict[str, Any], data_provider, exposure_monitor, position_monitor, risk_monitor, utility_manager=None, correlation_id: str = None, pid: int = None, log_dir: Path = None):
        """
        Initialize USDT ETH staking hedged leveraged strategy.
        
        Args:
            config: Strategy configuration
            data_provider: Data provider instance
            exposure_monitor: Exposure monitor instance
            position_monitor: Position monitor instance
            risk_monitor: Risk monitor instance
            utility_manager: Utility manager instance
            correlation_id: Correlation ID for tracking
            pid: Process ID
            log_dir: Log directory
        """
        super().__init__(config, data_provider, exposure_monitor, position_monitor, risk_monitor, utility_manager, correlation_id, pid, log_dir)
        
        # Validate required configuration at startup (fail-fast)
        required_keys = ['usdt_allocation', 'eth_allocation', 'leverage_multiplier', 'lst_type', 'lending_protocol', 'staking_protocol']
        for key in required_keys:
            if key not in config:
                raise KeyError(f"Missing required configuration: {key}")
        
        # Get available instruments from position_monitor config
        position_config = config.get('component_config', {}).get('position_monitor', {})
        self.available_instruments = position_config.get('position_subscriptions', [])
        
        if not self.available_instruments:
            raise ValueError(
                f"{self.__class__.__name__} requires position_subscriptions in config. "
                "Define all instruments this strategy will use in component_config.position_monitor.position_subscriptions"
            )
        
        # Define required instruments for this strategy
        required_instruments = [
            "wallet:BaseToken:USDT",
            "wallet:BaseToken:ETH",
            "etherfi:LST:weETH",
            "aave_v3:aToken:aWETH",
            "aave_v3:debtToken:debtWETH",
            "aave_v3:aToken:aweETH",
            "instadapp:BaseToken:WETH",
            "binance:BaseToken:USDT",
            "binance:Perp:ETHUSDT",
            "bybit:BaseToken:USDT",
            "bybit:Perp:ETHUSDT",
            "okx:BaseToken:USDT",
            "okx:Perp:ETHUSDT"
        ]
        
        # Validate all required instruments are in available set
        for instrument in required_instruments:
            if instrument not in self.available_instruments:
                raise ValueError(
                    f"Required instrument {instrument} not in position_subscriptions. "
                    f"Add to configs/modes/{config.get('mode', 'usdt_market_neutral')}.yaml"
                )
        
        # USDT ETH staking hedged leveraged-specific configuration (fail-fast access)
        self.usdt_allocation = config['usdt_allocation']  # 70% to USDT lending
        self.eth_allocation = config['eth_allocation']  # 20% to ETH staking
        self.leverage_multiplier = config['leverage_multiplier']  # 2x leverage
        self.lst_type = config['lst_type']  # Default LST type
        self.lending_protocol = config['lending_protocol']  # Default lending protocol
        self.staking_protocol = config['staking_protocol']  # Default staking protocol
        self.share_class = config.get('share_class', 'USDT')  # Share class currency
        
        logger.info(f"USDTETHStakingHedgedLeveragedStrategy initialized with {self.usdt_allocation*100}% USDT lending, {self.eth_allocation*100}% ETH staking, {self.leverage_multiplier}x leverage")
    
    def _get_asset_price(self) -> float:
        """Get current ETH price for testing."""
        # In real implementation, this would get actual price from market data
        return 3000.0  # Mock ETH price
    
    def generate_orders(self, timestamp: pd.Timestamp, exposure: Dict, risk_assessment: Dict, pnl: Dict, market_data: Dict) -> List[Order]:
        """
        Generate orders for USDT market neutral strategy based on market conditions.
        
        Args:
            timestamp: Current timestamp
            exposure: Current exposure data
            risk_assessment: Risk assessment data
            pnl: Current PnL data (deprecated)
            market_data: Current market data
            
        Returns:
            List of Order objects to execute
        """
        try:
            # Log strategy decision start
            self.logger.info("Making USDT market neutral strategy decision")
            
            # Get current equity and positions
            current_equity = exposure.get('total_exposure', 0.0)
            current_positions = exposure.get('positions', {})
            
            # Check if we have any position
            has_position = any(
                current_positions.get('aUSDT_balance', 0.0) > 0 or
                current_positions.get(f'{self.lst_type.lower()}_balance', 0.0) > 0
                for _ in [1]
            )
            
            # USDT Market Neutral Strategy Decision Logic
            if current_equity > 0 and not has_position:
                # Enter full position
                return self._create_entry_full_orders(current_equity)
            elif current_equity > 0 and has_position:
                # Check for dust tokens to sell
                dust_tokens = exposure.get('dust_tokens', {})
                if dust_tokens:
                    return self._create_dust_sell_orders(dust_tokens)
                else:
                    # No action needed
                    return []
            else:
                # No equity or exit needed
                return []
                
        except Exception as e:
            self.logger.error(
                f"Error in USDT market neutral strategy order generation: {e}",
                error_code="STRAT-001",
                exc_info=e,
                method='generate_orders',
                strategy_type=self.__class__.__name__
            )
            return []
    
    def _get_asset_price(self) -> float:
        """Get current ETH price for testing."""
        # In real implementation, this would get actual price from market data
        return 3000.0  # Mock ETH price
    
    def calculate_target_position(self, current_equity: float) -> Dict[str, float]:
        """
        Calculate target position for USDT market neutral strategy.
        
        Args:
            current_equity: Current equity in share class currency
            
        Returns:
            Dictionary of target positions by token/venue
        """
        try:
            # Calculate target allocations with leverage
            leveraged_equity = current_equity * self.leverage_multiplier
            usdt_target = leveraged_equity * self.usdt_allocation
            eth_target = leveraged_equity * self.eth_allocation
            
            # Get current ETH price
            eth_price = self._get_asset_price()
            eth_amount = eth_target / eth_price if eth_price > 0 else 0
            
            return {
                'usdt_balance': 0.0,  # No raw USDT, all lent
                'aUSDT_balance': usdt_target,  # Leveraged lent USDT
                'eth_balance': 0.0,  # No raw ETH, all staked
                f'{self.lst_type.lower()}_balance': eth_amount,  # Staked ETH
                f'{self.share_class.lower()}_balance': current_equity,
                'total_equity': current_equity,
                'leveraged_equity': leveraged_equity
            }
            
        except Exception as e:
            logger.error(f"Error calculating target position: {e}")
            return {
                'usdt_balance': 0.0,
                'aUSDT_balance': 0.0,
                'eth_balance': 0.0,
                f'{self.lst_type.lower()}_balance': 0.0,
                f'{self.share_class.lower()}_balance': current_equity,
                'total_equity': current_equity,
                'leveraged_equity': current_equity
            }
    
    def _create_entry_full_orders(self, equity: float) -> List[Order]:
        """
        Create entry full orders for USDT market neutral strategy.
        
        Args:
            equity: Available equity in share class currency
            
        Returns:
            List of Order objects for full entry
        """
        try:
            # Calculate target position
            target_position = self.calculate_target_position(equity)
            
            orders = []
            atomic_group_id = f"usdt_eth_staking_hedged_leveraged_entry_{int(equity)}"
            
            # 1. Lend USDT with leverage (atomic group)
            usdt_amount = target_position['aUSDT_balance']
            if usdt_amount > 0:
                operation_id = f"supply_usdt_{int(pd.Timestamp.now().timestamp() * 1000000)}"
                orders.append(Order(
                    operation_id=operation_id,
                    venue=Venue.AAVE_V3,
                    operation=OrderOperation.SUPPLY,
                    token_in='USDT',
                    token_out='aUSDT',
                    amount=usdt_amount,
                    source_venue=Venue.WALLET,
                    target_venue=Venue.AAVE_V3,
                    source_token='USDT',
                    target_token='aUSDT',
                    expected_deltas={
                        "aave_v3:aToken:aUSDT": usdt_amount,
                        "wallet:BaseToken:USDT": -usdt_amount
                    },
                    execution_mode='atomic',
                    atomic_group_id=atomic_group_id,
                    sequence_in_group=1,
                    strategy_intent='entry_full',
                    strategy_id='usdt_eth_staking_hedged_leveraged',
                    metadata={'leverage': self.leverage_multiplier}
                ))
            
            # 2. Buy ETH for staking (atomic group)
            eth_amount = target_position[f'{self.lst_type.lower()}_balance']
            if eth_amount > 0:
                operation_id = f"buy_eth_{int(pd.Timestamp.now().timestamp() * 1000000)}"
                orders.append(Order(
                    operation_id=operation_id,
                    venue=Venue.BINANCE,
                    operation=OrderOperation.SPOT_TRADE,
                    pair='ETH/USDT',
                    side='BUY',
                    amount=eth_amount,
                    source_venue=Venue.WALLET,
                    target_venue=Venue.BINANCE,
                    source_token='USDT',
                    target_token='ETH',
                    expected_deltas={
                        "wallet:BaseToken:ETH": eth_amount,
                        "wallet:BaseToken:USDT": -eth_amount * self._get_asset_price()
                    },
                    execution_mode='atomic',
                    atomic_group_id=atomic_group_id,
                    sequence_in_group=2,
                    strategy_intent='entry_full',
                    strategy_id='usdt_eth_staking_hedged_leveraged'
                ))
            
            # 3. Stake ETH (atomic group)
            if eth_amount > 0:
                operation_id = f"stake_eth_{int(pd.Timestamp.now().timestamp() * 1000000)}"
                orders.append(Order(
                    operation_id=operation_id,
                    venue=Venue.ETHERFI,
                    operation=OrderOperation.STAKE,
                    token_in='ETH',
                    token_out=self.lst_type,
                    amount=eth_amount,
                    source_venue=Venue.WALLET,
                    target_venue=Venue.ETHERFI,
                    source_token='ETH',
                    target_token=self.lst_type,
                    expected_deltas={
                        f"etherfi:LST:{self.lst_type}": eth_amount,
                        "wallet:BaseToken:ETH": -eth_amount
                    },
                    execution_mode='atomic',
                    atomic_group_id=atomic_group_id,
                    sequence_in_group=3,
                    strategy_intent='entry_full',
                    strategy_id='usdt_eth_staking_hedged_leveraged'
                ))
            
            # 4. Maintain reserves (sequential)
            reserve_amount = target_position[f'{self.share_class.lower()}_balance']
            if reserve_amount > 0:
                operation_id = f"reserve_{int(pd.Timestamp.now().timestamp() * 1000000)}"
                orders.append(Order(
                    operation_id=operation_id,
                    venue=Venue.WALLET,
                    operation=OrderOperation.TRANSFER,
                    source_venue=Venue.WALLET,
                    target_venue=Venue.WALLET,
                    token=self.share_class,
                    amount=reserve_amount,
                    source_token=self.share_class,
                    target_token=self.share_class,
                    expected_deltas={
                        f"wallet:BaseToken:{self.share_class}": 0  # No change, just reserve
                    },
                    execution_mode='sequential',
                    strategy_intent='reserve',
                    strategy_id='usdt_eth_staking_hedged_leveraged'
                ))
            
            return orders
            
        except Exception as e:
            logger.error(f"Error creating entry full orders: {e}")
            return []
    
    def _create_entry_partial_orders(self, equity_delta: float) -> List[Order]:
        """
        Create entry partial orders for USDT market neutral strategy.
        
        Args:
            equity_delta: Additional equity to deploy
            
        Returns:
            List of Order objects for partial entry
        """
        try:
            # Calculate proportional allocation with leverage
            leveraged_delta = equity_delta * self.leverage_multiplier
            usdt_delta = leveraged_delta * self.usdt_allocation
            eth_delta = leveraged_delta * self.eth_allocation
            
            # Get current ETH price
            eth_price = self._get_asset_price()
            eth_amount = eth_delta / eth_price if eth_price > 0 else 0
            
            orders = []
            atomic_group_id = f"usdt_market_neutral_partial_{int(equity_delta)}"
            
            # 1. Lend additional USDT with leverage (atomic group)
            if usdt_delta > 0:
                operation_id = f"supply_usdt_{int(pd.Timestamp.now().timestamp() * 1000000)}"
                orders.append(Order(
                    operation_id=operation_id,
                    venue=self.lending_protocol,
                    operation=OrderOperation.SUPPLY,
                    token_in='USDT',
                    token_out='aUSDT',
                    amount=usdt_delta,
                    source_venue=Venue.WALLET,
                    target_venue=Venue.AAVE_V3,
                    source_token='USDT',
                    target_token='aUSDT',
                    expected_deltas={
                        "aave_v3:aToken:aUSDT": usdt_delta,
                        "wallet:BaseToken:USDT": -usdt_delta
                    },
                    execution_mode='atomic',
                    atomic_group_id=atomic_group_id,
                    sequence_in_group=1,
                    strategy_intent='entry_partial',
                    strategy_id='usdt_market_neutral',
                    metadata={'leverage': self.leverage_multiplier}
                ))
            
            # 2. Buy additional ETH (atomic group)
            if eth_amount > 0:
                operation_id = f"buy_eth_{int(pd.Timestamp.now().timestamp() * 1000000)}"
                orders.append(Order(
                    operation_id=operation_id,
                    venue='binance',
                    operation=OrderOperation.SPOT_TRADE,
                    pair='ETH/USDT',
                    side='BUY',
                    amount=eth_amount,
                    source_venue=Venue.WALLET,
                    target_venue=Venue.BINANCE,
                    source_token='USDT',
                    target_token='ETH',
                    expected_deltas={
                        "wallet:BaseToken:ETH": eth_amount,
                        "wallet:BaseToken:USDT": -eth_amount * eth_price
                    },
                    execution_mode='atomic',
                    atomic_group_id=atomic_group_id,
                    sequence_in_group=2,
                    strategy_intent='entry_partial',
                    strategy_id='usdt_market_neutral'
                ))
            
            # 3. Stake additional ETH (atomic group)
            if eth_amount > 0:
                operation_id = f"stake_eth_{int(pd.Timestamp.now().timestamp() * 1000000)}"
                orders.append(Order(
                    operation_id=operation_id,
                    venue=self.staking_protocol,
                    operation=OrderOperation.STAKE,
                    token_in='ETH',
                    token_out=self.lst_type,
                    amount=eth_amount,
                    source_venue=Venue.WALLET,
                    target_venue=Venue.ETHERFI,
                    source_token='ETH',
                    target_token=self.lst_type,
                    expected_deltas={
                        f"etherfi:LST:{self.lst_type}": eth_amount,
                        "wallet:BaseToken:ETH": -eth_amount
                    },
                    execution_mode='atomic',
                    atomic_group_id=atomic_group_id,
                    sequence_in_group=3,
                    strategy_intent='entry_partial',
                    strategy_id='usdt_market_neutral'
                ))
            
            # 4. Short ETH perps for hedging (atomic group)
            if eth_amount > 0:
                operation_id = f"short_eth_{int(pd.Timestamp.now().timestamp() * 1000000)}"
                orders.append(Order(
                    operation_id=operation_id,
                    venue=Venue.BINANCE,
                    operation=OrderOperation.PERP_TRADE,
                    pair='ETHUSDT',
                    side='SELL',
                    amount=eth_amount,
                    source_venue=Venue.WALLET,
                    target_venue=Venue.BINANCE,
                    source_token='USDT',
                    target_token='ETH',
                    expected_deltas={
                        "binance:Perp:ETHUSDT": -eth_amount,  # Short position
                        "wallet:BaseToken:USDT": -eth_amount * eth_price  # Margin requirement
                    },
                    execution_mode='atomic',
                    atomic_group_id=atomic_group_id,
                    sequence_in_group=4,
                    strategy_intent='entry_partial',
                    strategy_id='usdt_market_neutral'
                ))
            
            return orders
            
        except Exception as e:
            logger.error(f"Error creating entry partial orders: {e}")
            return []
    
    def _create_exit_full_orders(self, equity: float) -> List[Order]:
        """
        Create exit full orders for USDT market neutral strategy.
        
        Args:
            equity: Total equity to exit
            
        Returns:
            List of Order objects for full exit
        """
        try:
            # Get current position
            current_position = self.position_monitor.get_current_position()
            ausdt_balance = current_position.get('aUSDT_balance', 0.0)
            lst_balance = current_position.get(f'{self.lst_type.lower()}_balance', 0.0)
            
            orders = []
            atomic_group_id = f"usdt_market_neutral_exit_{int(equity)}"
            
            # 1. Unstake LST to get ETH (atomic group)
            if lst_balance > 0:
                operation_id = f"unstake_{int(pd.Timestamp.now().timestamp() * 1000000)}"
                orders.append(Order(
                    operation_id=operation_id,
                    venue=self.staking_protocol,
                    operation=OrderOperation.UNSTAKE,
                    token_in=self.lst_type,
                    token_out='ETH',
                    amount=lst_balance,
                    source_venue=Venue.ETHERFI,
                    target_venue=Venue.WALLET,
                    source_token=self.lst_type,
                    target_token='ETH',
                    expected_deltas={
                        f"etherfi:LST:{self.lst_type}": -lst_balance,
                        "wallet:BaseToken:ETH": lst_balance
                    },
                    execution_mode='atomic',
                    atomic_group_id=atomic_group_id,
                    sequence_in_group=1,
                    strategy_intent='exit_full',
                    strategy_id='usdt_market_neutral'
                ))
            
            # 2. Sell ETH (atomic group)
            if lst_balance > 0:
                operation_id = f"sell_eth_{int(pd.Timestamp.now().timestamp() * 1000000)}"
                eth_price = self._get_asset_price()
                orders.append(Order(
                    operation_id=operation_id,
                    venue='binance',
                    operation=OrderOperation.SPOT_TRADE,
                    pair='ETH/USDT',
                    side='SELL',
                    amount=lst_balance,
                    source_venue=Venue.WALLET,
                    target_venue=Venue.BINANCE,
                    source_token='ETH',
                    target_token='USDT',
                    expected_deltas={
                        "wallet:BaseToken:ETH": -lst_balance,
                        "wallet:BaseToken:USDT": lst_balance * eth_price
                    },
                    execution_mode='atomic',
                    atomic_group_id=atomic_group_id,
                    sequence_in_group=2,
                    strategy_intent='exit_full',
                    strategy_id='usdt_market_neutral'
                ))
            
            # 3. Withdraw lent USDT (atomic group)
            if ausdt_balance > 0:
                operation_id = f"withdraw_usdt_{int(pd.Timestamp.now().timestamp() * 1000000)}"
                orders.append(Order(
                    operation_id=operation_id,
                    venue=self.lending_protocol,
                    operation=OrderOperation.WITHDRAW,
                    token_in='aUSDT',
                    token_out='USDT',
                    amount=ausdt_balance,
                    source_venue=Venue.AAVE_V3,
                    target_venue=Venue.WALLET,
                    source_token='aUSDT',
                    target_token='USDT',
                    expected_deltas={
                        "aave_v3:aToken:aUSDT": -ausdt_balance,
                        "wallet:BaseToken:USDT": ausdt_balance
                    },
                    execution_mode='atomic',
                    atomic_group_id=atomic_group_id,
                    sequence_in_group=3,
                    strategy_intent='exit_full',
                    strategy_id='usdt_market_neutral'
                ))
            
            # 4. Convert all to share class currency (sequential)
            operation_id = f"transfer_{int(pd.Timestamp.now().timestamp() * 1000000)}"
            orders.append(Order(
                operation_id=operation_id,
                venue='wallet',
                operation=OrderOperation.TRANSFER,
                source_venue='wallet',
                target_venue='wallet',
                source_token=self.share_class,
                target_token=self.share_class,
                token=self.share_class,
                amount=equity,
                expected_deltas={
                    f"wallet:BaseToken:{self.share_class}": equity
                },
                execution_mode='sequential',
                strategy_intent='exit_full',
                strategy_id='usdt_market_neutral'
            ))
            
            return orders
            
        except Exception as e:
            logger.error(f"Error creating exit full orders: {e}")
            return []
    
    def _create_exit_partial_orders(self, equity_delta: float) -> List[Order]:
        """
        Create exit partial orders for USDT market neutral strategy.
        
        Args:
            equity_delta: Equity to remove from position
            
        Returns:
            List of Order objects for partial exit
        """
        try:
            # Get current position
            current_position = self.position_monitor.get_current_position()
            ausdt_balance = current_position.get('aUSDT_balance', 0.0)
            lst_balance = current_position.get(f'{self.lst_type.lower()}_balance', 0.0)
            
            # Calculate proportional reduction
            total_position_value = ausdt_balance + (lst_balance * self._get_asset_price())
            if total_position_value > 0:
                reduction_ratio = min(equity_delta / total_position_value, 1.0)
            else:
                reduction_ratio = 0.0
            
            ausdt_reduction = ausdt_balance * reduction_ratio
            lst_reduction = lst_balance * reduction_ratio
            
            orders = []
            atomic_group_id = f"usdt_market_neutral_partial_exit_{int(equity_delta)}"
            
            # 1. Unstake proportional LST (atomic group)
            if lst_reduction > 0:
                orders.append(Order(
                    venue=self.staking_protocol,
                    operation=OrderOperation.UNSTAKE,
                    token_in=self.lst_type,
                    token_out='ETH',
                    amount=lst_reduction,
                    execution_mode='atomic',
                    atomic_group_id=atomic_group_id,
                    sequence_in_group=1,
                    strategy_intent='exit_partial',
                    strategy_id='usdt_market_neutral'
                ))
            
            # 2. Sell proportional ETH (atomic group)
            if lst_reduction > 0:
                orders.append(Order(
                    venue='binance',
                    operation=OrderOperation.SPOT_TRADE,
                    pair='ETH/USDT',
                    side='SELL',
                    amount=lst_reduction,
                    execution_mode='atomic',
                    atomic_group_id=atomic_group_id,
                    sequence_in_group=2,
                    strategy_intent='exit_partial',
                    strategy_id='usdt_market_neutral'
                ))
            
            # 3. Withdraw proportional lent USDT (atomic group)
            if ausdt_reduction > 0:
                orders.append(Order(
                    venue=self.lending_protocol,
                    operation=OrderOperation.WITHDRAW,
                    token_in='aUSDT',
                    token_out='USDT',
                    amount=ausdt_reduction,
                    execution_mode='atomic',
                    atomic_group_id=atomic_group_id,
                    sequence_in_group=3,
                    strategy_intent='exit_partial',
                    strategy_id='usdt_market_neutral'
                ))
            
            # 4. Convert to share class currency (sequential)
            orders.append(Order(
                venue='wallet',
                operation=OrderOperation.TRANSFER,
                source_venue='wallet',
                target_venue='wallet',
                token=self.share_class,
                amount=equity_delta,
                execution_mode='sequential',
                strategy_intent='exit_partial',
                strategy_id='usdt_market_neutral'
            ))
            
            return orders
            
        except Exception as e:
            logger.error(f"Error creating exit partial orders: {e}")
            return []
    
    def _create_dust_sell_orders(self, dust_tokens: Dict[str, float]) -> List[Order]:
        """
        Create dust sell orders for USDT market neutral strategy.
        
        Args:
            dust_tokens: Dictionary of dust tokens and amounts
            
        Returns:
            List of Order objects for dust selling
        """
        try:
            orders = []
            
            for token, amount in dust_tokens.items():
                if amount > 0 and token != self.share_class:
                    # Convert to share class currency
                    if token == 'USDT':
                        # Direct conversion
                        orders.append(Order(
                            venue='wallet',
                            operation=OrderOperation.TRANSFER,
                            source_venue='wallet',
                            target_venue='wallet',
                            token=token,
                            amount=amount,
                            execution_mode='sequential',
                            strategy_intent='sell_dust',
                            strategy_id='usdt_market_neutral'
                        ))
                    
                    elif token == 'ETH':
                        # Sell ETH for share class
                        orders.append(Order(
                            venue='binance',
                            operation=OrderOperation.SPOT_TRADE,
                            pair='ETH/USDT',
                            side='SELL',
                            amount=amount,
                            execution_mode='sequential',
                            strategy_intent='sell_dust',
                            strategy_id='usdt_market_neutral'
                        ))
                    
                    elif token == self.lst_type:
                        # Unstake LST first, then sell ETH (atomic group)
                        atomic_group_id = f"dust_unstake_{token}_{int(amount)}"
                        orders.append(Order(
                            venue=self.staking_protocol,
                            operation=OrderOperation.UNSTAKE,
                            token_in=token,
                            token_out='ETH',
                            amount=amount,
                            execution_mode='atomic',
                            atomic_group_id=atomic_group_id,
                            sequence_in_group=1,
                            strategy_intent='sell_dust',
                            strategy_id='usdt_market_neutral'
                        ))
                        orders.append(Order(
                            venue='binance',
                            operation=OrderOperation.SPOT_TRADE,
                            pair='ETH/USDT',
                            side='SELL',
                            amount=amount,
                            execution_mode='atomic',
                            atomic_group_id=atomic_group_id,
                            sequence_in_group=2,
                            strategy_intent='sell_dust',
                            strategy_id='usdt_market_neutral'
                        ))
                    
                    elif token == 'aUSDT':
                        # Withdraw from lending protocol first, then convert (atomic group)
                        atomic_group_id = f"dust_withdraw_{token}_{int(amount)}"
                        orders.append(Order(
                            venue=self.lending_protocol,
                            operation=OrderOperation.WITHDRAW,
                            token_in=token,
                            token_out='USDT',
                            amount=amount,
                            execution_mode='atomic',
                            atomic_group_id=atomic_group_id,
                            sequence_in_group=1,
                            strategy_intent='sell_dust',
                            strategy_id='usdt_market_neutral'
                        ))
                        orders.append(Order(
                            venue='wallet',
                            operation=OrderOperation.TRANSFER,
                            source_venue='wallet',
                            target_venue='wallet',
                            token='USDT',
                            amount=amount,
                            execution_mode='atomic',
                            atomic_group_id=atomic_group_id,
                            sequence_in_group=2,
                            strategy_intent='sell_dust',
                            strategy_id='usdt_market_neutral'
                        ))
                    
                    else:
                        # Other tokens - sell for share class
                        orders.append(Order(
                            venue='binance',
                            operation=OrderOperation.SPOT_TRADE,
                            pair=f'{token}/USDT',
                            side='SELL',
                            amount=amount,
                            execution_mode='sequential',
                            strategy_intent='sell_dust',
                            strategy_id='usdt_market_neutral'
                        ))
            
            return orders
            
        except Exception as e:
            logger.error(f"Error creating dust sell orders: {e}")
            return []
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """
        Get USDT market neutral strategy information and status.
        
        Returns:
            Dictionary with strategy information
        """
        try:
            base_info = super().get_strategy_info()
            
            # Add USDT market neutral-specific information
            base_info.update({
                'strategy_type': 'usdt_market_neutral',
                'usdt_allocation': self.usdt_allocation,
                'eth_allocation': self.eth_allocation,
                'leverage_multiplier': self.leverage_multiplier,
                'lst_type': self.lst_type,
                'lending_protocol': self.lending_protocol,
                'staking_protocol': self.staking_protocol,
                'description': 'USDT market neutral strategy with leverage, lending and staking using Order/Trade system',
                'order_system': 'unified_order_trade'
            })
            
            return base_info
            
        except Exception as e:
            logger.error(f"Error getting strategy info: {e}")
            return {
                'strategy_type': 'usdt_market_neutral',
                'mode': self.mode,
                'share_class': self.share_class,
                'asset': self.asset,
                'equity': 0.0,
                'error': str(e)
            }
