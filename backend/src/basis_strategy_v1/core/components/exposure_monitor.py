"""
Mode-Agnostic Exposure Monitor

Provides mode-agnostic exposure monitoring that works for both backtest and live modes.
Calculates exposures across all venues and provides generic exposure logic.

Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Section 7 (Generic vs Mode-Specific)
Reference: docs/specs/05_EXPOSURE_MONITOR.md - Mode-agnostic exposure calculation
"""

from typing import Dict, List, Any, Optional
import logging
import pandas as pd
from datetime import datetime

from ...core.logging.base_logging_interface import StandardizedLoggingMixin, LogLevel, EventType

logger = logging.getLogger(__name__)

class ExposureMonitor(StandardizedLoggingMixin):
    """Mode-agnostic exposure monitor that works for both backtest and live modes"""
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config: Dict[str, Any], data_provider, utility_manager):
        """
        Initialize exposure monitor.
        
        Args:
            config: Strategy configuration
            data_provider: Data provider instance
            utility_manager: Centralized utility manager
        """
        self.config = config
        self.data_provider = data_provider
        self.utility_manager = utility_manager
        self.health_status = "healthy"
        self.error_count = 0
        
        # Load component-specific configuration
        component_config = config['component_config']
        exposure_monitor_config = component_config['exposure_monitor']
        self.exposure_currency = exposure_monitor_config['exposure_currency']
        self.track_assets = exposure_monitor_config['track_assets']
        self.conversion_methods = exposure_monitor_config['conversion_methods']
        
        # Exposure tracking
        self.last_exposures = None
        
        logger.info("ExposureMonitor initialized (mode-agnostic)")
    
    def _handle_error(self, error: Exception, context: str = "") -> None:
        """Handle errors with structured error handling."""
        self.error_count += 1
        error_code = f"EXP_ERROR_{self.error_count:04d}"
        
        logger.error(f"Exposure Monitor error {error_code}: {str(error)}", extra={
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
            'exposure_currency': self.exposure_currency,
            'track_assets_count': len(self.track_assets),
            'last_exposures_available': self.last_exposures is not None,
            'component': self.__class__.__name__
        }
    
    def calculate_exposure(self, timestamp: pd.Timestamp, position_snapshot: Dict, market_data: Dict) -> Dict[str, Any]:
        """
        Main entry point for exposure calculations.
        
        Args:
            timestamp: Current loop timestamp (from EventDrivenStrategyEngine)
            position_snapshot: Current position data from position_monitor.get_current_positions()
            market_data: Market data from DataProvider (queried by caller)
            
        Returns:
            Dictionary with exposure calculation results
        """
        try:
            # Get all positions across all venues from position_snapshot
            wallet_positions = self._get_wallet_positions(position_snapshot, timestamp)
            smart_contract_positions = self._get_smart_contract_positions(position_snapshot, timestamp)
            cex_spot_positions = self._get_cex_spot_positions(position_snapshot, timestamp)
            cex_derivatives_positions = self._get_cex_derivatives_positions(position_snapshot, timestamp)
            
            # Calculate total exposures
            total_exposures = self._calculate_total_exposures(
                wallet_positions, smart_contract_positions, 
                cex_spot_positions, cex_derivatives_positions, timestamp
            )
            
            # Calculate exposure metrics
            exposure_metrics = self._calculate_exposure_metrics(
                total_exposures, timestamp
            )
            
            # Calculate exposure by category
            exposure_by_category = self._calculate_exposure_by_category(
                wallet_positions, smart_contract_positions, 
                cex_spot_positions, cex_derivatives_positions, timestamp
            )
            
            # Update last exposures
            self._update_last_exposures(total_exposures, timestamp)
            
            return {
                'timestamp': timestamp,
                'total_value_usd': exposure_metrics['total_usdt_exposure'],  # Use total_value_usd for PnL calculator
                'total_exposure': exposure_metrics['total_usdt_exposure'],  # Keep total_exposure for compatibility
                'total_exposures': total_exposures,
                'exposure_metrics': exposure_metrics,
                'exposure_by_category': exposure_by_category,
                'exposure_by_venue': {  # Add missing exposure_by_venue field
                    'wallet': wallet_positions,
                    'smart_contract': smart_contract_positions,
                    'cex_spot': cex_spot_positions,
                    'cex_derivatives': cex_derivatives_positions
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating exposures: {e}")
            return {
                'timestamp': timestamp,
                'total_value_usd': 0.0,  # Add total_value_usd for PnL calculator
                'total_exposure': 0.0,  # Keep total_exposure for compatibility
                'total_exposures': {},
                'exposure_metrics': {},
                'exposure_by_category': {},
                'positions': {},
                'error': str(e)
            }
    
    def _get_wallet_positions(self, positions: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, float]:
        """Get wallet positions from position data."""
        try:
            wallet_positions = {}
            
            # Extract wallet positions from positions
            wallet_data = positions['wallet_positions']
            
            for venue, balances in wallet_data.items():
                for token, amount in balances.items():
                    key = f"{venue}_{token}"
                    wallet_positions[key] = amount
            
            return wallet_positions
        except Exception as e:
            logger.error(f"Error getting wallet positions: {e}")
            return {}
    
    def _get_smart_contract_positions(self, positions: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, float]:
        """Get smart contract positions from position data."""
        try:
            smart_contract_positions = {}
            
            # Extract smart contract positions from positions
            smart_contract_data = positions['smart_contract_positions']
            
            for protocol, balances in smart_contract_data.items():
                for token, amount in balances.items():
                    key = f"{protocol}_{token}"
                    smart_contract_positions[key] = amount
            
            return smart_contract_positions
        except Exception as e:
            logger.error(f"Error getting smart contract positions: {e}")
            return {}
    
    def _get_cex_spot_positions(self, positions: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, float]:
        """Get CEX spot positions from position data."""
        try:
            cex_spot_positions = {}
            
            # Extract CEX spot positions from positions
            cex_spot_data = positions['cex_spot_positions']
            
            for exchange, balances in cex_spot_data.items():
                for token, amount in balances.items():
                    key = f"{exchange}_spot_{token}"
                    cex_spot_positions[key] = amount
            
            return cex_spot_positions
        except Exception as e:
            logger.error(f"Error getting CEX spot positions: {e}")
            return {}
    
    def _get_cex_derivatives_positions(self, positions: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, float]:
        """Get CEX derivatives positions from position data."""
        try:
            cex_derivatives_positions = {}
            
            # Extract CEX derivatives positions from positions
            cex_derivatives_data = positions['cex_derivatives_positions']
            
            for exchange, balances in cex_derivatives_data.items():
                for token, amount in balances.items():
                    key = f"{exchange}_derivatives_{token}"
                    cex_derivatives_positions[key] = amount
            
            return cex_derivatives_positions
        except Exception as e:
            logger.error(f"Error getting CEX derivatives positions: {e}")
            return {}
    
    def _calculate_total_exposures(self, wallet_positions: Dict[str, float], 
                                 smart_contract_positions: Dict[str, float],
                                 cex_spot_positions: Dict[str, float],
                                 cex_derivatives_positions: Dict[str, float],
                                 timestamp: pd.Timestamp) -> Dict[str, float]:
        """Calculate total exposures across all venues."""
        try:
            all_positions = {}
            all_positions.update(wallet_positions)
            all_positions.update(smart_contract_positions)
            all_positions.update(cex_spot_positions)
            all_positions.update(cex_derivatives_positions)
            
            return self.utility_manager.calculate_total_exposures(all_positions, timestamp)
        except Exception as e:
            logger.error(f"Error calculating total exposures: {e}")
            return {}
    
    def _calculate_exposure_metrics(self, total_exposures: Dict[str, float], 
                                  timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Calculate exposure metrics."""
        try:
            metrics = {
                'total_usdt_exposure': 0.0,
                'total_share_class_exposure': 0.0,
                'exposure_concentration': 0.0,
                'exposure_diversification': 0.0
            }
            
            if not total_exposures:
                return metrics
            
            # Calculate total USDT exposure
            total_usdt_exposure = 0.0
            for token, amount in total_exposures.items():
                if amount > 0:
                    usdt_value = self.utility_manager.convert_to_usdt(amount, token, timestamp)
                    total_usdt_exposure += usdt_value
            
            metrics['total_usdt_exposure'] = total_usdt_exposure
            
            # Calculate total share class exposure using config-driven parameters
            # Get share class from mode configuration (config-driven, not hardcoded)
            share_class = self.utility_manager.get_share_class_from_mode('current_mode')  # Will be passed from strategy
            total_share_class_exposure = 0.0
            for token, amount in total_exposures.items():
                if amount > 0:
                    share_class_value = self.utility_manager.convert_to_share_class(
                        amount, token, share_class, timestamp
                    )
                    total_share_class_exposure += share_class_value
            
            metrics['total_share_class_exposure'] = total_share_class_exposure
            
            # Calculate exposure concentration (Herfindahl index)
            if total_usdt_exposure > 0:
                concentration = 0.0
                for token, amount in total_exposures.items():
                    if amount > 0:
                        usdt_value = self.utility_manager.convert_to_usdt(amount, token, timestamp)
                        share = usdt_value / total_usdt_exposure
                        concentration += share ** 2
                metrics['exposure_concentration'] = concentration
            
            # Calculate exposure diversification (1 - concentration)
            metrics['exposure_diversification'] = 1.0 - metrics['exposure_concentration']
            
            return metrics
        except Exception as e:
            logger.error(f"Error calculating exposure metrics: {e}")
            return {}
    
    def _calculate_exposure_by_category(self, wallet_positions: Dict[str, float], 
                                      smart_contract_positions: Dict[str, float],
                                      cex_spot_positions: Dict[str, float],
                                      cex_derivatives_positions: Dict[str, float],
                                      timestamp: pd.Timestamp) -> Dict[str, float]:
        """Calculate exposure by category."""
        try:
            exposure_by_category = {
                'lending': 0.0,
                'staking': 0.0,
                'basis': 0.0,
                'funding': 0.0,
                'delta': 0.0,
                'other': 0.0
            }
            
            # Calculate exposure for each position category
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
                    exposure_by_category[category] += usdt_value
            
            return exposure_by_category
        except Exception as e:
            logger.error(f"Error calculating exposure by category: {e}")
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
    
    def _update_last_exposures(self, total_exposures: Dict[str, float], timestamp: pd.Timestamp):
        """Update last exposures."""
        try:
            self.last_exposures = {
                'timestamp': timestamp,
                'total_exposures': total_exposures
            }
        except Exception as e:
            logger.error(f"Error updating last exposures: {e}")
    
    def get_current_exposure(self) -> Dict[str, Any]:
        """Get current exposure snapshot."""
        try:
            return {
                'last_exposures': self.last_exposures,
                'mode_agnostic': True
            }
        except Exception as e:
            logger.error(f"Error getting current exposure: {e}")
            return {
                'last_exposures': None,
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
    
    def update_state(self, timestamp: pd.Timestamp, trigger_source: str, **kwargs) -> None:
        """
        Update component state (called by EventDrivenStrategyEngine).
        
        Args:
            timestamp: Current loop timestamp (from EventDrivenStrategyEngine)
            trigger_source: 'full_loop' | 'tight_loop' | 'manual'
            **kwargs: Additional parameters (position_snapshot, market_data, etc.)
        """
        # Extract position and market data from kwargs if present
        position_snapshot = kwargs.get('position_snapshot')
        market_data = kwargs.get('market_data')
        
        if position_snapshot and market_data:
            # Perform exposure calculation
            exposure_result = self.calculate_exposure(timestamp, position_snapshot, market_data)
            
            # Log exposure calculation
            logger.info(
                f"Exposure calculation completed: trigger_source={trigger_source}, "
                f"total_value_usd={exposure_result.get('total_value_usd', 0.0):.2f}, "
                f"tracked_assets={len(exposure_result.get('tracked_assets', []))}"
            )
            
            # Log using standardized logging
            self.log_component_event(
                EventType.BUSINESS_EVENT,
                f"Exposure calculation completed: trigger_source={trigger_source}",
                {
                    'total_value_usd': exposure_result.get('total_value_usd', 0.0),
                    'tracked_assets_count': len(exposure_result.get('tracked_assets', [])),
                    'trigger_source': trigger_source
                }
            )