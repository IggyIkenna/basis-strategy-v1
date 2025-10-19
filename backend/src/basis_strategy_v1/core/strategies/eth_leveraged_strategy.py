"""
ETH Leveraged Strategy Implementation

Implements ETH leveraged staking strategy with LSTs and optional hedging.
Uses unified Order/Trade system for execution.

Reference: docs/STRATEGY_MODES.md - ETH Leveraged Strategy Mode
Reference: docs/specs/05_STRATEGY_MANAGER.md - Component specification
"""

from typing import Dict, List, Any
import logging
import pandas as pd
from pathlib import Path

from .base_strategy_manager import BaseStrategyManager
from ...core.models.order import Order, OrderOperation
from ...core.models.venues import Venue
from ...core.models.instruments import validate_instrument_key, get_display_name

logger = logging.getLogger(__name__)


class ETHLeveragedStrategy(BaseStrategyManager):
    """
    ETH Leveraged Strategy - Leveraged staking with LSTs.

    Strategy Overview:
    - Stake ETH via liquid staking protocols
    - Use leverage to increase exposure
    - Target APY: 20-40%
    """

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
        Initialize ETH leveraged strategy.

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
        super().__init__(
            config,
            data_provider,
            exposure_monitor,
            position_monitor,
            risk_monitor,
            utility_manager,
            correlation_id,
            pid,
            log_dir,
        )

        # Validate required configuration at startup (fail-fast)
        required_keys = ["lst_type", "staking_protocol"]
        for key in required_keys:
            if key not in config:
                raise KeyError(f"Missing required configuration: {key}")

        # ETH leveraged-specific configuration (fail-fast access)
        self.lst_type = config["lst_type"]  # Default LST type
        self.staking_protocol = config["staking_protocol"]  # Default protocol
        self.share_class = config.get("share_class", "ETH")  # Share class currency
        self.mode = config.get("mode", "backtest")  # Execution mode

        # For leveraged staking, allocate 100% to ETH staking
        self.eth_allocation = 1.0

        # Define and validate instrument keys
        self.entry_instrument = f"{Venue.WALLET.value}:BaseToken:ETH"
        self.staking_instrument = f"{Venue.ETHERFI.value}:LST:weETH"  # Fixed: use LST not aToken
        self.lending_instrument = f"{Venue.AAVE_V3.value}:aToken:aWETH"
        self.borrow_instrument = f"{Venue.AAVE_V3.value}:debtToken:debtWETH"

        # Validate instrument keys
        validate_instrument_key(self.entry_instrument)
        validate_instrument_key(self.staking_instrument)
        validate_instrument_key(self.lending_instrument)
        validate_instrument_key(self.borrow_instrument)

        # Get available instruments from position_monitor config
        position_config = config.get("component_config", {}).get("position_monitor", {})
        self.available_instruments = position_config.get("position_subscriptions", [])

        if not self.available_instruments:
            raise ValueError(
                f"{self.__class__.__name__} requires position_subscriptions in config. "
                "Define all instruments this strategy will use in component_config.position_monitor.position_subscriptions"
            )

        # Define required instruments for this strategy
        required_instruments = [
            self.entry_instrument,
            self.staking_instrument,
            self.lending_instrument,
            self.borrow_instrument,
        ]

        # Validate all required instruments are in available set
        for instrument in required_instruments:
            if instrument not in self.available_instruments:
                raise ValueError(
                    f"Required instrument {instrument} not in position_subscriptions. "
                    f"Add to configs/modes/{config.get('mode', 'eth_leveraged')}.yaml"
                )

        logger.info(
            f"ETHLeveragedStrategy initialized with {self.eth_allocation*100}% ETH allocation, {self.lst_type}"
        )
        logger.info(f"  Available instruments: {len(self.available_instruments)}")
        logger.info(f"  Entry: {get_display_name(self.entry_instrument)}")
        logger.info(f"  Staking: {get_display_name(self.staking_instrument)}")
        logger.info(f"  Lending: {get_display_name(self.lending_instrument)}")
        logger.info(f"  Borrow: {get_display_name(self.borrow_instrument)}")

    def generate_orders(
        self,
        timestamp: pd.Timestamp,
        exposure: Dict,
        risk_assessment: Dict,
        pnl: Dict,
        market_data: Dict,
    ) -> List[Order]:
        """
        Generate orders for ETH leveraged strategy based on market conditions.

        Args:
            timestamp: Current timestamp
            exposure: Current exposure data
            risk_assessment: Risk assessment data (includes target_ltv)
            pnl: Current PnL data (deprecated)
            market_data: Current market data

        Returns:
            List of Order objects to execute
        """
        try:
            # Get target_ltv from risk_assessment
            target_ltv = risk_assessment.get("target_ltv", 0.0)

            # Log strategy decision start
            self.logger.info(f"Making ETH leveraged strategy decision with target_ltv={target_ltv}")

            # Get current equity and positions
            current_equity = exposure.get("total_exposure", 0.0)
            current_positions = exposure.get("positions", {})

            # Check if we have any position
            has_position = any(
                current_positions.get(f"{self.lst_type.lower()}_balance", 0.0) > 0
                or current_positions.get("aave_v3:aToken:aWETH", 0.0) > 0
                or current_positions.get("aave_v3:debtToken:debtWETH", 0.0) != 0
                for _ in [1]
            )

            # ETH Leveraged Strategy Decision Logic
            if current_equity > 0 and not has_position:
                # Enter full position with target_ltv
                return self._create_entry_full_orders(current_equity, target_ltv)
            elif current_equity > 0 and has_position:
                # Check for dust tokens to sell
                dust_tokens = exposure.get("dust_tokens", {})
                if dust_tokens:
                    return self._create_dust_sell_orders(dust_tokens)
                else:
                    # No action needed
                    return []
            else:
                # No equity or exit needed
                return []

        except Exception as e:
            self.log_error(
                error=e,
                context={"method": "generate_orders", "strategy_type": self.__class__.__name__},
            )
            logger.error(f"Error in ETH leveraged strategy order generation: {e}")
            return []

    def _get_asset_price(self) -> float:
        """Get current ETH price for testing."""
        # In real implementation, this would get actual price from market data
        return 3000.0  # Mock ETH price

    def calculate_target_position(
        self, current_equity: float, target_ltv: float = 0.0
    ) -> Dict[str, float]:
        """
        Calculate target position for ETH leveraged strategy using target_ltv from risk_monitor.

        Args:
            current_equity: Current equity in share class currency
            target_ltv: Target loan-to-value ratio from risk_monitor

        Returns:
            Dictionary of target positions by token/venue
        """
        try:
            # Calculate leverage from target_ltv: leverage = target_ltv / (1 - target_ltv)
            if target_ltv > 0 and target_ltv < 1:
                leverage = target_ltv / (1 - target_ltv)
            else:
                leverage = 1.0  # No leverage if target_ltv is 0 or invalid

            # Calculate target allocations
            leveraged_equity = current_equity * leverage
            eth_target = leveraged_equity * self.eth_allocation

            # Get current ETH price
            eth_price = self._get_asset_price()
            eth_amount = eth_target / eth_price if eth_price > 0 else 0

            # Calculate AAVE positions
            supply_amount = eth_amount  # LST supplied as collateral
            debt_amount = eth_amount * (leverage - 1)  # WETH borrowed

            return {
                "eth_balance": 0.0,  # No raw ETH, all staked
                f"{self.lst_type.lower()}_balance": eth_amount,  # LST staked
                "aave_v3:aToken:aWETH": supply_amount,  # LST supplied as collateral
                "aave_v3:debtToken:debtWETH": debt_amount,  # WETH borrowed
                f"{self.share_class.lower()}_balance": current_equity,
                "total_equity": current_equity,
                "leveraged_equity": leveraged_equity,
                "target_ltv": target_ltv,
                "leverage": leverage,
            }

        except Exception as e:
            logger.error(f"Error calculating target position: {e}")
            return {
                "eth_balance": 0.0,
                f"{self.lst_type.lower()}_balance": 0.0,
                "aave_v3:aToken:aWETH": 0.0,
                "aave_v3:debtToken:debtWETH": 0.0,
                f"{self.share_class.lower()}_balance": 0.0,
                "total_equity": current_equity,
                "leveraged_equity": current_equity,
                "target_ltv": 0.0,
                "leverage": 1.0,
            }

    def _create_entry_full_orders(self, equity: float, target_ltv: float) -> List[Order]:
        """
        Create entry full orders for ETH leveraged strategy using atomic flash loan.

        Args:
            equity: Available equity in share class currency
            target_ltv: Target loan-to-value ratio from risk_monitor

        Returns:
            List of Order objects for full entry
        """
        try:
            # Calculate target position with target_ltv
            target_position = self.calculate_target_position(equity, target_ltv)

            orders = []
            atomic_group_id = f"eth_leveraged_entry_{int(equity)}"

            # Calculate leverage and amounts
            leverage = target_position.get("leverage", 1.0)
            eth_amount = target_position[f"{self.lst_type.lower()}_balance"]
            supply_amount = target_position.get("aave_v3:aToken:aWETH", 0.0)
            debt_amount = target_position.get("aave_v3:debtToken:debtWETH", 0.0)

            if eth_amount > 0 and leverage > 1.0:
                # Atomic flash loan sequence:
                # 1. FLASH_BORROW WETH from Morpho (via Instadapp)
                orders.append(
                    Order(
                        operation_id=f"flash_borrow_{int(pd.Timestamp.now().timestamp() * 1000000)}",
                        venue=Venue.INSTADAPP,
                        operation=OrderOperation.FLASH_BORROW,
                        token_out="WETH",
                        amount=debt_amount,
                        source_venue=Venue.INSTADAPP,
                        target_venue=Venue.WALLET,
                        source_token="WETH",
                        target_token="WETH",
                        expected_deltas={
                            f"{Venue.INSTADAPP}:BaseToken:WETH": debt_amount,  # Gain WETH from flash loan
                            f"{Venue.WALLET}:BaseToken:WETH": debt_amount,
                        },
                        operation_details={"target_ltv": target_ltv, "leverage": leverage},
                        execution_mode="atomic",
                        atomic_group_id=atomic_group_id,
                        sequence_in_group=1,
                        strategy_intent="entry_full",
                        strategy_id="eth_leveraged",
                        metadata={"target_ltv": target_ltv, "leverage": leverage},
                    )
                )

                # 2. STAKE WETH to get LST (weETH/wstETH)
                orders.append(
                    Order(
                        operation_id=f"stake_{int(pd.Timestamp.now().timestamp() * 1000000)}",
                        venue=Venue.ETHERFI,
                        operation=OrderOperation.STAKE,
                        token_in="WETH",
                        token_out=self.lst_type,
                        amount=eth_amount,
                        source_venue="wallet",
                        target_venue=self.staking_protocol,
                        source_token="WETH",
                        target_token=self.lst_type,
                        expected_deltas={
                            f"{Venue.WALLET}:BaseToken:WETH": -eth_amount,  # Lose WETH
                            self.staking_instrument: eth_amount,  # Gain LST
                        },
                        operation_details={
                            "lst_type": self.lst_type,
                            "staking_protocol": self.staking_protocol,
                        },
                        execution_mode="atomic",
                        atomic_group_id=atomic_group_id,
                        sequence_in_group=2,
                        strategy_intent="entry_full",
                        strategy_id="eth_leveraged",
                    )
                )

                # 3. SUPPLY LST to AAVE as collateral
                orders.append(
                    Order(
                        operation_id=f"supply_{int(pd.Timestamp.now().timestamp() * 1000000)}",
                        venue=Venue.AAVE_V3,
                        operation=OrderOperation.SUPPLY,
                        token_in=self.lst_type,
                        token_out=f"a{self.lst_type}",
                        amount=supply_amount,
                        source_venue=Venue.WALLET,
                        target_venue=Venue.AAVE_V3,
                        source_token=self.lst_type,
                        target_token=f"a{self.lst_type}",
                        expected_deltas={
                            f"{Venue.WALLET}:BaseToken:{self.lst_type}": -supply_amount,  # Lose LST
                            f"{Venue.AAVE_V3}:aToken:a{self.lst_type}": supply_amount,  # Gain aToken
                        },
                        operation_details={
                            "lending_protocol": "aave_v3",
                            "COLLATERAL_TYPE": self.lst_type,
                        },
                        execution_mode="atomic",
                        atomic_group_id=atomic_group_id,
                        sequence_in_group=3,
                        strategy_intent="entry_full",
                        strategy_id="eth_leveraged",
                    )
                )

                # 4. BORROW WETH from AAVE (up to target_ltv)
                orders.append(
                    Order(
                        operation_id=f"borrow_{int(pd.Timestamp.now().timestamp() * 1000000)}",
                        venue=Venue.AAVE_V3,
                        operation=OrderOperation.BORROW,
                        token_out="WETH",
                        amount=debt_amount,
                        source_venue=Venue.AAVE_V3,
                        target_venue=Venue.WALLET,
                        source_token="WETH",
                        target_token="WETH",
                        expected_deltas={
                            self.borrow_instrument: debt_amount,  # Gain debt
                            f"{Venue.WALLET}:BaseToken:WETH": debt_amount,  # Gain WETH
                        },
                        operation_details={"lending_protocol": "aave_v3", "borrow_asset": "WETH"},
                        execution_mode="atomic",
                        atomic_group_id=atomic_group_id,
                        sequence_in_group=4,
                        strategy_intent="entry_full",
                        strategy_id="eth_leveraged",
                    )
                )

                # 5. FLASH_REPAY WETH to Morpho
                orders.append(
                    Order(
                        operation_id=f"flash_repay_{int(pd.Timestamp.now().timestamp() * 1000000)}",
                        venue=Venue.INSTADAPP,
                        operation=OrderOperation.FLASH_REPAY,
                        token_in="WETH",
                        amount=debt_amount,
                        source_venue=Venue.WALLET,
                        target_venue=Venue.INSTADAPP,
                        source_token="WETH",
                        target_token="WETH",
                        expected_deltas={
                            f"{Venue.WALLET}:BaseToken:WETH": -debt_amount,  # Lose WETH
                            f"{Venue.INSTADAPP}:BaseToken:WETH": -debt_amount,  # Repay flash loan
                        },
                        operation_details={
                            "flash_loan_protocol": "instadapp",
                            "REPAY_ASSET": "WETH",
                        },
                        execution_mode="atomic",
                        atomic_group_id=atomic_group_id,
                        sequence_in_group=5,
                        strategy_intent="entry_full",
                        strategy_id="eth_leveraged",
                    )
                )
            else:
                # No leverage needed - simple staking only
                orders.append(
                    Order(
                        operation_id=f"stake_{int(pd.Timestamp.now().timestamp() * 1000000)}",
                        venue=Venue.ETHERFI,
                        operation=OrderOperation.STAKE,
                        token_in="WETH",
                        token_out=self.lst_type,
                        amount=eth_amount,
                        source_venue="wallet",
                        target_venue=self.staking_protocol,
                        source_token="WETH",
                        target_token=self.lst_type,
                        expected_deltas={
                            f"{Venue.WALLET}:BaseToken:WETH": -eth_amount,  # Lose WETH
                            self.staking_instrument: eth_amount,  # Gain LST
                        },
                        operation_details={
                            "lst_type": self.lst_type,
                            "staking_protocol": self.staking_protocol,
                        },
                        execution_mode="sequential",
                        strategy_intent="entry_full",
                        strategy_id="eth_leveraged",
                    )
                )

            return orders

        except Exception as e:
            logger.error(f"Error creating entry full orders: {e}")
            return []

    def _create_entry_partial_orders(self, equity_delta: float, target_ltv: float) -> List[Order]:
        """
        Create entry partial orders for ETH leveraged strategy.

        Args:
            equity_delta: Additional equity to deploy
            target_ltv: Target loan-to-value ratio from risk_monitor

        Returns:
            List of Order objects for partial entry
        """
        try:
            # Calculate target position for additional equity
            target_position = self.calculate_target_position(equity_delta, target_ltv)

            orders = []
            atomic_group_id = f"eth_leveraged_partial_{int(equity_delta)}"

            # Calculate amounts
            leverage = target_position.get("leverage", 1.0)
            eth_amount = target_position[f"{self.lst_type.lower()}_balance"]
            supply_amount = target_position.get("aave_v3:aToken:aWETH", 0.0)
            debt_amount = target_position.get("aave_v3:debtToken:debtWETH", 0.0)

            if eth_amount > 0 and leverage > 1.0:
                # Use same atomic flash loan sequence as full entry
                # 1. FLASH_BORROW WETH
                orders.append(
                    Order(
                        operation_id=f"flash_borrow_{int(pd.Timestamp.now().timestamp() * 1000000)}",
                        venue=Venue.INSTADAPP,
                        operation=OrderOperation.FLASH_BORROW,
                        token_out="WETH",
                        amount=debt_amount,
                        source_venue="instadapp",
                        target_venue="wallet",
                        source_token="WETH",
                        target_token="WETH",
                        expected_deltas={
                            f"{Venue.INSTADAPP}:BaseToken:WETH": debt_amount,  # Gain WETH from flash loan
                            f"{Venue.WALLET}:BaseToken:WETH": debt_amount,
                        },
                        operation_details={"target_ltv": target_ltv, "leverage": leverage},
                        execution_mode="atomic",
                        atomic_group_id=atomic_group_id,
                        sequence_in_group=1,
                        strategy_intent="entry_partial",
                        strategy_id="eth_leveraged",
                        metadata={"target_ltv": target_ltv, "leverage": leverage},
                    )
                )

                # 2. STAKE WETH to get LST
                orders.append(
                    Order(
                        operation_id=f"stake_{int(pd.Timestamp.now().timestamp() * 1000000)}",
                        venue=Venue.ETHERFI,
                        operation=OrderOperation.STAKE,
                        token_in="WETH",
                        token_out=self.lst_type,
                        amount=eth_amount,
                        source_venue="wallet",
                        target_venue=self.staking_protocol,
                        source_token="WETH",
                        target_token=self.lst_type,
                        expected_deltas={
                            f"{Venue.WALLET}:BaseToken:WETH": -eth_amount,  # Lose WETH
                            self.staking_instrument: eth_amount,  # Gain LST
                        },
                        operation_details={
                            "lst_type": self.lst_type,
                            "staking_protocol": self.staking_protocol,
                        },
                        execution_mode="atomic",
                        atomic_group_id=atomic_group_id,
                        sequence_in_group=2,
                        strategy_intent="entry_partial",
                        strategy_id="eth_leveraged",
                    )
                )

                # 3. SUPPLY LST to AAVE
                orders.append(
                    Order(
                        operation_id=f"supply_{int(pd.Timestamp.now().timestamp() * 1000000)}",
                        venue=Venue.AAVE_V3,
                        operation=OrderOperation.SUPPLY,
                        token_in=self.lst_type,
                        token_out=f"a{self.lst_type}",
                        amount=supply_amount,
                        source_venue=Venue.WALLET,
                        target_venue=Venue.AAVE_V3,
                        source_token=self.lst_type,
                        target_token=f"a{self.lst_type}",
                        expected_deltas={
                            f"{Venue.WALLET}:BaseToken:{self.lst_type}": -supply_amount,  # Lose LST
                            f"{Venue.AAVE_V3}:aToken:a{self.lst_type}": supply_amount,  # Gain aToken
                        },
                        operation_details={
                            "lending_protocol": "aave_v3",
                            "COLLATERAL_TYPE": self.lst_type,
                        },
                        execution_mode="atomic",
                        atomic_group_id=atomic_group_id,
                        sequence_in_group=3,
                        strategy_intent="entry_partial",
                        strategy_id="eth_leveraged",
                    )
                )

                # 4. BORROW WETH from AAVE
                orders.append(
                    Order(
                        operation_id=f"borrow_{int(pd.Timestamp.now().timestamp() * 1000000)}",
                        venue=Venue.AAVE_V3,
                        operation=OrderOperation.BORROW,
                        token_out="WETH",
                        amount=debt_amount,
                        source_venue=Venue.AAVE_V3,
                        target_venue=Venue.WALLET,
                        source_token="WETH",
                        target_token="WETH",
                        expected_deltas={
                            self.borrow_instrument: debt_amount,  # Gain debt
                            f"{Venue.WALLET}:BaseToken:WETH": debt_amount,  # Gain WETH
                        },
                        operation_details={"lending_protocol": "aave_v3", "borrow_asset": "WETH"},
                        execution_mode="atomic",
                        atomic_group_id=atomic_group_id,
                        sequence_in_group=4,
                        strategy_intent="entry_partial",
                        strategy_id="eth_leveraged",
                    )
                )

                # 5. FLASH_REPAY WETH
                orders.append(
                    Order(
                        operation_id=f"flash_repay_{int(pd.Timestamp.now().timestamp() * 1000000)}",
                        venue=Venue.INSTADAPP,
                        operation=OrderOperation.FLASH_REPAY,
                        token_in="WETH",
                        amount=debt_amount,
                        source_venue=Venue.WALLET,
                        target_venue=Venue.INSTADAPP,
                        source_token="WETH",
                        target_token="WETH",
                        expected_deltas={
                            f"{Venue.WALLET}:BaseToken:WETH": -debt_amount,  # Lose WETH
                            f"{Venue.INSTADAPP}:BaseToken:WETH": -debt_amount,  # Repay flash loan
                        },
                        operation_details={
                            "flash_loan_protocol": "instadapp",
                            "REPAY_ASSET": "WETH",
                        },
                        execution_mode="atomic",
                        atomic_group_id=atomic_group_id,
                        sequence_in_group=5,
                        strategy_intent="entry_partial",
                        strategy_id="eth_leveraged",
                    )
                )
            else:
                # Simple staking for additional equity
                orders.append(
                    Order(
                        operation_id=f"stake_{int(pd.Timestamp.now().timestamp() * 1000000)}",
                        venue=Venue.ETHERFI,
                        operation=OrderOperation.STAKE,
                        token_in="WETH",
                        token_out=self.lst_type,
                        amount=eth_amount,
                        source_venue="wallet",
                        target_venue=self.staking_protocol,
                        source_token="WETH",
                        target_token=self.lst_type,
                        expected_deltas={
                            f"{Venue.WALLET}:BaseToken:WETH": -eth_amount,  # Lose WETH
                            self.staking_instrument: eth_amount,  # Gain LST
                        },
                        operation_details={
                            "lst_type": self.lst_type,
                            "staking_protocol": self.staking_protocol,
                        },
                        execution_mode="sequential",
                        strategy_intent="entry_partial",
                        strategy_id="eth_leveraged",
                    )
                )

            return orders

        except Exception as e:
            logger.error(f"Error creating entry partial orders: {e}")
            return []

    def _create_exit_full_orders(self, equity: float) -> List[Order]:
        """
        Create exit full orders for ETH leveraged strategy.

        Args:
            equity: Total equity to exit

        Returns:
            List of Order objects for full exit
        """
        try:
            # Get current position
            current_position = self.position_monitor.get_current_position()
            lst_balance = current_position.get(f"{self.lst_type.lower()}_balance", 0.0)
            aave_supply = current_position.get("aave_v3:aToken:aWETH", 0.0)
            aave_debt = current_position.get("aave_v3:debtToken:debtWETH", 0.0)

            orders = []
            atomic_group_id = f"eth_leveraged_exit_{int(equity)}"

            # 1. Repay AAVE debt (atomic group)
            if aave_debt > 0:
                orders.append(
                    Order(
                        operation_id=f"repay_{int(pd.Timestamp.now().timestamp() * 1000000)}",
                        venue=Venue.AAVE_V3,
                        operation=OrderOperation.REPAY,
                        token_in="WETH",
                        amount=aave_debt,
                        source_venue=Venue.WALLET,
                        target_venue=Venue.AAVE_V3,
                        source_token="WETH",
                        target_token="WETH",
                        expected_deltas={
                            f"{Venue.WALLET}:BaseToken:WETH": -aave_debt,  # Lose WETH
                            "aave_v3:debtToken:debtWETH": -aave_debt,  # Reduce debt
                        },
                        operation_details={"lending_protocol": "aave_v3", "repay_asset": "WETH"},
                        execution_mode="atomic",
                        atomic_group_id=atomic_group_id,
                        sequence_in_group=1,
                        strategy_intent="exit_full",
                        strategy_id="eth_leveraged",
                    )
                )

            # 2. Withdraw LST from AAVE (atomic group)
            if aave_supply > 0:
                orders.append(
                    Order(
                        operation_id=f"withdraw_{int(pd.Timestamp.now().timestamp() * 1000000)}",
                        venue=Venue.AAVE_V3,
                        operation=OrderOperation.WITHDRAW,
                        token_out=self.lst_type,
                        amount=aave_supply,
                        source_venue=Venue.AAVE_V3,
                        target_venue=Venue.WALLET,
                        source_token=f"a{self.lst_type}",
                        target_token=self.lst_type,
                        expected_deltas={
                            f"aave_v3:aToken:a{self.lst_type}": -aave_supply,  # Lose aToken
                            f"{Venue.WALLET}:BaseToken:{self.lst_type}": aave_supply,  # Gain LST
                        },
                        operation_details={
                            "lending_protocol": "aave_v3",
                            "WITHDRAW_ASSET": self.lst_type,
                        },
                        execution_mode="atomic",
                        atomic_group_id=atomic_group_id,
                        sequence_in_group=2,
                        strategy_intent="exit_full",
                        strategy_id="eth_leveraged",
                    )
                )

            # 3. Unstake LST to get WETH (atomic group)
            total_lst = lst_balance + aave_supply
            if total_lst > 0:
                orders.append(
                    Order(
                        operation_id=f"unstake_{int(pd.Timestamp.now().timestamp() * 1000000)}",
                        venue=Venue.ETHERFI,
                        operation=OrderOperation.UNSTAKE,
                        token_in=self.lst_type,
                        token_out="WETH",
                        amount=total_lst,
                        source_venue=self.staking_protocol,
                        target_venue="wallet",
                        source_token=self.lst_type,
                        target_token="WETH",
                        expected_deltas={
                            f"{self.staking_protocol}:aToken:{self.lst_type}": -total_lst,  # Lose LST
                            f"{Venue.WALLET}:BaseToken:WETH": total_lst,  # Gain WETH
                        },
                        operation_details={
                            "lst_type": self.lst_type,
                            "staking_protocol": self.staking_protocol,
                        },
                        execution_mode="atomic",
                        atomic_group_id=atomic_group_id,
                        sequence_in_group=3,
                        strategy_intent="exit_full",
                        strategy_id="eth_leveraged",
                    )
                )

            # 4. Convert WETH to share class currency (sequential)
            orders.append(
                Order(
                    operation_id=f"transfer_{int(pd.Timestamp.now().timestamp() * 1000000)}",
                    venue="wallet",
                    operation=OrderOperation.TRANSFER,
                    source_venue="wallet",
                    target_venue="wallet",
                    source_token="WETH",
                    target_token=self.share_class,
                    token=self.share_class,
                    amount=equity,
                    expected_deltas={
                        f"{Venue.WALLET}:BaseToken:WETH": -equity,  # Lose WETH
                        f"{Venue.WALLET}:BaseToken:{self.share_class}": equity,  # Gain share class (simplified 1:1)
                    },
                    operation_details={
                        "conversion_type": "exit_conversion",
                        "FROM_ASSET": "WETH",
                        "to_asset": self.share_class,
                    },
                    execution_mode="sequential",
                    strategy_intent="exit_full",
                    strategy_id="eth_leveraged",
                )
            )

            return orders

        except Exception as e:
            logger.error(f"Error creating exit full orders: {e}")
            return []

    def _create_exit_partial_orders(self, equity_delta: float) -> List[Order]:
        """
        Create exit partial orders for ETH leveraged strategy.

        Args:
            equity_delta: Equity to remove from position

        Returns:
            List of Order objects for partial exit
        """
        try:
            # Get current position
            current_position = self.position_monitor.get_current_position()
            lst_balance = current_position.get(f"{self.lst_type.lower()}_balance", 0.0)
            aave_supply = current_position.get("aave_v3:aToken:aWETH", 0.0)
            aave_debt = current_position.get("aave_v3:debtToken:debtWETH", 0.0)

            # Calculate proportional reduction
            total_lst = lst_balance + aave_supply
            if total_lst > 0:
                reduction_ratio = min(equity_delta / (total_lst * self._get_asset_price()), 1.0)
            else:
                reduction_ratio = 0.0

            lst_reduction = lst_balance * reduction_ratio
            aave_supply_reduction = aave_supply * reduction_ratio
            aave_debt_reduction = aave_debt * reduction_ratio

            orders = []
            atomic_group_id = f"eth_leveraged_partial_exit_{int(equity_delta)}"

            # 1. Repay proportional AAVE debt (atomic group)
            if aave_debt_reduction > 0:
                orders.append(
                    Order(
                        operation_id=f"repay_{int(pd.Timestamp.now().timestamp() * 1000000)}",
                        venue=Venue.AAVE_V3,
                        operation=OrderOperation.REPAY,
                        token_in="WETH",
                        amount=aave_debt_reduction,
                        source_venue="wallet",
                        target_venue=Venue.AAVE_V3,
                        source_token="WETH",
                        target_token="debtWETH",
                        expected_deltas={"aave_v3:debtToken:debtWETH": -aave_debt_reduction},
                        execution_mode="atomic",
                        atomic_group_id=atomic_group_id,
                        sequence_in_group=1,
                        strategy_intent="exit_partial",
                        strategy_id="eth_leveraged",
                    )
                )

            # 2. Withdraw proportional LST from AAVE (atomic group)
            if aave_supply_reduction > 0:
                orders.append(
                    Order(
                        operation_id=f"withdraw_{int(pd.Timestamp.now().timestamp() * 1000000)}",
                        venue=Venue.AAVE_V3,
                        operation=OrderOperation.WITHDRAW,
                        token_out=self.lst_type,
                        amount=aave_supply_reduction,
                        source_venue=Venue.AAVE_V3,
                        target_venue="wallet",
                        source_token=f"a{self.lst_type}",
                        target_token=self.lst_type,
                        expected_deltas={
                            f"aave_v3:aToken:a{self.lst_type}": -aave_supply_reduction
                        },
                        execution_mode="atomic",
                        atomic_group_id=atomic_group_id,
                        sequence_in_group=2,
                        strategy_intent="exit_partial",
                        strategy_id="eth_leveraged",
                    )
                )

            # 3. Unstake proportional LST (atomic group)
            total_lst_reduction = lst_reduction + aave_supply_reduction
            if total_lst_reduction > 0:
                orders.append(
                    Order(
                        operation_id=f"unstake_{int(pd.Timestamp.now().timestamp() * 1000000)}",
                        venue=Venue.ETHERFI,
                        operation=OrderOperation.UNSTAKE,
                        token_in=self.lst_type,
                        token_out="WETH",
                        amount=total_lst_reduction,
                        source_venue=Venue.ETHERFI,
                        target_venue="wallet",
                        source_token=self.lst_type,
                        target_token="WETH",
                        expected_deltas={
                            f"{self.lst_type.lower()}_balance": -total_lst_reduction,
                            "weth_balance": total_lst_reduction,
                        },
                        execution_mode="atomic",
                        atomic_group_id=atomic_group_id,
                        sequence_in_group=3,
                        strategy_intent="exit_partial",
                        strategy_id="eth_leveraged",
                    )
                )

            # 4. Convert to share class currency (sequential)
            orders.append(
                Order(
                    operation_id=f"transfer_{int(pd.Timestamp.now().timestamp() * 1000000)}",
                    venue="wallet",
                    operation=OrderOperation.TRANSFER,
                    source_venue="wallet",
                    target_venue="wallet",
                    token=self.share_class,
                    source_token="WETH",
                    target_token=self.share_class,
                    amount=equity_delta,
                    expected_deltas={
                        "weth_balance": -equity_delta,
                        f"{self.share_class.lower()}_balance": equity_delta,
                    },
                    execution_mode="sequential",
                    strategy_intent="exit_partial",
                    strategy_id="eth_leveraged",
                )
            )

            return orders

        except Exception as e:
            logger.error(f"Error creating exit partial orders: {e}")
            return []

    def _create_dust_sell_orders(self, dust_tokens: Dict[str, float]) -> List[Order]:
        """
        Create dust sell orders for ETH leveraged strategy.

        Args:
            dust_tokens: Dictionary of dust tokens and amounts

        Returns:
            List of Order objects for dust selling
        """
        try:
            orders = []

            for token, amount in dust_tokens.items():
                if amount > 0 and token != self.share_class:
                    # Convert to share class currency
                    if token == "WETH":
                        # Convert WETH to share class
                        orders.append(
                            Order(
                                operation_id=f"dust_transfer_{int(pd.Timestamp.now().timestamp() * 1000000)}",
                                venue="wallet",
                                operation=OrderOperation.TRANSFER,
                                source_venue="wallet",
                                target_venue="wallet",
                                source_token=token,
                                target_token=self.share_class,
                                token=token,
                                amount=amount,
                                expected_deltas={
                                    f"{Venue.WALLET}:BaseToken:{token}": -amount,  # Lose dust token
                                    f"{Venue.WALLET}:BaseToken:{self.share_class}": amount,  # Gain share class (simplified 1:1)
                                },
                                operation_details={
                                    "conversion_type": "dust_cleanup",
                                    "FROM_ASSET": token,
                                    "to_asset": self.share_class,
                                },
                                execution_mode="sequential",
                                strategy_intent="sell_dust",
                                strategy_id="eth_leveraged",
                            )
                        )

                    elif token == self.lst_type:
                        # Unstake LST first, then convert WETH (atomic group)
                        atomic_group_id = f"dust_unstake_{token}_{int(amount)}"
                        orders.append(
                            Order(
                                operation_id=f"dust_unstake_{int(pd.Timestamp.now().timestamp() * 1000000)}",
                                venue=Venue.ETHERFI,
                                operation=OrderOperation.UNSTAKE,
                                token_in=token,
                                token_out="WETH",
                                amount=amount,
                                source_venue=self.staking_protocol,
                                target_venue="wallet",
                                source_token=token,
                                target_token="WETH",
                                expected_deltas={
                                    f"{self.staking_protocol}:aToken:{token}": -amount,  # Lose LST
                                    f"{Venue.WALLET}:BaseToken:WETH": amount,  # Gain WETH
                                },
                                operation_details={
                                    "lst_type": token,
                                    "staking_protocol": self.staking_protocol,
                                },
                                execution_mode="atomic",
                                atomic_group_id=atomic_group_id,
                                sequence_in_group=1,
                                strategy_intent="sell_dust",
                                strategy_id="eth_leveraged",
                            )
                        )
                        orders.append(
                            Order(
                                operation_id=f"dust_transfer_{int(pd.Timestamp.now().timestamp() * 1000000)}",
                                venue="wallet",
                                operation=OrderOperation.TRANSFER,
                                source_venue="wallet",
                                target_venue="wallet",
                                source_token="WETH",
                                target_token=self.share_class,
                                token="WETH",
                                amount=amount,
                                expected_deltas={
                                    f"{Venue.WALLET}:BaseToken:WETH": -amount,  # Lose WETH
                                    f"{Venue.WALLET}:BaseToken:{self.share_class}": amount,  # Gain share class (simplified 1:1)
                                },
                                operation_details={
                                    "conversion_type": "dust_cleanup",
                                    "FROM_ASSET": "WETH",
                                    "to_asset": self.share_class,
                                },
                                execution_mode="atomic",
                                atomic_group_id=atomic_group_id,
                                sequence_in_group=2,
                                strategy_intent="sell_dust",
                                strategy_id="eth_leveraged",
                            )
                        )

                    elif token in ["EIGEN", "ETHFI", "KING"]:
                        # Dust tokens from staking rewards - swap via Uniswap
                        orders.append(
                            Order(
                                operation_id=f"dust_swap_{int(pd.Timestamp.now().timestamp() * 1000000)}",
                                venue=Venue.UNISWAP,
                                operation=OrderOperation.SWAP,
                                token_in=token,
                                token_out="ETH",
                                amount=amount,
                                source_venue="wallet",
                                target_venue="wallet",
                                source_token=token,
                                target_token="ETH",
                                expected_deltas={
                                    f"{Venue.WALLET}:BaseToken:{token}": -amount,  # Lose dust token
                                    f"{Venue.WALLET}:BaseToken:ETH": amount,  # Gain ETH
                                },
                                operation_details={
                                    "conversion_type": "dust_cleanup",
                                    "FROM_ASSET": token,
                                    "to_asset": "ETH",
                                },
                                execution_mode="sequential",
                                strategy_intent="dust_sell",
                                strategy_id="eth_leveraged",
                            )
                        )

                    else:
                        # Other tokens - convert to share class
                        orders.append(
                            Order(
                                operation_id=f"dust_transfer_{int(pd.Timestamp.now().timestamp() * 1000000)}",
                                venue="wallet",
                                operation=OrderOperation.TRANSFER,
                                source_venue="wallet",
                                target_venue="wallet",
                                source_token=token,
                                target_token=self.share_class,
                                token=token,
                                amount=amount,
                                expected_deltas={
                                    f"{Venue.WALLET}:BaseToken:{token}": -amount,  # Lose dust token
                                    f"{Venue.WALLET}:BaseToken:{self.share_class}": amount,  # Gain share class (simplified 1:1)
                                },
                                operation_details={
                                    "conversion_type": "dust_cleanup",
                                    "FROM_ASSET": token,
                                    "to_asset": self.share_class,
                                },
                                execution_mode="sequential",
                                strategy_intent="sell_dust",
                                strategy_id="eth_leveraged",
                            )
                        )

            return orders

        except Exception as e:
            logger.error(f"Error creating dust sell orders: {e}")
            return []

    def get_strategy_info(self) -> Dict[str, Any]:
        """
        Get ETH leveraged strategy information and status.

        Returns:
            Dictionary with strategy information
        """
        try:
            base_info = super().get_strategy_info()

            # Add ETH leveraged-specific information
            base_info.update(
                {
                    "strategy_type": "eth_leveraged",
                    "eth_allocation": self.eth_allocation,
                    "lst_type": self.lst_type,
                    "staking_protocol": self.staking_protocol,
                    "description": "ETH leveraged staking with LST tokens using atomic flash loan leverage via unified_order_trade system",
                    "order_system": "unified_order_trade",
                    "leverage_mechanism": "atomic_flash_loan",
                    "target_ltv_source": "risk_monitor",
                }
            )

            return base_info

        except Exception as e:
            logger.error(f"Error getting strategy info: {e}")
            return {
                "strategy_type": "eth_leveraged",
                "mode": self.mode,
                "share_class": self.share_class,
                "asset": self.delta_tracking_asset,
                "equity": 0.0,
                "error": str(e),
            }
