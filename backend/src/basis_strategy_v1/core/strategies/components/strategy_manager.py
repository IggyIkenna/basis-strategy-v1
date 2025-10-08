"""
Strategy Manager Component

Mode-specific orchestration and rebalancing decisions.

Key Principles:
- Unified interface: Same methods for all position changes (initial, rebalancing, deposits, withdrawals)
- Mode-specific logic: Desired position different per mode (if/else on mode)
- Actual vs Desired: Compare current exposure to target, generate instructions to close gap
- Instruction generation: Creates tasks for execution managers

Handles:
- Initial position setup (t=0)
- Deposits/withdrawals (user adds/removes capital)
- Rebalancing (risk-triggered)
- Unwinding (exit strategy)
"""

import pandas as pd
import numpy as np
import logging
import json
from typing import Dict, List, Optional, Any, Union
import redis
import asyncio
from datetime import datetime, timezone
from pathlib import Path

# Import new instruction system
from ...instructions import (
    WalletTransferInstruction,
    CEXTradeInstruction,
    SmartContractInstruction,
    InstructionBlock,
    InstructionGenerator,
    ExecutionMode
)
from ...execution import WalletTransferExecutor

logger = logging.getLogger(__name__)

# Create dedicated strategy manager logger
strategy_logger = logging.getLogger('strategy_manager')
strategy_logger.setLevel(logging.INFO)

# Create logs directory if it doesn't exist
logs_dir = Path(__file__).parent.parent.parent.parent.parent.parent / 'logs'
logs_dir.mkdir(exist_ok=True)

# Create file handler for strategy manager logs
strategy_handler = logging.FileHandler(logs_dir / 'strategy_manager.log')
strategy_handler.setLevel(logging.INFO)

# Create formatter
strategy_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
strategy_handler.setFormatter(strategy_formatter)

# Add handler to logger if not already added
if not strategy_logger.handlers:
    strategy_logger.addHandler(strategy_handler)
    strategy_logger.propagate = False

# Error codes for Strategy Manager
ERROR_CODES = {
    'STRAT-001': 'Strategy mode detection failed',
    'STRAT-002': 'Invalid strategy mode configuration',
    'STRAT-003': 'Desired position calculation failed',
    'STRAT-004': 'Strategy decision generation failed',
    'STRAT-005': 'Component orchestration failed',
    'STRAT-006': 'Position change handling failed',
    'STRAT-007': 'Instruction generation failed',
    'STRAT-008': 'Rebalancing check failed',
    'STRAT-009': 'KING token management failed',
    'STRAT-010': 'Redis communication failed',
    # BTC Basis specific error codes
    'STRAT-BTC-001': 'BTC basis initial setup failed',
    'STRAT-BTC-002': 'BTC basis rebalancing failed', 
    'STRAT-BTC-003': 'BTC hedge allocation calculation failed',
    'STRAT-BTC-004': 'BTC delta neutrality check failed',
    'STRAT-BTC-005': 'BTC funding rate lookup failed (no fallbacks allowed)',
    'STRAT-BTC-006': 'BTC venue-specific price lookup failed'
}


class StrategyManager:
    """Enhanced strategy manager with mode detection and component orchestration."""

    def __init__(self, config: Dict, exposure_monitor=None, risk_monitor=None):
        self.config = config
        self.exposure_monitor = exposure_monitor
        self.risk_monitor = risk_monitor

        # Detect strategy mode from config
        self.mode = self.detect_strategy_mode()

        # Initial capital (for delta calculations)
        self.initial_capital = config.get(
            'backtest', {}).get(
            'initial_capital', 100000.0)
        
        # Get config values from top level (not strategy section)
        self.share_class = config.get('share_class', 'USDT')
        self.asset = config.get('asset', 'ETH')
        self.lst_type = config.get('lst_type', 'weeth')
        
        logger.info(f"Strategy Manager: share_class = {self.share_class}, asset = {self.asset}")

        # Redis (optional for testing)
        try:
            self.redis = redis.Redis()
            self.pubsub = self.redis.pubsub()
            self.pubsub.subscribe('risk:calculated')
        except redis.exceptions.ConnectionError:
            # Redis not available (e.g., in tests)
            self.redis = None
            self.pubsub = None

        # Thresholds
        self.margin_warning_threshold = config.get(
            'strategy', {}).get(
            'margin_warning_threshold', 0.20)
        self.delta_warning_threshold = config.get(
            'strategy', {}).get(
            'delta_warning_threshold', 0.05)
        self.ltv_warning_threshold = config.get(
            'strategy', {}).get(
            'ltv_warning_threshold', 0.88)

        logger.info(f"StrategyManager initialized for mode: {self.mode}")

    def detect_strategy_mode(self) -> str:
        """
        Determine strategy mode from config.

        Returns:
            Strategy mode: 'pure_lending', 'btc_basis', 'eth_leveraged', 'usdt_market_neutral'
        """
        strategy_config = self.config.get('strategy', {})
        
        logger.info(f"Strategy Manager: self.config keys = {list(self.config.keys())}")
        logger.info(f"Strategy Manager: strategy_config keys = {list(strategy_config.keys())}")
        logger.info(f"Strategy Manager: top-level mode = {self.config.get('mode')}")
        logger.info(f"Strategy Manager: strategy.mode = {strategy_config.get('mode')}")

        # Check explicit mode setting (try both top-level and strategy-level)
        if 'mode' in self.config:
            logger.info(f"Strategy Manager: Using top-level mode = {self.config['mode']}")
            return self.config['mode']
        elif 'mode' in strategy_config:
            logger.info(f"Strategy Manager: Using strategy.mode = {strategy_config['mode']}")
            return strategy_config['mode']

        # Auto-detect based on configuration (check top level first, then strategy section)
        share_class = self.config.get('share_class', strategy_config.get('share_class', 'USDT'))
        lending_enabled = self.config.get('lending_enabled', strategy_config.get('lending_enabled', False))
        staking_enabled = self.config.get('staking_enabled', strategy_config.get('staking_enabled', True))
        basis_trade_enabled = self.config.get('basis_trade_enabled', strategy_config.get('basis_trade_enabled', True))
        staking_leverage_enabled = strategy_config.get(
            'staking_leverage_enabled', False)
        restaking_enabled = strategy_config.get('restaking_enabled', False)

        # Pure lending: Only lending, no staking, no basis trading
        if lending_enabled and not staking_enabled and not basis_trade_enabled:
            return 'pure_lending'

        # BTC basis: Basis trading with BTC asset
        if basis_trade_enabled and strategy_config.get(
                'coin_symbol', 'ETH') == 'BTC':
            return 'btc_basis'

        # ETH leveraged: Staking with leverage, ETH share class
        if staking_enabled and staking_leverage_enabled and share_class == 'ETH':
            return 'eth_leveraged'

        # USDT market neutral: Default for USDT share class with staking and
        # basis trading
        if share_class == 'USDT' and staking_enabled and basis_trade_enabled:
            return 'usdt_market_neutral'

        # Default fallback
        logger.warning(
            "Could not auto-detect strategy mode, defaulting to usdt_market_neutral")
        return 'usdt_market_neutral'

    def calculate_desired_positions(self, current_exposure: Dict) -> Dict:
        """
        Calculate target positions based on mode.

        Args:
            current_exposure: Current exposure from exposure monitor

        Returns:
            Dictionary with desired positions
        """
        return self._get_desired_position('REBALANCE', {}, current_exposure)

    def make_strategy_decision(
            self,
            current_exposure: Dict,
            risk_assessment: Dict,
            config: Dict,
            market_data: Dict) -> Dict:
        """
        Make strategy decisions based on market conditions.

        Args:
            current_exposure: Current exposure data from ExposureMonitor
            risk_assessment: Risk assessment from RiskMonitor
            config: Configuration dictionary
            market_data: Current market data

        Returns:
            Strategy decision with actions to take
        """
        # Use the exposure data passed from the event engine
        # Don't recalculate - the event engine already calculated it properly
        # current_exposure parameter contains the correct data

        # Get current risk metrics
        if self.risk_monitor:
            risk_metrics = self.risk_monitor.get_risk_summary()
        else:
            risk_metrics = {}

        # Make decision based on mode and market conditions
        decision = {
            'mode': self.mode,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'market_data': market_data,
            'current_exposure': current_exposure,
            'risk_metrics': risk_metrics,
            'action': 'HOLD'  # Default action
        }

        # Mode-specific decision logic
        logger.info(f"Strategy Manager: self.mode = '{self.mode}', checking if == 'pure_lending'")
        if self.mode == 'pure_lending':
            # For pure lending, only supply to AAVE if we have free USDT (not already in aUSDT)
            exposures = current_exposure.get('exposures', {})
            usdt_balance = exposures.get('USDT', {}).get('balance', 0)
            ausdt_balance = exposures.get('aUSDT', {}).get('balance', 0)
            
            logger.info(f"Strategy Manager (pure_lending): USDT balance = {usdt_balance}, aUSDT balance = {ausdt_balance}")
            
            # Only supply if we have free USDT and haven't already supplied to AAVE
            if usdt_balance > 1000 and ausdt_balance == 0:  # Only supply once, when we have USDT and no aUSDT yet
                decision['action'] = 'AAVE_SUPPLY'
                decision['asset'] = 'USDT'
                decision['amount'] = usdt_balance
                logger.info(f"Strategy Manager: Making AAVE_SUPPLY decision for {usdt_balance} USDT (first time)")
            else:
                decision['action'] = 'HOLD'
                logger.info(f"Strategy Manager: Making HOLD decision (already supplied to AAVE or no USDT)")
        elif self.mode == 'btc_basis':
            action = self._btc_basis_decision(market_data, current_exposure)
            decision['action'] = action
            
            # If action requires execution, get desired positions
            if action in ['INITIAL_SETUP', 'REBALANCE']:
                params = {
                    'market_data': market_data,
                    'current_exposure': current_exposure
                }
                decision['desired_positions'] = self._desired_btc_basis(
                    action, params, current_exposure)
        elif self.mode == 'eth_leveraged':
            decision['action'] = self._eth_leveraged_decision(
                market_data, current_exposure, risk_metrics)
        elif self.mode == 'usdt_market_neutral':
            logger.info(f"Strategy Manager: Entering usdt_market_neutral branch")
            decision['action'] = self._usdt_market_neutral_decision(
                market_data, current_exposure, risk_metrics)
        else:
            logger.info(f"Strategy Manager: No matching mode branch for '{self.mode}', using default action")

        logger.info(f"Strategy Manager: Final decision action = {decision.get('action')}")
        return decision

    def orchestrate_components(self) -> Dict:
        """
        Coordinate with other components.

        Returns:
            Orchestration result with component status
        """
        result = {
            'mode': self.mode,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'components': {}
        }

        # Check component availability
        if self.exposure_monitor:
            result['components']['exposure_monitor'] = 'available'
        else:
            result['components']['exposure_monitor'] = 'unavailable'

        if self.risk_monitor:
            result['components']['risk_monitor'] = 'available'
        else:
            result['components']['risk_monitor'] = 'unavailable'

        # Redis connectivity
        if self.redis:
            try:
                self.redis.ping()
                result['components']['redis'] = 'connected'
            except BaseException:
                result['components']['redis'] = 'disconnected'
        else:
            result['components']['redis'] = 'unavailable'

        return result

    def _btc_basis_decision(
            self,
            market_data: Dict,
            current_exposure: Dict) -> str:
        """
        Make BTC basis trading decision with perfect delta neutrality.
        
        Key Requirements:
        - Perfect delta neutrality (net delta EXACTLY 0)
        - Use actual funding rates (NO FALLBACKS)
        - Sequential execution per venue (transfer → spot → perp)
        - Only delta deviation triggers rebalancing
        """
        try:
            strategy_logger.info("BTC Basis: Starting decision logic")
            
            # Check if initial setup is needed
            needs_setup = self._needs_initial_btc_basis_setup(current_exposure)
            strategy_logger.info(f"BTC Basis: Initial setup check result: {needs_setup}")
            if needs_setup:
                strategy_logger.info("BTC Basis: Initial setup needed")
                return 'INITIAL_SETUP'
            
            # Check if rebalancing is needed (delta deviation only)
            if self._needs_btc_basis_rebalancing(current_exposure):
                strategy_logger.info("BTC Basis: Rebalancing needed due to delta deviation")
                return 'REBALANCE'
            
            strategy_logger.info("BTC Basis: No action needed - maintaining positions")
            return 'HOLD'
            
        except Exception as e:
            strategy_logger.error(f"BTC Basis decision failed: {e}")
            raise ValueError(f"STRAT-BTC-001: BTC basis decision failed: {e}")
    
    def _needs_initial_btc_basis_setup(self, current_exposure: Dict) -> bool:
        """
        Check if initial BTC basis setup is needed.
        
        Initial setup is needed when:
        - We have USDT in wallet but no BTC positions on any venue
        """
        try:
            # Check position monitor wallet balance directly (not exposure monitor)
            if self.exposure_monitor and self.exposure_monitor.position_monitor:
                wallet_usdt = self.exposure_monitor.position_monitor._token_monitor.wallet.get('USDT', 0.0)
                strategy_logger.info(f"BTC Basis: Position monitor wallet USDT balance: {wallet_usdt}")
                if wallet_usdt <= 1000:  # Need at least $1000 to start
                    strategy_logger.info(f"BTC Basis: Insufficient wallet USDT: {wallet_usdt}")
                    return False
            else:
                strategy_logger.warning("BTC Basis: No position monitor available for wallet balance check")
                return False
            
            # Check if we have any BTC positions on any venue
            exposures = current_exposure.get('exposures', {})
            btc_exposure = exposures.get('BTC', {})
            if not btc_exposure:
                return True
            
            # Check spot positions
            cex_spot = btc_exposure.get('cex_spot', {})
            has_btc_spot = any(spot > 0.001 for spot in cex_spot.values())
            
            # Check perp positions
            cex_perps = btc_exposure.get('cex_perps', {})
            has_btc_perps = any(
                abs(venue_positions.get('size', 0)) > 0.001 
                for venue_positions in cex_perps.values() 
                if venue_positions
            )
            
            # Need initial setup if we have USDT but no BTC positions
            needs_setup = not has_btc_spot and not has_btc_perps
            
            strategy_logger.info(f"BTC Basis: Initial setup check - wallet_usdt={wallet_usdt}, "
                               f"has_btc_spot={has_btc_spot}, has_btc_perps={has_btc_perps}, "
                               f"needs_setup={needs_setup}")
            
            return needs_setup
            
        except Exception as e:
            strategy_logger.error(f"BTC Basis initial setup check failed: {e}")
            raise ValueError(f"STRAT-BTC-001: Initial setup check failed: {e}")
    
    def _needs_btc_basis_rebalancing(self, current_exposure: Dict) -> bool:
        """
        Check if BTC basis rebalancing is needed due to delta deviation.
        
        Only delta deviation triggers rebalancing (no other triggers).
        """
        try:
            # Get current net delta
            net_delta_btc = current_exposure.get('net_delta_primary_asset', 0)
            
            # Get delta tolerance from config (default 0.5%)
            delta_tolerance = self.config.get('delta_tolerance', 0.005)
            
            # Calculate gross exposure for tolerance calculation
            gross_exposure = self._calculate_btc_gross_exposure(current_exposure)
            tolerance_threshold = gross_exposure * delta_tolerance
            
            # Check if delta deviation exceeds tolerance
            needs_rebalance = abs(net_delta_btc) > tolerance_threshold
            
            strategy_logger.info(f"BTC Basis: Rebalancing check - net_delta_btc={net_delta_btc}, "
                               f"gross_exposure={gross_exposure}, tolerance_threshold={tolerance_threshold}, "
                               f"needs_rebalance={needs_rebalance}")
            
            return needs_rebalance
            
        except Exception as e:
            strategy_logger.error(f"BTC Basis rebalancing check failed: {e}")
            raise ValueError(f"STRAT-BTC-004: Rebalancing check failed: {e}")
    
    def _calculate_btc_gross_exposure(self, current_exposure: Dict) -> float:
        """Calculate gross BTC exposure for delta tolerance calculation."""
        try:
            btc_exposure = current_exposure.get('exposures', {}).get('BTC', {})
            if not btc_exposure:
                return 0.0
            
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
            
        except Exception as e:
            strategy_logger.error(f"BTC gross exposure calculation failed: {e}")
            raise ValueError(f"STRAT-BTC-003: Gross exposure calculation failed: {e}")

    def _eth_leveraged_decision(
            self,
            market_data: Dict,
            current_exposure: Dict,
            risk_metrics: Dict) -> str:
        """Make ETH leveraged strategy decision."""
        # Check risk metrics
        ltv = risk_metrics.get('aave_ltv', 0)
        if ltv > 0.85:  # High LTV
            return 'REDUCE_LEVERAGE'
        elif ltv < 0.70:  # Low LTV
            return 'INCREASE_LEVERAGE'
        else:
            return 'MAINTAIN_LEVERAGE'

    def _usdt_market_neutral_decision(
            self,
            market_data: Dict,
            current_exposure: Dict,
            risk_metrics: Dict) -> str:
        """Make USDT market neutral strategy decision."""
        # Check delta exposure
        net_delta = current_exposure.get('net_delta_eth', 0)
        if abs(net_delta) > 10:  # Large delta exposure
            return 'REBALANCE_DELTA'
        else:
            return 'MAINTAIN_NEUTRAL'

    async def handle_position_change(
        self,
        change_type: str,
        params: Dict,
        current_exposure: Dict,
        risk_metrics: Dict
    ) -> Dict:
        """
        Unified handler for ALL position changes.

        Args:
            change_type: 'INITIAL_SETUP', 'DEPOSIT', 'WITHDRAWAL', 'REBALANCE'
            params: Type-specific parameters
            current_exposure: Current exposure from monitor
            risk_metrics: Current risks from monitor

        Returns:
            Instructions for execution managers
        """
        # Get desired position (mode-specific!)
        desired = self._get_desired_position(
            change_type, params, current_exposure)

        # Calculate gap
        gap = self._calculate_gap(current_exposure, desired)

        # Generate instructions to close gap
        instructions = self._generate_instructions(gap, change_type)

        return {
            'trigger': change_type,
            'current_state': self._extract_current_state(current_exposure),
            'desired_state': desired,
            'gaps': gap,
            'instructions': instructions
        }

    def _get_desired_position(
        self,
        change_type: str,
        params: Dict,
        current_exposure: Dict
    ) -> Dict:
        """
        Get desired position (MODE-SPECIFIC!).

        This is THE key function - different per mode!
        """
        if self.mode == 'pure_lending':
            return self._desired_pure_lending(change_type, params)

        elif self.mode == 'btc_basis':
            return self._desired_btc_basis(
                change_type, params, current_exposure)

        elif self.mode == 'eth_leveraged':
            return self._desired_eth_leveraged(
                change_type, params, current_exposure)

        elif self.mode == 'usdt_market_neutral':
            return self._desired_usdt_market_neutral(
                change_type, params, current_exposure)

        else:
            raise ValueError(f"Unknown mode: {self.mode}")

    # ===== MODE-SPECIFIC DESIRED POSITION FUNCTIONS =====

    def _desired_pure_lending(self, change_type: str, params: Dict) -> Dict:
        """Pure lending: All capital in AAVE USDT."""
        if change_type == 'INITIAL_SETUP':
            return {
                'aave_usdt_supplied': self.initial_capital,
                'target_delta_eth': 0,
                'target_perp_positions': {}
            }

        elif change_type == 'DEPOSIT':
            return {
                'aave_usdt_supplied': 'INCREASE',  # Add to AAVE
                'deposit_amount': params['amount']
            }

        # No rebalancing needed for pure lending
        return {}

    def _desired_btc_basis(
            self,
            change_type: str,
            params: Dict,
            current_exposure: Dict) -> Dict:
        """
        BTC basis: Long spot, short perp (perfect market-neutral).
        
        Key Requirements:
        - Perfect delta neutrality (net delta EXACTLY 0)
        - Use hedge allocation ratios (40% Binance, 30% Bybit, 30% OKX)
        - Sequential execution per venue (transfer → spot → perp)
        - Use actual venue-specific prices (NO FALLBACKS)
        """
        try:
            if change_type == 'INITIAL_SETUP':
                return self._calculate_initial_btc_basis_positions(params)
            elif change_type == 'REBALANCE':
                return self._calculate_rebalance_btc_basis_positions(current_exposure)
            else:
                strategy_logger.warning(f"BTC Basis: Unknown change_type {change_type}")
                return {}
                
        except Exception as e:
            strategy_logger.error(f"BTC Basis desired position calculation failed: {e}")
            raise ValueError(f"STRAT-BTC-002: Desired position calculation failed: {e}")
    
    def _calculate_initial_btc_basis_positions(self, params: Dict) -> Dict:
        """Calculate initial BTC basis positions - buy spot and sell perp on ALL venues."""
        try:
            total_capital = self.initial_capital
            market_data = params.get('market_data', {})
            
            # Get hedge allocations from config (NO FALLBACKS)
            hedge_allocations = {
                'binance': self.config.get('hedge_allocation_binance'),
                'bybit': self.config.get('hedge_allocation_bybit'),
                'okx': self.config.get('hedge_allocation_okx')
            }
            
            # Validate hedge allocations (NO FALLBACKS)
            if any(allocation is None for allocation in hedge_allocations.values()):
                raise ValueError("STRAT-BTC-003: Hedge allocations not found in config")
            
            if abs(sum(hedge_allocations.values()) - 1.0) > 0.001:
                raise ValueError(f"STRAT-BTC-003: Hedge allocations must sum to 1.0, got {sum(hedge_allocations.values())}")
            
            strategy_logger.info(f"BTC Basis: Hedge allocations - {hedge_allocations}")
            
            # Calculate positions for each venue
            transfers = []
            spot_trades = []
            perp_trades = []
            
            for venue, allocation in hedge_allocations.items():
                venue_capital = total_capital * allocation
                
                # Transfer USDT to venue
                transfers.append({
                    'source_venue': 'wallet',
                    'target_venue': venue,
                    'amount_usd': venue_capital,
                    'token': 'USDT',
                    'purpose': 'BTC basis initial setup'
                })
                
                # Get venue-specific BTC price (NO FALLBACKS)
                btc_price = self._get_venue_btc_price(venue, market_data)
                
                # Calculate BTC amount for this venue
                btc_amount = venue_capital / btc_price
                
                # Buy BTC spot on this venue
                spot_trades.append({
                    'venue': venue,
                    'symbol': 'BTCUSDT',
                    'side': 'buy',
                    'amount': btc_amount,
                    'price': btc_price,
                    'purpose': 'BTC basis spot purchase'
                })
                
                # Short BTC perp on this venue (EXACTLY same amount for perfect delta neutrality)
                perp_trades.append({
                    'venue': venue,
                    'symbol': 'BTCUSDT',
                    'side': 'sell',
                    'amount': btc_amount,  # EXACTLY same amount
                    'price': btc_price,
                    'purpose': 'BTC basis perp short'
                })
                
                strategy_logger.info(f"BTC Basis: {venue} - capital={venue_capital}, btc_price={btc_price}, "
                                   f"btc_amount={btc_amount}")
            
            return {
                'transfers': transfers,
                'spot_trades': spot_trades,
                'perp_trades': perp_trades,
                'target_delta_btc': 0,  # Perfect market neutrality
                'execution_order': 'sequential_per_venue'  # Transfer → Spot → Perp per venue
            }
            
        except Exception as e:
            strategy_logger.error(f"BTC Basis initial position calculation failed: {e}")
            raise ValueError(f"STRAT-BTC-002: Initial position calculation failed: {e}")
    
    def _calculate_rebalance_btc_basis_positions(self, current_exposure: Dict) -> Dict:
        """Calculate rebalancing positions to maintain perfect delta neutrality."""
        try:
            # Get current BTC positions
            btc_exposure = current_exposure.get('exposures', {}).get('BTC', {})
            cex_spot = btc_exposure.get('cex_spot', {})
            cex_perps = btc_exposure.get('cex_perps', {})
            
            # Calculate current net delta per venue
            venue_deltas = {}
            for venue in ['binance', 'bybit', 'okx']:
                spot_amount = cex_spot.get(venue, 0)
                perp_amount = cex_perps.get(venue, {}).get('size', 0)
                venue_deltas[venue] = spot_amount + perp_amount  # Spot is positive, perp is negative
            
            # Generate rebalancing trades to bring delta to EXACTLY zero
            rebalance_trades = []
            for venue, delta in venue_deltas.items():
                if abs(delta) > 0.001:  # Small tolerance for rounding
                    # Need to adjust perp position to neutralize delta
                    adjustment_amount = -delta  # Opposite sign to neutralize
                    
                    rebalance_trades.append({
                        'venue': venue,
                        'symbol': 'BTCUSDT',
                        'side': 'sell' if adjustment_amount < 0 else 'buy',
                        'amount': abs(adjustment_amount),
                        'purpose': f'BTC basis rebalance - neutralize {delta:.6f} delta'
                    })
                    
                    strategy_logger.info(f"BTC Basis: {venue} rebalance - delta={delta:.6f}, "
                                       f"adjustment={adjustment_amount:.6f}")
            
            return {
                'rebalance_trades': rebalance_trades,
                'target_delta_btc': 0,  # Perfect market neutrality
                'execution_order': 'sequential_per_venue'
            }
            
        except Exception as e:
            strategy_logger.error(f"BTC Basis rebalance calculation failed: {e}")
            raise ValueError(f"STRAT-BTC-002: Rebalance calculation failed: {e}")
    
    def _get_venue_btc_price(self, venue: str, market_data: Dict) -> float:
        """Get BTC price for venue (use same BTC price across all venues)."""
        try:
            # Use centralized utility for price lookups
            from ...utils.market_data_utils import get_market_data_utils
            market_utils = get_market_data_utils()
            
            # For BTC basis trading, use the same BTC price across all venues
            # since BTC is the same asset everywhere
            btc_price = market_utils.get_btc_price(market_data)
            
            if btc_price <= 0:
                raise ValueError(f"STRAT-BTC-006: Invalid BTC price: {btc_price}")
            
            return btc_price
            
        except Exception as e:
            strategy_logger.error(f"BTC price lookup failed for {venue}: {e}")
            raise ValueError(f"STRAT-BTC-006: BTC price lookup failed for {venue}: {e}")

    def _desired_eth_leveraged(
            self,
            change_type: str,
            params: Dict,
            current_exposure: Dict) -> Dict:
        """
        ETH leveraged staking.

        Two sub-modes:
        - ETH share class: Long ETH, no hedge
        - USDT share class: Hedged with perps
        """
        if change_type == 'INITIAL_SETUP':
            if self.share_class == 'ETH':
                # No hedging, directional ETH
                return {
                    'aave_ltv': self.config.get('strategy', {}).get('target_ltv', 0.91),
                    'target_delta_eth': self.initial_capital,  # Stay long ETH
                    'target_perp_positions': {}  # No hedging!
                }

            else:  # USDT share class
                # Need hedging
                eth_price = params.get('eth_price', 3000.0)
                capital_for_staking = self.initial_capital * 0.5
                eth_amount = capital_for_staking / eth_price

                return {
                    'aave_ltv': 0.91,
                    'target_delta_eth': 0,  # Market-neutral
                    'initial_eth_to_stake': eth_amount,
                    'target_perp_short_total': -eth_amount  # Hedge
                }

        elif change_type == 'REBALANCE':
            # Maintain target LTV and delta
            if self.share_class == 'ETH':
                return {
                    'aave_ltv': 0.91,
                    # Don't change (directional)
                    'target_delta_eth': 'MAINTAIN',
                }
            else:  # USDT
                # Hedge should match AAVE net position
                aave_net_eth = current_exposure.get(
                    'erc20_wallet_net_delta_eth', 0)
                return {
                    'aave_ltv': 0.91,
                    'target_delta_eth': 0,
                    'target_perp_short_total': -aave_net_eth
                }

        return {}

    def _desired_usdt_market_neutral(
            self,
            change_type: str,
            params: Dict,
            current_exposure: Dict) -> Dict:
        """
        USDT market-neutral (most complex).

        Always maintain:
        - AAVE LTV: 0.91
        - Net delta: 0
        - Perp short = AAVE net long
        """
        aave_net_eth = current_exposure.get('erc20_wallet_net_delta_eth', 0)

        if change_type == 'INITIAL_SETUP':
            eth_price = params.get('eth_price', 3000.0)
            capital_for_staking = self.initial_capital * 0.5
            eth_to_stake = capital_for_staking / eth_price

            return {
                'aave_ltv': 0.91,
                'target_delta_eth': 0,
                'initial_eth_to_stake': eth_to_stake,
                'target_perp_short_total': -eth_to_stake,
                'hedge_allocation': self.config.get('strategy', {}).get('hedge_allocation', {
                    'binance': 0.33, 'bybit': 0.33, 'okx': 0.34
                })
            }

        elif change_type == 'REBALANCE':
            return {
                'aave_ltv': 0.91,
                'target_delta_eth': 0,
                'target_perp_short_total': -aave_net_eth,  # Match AAVE
                'target_margin_ratio': 1.0  # Full capital utilization
            }

        elif change_type == 'DEPOSIT':
            # New capital: Split 50/50 (staking / hedge)
            return {
                'add_to_aave': params['amount'] * 0.5,
                'add_to_cex_margin': params['amount'] * 0.5
            }

        return {}

    def _calculate_gap(self, current_exposure: Dict, desired: Dict) -> Dict:
        """Calculate gap between current and desired positions."""
        gap = {}

        # AAVE LTV gap
        current_ltv = current_exposure.get('aave_ltv', 0)
        desired_ltv = desired.get('aave_ltv', current_ltv)
        gap['aave_ltv_gap'] = desired_ltv - current_ltv

        # Delta gap
        current_delta = current_exposure.get('net_delta_eth', 0)
        desired_delta = desired.get('target_delta_eth', current_delta)
        if desired_delta == 'MAINTAIN':
            desired_delta = current_delta
        gap['delta_gap_eth'] = desired_delta - current_delta

        # Margin gap (if critical)
        margin_ratios = current_exposure.get('cex_margin_ratios', {})
        min_margin_ratio = min(
            margin_ratios.values()) if margin_ratios else 1.0
        if min_margin_ratio < 0.20:  # Critical margin
            gap['margin_deficit_usd'] = self._calculate_margin_deficit(
                current_exposure)
            gap['critical_venue'] = min(margin_ratios, key=margin_ratios.get)

        return gap

    def _calculate_margin_deficit(self, current_exposure: Dict) -> float:
        """Calculate margin deficit in USD."""
        # Simplified calculation - in practice would use current prices
        margin_ratios = current_exposure.get('cex_margin_ratios', {})
        min_ratio = min(margin_ratios.values()) if margin_ratios else 1.0

        # Calculate how much margin needed to get back to 50%
        target_ratio = 0.50
        if min_ratio < target_ratio:
            # This is a simplified calculation
            return 10000.0  # Placeholder

        return 0.0

    def _extract_current_state(self, current_exposure: Dict) -> Dict:
        """Extract current state for comparison."""
        return {
            'aave_ltv': current_exposure.get(
                'aave_ltv', 0), 'net_delta_eth': current_exposure.get(
                'net_delta_eth', 0), 'margin_ratio_binance': current_exposure.get(
                'cex_margin_ratios', {}).get(
                    'binance', 1.0)}

    def _generate_instructions(
            self,
            gap: Dict,
            trigger_type: str) -> List[Dict]:
        """
        Generate execution instructions to close gap.

        Instructions are prioritized and sequenced.
        """
        instructions = []

        # Priority 1: Margin critical (prevent CEX liquidation)
        if 'margin_deficit_usd' in gap and gap['margin_deficit_usd'] > 1000:
            instructions.append(self._gen_add_margin_instruction(gap))

        # Priority 2: AAVE LTV critical (prevent AAVE liquidation)
        if 'aave_ltv_excess' in gap and gap['aave_ltv_excess'] > 0.02:
            instructions.append(self._gen_reduce_ltv_instruction(gap))

        # Priority 3: Delta drift (maintain market neutrality)
        if 'delta_gap_eth' in gap and abs(gap['delta_gap_eth']) > 2.0:
            instructions.append(self._gen_adjust_delta_instruction(gap))

        return instructions

    def _gen_add_margin_instruction(self, gap: Dict) -> Dict:
        """
        Generate instruction to add margin to CEX.

        Flow:
        1. Atomic deleverage AAVE (free up ETH)
        2. Transfer ETH to CEX
        3. Sell ETH for USDT (spot)
        4. Reduce perp short (proportionally)
        """
        amount_usd = gap['margin_deficit_usd']
        venue = gap['critical_venue']  # Which exchange needs margin

        return {
            'priority': 1,
            'type': 'ADD_MARGIN_TO_CEX',
            'venue': venue,
            'amount_usd': amount_usd,
            'actions': [
                {
                    'step': 1,
                    'action': 'ATOMIC_DELEVERAGE_AAVE',
                    'executor': 'OnChainExecutionManager',
                    'params': {
                        'amount_usd': amount_usd,
                        'mode': 'atomic' if self.config.get('strategy', {}).get('use_flash_loan', False) else 'sequential',
                        'unwind_mode': self.config.get('strategy', {}).get('unwind_mode', 'fast')
                    }
                },
                {
                    'step': 2,
                    'action': 'TRANSFER_ETH_TO_CEX',
                    'executor': 'OnChainExecutionManager',
                    'params': {
                        'venue': venue,
                        'amount_eth': amount_usd / 3000.0  # Simplified ETH price
                    }
                },
                {
                    'step': 3,
                    'action': 'SELL_ETH_SPOT',
                    'executor': 'CEXExecutionManager',
                    'params': {
                        'venue': venue,
                        'amount_eth': amount_usd / 3000.0
                    }
                },
                {
                    'step': 4,
                    'action': 'REDUCE_PERP_SHORT',
                    'executor': 'CEXExecutionManager',
                    'params': {
                        'venue': venue,
                        'instrument': 'ETHUSDT-PERP',
                        'amount_eth': amount_usd / 3000.0
                    }
                }
            ]
        }

    def _gen_reduce_ltv_instruction(self, gap: Dict) -> Dict:
        """Generate instruction to reduce AAVE LTV."""
        return {
            'priority': 2,
            'type': 'REDUCE_AAVE_LTV',
            'amount_usd': gap.get('aave_ltv_excess', 0) * 10000,  # Simplified
            'actions': [
                {
                    'step': 1,
                    'action': 'ATOMIC_DELEVERAGE_AAVE',
                    'executor': 'OnChainExecutionManager',
                    'params': {
                        'amount_usd': gap.get('aave_ltv_excess', 0) * 10000,
                        'mode': 'atomic'
                    }
                }
            ]
        }

    def _gen_adjust_delta_instruction(self, gap: Dict) -> Dict:
        """Generate instruction to adjust delta exposure."""
        delta_gap = gap.get('delta_gap_eth', 0)

        if delta_gap > 0:
            # Need to reduce long exposure (short more)
            action = 'INCREASE_PERP_SHORT'
        else:
            # Need to increase long exposure (reduce shorts)
            action = 'REDUCE_PERP_SHORT'

        return {
            'priority': 3,
            'type': 'ADJUST_DELTA',
            'delta_gap_eth': delta_gap,
            'actions': [
                {
                    'step': 1,
                    'action': action,
                    'executor': 'CEXExecutionManager',
                    'params': {
                        'venue': 'binance',  # Default venue
                        'instrument': 'ETHUSDT-PERP',
                        'amount_eth': abs(delta_gap)
                    }
                }
            ]
        }

    def check_rebalancing_needed(self, risk_metrics: Dict) -> Optional[str]:
        """Check if rebalancing needed."""

        # Priority 1: Margin critical (prevent CEX liquidation)
        if risk_metrics.get('cex_margin', {}).get('any_critical', False):
            return 'MARGIN_CRITICAL'

        min_margin_ratio = risk_metrics.get(
            'cex_margin', {}).get(
            'min_margin_ratio', 1.0)
        if min_margin_ratio < self.margin_warning_threshold:
            return 'MARGIN_WARNING'

        # Priority 2: Delta drift (maintain market neutrality)
        if risk_metrics.get('delta', {}).get('critical', False):
            return 'DELTA_DRIFT_CRITICAL'

        if risk_metrics.get('delta', {}).get('warning', False):
            return 'DELTA_DRIFT_WARNING'

        # Priority 3: AAVE LTV (prevent AAVE liquidation)
        if risk_metrics.get('aave', {}).get('critical', False):
            return 'AAVE_LTV_CRITICAL'

        if risk_metrics.get('aave', {}).get('warning', False):
            return 'AAVE_LTV_WARNING'

        # No rebalancing needed
        return None

    async def _on_risk_update(self, message):
        """Handle risk update from Redis."""
        try:
            risk_data = json.loads(message['data'])
            trigger = self.check_rebalancing_needed(risk_data)

            if trigger:
                logger.info(f"Rebalancing triggered: {trigger}")
                # Get current exposure and generate instructions
                current_exposure = self.exposure_monitor.get_snapshot()
                instructions = await self.handle_position_change(
                    'REBALANCE',
                    {'trigger': trigger},
                    current_exposure,
                    risk_data
                )

                # Publish instructions to execution managers
                await self.redis.publish('strategy:instructions', json.dumps(instructions))

        except Exception as e:
            logger.error(f"Error handling risk update: {e}")

    async def publish_instructions(self, instructions: Dict):
        """Publish instructions to execution managers via Redis."""
        await self.redis.publish('strategy:instructions', json.dumps(instructions))

    async def handle_king_token_management(
        self,
        position_snapshot: Dict,
        timestamp: pd.Timestamp
    ) -> Optional[Dict]:
        """
        Check KING token balance and orchestrate unwrapping if threshold exceeded.

        Threshold: KING balance > 100x gas fee (economical to unwrap)

        Flow:
        1. EventLogger triggers token balance update (shows KING tokens)
        2. StrategyManager detects KING balance (this method)
        3. If > threshold: Orchestrate unwrap → transfer → sell via OnChainExecutionManager

        Args:
            position_snapshot: Current position snapshot from PositionMonitor
            timestamp: Current timestamp

        Returns:
            KING unwrapping instruction if threshold exceeded, None otherwise
        """
        try:
            # Get KING balance from wallet
            wallet_balances = position_snapshot.get('wallet', {})
            king_balance = wallet_balances.get('KING', 0.0)

            if king_balance <= 0:
                return None

            # Calculate KING value in USD
            # For now, use a default KING price (would need KING price data in
            # production)
            king_price_usd = 1.0  # Default price - would need actual KING price data
            king_value_usd = king_balance * king_price_usd

            # Calculate threshold (100x gas fee)
            gas_fee_eth = 0.01  # Estimated gas fee for unwrap + transfer + sell
            eth_price_usd = 3000.0  # Default ETH price - would need actual price data
            threshold_usd = gas_fee_eth * eth_price_usd * 100  # 100x gas fee

            if king_value_usd <= threshold_usd:
                logger.debug(
                    f"KING balance ${king_value_usd:.2f} below threshold ${threshold_usd:.2f}, holding")
                return None

            # Above threshold - generate unwrap instruction
            logger.info(
                f"🎁 KING balance ${king_value_usd:.2f} > threshold ${threshold_usd:.2f}, unwrapping")

            return {
                'priority': 2,  # After critical rebalancing
                'type': 'UNWRAP_AND_SELL_KING',
                'actions': [
                    {
                        'action': 'unwrap_and_sell_king_tokens',
                        'params': {
                            'king_balance': king_balance,
                            'timestamp': timestamp
                        },
                        'executor': 'onchain_execution_manager'
                    }
                ],
                'metadata': {
                    'king_balance': king_balance,
                    'king_value_usd': king_value_usd,
                    'threshold_usd': threshold_usd,
                    'trigger': 'KING_THRESHOLD_EXCEEDED'
                }
            }

        except Exception as e:
            logger.error(f"Error in KING token management: {e}")
            return None

    async def execute_decision(self, decision: Dict, timestamp: pd.Timestamp, execution_interfaces: Dict, market_data: Dict = None) -> Dict:
        """
        Execute a strategy decision using the new instruction-based architecture.
        
        Args:
            decision: Strategy decision dictionary
            timestamp: Current timestamp
            execution_interfaces: Dictionary of execution interfaces
            market_data: Market data for execution cost calculations
            
        Returns:
            Execution result dictionary
        """
        action = decision.get('action')
        strategy_logger.info(f"Strategy Manager: Executing decision action: {action}")
        
        try:
            # Generate instruction blocks based on action and mode
            instruction_blocks = self._generate_instruction_blocks(decision)
            
            # Execute instruction blocks in sequence
            results = await self._execute_instruction_blocks(instruction_blocks, timestamp, execution_interfaces, market_data)
            
            strategy_logger.info(f"Strategy Manager: Decision execution completed - {len(instruction_blocks)} blocks executed")
            
            return {
                'success': True,
                'action': action,
                'mode': self.mode,
                'blocks_executed': len(instruction_blocks),
                'results': results
            }
                
        except Exception as e:
            strategy_logger.error(f"Decision execution failed: {e}")
            raise

    def _generate_instruction_blocks(self, decision: Dict) -> List[InstructionBlock]:
        """Generate instruction blocks based on decision action and mode."""
        action = decision.get('action')
        strategy_logger.info(f"Strategy Manager: Generating instruction blocks for action: {action}, mode: {self.mode}")
        
        if action == 'INITIAL_SETUP' and self.mode == 'btc_basis':
            desired_positions = decision.get('desired_positions', {})
            strategy_logger.info(f"Strategy Manager: Desired positions keys: {list(desired_positions.keys())}")
            blocks = InstructionGenerator.create_btc_basis_setup_instructions(desired_positions)
            strategy_logger.info(f"Strategy Manager: Generated {len(blocks)} instruction blocks")
            return blocks
        elif action == 'AAVE_SUPPLY':
            blocks = InstructionGenerator.create_aave_supply_instructions(
                decision.get('asset', 'USDT'),
                decision.get('amount', 0)
            )
            strategy_logger.info(f"Strategy Manager: Generated {len(blocks)} instruction blocks for AAVE_SUPPLY")
            return blocks
        else:
            strategy_logger.warning(f"No instruction generator for action: {action}, mode: {self.mode}")
            return []

    async def _execute_instruction_blocks(self, instruction_blocks: List[InstructionBlock], timestamp: pd.Timestamp, execution_interfaces: Dict, market_data: Dict = None) -> List[Dict]:
        """Execute instruction blocks in sequence with proper routing and position monitor updates."""
        results = []
        
        # Initialize wallet transfer executor
        wallet_transfer_executor = WalletTransferExecutor(
            position_monitor=self.exposure_monitor.position_monitor if self.exposure_monitor else None,
            event_logger=None,  # Will be set by Event Engine
            execution_mode='backtest'  # TODO: Get from config
        )
        
        # Set Position Update Handler on wallet transfer executor if available
        if hasattr(self, 'position_update_handler') and self.position_update_handler:
            wallet_transfer_executor.position_update_handler = self.position_update_handler
        
        for block in instruction_blocks:
            strategy_logger.info(f"Strategy Manager: Executing block {block.timestamp_group} ({block.block_type})")
            
            try:
                if block.block_type == 'wallet_transfers':
                    strategy_logger.info(f"Strategy Manager: Routing to WalletTransferExecutor for {len(block.instructions)} transfers")
                    result = await wallet_transfer_executor.execute_transfer_block(block, timestamp)
                    strategy_logger.info(f"Strategy Manager: WalletTransferExecutor completed: {result.get('success')}")
                    
                    # Note: Position monitor is already updated by WalletTransferExecutor
                        
                elif block.block_type == 'cex_trades':
                    result = await self._execute_cex_trade_block(block, timestamp, execution_interfaces, market_data)
                    
                    # Note: Position monitor is already updated by CEX execution interface
                        
                elif block.block_type == 'smart_contracts':
                    result = await self._execute_smart_contract_block(block, timestamp, execution_interfaces)
                    
                    # Note: Position monitor is already updated by OnChain execution interface
                        
                else:
                    raise ValueError(f"Unknown block type: {block.block_type}")
                
                results.append(result)
                strategy_logger.info(f"Strategy Manager: Block {block.timestamp_group} completed successfully")
                
                # NOTE: Strategy Manager is READ-ONLY - it never updates position monitor
                # Position monitor updates are handled by execution interfaces
                # Fast path updates (exposure → risk → P&L) are handled by the tight loop abstraction
                
            except Exception as e:
                strategy_logger.error(f"Block {block.timestamp_group} execution failed: {e}")
                raise
        
        return results

    async def _execute_cex_trade_block(self, trade_block: InstructionBlock, timestamp: pd.Timestamp, execution_interfaces: Dict, market_data: Dict = None) -> Dict:
        """Execute a block of CEX trade instructions."""
        cex_interface = execution_interfaces.get('cex')
        if not cex_interface:
            raise ValueError("CEX execution interface not available")
        
        results = []
        for instruction in trade_block.instructions:
            # Convert CEXTradeInstruction to interface format
            interface_instruction = instruction.to_dict()
            strategy_logger.info(f"Strategy Manager: Sending instruction to CEX interface: {interface_instruction}")
            result = await cex_interface.execute_trade(interface_instruction, market_data or {})
            results.append(result)
            strategy_logger.info(f"Strategy Manager: CEX trade result: {result}")
            
            # NOTE: Strategy Manager is READ-ONLY - it never updates position monitor
            # Position monitor updates are handled by execution interfaces
            # Fast path updates (exposure → risk → P&L) are handled by the tight loop abstraction
        
        return {
            'success': True,
            'block_type': trade_block.block_type,
            'timestamp_group': trade_block.timestamp_group,
            'trades_executed': len(results),
            'results': results
        }

    async def _execute_smart_contract_block(self, contract_block: InstructionBlock, timestamp: pd.Timestamp, execution_interfaces: Dict) -> Dict:
        """Execute a block of smart contract instructions."""
        onchain_interface = execution_interfaces.get('onchain')
        if not onchain_interface:
            raise ValueError("OnChain execution interface not available")
        
        if contract_block.execution_mode == ExecutionMode.ATOMIC.value:
            # Atomic execution - single transaction
            return await self._execute_atomic_contract_operations(contract_block, timestamp, onchain_interface, market_data)
        else:
            # Sequential execution - multiple transactions
            return await self._execute_sequential_contract_operations(contract_block, timestamp, onchain_interface, market_data)

    async def _execute_atomic_contract_operations(self, contract_block: InstructionBlock, timestamp: pd.Timestamp, onchain_interface, market_data: Dict = None) -> Dict:
        """Execute atomic smart contract operations (single transaction)."""
        strategy_logger.info(f"Strategy Manager: Executing atomic smart contract block: {contract_block.timestamp_group}")
        
        # Group all operations into single atomic instruction
        atomic_instruction = {
            'operation': 'ATOMIC_TRANSACTION',
            'execution_mode': ExecutionMode.ATOMIC.value,
            'operations': [instr.to_dict() for instr in contract_block.instructions],
            'timestamp_group': contract_block.timestamp_group,
            'gas_cost_type': contract_block.instructions[0].gas_cost_type if contract_block.instructions else 'ATOMIC_ENTRY'
        }
        
        result = await onchain_interface.execute_trade(atomic_instruction, market_data or {})
        
        # For atomic operations, trigger tight loop after all operations complete
        if hasattr(self, 'position_update_handler') and self.position_update_handler:
            strategy_logger.info(f"Strategy Manager: Triggering tight loop after atomic operations complete")
            await self.position_update_handler.trigger_tight_loop_after_atomic(
                timestamp=timestamp,
                market_data={}  # Smart contract operations don't need market data
            )
        
        return {
            'success': True,
            'block_type': contract_block.block_type,
            'execution_mode': 'atomic',
            'timestamp_group': contract_block.timestamp_group,
            'operations_executed': len(contract_block.instructions),
            'result': result
        }

    async def _execute_sequential_contract_operations(self, contract_block: InstructionBlock, timestamp: pd.Timestamp, onchain_interface, market_data: Dict = None) -> Dict:
        """Execute sequential smart contract operations (multiple transactions)."""
        strategy_logger.info(f"Strategy Manager: Executing sequential smart contract block: {contract_block.timestamp_group}")
        
        results = []
        for instruction in contract_block.instructions:
            interface_instruction = instruction.to_dict()
            result = await onchain_interface.execute_trade(interface_instruction, market_data or {})
            results.append(result)
            
            # NOTE: Strategy Manager is READ-ONLY - it never updates position monitor
            # Position monitor updates are handled by execution interfaces
            # Fast path updates (exposure → risk → P&L) are handled by the tight loop abstraction
        
        return {
            'success': True,
            'block_type': contract_block.block_type,
            'execution_mode': 'sequential',
            'timestamp_group': contract_block.timestamp_group,
            'operations_executed': len(results),
            'results': results
        }

    # Remove old execution methods - replaced by new instruction-based system
    # async def _execute_btc_basis_setup - REMOVED
    # async def _execute_btc_basis_rebalance - REMOVED  
    # async def _execute_aave_supply - REMOVED
    # async def _execute_cex_trade - REMOVED
    # async def _execute_onchain_operation - REMOVED
    # async def _execute_simple_transfer - REMOVED (now in WalletTransferExecutor)
    

