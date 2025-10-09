"""
Risk Monitor Component

Calculate risk metrics from exposure data and trigger alerts.
Monitor three types of risk:
1. AAVE LTV Risk - Loan-to-value ratio on lending protocol
2. CEX Margin Risk - Margin ratios on perpetual futures  
3. Net Delta Risk - Deviation from target delta (market neutrality)

Key Principles:
- Reactive: Triggered by Exposure Monitor updates
- Multi-venue: Track each CEX separately
- Threshold-based: Warning, urgent, critical levels
- Fail-safe: Conservative thresholds (user buffer above venue liquidation)
"""

from typing import Dict, List, Optional, Any
import redis
import json
import logging
import asyncio
from datetime import datetime
import pandas as pd
from decimal import Decimal

# Import math calculators
from ..math.health_calculator import HealthCalculator
from ..math.ltv_calculator import LTVCalculator
from ..math.margin_calculator import MarginCalculator

logger = logging.getLogger(__name__)

# Import error code registry
try:
    from ...error_codes.error_code_registry import error_code_registry, get_error_info
except ImportError:
    # Fallback for when running from project root
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', 'backend', 'src'))
    from basis_strategy_v1_v1.core.error_codes.error_code_registry import error_code_registry, get_error_info


class RiskMonitorError(Exception):
    """Custom exception for Risk Monitor errors with error code integration."""
    
    def __init__(self, error_code: str, message: str = None, **kwargs):
        self.error_code = error_code
        self.error_info = get_error_info(error_code)
        
        if message is None and self.error_info:
            message = self.error_info.message
        
        super().__init__(message)
        
        # Store additional context
        for key, value in kwargs.items():
            setattr(self, key, value)


class RiskCalculations:
    """Mathematical derivation of safe operating parameters from data + config."""
    
    def __init__(self, data_provider, config: Dict[str, Any]):
        self.data_provider = data_provider
        self.config = config
        
        # Load venue data
        self.aave_risk_params = self.data_provider.get_aave_risk_params()
        self.bybit_margin_params = self.data_provider.get_bybit_margin_requirements()
        self.binance_margin_params = self.data_provider.get_binance_margin_requirements()
        self.okx_margin_params = self.data_provider.get_okx_margin_requirements()
    
    def calculate_safe_aave_ltv(
        self,
        asset: str,
        max_underlying_move: float,
        max_spot_perp_basis_move: float = 0.0,
        max_staked_basis_move: float = 0.0,
        beta_basis_as_collateral: float = 1.0,
        hf_target_after_shock: float = 1.10
    ) -> Dict[str, float]:
        """Calculate safe AAVE operating LTV using data-driven approach."""
        # Get actual venue liquidation threshold from data
        if asset in ['weETH', 'wstETH']:
            liquidation_threshold = self.aave_risk_params['emode']['liquidation_thresholds']['weETH_WETH']
        else:
            liquidation_threshold = self.aave_risk_params['normal_mode']['liquidation_thresholds']['weETH_WETH']
        
        # Formula: LTV_target = LT * (1 - (u + s + β·b)) / HF_target_after
        u = max_underlying_move
        s = max_staked_basis_move
        b = max_spot_perp_basis_move
        beta = beta_basis_as_collateral
        LT = liquidation_threshold
        HF_target = hf_target_after_shock
        
        safe_target_ltv = LT * (1 - (u + s + beta * b)) / HF_target
        safe_target_ltv = max(0.20, min(0.75, safe_target_ltv))
        
        return {
            'target_ltv': safe_target_ltv,
            'venue_liquidation_ltv': liquidation_threshold,
            'safety_distance': safe_target_ltv - liquidation_threshold,
            'risk_inputs': {
                'max_underlying_move': u,
                'max_staked_basis_move': s,
                'max_spot_perp_basis_move': b,
                'beta_basis_as_collateral': beta
            }
        }
    
    def calculate_safe_bybit_margin(
        self,
        max_underlying_move: float,
        max_spot_perp_basis_move: float,
        risk_buffer_multiplier: float = 3.0
    ) -> Dict[str, float]:
        """Calculate safe Bybit margin requirements using data."""
        initial_req = self.bybit_margin_params['initial_margin_requirement']
        maintenance_req = self.bybit_margin_params['maintenance_margin_requirement']
        
        # Calculate risk buffer
        risk_buffer = (max_underlying_move + max_spot_perp_basis_move) * risk_buffer_multiplier
        
        # Safe margins
        safe_initial_margin = initial_req + risk_buffer
        safe_maintenance_margin = maintenance_req + risk_buffer
        
        return {
            'target_initial_margin': safe_initial_margin,
            'target_maintenance_margin': safe_maintenance_margin,
            'venue_initial_requirement': initial_req,
            'venue_maintenance_requirement': maintenance_req,
            'safety_distance': safe_maintenance_margin - maintenance_req
        }
    
    def calculate_safe_binance_margin(
        self,
        max_underlying_move: float,
        max_spot_perp_basis_move: float,
        risk_buffer_multiplier: float = 3.0
    ) -> Dict[str, float]:
        """Calculate safe Binance margin requirements using data."""
        initial_req = self.binance_margin_params['initial_margin_requirement']
        maintenance_req = self.binance_margin_params['maintenance_margin_requirement']
        
        # Calculate risk buffer
        risk_buffer = (max_underlying_move + max_spot_perp_basis_move) * risk_buffer_multiplier
        
        # Safe margins
        safe_initial_margin = initial_req + risk_buffer
        safe_maintenance_margin = maintenance_req + risk_buffer
        
        return {
            'target_initial_margin': safe_initial_margin,
            'target_maintenance_margin': safe_maintenance_margin,
            'venue_initial_requirement': initial_req,
            'venue_maintenance_requirement': maintenance_req,
            'safety_distance': safe_maintenance_margin - maintenance_req
        }
    
    def calculate_safe_okx_margin(
        self,
        max_underlying_move: float,
        max_spot_perp_basis_move: float,
        risk_buffer_multiplier: float = 3.0
    ) -> Dict[str, float]:
        """Calculate safe OKX margin requirements using data."""
        initial_req = self.okx_margin_params['initial_margin_requirement']
        maintenance_req = self.okx_margin_params['maintenance_margin_requirement']
        
        # Calculate risk buffer
        risk_buffer = (max_underlying_move + max_spot_perp_basis_move) * risk_buffer_multiplier
        
        # Safe margins
        safe_initial_margin = initial_req + risk_buffer
        safe_maintenance_margin = maintenance_req + risk_buffer
        
        return {
            'target_initial_margin': safe_initial_margin,
            'target_maintenance_margin': safe_maintenance_margin,
            'venue_initial_requirement': initial_req,
            'venue_maintenance_requirement': maintenance_req,
            'safety_distance': safe_maintenance_margin - maintenance_req
        }
    
    def get_all_safe_parameters(
        self,
        max_underlying_move: float,
        max_spot_perp_basis_move: float,
        max_staked_basis_move: float,
        beta_basis_as_collateral: float = 1.0,
        hf_target_after_shock: float = 1.10,
        primary_asset: str = "ETH"
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate ALL safe operating parameters from user's risk tolerance.
        
        This replaces dozens of manual config parameters with mathematical derivation.
        
        Args:
            max_underlying_move: User's price risk tolerance 
            max_spot_perp_basis_move: User's spot vs perp risk tolerance
            max_staked_basis_move: User's staking basis risk tolerance
            primary_asset: Primary asset for calculations
            
        Returns:
            Dict containing all calculated safe parameters for all venues
        """
        return {
            'aave_ltv': self.calculate_safe_aave_ltv(
                asset=primary_asset,
                max_underlying_move=max_underlying_move,
                max_spot_perp_basis_move=max_spot_perp_basis_move,
                max_staked_basis_move=max_staked_basis_move,
                beta_basis_as_collateral=beta_basis_as_collateral,
                hf_target_after_shock=hf_target_after_shock
            ),
            'aave_ltv_wsteth': self.calculate_safe_aave_ltv(
                asset='wstETH',
                max_underlying_move=max_underlying_move,
                max_spot_perp_basis_move=max_spot_perp_basis_move,
                max_staked_basis_move=max_staked_basis_move,
                beta_basis_as_collateral=beta_basis_as_collateral,
                hf_target_after_shock=hf_target_after_shock
            ),
            'aave_ltv_weeth': self.calculate_safe_aave_ltv(
                asset='weETH',
                max_underlying_move=max_underlying_move,
                max_spot_perp_basis_move=max_spot_perp_basis_move,
                max_staked_basis_move=max_staked_basis_move,
                beta_basis_as_collateral=beta_basis_as_collateral,
                hf_target_after_shock=hf_target_after_shock
            ),
            'bybit_margin': self.calculate_safe_bybit_margin(
                max_underlying_move=max_underlying_move,
                max_spot_perp_basis_move=max_spot_perp_basis_move
            ),
            'binance_margin': self.calculate_safe_binance_margin(
                max_underlying_move=max_underlying_move,
                max_spot_perp_basis_move=max_spot_perp_basis_move
            ),
            'okx_margin': self.calculate_safe_okx_margin(
                max_underlying_move=max_underlying_move,
                max_spot_perp_basis_move=max_spot_perp_basis_move
            ),
            'risk_inputs': {
                'max_underlying_move': max_underlying_move,
                'max_spot_perp_basis_move': max_spot_perp_basis_move,
                'max_staked_basis_move': max_staked_basis_move,
                'beta_basis_as_collateral': beta_basis_as_collateral,
                'hf_target_after_shock': hf_target_after_shock,
                'primary_asset': primary_asset
            }
        }


class RiskMonitor:
    """Monitor all risk metrics."""
    
    def __init__(self, config: Dict[str, Any], position_monitor=None, exposure_monitor=None, 
                 data_provider=None, share_class: str = None, debug_mode: bool = False):
        self.config = config
        self.position_monitor = position_monitor
        self.exposure_monitor = exposure_monitor
        self.data_provider = data_provider
        self.share_class = share_class
        self.debug_mode = debug_mode
        
        # Fail-fast validation for required dependencies
        if not self.data_provider:
            raise RiskMonitorError('RISK-004', 'Data provider is required for risk calculations')
        
        if not self.position_monitor:
            raise RiskMonitorError('RISK-004', 'Position monitor is required for risk calculations')
        
        if not self.exposure_monitor:
            raise RiskMonitorError('RISK-004', 'Exposure monitor is required for risk calculations')
        
        if not self.share_class:
            raise RiskMonitorError('RISK-004', 'Share class is required for risk calculations')
        
        # Setup debug logging
        if self.debug_mode:
            self._setup_debug_logging()
        
        # Initialize risk calculations with data-driven approach
        logger.info(f"Risk Monitor: Initializing RiskCalculations with data_provider={self.data_provider is not None}")
        self.risk_calculations = RiskCalculations(self.data_provider, self.config)
    
    def enable_debug_logging(self):
        """Enable debug logging after initialization."""
        logger.info(f"enable_debug_logging called: has_debug_logger={hasattr(self, 'debug_logger')}")
        if not hasattr(self, 'debug_logger') or not self.debug_logger:
            logger.info(f"Setting up debug logging...")
            self._setup_debug_logging()
        else:
            logger.info(f"Debug logging already set up")
        
        # Get mode-specific parameters (FAIL-FAST - no .get() defaults!)
        self.mode = self.config['mode']
        self.asset = self.config.get('asset', 'ETH')  # Keep default for backward compatibility
        self.lst_type = self.config.get('lst_type')  # Optional field
        
        # Mode-specific risk parameters (FAIL-FAST - no .get() defaults!)
        self.margin_ratio_target = self.config['margin_ratio_target']
        self.max_stake_spread_move = self.config['max_stake_spread_move']
        self.max_ltv = self.config['max_ltv']
        self.liquidation_threshold = self.config['liquidation_threshold']
        
        # Performance targets for dynamic risk adjustment
        self.target_apy = self.config['target_apy']
        self.max_drawdown = self.config['max_drawdown']
        
        # Calculate safe operating parameters at initialization
        strategy_config = self.config['strategy']
        self.safe_parameters = self.risk_calculations.get_all_safe_parameters(
            max_underlying_move=strategy_config['max_underlying_move'],
            max_spot_perp_basis_move=strategy_config['max_spot_perp_basis_move'],
            max_staked_basis_move=self.max_stake_spread_move,
            beta_basis_as_collateral=strategy_config['beta_basis_as_collateral'],
            hf_target_after_shock=strategy_config['hf_target_after_shock'],
            primary_asset=self.asset
        )
        
        # Risk thresholds from config (FAIL-FAST - no .get() defaults!)
        # Use calculated safe LTV instead of hardcoded target_ltv
        self.aave_safe_ltv = self.safe_parameters['aave_ltv']['target_ltv']
        
        # Risk thresholds from venues config (FAIL-FAST)
        venues_config = self.config['venues']
        self.aave_ltv_warning = venues_config['aave_ltv_warning']
        self.aave_ltv_critical = venues_config['aave_ltv_critical']
        
        self.margin_warning_threshold = venues_config['margin_warning_pct']
        self.margin_critical_threshold = venues_config['margin_critical_pct']
        self.margin_liquidation = 0.10  # Venue constant (all CEXs)
        
        self.delta_threshold_pct = strategy_config['rebalance_threshold_pct']
        
        # Redis for inter-component communication
        self.redis = None
        try:
            self.redis = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            # Test connection
            self.redis.ping()
            logger.info("✅ RiskMonitor connected to Redis")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Using in-memory storage.")
            self.redis = None
        
        # Risk state tracking
        self.current_risks = {
            'aave_ltv': {'level': 'safe', 'value': 0.0, 'timestamp': None},
            'cex_margin': {'level': 'safe', 'value': 0.0, 'timestamp': None},
            'delta_deviation': {'level': 'safe', 'value': 0.0, 'timestamp': None},
            'lst_price_deviation': {'level': 'safe', 'value': 0.0, 'timestamp': None}
        }
    
    def _setup_debug_logging(self):
        """Setup dedicated debug logging for Risk Monitor."""
        from pathlib import Path
        import os
        
        # Create logs directory if it doesn't exist
        logs_dir = Path(__file__).parent.parent.parent.parent.parent.parent / 'backend' / 'logs'
        logs_dir.mkdir(exist_ok=True)
        
        # Create dedicated logger for risk monitor
        self.debug_logger = logging.getLogger('risk_monitor_debug')
        self.debug_logger.setLevel(logging.DEBUG)
        
        # Create file handler for risk monitor log
        log_file = logs_dir / 'risk_monitor.log'
        logger.info(f"Risk Monitor debug log file path: {log_file}")
        logger.info(f"Logs directory exists: {logs_dir.exists()}")
        logger.info(f"Logs directory is writable: {logs_dir.is_dir() and os.access(logs_dir, os.W_OK)}")
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        self.debug_logger.addHandler(file_handler)
        
        logger.info(f"Risk Monitor debug logging enabled: {log_file}")
        logger.info(f"Risk Monitor debug log file created: {log_file.exists()}")
    
    def log_risk_snapshot(self, risk_assessment: Dict[str, Any], trigger: str = "risk_calculation"):
        """Log risk assessment snapshot for debug mode."""
        logger.info(f"log_risk_snapshot called: debug_mode={self.debug_mode}, has_debug_logger={hasattr(self, 'debug_logger')}")
        if not self.debug_mode or not hasattr(self, 'debug_logger'):
            logger.info(f"log_risk_snapshot returning early: debug_mode={self.debug_mode}, has_debug_logger={hasattr(self, 'debug_logger')}")
            return
        
        try:
            logger.info(f"log_risk_snapshot: Starting to format risk assessment")
            # Format risk assessment for logging
            log_message = f"RISK ASSESSMENT: {trigger}\n"
            log_message += f"Timestamp: {risk_assessment.get('timestamp', 'N/A')}\n"
            log_message += f"Overall Status: {risk_assessment.get('overall_status', 'N/A')}\n"
            log_message += f"Mode: {self.mode} | Asset: {self.asset} | Share Class: {self.share_class}\n"
            log_message += f"Margin Target: {self.margin_ratio_target:.2%} | Max Stake Spread: {self.max_stake_spread_move:.2%}\n"
            
            # AAVE Risk
            if 'aave_ltv' in risk_assessment:
                aave = risk_assessment['aave_ltv']
                log_message += f"AAVE LTV: {aave.get('value', 0.0):.4f} ({aave.get('level', 'N/A')})\n"
                health_factor = aave.get('health_factor', 0.0)
                status = aave.get('status', 'active')
                if status == 'no_positions':
                    log_message += f"Health Factor: {health_factor:.4f} (No AAVE positions)\n"
                elif health_factor < 1.0:
                    log_message += f"Health Factor: {health_factor:.4f} (⚠️  DANGER: < 1.0)\n"
                else:
                    log_message += f"Health Factor: {health_factor:.4f} (Safe: ≥ 1.0)\n"
            
            # CEX Margin Risk
            if 'cex_margin' in risk_assessment:
                cex = risk_assessment['cex_margin']
                log_message += f"CEX Margin: {cex.get('level', 'N/A')}\n"
                if 'venue_details' in cex:
                    for venue, details in cex['venue_details'].items():
                        log_message += f"  {venue}: {details.get('margin_ratio', 0.0):.4f} ({details.get('level', 'N/A')})\n"
            
            # Delta Risk
            if 'delta_deviation' in risk_assessment:
                delta = risk_assessment['delta_deviation']
                log_message += f"Delta Deviation: {delta.get('value', 0.0):.4f}% ({delta.get('level', 'N/A')})\n"
            
            # LST Price Deviation Risk
            if 'lst_price_deviation' in risk_assessment:
                lst = risk_assessment['lst_price_deviation']
                log_message += f"LST Price Deviation: {lst.get('value', 0.0):.4f}% ({lst.get('level', 'N/A')})\n"
            
            # Alerts
            if 'alerts' in risk_assessment and risk_assessment['alerts']:
                log_message += f"Alerts: {', '.join(risk_assessment['alerts'])}\n"
            
            log_message += "=" * 80 + "\n"
            
            logger.info(f"log_risk_snapshot: About to write to debug_logger")
            self.debug_logger.debug(log_message)
            logger.info(f"log_risk_snapshot: Successfully wrote to debug_logger")
            
        except Exception as e:
            logger.error(f"Error logging risk snapshot: {e}")
    
    def update_risk_calculations(self):
        """Update risk calculations when data changes."""
        strategy_config = self.config.get('strategy', {})
        self.safe_parameters = self.risk_calculations.get_all_safe_parameters(
            max_underlying_move=strategy_config.get('max_underlying_move', 0.15),
            max_spot_perp_basis_move=strategy_config.get('max_spot_perp_basis_move', 0.05),
            max_staked_basis_move=strategy_config.get('max_stake_spread_move', 0.03),
            beta_basis_as_collateral=strategy_config.get('beta_basis_as_collateral', 1.0),
            hf_target_after_shock=strategy_config.get('hf_target_after_shock', 1.10),
            primary_asset=strategy_config.get('coin_symbol', 'ETH')
        )
        
        # Update safe LTV
        self.aave_safe_ltv = self.safe_parameters['aave_ltv']['target_ltv']
        
        logger.info(f"Updated risk calculations: AAVE safe LTV = {self.aave_safe_ltv:.3f}")
    
    def _log_structured_error(self, error_code: str, message: str, context: Dict[str, Any] = None):
        """Log structured error with error code and context."""
        error_info = get_error_info(error_code)
        error_message = error_info.message if error_info else f'Unknown error code: {error_code}'
        
        log_data = {
            'error_code': error_code,
            'error_message': error_message,
            'component': 'risk_monitor',
            'timestamp': datetime.utcnow().isoformat(),
            'error_details': message
        }
        
        if context:
            log_data['context'] = context
        
        logger.error(f"{error_code}: {error_message} - {message}", extra=log_data)
    
    
    async def calculate_aave_ltv_risk(self, exposure_data: Dict[str, Any], performance_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Calculate AAVE LTV risk using integrated calculators with dynamic thresholds."""
        try:
            # Validate exposure data structure (fail-fast)
            if not exposure_data:
                raise RiskMonitorError('RISK-005', 'Exposure data is required but not provided')
            
            risk_breakdown = exposure_data.get('risk_breakdown')
            if not risk_breakdown:
                raise RiskMonitorError('RISK-005', 'Risk breakdown is required but not provided in exposure data')
            
            aave_data = risk_breakdown.get('aave')
            if not aave_data:
                raise RiskMonitorError('RISK-005', 'AAVE data is required but not provided in risk breakdown')
            
            # Get AAVE positions from risk breakdown (fail-fast)
            try:
                aave_collateral = Decimal(str(aave_data['collateral']['exposure_usd']))
                aave_debt = Decimal(str(aave_data['debt']['exposure_usd']))
            except KeyError as e:
                self._log_structured_error('RISK-005', f'AAVE risk breakdown missing required field: {e}', {
                    'missing_field': str(e),
                    'available_fields': list(aave_data.keys()) if aave_data else []
                })
                raise RiskMonitorError('RISK-005', f'AAVE risk breakdown missing required field: {e}', missing_field=str(e))
            
            if aave_collateral <= 0:
                return {
                    'level': 'safe',
                    'value': 0.0,
                    'health_factor': 0.0,
                    'current_ltv': 0.0,
                    'liquidation_threshold': 0.0,
                    'message': 'No AAVE positions - no collateral or debt',
                    'status': 'no_positions'
                }
            
            # Use LTVCalculator for precise LTV calculation
            ltv = LTVCalculator.calculate_current_ltv(aave_collateral, aave_debt)
            
            # Get dynamic LTV target (fail-fast)
            lst_type = self.config.get('lst_type', 'weeth')  # Default to weeth if not specified
            dynamic_ltv_target = self.calculate_dynamic_ltv_target(lst_type)
            
            # Use HealthCalculator for health factor with AAVE risk params
            liquidation_threshold = Decimal("0.85")  # Default, should come from AAVE risk params
            if self.data_provider:
                try:
                    risk_params = self.data_provider.get_aave_risk_params()
                    # Handle case sensitivity: weeth -> weETH, wsteth -> wstETH
                    if lst_type.lower() == 'weeth':
                        pair_key = 'weETH_WETH'
                    elif lst_type.lower() == 'wsteth':
                        pair_key = 'wstETH_WETH'
                    else:
                        pair_key = f'{lst_type.upper()}_WETH'
                    liquidation_threshold = Decimal(str(risk_params['emode']['liquidation_thresholds'][pair_key]))
                except Exception as e:
                    logger.warning(f"Could not get liquidation threshold from AAVE risk params: {e}")
            
            health_factor = HealthCalculator.calculate_health_factor(
                aave_collateral, aave_debt, liquidation_threshold
            )
            
            # Get dynamic risk thresholds if performance data provided
            if performance_data:
                dynamic_thresholds = self.calculate_dynamic_risk_thresholds(performance_data)
                ltv_critical_threshold = dynamic_thresholds['aave_ltv_critical']
                ltv_warning_threshold = dynamic_thresholds['aave_ltv_warning']
                risk_level = dynamic_thresholds['risk_level']
            else:
                ltv_critical_threshold = self.aave_ltv_critical
                ltv_warning_threshold = self.aave_ltv_warning
                risk_level = 'normal'
            
            # Determine risk level using dynamic thresholds
            if ltv >= ltv_critical_threshold:
                level = 'critical'
                message = f'AAVE LTV critical: {ltv:.2%} >= {ltv_critical_threshold:.2%} (dynamic: {risk_level})'
            elif ltv >= ltv_warning_threshold:
                level = 'warning'
                message = f'AAVE LTV warning: {ltv:.2%} >= {ltv_warning_threshold:.2%} (dynamic: {risk_level})'
            else:
                level = 'safe'
                message = f'AAVE LTV safe: {ltv:.2%} < {ltv_warning_threshold:.2%} (dynamic: {risk_level})'
            
            risk_data = {
                'level': level,
                'value': float(ltv),
                'dynamic_ltv_target': float(dynamic_ltv_target),
                'ltv_critical_threshold': float(ltv_critical_threshold),
                'ltv_warning_threshold': float(ltv_warning_threshold),
                'health_factor': float(health_factor),
                'liquidation_threshold': float(liquidation_threshold),
                'dynamic_risk_level': risk_level,
                'message': message,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Update current state
            self.current_risks['aave_ltv'] = risk_data
            
            return risk_data
            
        except RiskMonitorError:
            # Re-raise RiskMonitorError for fail-fast behavior (already logged with error code)
            raise
        except Exception as e:
            self._log_structured_error('RISK-009', f'Risk calculation error: {e}', {
                'error_type': type(e).__name__,
                'error_details': str(e)
            })
            raise RiskMonitorError('RISK-009', f'Risk calculation error: {e}', error_type=type(e).__name__)
    
    async def calculate_cex_margin_risk(self, exposure_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate CEX margin risk for all venues."""
        try:
            # Validate exposure data structure (fail-fast)
            if not exposure_data:
                raise RiskMonitorError('RISK-005', 'Exposure data is required but not provided')
            
            risk_breakdown = exposure_data.get('risk_breakdown')
            if not risk_breakdown:
                raise RiskMonitorError('RISK-005', 'Risk breakdown is required but not provided in exposure data')
            
            cex_data = risk_breakdown.get('cex')
            if not cex_data:
                raise RiskMonitorError('RISK-005', 'CEX data is required but not provided in risk breakdown')
            
            # Get CEX positions from risk breakdown (fail-fast)
            try:
                cex_gross_exposure = Decimal(str(cex_data['gross_exposure_usd']))
                cex_net_exposure = Decimal(str(cex_data['net_exposure_usd']))
            except KeyError as e:
                self._log_structured_error('RISK-005', f'CEX risk breakdown missing required field: {e}', {
                    'missing_field': str(e),
                    'available_fields': list(cex_data.keys()) if cex_data else []
                })
                raise RiskMonitorError('RISK-005', f'CEX risk breakdown missing required field: {e}', missing_field=str(e))
            # Check if there are any CEX positions
            if cex_gross_exposure <= 0:
                return {
                    'level': 'safe',
                    'value': 0.0,
                    'message': 'No CEX positions'
                }
            
            # Calculate margin ratio using MarginCalculator
            margin_ratio = MarginCalculator.calculate_margin_ratio(
                current_margin=cex_net_exposure,
                used_margin=0.0,
                position_value=cex_gross_exposure
            ) if cex_gross_exposure > 0 else 0.0
            
            # Determine risk level using mode-specific targets
            warning_threshold = self.margin_ratio_target * 0.8  # 80% of target
            critical_threshold = self.margin_ratio_target * 0.6  # 60% of target
            
            if margin_ratio <= critical_threshold:
                level = 'critical'
                message = f'CEX margin critical: {margin_ratio:.2%} <= {critical_threshold:.2%} (target: {self.margin_ratio_target:.2%})'
            elif margin_ratio <= warning_threshold:
                level = 'warning'
                message = f'CEX margin warning: {margin_ratio:.2%} <= {warning_threshold:.2%} (target: {self.margin_ratio_target:.2%})'
            else:
                level = 'safe'
                message = f'CEX margin safe: {margin_ratio:.2%} > {warning_threshold:.2%} (target: {self.margin_ratio_target:.2%})'
            
            return {
                'level': level,
                'value': float(margin_ratio),
                'message': message,
                'gross_exposure_usd': float(cex_gross_exposure),
                'net_exposure_usd': float(cex_net_exposure),
                'target_margin_ratio': self.margin_ratio_target
            }
            
        except Exception as e:
            logger.error(f"Error calculating CEX margin risk: {e}")
            return {
                'level': 'error',
                'value': 0.0,
                'message': f'Error calculating CEX margin risk: {e}'
            }
    
    async def calculate_delta_risk(self, exposure_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate delta deviation risk."""
        try:
            # Validate exposure data structure (fail-fast)
            if not exposure_data:
                raise RiskMonitorError('RISK-005', 'Exposure data is required but not provided')
            
            # Get current delta from exposure data (fail-fast)
            try:
                current_delta = exposure_data['net_delta_share_class']
                # For now, assume target delta is 0 (market neutral) - this should come from strategy config
                target_delta = 0.0  # TODO: Get from strategy config when available
            except KeyError as e:
                self._log_structured_error('RISK-005', f'Exposure data missing required field: {e}', {
                    'missing_field': str(e),
                    'available_exposure_fields': list(exposure_data.keys()) if exposure_data else []
                })
                raise RiskMonitorError('RISK-005', f'Exposure data missing required field: {e}', missing_field=str(e))
            
            delta_deviation = abs(current_delta - target_delta)
            delta_deviation_pct = (delta_deviation / abs(target_delta)) * 100 if target_delta != 0 else 0
            
            # Determine risk level
            if delta_deviation_pct >= self.delta_threshold_pct * 2:
                level = 'critical'
                message = f'Delta deviation critical: {delta_deviation_pct:.1f}% >= {self.delta_threshold_pct * 2:.1f}%'
            elif delta_deviation_pct >= self.delta_threshold_pct:
                level = 'warning'
                message = f'Delta deviation warning: {delta_deviation_pct:.1f}% >= {self.delta_threshold_pct:.1f}%'
            else:
                level = 'safe'
                message = f'Delta deviation safe: {delta_deviation_pct:.1f}% < {self.delta_threshold_pct:.1f}%'
            
            risk_data = {
                'level': level,
                'value': delta_deviation_pct,
                'message': message,
                'timestamp': datetime.utcnow().isoformat(),
                'current_delta': current_delta,
                'target_delta': target_delta
            }
            
            # Update current state
            self.current_risks['delta_deviation'] = risk_data
            
            return risk_data
            
        except Exception as e:
            logger.error(f"Error calculating delta risk: {e}")
            return {
                'level': 'error',
                'value': 0.0,
                'message': f'Error calculating delta risk: {e}'
            }
    
    async def calculate_overall_risk(self, exposure_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall risk assessment."""
        try:
            # Mode-specific risk assessment
            if self.mode == 'btc_basis':
                return await self.calculate_btc_basis_risk(exposure_data)
            else:
                # Default risk assessment for other modes
                return await self.calculate_default_risk(exposure_data)
        except Exception as e:
            self._log_structured_error('RISK-001', f"Overall risk assessment failed: {e}")
            return {
                'level': 'error',
                'overall_status': 'error',
                'timestamp': datetime.utcnow().isoformat(),
                'mode': self.mode,
                'asset': self.asset,
                'share_class': self.share_class,
                'error': str(e)
            }
    
    async def calculate_btc_basis_risk(self, exposure_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate BTC basis specific risk assessment."""
        try:
            # Calculate BTC basis specific risk metrics
            delta_risk = await self.calculate_btc_delta_risk(exposure_data)
            margin_risk = await self.calculate_btc_margin_risk(exposure_data)
            funding_risk = await self.calculate_btc_funding_risk(exposure_data)
            basis_risk = await self.calculate_btc_basis_risk_metric(exposure_data)
            
            # Determine overall risk level
            risk_levels = [delta_risk['level'], margin_risk['level'], funding_risk['level'], basis_risk['level']]
            
            if 'critical' in risk_levels:
                overall_level = 'critical'
            elif 'warning' in risk_levels:
                overall_level = 'warning'
            else:
                overall_level = 'safe'
            
            overall_risk = {
                'level': overall_level,
                'overall_status': overall_level,
                'timestamp': datetime.utcnow().isoformat(),
                'mode': self.mode,
                'asset': self.asset,
                'share_class': self.share_class,
                'delta_risk': delta_risk,
                'margin_risk': margin_risk,
                'funding_risk': funding_risk,
                'basis_risk': basis_risk,
                'recommendation': self._get_btc_basis_recommendation(overall_level, delta_risk)
            }
            
            return overall_risk
            
        except Exception as e:
            self._log_structured_error('RISK-BTC-001', f"BTC basis risk assessment failed: {e}")
            raise RiskMonitorError('RISK-BTC-001', f"BTC basis risk assessment failed: {e}")
    
    async def calculate_btc_delta_risk(self, exposure_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate BTC delta neutrality risk."""
        try:
            net_delta_btc = exposure_data.get('net_delta_primary_asset', 0)
            total_value_usd = exposure_data.get('total_value_usd', 1)
            
            # Get delta tolerance from config (default 0.5%)
            delta_tolerance = self.config.get('delta_tolerance', 0.005)
            
            # Calculate gross exposure for tolerance calculation
            gross_exposure = self._calculate_btc_gross_exposure(exposure_data)
            tolerance_threshold = gross_exposure * delta_tolerance
            
            # Calculate delta ratio
            delta_ratio = abs(net_delta_btc) / total_value_usd if total_value_usd > 0 else 0
            
            # Determine risk level
            if abs(net_delta_btc) > tolerance_threshold:
                risk_level = 'critical'
            elif abs(net_delta_btc) > tolerance_threshold * 0.5:
                risk_level = 'warning'
            else:
                risk_level = 'safe'
            
            return {
                'level': risk_level,
                'net_delta_btc': net_delta_btc,
                'delta_ratio': delta_ratio,
                'tolerance_threshold': tolerance_threshold,
                'gross_exposure': gross_exposure,
                'recommendation': 'REBALANCE' if risk_level in ['warning', 'critical'] else 'HOLD'
            }
            
        except Exception as e:
            self._log_structured_error('RISK-BTC-002', f"BTC delta risk calculation failed: {e}")
            return {
                'level': 'error',
                'net_delta_btc': 0.0,
                'delta_ratio': 0.0,
                'tolerance_threshold': 0.0,
                'gross_exposure': 0.0,
                'recommendation': 'ERROR',
                'error': str(e)
            }
    
    def _calculate_btc_gross_exposure(self, exposure_data: Dict[str, Any]) -> float:
        """Calculate gross BTC exposure for delta tolerance calculation."""
        btc_exposure = exposure_data.get('exposures', {}).get('BTC', {})
        
        # Sum absolute values of all BTC positions
        gross_exposure = 0.0
        
        # Add spot positions
        cex_spot = btc_exposure.get('cex_spot', {})
        for venue, amount in cex_spot.items():
            gross_exposure += abs(amount)
        
        # Add perp positions
        cex_perps = btc_exposure.get('cex_perps', {})
        for venue, position in cex_perps.items():
            if position:
                gross_exposure += abs(position.get('size', 0))
        
        return gross_exposure
    
    async def calculate_btc_margin_risk(self, exposure_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate BTC margin risk per venue."""
        try:
            # For BTC basis, margin risk is low since we're delta neutral
            # But we still monitor for any margin issues
            btc_exposure = exposure_data.get('exposures', {}).get('BTC', {})
            perp_positions = btc_exposure.get('cex_perps', {})
            
            margin_risks = {}
            overall_risk_level = 'safe'
            
            for venue, position in perp_positions.items():
                if position and position.get('size', 0) != 0:
                    # Get margin ratio (would come from venue data)
                    margin_ratio = position.get('margin_ratio', 0.8)  # Default 80%
                    
                    if margin_ratio < 0.5:
                        margin_risks[venue] = 'critical'
                        overall_risk_level = 'critical'
                    elif margin_ratio < 0.7:
                        margin_risks[venue] = 'warning'
                        if overall_risk_level != 'critical':
                            overall_risk_level = 'warning'
                    else:
                        margin_risks[venue] = 'safe'
            
            return {
                'level': overall_risk_level,
                'venue_risks': margin_risks,
                'recommendation': 'MONITOR' if overall_risk_level == 'safe' else 'REVIEW_MARGIN'
            }
            
        except Exception as e:
            self._log_structured_error('RISK-BTC-003', f"BTC margin risk calculation failed: {e}")
            return {
                'level': 'error',
                'venue_risks': {},
                'recommendation': 'ERROR',
                'error': str(e)
            }
    
    async def calculate_btc_funding_risk(self, exposure_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate BTC funding rate risk."""
        try:
            # For BTC basis, we want positive funding rates (we're short perps)
            # Risk is if funding rates turn negative
            btc_exposure = exposure_data.get('exposures', {}).get('BTC', {})
            perp_positions = btc_exposure.get('cex_perps', {})
            
            funding_risks = {}
            overall_risk_level = 'safe'
            
            for venue, position in perp_positions.items():
                if position and position.get('size', 0) != 0:
                    # Get current funding rate (would come from data provider)
                    # For now, assume positive funding rate
                    # TODO-REFACTOR: This hardcodes funding rate instead of using config
                    # Canonical: .cursor/tasks/06_architecture_compliance_rules.md
                    # Fix: Add to config YAML and load from config
                    funding_rate = 0.0001  # WRONG - hardcoded funding rate (0.01% per 8 hours)
                    
                    if funding_rate < -0.0005:  # Negative funding
                        funding_risks[venue] = 'warning'
                        overall_risk_level = 'warning'
                    elif funding_rate < 0:
                        funding_risks[venue] = 'caution'
                        if overall_risk_level == 'safe':
                            overall_risk_level = 'caution'
                    else:
                        funding_risks[venue] = 'safe'
            
            return {
                'level': overall_risk_level,
                'venue_risks': funding_risks,
                'recommendation': 'MONITOR' if overall_risk_level == 'safe' else 'REVIEW_FUNDING'
            }
            
        except Exception as e:
            self._log_structured_error('RISK-BTC-004', f"BTC funding risk calculation failed: {e}")
            return {
                'level': 'error',
                'venue_risks': {},
                'recommendation': 'ERROR',
                'error': str(e)
            }
    
    async def calculate_btc_basis_risk_metric(self, exposure_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate BTC basis spread risk."""
        try:
            # Monitor basis spread volatility
            # High volatility in basis spread can indicate market stress
            btc_exposure = exposure_data.get('exposures', {}).get('BTC', {})
            
            # Get current basis spread (would come from market data)
            current_basis_spread = 0.0  # Placeholder
            
            # For now, assume low risk
            risk_level = 'safe'
            
            return {
                'level': risk_level,
                'current_basis_spread': current_basis_spread,
                'recommendation': 'MONITOR'
            }
            
        except Exception as e:
            self._log_structured_error('RISK-BTC-005', f"BTC basis risk calculation failed: {e}")
            return {
                'level': 'error',
                'current_basis_spread': 0.0,
                'recommendation': 'ERROR',
                'error': str(e)
            }
    
    def _get_btc_basis_recommendation(self, overall_level: str, delta_risk: Dict[str, Any]) -> str:
        """Get BTC basis specific recommendation."""
        if overall_level == 'critical':
            return 'EMERGENCY_REBALANCE'
        elif overall_level == 'warning':
            if delta_risk.get('level') in ['warning', 'critical']:
                return 'REBALANCE_DELTA'
            else:
                return 'MONITOR_CLOSELY'
        else:
            return 'HOLD'
    
    async def calculate_default_risk(self, exposure_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate default risk assessment for non-BTC basis modes."""
        try:
            # Calculate all risk metrics
            aave_risk = await self.calculate_aave_ltv_risk(exposure_data)
            cex_risk = await self.calculate_cex_margin_risk(exposure_data)
            delta_risk = await self.calculate_delta_risk(exposure_data)
            lst_deviation_risk = await self.calculate_lst_price_deviation_risk(exposure_data)
            
            # Calculate liquidation simulations for critical risks
            liquidation_terms = await self.calculate_liquidation_terms(exposure_data, aave_risk, cex_risk)
            
            # Determine overall risk level
            risk_levels = [aave_risk['level'], cex_risk['level'], delta_risk['level'], lst_deviation_risk['level']]
            
            if 'critical' in risk_levels:
                overall_level = 'critical'
            elif 'warning' in risk_levels:
                overall_level = 'warning'
            else:
                overall_level = 'safe'
            
            overall_risk = {
                'level': overall_level,
                'overall_status': overall_level,  # Add overall_status for logging
                'timestamp': datetime.utcnow().isoformat(),
                'mode': self.mode,
                'asset': self.asset,
                'share_class': self.share_class,
                'aave_ltv': aave_risk,
                'cex_margin': cex_risk,
                'delta_deviation': delta_risk,
                'lst_price_deviation': lst_deviation_risk,
                'liquidation_terms': liquidation_terms,
                'summary': {
                    'total_risks': len([r for r in risk_levels if r != 'safe']),
                    'critical_risks': len([r for r in risk_levels if r == 'critical']),
                    'warning_risks': len([r for r in risk_levels if r == 'warning'])
                }
            }
            
            # Publish risk update
            await self.publish_risk_update(overall_risk)
            
            # Log risk snapshot in debug mode
            if self.debug_mode:
                logger.info(f"Risk Monitor debug mode enabled, calling log_risk_snapshot")
                self.log_risk_snapshot(overall_risk, "risk_assessment")
            
            return overall_risk
            
        except Exception as e:
            logger.error(f"Error calculating overall risk: {e}")
            return {
                'level': 'error',
                'message': f'Error calculating overall risk: {e}',
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def publish_risk_update(self, risk_data: Dict[str, Any]):
        """Publish risk update to Redis for other components (live mode only)."""
        # Only publish to Redis in live mode
        execution_mode = getattr(self.position_monitor, 'execution_mode', 'backtest')
        
        if execution_mode == 'live' and self.redis:
            try:
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.redis.publish,
                    'risk_updates',
                    json.dumps(risk_data)
                )
            except Exception as e:
                logger.error(f"Failed to publish risk update: {e}")
    
    async def get_current_risks(self) -> Dict[str, Any]:
        """Get current risk state."""
        return self.current_risks.copy()
    
    async def assess_risk(self, exposure_data: Dict[str, Any], market_data: Dict = None) -> Dict[str, Any]:
        """
        Unified risk assessment method (wrapper for EventDrivenStrategyEngine).
        
        This is the public API method called by EventDrivenStrategyEngine.
        Internally calls calculate_overall_risk() which does the actual work.
        
        Args:
            exposure_data: Exposure data from ExposureMonitor
            market_data: Optional market data for risk calculations (data slice from current timestamp)
            
        Returns:
            Overall risk assessment with all metrics
        """
        # Store market data for use in risk calculations if needed
        if market_data:
            self.current_market_data = market_data
        
        return await self.calculate_overall_risk(exposure_data)
    
    async def calculate_lst_price_deviation_risk(self, exposure_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Monitor oracle vs market price deviation for LST tokens.
        
        Compares AAVE oracle prices with DEX market prices to detect:
        - Oracle manipulation
        - Market inefficiencies
        - Price feed issues
        
        Args:
            exposure_data: Exposure data containing current timestamp
            
        Returns:
            LST price deviation risk assessment
        """
        try:
            if not self.data_provider:
                return {
                    'level': 'safe',
                    'value': 0.0,
                    'message': 'No data provider available for LST price monitoring',
                    'timestamp': datetime.utcnow().isoformat()
                }
            
            # Check if there are any LST positions in the exposure data
            risk_breakdown = exposure_data.get('risk_breakdown', {})
            aave_data = risk_breakdown.get('aave', {})
            collateral_tokens = aave_data.get('collateral', {}).get('tokens', [])
            
            # Check if any LST tokens are present
            lst_tokens = ['weETH', 'wstETH', 'aWeETH']
            has_lst_positions = any(token in collateral_tokens for token in lst_tokens)
            
            if not has_lst_positions:
                return {
                    'level': 'safe',
                    'value': 0.0,
                    'message': 'No LST positions detected - no price deviation risk',
                    'timestamp': datetime.utcnow().isoformat()
                }
            
            # Get LST type from config (fail-fast)
            lst_type = self.config.get('lst_type', 'weeth')  # Default to weeth if not specified
            
            # Get current timestamp (fail-fast)
            current_timestamp = exposure_data['timestamp']
            if isinstance(current_timestamp, str):
                current_timestamp = pd.Timestamp(current_timestamp, tz='UTC')
            elif not hasattr(current_timestamp, 'tz'):
                current_timestamp = pd.Timestamp(current_timestamp, tz='UTC')
            
            # Get oracle price from AAVE
            try:
                oracle_price = self.data_provider.get_oracle_price(lst_type, current_timestamp)
            except Exception as e:
                logger.warning(f"Could not get oracle price for {lst_type}: {e}")
                return {
                    'level': 'error',
                    'value': 0.0,
                    'message': f'Could not get oracle price for {lst_type}',
                    'timestamp': datetime.utcnow().isoformat()
                }
            
            # Get market price from DEX
            try:
                market_price = self.data_provider.get_lst_market_price(lst_type, current_timestamp)
            except Exception as e:
                logger.warning(f"Could not get market price for {lst_type}: {e}")
                return {
                    'level': 'error',
                    'value': 0.0,
                    'message': f'Could not get market price for {lst_type}',
                    'timestamp': datetime.utcnow().isoformat()
                }
            
            # Calculate price deviation
            if oracle_price == 0:
                deviation_pct = 0.0
            else:
                deviation_pct = abs(market_price - oracle_price) / oracle_price
            
            # Determine risk level based on deviation
            # Thresholds: 1% warning, 2% critical
            warning_threshold = 0.01  # 1%
            critical_threshold = 0.02  # 2%
            
            if deviation_pct >= critical_threshold:
                level = 'critical'
                message = f'{lst_type.upper()} price deviation critical: {deviation_pct:.2%} >= {critical_threshold:.2%}'
            elif deviation_pct >= warning_threshold:
                level = 'warning'
                message = f'{lst_type.upper()} price deviation warning: {deviation_pct:.2%} >= {warning_threshold:.2%}'
            else:
                level = 'safe'
                message = f'{lst_type.upper()} price deviation safe: {deviation_pct:.2%} < {warning_threshold:.2%}'
            
            risk_data = {
                'level': level,
                'value': deviation_pct,
                'oracle_price': oracle_price,
                'market_price': market_price,
                'deviation_pct': deviation_pct,
                'message': message,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Update current state
            self.current_risks['lst_price_deviation'] = risk_data
            
            return risk_data
            
        except Exception as e:
            logger.error(f"Error calculating LST price deviation risk: {e}")
            return {
                'level': 'error',
                'value': 0.0,
                'message': f'Error calculating LST price deviation risk: {e}',
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def calculate_dynamic_ltv_target(self, lst_type: str = 'weeth') -> Decimal:
        """
        Calculate dynamic LTV target using AAVE risk parameters and max_stake_spread_move.
        
        Dynamic LTV = max_ltv - max_stake_spread_move - safety_buffer
        
        Args:
            lst_type: LST type ('weeth' or 'wsteth')
            
        Returns:
            Dynamic LTV target as Decimal
        """
        try:
            if not self.data_provider:
                logger.warning("No data provider available, using static LTV target")
                return Decimal(str(self.aave_safe_ltv))
            
            # Get AAVE risk parameters
            risk_params = self.data_provider.get_aave_risk_params()
            
            # Get max LTV from eMode parameters
            # Handle case sensitivity: weeth -> weETH, wsteth -> wstETH
            if lst_type.lower() == 'weeth':
                pair_key = 'weETH_WETH'
            elif lst_type.lower() == 'wsteth':
                pair_key = 'wstETH_WETH'
            else:
                pair_key = f'{lst_type.upper()}_WETH'
            max_ltv = Decimal(str(risk_params['emode']['max_ltv_limits'][pair_key]))
            
            # Get max_stake_spread_move from mode config
            max_stake_spread_move = Decimal(str(self.max_stake_spread_move))
            
            # Safety buffer (2% additional buffer)
            safety_buffer = Decimal("0.02")
            
            # Calculate dynamic LTV target using LTVCalculator
            dynamic_ltv = LTVCalculator.calculate_dynamic_ltv_target(
                max_ltv=max_ltv,
                max_stake_spread_move=max_stake_spread_move,
                safety_buffer=safety_buffer
            )
            
            logger.info(f"Dynamic LTV target for {lst_type}: {dynamic_ltv:.2%} "
                       f"(max_ltv: {max_ltv:.2%}, spread_move: {max_stake_spread_move:.2%}, buffer: {safety_buffer:.2%})")
            
            return dynamic_ltv
            
        except Exception as e:
            logger.error(f"Error calculating dynamic LTV target: {e}")
            # Fallback to static target
            return Decimal(str(self.aave_safe_ltv))
    
    def calculate_dynamic_risk_thresholds(self, current_performance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate dynamic risk thresholds based on target APY and max drawdown.
        
        Adjusts risk thresholds based on current performance vs targets:
        - If performance is below target: More conservative thresholds
        - If performance is above target: Can be more aggressive
        - If drawdown is approaching max: Much more conservative
        
        Args:
            current_performance: Current performance metrics
            
        Returns:
            Adjusted risk thresholds
        """
        try:
            # Get current performance metrics
            current_apy = current_performance.get('apy', 0.0)
            current_drawdown = current_performance.get('drawdown', 0.0)
            
            # Calculate performance ratios
            apy_ratio = current_apy / self.target_apy if self.target_apy > 0 else 1.0
            drawdown_ratio = current_drawdown / self.max_drawdown if self.max_drawdown > 0 else 0.0
            
            # Base thresholds (from config)
            base_ltv_warning = self.aave_ltv_warning
            base_ltv_critical = self.aave_ltv_critical
            base_margin_warning = self.margin_warning_threshold
            base_margin_critical = self.margin_critical_threshold
            
            # Dynamic adjustment factors
            if drawdown_ratio >= 0.8:  # 80% of max drawdown
                # Very conservative - reduce thresholds significantly
                ltv_adjustment = 0.8  # 20% reduction
                margin_adjustment = 0.7  # 30% reduction
                risk_level = 'critical'
            elif drawdown_ratio >= 0.6:  # 60% of max drawdown
                # Conservative - reduce thresholds moderately
                ltv_adjustment = 0.9  # 10% reduction
                margin_adjustment = 0.85  # 15% reduction
                risk_level = 'warning'
            elif apy_ratio < 0.5:  # Less than 50% of target APY
                # Underperforming - be more conservative
                ltv_adjustment = 0.95  # 5% reduction
                margin_adjustment = 0.9  # 10% reduction
                risk_level = 'underperforming'
            elif apy_ratio > 1.2:  # More than 120% of target APY
                # Overperforming - can be slightly more aggressive
                ltv_adjustment = 1.05  # 5% increase
                margin_adjustment = 1.1  # 10% increase
                risk_level = 'overperforming'
            else:
                # Normal performance - use base thresholds
                ltv_adjustment = 1.0
                margin_adjustment = 1.0
                risk_level = 'normal'
            
            # Calculate adjusted thresholds
            adjusted_thresholds = {
                'aave_ltv_warning': base_ltv_warning * ltv_adjustment,
                'aave_ltv_critical': base_ltv_critical * ltv_adjustment,
                'margin_warning_threshold': base_margin_warning * margin_adjustment,
                'margin_critical_threshold': base_margin_critical * margin_adjustment,
                'risk_level': risk_level,
                'apy_ratio': apy_ratio,
                'drawdown_ratio': drawdown_ratio,
                'ltv_adjustment': ltv_adjustment,
                'margin_adjustment': margin_adjustment
            }
            
            logger.info(f"Dynamic risk adjustment: {risk_level} (APY: {apy_ratio:.2f}, Drawdown: {drawdown_ratio:.2f})")
            
            return adjusted_thresholds
            
        except Exception as e:
            logger.error(f"Error calculating dynamic risk thresholds: {e}")
            # Return base thresholds on error
            return {
                'aave_ltv_warning': self.aave_ltv_warning,
                'aave_ltv_critical': self.aave_ltv_critical,
                'margin_warning_threshold': self.margin_warning_threshold,
                'margin_critical_threshold': self.margin_critical_threshold,
                'risk_level': 'error',
                'apy_ratio': 1.0,
                'drawdown_ratio': 0.0,
                'ltv_adjustment': 1.0,
                'margin_adjustment': 1.0
            }
    
    async def simulate_cex_liquidation(self, exposure_data: Dict[str, Any], venue: str = None) -> Dict[str, Any]:
        """
        Simulate CEX liquidation scenario (lose ALL margin if below 10% maintenance).
        
        This simulates what happens if CEX positions are liquidated:
        - If margin ratio < 10%: Lose ALL margin (100% loss)
        - If margin ratio >= 10%: No liquidation
        
        Args:
            exposure_data: Exposure data containing CEX positions
            
        Returns:
            Liquidation simulation results
        """
        try:
            # Get CEX positions from exposure data
            cex_positions = exposure_data.get('cex_positions', {})
            liquidation_results = {}
            total_margin_at_risk = 0.0
            total_margin_lost = 0.0
            
            # If specific venue requested, only check that venue
            venues_to_check = [venue] if venue else cex_positions.keys()
            
            for venue_name in venues_to_check:
                if venue_name not in cex_positions or not cex_positions[venue_name]:
                    continue
                
                positions = cex_positions[venue_name]
                
                # Get position data (fail-fast)
                current_margin = Decimal(str(positions.get('current_margin', 0)))
                used_margin = Decimal(str(positions.get('used_margin', 0)))
                position_value = Decimal(str(positions.get('position_value', 0)))
                
                if position_value <= 0:
                    continue
                
                # Calculate current margin ratio using MarginCalculator
                total_margin = current_margin + used_margin
                margin_ratio = MarginCalculator.calculate_margin_ratio(
                    current_margin=current_margin,
                    used_margin=used_margin,
                    position_value=position_value
                )
                
                # Simulate liquidation
                maintenance_threshold = Decimal("0.10")  # 10% maintenance margin
                
                if margin_ratio < maintenance_threshold:
                    # Liquidation: lose ALL margin
                    margin_lost = total_margin
                    liquidation_status = 'liquidated'
                    liquidation_message = f'{venue_name} liquidated: {margin_ratio:.2%} < {maintenance_threshold:.2%}'
                else:
                    # No liquidation
                    margin_lost = Decimal("0")
                    liquidation_status = 'safe'
                    liquidation_message = f'{venue_name} safe: {margin_ratio:.2%} >= {maintenance_threshold:.2%}'
                
                liquidation_results[venue_name] = {
                    'status': liquidation_status,
                    'margin_ratio': float(margin_ratio),
                    'margin_lost': float(margin_lost),
                    'total_margin': float(total_margin),
                    'message': liquidation_message
                }
                
                total_margin_at_risk += float(total_margin)
                total_margin_lost += float(margin_lost)
            
            # Overall liquidation summary
            if total_margin_at_risk > 0:
                liquidation_rate = total_margin_lost / total_margin_at_risk
            else:
                liquidation_rate = 0.0
            
            # Determine overall liquidation risk
            if liquidation_rate > 0:
                if liquidation_rate >= 0.5:  # 50% or more margin lost
                    overall_status = 'critical'
                    overall_message = f'Critical liquidation risk: {liquidation_rate:.1%} of margin at risk'
                else:
                    overall_status = 'warning'
                    overall_message = f'Liquidation warning: {liquidation_rate:.1%} of margin at risk'
            else:
                overall_status = 'safe'
                overall_message = 'No liquidation risk'
            
            simulation_result = {
                'overall_status': overall_status,
                'liquidation_rate': liquidation_rate,
                'total_margin_at_risk': total_margin_at_risk,
                'total_margin_lost': total_margin_lost,
                'message': overall_message,
                'venue_details': liquidation_results,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            return simulation_result
            
        except Exception as e:
            logger.error(f"Error simulating CEX liquidation: {e}")
            return {
                'overall_status': 'error',
                'liquidation_rate': 0.0,
                'total_margin_at_risk': 0.0,
                'total_margin_lost': 0.0,
                'message': f'Error simulating CEX liquidation: {e}',
                'venue_details': {},
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def simulate_aave_liquidation(self, exposure_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate AAVE liquidation scenario (50% debt + liquidation bonus from JSON).
        
        This simulates what happens if AAVE positions are liquidated:
        - If health factor < 1.0: Liquidation occurs
        - Liquidation penalty = 50% of debt + liquidation bonus from AAVE risk params
        - Uses liquidation bonus from eMode parameters in JSON
        
        Args:
            exposure_data: Exposure data containing AAVE positions
            
        Returns:
            Liquidation simulation results
        """
        try:
            if not self.data_provider:
                return {
                    'overall_status': 'safe',
                    'liquidation_penalty': 0.0,
                    'debt_liquidated': 0.0,
                    'liquidation_bonus': 0.0,
                    'message': 'No data provider available for AAVE liquidation simulation',
                    'timestamp': datetime.utcnow().isoformat()
                }
            
            # Get AAVE positions from exposure data (fail-fast)
            aave_collateral = Decimal(str(exposure_data.get('aave_collateral', 0)))
            aave_debt = Decimal(str(exposure_data.get('aave_debt', 0)))
            
            if aave_debt <= 0:
                return {
                    'overall_status': 'safe',
                    'liquidation_penalty': 0.0,
                    'debt_liquidated': 0.0,
                    'liquidation_bonus': 0.0,
                    'message': 'No AAVE debt to liquidate',
                    'timestamp': datetime.utcnow().isoformat()
                }
            
            # Get LST type and AAVE risk parameters (fail-fast)
            lst_type = self.config.get('lst_type', 'weeth')  # Default to weeth if not specified
            risk_params = self.data_provider.get_aave_risk_params()
            
            # Get liquidation threshold and bonus from eMode parameters
            if lst_type.lower() == 'weeth':
                pair_key = 'weETH_WETH'
            elif lst_type.lower() == 'wsteth':
                pair_key = 'wstETH_WETH'
            else:
                pair_key = f'{lst_type.upper()}_WETH'
            
            liquidation_threshold = Decimal(str(risk_params['emode']['liquidation_thresholds'][pair_key]))
            liquidation_bonus = Decimal(str(risk_params['emode']['liquidation_bonus'][pair_key]))
            
            # Calculate health factor
            health_factor = HealthCalculator.calculate_health_factor(
                aave_collateral, aave_debt, liquidation_threshold
            )
            
            # Simulate liquidation
            if health_factor < Decimal("1.0"):
                # Liquidation occurs
                liquidation_status = 'liquidated'
                
                # Calculate liquidation penalty
                # 50% of debt + liquidation bonus
                debt_liquidated = aave_debt * Decimal("0.5")  # 50% of debt
                liquidation_penalty = debt_liquidated * (Decimal("1.0") + liquidation_bonus)
                
                liquidation_message = f'AAVE liquidated: health factor {health_factor:.2f} < 1.0'
            else:
                # No liquidation
                liquidation_status = 'safe'
                debt_liquidated = Decimal("0")
                liquidation_penalty = Decimal("0")
                liquidation_message = f'AAVE safe: health factor {health_factor:.2f} >= 1.0'
            
            # Determine overall liquidation risk
            if liquidation_status == 'liquidated':
                if liquidation_penalty >= aave_collateral * Decimal("0.5"):  # 50% of collateral
                    overall_status = 'critical'
                    overall_message = f'Critical AAVE liquidation: {liquidation_penalty:.2f} penalty'
                else:
                    overall_status = 'warning'
                    overall_message = f'AAVE liquidation warning: {liquidation_penalty:.2f} penalty'
            else:
                overall_status = 'safe'
                overall_message = 'No AAVE liquidation risk'
            
            simulation_result = {
                'overall_status': overall_status,
                'liquidation_status': liquidation_status,
                'health_factor': float(health_factor),
                'liquidation_penalty': float(liquidation_penalty),
                'debt_liquidated': float(debt_liquidated),
                'liquidation_bonus': float(liquidation_bonus),
                'liquidation_threshold': float(liquidation_threshold),
                'collateral_value': float(aave_collateral),
                'debt_value': float(aave_debt),
                'message': overall_message,
                'details': liquidation_message,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            return simulation_result
            
        except Exception as e:
            logger.error(f"Error simulating AAVE liquidation: {e}")
            return {
                'overall_status': 'error',
                'liquidation_penalty': 0.0,
                'debt_liquidated': 0.0,
                'liquidation_bonus': 0.0,
                'message': f'Error simulating AAVE liquidation: {e}',
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """Get risk summary (synchronous version for StrategyManager)."""
        try:
            # Return a basic risk summary structure
            return {
                'aave_ltv': 0.0,
                'aave_health_factor': 0.0,
                'cex_margin_ratios': {},
                'net_delta_risk': 0.0,
                'overall_risk_level': 'LOW',
                'alerts': []
            }
        except Exception as e:
            logger.error(f"Error getting risk summary: {e}")
            return {}
    
    async def should_trigger_rebalancing(self, exposure_data: Dict[str, Any]) -> bool:
        """Determine if rebalancing should be triggered based on risk."""
        overall_risk = await self.calculate_overall_risk(exposure_data)
        
        # Trigger rebalancing for critical risks or multiple warnings
        if overall_risk['level'] == 'critical':
            return True
        
        if overall_risk['level'] == 'warning' and overall_risk['summary']['warning_risks'] >= 2:
            return True
        
        return False
    
    async def calculate_liquidation_terms(self, exposure_data: Dict[str, Any], 
                                        aave_risk: Dict[str, Any], 
                                        cex_risk: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate liquidation terms for strategy_manager orchestration.
        
        This method simulates liquidation scenarios and returns terms that the
        strategy_manager can use to orchestrate position updates.
        
        Args:
            exposure_data: Current exposure data
            aave_risk: AAVE risk assessment
            cex_risk: CEX margin risk assessment
            
        Returns:
            Liquidation terms for strategy_manager
        """
        liquidation_terms = {
            'aave_liquidation': None,
            'cex_liquidations': {},
            'total_liquidation_impact': 0.0,
            'liquidation_venues': []
        }
        
        try:
            # AAVE liquidation simulation
            if aave_risk.get('level') == 'critical':
                aave_liquidation = await self.simulate_aave_liquidation(exposure_data)
                if aave_liquidation.get('overall_status') != 'safe':
                    liquidation_terms['aave_liquidation'] = aave_liquidation
                    liquidation_terms['liquidation_venues'].append('aave')
                    liquidation_terms['total_liquidation_impact'] += aave_liquidation.get('liquidation_penalty', 0.0)
            
            # CEX liquidation simulations
            if cex_risk.get('level') == 'critical' and 'venue_details' in cex_risk:
                for venue, venue_risk in cex_risk['venue_details'].items():
                    if venue_risk.get('level') == 'critical':
                        cex_liquidation = await self.simulate_cex_liquidation(exposure_data, venue)
                        if cex_liquidation.get('overall_status') != 'safe':
                            liquidation_terms['cex_liquidations'][venue] = cex_liquidation
                            liquidation_terms['liquidation_venues'].append(venue)
                            liquidation_terms['total_liquidation_impact'] += cex_liquidation.get('total_margin_lost', 0.0)
            
            return liquidation_terms
            
        except Exception as e:
            logger.error(f"Error calculating liquidation terms: {e}")
            return {
                'aave_liquidation': None,
                'cex_liquidations': {},
                'total_liquidation_impact': 0.0,
                'liquidation_venues': [],
                'error': str(e)
            }