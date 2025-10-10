"""
Mode-Agnostic P&L Monitor

Provides mode-agnostic P&L monitoring and attribution that works for both
backtest and live modes. Calculates balances across all venues and provides
generic attribution logic.

Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Section 7 (Generic vs Mode-Specific)
Reference: docs/specs/04_PNL_CALCULATOR.md - Mode-agnostic P&L calculation
"""

from typing import Dict, List, Any, Optional
import logging
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

class PnLMonitor:
    """Mode-agnostic P&L monitor that works for both backtest and live modes"""
    
    def __init__(self, config: Dict[str, Any], data_provider, utility_manager):
        """
        Initialize P&L monitor.
        
        Args:
            config: Strategy configuration
            data_provider: Data provider instance
            utility_manager: Centralized utility manager
        """
        # Validate required configuration at startup (fail-fast)
        required_keys = ['share_class', 'target_apy', 'max_drawdown']
        for key in required_keys:
            if key not in config:
                raise KeyError(f"Missing required configuration: {key}")
        
        self.config = config
        self.data_provider = data_provider
        self.utility_manager = utility_manager
        
        # P&L tracking
        self.last_snapshot = None
        self.cumulative_pnl = 0.0
        
        logger.info("PnLMonitor initialized (mode-agnostic)")
    
    def calculate_pnl(self, exposures: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """
        Calculate P&L regardless of mode (backtest or live).
        
        Args:
            exposures: Current exposure data
            timestamp: Current timestamp
            
        Returns:
            Dictionary with P&L calculation results
        """
        try:
            # Get all balances across all venues
            wallet_balances = self._get_wallet_balances(exposures, timestamp)
            smart_contract_balances = self._get_smart_contract_balances(exposures, timestamp)
            cex_spot_balances = self._get_cex_spot_balances(exposures, timestamp)
            cex_derivatives_balances = self._get_cex_derivatives_balances(exposures, timestamp)
            
            # Calculate total USDT equivalent
            total_usdt_balance = self._calculate_total_usdt_balance(
                wallet_balances, smart_contract_balances, 
                cex_spot_balances, cex_derivatives_balances, timestamp
            )
            
            # Calculate total share class balance
            share_class = self._get_share_class_from_exposures(exposures)
            total_share_class_balance = self._calculate_total_share_class_balance(
                wallet_balances, smart_contract_balances, 
                cex_spot_balances, cex_derivatives_balances, 
                share_class, timestamp
            )
            
            # Calculate P&L change since last snapshot
            pnl_change = self._calculate_pnl_change(
                total_usdt_balance, total_share_class_balance, timestamp
            )
            
            # Calculate attribution
            attribution = self._calculate_attribution(
                wallet_balances, smart_contract_balances, 
                cex_spot_balances, cex_derivatives_balances, 
                share_class, timestamp
            )
            
            # Update snapshot
            self._update_snapshot(total_usdt_balance, total_share_class_balance, timestamp)
            
            return {
                'timestamp': timestamp,
                'total_usdt_balance': total_usdt_balance,
                'total_share_class_balance': total_share_class_balance,
                'share_class': share_class,
                'pnl_change': pnl_change,
                'cumulative_pnl': self.cumulative_pnl,
                'attribution': attribution,
                'balances': {
                    'wallet': wallet_balances,
                    'smart_contract': smart_contract_balances,
                    'cex_spot': cex_spot_balances,
                    'cex_derivatives': cex_derivatives_balances
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating P&L: {e}")
            return {
                'timestamp': timestamp,
                'total_usdt_balance': 0.0,
                'total_share_class_balance': 0.0,
                'share_class': 'USDT',
                'pnl_change': 0.0,
                'cumulative_pnl': self.cumulative_pnl,
                'attribution': {},
                'balances': {},
                'error': str(e)
            }
    
    def _get_wallet_balances(self, exposures: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, float]:
        """Get wallet balances from exposures."""
        try:
            wallet_balances = {}
            
            # Extract wallet balances from exposures
            try:
                wallet_data = exposures['wallet_balances']
            except KeyError as e:
                logger.error(f"Missing wallet balances data: {e}")
                wallet_data = {}
            
            for venue, balances in wallet_data.items():
                for token, amount in balances.items():
                    key = f"{venue}_{token}"
                    wallet_balances[key] = amount
            
            return wallet_balances
        except Exception as e:
            logger.error(f"Error getting wallet balances: {e}")
            return {}
    
    def _get_smart_contract_balances(self, exposures: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, float]:
        """Get smart contract balances from exposures."""
        try:
            smart_contract_balances = {}
            
            # Extract smart contract balances from exposures
            try:
                smart_contract_data = exposures['smart_contract_balances']
            except KeyError as e:
                logger.error(f"Missing smart contract balances data: {e}")
                smart_contract_data = {}
            
            for protocol, balances in smart_contract_data.items():
                for token, amount in balances.items():
                    key = f"{protocol}_{token}"
                    smart_contract_balances[key] = amount
            
            return smart_contract_balances
        except Exception as e:
            logger.error(f"Error getting smart contract balances: {e}")
            return {}
    
    def _get_cex_spot_balances(self, exposures: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, float]:
        """Get CEX spot balances from exposures."""
        try:
            cex_spot_balances = {}
            
            # Extract CEX spot balances from exposures
            try:
                cex_spot_data = exposures['cex_spot_balances']
            except KeyError as e:
                logger.error(f"Missing CEX spot balances data: {e}")
                cex_spot_data = {}
            
            for exchange, balances in cex_spot_data.items():
                for token, amount in balances.items():
                    key = f"{exchange}_spot_{token}"
                    cex_spot_balances[key] = amount
            
            return cex_spot_balances
        except Exception as e:
            logger.error(f"Error getting CEX spot balances: {e}")
            return {}
    
    def _get_cex_derivatives_balances(self, exposures: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, float]:
        """Get CEX derivatives balances from exposures."""
        try:
            cex_derivatives_balances = {}
            
            # Extract CEX derivatives balances from exposures
            try:
                cex_derivatives_data = exposures['cex_derivatives_balances']
            except KeyError as e:
                logger.error(f"Missing CEX derivatives balances data: {e}")
                cex_derivatives_data = {}
            
            for exchange, balances in cex_derivatives_data.items():
                for token, amount in balances.items():
                    key = f"{exchange}_derivatives_{token}"
                    cex_derivatives_balances[key] = amount
            
            return cex_derivatives_balances
        except Exception as e:
            logger.error(f"Error getting CEX derivatives balances: {e}")
            return {}
    
    def _calculate_total_usdt_balance(self, wallet_balances: Dict[str, float], 
                                    smart_contract_balances: Dict[str, float],
                                    cex_spot_balances: Dict[str, float],
                                    cex_derivatives_balances: Dict[str, float],
                                    timestamp: pd.Timestamp) -> float:
        """Calculate total USDT equivalent balance."""
        try:
            all_balances = {}
            all_balances.update(wallet_balances)
            all_balances.update(smart_contract_balances)
            all_balances.update(cex_spot_balances)
            all_balances.update(cex_derivatives_balances)
            
            return self.utility_manager.calculate_total_usdt_balance(all_balances, timestamp)
        except Exception as e:
            logger.error(f"Error calculating total USDT balance: {e}")
            return 0.0
    
    def _calculate_total_share_class_balance(self, wallet_balances: Dict[str, float], 
                                           smart_contract_balances: Dict[str, float],
                                           cex_spot_balances: Dict[str, float],
                                           cex_derivatives_balances: Dict[str, float],
                                           share_class: str, timestamp: pd.Timestamp) -> float:
        """Calculate total share class equivalent balance."""
        try:
            all_balances = {}
            all_balances.update(wallet_balances)
            all_balances.update(smart_contract_balances)
            all_balances.update(cex_spot_balances)
            all_balances.update(cex_derivatives_balances)
            
            return self.utility_manager.calculate_total_share_class_balance(all_balances, share_class, timestamp)
        except Exception as e:
            logger.error(f"Error calculating total {share_class} balance: {e}")
            return 0.0
    
    def _calculate_pnl_change(self, total_usdt_balance: float, total_share_class_balance: float, 
                            timestamp: pd.Timestamp) -> float:
        """Calculate P&L change since last snapshot."""
        try:
            if self.last_snapshot is None:
                # First snapshot, no change
                return 0.0
            
            # Calculate change in share class balance
            try:
                previous_share_class_balance = self.last_snapshot['total_share_class_balance']
            except (KeyError, TypeError):
                previous_share_class_balance = 0.0
            pnl_change = total_share_class_balance - previous_share_class_balance
            
            # Update cumulative P&L
            self.cumulative_pnl += pnl_change
            
            return pnl_change
        except Exception as e:
            logger.error(f"Error calculating P&L change: {e}")
            return 0.0
    
    def _calculate_attribution(self, wallet_balances: Dict[str, float], 
                             smart_contract_balances: Dict[str, float],
                             cex_spot_balances: Dict[str, float],
                             cex_derivatives_balances: Dict[str, float],
                             share_class: str, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Calculate P&L attribution by category."""
        try:
            attribution = {
                'lending': 0.0,
                'staking': 0.0,
                'basis': 0.0,
                'funding': 0.0,
                'delta': 0.0,
                'other': 0.0
            }
            
            # Calculate attribution for each balance category
            all_balances = {}
            all_balances.update(wallet_balances)
            all_balances.update(smart_contract_balances)
            all_balances.update(cex_spot_balances)
            all_balances.update(cex_derivatives_balances)
            
            for balance_key, amount in all_balances.items():
                if amount > 0:
                    # Convert to share class currency
                    share_class_value = self.utility_manager.convert_to_share_class(
                        amount, self._extract_token_from_balance_key(balance_key), 
                        share_class, timestamp
                    )
                    
                    # Categorize based on balance key
                    category = self._categorize_balance(balance_key)
                    attribution[category] += share_class_value
            
            return attribution
        except Exception as e:
            logger.error(f"Error calculating attribution: {e}")
            return {}
    
    def _extract_token_from_balance_key(self, balance_key: str) -> str:
        """Extract token symbol from balance key."""
        try:
            # Balance key format: "venue_token" or "venue_type_token"
            parts = balance_key.split('_')
            if len(parts) >= 2:
                return parts[-1]  # Last part is usually the token
            return balance_key
        except Exception as e:
            logger.error(f"Error extracting token from {balance_key}: {e}")
            return balance_key
    
    def _categorize_balance(self, balance_key: str) -> str:
        """Categorize balance based on key."""
        try:
            balance_key_lower = balance_key.lower()
            
            # Lending category
            if any(keyword in balance_key_lower for keyword in ['aave', 'compound', 'venus', 'ausdt', 'aeth']):
                return 'lending'
            
            # Staking category
            if any(keyword in balance_key_lower for keyword in ['lido', 'etherfi', 'steth', 'weth', 'eeth']):
                return 'staking'
            
            # Basis category
            if any(keyword in balance_key_lower for keyword in ['basis', 'perp', 'futures']):
                return 'basis'
            
            # Funding category
            if any(keyword in balance_key_lower for keyword in ['funding', 'rate']):
                return 'funding'
            
            # Delta category
            if any(keyword in balance_key_lower for keyword in ['delta', 'spot']):
                return 'delta'
            
            # Default to other
            return 'other'
        except Exception as e:
            logger.error(f"Error categorizing balance {balance_key}: {e}")
            return 'other'
    
    def _get_share_class_from_exposures(self, exposures: Dict[str, Any]) -> str:
        """Get share class from exposures or config."""
        try:
            # Try to get from exposures first
            share_class = exposures.get('share_class')
            if share_class:
                return share_class
            
            # Fall back to config
            return self.config['share_class']
        except Exception as e:
            logger.error(f"Error getting share class: {e}")
            return 'USDT'
    
    def _update_snapshot(self, total_usdt_balance: float, total_share_class_balance: float, 
                        timestamp: pd.Timestamp):
        """Update last snapshot."""
        try:
            self.last_snapshot = {
                'timestamp': timestamp,
                'total_usdt_balance': total_usdt_balance,
                'total_share_class_balance': total_share_class_balance
            }
        except Exception as e:
            logger.error(f"Error updating snapshot: {e}")
    
    def get_pnl_summary(self) -> Dict[str, Any]:
        """Get P&L summary."""
        try:
            return {
                'cumulative_pnl': self.cumulative_pnl,
                'last_snapshot': self.last_snapshot,
                'mode_agnostic': True
            }
        except Exception as e:
            logger.error(f"Error getting P&L summary: {e}")
            return {
                'cumulative_pnl': 0.0,
                'last_snapshot': None,
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
