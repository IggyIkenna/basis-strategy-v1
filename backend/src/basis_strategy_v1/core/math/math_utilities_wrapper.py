"""
Math Utilities Wrapper with JSONL Logging

Provides a wrapper around the pure math calculators that adds JSONL event logging
as specified in the component specifications.

Reference: docs/specs/16_MATH_UTILITIES.md - Event Logging Requirements
"""

import logging
import os
import uuid
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional
from decimal import Decimal

from .ltv_calculator import LTVCalculator
from .margin_calculator import MarginCalculator
from .health_calculator import HealthCalculator
from .metrics_calculator import MetricsCalculator
from ...infrastructure.logging.structured_logger import StructuredLogger

logger = logging.getLogger(__name__)


class MathUtilities:
    """
    Math Utilities wrapper with JSONL event logging.

    Provides centralized access to all math calculators with component-specific
    event logging as specified in the component specifications.
    """

    def __init__(self, config: Dict[str, Any], execution_mode: str, utility_manager=None):
        """
        Initialize Math Utilities with JSONL logging and UtilityManager integration.

        Args:
            config: Configuration dictionary (reference, never modified)
            execution_mode: 'backtest' or 'live' (from BASIS_EXECUTION_MODE)
            utility_manager: Centralized utility manager for config-driven operations
        """
        # Store references (never passed as runtime parameters)
        self.config = config
        self.execution_mode = execution_mode
        self.utility_manager = utility_manager

        # Initialize structured logger (includes JSONL logging)
        self.structured_logger = StructuredLogger(
            component_name="math_utilities",
            correlation_id=str(uuid.uuid4().hex),
            pid=os.getpid(),
            log_dir=Path("logs/default/0"),
            engine=None,
        )

        # Initialize calculators
        self.ltv_calculator = LTVCalculator()
        self.margin_calculator = MarginCalculator()
        self.health_calculator = HealthCalculator()
        self.metrics_calculator = MetricsCalculator()

        # Component state
        self.calculation_count = 0
        self.error_count = 0
        self.last_calculation_timestamp = None

        # Log initialization
        self.structured_logger.info(
            f"MathUtilities initialized in {execution_mode} mode",
            event_type="component_initialization",
            metadata={
                "execution_mode": execution_mode,
                "config_hash": hash(str(config)),
                "precision": config.get("decimal_places", 8),
                "utility_manager_available": utility_manager is not None,
                "component_type": "MathUtilities",
            },
        )

        logger.info(
            f"MathUtilities initialized in {execution_mode} mode with UtilityManager: {utility_manager is not None}"
        )

    def calculate_current_ltv(self, collateral_value: Decimal, debt_value: Decimal) -> Decimal:
        """Calculate current LTV ratio with event logging."""
        try:
            result = self.ltv_calculator.calculate_current_ltv(collateral_value, debt_value)

            # Log calculation event
            self.calculation_count += 1
            self.last_calculation_timestamp = pd.Timestamp.now(tz="UTC")

            self.structured_logger.info(
                f"LTV calculation completed: {float(result):.4f}",
                event_type="ltv_calculation",
                metadata={
                    "collateral_value": float(collateral_value),
                    "debt_value": float(debt_value),
                    "result": float(result),
                    "calculation_count": self.calculation_count,
                },
            )

            return result

        except Exception as e:
            self.error_count += 1
            self.structured_logger.error(
                f"LTV calculation failed: {str(e)}",
                event_type="calculation_error",
                metadata={
                    "error_code": "LTV-001",
                    "error_message": f"LTV calculation failed: {str(e)}",
                    "error_severity": "HIGH",
                    "collateral_value": float(collateral_value),
                    "debt_value": float(debt_value),
                },
            )
            raise

    def calculate_projected_ltv_after_borrowing(
        self,
        current_collateral_value: Decimal,
        current_debt_value: Decimal,
        additional_borrowing_usd: Decimal,
        collateral_efficiency: Decimal = Decimal("0.95"),
    ) -> Decimal:
        """Calculate projected LTV after borrowing with event logging."""
        try:
            result = self.ltv_calculator.calculate_projected_ltv_after_borrowing(
                current_collateral_value,
                current_debt_value,
                additional_borrowing_usd,
                collateral_efficiency,
            )

            # Log calculation event
            self.calculation_count += 1
            self.last_calculation_timestamp = pd.Timestamp.now(tz="UTC")

            self.structured_logger.info(
                f"Projected LTV calculation completed: {float(result):.4f}",
                event_type="projected_ltv_calculation",
                metadata={
                    "current_collateral_value": float(current_collateral_value),
                    "current_debt_value": float(current_debt_value),
                    "additional_borrowing_usd": float(additional_borrowing_usd),
                    "collateral_efficiency": float(collateral_efficiency),
                    "result": float(result),
                    "calculation_count": self.calculation_count,
                },
            )

            return result

        except Exception as e:
            self.error_count += 1
            self.structured_logger.error(
                f"Projected LTV calculation failed: {str(e)}",
                event_type="calculation_error",
                metadata={
                    "error_code": "LTV-002",
                    "error_message": f"Projected LTV calculation failed: {str(e)}",
                    "error_severity": "HIGH",
                    "current_collateral_value": float(current_collateral_value),
                    "current_debt_value": float(current_debt_value),
                    "additional_borrowing_usd": float(additional_borrowing_usd),
                },
            )
            raise

    def calculate_margin_capacity(
        self,
        available_balance: Decimal,
        margin_requirement: Decimal,
        safety_buffer: Decimal = Decimal("0.1"),
    ) -> Decimal:
        """Calculate margin capacity with event logging."""
        try:
            result = self.margin_calculator.calculate_margin_capacity(
                available_balance, margin_requirement, safety_buffer
            )

            # Log calculation event
            self.calculation_count += 1
            self.last_calculation_timestamp = pd.Timestamp.now(tz="UTC")

            self.structured_logger.info(
                f"Margin capacity calculation completed: {float(result):.4f}",
                event_type="margin_capacity_calculation",
                metadata={
                    "available_balance": float(available_balance),
                    "margin_requirement": float(margin_requirement),
                    "safety_buffer": float(safety_buffer),
                    "result": float(result),
                    "calculation_count": self.calculation_count,
                },
            )

            return result

        except Exception as e:
            self.error_count += 1
            self.structured_logger.error(
                f"Margin capacity calculation failed: {str(e)}",
                event_type="calculation_error",
                metadata={
                    "error_code": "MARGIN-001",
                    "error_message": f"Margin capacity calculation failed: {str(e)}",
                    "error_severity": "HIGH",
                    "available_balance": float(available_balance),
                    "margin_requirement": float(margin_requirement),
                },
            )
            raise

    def calculate_health_factor(
        self, collateral_value: Decimal, debt_value: Decimal, liquidation_threshold: Decimal
    ) -> Decimal:
        """Calculate health factor with event logging."""
        try:
            result = self.health_calculator.calculate_health_factor(
                collateral_value, debt_value, liquidation_threshold
            )

            # Log calculation event
            self.calculation_count += 1
            self.last_calculation_timestamp = pd.Timestamp.now(tz="UTC")

            self.structured_logger.info(
                f"Health factor calculation completed: {float(result):.4f}",
                event_type="health_factor_calculation",
                metadata={
                    "collateral_value": float(collateral_value),
                    "debt_value": float(debt_value),
                    "liquidation_threshold": float(liquidation_threshold),
                    "result": float(result),
                    "calculation_count": self.calculation_count,
                },
            )

            return result

        except Exception as e:
            self.error_count += 1
            self.structured_logger.error(
                f"Health factor calculation failed: {str(e)}",
                event_type="calculation_error",
                metadata={
                    "error_code": "HEALTH-001",
                    "error_message": f"Health factor calculation failed: {str(e)}",
                    "error_severity": "HIGH",
                    "collateral_value": float(collateral_value),
                    "debt_value": float(debt_value),
                    "liquidation_threshold": float(liquidation_threshold),
                },
            )
            raise

    def calculate_metrics(
        self, portfolio, initial_capital: Decimal, timestamp: pd.Timestamp
    ) -> Dict[str, Any]:
        """Calculate portfolio metrics with event logging."""
        try:
            result = self.metrics_calculator.calculate_metrics(
                portfolio, initial_capital, timestamp
            )

            # Log calculation event
            self.calculation_count += 1
            self.last_calculation_timestamp = pd.Timestamp.now(tz="UTC")

            self.structured_logger.info(
                f"Metrics calculation completed with {len(result) if isinstance(result, dict) else 0} metrics",
                event_type="metrics_calculation",
                metadata={
                    "initial_capital": float(initial_capital),
                    "timestamp": timestamp.isoformat(),
                    "result_keys": list(result.keys()) if isinstance(result, dict) else [],
                    "calculation_count": self.calculation_count,
                },
            )

            return result

        except Exception as e:
            self.error_count += 1
            self.structured_logger.error(
                f"Metrics calculation failed: {str(e)}",
                event_type="calculation_error",
                metadata={
                    "error_code": "METRICS-001",
                    "error_message": f"Metrics calculation failed: {str(e)}",
                    "error_severity": "HIGH",
                    "initial_capital": float(initial_capital),
                    "timestamp": timestamp.isoformat(),
                },
            )
            raise

    def check_component_health(self) -> Dict[str, Any]:
        """Check component health status for monitoring and diagnostics."""
        return {
            "status": "healthy" if self.error_count < 10 else "degraded",
            "error_count": self.error_count,
            "execution_mode": self.execution_mode,
            "calculation_count": self.calculation_count,
            "last_calculation_timestamp": self.last_calculation_timestamp.isoformat()
            if self.last_calculation_timestamp
            else None,
            "component": "MathUtilities",
        }

    def log_performance_metric(
        self,
        metric_name: str,
        value: float,
        unit: str,
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log a performance metric."""
        self.structured_logger.info(
            f"Performance metric: {metric_name} = {value} {unit}",
            event_type="performance_metric",
            metadata={
                "metric_name": metric_name,
                "value": value,
                "unit": unit,
                "additional_data": additional_data or {},
            },
        )

    def get_liquidity_index(self, token: str, timestamp: pd.Timestamp) -> float:
        """Get liquidity index using UtilityManager if available."""
        if self.utility_manager:
            return self.utility_manager.get_liquidity_index(token, timestamp)
        else:
            logger.warning("UtilityManager not available, returning default liquidity index")
            return 1.0

    def get_market_price(self, token: str, currency: str, timestamp: pd.Timestamp) -> float:
        """Get market price using UtilityManager if available."""
        if self.utility_manager:
            # Use position key convention for price lookup
            instrument_key = f"wallet:BaseToken:{token}"
            return self.utility_manager.get_price_for_instrument_key(instrument_key, timestamp)
        else:
            logger.warning("UtilityManager not available, returning default price")
            return 1.0 if token == currency else 0.0

    def convert_to_usdt(self, amount: float, token: str, timestamp: pd.Timestamp) -> float:
        """Convert token amount to USDT equivalent using UtilityManager if available."""
        if self.utility_manager:
            instrument_key = f"wallet:BaseToken:{token}"
            return self.utility_manager.convert_position_to_usd(instrument_key, amount, timestamp)
        else:
            logger.warning("UtilityManager not available, returning original amount")
            return amount

    def convert_from_liquidity_index(
        self, amount: float, token: str, timestamp: pd.Timestamp
    ) -> float:
        """Convert from liquidity index using UtilityManager if available."""
        if self.utility_manager:
            liquidity_index = self.utility_manager.get_liquidity_index(token, timestamp)
            return amount / liquidity_index if liquidity_index > 0 else amount
        else:
            logger.warning("UtilityManager not available, returning original amount")
            return amount

    def close(self):
        """Close structured logger."""
        if hasattr(self, "structured_logger"):
            # StructuredLogger handles its own cleanup
            pass
