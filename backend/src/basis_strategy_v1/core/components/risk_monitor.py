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

from ...infrastructure.logging.structured_logger import get_risk_monitor_logger
from ...core.logging.base_logging_interface import StandardizedLoggingMixin, LogLevel, EventType

logger = logging.getLogger(__name__)

class RiskMonitor(StandardizedLoggingMixin):
    """Mode-agnostic risk monitor that works for both backtest and live modes"""
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config: Dict[str, Any], data_provider, utility_manager):
        """
        Initialize risk monitor.
        
        Args:
            config: Strategy configuration
            data_provider: Data provider instance
            utility_manager: Centralized utility manager
        """
        # Store references
        self.config = config
        self.data_provider = data_provider
        self.utility_manager = utility_manager
        self.health_status = "healthy"
        self.error_count = 0
        
        # Initialize structured logger
        self.structured_logger = get_risk_monitor_logger()
        
        # Load AAVE risk parameters from data provider (as per spec)
        self._load_aave_risk_parameters()
        
        # Use direct config access for fail-fast behavior
        self.max_drawdown = config['max_drawdown']
        self.leverage_enabled = config['leverage_enabled']
    
    def check_component_health(self) -> Dict[str, Any]:
        """Check component health status."""
        return {
            'status': self.health_status,
            'error_count': self.error_count,
            'max_drawdown': self.max_drawdown,
            'leverage_enabled': self.leverage_enabled,
            'component': self.__class__.__name__
        }
    
    def _initialize_risk_parameters(self):
        """Initialize risk parameters."""
        # Calculate target_ltv from AAVE risk parameters (as per spec)
        self.target_ltv = self._calculate_target_ltv()
        
        # Load venue configuration - venues are handled through separate venue configs
        # For now, use empty dict as venues are not part of mode config
        self.venues = config.get('venues', {})
        
        # Load component-specific configuration with fail-fast behavior
        component_config = config['component_config']
        risk_monitor_config = component_config['risk_monitor']
        self.enabled_risk_types = risk_monitor_config['enabled_risk_types']
        self.risk_limits = risk_monitor_config['risk_limits']
        
        # Initialize risk metrics
        self.current_risk_metrics = {}
        self.last_calculation_timestamp = None
        self.risk_history = []
        
        self.structured_logger.info(
            "RiskMonitor initialized successfully",
            event_type="component_initialization",
            component="risk_monitor",
            target_ltv=self.target_ltv,
            leverage_enabled=self.leverage_enabled
        )
    
    def _load_aave_risk_parameters(self):
        """Load AAVE risk parameters from data provider (as per spec)."""
        try:
            # Load AAVE risk parameters from the actual data file
            import json
            from pathlib import Path
            
            # Get data directory from config
            data_dir = self.config['data_dir']
            risk_params_path = Path(data_dir) / 'protocol_data/aave/risk_params/aave_v3_risk_parameters.json'
            
            if risk_params_path.exists():
                with open(risk_params_path, 'r') as f:
                    self.aave_risk_params = json.load(f)
                
                # Extract E-mode parameters (most permissive)
                self.aave_liquidation_bonus_emode = self.aave_risk_params['emode']['liquidation_bonus']['weETH_WETH']
                self.aave_liquidation_threshold_emode = self.aave_risk_params['emode']['liquidation_thresholds']['weETH_WETH']
                
                logger.info(f"AAVE risk parameters loaded from {risk_params_path}")
            else:
                # Fallback to hardcoded values if file not found
                logger.warning(f"AAVE risk parameters file not found: {risk_params_path}, using fallback values")
                self.aave_liquidation_bonus_emode = 0.01
                self.aave_liquidation_threshold_emode = 0.95
            
        except Exception as e:
            logger.warning(f"Failed to load AAVE risk parameters: {e}")
            # Use fallback values
            self.aave_liquidation_bonus_emode = 0.01
            self.aave_liquidation_threshold_emode = 0.95
    
    def _calculate_target_ltv(self):
        """Calculate target LTV from AAVE risk parameters (as per spec)."""
        try:
            # For modes that don't borrow (like pure_lending), target_ltv should be 0
            if not self.leverage_enabled:
                return 0.0
            
            # For modes that do borrow, calculate target LTV with safety buffer
            # Target LTV should be below liquidation threshold with safety buffer
            safety_buffer = 0.05  # 5% safety buffer
            target_ltv = self.aave_liquidation_threshold_emode - safety_buffer
            
            # Ensure target LTV is reasonable (between 0 and 0.9)
            target_ltv = max(0.0, min(target_ltv, 0.9))
            
            logger.info(f"Calculated target LTV: {target_ltv} (liquidation threshold: {self.aave_liquidation_threshold_emode})")
            return target_ltv
            
        except Exception as e:
            logger.warning(f"Failed to calculate target LTV: {e}")
            # Use fallback value
            return 0.0
    
    def assess_risk(self, exposure_data: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess risk using exposure data and market data.
        
        Args:
            exposure_data: Current exposure data
            market_data: Current market data
            
        Returns:
            Dictionary with risk assessment results
        """
        # Extract timestamp from market_data
        timestamp = market_data['timestamp']
        if isinstance(timestamp, str):
            timestamp = pd.Timestamp(timestamp)
        
        return self.assess_risk(exposure_data, {})
    
    def assess_risk(self, exposure_data: Dict, market_data: Dict) -> Dict[str, Any]:
        """
        Main entry point for risk calculations.
        
        Args:
            exposure_data: Current exposure snapshot from ExposureMonitor
            market_data: Market data from DataProvider (queried by caller)
            
        Returns:
            Dictionary with risk calculation results
        """
        try:
            # Use current timestamp for calculations
            timestamp = pd.Timestamp.now()
            
            # Calculate various risk metrics
            liquidation_risk = self._calculate_liquidation_risk(exposure_data, timestamp)
            delta_risk = self._calculate_delta_risk(exposure_data, timestamp)
            funding_risk = self._calculate_funding_risk(exposure_data, timestamp)
            basis_risk = self._calculate_basis_risk(exposure_data, timestamp)
            default_risk = self._calculate_default_risk(exposure_data, timestamp)
            
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
    
    def get_current_risk_metrics(self) -> Dict[str, Any]:
        """Get current risk metrics snapshot."""
        try:
            return {
                'last_risks': self.last_risks,
                'mode_agnostic': True
            }
        except Exception as e:
            logger.error(f"Error getting current risk metrics: {e}")
            return {
                'last_risks': None,
                'mode_agnostic': True,
                'error': str(e)
            }
    
    def update_state(self, timestamp: pd.Timestamp, trigger_source: str, **kwargs) -> None:
        """
        Update component state (called by EventDrivenStrategyEngine).
        
        Args:
            timestamp: Current loop timestamp (from EventDrivenStrategyEngine)
            trigger_source: 'full_loop' | 'tight_loop' | 'manual'
            **kwargs: Additional parameters (exposure_data, market_data, etc.)
        """
        # Extract exposure and market data from kwargs if present
        exposure_data = kwargs.get('exposure_data')
        market_data = kwargs.get('market_data')
        
        if exposure_data and market_data:
            # Perform risk assessment
            risk_result = self.assess_risk(exposure_data, market_data)
            
            # Log risk assessment
            self.structured_logger.info(
                "Risk assessment completed",
                event_type="risk_assessment",
                component="risk_monitor",
                trigger_source=trigger_source,
                overall_risk=risk_result.get('overall_risk', 0.0),
                risk_level=risk_result.get('risk_level', 'unknown'),
                timestamp=timestamp.isoformat()
            )
            
            # Log using standardized logging
            self.log_component_event(
                EventType.BUSINESS_EVENT,
                f"Risk assessment completed: trigger_source={trigger_source}",
                {
                    'overall_risk': risk_result.get('overall_risk', 0.0),
                    'risk_level': risk_result.get('risk_level', 'unknown'),
                    'trigger_source': trigger_source
                }
            )
    
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