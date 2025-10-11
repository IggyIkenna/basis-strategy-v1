"""
Strategy Manager Component - Factory-Based Implementation

Uses the new factory-based strategy architecture with standardized wrapper actions
and tight loop integration.

Reference: .cursor/tasks/06_strategy_manager_refactor.md
Reference: docs/MODES.md - Standardized Strategy Manager Architecture
"""

from typing import Dict, List, Any, Optional
import logging
import pandas as pd
from datetime import datetime

from ..strategy_factory import StrategyFactory
from ....infrastructure.logging.structured_logger import get_strategy_manager_logger

logger = logging.getLogger(__name__)

class StrategyManager:
    """Factory-based strategy manager implementation."""
    
    def __init__(self, config: Dict[str, Any], data_provider, utility_manager, exposure_monitor=None, risk_monitor=None, event_engine=None):
        """
        Initialize strategy manager.
        
        Args:
            config: Strategy configuration
            data_provider: Data provider instance
            utility_manager: Centralized utility manager
            exposure_monitor: Exposure monitor instance
            risk_monitor: Risk monitor instance
            event_engine: Event engine instance
        """
        self.config = config
        self.data_provider = data_provider
        self.utility_manager = utility_manager
        self.exposure_monitor = exposure_monitor
        self.risk_monitor = risk_monitor
        self.event_engine = event_engine
        
        # Initialize structured logger
        self.structured_logger = get_strategy_manager_logger()
        
        # Get strategy mode from config
        self.mode = config.get('mode', 'pure_lending')
        
        # Load component-specific configuration
        component_config = config.get('component_config', {})
        strategy_manager_config = component_config.get('strategy_manager', {})
        self.strategy_type = strategy_manager_config.get('strategy_type', self.mode)
        self.actions = strategy_manager_config.get('actions', [])
        self.rebalancing_triggers = strategy_manager_config.get('rebalancing_triggers', [])
        self.position_calculation = strategy_manager_config.get('position_calculation', {})
        
        # Create strategy instance using factory
        try:
            self.strategy = StrategyFactory.create_strategy(
                mode=self.mode,
                config=config,
                risk_monitor=risk_monitor,
                position_monitor=self,  # Strategy manager acts as position monitor interface
                event_engine=event_engine
            )
            
            self.structured_logger.info(
                f"StrategyManager initialized with {self.mode} strategy",
                event_type="component_initialization",
                component="strategy_manager",
                mode=self.mode
            )
            
        except Exception as e:
            self.structured_logger.error(
                f"Failed to create strategy: {e}",
                event_type="strategy_creation_error",
                error=str(e),
                mode=self.mode
            )
            self.strategy = None
    
    def calculate_strategy_actions(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """
        Calculate strategy actions using the strategy instance.
        
        Args:
            timestamp: Current timestamp
        
        Returns:
            Dictionary with strategy actions
        """
        try:
            if self.strategy is None:
                return {
                    'actions': [],
                    'timestamp': timestamp,
                    'status': 'error',
                    'error': 'No strategy instance available'
                }
            
            # Get market data (placeholder for now)
            market_data = {}
            
            # Make strategy decision
            action = self.strategy.make_decision(timestamp, market_data)
            
            if action:
                return {
                    'actions': [action.model_dump()],
                    'timestamp': timestamp,
                    'status': 'action_generated',
                    'mode': self.mode
                }
            else:
                return {
                    'actions': [],
                    'timestamp': timestamp,
                    'status': 'no_action_needed',
                    'mode': self.mode
                }
                
        except Exception as e:
            self.structured_logger.error(
                f"Error calculating strategy actions: {e}",
                event_type="strategy_action_error",
                error=str(e),
                timestamp=timestamp.isoformat()
            )
            return {
                'actions': [],
                'timestamp': timestamp,
                'status': 'error',
                'error': str(e)
            }
    
    def get_current_positions(self) -> Dict[str, Any]:
        """
        Get current positions (interface for strategy).
        
        Returns:
            Dictionary with current positions
        """
        try:
            # This is a placeholder - in production, this would get actual positions
            # from the position monitor or other data sources
            return {
                'wallet': {},
                'smart_contract': {},
                'cex_spot': {},
                'cex_derivatives': {}
            }
        except Exception as e:
            self.structured_logger.error(
                f"Error getting current positions: {e}",
                event_type="position_error",
                error=str(e)
            )
            return {}