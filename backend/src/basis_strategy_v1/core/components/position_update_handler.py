"""
Position Monitor Update Handler

TODO-REFACTOR: TIGHT LOOP ARCHITECTURE VIOLATION - See docs/REFERENCE_ARCHITECTURE_CANONICAL.md
ISSUE: This component may violate tight loop architecture requirements:

1. TIGHT LOOP ARCHITECTURE REQUIREMENTS:
   - Components must follow strict tight loop sequence
   - Proper event processing order
   - No state clearing between iterations
   - Consistent processing flow

2. REQUIRED VERIFICATION:
   - Verify tight loop sequence is enforced
   - Check for proper event processing order
   - Ensure no state clearing violations
   - Validate consistent processing flow

3. CANONICAL SOURCE:
   - docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Tight Loop Architecture
   - Tight loop sequence must be enforced

Provides a tight loop abstraction for position monitor updates that automatically triggers
the exposure → risk → P&L calculation sequence.

This ensures that any component performing an action always has access to the most
up-to-date position, exposure, risk, and P&L data.

Architecture:
- Strategy Manager: READ-ONLY, queries state, never updates position monitor
- Execution Interfaces: Write updates to position monitor (backtest) or trigger refresh (live)
- Position Update Handler: Manages the tight loop (position → exposure → risk → P&L)
- Event Engine: Orchestrates the overall flow

Live vs Backtest Mode:
- Backtest Mode: Position monitor is updated with simulated changes
- Live Mode: Position monitor refreshes from actual exchange connections
"""

import logging
import pandas as pd
from typing import Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Create dedicated position update handler logger
position_update_logger = logging.getLogger('position_update_handler')
position_update_logger.setLevel(logging.INFO)

# Create logs directory if it doesn't exist
from pathlib import Path
logs_dir = Path(__file__).parent.parent.parent.parent.parent.parent / 'logs'
logs_dir.mkdir(exist_ok=True)

# Create file handler for position update handler logs
position_update_handler = logging.FileHandler(logs_dir / 'position_update_handler.log')
position_update_handler.setLevel(logging.INFO)

# Create formatter
position_update_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
position_update_handler.setFormatter(position_update_formatter)

# Add handler to logger if not already added
if not position_update_logger.handlers:
    position_update_logger.addHandler(position_update_handler)
    position_update_logger.propagate = False


class PositionUpdateHandler:
    """
    Manages the tight loop between position monitor updates and downstream components.
    
    This class ensures that whenever the position monitor is updated, the exposure,
    risk, and P&L monitors are automatically recalculated in sequence.
    
    This abstraction simplifies the event engine and execution interfaces by providing
    a single point of control for the tight loop.
    """
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, 
                 config: Dict[str, Any],
                 position_monitor,
                 exposure_monitor,
                 risk_monitor,
                 pnl_calculator):
        """
        Initialize position update handler (mode-agnostic).
        
        Args:
            config: Strategy configuration
            position_monitor: Position monitor instance
            exposure_monitor: Exposure monitor instance
            risk_monitor: Risk monitor instance
            pnl_calculator: P&L calculator instance
        """
        self.config = config
        self.position_monitor = position_monitor
        self.exposure_monitor = exposure_monitor
        self.risk_monitor = risk_monitor
        self.pnl_calculator = pnl_calculator
        
        position_update_logger.info(f"Position Update Handler initialized (mode-agnostic)")
    
    def handle_position_update(self, 
                                   changes: Dict[str, Any], 
                                   timestamp: pd.Timestamp,
                                   market_data: Dict[str, Any] = None,
                                   trigger_component: str = 'unknown') -> Dict[str, Any]:
        """
        Handle position monitor update and trigger the tight loop.
        
        This method:
        1. Updates the position monitor (backtest) or triggers refresh (live)
        2. Recalculates exposure
        3. Reassesses risk
        4. Recalculates P&L
        
        Args:
            changes: Position changes to apply (backtest mode only)
            timestamp: Current timestamp
            market_data: Market data for calculations
            trigger_component: Component that triggered the update
            
        Returns:
            Dictionary with updated exposure, risk, and P&L data
        """
        try:
            position_update_logger.info(f"Position Update Handler: Handling update from {trigger_component}")
            
            # Step 1: Update position monitor (mode-agnostic)
            # Use configuration to determine behavior instead of mode checks
            use_simulated_changes = self.config.get('use_simulated_changes', True)
            
            if use_simulated_changes:
                # Apply simulated changes (backtest behavior)
                position_update_logger.info(f"Position Update Handler: Applying simulated changes")
                # Ensure timestamp is in the correct format for position monitor
                if 'timestamp' in changes and not isinstance(changes['timestamp'], pd.Timestamp):
                    changes['timestamp'] = pd.Timestamp(changes['timestamp'])
                updated_snapshot =  self.position_monitor.update(changes)
            else:
                # Refresh from actual exchange connections (live behavior)
                position_update_logger.info(f"Position Update Handler: Refreshing position from exchanges")
                updated_snapshot =  self.position_monitor.refresh_from_exchanges()
            
            # Step 2: Recalculate exposure
            position_update_logger.info(f"Position Update Handler: Recalculating exposure")
            updated_exposure = self.exposure_monitor.calculate_exposure(
                timestamp=timestamp,
                position_snapshot=updated_snapshot,
                market_data=market_data or {}
            )
            position_update_logger.info(f"Position Update Handler: Exposure recalculated - total_value_usd = {updated_exposure.get('total_value_usd', 0)}")
            
            # Step 3: Reassess risk
            position_update_logger.info(f"Position Update Handler: Reassessing risk")
            updated_risk =  self.risk_monitor.assess_risk(
                exposure_data=updated_exposure,
                market_data=market_data or {}
            )
            position_update_logger.info(f"Position Update Handler: Risk reassessed")
            
            # Step 4: Recalculate P&L
            position_update_logger.info(f"Position Update Handler: Recalculating P&L")
            try:
                updated_pnl =  self.pnl_calculator.calculate_pnl(
                    current_exposure=updated_exposure,
                    timestamp=timestamp
                )
                position_update_logger.info(f"Position Update Handler: P&L recalculated successfully")
            except Exception as e:
                position_update_logger.error(f"Position Update Handler: P&L recalculation failed: {e}")
                # Create default P&L structure to avoid downstream errors
                updated_pnl = {
                    'balance_based': {'pnl_cumulative': 0.0, 'pnl_pct': 0.0},
                    'attribution': {'pnl_cumulative': 0.0},
                    'error': str(e)
                }
            
            position_update_logger.info(f"Position Update Handler: Tight loop completed successfully")
            
            return {
                'success': True,
                'position_snapshot': updated_snapshot,
                'exposure': updated_exposure,
                'risk': updated_risk,
                'pnl': updated_pnl,
                'trigger_component': trigger_component,
                'mode_agnostic': True
            }
            
        except Exception as e:
            position_update_logger.error(f"Position Update Handler: Tight loop failed: {e}")
            raise
    
    def handle_atomic_position_update(self,
                                          changes: Dict[str, Any],
                                          timestamp: pd.Timestamp,
                                          market_data: Dict[str, Any] = None,
                                          trigger_component: str = 'atomic_operation') -> Dict[str, Any]:
        """
        Handle position monitor update for atomic operations.
        
        For atomic operations, we skip the tight loop until the entire atomic block completes.
        This prevents intermediate calculations that might not reflect the final state.
        
        Args:
            changes: Position changes to apply (backtest mode only)
            timestamp: Current timestamp
            market_data: Market data for calculations
            trigger_component: Component that triggered the update
            
        Returns:
            Dictionary with updated position snapshot only
        """
        try:
            position_update_logger.info(f"Position Update Handler: Handling atomic update from {trigger_component}")
            
            # For atomic operations, only update position monitor (mode-agnostic)
            # Use configuration to determine behavior instead of mode checks
            use_simulated_changes = self.config.get('use_simulated_changes', True)
            
            if use_simulated_changes:
                # Ensure timestamp is in the correct format for position monitor
                if 'timestamp' in changes and not isinstance(changes['timestamp'], pd.Timestamp):
                    changes['timestamp'] = pd.Timestamp(changes['timestamp'])
                updated_snapshot =  self.position_monitor.update(changes)
            else:
                updated_snapshot =  self.position_monitor.refresh_from_exchanges()
            
            position_update_logger.info(f"Position Update Handler: Atomic position update completed")
            
            return {
                'success': True,
                'position_snapshot': updated_snapshot,
                'trigger_component': trigger_component,
                'mode_agnostic': True,
                'atomic_mode': True
            }
            
        except Exception as e:
            position_update_logger.error(f"Position Update Handler: Atomic update failed: {e}")
            raise
    
    def trigger_tight_loop_after_atomic(self,
                                            timestamp: pd.Timestamp,
                                            market_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Trigger the tight loop after atomic operations complete.
        
        This method is called after all atomic operations in a block are complete
        to ensure the exposure, risk, and P&L are recalculated with the final state.
        
        Args:
            timestamp: Current timestamp
            market_data: Market data for calculations
            
        Returns:
            Dictionary with updated exposure, risk, and P&L data
        """
        try:
            position_update_logger.info(f"Position Update Handler: Triggering tight loop after atomic operations")
            
            # Get current position snapshot
            current_snapshot = self.position_monitor.get_snapshot()
            
            # Recalculate exposure
            updated_exposure = self.exposure_monitor.calculate_exposure(
                timestamp=timestamp,
                position_snapshot=current_snapshot,
                market_data=market_data or {}
            )
            
            # Reassess risk
            updated_risk =  self.risk_monitor.assess_risk(
                exposure_data=updated_exposure,
                market_data=market_data or {}
            )
            
            # Recalculate P&L
            try:
                updated_pnl =  self.pnl_calculator.calculate_pnl(
                    current_exposure=updated_exposure,
                    timestamp=timestamp
                )
            except Exception as e:
                position_update_logger.error(f"Position Update Handler: P&L recalculation failed after atomic: {e}")
                updated_pnl = {
                    'balance_based': {'pnl_cumulative': 0.0, 'pnl_pct': 0.0},
                    'attribution': {'pnl_cumulative': 0.0},
                    'error': str(e)
                }
            
            position_update_logger.info(f"Position Update Handler: Tight loop after atomic operations completed")
            
            return {
                'success': True,
                'exposure': updated_exposure,
                'risk': updated_risk,
                'pnl': updated_pnl,
                'mode_agnostic': True,
                'post_atomic': True
            }
            
        except Exception as e:
            position_update_logger.error(f"Position Update Handler: Tight loop after atomic failed: {e}")
            raise
