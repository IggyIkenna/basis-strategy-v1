"""
ETH Staking Only Strategy Implementation

Implements ETH staking strategy with liquid staking tokens (LSTs).
Inherits from BaseStrategyManager and implements the 5 standard actions.

Reference: docs/STRATEGY_MODES.md - ETH Staking Only Strategy Mode
Reference: docs/specs/05_STRATEGY_MANAGER.md - Component specification
"""

from typing import Dict, List, Any, Optional
import logging
import pandas as pd
from pathlib import Path

from .base_strategy_manager import BaseStrategyManager
from ...core.models.order import Order, OrderOperation
from ...core.models.venues import Venue
from ...core.models.instruments import validate_instrument_key, get_display_name


logger = logging.getLogger(__name__)


class ETHStakingOnlyStrategy(BaseStrategyManager):
    """
    ETH Staking Only Strategy - Liquid staking with LSTs.
    
    Strategy Overview:
    - Stake ETH via liquid staking protocols
    - Hold LST tokens (wstETH, weETH, etc.)
    - Earn staking rewards
    - Target APY: 8-15%
    """
    
    def __init__(self, config: Dict[str, Any], data_provider, exposure_monitor, 
                 position_monitor, risk_monitor, utility_manager=None, 
                 correlation_id: str = None, pid: int = None, log_dir: Path = None):
        """
        Initialize ETH staking only strategy.
        
        Args:
            config: Strategy configuration
            data_provider: Data provider instance for market data
            exposure_monitor: Exposure monitor instance for exposure data
            position_monitor: Position monitor instance for position data
            risk_monitor: Risk monitor instance for risk assessment
            utility_manager: Centralized utility manager for conversion rates
            correlation_id: Unique correlation ID for this run
            pid: Process ID
            log_dir: Log directory path (logs/{correlation_id}/{pid}/)
        """
        super().__init__(config, data_provider, exposure_monitor, position_monitor, 
                        risk_monitor, utility_manager, correlation_id, pid, log_dir)
        
        # Validate required configuration at startup (fail-fast)
        required_keys = ['eth_allocation', 'lst_type', 'staking_protocol']
        for key in required_keys:
            if key not in config:
                raise KeyError(f"Missing required configuration: {key}")
        
        # ETH staking-specific configuration (fail-fast access)
        self.eth_allocation = config['eth_allocation']  # 90% to ETH staking
        self.lst_type = config['lst_type']  # Default LST type
        self.staking_protocol = config['staking_protocol']  # Default protocol
        self.share_class = config.get('share_class', 'ETH')  # Share class currency
        self.asset = config.get('asset', 'ETH')  # Primary asset
        
        # Define and validate instrument keys
        self.entry_instrument = f"{Venue.WALLET.value}:BaseToken:ETH"
        self.staking_instrument = f"{Venue.ETHERFI.value}:LST:weETH"  # Fixed: use LST not aToken
        
        # Validate instrument keys
        validate_instrument_key(self.entry_instrument)
        validate_instrument_key(self.staking_instrument)
        
        # Get available instruments from position_monitor config
        position_config = config.get('component_config', {}).get('position_monitor', {})
        self.available_instruments = position_config.get('position_subscriptions', [])
        
        if not self.available_instruments:
            raise ValueError(
                f"{self.__class__.__name__} requires position_subscriptions in config. "
                "Define all instruments this strategy will use in component_config.position_monitor.position_subscriptions"
            )
        
        # Define required instruments for this strategy
        required_instruments = [self.entry_instrument, self.staking_instrument]
        
        # Validate all required instruments are in available set
        for instrument in required_instruments:
            if instrument not in self.available_instruments:
                raise ValueError(
                    f"Required instrument {instrument} not in position_subscriptions. "
                    f"Add to configs/modes/{config.get('mode', 'eth_staking_only')}.yaml"
                )
        
        logger.info(f"ETHStakingOnlyStrategy initialized with {self.eth_allocation*100}% ETH allocation, {self.lst_type}")
        logger.info(f"  Available instruments: {len(self.available_instruments)}")
        logger.info(f"  Entry: {get_display_name(self.entry_instrument)}")
        logger.info(f"  Staking: {get_display_name(self.staking_instrument)}")
    
    def _get_asset_price(self) -> float:
        """Get current ETH price for testing."""
        # In real implementation, this would get actual price from market data
        return 3000.0  # Mock ETH price
    
    def calculate_target_position(self, current_equity: float) -> Dict[str, float]:
        """
        Calculate target position for ETH staking strategy.
        
        Args:
            current_equity: Current equity in share class currency
            
        Returns:
            Dictionary of target positions by token/venue
        """
        try:
            # Calculate target allocations
            eth_target = current_equity * self.eth_allocation
            
            # Get current ETH price
            eth_price = self._get_asset_price()
            eth_amount = eth_target / eth_price if eth_price > 0 else 0
            
            return {
                'eth_balance': 0.0,  # No raw ETH, all staked
                f'{self.lst_type.lower()}_balance': eth_amount,  # All ETH converted to LST
                f'{self.share_class.lower()}_balance': current_equity,
                'total_equity': current_equity
            }
            
        except Exception as e:
            logger.error(f"Error calculating target position: {e}")
            return {
                'eth_balance': 0.0,
                f'{self.lst_type.lower()}_balance': 0.0,
                f'{self.share_class.lower()}_balance': 0.0,  # No reserve balance needed
                'total_equity': current_equity
            }
    
    def generate_orders(self, timestamp: pd.Timestamp, exposure: Dict, risk_assessment: Dict, pnl: Dict, market_data: Dict) -> List[Order]:
        """
        Generate orders for ETH staking only strategy.
        
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
            # Get current equity and positions
            current_equity = exposure.get('total_exposure', 0.0)
            current_positions = exposure.get('positions', {})
            
            # Check if we have any position
            has_position = current_positions.get(f'{self.lst_type.lower()}_balance', 0.0) > 0
            
            # ETH Staking Only Strategy Decision Logic
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
            self.log_error(
                error=e,
                context={
                    'method': 'generate_orders',
                    'strategy_type': self.__class__.__name__
                }
            )
            logger.error(f"Error in ETH staking only strategy order generation: {e}")
            return []
    
    def _create_entry_full_orders(self, equity: float) -> List[Order]:
        """
        Create entry full orders for ETH staking only strategy.
        
        Args:
            equity: Available equity in share class currency
            
        Returns:
            List of Order objects for full entry
        """
        try:
            # Calculate target position
            target_position = self.calculate_target_position(equity)
            orders = []
            
            # Calculate ETH amount to stake
            eth_price = self._get_asset_price()
            eth_amount = equity / eth_price if eth_price > 0 else 0
            
            if eth_amount > 0:
                # Generate unique operation ID
                operation_id = f"stake_{int(pd.Timestamp.now().timestamp() * 1000000)}"
                
                # Calculate expected deltas for staking operation
                expected_deltas = {
                    self.entry_instrument: -eth_amount,  # Lose ETH
                    self.staking_instrument: eth_amount  # Gain LST
                }
                
                # Operation details
                operation_details = {
                    'eth_allocation': self.eth_allocation,
                    'eth_price': eth_price,
                    'lst_type': self.lst_type
                }
                
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
                    expected_deltas=expected_deltas,
                    operation_details=operation_details,
                    execution_mode='sequential',
                    strategy_intent='entry_full',
                    strategy_id='eth_staking_only'
                ))
            
            return orders
            
        except Exception as e:
            logger.error(f"Error creating entry full orders: {e}")
            return []
    
    def _create_entry_partial_orders(self, equity_delta: float) -> List[Order]:
        """
        Create entry partial orders for ETH staking only strategy.
        
        Args:
            equity_delta: Additional equity to deploy
            
        Returns:
            List of Order objects for partial entry
        """
        try:
            # Calculate additional ETH amount to stake
            eth_price = self._get_asset_price()
            eth_amount = equity_delta / eth_price if eth_price > 0 else 0
            
            orders = []
            
            if eth_amount > 0:
                # Generate unique operation ID
                operation_id = f"stake_{int(pd.Timestamp.now().timestamp() * 1000000)}"
                
                # Calculate expected deltas for staking operation
                expected_deltas = {
                    self.entry_instrument: -eth_amount,  # Lose ETH
                    self.staking_instrument: eth_amount  # Gain LST
                }
                
                # Operation details
                operation_details = {
                    'eth_allocation': self.eth_allocation,
                    'eth_price': eth_price,
                    'lst_type': self.lst_type,
                    'partial_entry': True
                }
                
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
                    expected_deltas=expected_deltas,
                    operation_details=operation_details,
                    execution_mode='sequential',
                    strategy_intent='entry_partial',
                    strategy_id='eth_staking_only'
                ))
            
            return orders
            
        except Exception as e:
            logger.error(f"Error creating entry partial orders: {e}")
            return []
    
    def _create_exit_full_orders(self, equity: float) -> List[Order]:
        """
        Create exit full orders for ETH staking only strategy.
        
        Args:
            equity: Total equity to exit
            
        Returns:
            List of Order objects for full exit
        """
        try:
            # Get current position
            current_position = self.position_monitor.get_current_position()
            lst_balance = current_position.get(f'{self.lst_type.lower()}_balance', 0.0)
            
            orders = []
            
            if lst_balance > 0:
                # Generate unique operation ID
                operation_id = f"unstake_{int(pd.Timestamp.now().timestamp() * 1000000)}"
                
                # Calculate expected deltas for unstaking operation
                expected_deltas = {
                    self.staking_instrument: -lst_balance,  # Lose LST
                    self.entry_instrument: lst_balance  # Gain ETH
                }
                
                # Operation details
                operation_details = {
                    'lst_balance': lst_balance,
                    'lst_type': self.lst_type,
                    'exit_type': 'full'
                }
                
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
                    expected_deltas=expected_deltas,
                    operation_details=operation_details,
                    execution_mode='sequential',
                    strategy_intent='exit_full',
                    strategy_id='eth_staking_only'
                ))
            
            return orders
            
        except Exception as e:
            logger.error(f"Error creating exit full orders: {e}")
            return []
    
    def _create_exit_partial_orders(self, equity_delta: float) -> List[Order]:
        """
        Create exit partial orders for ETH staking only strategy.
        
        Args:
            equity_delta: Equity to remove from position
            
        Returns:
            List of Order objects for partial exit
        """
        try:
            # Get current position
            current_position = self.position_monitor.get_current_position()
            lst_balance = current_position.get(f'{self.lst_type.lower()}_balance', 0.0)
            
            # Calculate proportional reduction
            if lst_balance > 0:
                eth_price = self._get_asset_price()
                reduction_ratio = min(equity_delta / (lst_balance * eth_price), 1.0)
            else:
                reduction_ratio = 0.0
            
            lst_reduction = lst_balance * reduction_ratio
            orders = []
            
            if lst_reduction > 0:
                # Generate unique operation ID
                operation_id = f"unstake_{int(pd.Timestamp.now().timestamp() * 1000000)}"
                
                # Calculate expected deltas for unstaking operation
                expected_deltas = {
                    self.staking_instrument: -lst_reduction,  # Lose LST
                    self.entry_instrument: lst_reduction  # Gain ETH
                }
                
                # Operation details
                operation_details = {
                    'lst_reduction': lst_reduction,
                    'reduction_ratio': reduction_ratio,
                    'lst_type': self.lst_type,
                    'exit_type': 'partial'
                }
                
                orders.append(Order(
                    operation_id=operation_id,
                    venue=Venue.ETHERFI,
                    operation=OrderOperation.UNSTAKE,
                    token_in=self.lst_type,
                    token_out='ETH',
                    amount=lst_reduction,
                    source_venue=Venue.ETHERFI,
                    target_venue=Venue.WALLET,
                    source_token=self.lst_type,
                    target_token='ETH',
                    expected_deltas=expected_deltas,
                    operation_details=operation_details,
                    execution_mode='sequential',
                    strategy_intent='exit_partial',
                    strategy_id='eth_staking_only'
                ))
            
            return orders
            
        except Exception as e:
            logger.error(f"Error creating exit partial orders: {e}")
            return []
    
    def _create_dust_sell_orders(self, dust_tokens: Dict[str, float]) -> List[Order]:
        """
        Create dust sell orders for ETH staking only strategy.
        
        Args:
            dust_tokens: Dictionary of dust tokens and amounts
            
        Returns:
            List of Order objects for dust selling
        """
        try:
            orders = []
            
            for token, amount in dust_tokens.items():
                if amount > 0 and token != self.share_class:
                    # Convert dust tokens (ETH, EIGEN, ETHFI) to share class
                    if token in ['ETH', 'EIGEN', 'ETHFI']:
                        # Generate unique operation ID
                        operation_id = f"dust_sell_{int(pd.Timestamp.now().timestamp() * 1000000)}"
                        
                        # Calculate expected deltas for dust conversion
                        dust_instrument = f"{Venue.WALLET.value}:BaseToken:{token}"
                        eth_instrument = f"{Venue.WALLET.value}:BaseToken:ETH"
                        expected_deltas = {
                            dust_instrument: -amount,  # Lose dust token
                            eth_instrument: amount  # Gain ETH
                        }
                        
                        # Operation details
                        operation_details = {
                            'dust_token': token,
                            'target_currency': 'ETH',
                            'conversion_type': 'dust_cleanup'
                        }
                        
                        orders.append(Order(
                            operation_id=operation_id,
                            venue=Venue.UNISWAP,
                            operation=OrderOperation.SWAP,
                            token_in=token,
                            token_out='ETH',
                            amount=amount,
                            source_venue=Venue.WALLET,
                            target_venue=Venue.WALLET,
                            source_token=token,
                            target_token='ETH',
                            expected_deltas=expected_deltas,
                            operation_details=operation_details,
                            execution_mode='sequential',
                            strategy_intent='dust_sell',
                            strategy_id='eth_staking_only'
                        ))
            
            return orders
            
        except Exception as e:
            logger.error(f"Error creating dust sell orders: {e}")
            return []
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """
        Get ETH staking only strategy information and status.
        
        Returns:
            Dictionary with strategy information
        """
        try:
            base_info = super().get_strategy_info()
            
            # Add ETH staking only-specific information
            base_info.update({
                'strategy_type': 'eth_staking_only',
                'eth_allocation': self.eth_allocation,
                'lst_type': self.lst_type,
                'staking_protocol': self.staking_protocol,
                'description': 'ETH staking only strategy using Order/Trade system',
                'order_system': 'unified_order_trade'
            })
            
            return base_info
            
        except Exception as e:
            logger.error(f"Error getting strategy info: {e}")
            return {
                'strategy_type': 'eth_staking_only',
                'mode': self.mode,
                'share_class': self.share_class,
                'asset': self.asset,
                'equity': 0.0,
                'error': str(e)
            }
