"""
Strategy Manager Component

Centralized strategy decision making that coordinates between exposure, risk, and execution.
Implements the 5 standardized actions and instruction block generation.

Reference: docs/specs/05_STRATEGY_MANAGER.md
Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Section 4
"""

import logging
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
from ..strategies.base_strategy_manager import BaseStrategyManager

from ...core.logging.base_logging_interface import StandardizedLoggingMixin, LogLevel, EventType

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
    
    def __init__(self, config: Dict[str, Any], data_provider, exposure_monitor, risk_monitor, utility_manager=None):
        """
        Initialize strategy manager.
        
        Args:
            config: Configuration dictionary (reference, never modified)
            data_provider: Data provider instance (reference)
            exposure_monitor: Exposure monitor instance (reference)
            risk_monitor: Risk monitor instance (reference)
            utility_manager: Centralized utility manager for config-driven operations
        """
        # Store references (NEVER modified)
        self.config = config
        self.data_provider = data_provider
        self.exposure_monitor = exposure_monitor
        self.risk_monitor = risk_monitor
        self.utility_manager = utility_manager
        self.health_status = "healthy"
        self.error_count = 0
        
        # Initialize strategy state
        self.current_strategy_state = {
            'last_action': None,
            'last_timestamp': None,
            'action_history': [],
            'instruction_blocks_generated': 0
        }
        
        # Load strategy configuration
        self.strategy_type = config.get('component_config', {}).get('strategy_manager', {}).get('strategy_type', 'default')
        self.actions = config.get('component_config', {}).get('strategy_manager', {}).get('actions', [])
        self.rebalancing_triggers = config.get('component_config', {}).get('strategy_manager', {}).get('rebalancing_triggers', [])
        
        logger.info(f"StrategyManager initialized with strategy_type: {self.strategy_type}")
    
    def _handle_error(self, error: Exception, context: str = "") -> None:
        """Handle errors with structured error handling."""
        self.error_count += 1
        error_code = f"SM_ERROR_{self.error_count:04d}"
        
        logger.error(f"Strategy Manager error {error_code}: {str(error)}", extra={
            'error_code': error_code,
            'context': context,
            'component': self.__class__.__name__
        })
        
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
            'actions_count': len(self.actions),
            'rebalancing_triggers_count': len(self.rebalancing_triggers),
            'component': self.__class__.__name__
        }
    
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
            logger.info(f"Strategy Manager: Updating state from {trigger_source}")
            
            # Query data using shared clock
            market_data = self.data_provider.get_data(timestamp)
            
            # Access other components via references
            current_exposure = self.exposure_monitor.get_current_exposure()
            risk_metrics = self.risk_monitor.get_current_risk_metrics()
            
            # Use utility_manager for config-driven operations if available
            if self.utility_manager:
                # Get share class from config via utility_manager
                share_class = self.utility_manager.get_share_class_from_mode(self.config.get('mode', 'default'))
                logger.info(f"Strategy Manager: Using share class {share_class} from config")
            
            # Decide appropriate action based on current state
            action = self.decide_action(timestamp, current_exposure, risk_metrics, market_data)
            
            # Break down action into instruction blocks
            instruction_blocks = self.generate_instruction_blocks(action, current_exposure, risk_metrics, market_data, **kwargs)
            
            # Update strategy state
            self.current_strategy_state.update({
                'last_action': action,
                'last_timestamp': timestamp,
                'action_history': self.current_strategy_state['action_history'][-9:] + [action],  # Keep last 10 actions
                'instruction_blocks_generated': self.current_strategy_state['instruction_blocks_generated'] + len(instruction_blocks)
            })
            
            return instruction_blocks
            
        except Exception as e:
            logger.error(f"Strategy Manager: Error in update_state: {e}")
            return []
    
    def decide_action(self, timestamp: pd.Timestamp, current_exposure: Dict, risk_metrics: Dict, market_data: Dict) -> str:
        """
        Decide which of the 5 standardized actions to take.
        
        Args:
            timestamp: Current loop timestamp
            current_exposure: Current exposure from ExposureMonitor
            risk_metrics: Current risk metrics from RiskMonitor
            market_data: Market data from DataProvider
            
        Returns:
            str: One of 'entry_full', 'entry_partial', 'exit_full', 'exit_partial', 'sell_dust'
        """
        try:
            # Simple strategy logic - can be enhanced based on specific strategy requirements
            total_exposure = current_exposure.get('total_exposure', 0)
            risk_level = risk_metrics.get('overall_risk', 0)
            
            # Basic decision logic
            if total_exposure == 0:
                return 'entry_full'
            elif risk_level > 0.8:  # High risk
                return 'exit_full'
            elif risk_level > 0.6:  # Medium risk
                return 'exit_partial'
            elif total_exposure < 1000:  # Low exposure
                return 'entry_partial'
            else:
                return 'sell_dust'  # Maintain current position
                
        except Exception as e:
            logger.error(f"Strategy Manager: Error in decide_action: {e}")
            return 'sell_dust'
    
    def break_down_action(self, action: str, params: Dict, market_data: Dict) -> List[Dict]:
        """
        Break down action into sequential instruction blocks.
        
        Args:
            action: The standardized action to break down
            params: Action-specific parameters
            market_data: Market data for instruction generation
            
        Returns:
            List[Dict]: Sequential instruction blocks for Execution Manager
        """
        try:
            # This is a simplified version - can be enhanced based on specific strategy requirements
            return self._generate_instruction_blocks(action, {}, {}, market_data, **params)
        except Exception as e:
            logger.error(f"Strategy Manager: Error in break_down_action: {e}")
            return []
    
    def _generate_instruction_blocks(self, action: str, current_exposure: Dict, risk_metrics: Dict, market_data: Dict, **kwargs) -> List[Dict]:
        """
        Generate instruction blocks for the decided action.
        
        Args:
            action: Decided action
            current_exposure: Current exposure data
            risk_metrics: Current risk metrics
            market_data: Market data
            **kwargs: Additional parameters
            
        Returns:
            List[Dict]: Sequential instruction blocks
        """
        try:
            instruction_blocks = []
            
            if action == 'entry_full':
                # Generate full entry instruction blocks
                instruction_blocks.append({
                    'type': 'wallet_transfer',
                    'from_venue': 'wallet',
                    'to_venue': 'aave',
                    'token': 'USDT',
                    'amount': kwargs.get('deposit_amount', 1000.0),
                    'estimated_deltas': {
                        'wallet': {'USDT': -kwargs.get('deposit_amount', 1000.0)},
                        'aave': {'aUSDT': kwargs.get('deposit_amount', 1000.0)}
                    }
                })
                
            elif action == 'exit_full':
                # Generate full exit instruction blocks
                instruction_blocks.append({
                    'type': 'wallet_transfer',
                    'from_venue': 'aave',
                    'to_venue': 'wallet',
                    'token': 'aUSDT',
                    'amount': current_exposure.get('total_exposure', 0),
                    'estimated_deltas': {
                        'aave': {'aUSDT': -current_exposure.get('total_exposure', 0)},
                        'wallet': {'USDT': current_exposure.get('total_exposure', 0)}
                    }
                })
                
            elif action == 'entry_partial':
                # Generate partial entry instruction blocks
                partial_amount = kwargs.get('deposit_amount', 500.0)
                instruction_blocks.append({
                    'type': 'wallet_transfer',
                    'from_venue': 'wallet',
                    'to_venue': 'aave',
                    'token': 'USDT',
                    'amount': partial_amount,
                    'estimated_deltas': {
                        'wallet': {'USDT': -partial_amount},
                        'aave': {'aUSDT': partial_amount}
                    }
                })
                
            elif action == 'exit_partial':
                # Generate partial exit instruction blocks
                partial_amount = current_exposure.get('total_exposure', 0) * 0.5
                instruction_blocks.append({
                    'type': 'wallet_transfer',
                    'from_venue': 'aave',
                    'to_venue': 'wallet',
                    'token': 'aUSDT',
                    'amount': partial_amount,
                    'estimated_deltas': {
                        'aave': {'aUSDT': -partial_amount},
                        'wallet': {'USDT': partial_amount}
                    }
                })
                
            # For 'sell_dust', no instruction blocks are generated (maintain current position)
            
            return instruction_blocks
            
        except Exception as e:
            logger.error(f"Strategy Manager: Error in generate_instruction_blocks: {e}")
            return []
    
    def _get_current_strategy_state(self) -> Dict[str, Any]:
        """
        Get current strategy state snapshot.
        
        Returns:
            Dict: Current strategy state information
        """
        try:
            return {
                'strategy_type': self.strategy_type,
                'current_state': self.current_strategy_state,
                'available_actions': self.actions,
                'rebalancing_triggers': self.rebalancing_triggers,
                'mode_agnostic': True
            }
        except Exception as e:
            logger.error(f"Strategy Manager: Error getting current strategy state: {e}")
            return {
                'strategy_type': self.strategy_type,
                'current_state': {},
                'error': str(e)
            }
