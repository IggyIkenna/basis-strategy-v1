"""
USDT ETH Staking Hedged Simple Strategy Implementation

Implements USDT ETH staking hedged simple strategy without leverage.
Inherits from BaseStrategyManager and implements the 5 standard actions.

Reference: docs/STRATEGY_MODES.md - USDT ETH Staking Hedged Simple Strategy Mode
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


class USDTETHStakingHedgedSimpleStrategy(BaseStrategyManager):
    """
    USDT ETH Staking Hedged Simple Strategy - Market neutral with lending and staking.
    
    Strategy Overview:
    - Lend USDT on AAVE/Morpho
    - Stake ETH via liquid staking
    - No leverage, market neutral exposure
    - Target APY: 8-15%
    """
    
    def __init__(self, config: Dict[str, Any], data_provider, exposure_monitor, position_monitor, risk_monitor, utility_manager=None, correlation_id: str = None, pid: int = None, log_dir: Path = None):
        """
        Initialize USDT ETH staking hedged simple strategy.
        
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
                    f"Add to configs/modes/{config.get('mode', 'usdt_market_neutral_no_leverage')}.yaml"
                )
        
        # Validate required configuration at startup (fail-fast)
        required_keys = ['usdt_allocation', 'eth_allocation', 'lst_type', 'lending_protocol', 'staking_protocol']
        for key in required_keys:
            if key not in config:
                raise KeyError(f"Missing required configuration: {key}")
        
        # USDT ETH staking hedged simple-specific configuration (fail-fast access)
        self.usdt_allocation = config['usdt_allocation']  # 60% to USDT lending
        self.eth_allocation = config['eth_allocation']  # 30% to ETH staking
        self.lst_type = config['lst_type']  # Default LST type
        self.lending_protocol = config['lending_protocol']  # Default lending protocol
        self.staking_protocol = config['staking_protocol']  # Default staking protocol
        self.share_class = config.get('share_class', 'USDT')  # Share class currency
        
        logger.info(f"USDTETHStakingHedgedSimpleStrategy initialized with {self.usdt_allocation*100}% USDT lending, {self.eth_allocation*100}% ETH staking")
    
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
            # Calculate target allocations
            usdt_target = current_equity * self.usdt_allocation
            eth_target = current_equity * self.eth_allocation
            
            # Get current ETH price
            eth_price = self._get_asset_price()
            eth_amount = eth_target / eth_price if eth_price > 0 else 0
            
            return {
                'usdt_balance': 0.0,  # No raw USDT, all lent
                'aUSDT_balance': usdt_target,  # Lent USDT
                'eth_balance': 0.0,  # No raw ETH, all staked
                f'{self.lst_type.lower()}_balance': eth_amount,  # Staked ETH
                f'{self.share_class.lower()}_balance': 0.0,  # No reserve balance needed
                'total_equity': current_equity
            }
            
        except Exception as e:
            logger.error(f"Error calculating target position: {e}")
            return {
                'usdt_balance': 0.0,
                'aUSDT_balance': 0.0,
                'eth_balance': 0.0,
                f'{self.lst_type.lower()}_balance': 0.0,
                f'{self.share_class.lower()}_balance': 0.0,  # No reserve balance needed
                'total_equity': current_equity
            }
    
    def generate_orders(self, timestamp: pd.Timestamp, exposure: Dict, risk_assessment: Dict, pnl: Dict, market_data: Dict) -> List[Order]:
        """
        Generate orders for USDT market neutral strategy.
        
        Args:
            timestamp: Current timestamp
            exposure: Current exposure data
            risk_assessment: Current risk assessment
            pnl: Current PnL data (deprecated)
            market_data: Current market data
            
        Returns:
            List[Order]: List of orders to execute
        """
        try:
            current_equity = self.get_current_equity(exposure)
            
            # Determine action based on current state
            if current_equity == 0:
                # No position - enter full
                return self._create_entry_full_orders(current_equity)
            elif risk_assessment.get('risk_override', False):
                # Risk override - exit full
                return self._create_exit_full_orders(current_equity)
            elif exposure.get('withdrawal_requested', False):
                # Withdrawal requested - exit full
                return self._create_exit_full_orders(current_equity)
            else:
                # Maintain current position
                return []
                
        except Exception as e:
            logger.error(f"Error in generate_orders: {e}")
            return []
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """
        Get USDT market neutral no leverage strategy information and status.
        
        Returns:
            Dictionary with strategy information
        """
        try:
            base_info = super().get_strategy_info()
            
            # Add USDT market neutral-specific information
            base_info.update({
                'strategy_type': 'usdt_market_neutral_no_leverage',
                'usdt_allocation': self.usdt_allocation,
                'eth_allocation': self.eth_allocation,
                'lst_type': self.lst_type,
                'lending_protocol': self.lending_protocol,
                'staking_protocol': self.staking_protocol,
                'description': 'USDT market neutral strategy with lending and staking, no leverage using Order/Trade system',
                'order_system': 'unified_order_trade'
            })
            
            return base_info
            
        except Exception as e:
            logger.error(f"Error getting strategy info: {e}")
            return {
                'strategy_type': 'usdt_eth_staking_hedged_simple',
                'mode': self.mode,
                'share_class': self.share_class,
                'asset': self.asset,
                'equity': 0.0,
                'error': str(e)
            }
    
    def _create_entry_full_orders(self, equity: float) -> List[Order]:
        """Create entry full orders for USDT ETH staking hedged simple strategy."""
        try:
            orders = []
            
            # Calculate target position
            target_position = self.calculate_target_position(equity)
            
            # 1. Buy ETH for staking
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
                    execution_mode='sequential',
                    strategy_intent='entry_full',
                    strategy_id='usdt_eth_staking_hedged_simple'
                ))
            
            # 2. Stake ETH
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
                    execution_mode='sequential',
                    strategy_intent='entry_full',
                    strategy_id='usdt_eth_staking_hedged_simple'
                ))
            
            return orders
            
        except Exception as e:
            logger.error(f"Error creating entry full orders: {e}")
            return []
    
    def _create_entry_partial_orders(self, equity_delta: float) -> List[Order]:
        """Create entry partial orders for USDT ETH staking hedged simple strategy."""
        try:
            # Calculate proportional allocation
            usdt_delta = equity_delta * self.usdt_allocation
            eth_delta = equity_delta * self.eth_allocation
            
            orders = []
            
            # Buy ETH for staking
            eth_price = self._get_asset_price()
            eth_amount = eth_delta / eth_price if eth_price > 0 else 0
            
            if eth_amount > 0:
                operation_id = f"buy_eth_partial_{int(pd.Timestamp.now().timestamp() * 1000000)}"
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
                        "wallet:BaseToken:USDT": -eth_amount * eth_price
                    },
                    execution_mode='sequential',
                    strategy_intent='entry_partial',
                    strategy_id='usdt_eth_staking_hedged_simple'
                ))
                
                # Stake ETH
                operation_id2 = f"stake_eth_partial_{int(pd.Timestamp.now().timestamp() * 1000000)}"
                orders.append(Order(
                    operation_id=operation_id2,
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
                    execution_mode='sequential',
                    strategy_intent='entry_partial',
                    strategy_id='usdt_eth_staking_hedged_simple'
                ))
            
            return orders
            
        except Exception as e:
            logger.error(f"Error creating entry partial orders: {e}")
            return []
    
    def _create_exit_full_orders(self, equity: float) -> List[Order]:
        """Create exit full orders for USDT ETH staking hedged simple strategy."""
        try:
            orders = []
            
            # Get current position to determine close side
            current_position = self.position_monitor.get_current_position()
            lst_balance = current_position.get(f'{self.lst_type.lower()}_balance', 0.0)
            
            if lst_balance > 0:
                # Unstake ETH
                operation_id = f"unstake_eth_{int(pd.Timestamp.now().timestamp() * 1000000)}"
                orders.append(Order(
                    operation_id=operation_id,
                    venue=Venue.ETHERFI,
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
                    execution_mode='sequential',
                    strategy_intent='exit_full',
                    strategy_id='usdt_eth_staking_hedged_simple'
                ))
                
                # Sell ETH for USDT
                operation_id2 = f"sell_eth_{int(pd.Timestamp.now().timestamp() * 1000000)}"
                eth_price = self._get_asset_price()
                orders.append(Order(
                    operation_id=operation_id2,
                    venue=Venue.BINANCE,
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
                    execution_mode='sequential',
                    strategy_intent='exit_full',
                    strategy_id='usdt_eth_staking_hedged_simple'
                ))
            
            return orders
            
        except Exception as e:
            logger.error(f"Error creating exit full orders: {e}")
            return []
    
    def _create_exit_partial_orders(self, equity_delta: float) -> List[Order]:
        """Create exit partial orders for USDT ETH staking hedged simple strategy."""
        try:
            orders = []
            
            # Get current position to determine close side
            current_position = self.position_monitor.get_current_position()
            lst_balance = current_position.get(f'{self.lst_type.lower()}_balance', 0.0)
            
            if lst_balance > 0:
                # Calculate partial exit amount
                partial_exit = min(equity_delta, lst_balance)
                
                # Unstake partial ETH
                operation_id = f"unstake_eth_partial_{int(pd.Timestamp.now().timestamp() * 1000000)}"
                orders.append(Order(
                    operation_id=operation_id,
                    venue=Venue.ETHERFI,
                    operation=OrderOperation.UNSTAKE,
                    token_in=self.lst_type,
                    token_out='ETH',
                    amount=partial_exit,
                    source_venue=Venue.ETHERFI,
                    target_venue=Venue.WALLET,
                    source_token=self.lst_type,
                    target_token='ETH',
                    expected_deltas={
                        f"etherfi:LST:{self.lst_type}": -partial_exit,
                        "wallet:BaseToken:ETH": partial_exit
                    },
                    execution_mode='sequential',
                    strategy_intent='exit_partial',
                    strategy_id='usdt_eth_staking_hedged_simple'
                ))
                
                # Sell ETH for USDT
                operation_id2 = f"sell_eth_partial_{int(pd.Timestamp.now().timestamp() * 1000000)}"
                eth_price = self._get_asset_price()
                orders.append(Order(
                    operation_id=operation_id2,
                    venue=Venue.BINANCE,
                    operation=OrderOperation.SPOT_TRADE,
                    pair='ETH/USDT',
                    side='SELL',
                    amount=partial_exit,
                    source_venue=Venue.WALLET,
                    target_venue=Venue.BINANCE,
                    source_token='ETH',
                    target_token='USDT',
                    expected_deltas={
                        "wallet:BaseToken:ETH": -partial_exit,
                        "wallet:BaseToken:USDT": partial_exit * eth_price
                    },
                    execution_mode='sequential',
                    strategy_intent='exit_partial',
                    strategy_id='usdt_eth_staking_hedged_simple'
                ))
            
            return orders
            
        except Exception as e:
            logger.error(f"Error creating exit partial orders: {e}")
            return []
    
    def _create_dust_sell_orders(self, dust_tokens: Dict[str, float]) -> List[Order]:
        """Create dust sell orders for USDT ETH staking hedged simple strategy."""
        try:
            orders = []
            
            for token, amount in dust_tokens.items():
                if amount > 0 and token != 'USDT':  # USDT is the target asset
                    # Sell dust tokens for USDT
                    operation_id = f"dust_sell_{token}_{int(pd.Timestamp.now().timestamp() * 1000000)}"
                    orders.append(Order(
                        operation_id=operation_id,
                        venue=Venue.BINANCE,
                        operation=OrderOperation.SPOT_TRADE,
                        pair=f'{token}/USDT',
                        side='SELL',
                        amount=amount,
                        source_venue=Venue.BINANCE,
                        target_venue=Venue.BINANCE,
                        source_token=token,
                        target_token='USDT',
                        expected_deltas={
                            f"{Venue.BINANCE.value}:BaseToken:{token}": -amount,
                            f"{Venue.BINANCE.value}:BaseToken:USDT": amount * 0.99  # Assume 1% slippage
                        },
                        execution_mode='sequential',
                        strategy_intent='sell_dust',
                        strategy_id='usdt_eth_staking_hedged_simple'
                    ))
            
            return orders
            
        except Exception as e:
            logger.error(f"Error creating dust sell orders: {e}")
            return []
