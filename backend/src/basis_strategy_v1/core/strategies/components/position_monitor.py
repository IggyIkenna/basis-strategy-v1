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

from ....infrastructure.logging.structured_logger import get_position_monitor_logger

logger = logging.getLogger(__name__)

class PositionMonitor:
    """Mode-agnostic position monitor that works for both backtest and live modes"""
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config: Dict[str, Any], data_provider, utility_manager):
        """
        Initialize position monitor.
        
        Args:
            config: Strategy configuration
            data_provider: Data provider instance
            utility_manager: Centralized utility manager
        """
        self.config = config
        self.data_provider = data_provider
        self.utility_manager = utility_manager
        
        # Initialize structured logger
        self.structured_logger = get_position_monitor_logger()
        
        # Position tracking
        self.last_positions = None
        
        self.structured_logger.info(
            "PositionMonitor initialized",
            event_type="component_initialization",
            component="position_monitor",
            mode="mode-agnostic"
        )
    
    def calculate_positions(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """
        Calculate positions regardless of mode (backtest or live).
        
        Args:
            timestamp: Current timestamp
        
        Returns:
            Dictionary with position calculation results
        """
        try:
            # Get positions from all venues
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
                'positions': {
                    'wallet': wallet_positions,
                    'smart_contract': smart_contract_positions,
                    'cex_spot': cex_spot_positions,
                    'cex_derivatives': cex_derivatives_positions
                }
            }
            
        except Exception as e:
            self.structured_logger.error(
                f"Error calculating positions: {e}",
                event_type="position_calculation_error",
                error=str(e),
                timestamp=timestamp.isoformat()
            )
            return {
                'timestamp': timestamp,
                'total_positions': {},
                'position_metrics': {},
                'position_by_category': {},
                'wallet_positions': {},
                'smart_contract_positions': {},
                'cex_spot_positions': {},
                'cex_derivatives_positions': {},
                'positions': {},
                'error': str(e)
            }
    
    def _get_wallet_positions(self, timestamp: pd.Timestamp) -> Dict[str, float]:
        """Get wallet positions from data provider."""
        try:
            wallet_positions = {}
            
            # Get wallet balances from data provider
            wallet_balances = self.data_provider.get_wallet_balances(timestamp)
            
            for venue, balances in wallet_balances.items():
                for token, amount in balances.items():
                    key = f"{venue}_{token}"
                    wallet_positions[key] = amount
            
            return wallet_positions
        except Exception as e:
            logger.error(f"Error getting wallet positions: {e}")
            return {}
    
    def _get_smart_contract_positions(self, timestamp: pd.Timestamp) -> Dict[str, float]:
        """Get smart contract positions from data provider."""
        try:
            smart_contract_positions = {}
            
            # Get smart contract balances from data provider
            smart_contract_balances = self.data_provider.get_smart_contract_balances(timestamp)
            
            for protocol, balances in smart_contract_balances.items():
                for token, amount in balances.items():
                    key = f"{protocol}_{token}"
                    smart_contract_positions[key] = amount
            
            return smart_contract_positions
        except Exception as e:
            logger.error(f"Error getting smart contract positions: {e}")
            return {}
    
    def _get_cex_spot_positions(self, timestamp: pd.Timestamp) -> Dict[str, float]:
        """Get CEX spot positions from data provider."""
        try:
            cex_spot_positions = {}
            
            # Get CEX spot balances from data provider
            cex_spot_balances = self.data_provider.get_cex_spot_balances(timestamp)
            
            for exchange, balances in cex_spot_balances.items():
                for token, amount in balances.items():
                    key = f"{exchange}_spot_{token}"
                    cex_spot_positions[key] = amount
            
            return cex_spot_positions
        except Exception as e:
            logger.error(f"Error getting CEX spot positions: {e}")
            return {}
    
    def _get_cex_derivatives_positions(self, timestamp: pd.Timestamp) -> Dict[str, float]:
        """Get CEX derivatives positions from data provider."""
        try:
            cex_derivatives_positions = {}
            
            # Get CEX derivatives balances from data provider
            cex_derivatives_balances = self.data_provider.get_cex_derivatives_balances(timestamp)
            
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
    
    def get_snapshot(self, timestamp: pd.Timestamp = None) -> Dict[str, Any]:
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
    
    def log_position_snapshot(self, timestamp: pd.Timestamp, event_type: str) -> None:
        """Log position snapshot for debugging."""
        try:
            snapshot = self.get_snapshot(timestamp)
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
    
    def get_all_positions(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """
        Get all positions across all venues (alias for calculate_positions).
        
        Args:
            timestamp: Current timestamp
            
        Returns:
            Dictionary with all position data
        """
        return self.calculate_positions(timestamp)
    
    def get_position_summary(self) -> Dict[str, Any]:
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