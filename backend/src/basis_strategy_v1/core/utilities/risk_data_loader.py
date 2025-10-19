"""
Risk Data Loader

Centralized loader for all risk parameters from data files.
Loads AAVE risk parameters and CEX margin requirements.

Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Section 7 (Generic vs Mode-Specific)
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from decimal import Decimal
import os


logger = logging.getLogger(__name__)

# Error codes for Risk Data Loader
ERROR_CODES = {
    "RDL-001": "Failed to load AAVE risk parameters",
    "RDL-002": "Failed to load CEX margin requirements",
    "RDL-003": "Data directory not found",
    "RDL-004": "Risk parameter file not found",
    "RDL-005": "Invalid risk parameter format",
}


class RiskDataLoader:
    """Centralized loader for risk parameters from data files."""

    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize risk data loader.

        Args:
            data_dir: Data directory path (defaults to BASIS_DATA_DIR env var)
        """
        self.data_dir = data_dir or os.getenv("BASIS_DATA_DIR")
        if not self.data_dir:
            raise ValueError("Data directory not specified and BASIS_DATA_DIR not set")

        self.data_dir = Path(self.data_dir)
        if not self.data_dir.exists():
            raise ValueError(f"Data directory does not exist: {self.data_dir}")

        # Cache for loaded parameters
        self._aave_params_cache = None
        self._cex_params_cache = {}

        logger.info(f"RiskDataLoader initialized with data_dir: {self.data_dir}")

    def load_aave_risk_parameters(self) -> Dict[str, Any]:
        """
        Load AAVE risk parameters from data file.

        Returns:
            Dictionary containing AAVE risk parameters
        """
        if self._aave_params_cache is not None:
            return self._aave_params_cache

        try:
            risk_params_path = (
                self.data_dir / "protocol_data/aave/risk_params/aave_v3_risk_parameters.json"
            )

            if not risk_params_path.exists():
                raise FileNotFoundError(f"AAVE risk parameters file not found: {risk_params_path}")

            with open(risk_params_path, "r") as f:
                self._aave_params_cache = json.load(f)

            logger.info(f"AAVE risk parameters loaded from {risk_params_path}")
            return self._aave_params_cache

        except Exception as e:
            logger.error(f"Failed to load AAVE risk parameters: {e}")
            raise ValueError(f"Failed to load AAVE risk parameters: {e}")

    def load_cex_margin_requirements(self, venue: str) -> Dict[str, Any]:
        """
        Load CEX margin requirements for a specific venue.

        Args:
            venue: CEX venue name (binance, bybit, okx)

        Returns:
            Dictionary containing CEX margin requirements
        """
        if venue in self._cex_params_cache:
            return self._cex_params_cache[venue]

        try:
            margin_params_path = (
                self.data_dir
                / f"market_data/derivatives/risk_params/{venue}_margin_requirements.json"
            )

            if not margin_params_path.exists():
                raise FileNotFoundError(
                    f"CEX margin requirements file not found: {margin_params_path}"
                )

            with open(margin_params_path, "r") as f:
                self._cex_params_cache[venue] = json.load(f)

            logger.info(f"CEX margin requirements loaded for {venue} from {margin_params_path}")
            return self._cex_params_cache[venue]

        except Exception as e:
            logger.error(f"Failed to load CEX margin requirements for {venue}: {e}")
            raise ValueError(f"Failed to load CEX margin requirements for {venue}: {e}")

    def get_aave_ltv_limits(
        self, mode: str = "emode", collateral_pair: str = "weETH_WETH"
    ) -> Tuple[Decimal, Decimal]:
        """
        Get AAVE LTV limits for a specific collateral pair.

        Args:
            mode: Risk mode ('emode' or 'standard')
            collateral_pair: Collateral pair (e.g., 'weETH_WETH', 'wstETH_WETH', 'ETH_WETH')

        Returns:
            Tuple of (max_ltv, liquidation_threshold)
        """
        try:
            aave_params = self.load_aave_risk_parameters()

            if mode not in aave_params:
                raise ValueError(f"Invalid AAVE mode: {mode}")

            mode_params = aave_params[mode]

            if collateral_pair not in mode_params["LTV_LIMITS"]:
                raise ValueError(
                    f"Collateral pair {collateral_pair} not found in {mode} LTV limits"
                )

            max_ltv = Decimal(str(mode_params["LTV_LIMITS"][collateral_pair]))
            liquidation_threshold = Decimal(
                str(mode_params["liquidation_thresholds"][collateral_pair])
            )

            return max_ltv, liquidation_threshold

        except Exception as e:
            logger.error(f"Failed to get AAVE LTV limits for {mode}/{collateral_pair}: {e}")
            # Return conservative fallback values
            return Decimal("0.5"), Decimal("0.6")

    def get_cex_margin_requirements(self, venue: str) -> Tuple[Decimal, Decimal, Decimal]:
        """
        Get CEX margin requirements for a specific venue.

        Args:
            venue: CEX venue name (binance, bybit, okx)

        Returns:
            Tuple of (initial_margin, maintenance_margin, liquidation_threshold)
        """
        try:
            cex_params = self.load_cex_margin_requirements(venue)

            initial_margin = Decimal(str(cex_params["initial_margin_requirement"]))
            maintenance_margin = Decimal(str(cex_params["maintenance_margin_requirement"]))
            liquidation_threshold = Decimal(str(cex_params["liquidation_threshold"]))

            return initial_margin, maintenance_margin, liquidation_threshold

        except Exception as e:
            logger.error(f"Failed to get CEX margin requirements for {venue}: {e}")
            # Return conservative fallback values
            return Decimal("0.1"), Decimal("0.15"), Decimal("0.1")

    def get_aave_liquidation_bonus(
        self, mode: str = "emode", collateral_pair: str = "weETH_WETH"
    ) -> Decimal:
        """
        Get AAVE liquidation bonus for a specific collateral pair.

        Args:
            mode: Risk mode ('emode' or 'standard')
            collateral_pair: Collateral pair

        Returns:
            Liquidation bonus as Decimal
        """
        try:
            aave_params = self.load_aave_risk_parameters()

            if mode not in aave_params:
                raise ValueError(f"Invalid AAVE mode: {mode}")

            mode_params = aave_params[mode]

            if collateral_pair not in mode_params["liquidation_bonus"]:
                raise ValueError(
                    f"Collateral pair {collateral_pair} not found in {mode} liquidation bonus"
                )

            return Decimal(str(mode_params["liquidation_bonus"][collateral_pair]))

        except Exception as e:
            logger.error(f"Failed to get AAVE liquidation bonus for {mode}/{collateral_pair}: {e}")
            # Return conservative fallback value
            return Decimal("0.05")

    def get_available_collateral_pairs(self, mode: str = "emode") -> list:
        """
        Get available collateral pairs for a specific mode.

        Args:
            mode: Risk mode ('emode' or 'standard')

        Returns:
            List of available collateral pairs
        """
        try:
            aave_params = self.load_aave_risk_parameters()

            if mode not in aave_params:
                raise ValueError(f"Invalid AAVE mode: {mode}")

            return list(aave_params[mode]["LTV_LIMITS"].keys())

        except Exception as e:
            logger.error(f"Failed to get available collateral pairs for {mode}: {e}")
            return ["weETH_WETH", "wstETH_WETH", "ETH_WETH"]  # Fallback

    def get_available_cex_venues(self) -> list:
        """
        Get available CEX venues.

        Returns:
            List of available CEX venues
        """
        try:
            risk_params_dir = self.data_dir / "market_data/derivatives/risk_params"
            if not risk_params_dir.exists():
                return []

            venues = []
            for file_path in risk_params_dir.glob("*_margin_requirements.json"):
                venue_name = file_path.stem.replace("_margin_requirements", "")
                venues.append(venue_name)

            return venues

        except Exception as e:
            logger.error(f"Failed to get available CEX venues: {e}")
            return ["binance", "bybit", "okx"]  # Fallback

    def clear_cache(self):
        """Clear all cached parameters."""
        self._aave_params_cache = None
        self._cex_params_cache = {}
        logger.info("Risk data cache cleared")
