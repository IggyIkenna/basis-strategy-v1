"""
Simplified Mode-Agnostic Exposure Monitor

Converts position amounts to share class currency and USD equivalents.
Same dimensionality as PositionMonitor - no complex categorization yet.

Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Section 7 (Generic vs Mode-Specific)
Reference: docs/specs/02_EXPOSURE_MONITOR.md - Mode-agnostic exposure calculation
"""

from typing import Dict, List, Any, Optional
import logging
import pandas as pd
import os
import uuid
from pathlib import Path
from datetime import datetime, timezone

from ...infrastructure.logging.structured_logger import StructuredLogger
from ...infrastructure.logging.domain_event_logger import DomainEventLogger
from ...core.models.domain_events import ExposureSnapshot
from ...core.errors.error_codes import ERROR_REGISTRY

logger = logging.getLogger(__name__)

class ExposureMonitor:
    """
    Simplified exposure monitor that converts positions to share class currency + USD.
    
    Input: Flat position dict from PositionMonitor {"venue:position_type:token": amount}
    Output: Same structure with conversions to share_class currency and USD
    
    Uses utility_manager for all conversions (no hardcoded logic).
    """
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config: Dict[str, Any], data_provider, utility_manager, correlation_id: str = None, pid: int = None, log_dir: Path = None):
        """
        Initialize simplified exposure monitor.
        
        No component-specific config needed:
        - Uses position_subscriptions from position_monitor
        - Always calculates both USD and share_class values
        - All conversions via utility_manager
        
        Args:
            config: Strategy configuration
            data_provider: Data provider instance (for market data)
            utility_manager: Centralized utility manager (for conversions)
        """
        self.config = config
        self.data_provider = data_provider
        self.utility_manager = utility_manager
        self.health_status = "healthy"
        self.error_count = 0
        
        # Get share class from config (root level, not component_config)
        self.share_class = config['share_class']
        
        # Initialize logging infrastructure
        self.correlation_id = correlation_id or str(uuid.uuid4().hex)
        self.pid = pid or os.getpid()
        self.log_dir = log_dir
        
        # Initialize structured logger
        self.logger = StructuredLogger(
            component_name="ExposureMonitor",
            correlation_id=self.correlation_id,
            pid=self.pid,
            log_dir=self.log_dir,
            engine=None
        )
        
        # Initialize domain event logger
        self.domain_event_logger = DomainEventLogger(self.log_dir) if self.log_dir else None
        
        # Exposure tracking
        self.last_exposures = None
        self.last_calculation_timestamp = None
        
        self.logger.info(
            f"ExposureMonitor initialized: share_class={self.share_class}",
            share_class=self.share_class,
            mode=config.get('mode')
        )
        
        logger.info(f"ExposureMonitor initialized (simplified, config-free): share_class={self.share_class}")
    
    def _log_exposure_snapshot(self, exposures: Dict[str, Any]) -> None:
        """Log exposure snapshot as domain event."""
        if not self.log_dir or not self.domain_event_logger:
            return
        
        timestamp = datetime.now().isoformat()
        real_utc = datetime.now(timezone.utc).isoformat()
        
        snapshot = ExposureSnapshot(
            timestamp=timestamp,
            real_utc_time=real_utc,
            correlation_id=self.correlation_id,
            pid=self.pid,
            net_delta_usd=exposures.get('net_delta_usd', 0.0),
            asset_exposures=exposures.get('asset_exposures', {}),
            total_value_usd=exposures.get('total_value_usd', 0.0),
            share_class_value=exposures.get('share_class_value', 0.0),
            metadata={}
        )
        
        self.domain_event_logger.log_exposure_snapshot(snapshot)
    
    def _handle_error(self, error: Exception, context: str = "") -> None:
        """Handle errors with structured error handling."""
        self.error_count += 1
        error_code = f"EXP_ERROR_{self.error_count:04d}"
        
        self.logger.error(
            f"Exposure Monitor error: {str(error)}",
            error_code="EXP-001",
            exc_info=error,
            operation="exposure_calculation",
            context=context,
            error_count=self.error_count
        )
        
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
            'share_class': self.share_class,
            'last_exposures_available': self.last_exposures is not None,
            'last_calculation_timestamp': str(self.last_calculation_timestamp) if self.last_calculation_timestamp else None,
            'component': self.__class__.__name__
        }
    
    def calculate_exposure(
        self,
        timestamp: pd.Timestamp,
        position_snapshot: Dict[str, float],
        market_data: Dict
    ) -> Dict[str, Any]:
        """
        Calculate exposure by converting all positions to share class currency + USD.
        
        Simple approach:
        1. Take flat position dict from PositionMonitor
        2. For each position, convert to share_class currency using utility_manager
        3. Also convert to USD for reference
        4. Return exposure in same dimensional structure
        
        Args:
            timestamp: Current loop timestamp
            position_snapshot: Flat dict from PositionMonitor {"venue:position_type:token": amount}
            market_data: Market data from DataProvider
            
        Returns:
            Dictionary with:
                - timestamp: Current timestamp
                - share_class: Share class currency (USDT or ETH)
                - total_value_usd: Total portfolio value in USD
                - share_class_value: Total portfolio value in share class currency
                - total_exposure: Same as share_class_value (for compatibility)
                - exposures: Dict mapping each position_key to its exposure values
        """
        try:
            start_time = pd.Timestamp.now(tz='UTC')
            
            # Store timestamp
            self.last_calculation_timestamp = timestamp
            
            # Get position subscriptions from position_monitor config
            # This is the ONLY config we need - reuse what position_monitor uses
            position_subscriptions = self.config.get('component_config', {}).get('position_monitor', {}).get('position_subscriptions', [])
            
            # Calculate exposures for each position
            exposures = {}
            total_value_usd = 0.0
            total_value_share_class = 0.0
            
            # Process all subscribed positions (even if zero) + any active positions
            all_position_keys = set(position_subscriptions) | set(position_snapshot.keys())
            
            for position_key in all_position_keys:
                amount = position_snapshot.get(position_key, 0.0)
                # KEEP all positions including zeros for full record set
                
                # Parse position key: "venue:position_type:token"
                parts = position_key.split(':')
                if len(parts) < 3:
                    logger.warning(f"Invalid position key format: {position_key}")
                    continue
                
                venue, position_type, token = parts[0], parts[1], parts[2]
                
                # Convert to USD and share class using utility_manager
                try:
                    # Use utility_manager for conversions (handles aTokens correctly)
                    value_usd = self.utility_manager.convert_position_to_usd(
                        position_key=position_key,
                        amount=amount,
                        timestamp=timestamp
                    )
                    
                    # Convert to share class currency
                    value_share_class = self.utility_manager.convert_position_to_share_class(
                        position_key=position_key,
                        amount=amount,
                        share_class=self.share_class,
                        timestamp=timestamp
                    )
                    
                    # Calculate effective price per token unit
                    token_price_usd = value_usd / amount if amount > 0 else 0.0
                    
                    # Store exposure data with BOTH usd_value and share_class_value per instrument
                    exposures[position_key] = {
                        'venue': venue,
                        'position_type': position_type,
                        'token': token,
                        'amount': amount,
                        'price_usd': token_price_usd,  # Price per unit in USD
                        'value_usd': value_usd,  # Total value in USD
                        'value_share_class': value_share_class  # Total value in share class currency
                    }
                    
                    # Accumulate totals
                    total_value_usd += value_usd
                    total_value_share_class += value_share_class
                
                except Exception as e:
                    logger.warning(f"Error converting position {position_key}: {e}")
                    # Continue with other positions
                    continue
            
            # Build exposure result
            exposure_result = {
                'timestamp': timestamp,
                'share_class': self.share_class,
                'total_value_usd': total_value_usd,
                'share_class_value': total_value_share_class,
                'total_exposure': total_value_share_class,  # For compatibility
                'exposures': exposures,
                'exposure_count': len(exposures)
            }
            
            # Store for future reference
            self.last_exposures = exposure_result
            
            # Log calculation
            end_time = pd.Timestamp.now(tz='UTC')
            processing_time_ms = (end_time - start_time).total_seconds() * 1000
            
            # Log summary
            self.structured_logger.info(
                f"Exposure calculated: {len(exposures)} positions, ${total_value_usd:,.2f} USD, {total_value_share_class:,.2f} {self.share_class}",
                event_type="exposure_calculated",
                metadata={
                    'timestamp_utc': timestamp.isoformat(),
                    'exposure_count': len(exposures),
                    'total_value_usd': total_value_usd,
                    'share_class_value': total_value_share_class,
                    'share_class': self.share_class,
                    'processing_time_ms': processing_time_ms,
                    'subscribed_positions': len(position_subscriptions)
                }
            )
            
            # Log detailed instrument-level data
            self.structured_logger.info(
                f"Instrument exposures: {len(exposures)} instruments tracked",
                event_type="instrument_exposures",
                metadata={
                    'timestamp_utc': timestamp.isoformat(),
                    'exposures': exposures,  # Full granular data per instrument
                    'share_class': self.share_class
                }
            )
            
            logger.debug(
                f"Exposure calculated at {timestamp}: "
                f"{len(exposures)} positions, "
                f"${total_value_usd:,.2f} USD, "
                f"{total_value_share_class:,.2f} {self.share_class}"
            )
            
            # Log exposure snapshot
            self._log_exposure_snapshot(exposure_result)
            
            return exposure_result
        
        except Exception as e:
            self._handle_error(e, f"calculate_exposure at {timestamp}")
            # Return empty exposure on error
            return {
                'timestamp': timestamp,
                'share_class': self.share_class,
                'total_value_usd': 0.0,
                'share_class_value': 0.0,
                'total_exposure': 0.0,
                'exposures': {},
                'exposure_count': 0,
                'error': str(e)
            }
    
    def get_current_exposure(self) -> Dict:
        """Get current exposure snapshot."""
        if self.last_exposures is None:
            return {
                'timestamp': None,
                'share_class': self.share_class,
                'total_value_usd': 0.0,
                'share_class_value': 0.0,
                'total_exposure': 0.0,
                'exposures': {},
                'exposure_count': 0
            }
        return self.last_exposures.copy()
    
    def update_state(self, timestamp: pd.Timestamp, trigger_source: str, **kwargs) -> None:
        """
        Update component state with new timestamp.
        
        Args:
            timestamp: Current timestamp
            trigger_source: Source of the update trigger
            **kwargs: Additional update parameters
        """
        self.last_calculation_timestamp = timestamp
        
        self.structured_logger.info(
            f"State updated: trigger_source={trigger_source}",
            event_type="state_update",
            metadata={
                'timestamp_utc': timestamp.isoformat(),
                'trigger_source': trigger_source,
                **kwargs
            }
        )
        
        logger.debug(f"ExposureMonitor state updated at {timestamp} (trigger: {trigger_source})")
