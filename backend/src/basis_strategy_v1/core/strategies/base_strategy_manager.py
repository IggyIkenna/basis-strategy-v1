"""
Base Strategy Manager Architecture

This module provides the base class for all strategy managers, implementing
order generation focused architecture with inheritance-based strategy modes.

Reference: docs/ARCHITECTURAL_DECISION_RECORDS.md - ADR-007
Reference: docs/STRATEGY_MODES.md - Standardized Strategy Manager Architecture
Reference: docs/specs/5B_BASE_STRATEGY_MANAGER.md - Component specification
Reference: docs/WORKFLOW_GUIDE.md - Order generation workflow
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import logging
import os
import pandas as pd
from pathlib import Path

from ...core.models.order import Order
from ...infrastructure.logging.structured_logger import StructuredLogger
from ...infrastructure.logging.domain_event_logger import DomainEventLogger

logger = logging.getLogger(__name__)


class BaseStrategyManager(ABC):
    """Abstract base class for all strategy managers - ORDER GENERATION FOCUSED"""

    def __init__(
        self,
        config: Dict[str, Any],
        data_provider,
        exposure_monitor,
        position_monitor,
        risk_monitor,
        utility_manager=None,
        correlation_id: str = None,
        pid: int = None,
        log_dir: Path = None,
    ):
        """
        Initialize base strategy manager.

        Args:
            config: Strategy configuration
            data_provider: Data provider instance for market data
            exposure_monitor: Exposure monitor instance for exposure data
            position_monitor: Position monitor instance for position data
            risk_monitor: Risk monitor instance for risk assessment
            utility_manager: Centralized utility manager for conversion rates
            correlation_id: Unique correlation ID for this run
            pid: Process ID
            log_dir: Log directory path (logs/{correlation_id}/{pid}/)
        """
        self.config = config
        self.data_provider = data_provider
        self.exposure_monitor = exposure_monitor
        self.position_monitor = position_monitor
        self.risk_monitor = risk_monitor
        self.utility_manager = utility_manager

        # Initialize logging infrastructure
        self.correlation_id = correlation_id or "default"
        self.pid = pid or 0
        self.log_dir = log_dir or Path("logs/default/0")

        # Initialize structured logger
        self.logger = StructuredLogger(
            component_name=self.__class__.__name__,
            correlation_id=self.correlation_id,
            pid=self.pid,
            log_dir=self.log_dir,
            engine=None,  # Will be set by event engine if available
        )

        # Initialize domain event logger
        self.domain_event_logger = DomainEventLogger(
            self.log_dir, 
            correlation_id=self.correlation_id, 
            pid=self.pid
        )

        # Extract strategy-specific config
        self.strategy_config = config.get("component_config", {}).get("strategy_manager", {})
        self.strategy_type = self.strategy_config.get("strategy_type")
        self.available_actions = self.strategy_config.get("actions", [])
        self.rebalancing_triggers = self.strategy_config.get("rebalancing_triggers", [])

        # Log component initialization
        self.logger.info(
            f"BaseStrategyManager initialized for {self.strategy_type}",
            strategy_type=self.strategy_type,
            available_actions=self.available_actions,
            rebalancing_triggers=self.rebalancing_triggers,
            execution_mode=os.getenv("BASIS_EXECUTION_MODE", "backtest"),
        )

    @abstractmethod
    def generate_orders(
        self, timestamp: pd.Timestamp, exposure: Dict, risk_assessment: Dict, market_data: Dict
    ) -> List[Order]:
        """
        Generate orders for this strategy mode - MAIN METHOD

        Args:
            timestamp: Current timestamp
            exposure: From exposure_monitor.get_current_exposure()
            risk_assessment: From risk_monitor.get_current_risk_metrics()
            market_data: From data_provider.get_data(timestamp)

        Returns:
            List[Order]: Orders to execute via ExecutionManager
        """
        pass

    @abstractmethod
    def should_enter_position(
        self, current_equity: float, exposure_data: Dict, risk_assessment: Dict
    ) -> bool:
        """Check if strategy should enter a position"""
        pass

    @abstractmethod
    def should_exit_position(self, exposure_data: Dict, risk_assessment: Dict) -> bool:
        """Check if strategy should exit position"""
        pass

    @abstractmethod
    def should_sell_dust(self, exposure_data: Dict) -> bool:
        """Check if dust tokens exceed threshold"""
        pass

    def get_current_positions(self) -> Dict[str, float]:
        """Get current positions from position monitor"""
        try:
            return self.position_monitor.get_current_positions()
        except Exception as e:
            self.logger.error(
                "Failed to get current positions",
                error_code="STRAT-001",
                exc_info=e,
                method="get_current_positions",
            )
            return {}

    def get_current_exposure(self) -> Dict[str, Any]:
        """Get current exposure from exposure monitor"""
        try:
            return self.exposure_monitor.get_current_exposure()
        except Exception as e:
            self.logger.error(
                "Failed to get current exposure",
                error_code="STRAT-001",
                exc_info=e,
                method="get_current_exposure",
            )
            return {}

    def get_current_risk_metrics(self) -> Dict[str, Any]:
        """Get current risk metrics from risk monitor"""
        try:
            return self.risk_monitor.get_current_risk_metrics()
        except Exception as e:
            self.logger.error(
                "Failed to get current risk metrics",
                error_code="STRAT-001",
                exc_info=e,
                method="get_current_risk_metrics",
            )
            return {}

    def get_market_data(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Get market data from utility manager"""
        try:
            if not self.utility_manager:
                raise ValueError("utility_manager is required but not provided")
            # Use utility_manager methods for centralized data access
            return self.utility_manager.data_provider.get_data(timestamp)
        except Exception as e:
            self.logger.error(
                "Failed to get market data",
                error_code="STRAT-001",
                exc_info=e,
                method="get_market_data",
                timestamp=str(timestamp),
            )
            return {}

    def get_price_for_instrument(
        self, instrument_key: str, timestamp: pd.Timestamp, quote_currency: str = "USD"
    ) -> float:
        """Get price for instrument using utility manager"""
        try:
            if not self.utility_manager:
                raise ValueError("utility_manager is required but not provided")
            return self.utility_manager.get_price_for_instrument_key(
                instrument_key, timestamp, quote_currency
            )
        except Exception as e:
            self.logger.error(
                "Failed to get price for instrument",
                error_code="STRAT-002",
                exc_info=e,
                method="get_price_for_instrument",
                instrument_key=instrument_key,
                timestamp=str(timestamp),
            )
            return 0.0

    def get_equity(self) -> float:
        """Get current equity in share class currency"""
        try:
            exposure_data = self.get_current_exposure()
            return exposure_data.get("total_exposure", 0.0)
        except Exception as e:
            self.logger.error(
                "Failed to get equity", error_code="STRAT-001", exc_info=e, method="GET_EQUITY"
            )
            return 0.0

    def should_sell_dust(self, dust_tokens: Dict[str, float]) -> bool:
        """Check if dust tokens exceed threshold"""
        try:
            dust_value = sum(
                self.get_token_value(token, amount) for token, amount in dust_tokens.items()
            )
            equity = self.get_equity()
            dust_threshold = self.config.get("dust_delta", 0.002)
            return dust_value > (equity * dust_threshold)
        except Exception as e:
            self.logger.error(
                "Failed to check dust threshold",
                error_code="STRAT-001",
                exc_info=e,
                method="should_sell_dust",
                dust_tokens=dust_tokens,
            )
            return False

    def get_token_value(self, token: str, amount: float) -> float:
        """Get USD value of token amount"""
        try:
            # This would typically use a price feed or data provider
            # For now, return a placeholder implementation
            price_feed = self.config.get("price_feeds", {})
            token_price = price_feed.get(token, 1.0)  # Default to 1.0 if no price
            return amount * token_price
        except Exception as e:
            self.logger.error(
                "Failed to get token value",
                error_code="STRAT-001",
                exc_info=e,
                method="get_token_value",
                token=token,
                amount=amount,
            )
            return 0.0

    def trigger_tight_loop(self):
        """
        Trigger tight loop execution reconciliation pattern.

        The tight loop ensures that each execution instruction is followed by
        position reconciliation before proceeding to the next instruction.

        Tight Loop = execution → position_monitor → reconciliation → next instruction
        """
        try:
            # Note: event_engine would be passed in if needed for strategy logic
            # For now, this is a placeholder
            pass
        except Exception as e:
            self.logger.error(
                "Failed to trigger tight loop",
                error_code="STRAT-001",
                exc_info=e,
                method="trigger_tight_loop",
            )

    def get_current_equity(self, exposure_data: Dict) -> float:
        """Get current equity from exposure data."""
        return exposure_data.get("total_exposure", 0.0)

    def should_enter_position(self, exposure_data: Dict, risk_assessment: Dict) -> bool:
        """Check if strategy should enter a position."""
        current_equity = self.get_current_equity(exposure_data)
        return current_equity > 0

    def should_exit_position(self, exposure_data: Dict, risk_assessment: Dict) -> bool:
        """Check if strategy should exit position."""
        # Check for risk overrides
        if risk_assessment.get("risk_override", False):
            return True

        # Check for withdrawal triggers
        if exposure_data.get("WITHDRAWAL_REQUESTED", False):
            return True

        return False

    def get_dust_tokens(self, exposure_data: Dict) -> Dict[str, float]:
        """Get dust tokens that should be converted."""
        return exposure_data.get("dust_tokens", {})

    def should_sell_dust(self, exposure_data: Dict) -> bool:
        """Check if dust tokens exceed threshold."""
        dust_tokens = self.get_dust_tokens(exposure_data)
        if not dust_tokens:
            return False

        try:
            dust_value = sum(
                self.get_token_value(token, amount) for token, amount in dust_tokens.items()
            )
            equity = self.get_current_equity(exposure_data)
            dust_threshold = self.config.get("dust_delta", 0.002)
            return dust_value > (equity * dust_threshold)
        except Exception as e:
            self.logger.error(
                "Failed to check dust threshold",
                error_code="STRAT-001",
                exc_info=e,
                method="should_sell_dust",
                dust_tokens=dust_tokens,
            )
            return False

    def get_strategy_info(self) -> Dict[str, Any]:
        """
        Get basic strategy information.

        Returns:
            Dictionary with basic strategy information
        """
        try:
            return {
                "strategy_type": self.__class__.__name__,
                "equity": self.get_equity(),
                "CORRELATION_ID": self.correlation_id,
                "pid": self.pid,
            }
        except Exception as e:
            self.logger.error("Error getting strategy info", error_code="STRAT-001", exc_info=e)
            return {"strategy_type": self.__class__.__name__, "equity": 0.0, "error": str(e)}
