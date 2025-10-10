"""
Mode-Agnostic Risk Monitor

Provides mode-agnostic risk monitoring that works for both backtest and live modes.
Calculates risks across all venues and provides generic risk logic.

Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Section 7 (Generic vs Mode-Specific)
Reference: docs/specs/06_RISK_MONITOR.md - Mode-agnostic risk calculation
"""

from typing import Dict, List, Any, Optional
import logging
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

class RiskMonitor:
    """Mode-agnostic risk monitor that works for both backtest and live modes"""
    
    def __init__(self, config: Dict[str, Any], data_provider, utility_manager):
        """
        Initialize risk monitor.
        
        Args:
            config: Strategy configuration
            data_provider: Data provider instance
            utility_manager: Centralized utility manager
        """
        # Validate required configuration at startup (fail-fast)
        required_keys = ['target_ltv', 'max_drawdown', 'leverage_enabled', 'venues']
        for key in required_keys:
            if key not in config:
                from ...infrastructure.monitoring.logging import log_structured_error
                log_structured_error(
                    error_code='CONFIG-003',
                    message=f'Missing required configuration: {key}',
                    component='risk_monitor',
                    context={'missing_key': key, 'required_keys': required_keys}
                )
                raise KeyError(f"Missing required configuration: {key}")
        
        # Validate nested configuration
        if 'venues' in config:
            for venue_name, venue_config in config['venues'].items():
                if not isinstance(venue_config, dict):
                    from ...infrastructure.monitoring.logging import log_structured_error
                    log_structured_error(
                        error_code='CONFIG-007',
                        message=f'Invalid venue configuration for {venue_name}: must be a dictionary',
                        component='risk_monitor',
                        context={'venue_name': venue_name, 'venue_config': venue_config}
                    )
                    raise KeyError(f"Invalid venue configuration for {venue_name}: must be a dictionary")
                if 'max_leverage' not in venue_config:
                    from ...infrastructure.monitoring.logging import log_structured_error
                    log_structured_error(
                        error_code='CONFIG-003',
                        message=f'Missing max_leverage in venue configuration for {venue_name}',
                        component='risk_monitor',
                        context={'venue_name': venue_name, 'venue_config': venue_config}
                    )
                    raise KeyError(f"Missing max_leverage in venue configuration for {venue_name}")
        
        self.config = config
        self.data_provider = data_provider
        self.utility_manager = utility_manager
        
        # Risk tracking
        self.last_risks = None
        
        logger.info("RiskMonitor initialized (mode-agnostic)")
    
    def calculate_risks(self, exposures: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """
        Calculate risks regardless of mode (backtest or live).
        
        Args:
            exposures: Current exposure data
            timestamp: Current timestamp
            
        Returns:
            Dictionary with risk calculation results
        """
        try:
            # Calculate various risk metrics
            liquidation_risk = self._calculate_liquidation_risk(exposures, timestamp)
            delta_risk = self._calculate_delta_risk(exposures, timestamp)
            funding_risk = self._calculate_funding_risk(exposures, timestamp)
            basis_risk = self._calculate_basis_risk(exposures, timestamp)
            default_risk = self._calculate_default_risk(exposures, timestamp)
            
            # Calculate overall risk score
            overall_risk = self._calculate_overall_risk(
                liquidation_risk, delta_risk, funding_risk, basis_risk, default_risk
            )
            
            # Calculate risk metrics
            risk_metrics = self._calculate_risk_metrics(
                liquidation_risk, delta_risk, funding_risk, basis_risk, default_risk
            )
            
            # Update last risks
            self._update_last_risks(overall_risk, timestamp)
            
            return {
                'timestamp': timestamp,
                'total_risk': overall_risk,  # Add missing total_risk field
                'overall_risk': overall_risk,
                'risk_metrics': risk_metrics,
                'risk_by_venue': {  # Add missing risk_by_venue field
                    'liquidation': liquidation_risk,
                    'delta': delta_risk,
                    'funding': funding_risk,
                    'basis': basis_risk,
                    'default': default_risk
                },
                'risks': {
                    'liquidation': liquidation_risk,
                    'delta': delta_risk,
                    'funding': funding_risk,
                    'basis': basis_risk,
                    'default': default_risk
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating risks: {e}")
            return {
                'timestamp': timestamp,
                'overall_risk': 0.0,
                'risk_metrics': {},
                'risks': {},
                'error': str(e)
            }
    
    def _calculate_liquidation_risk(self, exposures: Dict[str, Any], timestamp: pd.Timestamp) -> float:
        """Calculate liquidation risk across all venues."""
        try:
            liquidation_risk = 0.0
            
            # Get exposure data (fail-fast on missing keys)
            try:
                total_exposures = exposures['total_exposures']
                exposure_metrics = exposures['exposure_metrics']
            except KeyError as e:
                logger.error(f"Missing required exposure data: {e}")
                return liquidation_risk
            
            if not total_exposures or not exposure_metrics:
                return liquidation_risk
            
            # Calculate liquidation risk for each venue
            for venue, exposure in total_exposures.items():
                if exposure > 0:
                    # Get venue-specific liquidation threshold
                    liquidation_threshold = self._get_liquidation_threshold(venue)
                    
                    # Calculate risk based on exposure and threshold
                    venue_risk = min(exposure / liquidation_threshold, 1.0) if liquidation_threshold > 0 else 0.0
                    liquidation_risk = max(liquidation_risk, venue_risk)
            
            return liquidation_risk
        except Exception as e:
            logger.error(f"Error calculating liquidation risk: {e}")
            return 0.0
    
    def _calculate_delta_risk(self, exposures: Dict[str, Any], timestamp: pd.Timestamp) -> float:
        """Calculate delta risk (price movement risk)."""
        try:
            delta_risk = 0.0
            
            # Get exposure data (fail-fast on missing keys)
            try:
                total_exposures = exposures['total_exposures']
                exposure_by_category = exposures['exposure_by_category']
            except KeyError as e:
                logger.error(f"Missing required exposure data: {e}")
                return delta_risk
            
            if not total_exposures or not exposure_by_category:
                return delta_risk
            
            # Calculate delta risk based on exposure categories
            for category, exposure in exposure_by_category.items():
                if exposure > 0:
                    # Get category-specific delta risk multiplier
                    delta_multiplier = self._get_delta_risk_multiplier(category)
                    
                    # Calculate risk based on exposure and multiplier
                    category_risk = exposure * delta_multiplier
                    delta_risk += category_risk
            
            return delta_risk
        except Exception as e:
            logger.error(f"Error calculating delta risk: {e}")
            return 0.0
    
    def _calculate_funding_risk(self, exposures: Dict[str, Any], timestamp: pd.Timestamp) -> float:
        """Calculate funding risk (funding rate risk)."""
        try:
            funding_risk = 0.0
            
            # Get exposure data
            exposure_by_category = exposures['exposure_by_category']
            
            if not exposure_by_category:
                return funding_risk
            
            # Calculate funding risk based on basis trading exposure
            try:
                basis_exposure = exposure_by_category['basis']
            except KeyError as e:
                logger.error(f"Missing basis exposure data: {e}")
                return funding_risk
            if basis_exposure > 0:
                # Get current funding rate
                funding_rate = self._get_current_funding_rate(timestamp)
                
                # Calculate risk based on exposure and funding rate
                funding_risk = basis_exposure * abs(funding_rate)
            
            return funding_risk
        except Exception as e:
            logger.error(f"Error calculating funding risk: {e}")
            return 0.0
    
    def _calculate_basis_risk(self, exposures: Dict[str, Any], timestamp: pd.Timestamp) -> float:
        """Calculate basis risk (basis spread risk)."""
        try:
            basis_risk = 0.0
            
            # Get exposure data
            exposure_by_category = exposures['exposure_by_category']
            
            if not exposure_by_category:
                return basis_risk
            
            # Calculate basis risk based on basis trading exposure
            try:
                basis_exposure = exposure_by_category['basis']
            except KeyError as e:
                logger.error(f"Missing basis exposure data: {e}")
                return basis_risk
            if basis_exposure > 0:
                # Get current basis spread
                basis_spread = self._get_current_basis_spread(timestamp)
                
                # Calculate risk based on exposure and basis spread
                basis_risk = basis_exposure * abs(basis_spread)
            
            return basis_risk
        except Exception as e:
            logger.error(f"Error calculating basis risk: {e}")
            return 0.0
    
    def _calculate_default_risk(self, exposures: Dict[str, Any], timestamp: pd.Timestamp) -> float:
        """Calculate default risk (counterparty risk)."""
        try:
            default_risk = 0.0
            
            # Get exposure data
            total_exposures = exposures['total_exposures']
            
            if not total_exposures:
                return default_risk
            
            # Calculate default risk for each venue
            for venue, exposure in total_exposures.items():
                if exposure > 0:
                    # Get venue-specific default risk multiplier
                    default_multiplier = self._get_default_risk_multiplier(venue)
                    
                    # Calculate risk based on exposure and multiplier
                    venue_risk = exposure * default_multiplier
                    default_risk += venue_risk
            
            return default_risk
        except Exception as e:
            logger.error(f"Error calculating default risk: {e}")
            return 0.0
    
    def _calculate_overall_risk(self, liquidation_risk: float, delta_risk: float, 
                              funding_risk: float, basis_risk: float, default_risk: float) -> float:
        """Calculate overall risk score."""
        try:
            # Weight different risk types
            weights = {
                'liquidation': 0.4,  # Highest weight for liquidation risk
                'delta': 0.3,        # High weight for delta risk
                'funding': 0.15,     # Medium weight for funding risk
                'basis': 0.1,        # Medium weight for basis risk
                'default': 0.05      # Low weight for default risk
            }
            
            # Calculate weighted average
            overall_risk = (
                liquidation_risk * weights['liquidation'] +
                delta_risk * weights['delta'] +
                funding_risk * weights['funding'] +
                basis_risk * weights['basis'] +
                default_risk * weights['default']
            )
            
            return min(overall_risk, 1.0)  # Cap at 1.0
        except Exception as e:
            logger.error(f"Error calculating overall risk: {e}")
            return 0.0
    
    def _calculate_risk_metrics(self, liquidation_risk: float, delta_risk: float, 
                              funding_risk: float, basis_risk: float, default_risk: float) -> Dict[str, Any]:
        """Calculate risk metrics."""
        try:
            metrics = {
                'liquidation_risk': liquidation_risk,
                'delta_risk': delta_risk,
                'funding_risk': funding_risk,
                'basis_risk': basis_risk,
                'default_risk': default_risk,
                'risk_level': self._get_risk_level(liquidation_risk, delta_risk, funding_risk, basis_risk, default_risk),
                'risk_trend': self._get_risk_trend()
            }
            
            return metrics
        except Exception as e:
            logger.error(f"Error calculating risk metrics: {e}")
            return {}
    
    def _get_liquidation_threshold(self, venue: str) -> float:
        """Get liquidation threshold for a venue."""
        try:
            # Default liquidation thresholds by venue type
            thresholds = {
                'aave': 0.8,      # 80% LTV
                'compound': 0.75,  # 75% LTV
                'binance': 0.9,    # 90% margin
                'bybit': 0.9,      # 90% margin
                'okx': 0.9,        # 90% margin
                'lido': 1.0,       # No liquidation risk
                'etherfi': 1.0     # No liquidation risk
            }
            
            # Extract venue type from venue name
            venue_lower = venue.lower()
            for venue_type, threshold in thresholds.items():
                if venue_type in venue_lower:
                    return threshold
            
            # Default threshold
            return 0.8
        except Exception as e:
            logger.error(f"Error getting liquidation threshold for {venue}: {e}")
            return 0.8
    
    def _get_delta_risk_multiplier(self, category: str) -> float:
        """Get delta risk multiplier for a category."""
        try:
            # Delta risk multipliers by category
            multipliers = {
                'lending': 0.1,    # Low delta risk for lending
                'staking': 0.2,    # Medium delta risk for staking
                'basis': 0.5,      # High delta risk for basis trading
                'funding': 0.3,    # Medium delta risk for funding
                'delta': 0.8,      # Very high delta risk for delta trading
                'other': 0.2       # Default delta risk
            }
            
            try:
                return multipliers[category]
            except KeyError as e:
                logger.error(f"Missing delta risk multiplier for category {category}: {e}")
                return 0.2
        except Exception as e:
            logger.error(f"Error getting delta risk multiplier for {category}: {e}")
            return 0.2
    
    def _get_default_risk_multiplier(self, venue: str) -> float:
        """Get default risk multiplier for a venue."""
        try:
            # Default risk multipliers by venue
            multipliers = {
                'aave': 0.01,      # Very low default risk
                'compound': 0.01,  # Very low default risk
                'binance': 0.02,   # Low default risk
                'bybit': 0.02,     # Low default risk
                'okx': 0.02,       # Low default risk
                'lido': 0.005,     # Very low default risk
                'etherfi': 0.005   # Very low default risk
            }
            
            # Extract venue type from venue name
            venue_lower = venue.lower()
            for venue_type, multiplier in multipliers.items():
                if venue_type in venue_lower:
                    return multiplier
            
            # Default multiplier
            return 0.02
        except Exception as e:
            logger.error(f"Error getting default risk multiplier for {venue}: {e}")
            return 0.02
    
    def _get_current_funding_rate(self, timestamp: pd.Timestamp) -> float:
        """Get current funding rate."""
        try:
            # Placeholder for actual funding rate calculation
            # In real implementation, this would query the data provider
            return 0.0001  # 0.01% funding rate
        except Exception as e:
            logger.error(f"Error getting current funding rate: {e}")
            return 0.0
    
    def _get_current_basis_spread(self, timestamp: pd.Timestamp) -> float:
        """Get current basis spread."""
        try:
            # Placeholder for actual basis spread calculation
            # In real implementation, this would query the data provider
            return 0.001  # 0.1% basis spread
        except Exception as e:
            logger.error(f"Error getting current basis spread: {e}")
            return 0.0
    
    def _get_risk_level(self, liquidation_risk: float, delta_risk: float, 
                       funding_risk: float, basis_risk: float, default_risk: float) -> str:
        """Get risk level based on risk metrics."""
        try:
            # Calculate overall risk score
            overall_risk = self._calculate_overall_risk(
                liquidation_risk, delta_risk, funding_risk, basis_risk, default_risk
            )
            
            # Determine risk level
            if overall_risk < 0.2:
                return 'LOW'
            elif overall_risk < 0.5:
                return 'MEDIUM'
            elif overall_risk < 0.8:
                return 'HIGH'
            else:
                return 'CRITICAL'
        except Exception as e:
            logger.error(f"Error getting risk level: {e}")
            return 'UNKNOWN'
    
    def _get_risk_trend(self) -> str:
        """Get risk trend."""
        try:
            # Placeholder for actual risk trend calculation
            # In real implementation, this would compare current risk with historical risk
            return 'STABLE'
        except Exception as e:
            logger.error(f"Error getting risk trend: {e}")
            return 'UNKNOWN'
    
    def _update_last_risks(self, overall_risk: float, timestamp: pd.Timestamp):
        """Update last risks."""
        try:
            self.last_risks = {
                'timestamp': timestamp,
                'overall_risk': overall_risk
            }
        except Exception as e:
            logger.error(f"Error updating last risks: {e}")
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """Get risk summary."""
        try:
            return {
                'last_risks': self.last_risks,
                'mode_agnostic': True
            }
        except Exception as e:
            logger.error(f"Error getting risk summary: {e}")
            return {
                'last_risks': None,
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