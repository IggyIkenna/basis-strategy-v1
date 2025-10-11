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

logger = logging.getLogger(__name__)

class ExposureMonitor:
    """Mode-agnostic exposure monitor that works for both backtest and live modes"""
    
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
        
        # Load component-specific configuration
        component_config = config.get('component_config', {})
        exposure_monitor_config = component_config.get('exposure_monitor', {})
        self.exposure_currency = exposure_monitor_config.get('exposure_currency', 'USDT')
        self.track_assets = exposure_monitor_config.get('track_assets', [])
        self.conversion_methods = exposure_monitor_config.get('conversion_methods', {})
        
        # Exposure tracking
        self.last_exposures = None
        
        logger.info("ExposureMonitor initialized (mode-agnostic)")
    
    def calculate_exposures(self, positions: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """
        Calculate exposures regardless of mode (backtest or live).
        
        Args:
            positions: Current position data
            timestamp: Current timestamp
            
        Returns:
            Dictionary with exposure calculation results
        """
        try:
            # Get all positions across all venues
            wallet_positions = self._get_wallet_positions(positions, timestamp)
            smart_contract_positions = self._get_smart_contract_positions(positions, timestamp)
            cex_spot_positions = self._get_cex_spot_positions(positions, timestamp)
            cex_derivatives_positions = self._get_cex_derivatives_positions(positions, timestamp)
            
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
                'total_exposure': exposure_metrics.get('total_usdt_exposure', 0.0),  # Add missing total_exposure field
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
            wallet_data = positions.get('wallet_positions', {})
            
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
            smart_contract_data = positions.get('smart_contract_positions', {})
            
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
            cex_spot_data = positions.get('cex_spot_positions', {})
            
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
            cex_derivatives_data = positions.get('cex_derivatives_positions', {})
            
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
    
    def get_exposure_summary(self) -> Dict[str, Any]:
        """Get exposure summary."""
        try:
            return {
                'last_exposures': self.last_exposures,
                'mode_agnostic': True
            }
        except Exception as e:
            logger.error(f"Error getting exposure summary: {e}")
            return {
                'last_exposures': None,
                'mode_agnostic': True,
                'error': str(e)
            }
    
    def get_config_parameters(self, mode: str) -> Dict[str, Any]:
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