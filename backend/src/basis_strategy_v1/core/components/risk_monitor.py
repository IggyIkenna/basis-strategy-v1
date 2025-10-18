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
import os
import uuid
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal

from ...infrastructure.logging.structured_logger import StructuredLogger
from ...infrastructure.logging.domain_event_logger import DomainEventLogger
from ...core.models.domain_events import RiskAssessment
from ...core.errors.error_codes import ERROR_REGISTRY
from ...core.utilities.risk_data_loader import RiskDataLoader

logger = logging.getLogger(__name__)

class RiskMonitor:
    """Mode-agnostic risk monitor that works for both backtest and live modes"""
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config: Dict[str, Any], data_provider, utility_manager, correlation_id: str = None, pid: int = None, log_dir: Path = None):
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
        
        # Get position subscriptions from config
        position_config = config.get('component_config', {}).get('position_monitor', {})
        self.position_subscriptions = position_config.get('position_subscriptions', [])
        
        logger.info(f"RiskMonitor subscribed to {len(self.position_subscriptions)} positions")
        
        # Initialize logging infrastructure
        self.correlation_id = correlation_id or str(uuid.uuid4().hex)
        self.pid = pid or os.getpid()
        self.log_dir = log_dir
        
        # Initialize structured logger
        self.logger = StructuredLogger(
            component_name="RiskMonitor",
            correlation_id=self.correlation_id,
            pid=self.pid,
            log_dir=self.log_dir,
            engine=None
        )
        
        # Initialize domain event logger
        self.domain_event_logger = DomainEventLogger(self.log_dir) if self.log_dir else None
        
        # Use direct config access for fail-fast behavior
        self.leverage_enabled = config['leverage_enabled']
        
        # Initialize risk data loader
        self.risk_data_loader = RiskDataLoader()
        
        # Load risk parameters
        self._load_risk_parameters()
        self._initialize_risk_parameters()
    
    def check_component_health(self) -> Dict[str, Any]:
        """Check component health status."""
        return {
            'status': self.health_status,
            'error_count': self.error_count,
            'max_drawdown': self.max_drawdown,
            'leverage_enabled': self.leverage_enabled,
            'component': self.__class__.__name__
        }
    
    def _log_risk_assessment(self, risk_data: Dict[str, Any]) -> None:
        """Log risk assessment as domain event."""
        if not self.log_dir or not self.domain_event_logger:
            return
        
        timestamp = datetime.now().isoformat()
        real_utc = datetime.now(timezone.utc).isoformat()
        
        assessment = RiskAssessment(
            timestamp=timestamp,
            real_utc_time=real_utc,
            correlation_id=self.correlation_id,
            pid=self.pid,
            health_factor=risk_data.get('health_factor'),
            ltv_ratio=risk_data.get('ltv_ratio'),
            liquidation_threshold=risk_data.get('liquidation_threshold'),
            margin_usage=risk_data.get('margin_usage'),
            risk_level=risk_data.get('risk_level', 'unknown'),
            warnings=risk_data.get('warnings', []),
            breaches=risk_data.get('breaches', []),
            metadata={}
        )
        
        self.domain_event_logger.log_risk_assessment(assessment)
    
    def _initialize_risk_parameters(self):
        """Initialize risk parameters."""
        try:
            # Calculate target_ltv from AAVE risk parameters (as per spec)
            max_stake_spread_move_value = self.config.get('max_stake_spread_move', 0.1)
            if max_stake_spread_move_value is None:
                max_stake_spread_move_value = 0.1
            logger.debug(f"max_stake_spread_move_value: {max_stake_spread_move_value} (type: {type(max_stake_spread_move_value)})")
            max_stake_spread_move = Decimal(str(max_stake_spread_move_value))
            self.target_ltv = self.utility_manager.calculate_dynamic_ltv_target(
                self.aave_max_ltv_emode, 
                max_stake_spread_move
            )
            
            # Calculate CEX target margins for all venues
            self.cex_target_margins = {}
            max_underlying_move_value = self.config.get('max_underlying_move', 0.2)
            if max_underlying_move_value is None:
                max_underlying_move_value = 0.2
            max_underlying_move = Decimal(str(max_underlying_move_value))
            for venue, requirements in self.cex_margin_requirements.items():
                self.cex_target_margins[venue] = self.utility_manager.calculate_cex_target_margin(
                    requirements['initial_margin'],
                    max_underlying_move
                )
            
            # Load component-specific configuration with fail-fast behavior
            self.enabled_risk_types = self.config['component_config']['risk_monitor']['enabled_risk_types']
            self.risk_limits = self.config['component_config']['risk_monitor']['risk_limits']
            
            self.logger.info(
                "RiskMonitor initialized successfully",
                component="risk_monitor",
                target_ltv=float(self.target_ltv),
                leverage_enabled=self.leverage_enabled,
                cex_target_margins={k: float(v) for k, v in self.cex_target_margins.items()}
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize risk parameters: {e}")
            logger.error(f"Config values - max_stake_spread_move: {self.config.get('max_stake_spread_move')}, max_underlying_move: {self.config.get('max_underlying_move')}")
            # Use conservative fallback values
            self.target_ltv = Decimal('0')
            self.cex_target_margins = {}
            self.enabled_risk_types = ['cex_margin_ratio', 'delta_risk']
            self.risk_limits = {
                'target_margin_ratio': 0.5,
                'cex_margin_ratio_min': 0.15,
                'maintenance_margin_requirement': 0.10,
                'delta_tolerance': 0.005,
                'liquidation_threshold': 0.95
            }
            
            # Log the fallback initialization
            self.logger.info(
                "RiskMonitor initialized with fallback values",
                component="risk_monitor",
                target_ltv=0.0,
                leverage_enabled=self.leverage_enabled,
                error=str(e)
            )
    
    def _load_risk_parameters(self):
        """Load all risk parameters using the risk data loader."""
        try:
            # Load AAVE risk parameters
            self.aave_max_ltv_emode, self.aave_liquidation_threshold_emode = self.risk_data_loader.get_aave_ltv_limits('emode', 'weETH_WETH')
            self.aave_liquidation_bonus_emode = self.risk_data_loader.get_aave_liquidation_bonus('emode', 'weETH_WETH')
            
            # Load CEX margin requirements for all available venues
            self.cex_margin_requirements = {}
            for venue in self.risk_data_loader.get_available_cex_venues():
                initial_margin, maintenance_margin, liquidation_threshold = self.risk_data_loader.get_cex_margin_requirements(venue)
                self.cex_margin_requirements[venue] = {
                    'initial_margin': initial_margin,
                    'maintenance_margin': maintenance_margin,
                    'liquidation_threshold': liquidation_threshold
                }
            
            logger.info(f"Risk parameters loaded: AAVE (max_ltv: {self.aave_max_ltv_emode}), CEX venues: {list(self.cex_margin_requirements.keys())}")
            
        except Exception as e:
            logger.error(f"Failed to load risk parameters: {e}")
            # Use conservative fallback values
            self.aave_max_ltv_emode = Decimal('0.5')
            self.aave_liquidation_threshold_emode = Decimal('0.6')
            self.aave_liquidation_bonus_emode = Decimal('0.05')
            self.cex_margin_requirements = {
                'binance': {'initial_margin': Decimal('0.1'), 'maintenance_margin': Decimal('0.15'), 'liquidation_threshold': Decimal('0.1')},
                'bybit': {'initial_margin': Decimal('0.1'), 'maintenance_margin': Decimal('0.15'), 'liquidation_threshold': Decimal('0.1')},
                'okx': {'initial_margin': Decimal('0.1'), 'maintenance_margin': Decimal('0.15'), 'liquidation_threshold': Decimal('0.1')}
            }
    
    

    
    def assess_risk(self, exposure_data: Dict, market_data: Dict, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """
        Main entry point for risk calculations.
        
        Args:
            exposure_data: Current exposure snapshot from ExposureMonitor
            market_data: Market data from DataProvider (queried by caller)
            timestamp: Current timestamp
            
        Returns:
            Dictionary with risk calculation results including:
            - current_ltv: Current LTV accounting for all debt and collateral instruments on AAVE
            - current_margin_ratio: Current margin ratio on CEX (accounting for all tokens and derivative positions)
            - health_ratio: Liquidation LTV / current LTV
            - maintenance_margin_ratio: Strategy risk config maintenance margin ratio
        """
        try:
            # Calculate current LTV for AAVE positions
            current_ltv = self._calculate_current_ltv(exposure_data)
            
            # Calculate current margin ratios for CEX positions
            cex_margin_ratios = self._calculate_cex_margin_ratios(exposure_data)
            
            # Calculate health ratios
            health_ratios = self._calculate_health_ratios(current_ltv, cex_margin_ratios)
            
            # Calculate maintenance margin ratios
            maintenance_margin_ratios = self._calculate_maintenance_margin_ratios(cex_margin_ratios)
            
            risk_result = {
                'timestamp': timestamp,
                'current_ltv': float(current_ltv),
                'target_ltv': float(self.target_ltv),
                'cex_margin_ratios': {k: float(v) for k, v in cex_margin_ratios.items()},
                'cex_target_margins': {k: float(v) for k, v in self.cex_target_margins.items()},
                'health_ratios': health_ratios,
                'maintenance_margin_ratios': maintenance_margin_ratios,
                'aave_liquidation_threshold': float(self.aave_liquidation_threshold_emode),
                'aave_max_ltv': float(self.aave_max_ltv_emode)
            }
            
            self._update_last_risks(risk_result, timestamp)
            
            # Log risk assessment
            self._log_risk_assessment(risk_result)
            
            return risk_result
            
        except Exception as e:
            self.logger.error(
                f"Error calculating risks: {e}",
                error_code="RISK-001",
                exc_info=e,
                operation="assess_risk"
            )
            return {
                'timestamp': timestamp,
                'error': str(e),
                'current_ltv': 0.0,
                'target_ltv': 0.0,
                'cex_margin_ratios': {},
                'health_ratios': {},
                'maintenance_margin_ratios': {}
            }
    
    def _calculate_current_ltv(self, exposure_data: Dict) -> Decimal:
        """Calculate current LTV for AAVE positions."""
        try:
            # Extract AAVE positions from exposure data
            exposures = exposure_data.get('exposures', {})
            
            total_collateral = Decimal('0')
            total_debt = Decimal('0')
            
            for position_key, position_data in exposures.items():
                if 'aave' in position_key.lower():
                    amount = Decimal(str(position_data.get('amount', 0)))
                    value_usd = Decimal(str(position_data.get('value_usd', 0)))
                    
                    # Determine if it's collateral or debt based on position type
                    if 'aToken' in position_key:  # Collateral
                        total_collateral += value_usd
                    elif 'debt' in position_key.lower() or 'borrow' in position_key.lower():  # Debt
                        total_debt += value_usd
            
            if total_collateral <= 0:
                return Decimal('0')
            
            current_ltv = total_debt / total_collateral
            logger.debug(f"Current LTV calculation: debt={total_debt}, collateral={total_collateral}, ltv={current_ltv}")
            
            return current_ltv
            
        except Exception as e:
            logger.error(f"Error calculating current LTV: {e}")
            return Decimal('0')
    
    def _calculate_cex_margin_ratios(self, exposure_data: Dict) -> Dict[str, Decimal]:
        """Calculate current margin ratios for CEX positions."""
        try:
            cex_margin_ratios = {}
            exposures = exposure_data.get('exposures', {})
            
            # Group positions by venue
            venue_positions = {}
            for position_key, position_data in exposures.items():
                venue = position_key.split(':')[0] if ':' in position_key else 'unknown'
                if venue in ['binance', 'bybit', 'okx']:
                    if venue not in venue_positions:
                        venue_positions[venue] = {'long': Decimal('0'), 'short': Decimal('0')}
                    
                    amount = Decimal(str(position_data.get('amount', 0)))
                    value_usd = Decimal(str(position_data.get('value_usd', 0)))
                    
                    # Determine if long or short position (simplified logic)
                    if 'spot' in position_key.lower() or amount > 0:
                        venue_positions[venue]['long'] += value_usd
                    else:
                        venue_positions[venue]['short'] += value_usd
            
            # Calculate margin ratios for each venue
            for venue, positions in venue_positions.items():
                if venue in self.cex_margin_requirements:
                    total_value = positions['long'] + positions['short']
                    if total_value > 0:
                        # Simplified margin ratio calculation
                        # In practice, this would be more complex based on CEX margin requirements
                        margin_ratio = positions['long'] / total_value
                        cex_margin_ratios[venue] = margin_ratio
                    else:
                        cex_margin_ratios[venue] = Decimal('1')  # No positions = 100% margin
            
            logger.debug(f"CEX margin ratios calculated: {cex_margin_ratios}")
            return cex_margin_ratios
            
        except Exception as e:
            logger.error(f"Error calculating CEX margin ratios: {e}")
            return {}
    
    def _calculate_health_ratios(self, current_ltv: Decimal, cex_margin_ratios: Dict[str, Decimal]) -> Dict[str, Decimal]:
        """Calculate health ratios (liquidation LTV / current LTV)."""
        try:
            health_ratios = {}
            
            # AAVE health ratio
            if current_ltv > 0:
                aave_health_ratio = self.aave_liquidation_threshold_emode / current_ltv
                health_ratios['aave'] = aave_health_ratio
            else:
                health_ratios['aave'] = Decimal('999')  # No debt = infinite health
            
            # CEX health ratios
            for venue, margin_ratio in cex_margin_ratios.items():
                if venue in self.cex_margin_requirements:
                    liquidation_threshold = self.cex_margin_requirements[venue]['liquidation_threshold']
                    if margin_ratio > 0:
                        cex_health_ratio = liquidation_threshold / margin_ratio
                        health_ratios[f'cex_{venue}'] = cex_health_ratio
                    else:
                        health_ratios[f'cex_{venue}'] = Decimal('999')  # No positions = infinite health
            
            logger.debug(f"Health ratios calculated: {health_ratios}")
            return health_ratios
            
        except Exception as e:
            logger.error(f"Error calculating health ratios: {e}")
            return {}
    
    def _calculate_maintenance_margin_ratios(self, cex_margin_ratios: Dict[str, Decimal]) -> Dict[str, Decimal]:
        """Calculate maintenance margin ratios from strategy risk config."""
        try:
            maintenance_margin_ratios = {}
            
            for venue, margin_ratio in cex_margin_ratios.items():
                if venue in self.cex_target_margins:
                    target_margin = self.cex_target_margins[venue]
                    maintenance_margin_ratios[venue] = target_margin
            
            logger.debug(f"Maintenance margin ratios calculated: {maintenance_margin_ratios}")
            return maintenance_margin_ratios
            
        except Exception as e:
            logger.error(f"Error calculating maintenance margin ratios: {e}")
            return {}

    

    

    

    

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
            self.logger.info(
                "Risk assessment completed",
                component="risk_monitor",
                trigger_source=trigger_source,
                overall_risk=risk_result.get('overall_risk', 0.0),
                risk_level=risk_result.get('risk_level', 'unknown'),
                timestamp=timestamp.isoformat()
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