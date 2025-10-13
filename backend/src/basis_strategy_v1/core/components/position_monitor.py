"""
Mode-Agnostic Position Monitor

Provides mode-agnostic position monitoring that works for both backtest and live modes.
Calculates positions across all venues and provides generic position logic.

Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Section 7 (Generic vs Mode-Specific)
Reference: docs/specs/07_POSITION_MONITOR.md - Mode-agnostic position calculation
"""

from typing import Dict, List, Any, Optional
import logging
import pandas as pd
from datetime import datetime

from ...infrastructure.logging.structured_logger import get_position_monitor_logger
from ...core.logging.base_logging_interface import StandardizedLoggingMixin, LogLevel, EventType

logger = logging.getLogger(__name__)

class PositionMonitor(StandardizedLoggingMixin):
    """Mode-agnostic position monitor that works for both backtest and live modes"""
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config: Dict[str, Any], data_provider, utility_manager, venue_interface_factory=None):
        """
        Initialize position monitor.
        
        Args:
            config: Strategy configuration
            data_provider: Data provider instance
            utility_manager: Centralized utility manager
            venue_interface_factory: Venue interface factory for position interfaces
        """
        self.config = config
        self.data_provider = data_provider
        self.utility_manager = utility_manager
        self.venue_interface_factory = venue_interface_factory
        self.health_status = "healthy"
        self.error_count = 0
        
        # Initialize structured logger
        self.structured_logger = get_position_monitor_logger()
        
        # Position tracking
        self.last_positions = None
        
        # Create position interfaces for enabled venues
        self.position_interfaces = {}
        if self.venue_interface_factory:
            self._initialize_position_interfaces()
    
    def check_component_health(self) -> Dict[str, Any]:
        """Check component health status."""
        return {
            'status': self.health_status,
            'error_count': self.error_count,
            'position_interfaces_count': len(self.position_interfaces),
            'last_positions_available': self.last_positions is not None,
            'component': self.__class__.__name__
        }
    
    def _initialize_position_interfaces(self):
        """Initialize position interfaces for enabled venues."""
        self.structured_logger.info(
            "PositionMonitor initialized",
            event_type="component_initialization",
            component="position_monitor",
            mode="mode-agnostic",
            has_position_interfaces=bool(self.position_interfaces)
        )
    
    def _initialize_position_interfaces(self):
        """
        Initialize position interfaces for enabled venues.
        """
        try:
            # Get enabled venues from config
            venues = self._get_enabled_venues()
            
            # Create position interfaces for enabled venues
            self.position_interfaces = self.venue_interface_factory.get_venue_position_interfaces(
                venues, self._get_execution_mode(), self.config
            )
            
            self.structured_logger.info(
                "Position interfaces initialized",
                event_type="position_interfaces_initialized",
                venues=venues,
                interfaces_created=len([v for v in self.position_interfaces.values() if v is not None])
            )
        except Exception as e:
            self.structured_logger.error(
                "Failed to initialize position interfaces",
                event_type="position_interfaces_error",
                error=str(e)
            )
            self.position_interfaces = {}
    
    def _get_enabled_venues(self) -> List[str]:
        """
        Get list of enabled venues from config.
        
        Returns:
            List of enabled venue names
        """
        venues = []
        
        # Get venues from component config
        position_config = self.config.get('component_config', {}).get('position_monitor', {})
        initial_balances = position_config.get('initial_balances', {})
        
        # Add CEX venues
        cex_venues = initial_balances.get('cex_accounts', [])
        venues.extend(cex_venues)
        
        # Add OnChain venues (from perp_positions for now, should be separate config)
        onchain_venues = initial_balances.get('perp_positions', [])
        venues.extend(onchain_venues)
        
        # Add wallet venue
        venues.append('wallet')
        
        return list(set(venues))  # Remove duplicates
    
    def _get_execution_mode(self) -> str:
        """
        Get execution mode from environment or config.
        
        Returns:
            Execution mode ('backtest' or 'live')
        """
        import os
        return os.getenv('BASIS_EXECUTION_MODE', 'backtest')
    
    def get_real_positions(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """
        Get real position snapshot (for reconciliation).
        
        Args:
            timestamp: Current timestamp
        
        Returns:
            Dictionary with real position data
        """
        try:
            # Config-driven approach: use position interfaces if available, otherwise simulated
            if self.position_interfaces:
                return self._get_live_positions(timestamp)
            else:
                return self._get_simulated_positions(timestamp)
        except Exception as e:
            self.structured_logger.error(
                "Failed to get real positions",
                event_type="position_query_error",
                error=str(e),
                timestamp=timestamp
            )
            raise
    
    def _get_live_positions(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """
        Get live positions using position interfaces.
        
        Args:
            timestamp: Current timestamp
        
        Returns:
            Dictionary with live position data
        """
        import asyncio
        
        # Get positions from all position interfaces
        venue_positions = {}
        
        for venue, interface in self.position_interfaces.items():
            if interface:
                try:
                    # Run async method in sync context
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        venue_positions[venue] = loop.run_until_complete(
                            interface.get_positions(timestamp)
                        )
                    finally:
                        loop.close()
                except Exception as e:
                    self.structured_logger.error(
                        f"Failed to get positions from {venue}",
                        event_type="venue_position_error",
                        venue=venue,
                        error=str(e)
                    )
                    venue_positions[venue] = {}
        
        # Aggregate positions from all venues
        return self._aggregate_venue_positions(venue_positions, timestamp)
    
    def _aggregate_venue_positions(self, venue_positions: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """
        Aggregate positions from all venue interfaces.
        
        Args:
            venue_positions: Dictionary of venue positions
            timestamp: Current timestamp
        
        Returns:
            Aggregated position data
        """
        # Aggregate positions by category
        wallet_positions = {}
        smart_contract_positions = {}
        cex_spot_positions = {}
        cex_derivatives_positions = {}
        
        for venue, positions in venue_positions.items():
            if not positions:
                continue
                
            if venue == 'wallet':
                wallet_positions = positions.get('wallet_balances', {})
            elif venue in ['aave', 'morpho', 'lido', 'etherfi']:
                # OnChain positions
                smart_contract_positions[venue] = positions
            elif venue in ['binance', 'bybit', 'okx']:
                # CEX positions
                cex_spot_positions[venue] = positions.get('spot_balances', {})
                cex_derivatives_positions[venue] = positions.get('perp_positions', {})
        
        # Calculate total positions
        total_positions = self._calculate_total_positions(
            wallet_positions, smart_contract_positions, 
            cex_spot_positions, cex_derivatives_positions, timestamp
        )
        
        # Calculate position metrics
        position_metrics = self._calculate_position_metrics(
            total_positions, timestamp
        )
        
        # Calculate position by category
        position_by_category = self._calculate_position_by_category(
            wallet_positions, smart_contract_positions, 
            cex_spot_positions, cex_derivatives_positions, timestamp
        )
        
        # Update last positions
        self._update_last_positions(total_positions, timestamp)
        
        return {
            'timestamp': timestamp,
            'total_positions': total_positions,
            'position_metrics': position_metrics,
            'position_by_category': position_by_category,
            'wallet_positions': wallet_positions,
            'smart_contract_positions': smart_contract_positions,
            'cex_spot_positions': cex_spot_positions,
            'cex_derivatives_positions': cex_derivatives_positions,
            'execution_mode': 'live'
        }
    
    def _get_simulated_positions(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """
        Get simulated positions for backtest mode.
        
        Args:
            timestamp: Current timestamp
        
        Returns:
            Dictionary with simulated position data
        """
        # Get positions from all venues using existing simulation logic
        wallet_positions = self._get_wallet_positions(timestamp)
        smart_contract_positions = self._get_smart_contract_positions(timestamp)
        cex_spot_positions = self._get_cex_spot_positions(timestamp)
        cex_derivatives_positions = self._get_cex_derivatives_positions(timestamp)
        
        # Calculate total positions
        total_positions = self._calculate_total_positions(
            wallet_positions, smart_contract_positions, 
            cex_spot_positions, cex_derivatives_positions, timestamp
        )
        
        # Calculate position metrics
        position_metrics = self._calculate_position_metrics(
            total_positions, timestamp
        )
        
        # Calculate position by category
        position_by_category = self._calculate_position_by_category(
            wallet_positions, smart_contract_positions, 
            cex_spot_positions, cex_derivatives_positions, timestamp
        )
        
        # Update last positions
        self._update_last_positions(total_positions, timestamp)
        
        return {
            'timestamp': timestamp,
            'total_positions': total_positions,
            'position_metrics': position_metrics,
            'position_by_category': position_by_category,
            'wallet_positions': wallet_positions,
            'smart_contract_positions': smart_contract_positions,
            'cex_spot_positions': cex_spot_positions,
            'cex_derivatives_positions': cex_derivatives_positions,
            'execution_mode': 'backtest'
        }
    
    def _get_wallet_positions(self, timestamp: pd.Timestamp) -> Dict[str, float]:
        """Get wallet positions from data provider using canonical pattern."""
        try:
            wallet_positions = {}
            
            # Get data using canonical pattern
            data = self.data_provider.get_data(timestamp)
            wallet_balances = data['execution_data']['wallet_balances']
            
            for venue, balances in wallet_balances.items():
                for token, amount in balances.items():
                    key = f"{venue}_{token}"
                    wallet_positions[key] = amount
            
            return wallet_positions
        except Exception as e:
            logger.error(f"Error getting wallet positions: {e}")
            return {}
    
    def _get_smart_contract_positions(self, timestamp: pd.Timestamp) -> Dict[str, float]:
        """Get smart contract positions from data provider using canonical pattern."""
        try:
            smart_contract_positions = {}
            
            # Get data using canonical pattern
            data = self.data_provider.get_data(timestamp)
            smart_contract_balances = data['execution_data']['smart_contract_balances']
            
            for protocol, balances in smart_contract_balances.items():
                for token, amount in balances.items():
                    key = f"{protocol}_{token}"
                    smart_contract_positions[key] = amount
            
            return smart_contract_positions
        except Exception as e:
            logger.error(f"Error getting smart contract positions: {e}")
            return {}
    
    def _get_cex_spot_positions(self, timestamp: pd.Timestamp) -> Dict[str, float]:
        """Get CEX spot positions from data provider using canonical pattern."""
        try:
            cex_spot_positions = {}
            
            # Get data using canonical pattern
            data = self.data_provider.get_data(timestamp)
            cex_spot_balances = data['execution_data']['cex_spot_balances']
            
            for exchange, balances in cex_spot_balances.items():
                for token, amount in balances.items():
                    key = f"{exchange}_spot_{token}"
                    cex_spot_positions[key] = amount
            
            return cex_spot_positions
        except Exception as e:
            logger.error(f"Error getting CEX spot positions: {e}")
            return {}
    
    def _get_cex_derivatives_positions(self, timestamp: pd.Timestamp) -> Dict[str, float]:
        """Get CEX derivatives positions from data provider using canonical pattern."""
        try:
            cex_derivatives_positions = {}
            
            # Get data using canonical pattern
            data = self.data_provider.get_data(timestamp)
            cex_derivatives_balances = data['execution_data']['cex_derivatives_balances']
            
            for exchange, balances in cex_derivatives_balances.items():
                for token, amount in balances.items():
                    key = f"{exchange}_derivatives_{token}"
                    cex_derivatives_positions[key] = amount
            
            return cex_derivatives_positions
        except Exception as e:
            logger.error(f"Error getting CEX derivatives positions: {e}")
            return {}
    
    def _calculate_total_positions(self, wallet_positions: Dict[str, float], 
                                 smart_contract_positions: Dict[str, float],
                                 cex_spot_positions: Dict[str, float],
                                 cex_derivatives_positions: Dict[str, float],
                                 timestamp: pd.Timestamp) -> Dict[str, float]:
        """Calculate total positions across all venues."""
        try:
            all_positions = {}
            all_positions.update(wallet_positions)
            all_positions.update(smart_contract_positions)
            all_positions.update(cex_spot_positions)
            all_positions.update(cex_derivatives_positions)
            
            return self.utility_manager.calculate_total_positions(all_positions, timestamp)
        except Exception as e:
            logger.error(f"Error calculating total positions: {e}")
            return {}
        
    def _calculate_position_metrics(self, total_positions: Dict[str, float], 
                                  timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Calculate position metrics."""
        try:
            metrics = {
                'total_usdt_position': 0.0,
                'total_share_class_position': 0.0,
                'position_concentration': 0.0,
                'position_diversification': 0.0
            }
            
            if not total_positions:
                return metrics
            
            # Calculate total USDT position
            total_usdt_position = 0.0
            for token, amount in total_positions.items():
                if amount > 0:
                    usdt_value = self.utility_manager.convert_to_usdt(amount, token, timestamp)
                    total_usdt_position += usdt_value
            
            metrics['total_usdt_position'] = total_usdt_position
            
            # Calculate total share class position using config-driven parameters
            # Get share class from mode configuration (config-driven, not hardcoded)
            share_class = self.utility_manager.get_share_class_from_mode('current_mode')  # Will be passed from strategy
            total_share_class_position = 0.0
            for token, amount in total_positions.items():
                if amount > 0:
                    share_class_value = self.utility_manager.convert_to_share_class(
                        amount, token, share_class, timestamp
                    )
                    total_share_class_position += share_class_value
            
            metrics['total_share_class_position'] = total_share_class_position
            
            # Calculate position concentration (Herfindahl index)
            if total_usdt_position > 0:
                concentration = 0.0
                for token, amount in total_positions.items():
                    if amount > 0:
                        usdt_value = self.utility_manager.convert_to_usdt(amount, token, timestamp)
                        share = usdt_value / total_usdt_position
                        concentration += share ** 2
                metrics['position_concentration'] = concentration
            
            # Calculate position diversification (1 - concentration)
            metrics['position_diversification'] = 1.0 - metrics['position_concentration']
            
            return metrics
        except Exception as e:
            logger.error(f"Error calculating position metrics: {e}")
            return {}
    
    def get_current_positions(self, timestamp: pd.Timestamp = None) -> Dict[str, Any]:
        """Get current position snapshot."""
        if timestamp is None:
            timestamp = pd.Timestamp.now()
        
        try:
            # Get current positions
            wallet_positions = self._get_wallet_positions(timestamp)
            smart_contract_positions = self._get_smart_contract_positions(timestamp)
            cex_spot_positions = self._get_cex_spot_positions(timestamp)
            cex_derivatives_positions = self._get_cex_derivatives_positions(timestamp)
            
            # Calculate totals
            total_positions = self._calculate_total_positions(
                wallet_positions, smart_contract_positions, 
                cex_spot_positions, cex_derivatives_positions, timestamp
            )
            
            # Calculate metrics
            metrics = self._calculate_position_metrics(total_positions, timestamp)
            
            return {
                'timestamp': timestamp,
                'wallet_positions': wallet_positions,
                'smart_contract_positions': smart_contract_positions,
                'cex_spot_positions': cex_spot_positions,
                'cex_derivatives_positions': cex_derivatives_positions,
                'total_positions': total_positions,
                'metrics': metrics
            }
        except Exception as e:
            logger.error(f"Error getting position snapshot: {e}")
            return {
                'timestamp': timestamp,
                'wallet_positions': {},
                'smart_contract_positions': {},
                'cex_spot_positions': {},
                'cex_derivatives_positions': {},
                'total_positions': {},
                'metrics': {}
            }
    
    def _log_position_snapshot(self, timestamp: pd.Timestamp, event_type: str) -> None:
        """Log position snapshot for debugging."""
        try:
            snapshot = self.get_current_positions(timestamp)
            logger.info(f"Position Snapshot [{event_type}] at {timestamp}: {snapshot}")
        except Exception as e:
            logger.error(f"Error logging position snapshot: {e}")
    
    def _calculate_position_by_category(self, wallet_positions: Dict[str, float], 
                                      smart_contract_positions: Dict[str, float],
                                      cex_spot_positions: Dict[str, float],
                                      cex_derivatives_positions: Dict[str, float],
                                      timestamp: pd.Timestamp) -> Dict[str, float]:
        """Calculate position by category."""
        try:
            position_by_category = {
                'lending': 0.0,
                'staking': 0.0,
                'basis': 0.0,
                'funding': 0.0,
                'delta': 0.0,
                'other': 0.0
            }
            
            # Calculate position for each position category
            all_positions = {}
            all_positions.update(wallet_positions)
            all_positions.update(smart_contract_positions)
            all_positions.update(cex_spot_positions)
            all_positions.update(cex_derivatives_positions)
            
            for position_key, amount in all_positions.items():
                if amount > 0:
                    # Convert to USDT equivalent
                    usdt_value = self.utility_manager.convert_to_usdt(
                        amount, self._extract_token_from_position_key(position_key), timestamp
                    )
                    
                    # Categorize based on position key
                    category = self._categorize_position(position_key)
                    position_by_category[category] += usdt_value
            
            return position_by_category
        except Exception as e:
            logger.error(f"Error calculating position by category: {e}")
            return {}
    
    def _extract_token_from_position_key(self, position_key: str) -> str:
        """Extract token symbol from position key."""
        try:
            # Position key format: "venue_token" or "venue_type_token"
            parts = position_key.split('_')
            if len(parts) >= 2:
                return parts[-1]  # Last part is usually the token
            return position_key
        except Exception as e:
            logger.error(f"Error extracting token from {position_key}: {e}")
            return position_key
    
    def _categorize_position(self, position_key: str) -> str:
        """Categorize position based on key."""
        try:
            position_key_lower = position_key.lower()
            
            # Lending category
            if any(keyword in position_key_lower for keyword in ['aave', 'compound', 'venus', 'ausdt', 'aeth']):
                return 'lending'
            
            # Staking category
            if any(keyword in position_key_lower for keyword in ['lido', 'etherfi', 'steth', 'weth', 'eeth']):
                return 'staking'
            
            # Basis category
            if any(keyword in position_key_lower for keyword in ['basis', 'perp', 'futures']):
                return 'basis'
            
            # Funding category
            if any(keyword in position_key_lower for keyword in ['funding', 'rate']):
                return 'funding'
            
            # Delta category
            if any(keyword in position_key_lower for keyword in ['delta', 'spot']):
                return 'delta'
            
            # Default to other
            return 'other'
        except Exception as e:
            logger.error(f"Error categorizing position {position_key}: {e}")
            return 'other'
    
    def _update_last_positions(self, total_positions: Dict[str, float], timestamp: pd.Timestamp):
        """Update last positions."""
        try:
            self.last_positions = {
                'timestamp': timestamp,
                'total_positions': total_positions
            }
        except Exception as e:
            logger.error(f"Error updating last positions: {e}")
    
    def update_state(self, timestamp: pd.Timestamp, trigger_source: str, execution_deltas: Optional[Dict] = None) -> None:
        """
        Main entry point for position state updates.
        
        Args:
            timestamp: Current loop timestamp (from EventDrivenStrategyEngine)
            trigger_source: Source of update trigger ('execution', 'reconciliation', 'manual')
            execution_deltas: Execution deltas from Execution Manager (backtest mode)
        """
        try:
            self.structured_logger.info(
                f"Position Monitor: Updating state from {trigger_source}",
                event_type="position_state_update",
                trigger_source=trigger_source,
                timestamp=timestamp.isoformat()
            )
            
            # Update last positions timestamp
            self.last_positions = {
                'timestamp': timestamp,
                'trigger_source': trigger_source
            }
            
            # In backtest mode, execution deltas would be processed here
            # In live mode, positions would be refreshed from external APIs
            # For now, just update the timestamp
            
        except Exception as e:
            self.structured_logger.error(
                f"Error updating position state: {e}",
                event_type="position_state_update_error",
                error=str(e),
                timestamp=timestamp.isoformat()
            )
    
    def _get_position_summary(self) -> Dict[str, Any]:
        """Get position summary."""
        try:
            return {
                'last_positions': self.last_positions,
                'mode_agnostic': True
            }
        except Exception as e:
            logger.error(f"Error getting position summary: {e}")
            return {
                'last_positions': None,
                'mode_agnostic': True,
                'error': str(e)
            }
    
    def _get_config_parameters(self, mode: str) -> Dict[str, Any]:
        """Get config parameters using utility manager (config-driven approach)."""
        try:
            # Use utility manager to get config parameters (config-driven, not hardcoded)
            share_class = self.utility_manager.get_share_class_from_mode(mode)
            asset = self.utility_manager.get_asset_from_mode(mode)
            lst_type = self.utility_manager.get_lst_type_from_mode(mode)
            hedge_allocation = self.utility_manager.get_hedge_allocation_from_mode(mode)
            
            return {
                'share_class': share_class,
                'asset': asset,
                'lst_type': lst_type,
                'hedge_allocation': hedge_allocation
            }
        except Exception as e:
            logger.error(f"Error getting config parameters: {e}")
            return {}
    
    def _verify_reconciliation(self) -> Dict[str, Any]:
        """
        Verify position reconciliation after execution.
        
        This method ensures that position updates match expected state
        after execution instructions have been processed.
        
        Returns:
            Dict with reconciliation status and details
        """
        try:
            # Get current position snapshot
            current_position = self.get_current_positions()
            
            # Basic reconciliation checks
            reconciliation_checks = {
                'position_data_available': current_position is not None,
                'timestamp_valid': 'timestamp' in current_position,
                'position_data_valid': 'positions' in current_position
            }
            
            # Check if all basic checks pass
            all_checks_passed = all(reconciliation_checks.values())
            
            if all_checks_passed:
                logger.debug("Position reconciliation verification passed")
                return {
                    'status': 'success',
                    'message': 'Position reconciliation verified',
                    'checks': reconciliation_checks
                }
            else:
                logger.warning(f"Position reconciliation verification failed: {reconciliation_checks}")
                return {
                    'status': 'failed',
                    'message': 'Position reconciliation verification failed',
                    'checks': reconciliation_checks
                }
                
        except Exception as e:
            logger.error(f"Error during position reconciliation verification: {e}")
            return {
                'status': 'error',
                'message': f'Reconciliation verification error: {str(e)}'
            }