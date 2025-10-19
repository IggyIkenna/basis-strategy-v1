"""
Strategy Manager Component

Centralized strategy decision making that coordinates between exposure, risk, and execution.
Implements the 5 standardized actions and instruction block generation.

Reference: docs/specs/05_STRATEGY_MANAGER.md
Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Section 4
"""

import logging
import pandas as pd
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from ..strategies.base_strategy_manager import BaseStrategyManager
from ..models.order import Order, OrderOperation
from ..models.domain_events import StrategyDecision, OrderEvent

from ...infrastructure.logging.structured_logger import StructuredLogger
from ...infrastructure.logging.domain_event_logger import DomainEventLogger
from ...core.errors.error_codes import ERROR_REGISTRY

logger = logging.getLogger(__name__)

class StrategyManager(BaseStrategyManager):
    """
    Centralized strategy decision making component.
    
    Coordinates between exposure monitor, risk monitor, and execution manager
    to make strategy decisions and generate instruction blocks.
    """
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(StrategyManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, config: Dict[str, Any], data_provider, exposure_monitor, risk_monitor, utility_manager=None, position_monitor=None, event_engine=None, correlation_id: str = None, pid: int = None, log_dir: Path = None):
        """
        Initialize strategy manager.
        
        Args:
            config: Configuration dictionary (reference, never modified)
            data_provider: Data provider instance (reference)
            exposure_monitor: Exposure monitor instance (reference)
            risk_monitor: Risk monitor instance (reference)
            utility_manager: Centralized utility manager for config-driven operations
            position_monitor: Position monitor instance (for strategy delegation)
            event_engine: Event engine instance (for strategy delegation)
            correlation_id: Unique correlation ID for this run
            pid: Process ID
            log_dir: Log directory path (logs/{correlation_id}/{pid}/)
        """
        # Store references (NEVER modified)
        self.config = config
        self.data_provider = data_provider
        self.exposure_monitor = exposure_monitor
        self.risk_monitor = risk_monitor
        self.utility_manager = utility_manager
        self.position_monitor = position_monitor
        self.event_engine = event_engine
        self.health_status = "healthy"
        self.error_count = 0
        
        # Initialize logging infrastructure
        self.correlation_id = correlation_id or str(uuid.uuid4().hex)
        self.pid = pid or 0
        self.log_dir = log_dir or Path("logs/default/0")
        
        # Initialize structured logger
        self.logger = StructuredLogger(
            component_name=self.__class__.__name__,
            correlation_id=self.correlation_id,
            pid=self.pid,
            log_dir=self.log_dir,
            engine=event_engine
        )
        
        # Initialize domain event logger
        self.domain_event_logger = DomainEventLogger(
            self.log_dir, 
            correlation_id=self.correlation_id, 
            pid=self.pid
        )
        
        # Initialize strategy state
        self.current_strategy_state = {
            'last_action': None,
            'last_timestamp': None,
            'ACTION_HISTORY': [],
            'instruction_blocks_generated': 0
        }
        
        # Load strategy configuration
        self.strategy_type = config.get('component_config', {}).get('strategy_manager', {}).get('strategy_type', 'default')
        self.actions = config.get('component_config', {}).get('strategy_manager', {}).get('actions', [])
        self.rebalancing_triggers = config.get('component_config', {}).get('strategy_manager', {}).get('REBALANCING_TRIGGERS', [])
        
        self.logger.info(f"StrategyManager initialized with strategy_type: {self.strategy_type}")
    
    def _handle_error(self, error: Exception, context: str = "") -> None:
        """Handle errors with structured error handling."""
        self.error_count += 1
        error_code = "STRAT-001"  # Strategy decision failed
        
        self.logger.error(
            f"Strategy Manager error: {str(error)}",
            error_code=error_code,
            exc_info=error,
            context=context,
            component=self.__class__.__name__
        )
        
        # Update health status based on error count
        if self.error_count > 10:
            self.health_status = "unhealthy"
        elif self.error_count > 5:
            self.health_status = "degraded"
    
    def check_component_health(self) -> Dict[str, Any]:
        """Check component health status."""
        return {
            'status': self.health_status,
            'error_count': self.error_count,
            'strategy_type': self.strategy_type,
            'ACTIONS_COUNT': len(self.actions),
            'rebalancing_triggers_count': len(self.rebalancing_triggers),
            'component': self.__class__.__name__
        }
    
    def _calculate_expected_deltas(self, order_params: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate expected position deltas for an order.
        
        Args:
            order_params: Order parameters including operation, amount, venue, tokens, etc.
            
        Returns:
            Dict[str, float]: Expected position deltas (instrument_key -> delta_amount)
        """
        try:
            operation = order_params.get('operation')
            
            if operation == OrderOperation.SPOT_TRADE:
                return self._calculate_spot_trade_deltas(order_params)
            elif operation == OrderOperation.PERP_TRADE:
                return self._calculate_perp_trade_deltas(order_params)
            elif operation == OrderOperation.SUPPLY:
                return self._calculate_supply_deltas(order_params)
            elif operation == OrderOperation.BORROW:
                return self._calculate_borrow_deltas(order_params)
            elif operation == OrderOperation.REPAY:
                return self._calculate_repay_deltas(order_params)
            elif operation == OrderOperation.WITHDRAW:
                return self._calculate_withdraw_deltas(order_params)
            elif operation == OrderOperation.STAKE:
                return self._calculate_stake_deltas(order_params)
            elif operation == OrderOperation.UNSTAKE:
                return self._calculate_unstake_deltas(order_params)
            elif operation == OrderOperation.SWAP:
                return self._calculate_swap_deltas(order_params)
            elif operation == OrderOperation.TRANSFER:
                return self._calculate_transfer_deltas(order_params)
            else:
                self.logger.warning(f"Unknown operation type: {operation}")
                return {}
                
        except Exception as e:
            self.logger.error(
                "Failed to calculate expected deltas",
                error_code="STRAT-002",
                exc_info=e,
                operation=order_params.get('operation'),
                order_params=order_params
            )
            return {}
    
    def _calculate_spot_trade_deltas(self, params: Dict[str, Any]) -> Dict[str, float]:
        """Calculate expected deltas for CEX spot trade."""
        try:
            venue = params.get('venue', 'unknown')
            source_token = params.get('source_token', '')
            target_token = params.get('target_token', '')
            amount = params.get('amount', 0.0)
            price = params.get('price', 0.0)
            side = params.get('side', 'BUY')
            
            deltas = {}
            
            if side == 'BUY':
                # Buying target_token with source_token
                deltas[f"{venue}:BaseToken:{target_token}"] = amount
                deltas[f"{venue}:BaseToken:{source_token}"] = -(amount * price)
            else:  # SELL
                # Selling source_token for target_token
                deltas[f"{venue}:BaseToken:{source_token}"] = -amount
                deltas[f"{venue}:BaseToken:{target_token}"] = amount * price
            
            return deltas
            
        except Exception as e:
            self.logger.error(
                "Failed to calculate spot trade deltas",
                error_code="STRAT-002",
                exc_info=e,
                params=params
            )
            return {}
    
    def _calculate_perp_trade_deltas(self, params: Dict[str, Any]) -> Dict[str, float]:
        """Calculate expected deltas for CEX perp trade."""
        try:
            venue = params.get('venue', 'unknown')
            source_token = params.get('source_token', '')
            target_token = params.get('target_token', '')
            amount = params.get('amount', 0.0)
            price = params.get('price', 0.0)
            side = params.get('side', 'LONG')
            
            deltas = {}
            
            if side == 'LONG':
                # Long position: gain target_token exposure, lose source_token
                deltas[f"{venue}:PerpPosition:{target_token}"] = amount
                deltas[f"{venue}:BaseToken:{source_token}"] = -(amount * price)
            else:  # SHORT
                # Short position: negative target_token exposure, gain source_token
                deltas[f"{venue}:PerpPosition:{target_token}"] = -amount
                deltas[f"{venue}:BaseToken:{source_token}"] = amount * price
            
            return deltas
            
        except Exception as e:
            self.logger.error(
                "Failed to calculate perp trade deltas",
                error_code="STRAT-002",
                exc_info=e,
                params=params
            )
            return {}
    
    def _calculate_supply_deltas(self, params: Dict[str, Any]) -> Dict[str, float]:
        """Calculate expected deltas for DeFi supply operation."""
        try:
            venue = params.get('venue', 'unknown')
            source_token = params.get('source_token', '')
            target_token = params.get('target_token', '')
            amount = params.get('amount', 0.0)
            
            deltas = {}
            
            # Get AAVE supply index from utility_manager if available
            if self.utility_manager and hasattr(self.utility_manager, 'get_aave_supply_index'):
                try:
                    supply_index = self.utility_manager.get_aave_supply_index(source_token)
                    # Supply: lose source_token, gain target_token (aToken) with index
                    deltas[f"{venue}:BaseToken:{source_token}"] = -amount
                    deltas[f"{venue}:BaseToken:{target_token}"] = amount * supply_index
                except Exception as e:
                    self.logger.warning(f"Failed to get AAVE supply index for {source_token}: {e}")
                    # Fallback: assume 1:1 conversion
                    deltas[f"{venue}:BaseToken:{source_token}"] = -amount
                    deltas[f"{venue}:BaseToken:{target_token}"] = amount
            else:
                # Fallback: assume 1:1 conversion
                deltas[f"{venue}:BaseToken:{source_token}"] = -amount
                deltas[f"{venue}:BaseToken:{target_token}"] = amount
            
            return deltas
            
        except Exception as e:
            self.logger.error(
                "Failed to calculate supply deltas",
                error_code="STRAT-002",
                exc_info=e,
                params=params
            )
            return {}
    
    def _calculate_borrow_deltas(self, params: Dict[str, Any]) -> Dict[str, float]:
        """Calculate expected deltas for DeFi borrow operation."""
        try:
            venue = params.get('venue', 'unknown')
            source_token = params.get('source_token', '')
            target_token = params.get('target_token', '')
            amount = params.get('amount', 0.0)
            
            deltas = {}
            
            # Borrow: gain target_token (borrowed), create debt position
            deltas[f"{venue}:BaseToken:{target_token}"] = amount
            deltas[f"{venue}:DebtPosition:{source_token}"] = amount
            
            return deltas
            
        except Exception as e:
            self.logger.error(
                "Failed to calculate borrow deltas",
                error_code="STRAT-002",
                exc_info=e,
                params=params
            )
            return {}
    
    def _calculate_repay_deltas(self, params: Dict[str, Any]) -> Dict[str, float]:
        """Calculate expected deltas for DeFi repay operation."""
        try:
            venue = params.get('venue', 'unknown')
            source_token = params.get('source_token', '')
            target_token = params.get('target_token', '')
            amount = params.get('amount', 0.0)
            
            deltas = {}
            
            # Repay: lose source_token (repayment), reduce debt position
            deltas[f"{venue}:BaseToken:{source_token}"] = -amount
            deltas[f"{venue}:DebtPosition:{target_token}"] = -amount
            
            return deltas
            
        except Exception as e:
            self.logger.error(
                "Failed to calculate repay deltas",
                error_code="STRAT-002",
                exc_info=e,
                params=params
            )
            return {}
    
    def _calculate_withdraw_deltas(self, params: Dict[str, Any]) -> Dict[str, float]:
        """Calculate expected deltas for DeFi withdraw operation."""
        try:
            venue = params.get('venue', 'unknown')
            source_token = params.get('source_token', '')
            target_token = params.get('target_token', '')
            amount = params.get('amount', 0.0)
            
            deltas = {}
            
            # Get AAVE supply index from utility_manager if available
            if self.utility_manager and hasattr(self.utility_manager, 'get_aave_supply_index'):
                try:
                    supply_index = self.utility_manager.get_aave_supply_index(target_token)
                    # Withdraw: lose source_token (aToken), gain target_token with index
                    deltas[f"{venue}:BaseToken:{source_token}"] = -amount
                    deltas[f"{venue}:BaseToken:{target_token}"] = amount * supply_index
                except Exception as e:
                    self.logger.warning(f"Failed to get AAVE supply index for {target_token}: {e}")
                    # Fallback: assume 1:1 conversion
                    deltas[f"{venue}:BaseToken:{source_token}"] = -amount
                    deltas[f"{venue}:BaseToken:{target_token}"] = amount
            else:
                # Fallback: assume 1:1 conversion
                deltas[f"{venue}:BaseToken:{source_token}"] = -amount
                deltas[f"{venue}:BaseToken:{target_token}"] = amount
            
            return deltas
            
        except Exception as e:
            self.logger.error(
                "Failed to calculate withdraw deltas",
                error_code="STRAT-002",
                exc_info=e,
                params=params
            )
            return {}
    
    def _calculate_stake_deltas(self, params: Dict[str, Any]) -> Dict[str, float]:
        """Calculate expected deltas for staking operation."""
        try:
            venue = params.get('venue', 'unknown')
            source_token = params.get('source_token', '')
            target_token = params.get('target_token', '')
            amount = params.get('amount', 0.0)
            
            deltas = {}
            
            # Get staking rate/conversion from utility_manager if available
            if self.utility_manager and hasattr(self.utility_manager, 'get_staking_rate'):
                try:
                    staking_rate = self.utility_manager.get_staking_rate(source_token, target_token)
                    # Stake: lose source_token, gain target_token (staked version) with rate
                    deltas[f"{venue}:BaseToken:{source_token}"] = -amount
                    deltas[f"{venue}:BaseToken:{target_token}"] = amount * staking_rate
                except Exception as e:
                    self.logger.warning(f"Failed to get staking rate for {source_token}->{target_token}: {e}")
                    # Fallback: assume 1:1 conversion
                    deltas[f"{venue}:BaseToken:{source_token}"] = -amount
                    deltas[f"{venue}:BaseToken:{target_token}"] = amount
            else:
                # Fallback: assume 1:1 conversion
                deltas[f"{venue}:BaseToken:{source_token}"] = -amount
                deltas[f"{venue}:BaseToken:{target_token}"] = amount
            
            return deltas
            
        except Exception as e:
            self.logger.error(
                "Failed to calculate stake deltas",
                error_code="STRAT-002",
                exc_info=e,
                params=params
            )
            return {}
    
    def _calculate_unstake_deltas(self, params: Dict[str, Any]) -> Dict[str, float]:
        """Calculate expected deltas for unstaking operation."""
        try:
            venue = params.get('venue', 'unknown')
            source_token = params.get('source_token', '')
            target_token = params.get('target_token', '')
            amount = params.get('amount', 0.0)
            
            deltas = {}
            
            # Get staking rate/conversion from utility_manager if available
            if self.utility_manager and hasattr(self.utility_manager, 'get_staking_rate'):
                try:
                    staking_rate = self.utility_manager.get_staking_rate(target_token, source_token)
                    # Unstake: lose source_token (staked version), gain target_token with rate
                    deltas[f"{venue}:BaseToken:{source_token}"] = -amount
                    deltas[f"{venue}:BaseToken:{target_token}"] = amount * staking_rate
                except Exception as e:
                    self.logger.warning(f"Failed to get staking rate for {source_token}->{target_token}: {e}")
                    # Fallback: assume 1:1 conversion
                    deltas[f"{venue}:BaseToken:{source_token}"] = -amount
                    deltas[f"{venue}:BaseToken:{target_token}"] = amount
            else:
                # Fallback: assume 1:1 conversion
                deltas[f"{venue}:BaseToken:{source_token}"] = -amount
                deltas[f"{venue}:BaseToken:{target_token}"] = amount
            
            return deltas
            
        except Exception as e:
            self.logger.error(
                "Failed to calculate unstake deltas",
                error_code="STRAT-002",
                exc_info=e,
                params=params
            )
            return {}
    
    def _calculate_swap_deltas(self, params: Dict[str, Any]) -> Dict[str, float]:
        """Calculate expected deltas for DEX swap operation."""
        try:
            venue = params.get('venue', 'unknown')
            source_token = params.get('source_token', '')
            target_token = params.get('target_token', '')
            amount = params.get('amount', 0.0)
            price = params.get('price', 0.0)
            
            deltas = {}
            
            # Swap: lose source_token, gain target_token at exchange rate
            deltas[f"{venue}:BaseToken:{source_token}"] = -amount
            deltas[f"{venue}:BaseToken:{target_token}"] = amount * price
            
            return deltas
            
        except Exception as e:
            self.logger.error(
                "Failed to calculate swap deltas",
                error_code="STRAT-002",
                exc_info=e,
                params=params
            )
            return {}
    
    def _calculate_transfer_deltas(self, params: Dict[str, Any]) -> Dict[str, float]:
        """Calculate expected deltas for transfer operation."""
        try:
            source_venue = params.get('source_venue', 'unknown')
            target_venue = params.get('target_venue', 'unknown')
            token = params.get('source_token', params.get('token', ''))
            amount = params.get('amount', 0.0)
            
            deltas = {}
            
            # Transfer: lose from source venue, gain at target venue (1:1 movement)
            deltas[f"{source_venue}:BaseToken:{token}"] = -amount
            deltas[f"{target_venue}:BaseToken:{token}"] = amount
            
            return deltas
            
        except Exception as e:
            self.logger.error(
                "Failed to calculate transfer deltas",
                error_code="STRAT-002",
                exc_info=e,
                params=params
            )
            return {}
    
    def _log_strategy_decision(
        self,
        timestamp: pd.Timestamp,
        trigger_source: str,
        action: str,
        instruction_blocks_count: int,
        market_data: Dict,
        current_exposure: Dict,
        risk_metrics: Dict
    ) -> None:
        """Log strategy decision event."""
        try:
            # Determine decision type from action
            decision_type = "hold"
            if "entry" in action.lower():
                decision_type = "entry"
            elif "exit" in action.lower():
                decision_type = "exit"
            elif "rebalance" in action.lower():
                decision_type = "rebalance"
            elif "emergency" in action.lower():
                decision_type = "EMERGENCY_EXIT"
            
            # Create strategy decision event
            decision_event = StrategyDecision(
                timestamp=timestamp.isoformat(),
                real_utc_time=datetime.now().isoformat(),
                correlation_id=self.correlation_id,
                pid=self.pid,
                decision_type=decision_type,
                trigger_source=trigger_source,
                orders_generated=instruction_blocks_count,
                action_taken=action,
                reasoning=f"Strategy decision: {action} triggered by {trigger_source}",
                market_conditions=market_data,
                portfolio_state={
                    "exposure": current_exposure,
                    "risk_metrics": risk_metrics
                },
                risk_level=risk_metrics.get("risk_level", "unknown"),
                constraints_violated=[],
                metadata={
                    "strategy_type": self.strategy_type,
                    "component": self.__class__.__name__
                }
            )
            
            # Log the event
            self.domain_event_logger.log_strategy_decision(decision_event)
            
        except Exception as e:
            self.logger.error(
                "Failed to log strategy decision",
                error_code="STRAT-003",
                exc_info=e,
                action=action,
                trigger_source=trigger_source
            )
    
    def update_state(self, timestamp: pd.Timestamp, trigger_source: str, **kwargs) -> List[Dict]:
        """
        Main entry point for strategy decision making.
        
        Args:
            timestamp: Current loop timestamp (from EventDrivenStrategyEngine)
            trigger_source: 'full_loop' | 'manual' | 'risk_trigger'
            **kwargs: Additional parameters (e.g., deposit_amount, withdrawal_amount)
            
        Returns:
            List[Dict]: Sequential instruction blocks for Execution Manager
        """
        try:
            self.logger.info(f"Strategy Manager: Updating state from {trigger_source}")
            
            # Query data using shared clock
            if not self.utility_manager:
                raise ValueError("utility_manager is required but not provided")
            market_data = self.utility_manager.data_provider.get_data(timestamp)
            
            # Access other components via references
            current_exposure = self.exposure_monitor.get_current_exposure()
            risk_metrics = self.risk_monitor.get_current_risk_metrics()
            
            # Use utility_manager for config-driven operations if available
            if self.utility_manager:
                # Get share class from config via utility_manager
                share_class = self.utility_manager.get_share_class_from_mode(self.config.get('mode', 'default'))
                self.logger.info(f"Strategy Manager: Using share class {share_class} from config")
            
            # Decide appropriate action based on current state
            action = self.decide_action(timestamp, current_exposure, risk_metrics, market_data)
            
            # Break down action into instruction blocks
            instruction_blocks = self.generate_instruction_blocks(action, current_exposure, risk_metrics, market_data, **kwargs)
            
            # Log strategy decision event
            self._log_strategy_decision(
                timestamp=timestamp,
                trigger_source=trigger_source,
                action=action,
                instruction_blocks_count=len(instruction_blocks),
                market_data=market_data,
                current_exposure=current_exposure,
                risk_metrics=risk_metrics
            )
            
            # Update strategy state
            self.current_strategy_state.update({
                'LAST_ACTION': action,
                'LAST_TIMESTAMP': timestamp,
                'ACTION_HISTORY': self.current_strategy_state['ACTION_HISTORY'][-9:] + [action],  # Keep last 10 actions
                'instruction_blocks_generated': self.current_strategy_state['instruction_blocks_generated'] + len(instruction_blocks)
            })
            
            return instruction_blocks
            
        except Exception as e:
            self.logger.error(
                "Strategy Manager: Error in update_state",
                error_code="STRAT-001",
                exc_info=e,
                trigger_source=trigger_source
            )
            return []
    
    def generate_orders(self, timestamp: pd.Timestamp, exposure: Dict, risk_assessment: Dict, pnl: Dict, market_data: Dict, position_snapshot: Dict = None) -> List[Order]:
        """
        Generate orders based on current market conditions, exposure, risk assessment, and PnL.
        
        Args:
            timestamp: Current timestamp
            exposure: Current exposure data from ExposureMonitor
            risk_assessment: Current risk metrics from RiskMonitor
            pnl: Current PnL data from PnLMonitor
            market_data: Current market data from data provider
            
        Returns:
            List[Order]: List of orders to execute
        """
        try:
            # Log input data for debugging
            self.logger.info(f"Strategy Manager: Generating orders with exposure keys: {list(exposure.keys()) if isinstance(exposure, dict) else 'Not a dict'}")
            self.logger.info(f"Strategy Manager: Risk assessment keys: {list(risk_assessment.keys()) if isinstance(risk_assessment, dict) else 'Not a dict'}")
            self.logger.info(f"Strategy Manager: Market data keys: {list(market_data.keys()) if isinstance(market_data, dict) else 'Not a dict'}")
            
            # Get the actual strategy instance from factory
            strategy_instance = self._get_strategy_instance()
            
            # Check if strategy instance creation failed
            if isinstance(strategy_instance, dict) and strategy_instance.get('error'):
                self.logger.error(
                    f"Strategy Manager: Strategy instantiation failed: {strategy_instance.get('error_message')}",
                    error_code="STRAT-004",
                    strategy_type=self.strategy_type
                )
                return []
            
            # Delegate order generation to strategy implementation
            # Strategy returns List[Order] directly
            orders = strategy_instance.generate_orders(
                timestamp=timestamp,
                exposure=exposure,
                risk_assessment=risk_assessment,
                pnl=pnl,
                market_data=market_data,
                position_snapshot=position_snapshot
            )
            
            # Log the generated orders
            self.logger.info(f"Strategy Manager: Generated {len(orders)} orders")
            for i, order in enumerate(orders):
                self.logger.info(f"Strategy Manager: Order {i+1}: {order}")
                
                # Log each order as a domain event
                self._log_order_event(order, timestamp)
            
            # Return orders directly
            return orders
            
        except Exception as e:
            self.logger.error(
                "Strategy Manager: Error in generate_orders",
                error_code="STRAT-001",
                exc_info=e,
                exposure_keys=list(exposure.keys()) if isinstance(exposure, dict) else "Not a dict"
            )
            # Return empty list on error
            return []
    
    def _log_order_event(self, order: Order, timestamp: pd.Timestamp) -> None:
        """Log order event."""
        try:
            # Create order event
            order_event = OrderEvent(
                timestamp=timestamp.isoformat(),
                real_utc_time=datetime.now().isoformat(),
                correlation_id=self.correlation_id,
                pid=self.pid,
                order_id=order.operation_id,
                operation_id=order.operation_id,
                operation_type=order.operation.value if hasattr(order.operation, 'value') else str(order.operation),
                venue=order.venue,
                source_venue=order.source_venue,
                target_venue=order.target_venue,
                source_token=order.source_token,
                target_token=order.target_token,
                amount=order.amount,
                expected_deltas=order.expected_deltas,
                strategy_intent=order.strategy_intent,
                strategy_id=order.strategy_id,
                atomic_group_id=order.atomic_group_id,
                sequence_in_group=order.sequence_in_group,
                metadata={
                    "strategy_type": self.strategy_type,
                    "component": self.__class__.__name__,
                    "operation_details": order.operation_details
                }
            )
            
            # Log the event
            self.domain_event_logger.log_order_event(order_event)
            
        except Exception as e:
            self.logger.error(
                "Failed to log order event",
                error_code="STRAT-003",
                exc_info=e,
                order_id=order.operation_id if hasattr(order, 'operation_id') else 'unknown'
            )
    
    def _get_strategy_instance(self):
        """Get the actual strategy instance from StrategyFactory."""
        try:
            from ..strategies.strategy_factory import StrategyFactory
            
            # Get strategy mode from config
            strategy_mode = self.config.get('mode', 'default')
            
            # Create strategy instance using factory
            strategy_instance = StrategyFactory.create_strategy(
                mode=strategy_mode,
                config=self.config,
                risk_monitor=self.risk_monitor,
                position_monitor=self.position_monitor,
                event_engine=self.event_engine
            )
            
            return strategy_instance
            
        except Exception as e:
            self.logger.error(
                "Strategy Manager: Error getting strategy instance",
                error_code="STRAT-004",
                exc_info=e,
                strategy_mode=self.config.get('mode', 'default')
            )
            # Return error object instead of None
            return {
                'error': True,
                'error_type': 'strategy_instantiation_failed',
                'error_message': str(e),
                'strategy_type': self.strategy_type,
                'component': self.__class__.__name__
            }
    
    
    
    
    def _get_current_strategy_state(self) -> Dict[str, Any]:
        """
        Get current strategy state snapshot.
        
        Returns:
            Dict: Current strategy state information
        """
        try:
            return {
                'strategy_type': self.strategy_type,
                'CURRENT_STATE': self.current_strategy_state,
                'available_actions': self.actions,
                'REBALANCING_TRIGGERS': self.rebalancing_triggers,
                'mode_agnostic': True
            }
        except Exception as e:
            self.logger.error(
                "Strategy Manager: Error getting current strategy state",
                error_code="STRAT-001",
                exc_info=e
            )
            return {
                'strategy_type': self.strategy_type,
                'CURRENT_STATE': {},
                'error': str(e)
            }
