"""
Exposure Monitor Component

TODO-REFACTOR: GENERIC VS MODE-SPECIFIC ARCHITECTURE VIOLATION - 18_generic_vs_mode_specific_architecture.md
ISSUE: This component violates canonical architecture requirements:

1. GENERIC COMPONENT VIOLATIONS:
   - Should be generic and mode-agnostic, but currently uses mode-specific logic
   - Should care about config parameters (asset, share_class), not strategy mode
   - Should NOT have hardcoded mode checks like "if mode == 'btc_basis'"

TODO-REFACTOR: MISSING CENTRALIZED UTILITY MANAGER VIOLATION - 14_mode_agnostic_architecture_requirements.md
ISSUE: This component has scattered utility methods that should be centralized:

1. CENTRALIZED UTILITY MANAGER REQUIREMENTS:
   - Utility methods should be centralized in a single manager
   - Liquidity index calculations should be centralized
   - Market price conversions should be centralized
   - No scattered utility methods across components

2. REQUIRED VERIFICATION:
   - Check for scattered utility methods in this component
   - Verify utility methods are properly centralized
   - Ensure no duplicate utility logic across components

3. CANONICAL SOURCE:
   - .cursor/tasks/14_mode_agnostic_architecture_requirements.md
   - Centralized utilities required

2. REQUIRED ARCHITECTURE (per 18_generic_vs_mode_specific_architecture.md):
   - Should be generic exposure calculation
   - Should care about: asset (which deltas to monitor), share_class (reporting currency)
   - Should NOT care about: strategy mode specifics
   - Should use config-driven parameters, not mode-specific logic

3. CURRENT VIOLATIONS:
   - Uses mode-specific logic instead of config-driven parameters
   - Has hardcoded strategy mode checks
   - Should be refactored to use: asset = config.get('asset'), share_class = config.get('share_class')

4. REQUIRED FIX:
   - Remove all mode-specific logic
   - Use config parameters: asset, share_class, lst_type, hedge_allocation
   - Make component truly mode-agnostic
   - Generic exposure calculation using config parameters

CURRENT STATE: This component needs refactoring to be truly generic and mode-agnostic.
"""

from typing import Dict, List, Optional, Any
import redis
import json
import logging
import asyncio
from datetime import datetime
import pandas as pd
from pathlib import Path

from ....core.error_codes.error_code_registry import get_error_info, ErrorCodeInfo

logger = logging.getLogger(__name__)

# Create dedicated exposure monitor logger
exposure_logger = logging.getLogger('exposure_monitor')
exposure_logger.setLevel(logging.INFO)

# Create logs directory if it doesn't exist
logs_dir = Path(__file__).parent.parent.parent.parent.parent.parent / 'logs'
logs_dir.mkdir(exist_ok=True)

# Create file handler for exposure monitor logs
exposure_handler = logging.FileHandler(logs_dir / 'exposure_monitor.log')
exposure_handler.setLevel(logging.INFO)

# Create formatter
exposure_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
exposure_handler.setFormatter(exposure_formatter)

# Add handler to logger if not already added
if not exposure_logger.handlers:
    exposure_logger.addHandler(exposure_handler)
    exposure_logger.propagate = False


class ExposureMonitorError(Exception):
    """Custom exception for exposure monitor errors with error codes."""
    
    def __init__(self, error_code: str, message: str = None, **kwargs):
        self.error_code = error_code
        error_info = get_error_info(error_code)
        
        if error_info:
            self.component = error_info.component
            self.severity = error_info.severity
            self.description = error_info.description
            self.resolution = error_info.resolution
            
            # Use provided message or default from error code
            self.message = message or error_info.message
        else:
            # Fallback if error code not found
            self.component = "EXP"
            self.severity = "HIGH"
            self.message = message or f"Unknown error: {error_code}"
        
        # Add any additional context
        self.context = kwargs
        
        # Create the full error message
        full_message = f"{error_code}: {self.message}"
        if self.context:
            context_str = ", ".join([f"{k}={v}" for k, v in self.context.items()])
            full_message += f" ({context_str})"
        
        super().__init__(full_message)


class ExposureMonitor:
    """Calculate exposure from raw balances."""
    
    def __init__(self, 
                 config: Dict[str, Any],
                 share_class: str, 
                 position_monitor=None, 
                 data_provider=None,
                 debug_mode: bool = False):
        """
        Initialize exposure monitor with injected dependencies.
        
        Phase 3: Uses validated config and injected data provider.
        
        Args:
            config: Strategy configuration from validated config manager
            share_class: Share class ('ETH' or 'USDT')
            position_monitor: Position monitor instance
            data_provider: Data provider instance for price lookups
            debug_mode: Enable debug logging for exposure calculations
        """
        self.config = config
        self.share_class = share_class  # 'ETH' or 'USDT'
        self.position_monitor = position_monitor
        self.data_provider = data_provider
        self.debug_mode = debug_mode
        
        # Validate required parameters (FAIL FAST)
        if share_class not in ['USDT', 'ETH']:
            raise ValueError(f"Invalid share_class: {share_class}. Must be 'USDT' or 'ETH'.")
        
        if not position_monitor:
            raise ValueError("Position monitor is required")
        
        if not data_provider:
            raise ValueError("Data provider is required")
        
        # Redis for inter-component communication
        self.redis = None
        execution_mode = getattr(position_monitor, 'execution_mode', 'backtest')
        if execution_mode == 'live':
            try:
                import os
                redis_url = os.getenv('BASIS_REDIS_URL')
                if not redis_url:
                    raise ValueError("BASIS_REDIS_URL environment variable required for live mode")
                
                self.redis = redis.Redis.from_url(redis_url, decode_responses=True)
                # Test connection
                self.redis.ping()
                logger.info("Redis connection established for Exposure Monitor")
            except Exception as e:
                logger.error(f"Redis connection failed for live mode: {e}")
                raise ValueError(f"Redis required for live mode but connection failed: {e}")
        
        logger.info(f"Exposure Monitor initialized: {share_class} share class, {execution_mode} mode")
    
    def _get_tracked_assets(self, mode: str, primary_asset: str) -> List[str]:
        """Get list of assets to track based on mode and primary asset."""
        if mode == "btc_basis":
            return ["USDT", "BTC"]  # USDT for wallet balance, BTC for positions
        elif mode == "pure_lending":
            return ["USDT", "aUSDT"]  # Only USDT and derivatives for USDT strategies
        elif mode in ["eth_leveraged", "eth_staking_only"]:
            return ["ETH", "weETH", "wstETH", "aWeETH", "variableDebtWETH"]  # ETH and derivatives
        elif mode in ["usdt_market_neutral", "usdt_market_neutral_no_leverage"]:
            return ["ETH", "weETH", "wstETH", "aWeETH", "variableDebtWETH"]  # ETH and derivatives
        else:
            # Default: track primary asset and derivatives
            if primary_asset == "BTC":
                return ["BTC"]
            elif primary_asset == "ETH":
                return ["ETH", "weETH", "wstETH", "aWeETH", "variableDebtWETH"]
            elif primary_asset == "USDT":
                return ["USDT", "aUSDT"]
            else:
                return [primary_asset]
    
    def _calculate_asset_exposure(self, asset: str, wallet: Dict, cex_accounts: Dict, 
                                 perp_positions: Dict, market_data: Dict, timestamp: pd.Timestamp) -> Dict:
        """Calculate exposure for a specific asset across all venues."""
        try:
            if self.debug_mode:
                logger.debug(f"Processing asset: {asset}")
            total_balance = 0.0
            total_exposure_eth = 0.0
            total_exposure_usd = 0.0
            total_exposure_btc = 0.0
            total_exposure_usdt = 0.0
            underlying_balance = None  # For AAVE tokens
            
            # 1. Wallet balance
            wallet_balance = wallet.get(asset, 0.0)
            if wallet_balance != 0:
                wallet_exposure = self._convert_balance_to_exposure(
                    asset=asset, 
                    balance=wallet_balance, 
                    market_data=market_data,
                    venue="wallet"
                )
                total_balance += wallet_balance
                total_exposure_eth += wallet_exposure.get('exposure_eth', 0.0)
                total_exposure_usd += wallet_exposure.get('exposure_usd', 0.0)
                total_exposure_btc += wallet_exposure.get('exposure_btc', 0.0)
                total_exposure_usdt += wallet_exposure.get('exposure_usdt', 0.0)
                
                # Preserve underlying_balance for AAVE tokens (for P&L calculation)
                if 'underlying_balance' in wallet_exposure:
                    underlying_balance = wallet_exposure['underlying_balance']
            
            # 2. CEX balances
            for venue, tokens in cex_accounts.items():
                cex_balance = tokens.get(asset, 0.0)
                if cex_balance != 0:
                    cex_exposure = self._convert_balance_to_exposure(
                        asset=asset,
                        balance=cex_balance,
                        market_data=market_data,
                        venue=venue
                    )
                    total_balance += cex_balance
                    total_exposure_eth += cex_exposure.get('exposure_eth', 0.0)
                    total_exposure_usd += cex_exposure.get('exposure_usd', 0.0)
                    total_exposure_btc += cex_exposure.get('exposure_btc', 0.0)
                    total_exposure_usdt += cex_exposure.get('exposure_usdt', 0.0)
            
            # 3. Perp positions (convert to underlying asset exposure)
            perp_exposure = self._calculate_perp_exposure(
                asset=asset,
                perp_positions=perp_positions,
                market_data=market_data
            )
            total_exposure_eth += perp_exposure.get('exposure_eth', 0.0)
            total_exposure_usd += perp_exposure.get('exposure_usd', 0.0)
            total_exposure_btc += perp_exposure.get('exposure_btc', 0.0)  # BTC exposure from perps
            total_exposure_usdt += perp_exposure.get('exposure_usdt', 0.0)  # USDT exposure from perps
            
            # Debug logging for BTC asset processing
            if asset == 'BTC':
                logger.info(f"Exposure Monitor: BTC processing - total_balance={total_balance}, total_exposure_eth={total_exposure_eth}, total_exposure_usd={total_exposure_usd}, total_exposure_btc={total_exposure_btc}, total_exposure_usdt={total_exposure_usdt}")
                logger.info(f"Exposure Monitor: BTC perp_exposure = {perp_exposure}")
                logger.info(f"Exposure Monitor: BTC wallet_balance = {wallet_balance}")
                logger.info(f"Exposure Monitor: BTC cex_accounts = {cex_accounts}")
            
            # Only return if there's actual exposure
            # For BTC basis strategy, include BTC exposure even if ETH/USD exposures are zero
            if total_exposure_eth != 0 or total_exposure_usd != 0 or total_exposure_btc != 0 or total_exposure_usdt != 0:
                # Calculate venue breakdown
                venue_breakdown = {
                    'on_chain_wallet': wallet_balance,
                    'cex_spot': sum(cex_accounts.get(venue, {}).get(asset, 0.0) for venue in cex_accounts),
                    'cex_perps': perp_exposure.get('balance', 0.0),
                    'aave_tokens': 0.0,
                    'aave_debt': 0.0
                }
                
                # For AAVE tokens, update venue breakdown
                if asset in ["aWeETH", "aUSDT"]:
                    aave_exposure = self._calculate_aave_token_exposure(asset, wallet_balance, market_data, "wallet")
                    venue_breakdown['aave_tokens'] = aave_exposure.get('venue_breakdown', {}).get('aave_tokens', 0.0)
                elif asset == "variableDebtWETH":
                    debt_exposure = self._calculate_aave_debt_exposure(asset, wallet_balance, market_data, "wallet")
                    venue_breakdown['aave_debt'] = debt_exposure.get('venue_breakdown', {}).get('aave_debt', 0.0)
                
                result = {
                    'balance': total_balance,
                    'exposure_eth': total_exposure_eth,
                    'exposure_usd': total_exposure_usd,
                    'exposure_btc': total_exposure_btc,
                    'exposure_usdt': total_exposure_usdt,
                    'net_delta': total_exposure_eth,  # Net delta in ETH units
                    'venue_breakdown': venue_breakdown
                }
                
                # Add underlying_balance for AAVE tokens (needed by P&L calculator)
                if underlying_balance is not None:
                    result['underlying_balance'] = underlying_balance
                
                return result
            
            return None
            
        except Exception as e:
            # Don't fail if asset position is 0, but log error for non-zero positions
            if total_balance != 0:
                logger.error(f"Error calculating exposure for {asset}: {e}")
                raise ExposureMonitorError(
                    'EXP-005',
                    message=f"Failed to calculate exposure for {asset}",
                    asset=asset,
                    error=str(e)
                )
            return None
    
    def _convert_balance_to_exposure(self, asset: str, balance: float, market_data: Dict, venue: str) -> Dict:
        """Convert asset balance to ETH and USD exposure."""
        if balance == 0:
            return {'exposure_eth': 0.0, 'exposure_usd': 0.0}
        
        # Fail fast for required pricing data
        if asset == "ETH":
            eth_usd_price = market_data.get('eth_usd_price')
            if eth_usd_price is None:
                raise ExposureMonitorError('EXP-004', message="ETH/USD price required", asset=asset, venue=venue)
            return {
                'exposure_eth': balance,
                'exposure_usd': balance * eth_usd_price,
                'exposure_btc': 0.0  # ETH doesn't have BTC exposure
            }
        
        elif asset == "BTC":
            btc_usd_price = market_data.get('btc_usd_price')
            eth_usd_price = market_data.get('eth_usd_price')
            if btc_usd_price is None or eth_usd_price is None:
                raise ExposureMonitorError('EXP-004', message="BTC/USD and ETH/USD prices required", asset=asset, venue=venue)
            return {
                'exposure_eth': balance * btc_usd_price / eth_usd_price,
                'exposure_usd': balance * btc_usd_price,
                'exposure_btc': balance  # Direct BTC exposure
            }
        
        elif asset == "USDT":
            eth_usd_price = market_data.get('eth_usd_price')
            if eth_usd_price is None:
                raise ExposureMonitorError('EXP-004', message="ETH/USD price required for USDT conversion", asset=asset, venue=venue)
            return {
                'exposure_eth': balance / eth_usd_price,
                'exposure_usd': balance,
                'exposure_btc': 0.0,  # USDT doesn't have BTC exposure
                'exposure_usdt': balance  # Direct USDT exposure
            }
        
        elif asset in ["weETH", "wstETH"]:
            oracle_price = market_data.get(f'{asset.lower()}_eth_oracle')
            eth_usd_price = market_data.get('eth_usd_price')
            if oracle_price is None or eth_usd_price is None:
                raise ExposureMonitorError('EXP-004', message=f"{asset}/ETH oracle and ETH/USD prices required", asset=asset, venue=venue)
            return {
                'exposure_eth': balance * oracle_price,
                'exposure_usd': balance * oracle_price * eth_usd_price,
                'exposure_btc': 0.0  # ETH derivatives don't have BTC exposure
            }
        
        elif asset.startswith('a'):  # AAVE tokens
            if self.debug_mode:
                logger.info(f"Exposure Monitor: Processing AAVE token {asset} with balance {balance}")
            try:
                result = self._calculate_aave_token_exposure(asset, balance, market_data, venue)
                if self.debug_mode:
                    logger.info(f"Exposure Monitor: AAVE token {asset} result = {result}")
                return result
            except Exception as e:
                logger.error(f"Exposure Monitor: Error calculating AAVE token {asset} exposure: {e}")
                raise
        
        elif asset.startswith('variableDebt'):  # AAVE debt tokens
            return self._calculate_aave_debt_exposure(asset, balance, market_data, venue)
        
        else:
            logger.warning(f"Unknown asset type: {asset}")
            return {'exposure_eth': 0.0, 'exposure_usd': 0.0}
    
    def _calculate_perp_exposure(self, asset: str, perp_positions: Dict, market_data: Dict) -> Dict:
        """Calculate perp position exposure for an asset."""
        total_exposure_eth = 0.0
        total_exposure_usd = 0.0
        total_exposure_btc = 0.0
        total_exposure_usdt = 0.0
        total_balance = 0.0
        
        # Debug logging for BTC perp processing
        if asset == 'BTC':
            logger.info(f"Exposure Monitor: BTC perp processing - perp_positions = {perp_positions}")
        
        for venue, positions in perp_positions.items():
            for instrument, position_data in positions.items():
                # Check if this perp position is for our target asset
                if self._is_perp_for_asset(instrument, asset):
                    size = position_data.get('size', 0.0)
                    entry_price = position_data.get('entry_price', 0.0)
                    
                    if asset == 'BTC':
                        logger.info(f"Exposure Monitor: BTC perp found - venue={venue}, instrument={instrument}, size={size}, entry_price={entry_price}")
                    
                    if size != 0:
                        # For BTC and ETH perps, size is already in asset units (1:1 mapping)
                        # For other assets, convert from USD notional to asset units
                        if asset in ["BTC", "ETH"]:
                            asset_units = size  # Direct 1:1 mapping
                        else:
                            asset_price = self._get_asset_price(asset, market_data)
                            if asset_price is None:
                                continue  # Skip if no pricing data
                            asset_units = size / asset_price  # Convert USD notional to asset units
                        
                        total_balance += asset_units
                        
                        # Convert to ETH and USD exposure
                        if asset == "ETH":
                            total_exposure_eth += asset_units
                            total_exposure_usd += asset_units * market_data.get('eth_usd_price', 0)
                        elif asset == "BTC":
                            btc_usd_price = market_data.get('btc_usd_price')
                            eth_usd_price = market_data.get('eth_usd_price')
                            if btc_usd_price and eth_usd_price:
                                total_exposure_eth += asset_units * btc_usd_price / eth_usd_price
                                total_exposure_usd += asset_units * btc_usd_price
                                total_exposure_btc += asset_units  # Direct BTC exposure
                                if asset == 'BTC':
                                    logger.info(f"Exposure Monitor: BTC perp calculation - asset_units={asset_units}, btc_usd_price={btc_usd_price}, eth_usd_price={eth_usd_price}, total_exposure_btc={total_exposure_btc}")
                            else:
                                if asset == 'BTC':
                                    logger.warning(f"Exposure Monitor: BTC perp missing price data - btc_usd_price={btc_usd_price}, eth_usd_price={eth_usd_price}")
                        elif asset == "USDT":
                            # USDT perps are typically short positions
                            total_exposure_usd += asset_units
                            total_exposure_usdt += asset_units  # Direct USDT exposure
                        # Add other assets as needed
        
        if asset == 'BTC':
            logger.info(f"Exposure Monitor: BTC perp result - total_exposure_btc={total_exposure_btc}, total_balance={total_balance}")
        
        return {
            'exposure_eth': total_exposure_eth,
            'exposure_usd': total_exposure_usd,
            'exposure_btc': total_exposure_btc,
            'exposure_usdt': total_exposure_usdt,
            'balance': total_balance
        }
    
    def _is_perp_for_asset(self, instrument: str, asset: str) -> bool:
        """Check if a perp instrument is for the target asset."""
        if asset == "ETH":
            return "ETH" in instrument.upper()
        elif asset == "BTC":
            is_btc_perp = "BTC" in instrument.upper()
            if is_btc_perp:
                logger.info(f"Exposure Monitor: BTC perp detected - instrument={instrument}, asset={asset}")
            return is_btc_perp
        elif asset == "USDT":
            # USDT perps are typically short positions, but we track them for USDT strategies
            return "USDT" in instrument.upper() and "BTC" not in instrument.upper() and "ETH" not in instrument.upper()
        return False
    
    def _get_asset_price(self, asset: str, market_data: Dict) -> Optional[float]:
        """Get current price for an asset."""
        if asset == "ETH":
            return market_data.get('eth_usd_price')
        elif asset == "BTC":
            return market_data.get('btc_usd_price')
        elif asset == "USDT":
            return 1.0  # USDT is always $1
        return None
    
    def _calculate_aave_token_exposure(self, asset: str, balance: float, market_data: Dict, venue: str) -> Dict:
        """Calculate exposure for AAVE tokens (aWeETH, aUSDT, etc.)."""
        if asset == "aWeETH":
            # Use centralized utility for liquidity index and price lookups
            from ...utils.market_data_utils import get_market_data_utils
            market_utils = get_market_data_utils()
            
            try:
                # Try to get liquidity index from data provider first
                liquidity_index = market_utils.get_liquidity_index('weETH', market_data.get('timestamp'))
            except (ValueError, Exception):
                # Fallback to market_data
                liquidity_index = market_utils.get_liquidity_index_from_market_data('weETH', market_data)
            
            oracle_price = market_data.get('weeth_eth_oracle')
            eth_usd_price = market_utils.get_eth_price(market_data)
            
            if liquidity_index is None or oracle_price is None or eth_usd_price is None:
                raise ExposureMonitorError('EXP-004', message="AAVE aWeETH pricing data required", asset=asset, venue=venue)
            
            # Convert aWeETH to underlying weETH using liquidity index
            underlying_weeth = balance * liquidity_index
            return {
                'exposure_eth': underlying_weeth * oracle_price,
                'exposure_usd': underlying_weeth * oracle_price * eth_usd_price,
                'exposure_btc': 0.0,  # ETH derivatives don't have BTC exposure
                'exposure_usdt': 0.0,  # ETH derivatives don't have USDT exposure
                'underlying_balance': underlying_weeth,  # For risk breakdown
                'venue_breakdown': {
                    'on_chain_wallet': 0.0,
                    'cex_spot': 0.0,
                    'cex_perps': 0.0,
                    'aave_tokens': underlying_weeth,
                    'aave_debt': 0.0
                }
            }
        
        elif asset == "aUSDT":
            # Use centralized utility for liquidity index and price lookups
            from ...utils.market_data_utils import get_market_data_utils
            market_utils = get_market_data_utils()
            
            try:
                # Try to get liquidity index from data provider first
                liquidity_index = market_utils.get_liquidity_index('USDT', market_data.get('timestamp'))
            except (ValueError, Exception):
                # Fallback to market_data
                liquidity_index = market_utils.get_liquidity_index_from_market_data('USDT', market_data)
            
            eth_usd_price = market_utils.get_eth_price(market_data)
            
            if self.debug_mode:
                logger.info(f"Exposure Monitor: aUSDT processing - balance: {balance}, liquidity_index: {liquidity_index}, eth_usd_price: {eth_usd_price}")
            
            if liquidity_index is None or eth_usd_price is None:
                raise ExposureMonitorError('EXP-004', message="AAVE aUSDT pricing data required", asset=asset, venue=venue)
            
            # Convert aUSDT to underlying USDT using liquidity index
            underlying_usdt = balance * liquidity_index
            
            if self.debug_mode:
                logger.info(f"Exposure Monitor: aUSDT calculation - balance: {balance}, liquidity_index: {liquidity_index}, underlying_usdt: {underlying_usdt}")
            
            return {
                'exposure_eth': underlying_usdt / eth_usd_price,
                'exposure_usd': underlying_usdt,
                'exposure_btc': 0.0,  # USDT doesn't have BTC exposure
                'exposure_usdt': underlying_usdt,  # Direct USDT exposure
                'underlying_balance': underlying_usdt,  # For risk breakdown and P&L calculation
                'venue_breakdown': {
                    'on_chain_wallet': 0.0,
                    'cex_spot': 0.0,
                    'cex_perps': 0.0,
                    'aave_tokens': underlying_usdt,
                    'aave_debt': 0.0
                }
            }
        
        else:
            logger.warning(f"Unknown AAVE token: {asset}")
            return {'exposure_eth': 0.0, 'exposure_usd': 0.0}
    
    def _calculate_aave_debt_exposure(self, asset: str, balance: float, market_data: Dict, venue: str) -> Dict:
        """Calculate exposure for AAVE debt tokens (negative exposure)."""
        if asset == "variableDebtWETH":
            borrow_index = market_data.get('weth_borrow_index')
            eth_usd_price = market_data.get('eth_usd_price')
            
            if borrow_index is None or eth_usd_price is None:
                raise ExposureMonitorError('EXP-004', message="AAVE debt pricing data required", asset=asset, venue=venue)
            
            # Convert debt token to underlying debt using borrow index
            underlying_debt = balance * borrow_index
            return {
                'exposure_eth': -underlying_debt,  # Negative exposure for debt
                'exposure_usd': -underlying_debt * eth_usd_price,
                'exposure_btc': 0.0,  # ETH debt doesn't have BTC exposure
                'exposure_usdt': 0.0,  # ETH debt doesn't have USDT exposure
                'underlying_balance': underlying_debt,  # For risk breakdown
                'venue_breakdown': {
                    'on_chain_wallet': 0.0,
                    'cex_spot': 0.0,
                    'cex_perps': 0.0,
                    'aave_tokens': 0.0,
                    'aave_debt': underlying_debt  # Positive value for debt amount
                }
            }
        
        else:
            logger.warning(f"Unknown AAVE debt token: {asset}")
            return {'exposure_eth': 0.0, 'exposure_usd': 0.0}
    
    def _calculate_net_deltas(self, exposures: Dict, primary_asset: str, mode: str) -> tuple:
        """Calculate net deltas in share class currency and primary asset currency."""
        net_delta_share_class = 0.0
        net_delta_primary_asset = 0.0
        
        for asset, exp in exposures.items():
            # Only assets in the primary asset class contribute to net delta
            if self._is_asset_in_primary_class(asset, primary_asset, mode):
                # Net delta in share class currency
                if self.share_class == 'USDT':
                    net_delta_share_class += exp.get('exposure_usd', 0.0)
                elif self.share_class == 'ETH':
                    net_delta_share_class += exp.get('exposure_eth', 0.0)
                
                # Net delta in primary asset currency
                if primary_asset == 'BTC':
                    net_delta_primary_asset += exp.get('exposure_btc', 0.0)
                elif primary_asset == 'ETH':
                    net_delta_primary_asset += exp.get('exposure_eth', 0.0)
                elif primary_asset == 'USDT':
                    net_delta_primary_asset += exp.get('exposure_usdt', 0.0)
        
        return net_delta_share_class, net_delta_primary_asset
    
    def _is_asset_in_primary_class(self, asset: str, primary_asset: str, mode: str) -> bool:
        """Check if an asset belongs to the primary asset class for net delta calculation."""
        if primary_asset == 'BTC':
            # For BTC strategies, only BTC and its derivatives contribute to net delta
            # USDT is tracked but NOT included in delta (USDT share class is neutral to USDT)
            return asset in ['BTC', 'BTCUSDT']  # Add more BTC derivatives as needed
        elif primary_asset == 'ETH':
            # For ETH strategies, only ETH and its derivatives contribute to net delta
            # USDT is tracked but NOT included in delta (ETH share class is neutral to USDT)
            return asset in ['ETH', 'weETH', 'wstETH', 'aWeETH', 'variableDebtWETH']
        elif primary_asset == 'USDT':
            # For USDT strategies, only USDT and its derivatives contribute to net delta
            # ETH, BTC are tracked but NOT included in delta (USDT share class is neutral to ETH/BTC)
            return asset in ['USDT', 'aUSDT']
        else:
            # Default: only the primary asset itself
            return asset == primary_asset
    
    def _calculate_venue_net_delta(self, exposures: Dict, venue: str, primary_asset: str, mode: str) -> float:
        """Calculate net delta for a specific venue in share class currency."""
        venue_net_delta = 0.0
        
        for asset, exp in exposures.items():
            if self._is_asset_in_primary_class(asset, primary_asset, mode):
                venue_breakdown = exp.get('venue_breakdown', {})
                venue_amount = venue_breakdown.get(venue, 0.0)
                
                if venue_amount != 0:
                    # Convert venue amount to share class currency
                    if self.share_class == 'USDT':
                        # Convert to USD
                        if asset == 'ETH':
                            eth_usd_price = exp.get('exposure_usd', 0.0) / max(exp.get('exposure_eth', 1.0), 1e-10)
                            venue_net_delta += venue_amount * eth_usd_price
                        elif asset == 'BTC':
                            btc_usd_price = exp.get('exposure_usd', 0.0) / max(exp.get('exposure_btc', 1.0), 1e-10)
                            venue_net_delta += venue_amount * btc_usd_price
                        elif asset == 'USDT':
                            venue_net_delta += venue_amount
                    elif self.share_class == 'ETH':
                        # Convert to ETH
                        if asset == 'ETH':
                            venue_net_delta += venue_amount
                        elif asset == 'BTC':
                            btc_eth_ratio = exp.get('exposure_eth', 0.0) / max(exp.get('exposure_btc', 1.0), 1e-10)
                            venue_net_delta += venue_amount * btc_eth_ratio
                        elif asset == 'USDT':
                            usdt_eth_ratio = exp.get('exposure_eth', 0.0) / max(exp.get('exposure_usd', 1.0), 1e-10)
                            venue_net_delta += venue_amount * usdt_eth_ratio
        
        return venue_net_delta
    
    def _calculate_risk_breakdown(self, exposures: Dict, primary_asset: str, mode: str, market_data: Dict) -> Dict:
        """
        Calculate comprehensive risk breakdown per venue for Risk Monitor consumption.
        
        Returns:
            Dict with venue-specific risk data including:
            - aave: AAVE protocol positions (collateral, debt, LTV)
            - on_chain_wallet: On-chain wallet positions
            - cex: CEX positions (spot, perps, margin)
        """
        # Initialize risk breakdown with all required fields
        risk_breakdown = {
            'aave': {
                'collateral': {
                    'raw_balances': {},  # Scaled balances from wallet
                    'underlying_balances': {},  # Converted using indices
                    'exposure_usd': 0.0,
                    'exposure_eth': 0.0,
                    'exposure_btc': 0.0,
                    'exposure_usdt': 0.0,
                    'exposure_primary_asset': 0.0,
                    'tokens': []  # List of collateral tokens
                },
                'debt': {
                    'raw_balances': {},  # Scaled debt balances
                    'underlying_balances': {},  # Converted using borrow indices
                    'exposure_usd': 0.0,
                    'exposure_eth': 0.0,
                    'exposure_btc': 0.0,
                    'exposure_usdt': 0.0,
                    'exposure_primary_asset': 0.0,
                    'tokens': []  # List of debt tokens
                },
                'ltv': 0.0,  # Loan-to-Value ratio
                'health_factor': 0.0,  # AAVE health factor
                'available_borrow': 0.0,  # Available borrow capacity
                'gross_exposure_usd': 0.0,  # Total collateral value
                'net_exposure_usd': 0.0  # Collateral - Debt
            },
            'on_chain_wallet': {
                'raw_balances': {},  # Native token balances
                'exposure_usd': 0.0,
                'exposure_eth': 0.0,
                'exposure_btc': 0.0,
                'exposure_usdt': 0.0,
                'exposure_primary_asset': 0.0,
                'tokens': []  # List of tokens
            },
            'cex': {
                'spot': {
                    'raw_balances': {},  # Spot balances per venue
                    'exposure_usd': 0.0,
                    'exposure_eth': 0.0,
                    'exposure_btc': 0.0,
                    'exposure_usdt': 0.0,
                    'exposure_primary_asset': 0.0,
                    'tokens': [],  # List of tokens
                    'venues': {}  # Per-venue breakdown
                },
                'perps': {
                    'raw_positions': {},  # Perp positions per venue
                    'exposure_usd': 0.0,
                    'exposure_eth': 0.0,
                    'exposure_btc': 0.0,
                    'exposure_usdt': 0.0,
                    'exposure_primary_asset': 0.0,
                    'tokens': [],  # List of tokens
                    'venues': {}  # Per-venue breakdown
                },
                'margin': {
                    'raw_balances': {},  # Margin balances
                    'exposure_usd': 0.0,
                    'exposure_eth': 0.0,
                    'exposure_btc': 0.0,
                    'exposure_usdt': 0.0,
                    'exposure_primary_asset': 0.0,
                    'tokens': [],  # List of tokens
                    'venues': {}  # Per-venue breakdown
                },
                'gross_exposure_usd': 0.0,  # Total CEX exposure
                'net_exposure_usd': 0.0  # Net CEX exposure
            }
        }
        
        # Process each asset exposure
        for asset, exp in exposures.items():
            venue_breakdown = exp.get('venue_breakdown', {})
            balance = exp.get('balance', 0.0)
            exposure_eth = exp.get('exposure_eth', 0.0)
            exposure_usd = exp.get('exposure_usd', 0.0)
            exposure_btc = exp.get('exposure_btc', 0.0)
            exposure_usdt = exp.get('exposure_usdt', 0.0)
            
            # Determine primary asset exposure
            if primary_asset == 'BTC':
                exposure_primary_asset = exposure_btc
            elif primary_asset == 'ETH':
                exposure_primary_asset = exposure_eth
            elif primary_asset == 'USDT':
                exposure_primary_asset = exposure_usdt
            else:
                exposure_primary_asset = exposure_eth  # Default to ETH
            
            # Categorize by venue type
            if asset.startswith('a') and asset != 'aUSDT':  # AAVE collateral tokens
                risk_breakdown['aave']['collateral']['raw_balances'][asset] = balance
                # Get underlying balance from exposure calculation
                underlying_balance = exp.get('underlying_balance', balance)
                risk_breakdown['aave']['collateral']['underlying_balances'][asset] = underlying_balance
                risk_breakdown['aave']['collateral']['exposure_usd'] += exposure_usd
                risk_breakdown['aave']['collateral']['exposure_eth'] += exposure_eth
                risk_breakdown['aave']['collateral']['exposure_btc'] += exposure_btc
                risk_breakdown['aave']['collateral']['exposure_usdt'] += exposure_usdt
                risk_breakdown['aave']['collateral']['exposure_primary_asset'] += exposure_primary_asset
                risk_breakdown['aave']['collateral']['tokens'].append(asset)
                
            elif asset.startswith('variableDebt'):  # AAVE debt tokens
                risk_breakdown['aave']['debt']['raw_balances'][asset] = balance
                # Get underlying balance from exposure calculation
                underlying_balance = exp.get('underlying_balance', balance)
                risk_breakdown['aave']['debt']['underlying_balances'][asset] = underlying_balance
                risk_breakdown['aave']['debt']['exposure_usd'] += abs(exposure_usd)  # Debt is negative
                risk_breakdown['aave']['debt']['exposure_eth'] += abs(exposure_eth)  # Debt is negative
                risk_breakdown['aave']['debt']['exposure_btc'] += abs(exposure_btc)  # Debt is negative
                risk_breakdown['aave']['debt']['exposure_usdt'] += abs(exposure_usdt)  # Debt is negative
                risk_breakdown['aave']['debt']['exposure_primary_asset'] += abs(exposure_primary_asset)  # Debt is negative
                risk_breakdown['aave']['debt']['tokens'].append(asset)
                
            elif asset == 'aUSDT':  # AAVE USDT lending (collateral for USDT strategies)
                underlying_balance = exp.get('underlying_balance', balance)
                if primary_asset == 'USDT':
                    risk_breakdown['aave']['collateral']['raw_balances'][asset] = balance
                    risk_breakdown['aave']['collateral']['underlying_balances'][asset] = underlying_balance
                    risk_breakdown['aave']['collateral']['exposure_usd'] += exposure_usd
                    risk_breakdown['aave']['collateral']['exposure_eth'] += exposure_eth
                    risk_breakdown['aave']['collateral']['exposure_btc'] += exposure_btc
                    risk_breakdown['aave']['collateral']['exposure_usdt'] += exposure_usdt
                    risk_breakdown['aave']['collateral']['exposure_primary_asset'] += exposure_primary_asset
                    risk_breakdown['aave']['collateral']['tokens'].append(asset)
                else:
                    # For non-USDT strategies, aUSDT is debt
                    risk_breakdown['aave']['debt']['raw_balances'][asset] = balance
                    risk_breakdown['aave']['debt']['underlying_balances'][asset] = underlying_balance
                    risk_breakdown['aave']['debt']['exposure_usd'] += abs(exposure_usd)
                    risk_breakdown['aave']['debt']['exposure_eth'] += abs(exposure_eth)
                    risk_breakdown['aave']['debt']['exposure_btc'] += abs(exposure_btc)
                    risk_breakdown['aave']['debt']['exposure_usdt'] += abs(exposure_usdt)
                    risk_breakdown['aave']['debt']['exposure_primary_asset'] += abs(exposure_primary_asset)
                    risk_breakdown['aave']['debt']['tokens'].append(asset)
            
            # On-chain wallet positions (non-AAVE tokens)
            elif asset in ['ETH', 'BTC', 'USDT', 'weETH', 'wstETH']:
                risk_breakdown['on_chain_wallet']['raw_balances'][asset] = balance
                risk_breakdown['on_chain_wallet']['exposure_usd'] += exposure_usd
                risk_breakdown['on_chain_wallet']['exposure_eth'] += exposure_eth
                risk_breakdown['on_chain_wallet']['exposure_btc'] += exposure_btc
                risk_breakdown['on_chain_wallet']['exposure_usdt'] += exposure_usdt
                risk_breakdown['on_chain_wallet']['exposure_primary_asset'] += exposure_primary_asset
                risk_breakdown['on_chain_wallet']['tokens'].append(asset)
        
        # Calculate AAVE metrics
        aave_collateral_usd = risk_breakdown['aave']['collateral']['exposure_usd']
        aave_debt_usd = risk_breakdown['aave']['debt']['exposure_usd']
        
        if aave_collateral_usd > 0:
            risk_breakdown['aave']['ltv'] = (aave_debt_usd / aave_collateral_usd) * 100
            risk_breakdown['aave']['health_factor'] = aave_collateral_usd / max(aave_debt_usd, 1.0)
            risk_breakdown['aave']['available_borrow'] = max(0, aave_collateral_usd * 0.8 - aave_debt_usd)  # 80% LTV max
        
        risk_breakdown['aave']['gross_exposure_usd'] = aave_collateral_usd
        risk_breakdown['aave']['net_exposure_usd'] = aave_collateral_usd - aave_debt_usd
        
        # Process CEX positions from venue breakdown
        for asset, exp in exposures.items():
            venue_breakdown = exp.get('venue_breakdown', {})
            exposure_eth = exp.get('exposure_eth', 0.0)
            exposure_usd = exp.get('exposure_usd', 0.0)
            exposure_btc = exp.get('exposure_btc', 0.0)
            exposure_usdt = exp.get('exposure_usdt', 0.0)
            
            # Determine primary asset exposure
            if primary_asset == 'BTC':
                exposure_primary_asset = exposure_btc
            elif primary_asset == 'ETH':
                exposure_primary_asset = exposure_eth
            elif primary_asset == 'USDT':
                exposure_primary_asset = exposure_usdt
            else:
                exposure_primary_asset = exposure_eth
            
            # CEX spot positions
            cex_spot = venue_breakdown.get('cex_spot', 0.0)
            if cex_spot != 0:
                risk_breakdown['cex']['spot']['raw_balances'][asset] = cex_spot
                risk_breakdown['cex']['spot']['exposure_usd'] += exposure_usd
                risk_breakdown['cex']['spot']['exposure_eth'] += exposure_eth
                risk_breakdown['cex']['spot']['exposure_btc'] += exposure_btc
                risk_breakdown['cex']['spot']['exposure_usdt'] += exposure_usdt
                risk_breakdown['cex']['spot']['exposure_primary_asset'] += exposure_primary_asset
                if asset not in risk_breakdown['cex']['spot']['tokens']:
                    risk_breakdown['cex']['spot']['tokens'].append(asset)
            
            # CEX perp positions
            cex_perps = venue_breakdown.get('cex_perps', 0.0)
            if cex_perps != 0:
                risk_breakdown['cex']['perps']['raw_positions'][asset] = cex_perps
                risk_breakdown['cex']['perps']['exposure_usd'] += exposure_usd
                risk_breakdown['cex']['perps']['exposure_eth'] += exposure_eth
                risk_breakdown['cex']['perps']['exposure_btc'] += exposure_btc
                risk_breakdown['cex']['perps']['exposure_usdt'] += exposure_usdt
                risk_breakdown['cex']['perps']['exposure_primary_asset'] += exposure_primary_asset
                if asset not in risk_breakdown['cex']['perps']['tokens']:
                    risk_breakdown['cex']['perps']['tokens'].append(asset)
        
        # Calculate CEX totals
        risk_breakdown['cex']['gross_exposure_usd'] = (
            risk_breakdown['cex']['spot']['exposure_usd'] + 
            risk_breakdown['cex']['perps']['exposure_usd'] + 
            risk_breakdown['cex']['margin']['exposure_usd']
        )
        risk_breakdown['cex']['net_exposure_usd'] = risk_breakdown['cex']['gross_exposure_usd']  # For now, same as gross
        
        return risk_breakdown
    
    def calculate_exposure(self, timestamp: pd.Timestamp, position_snapshot: Dict = None, market_data: Dict = None) -> Dict:
        """
        Calculate exposure from current positions.
        
        Args:
            timestamp: Current timestamp
            position_snapshot: Position data (if None, gets from position_monitor)
            market_data: Market data (if None, gets from data_provider)
        
        Returns:
            Complete exposure breakdown with net deltas by asset
        """
        try:
            # Fail fast validation
            logger.info(f"Exposure Monitor: position_snapshot type = {type(position_snapshot)}, is None = {position_snapshot is None}")
            if position_snapshot is not None:
                logger.info(f"Exposure Monitor: position_snapshot keys = {list(position_snapshot.keys())}")
            
            if position_snapshot is None:
                raise ExposureMonitorError('EXP-001', message="Position snapshot is required")
            
            if market_data is None:
                raise ExposureMonitorError('EXP-002', message="Market data is required")
            
            if self.debug_mode:
                logger.info(f"Exposure Monitor: Market data keys = {list(market_data.keys())}")
                logger.info(f"Exposure Monitor: usdt_liquidity_index = {market_data.get('usdt_liquidity_index')}")
            
            # Validate timestamp
            if not isinstance(timestamp, pd.Timestamp):
                raise ExposureMonitorError('EXP-003', message="Invalid timestamp format")
            
            # Get mode from config to determine which assets to track
            mode = self.config.get('mode')
            if not mode:
                raise ExposureMonitorError('EXP-004', message="Mode configuration is required")
            
            # Get primary asset from mode config
            primary_asset = self.config.get('asset')
            if not primary_asset:
                raise ExposureMonitorError('EXP-004', message="Primary asset configuration is required")
            
            # Calculate exposures per token
            exposures = {}
            
            # Get wallet and CEX positions
            wallet = position_snapshot.get('wallet', {})
            cex_accounts = position_snapshot.get('cex_accounts', {})
            perp_positions = position_snapshot.get('perp_positions', {})
            
            # Determine which assets to track based on mode and share class
            tracked_assets = self._get_tracked_assets(mode, primary_asset)
            
            if self.debug_mode:
                logger.debug(f"Tracked assets for mode {mode}: {tracked_assets}")
                logger.info(f"Exposure Monitor: Wallet balances = {wallet}")
                logger.info(f"Exposure Monitor: CEX accounts structure = {cex_accounts}")
                logger.info(f"Exposure Monitor: Perp positions structure = {perp_positions}")
            
            # Always log tracked assets for debugging
            logger.info(f"Exposure Monitor: Tracking assets {tracked_assets} for mode {mode}")
            
            # Process each tracked asset
            for asset in tracked_assets:
                if self.debug_mode:
                    wallet_balance = wallet.get(asset, 0.0)
                    logger.info(f"Exposure Monitor: Processing asset {asset} with wallet balance {wallet_balance}")
                    
                    # Debug: Show what positions are available for this asset
                    logger.info(f"Exposure Monitor: CEX accounts for {asset}: {[{venue: tokens.get(asset, 0)} for venue, tokens in cex_accounts.items()]}")
                    logger.info(f"Exposure Monitor: Perp positions for {asset}: {perp_positions}")
                
                asset_exposure = self._calculate_asset_exposure(
                    asset=asset,
                    wallet=wallet,
                    cex_accounts=cex_accounts,
                    perp_positions=perp_positions,
                    market_data=market_data,
                    timestamp=timestamp
                )
                
                if asset_exposure:
                    exposures[asset] = asset_exposure
                    if self.debug_mode:
                        logger.info(f"Exposure Monitor: Asset {asset} exposure calculated - underlying_balance: {asset_exposure.get('underlying_balance')}")
                        logger.info(f"Exposure Monitor: Asset {asset} full exposure: {asset_exposure}")
                else:
                    if self.debug_mode:
                        logger.info(f"Exposure Monitor: Asset {asset} returned None exposure - no positions found")
             
            # Legacy code removed - using new comprehensive approach above
            
            # Calculate aggregates using share class and asset class aware approach
            net_delta_share_class, net_delta_primary_asset = self._calculate_net_deltas(
                exposures, primary_asset, mode
            )
            total_value_usd = sum(exp.get('exposure_usd', 0.0) for exp in exposures.values())
            
            # Calculate net delta by venue (share class currency)
            erc20_wallet_net_delta_share_class = self._calculate_venue_net_delta(
                exposures, 'wallet', primary_asset, mode
            )
            cex_wallet_net_delta_share_class = self._calculate_venue_net_delta(
                exposures, 'cex', primary_asset, mode
            )
            
            # Calculate token equity (total value in ETH)
            eth_usd_price = market_data.get('eth_usd_price')
            if eth_usd_price is None:
                raise ExposureMonitorError('EXP-004', message="ETH/USD price required for equity calculation")
            token_equity_eth = total_value_usd / eth_usd_price
            token_equity_usd = total_value_usd
            
            # Calculate comprehensive risk breakdown per venue
            risk_breakdown = self._calculate_risk_breakdown(exposures, primary_asset, mode, market_data)
            
            result = {
                'timestamp': timestamp,
                'share_class': self.share_class,
                'primary_asset': primary_asset,
                'mode': mode,
                'exposures': exposures,
                'net_delta_share_class': net_delta_share_class,
                'net_delta_primary_asset': net_delta_primary_asset,
                'net_delta_pct': (net_delta_share_class / token_equity_eth * 100) if token_equity_eth != 0 else 0,
                'total_value_usd': total_value_usd,
                'total_value_eth': total_value_usd / eth_usd_price,
                'share_class_value': total_value_usd if self.share_class == 'USDT' else total_value_usd / eth_usd_price,
                'erc20_wallet_net_delta_share_class': erc20_wallet_net_delta_share_class,
                'cex_wallet_net_delta_share_class': cex_wallet_net_delta_share_class,
                'token_equity_eth': token_equity_eth,
                'token_equity_usd': token_equity_usd,
                'risk_breakdown': risk_breakdown
            }
            
            # Publish to Redis
            if self.redis:
                try:
                    asyncio.create_task(self._publish_exposure(result))
                except RuntimeError:
                    # No event loop running, skip publishing
                    logger.debug("No event loop running, skipping Redis publish")
            
            logger.debug(f"Exposure calculated: net_delta_share_class={net_delta_share_class:.4f}, total_value_usd=${total_value_usd:,.2f}")
            
            # Debug: Log exposure snapshot if debug mode is enabled
            if self.debug_mode:
                self.log_exposure_snapshot(timestamp, "EXPOSURE_CALCULATION", result)
            
            return result
            
        except ExposureMonitorError:
            # Re-raise our custom errors as-is
            raise
        except Exception as e:
            raise ExposureMonitorError(
                'EXP-005',
                message=f"Position snapshot invalid structure: {e}",
                error=str(e),
                timestamp=timestamp.isoformat()
            )
    
    def _calculate_aave_collateral_exposure(
        self,
        aweeth_scaled: float,
        liquidity_index: float,
        oracle_price: float,
        eth_usd_price: float
    ) -> Dict:
        """
        Calculate AAVE collateral exposure with INDEX-DEPENDENT conversion.
        
        This is THE MOST CRITICAL calculation in the entire system!
        
        Conversion chain:
        1. Scaled balance (wallet.aWeETH) - CONSTANT
        2. × liquidity_index → Underlying weETH (grows from AAVE yield)
        3. × oracle_price → ETH equivalent (grows from base staking)
        4. × eth_usd_price → USD equivalent (changes with ETH price)
        """
        # Step 1: Scaled → Underlying (via AAVE index)
        # Indices in our data are normalized (~1.0, NOT 1e27!)
        weeth_underlying = aweeth_scaled * liquidity_index
        
        # Step 2: Underlying weETH → ETH (via oracle)
        weeth_in_eth = weeth_underlying * oracle_price
        
        # Step 3: ETH → USD (via spot price)
        weeth_in_usd = weeth_in_eth * eth_usd_price
        
        return {
            'wallet_balance_scaled': aweeth_scaled,      # What wallet shows (CONSTANT)
            'underlying_native': weeth_underlying,        # What AAVE sees (GROWS)
            'exposure_eth': weeth_in_eth,                # For delta tracking
            'exposure_usd': weeth_in_usd,                # For P&L (USDT modes)
            'direction': 'LONG',
            
            # Conversion details (for debugging)
            'liquidity_index': liquidity_index,
            'oracle_price': oracle_price,
            'eth_usd_price': eth_usd_price,
            'conversion_chain': f'{aweeth_scaled:.2f} aWeETH → {weeth_underlying:.2f} weETH → {weeth_in_eth:.2f} ETH → ${weeth_in_usd:,.2f}'
        }
    
    def _calculate_aave_usdt_exposure(
        self,
        ausdt_scaled: float,
        liquidity_index: float
    ) -> Dict:
        """
        Calculate AAVE USDT exposure with INDEX-DEPENDENT conversion.
        
        For pure lending mode:
        1. Scaled balance (wallet.aUSDT) - CONSTANT
        2. × liquidity_index → Underlying USDT (grows from AAVE yield)
        3. USDT value stays in USD (no ETH conversion needed)
        """
        # Step 1: Scaled → Underlying (via AAVE index)
        usdt_underlying = ausdt_scaled * liquidity_index
        
        # Step 2: USDT stays in USD (1:1 with USD)
        usdt_in_usd = usdt_underlying
        
        return {
            'wallet_balance_scaled': ausdt_scaled,        # What wallet shows (CONSTANT)
            'underlying_native': usdt_underlying,         # What AAVE sees (GROWS)
            'exposure_eth': usdt_underlying / 3000.0,    # For delta tracking (convert to ETH equivalent)
            'exposure_usd': usdt_in_usd,                 # For P&L (USDT modes)
            'direction': 'LONG',
            
            # Conversion details (for debugging)
            'liquidity_index': liquidity_index,
            'conversion_chain': f'{ausdt_scaled:.2f} aUSDT → {usdt_underlying:.2f} USDT → ${usdt_in_usd:,.2f}'
        }
    
    
    def _calculate_eth_exposure(self, eth_amount: float, eth_usd_price: float) -> Dict:
        """Calculate free ETH exposure."""
        return {
            'balance': eth_amount,
            'exposure_eth': eth_amount,
            'exposure_usd': eth_amount * eth_usd_price,
            'direction': 'LONG' if eth_amount > 0 else 'SHORT'
        }
    
    def _calculate_weeth_exposure(self, weeth_amount: float, oracle_price: float, eth_usd_price: float) -> Dict:
        """Calculate free weETH exposure."""
        weeth_in_eth = weeth_amount * oracle_price
        weeth_in_usd = weeth_in_eth * eth_usd_price
        
        return {
            'balance': weeth_amount,
            'exposure_eth': weeth_in_eth,
            'exposure_usd': weeth_in_usd,
            'direction': 'LONG',
            'oracle_price': oracle_price,
            'eth_usd_price': eth_usd_price
        }
    
    def _calculate_net_delta(self, exposures: Dict) -> float:
        """
        Calculate net delta in ETH.
        
        Net delta = All long ETH - All short ETH
        
        Long ETH:
        - AAVE collateral (aWeETH converted to ETH)
        - Free wallet.ETH (if positive)
        - CEX ETH spot holdings
        
        Short ETH:
        - AAVE debt (variableDebtWETH)
        - Free wallet.ETH (if negative - gas debt)
        - CEX USDT balances (USDT / ETH price)
        - Short perp positions
        """
        long_eth = 0.0
        short_eth = 0.0
        
        for token, exp in exposures.items():
            eth_exposure = exp['exposure_eth']
            
            if exp['direction'] in ['LONG', 'LONG_ETH']:
                long_eth += abs(eth_exposure)
            elif exp['direction'] in ['SHORT', 'SHORT_ETH']:
                short_eth += abs(eth_exposure)
        
        return long_eth - short_eth
    
    def _calculate_total_value(self, exposures: Dict, market_data: Dict) -> float:
        """
        Calculate total portfolio value in USD.
        
        Sum of all assets minus all liabilities.
        """
        # Assets
        total_assets_usd = 0.0
        
        # AAVE collateral
        if 'aWeETH' in exposures:
            total_assets_usd += exposures['aWeETH']['exposure_usd']
        
        # AAVE USDT lending
        if 'aUSDT' in exposures:
            total_assets_usd += exposures['aUSDT']['exposure_usd']
        
        # Free wallet weETH
        if 'wallet_weETH' in exposures:
            total_assets_usd += exposures['wallet_weETH']['exposure_usd']
        
        # CEX balances (USDT + spot holdings)
        for venue in ['binance', 'bybit', 'okx']:
            total_assets_usd += exposures.get(f'{venue}_USDT', {}).get('exposure_usd', 0)
            total_assets_usd += exposures.get(f'{venue}_ETH_spot', {}).get('exposure_usd', 0)
        
        # Free wallet ETH (if positive)
        if 'wallet_ETH' in exposures and exposures['wallet_ETH']['balance'] > 0:
            total_assets_usd += exposures['wallet_ETH']['exposure_usd']
        
        # Liabilities
        total_liabilities_usd = 0.0
        
        # AAVE debt
        if 'variableDebtWETH' in exposures:
            total_liabilities_usd += exposures['variableDebtWETH']['exposure_usd']
        
        # Gas debt (if ETH balance negative)
        if 'wallet_ETH' in exposures and exposures['wallet_ETH']['balance'] < 0:
            gas_debt_usd = abs(exposures['wallet_ETH']['exposure_usd'])
            total_liabilities_usd += gas_debt_usd
        
        # Net value
        total_value_usd = total_assets_usd - total_liabilities_usd
        
        return total_value_usd
    
    def _calculate_erc20_wallet_net_delta(self, exposures: Dict) -> float:
        """Calculate net delta from ERC-20 wallet (on-chain positions)."""
        erc20_delta = 0.0
        
        # AAVE collateral
        if 'aWeETH' in exposures:
            erc20_delta += exposures['aWeETH']['exposure_eth']
        
        # AAVE debt
        if 'variableDebtWETH' in exposures:
            erc20_delta -= exposures['variableDebtWETH']['exposure_eth']
        
        # Free wallet ETH
        if 'wallet_ETH' in exposures:
            erc20_delta += exposures['wallet_ETH']['exposure_eth']
        
        # Free wallet weETH
        if 'wallet_weETH' in exposures:
            erc20_delta += exposures['wallet_weETH']['exposure_eth']
        
        return erc20_delta
    
    def _calculate_cex_wallet_net_delta(self, exposures: Dict) -> float:
        """Calculate net delta from CEX positions (off-chain)."""
        cex_delta = 0.0
        
        # CEX USDT balances (short ETH)
        for venue in ['binance', 'bybit', 'okx']:
            if f'{venue}_USDT' in exposures:
                cex_delta -= exposures[f'{venue}_USDT']['exposure_eth']
        
        # CEX ETH spot holdings (long ETH)
        for venue in ['binance', 'bybit', 'okx']:
            if f'{venue}_ETH_spot' in exposures:
                cex_delta += exposures[f'{venue}_ETH_spot']['exposure_eth']
        
        # Perp positions
        for venue in ['binance', 'bybit', 'okx']:
            for instrument, exp in exposures.items():
                if venue in instrument and 'PERP' in instrument:
                    cex_delta += exp['exposure_eth']
        
        return cex_delta
    
    def _calculate_token_equity_eth(self, exposures: Dict, market_data: Dict) -> float:
        """Calculate token equity in ETH (net assets - debts)."""
        equity_eth = 0.0
        
        # Assets
        if 'aWeETH' in exposures:
            equity_eth += exposures['aWeETH']['exposure_eth']
        
        if 'wallet_weETH' in exposures:
            equity_eth += exposures['wallet_weETH']['exposure_eth']
        
        if 'wallet_ETH' in exposures and exposures['wallet_ETH']['balance'] > 0:
            equity_eth += exposures['wallet_ETH']['exposure_eth']
        
        # CEX balances
        for venue in ['binance', 'bybit', 'okx']:
            if f'{venue}_USDT' in exposures:
                equity_eth += exposures[f'{venue}_USDT']['exposure_eth']
            if f'{venue}_ETH_spot' in exposures:
                equity_eth += exposures[f'{venue}_ETH_spot']['exposure_eth']
        
        # Liabilities
        if 'variableDebtWETH' in exposures:
            equity_eth -= exposures['variableDebtWETH']['exposure_eth']
        
        if 'wallet_ETH' in exposures and exposures['wallet_ETH']['balance'] < 0:
            equity_eth -= abs(exposures['wallet_ETH']['exposure_eth'])
        
        return equity_eth
    
    async def _publish_exposure(self, exposure_data: Dict):
        """Publish exposure data to Redis."""
        try:
            # Store current exposure
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.redis.set,
                'exposure:current',
                json.dumps(exposure_data, default=str)
            )
            
            # Publish update event
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.redis.publish,
                'exposure:calculated',
                json.dumps({
                    'timestamp': exposure_data['timestamp'].isoformat() if hasattr(exposure_data['timestamp'], 'isoformat') else str(exposure_data['timestamp']),
                    'net_delta_share_class': exposure_data['net_delta_share_class'],
                    'total_value_usd': exposure_data['total_value_usd'],
                    'share_class': exposure_data['share_class']
                })
            )
            
        except Exception as e:
            logger.error(f"Error publishing exposure to Redis: {e}")
    
    def get_current_exposure(self) -> Dict:
        """Get current exposure snapshot."""
        try:
            return self.calculate_exposure(timestamp=pd.Timestamp.now())
        except Exception as e:
            logger.error(f"Error getting current exposure: {e}")
            return {}
    
    def get_snapshot(self) -> Dict:
        """Get exposure snapshot (alias for get_current_exposure)."""
        return self.get_current_exposure()
    
    async def subscribe_to_position_updates(self):
        """Subscribe to position updates and recalculate exposure."""
        if not self.redis:
            logger.warning("Redis not available for position updates subscription")
            return
        
        try:
            pubsub = self.redis.pubsub()
            await pubsub.subscribe('position:updated')
            
            logger.info("Subscribed to position updates")
            
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        data = json.loads(message['data'])
                        timestamp = pd.Timestamp(data['timestamp'])
                        
                        # Recalculate exposure
                        exposure = self.calculate_exposure(timestamp)
                        logger.debug(f"Exposure recalculated from position update: net_delta={exposure['net_delta_share_class']:.4f}")
                        
                    except Exception as e:
                        logger.error(f"Error processing position update: {e}")
                        
        except Exception as e:
            logger.error(f"Error in position updates subscription: {e}")

    def log_exposure_snapshot(self, timestamp: pd.Timestamp, trigger: str = "TIMESTEP", exposure_result: Dict = None):
        """Log exposure snapshot to dedicated exposure monitor log file."""
        try:
            if exposure_result is None:
                # Try to get current exposure if not provided
                try:
                    exposure_result = self.calculate_exposure(timestamp)
                except Exception as e:
                    logger.error(f"Could not get current exposure for logging: {e}")
                    return
            
            # Format the log message
            log_message = f"TIMESTEP: {timestamp.isoformat()} | TRIGGER: {trigger} | MODE: {exposure_result.get('mode', 'N/A')} | ASSET: {exposure_result.get('primary_asset', 'N/A')}\n"
            
            # Net deltas
            log_message += f"NET_DELTA_SHARE_CLASS: {exposure_result.get('net_delta_share_class', 0):.6f} {self.share_class}\n"
            log_message += f"NET_DELTA_PRIMARY_ASSET: {exposure_result.get('net_delta_primary_asset', 0):.6f} {exposure_result.get('primary_asset', 'N/A')}\n"
            log_message += f"TOTAL_VALUE_USD: {exposure_result.get('total_value_usd', 0):.2f}\n"
            
            # Token exposures (new comprehensive format)
            exposures = exposure_result.get('exposures', {})
            if exposures:
                log_message += "TOKEN_EXPOSURES:\n"
                for asset, exp in exposures.items():
                    log_message += f"  {asset}: {exp.get('balance', 0):.6f} units, "
                    log_message += f"{exp.get('exposure_eth', 0):.6f} ETH, "
                    log_message += f"${exp.get('exposure_usd', 0):.2f} USD\n"
            else:
                log_message += "TOKEN_EXPOSURES: No exposures\n"
            
            # Venue breakdown
            venue_breakdown = {}
            for asset, exp in exposures.items():
                breakdown = exp.get('venue_breakdown', {})
                for venue, amount in breakdown.items():
                    if amount != 0:
                        if venue not in venue_breakdown:
                            venue_breakdown[venue] = {}
                        venue_breakdown[venue][asset] = amount
            
            if venue_breakdown:
                log_message += "VENUE_BREAKDOWN:\n"
                for venue, assets in venue_breakdown.items():
                    log_message += f"  {venue}: {assets}\n"
            else:
                log_message += "VENUE_BREAKDOWN: No venue data\n"
            
            # Risk breakdown summary - ALWAYS show all levels
            risk_breakdown = exposure_result.get('risk_breakdown', {})
            log_message += "RISK_BREAKDOWN:\n"
            
            # AAVE summary - always show
            aave = risk_breakdown.get('aave', {})
            log_message += f"  AAVE Collateral: ${aave.get('gross_exposure_usd', 0):.2f} USD, LTV: {aave.get('ltv', 0):.2f}%, Health: {aave.get('health_factor', 0):.2f}\n"
            log_message += f"    Tokens: {aave.get('collateral', {}).get('tokens', [])}\n"
            log_message += f"    Raw Balances: {aave.get('collateral', {}).get('raw_balances', {})}\n"
            log_message += f"    Underlying Balances: {aave.get('collateral', {}).get('underlying_balances', {})}\n"
            log_message += f"    Exposure Share Class: {aave.get('collateral', {}).get(f'exposure_{self.share_class.lower()}', 0):.6f} {self.share_class}\n"
            log_message += f"    Exposure Primary Asset: {aave.get('collateral', {}).get('exposure_primary_asset', 0):.6f} {exposure_result.get('primary_asset', 'N/A')}\n"
            
            log_message += f"  AAVE Debt: ${aave.get('debt', {}).get('exposure_usd', 0):.2f} USD\n"
            log_message += f"    Tokens: {aave.get('debt', {}).get('tokens', [])}\n"
            log_message += f"    Raw Balances: {aave.get('debt', {}).get('raw_balances', {})}\n"
            log_message += f"    Underlying Balances: {aave.get('debt', {}).get('underlying_balances', {})}\n"
            log_message += f"    Exposure Share Class: {aave.get('debt', {}).get(f'exposure_{self.share_class.lower()}', 0):.6f} {self.share_class}\n"
            log_message += f"    Exposure Primary Asset: {aave.get('debt', {}).get('exposure_primary_asset', 0):.6f} {exposure_result.get('primary_asset', 'N/A')}\n"
            
            # On-chain wallet summary - always show
            wallet = risk_breakdown.get('on_chain_wallet', {})
            log_message += f"  On-Chain Wallet: ${wallet.get('exposure_usd', 0):.2f} USD\n"
            log_message += f"    Tokens: {wallet.get('tokens', [])}\n"
            log_message += f"    Raw Balances: {wallet.get('raw_balances', {})}\n"
            log_message += f"    Exposure Share Class: {wallet.get(f'exposure_{self.share_class.lower()}', 0):.6f} {self.share_class}\n"
            log_message += f"    Exposure Primary Asset: {wallet.get('exposure_primary_asset', 0):.6f} {exposure_result.get('primary_asset', 'N/A')}\n"
            
            # CEX summary - always show
            cex = risk_breakdown.get('cex', {})
            log_message += f"  CEX Total: ${cex.get('gross_exposure_usd', 0):.2f} USD\n"
            log_message += f"    Spot: {cex.get('spot', {}).get('tokens', [])}\n"
            log_message += f"    Spot Raw Balances: {cex.get('spot', {}).get('raw_balances', {})}\n"
            log_message += f"    Spot Exposure Share Class: {cex.get('spot', {}).get(f'exposure_{self.share_class.lower()}', 0):.6f} {self.share_class}\n"
            log_message += f"    Spot Exposure Primary Asset: {cex.get('spot', {}).get('exposure_primary_asset', 0):.6f} {exposure_result.get('primary_asset', 'N/A')}\n"
            log_message += f"    Perps: {cex.get('perps', {}).get('tokens', [])}\n"
            log_message += f"    Perps Raw Positions: {cex.get('perps', {}).get('raw_positions', {})}\n"
            log_message += f"    Perps Exposure Share Class: {cex.get('perps', {}).get(f'exposure_{self.share_class.lower()}', 0):.6f} {self.share_class}\n"
            log_message += f"    Perps Exposure Primary Asset: {cex.get('perps', {}).get('exposure_primary_asset', 0):.6f} {exposure_result.get('primary_asset', 'N/A')}\n"
            log_message += f"    Margin: {cex.get('margin', {}).get('tokens', [])}\n"
            log_message += f"    Margin Raw Balances: {cex.get('margin', {}).get('raw_balances', {})}\n"
            log_message += f"    Margin Exposure Share Class: {cex.get('margin', {}).get(f'exposure_{self.share_class.lower()}', 0):.6f} {self.share_class}\n"
            log_message += f"    Margin Exposure Primary Asset: {cex.get('margin', {}).get('exposure_primary_asset', 0):.6f} {exposure_result.get('primary_asset', 'N/A')}\n"
            
            log_message += "-" * 80 + "\n"
            
            # Log to dedicated exposure monitor log file
            exposure_logger.info(log_message)
            
        except Exception as e:
            exposure_logger.error(f"Failed to log exposure snapshot: {e}")

