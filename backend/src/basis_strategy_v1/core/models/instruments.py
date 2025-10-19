# Instrument Registry
"""
Canonical instrument definitions with data availability validation

This module provides a comprehensive registry of all instruments used in the
basis-strategy-v1 platform, with strict validation and data availability tracking.
All components must use these canonical instrument keys to ensure consistency.
"""

from dataclasses import dataclass
from typing import Dict, Set, Optional, List
from enum import Enum

from .venues import Venue


class PositionType(str, Enum):
    """Position types from INSTRUMENT_DEFINITIONS.md"""

    BASE_TOKEN = "BaseToken"
    A_TOKEN = "aToken"  # AAVE/Morpho supply positions
    DEBT_TOKEN = "debtToken"  # AAVE/Morpho borrow positions
    LST = "LST"  # Liquid staking tokens (EtherFi, Lido)
    PERP = "Perp"  # Perpetual futures


class InstrumentType(str, Enum):
    """Instrument type classification for equity calculation"""

    ASSET = "asset"  # Owned value (BaseToken, aToken, LST)
    DEBT = "debt"  # Borrowed value (debtToken)
    DERIVATIVE = "derivative"  # Synthetic positions (Perp)


# Position type to instrument type mapping for equity calculation
POSITION_TYPE_TO_INSTRUMENT_TYPE = {
    PositionType.BASE_TOKEN: InstrumentType.ASSET,
    PositionType.A_TOKEN: InstrumentType.ASSET,
    PositionType.LST: InstrumentType.ASSET,
    PositionType.DEBT_TOKEN: InstrumentType.DEBT,
    PositionType.PERP: InstrumentType.DERIVATIVE,
}


def get_instrument_type_from_position_key(position_key: str) -> InstrumentType:
    """
    Get instrument type classification from position key.

    Maps position types to instrument classifications:
    - BaseToken, aToken, LST → 'asset'
    - debtToken → 'debt'
    - Perp → 'derivative'

    Args:
        position_key: Position key in format venue:position_type:symbol

    Returns:
        Instrument type: 'asset', 'debt', 'derivative', or 'unknown'
    """
    try:
        parts = position_key.split(':')
        if len(parts) != 3:
            return InstrumentType.ASSET  # Default to asset for invalid keys

        venue, position_type, symbol = parts

        # Map position type to instrument type
        for pos_type, inst_type in POSITION_TYPE_TO_INSTRUMENT_TYPE.items():
            if position_type == pos_type.value:
                return inst_type

        # Default to asset for unknown position types
        return InstrumentType.ASSET

    except Exception:
        return InstrumentType.ASSET  # Default to asset on error


@dataclass
class InstrumentDefinition:
    """Complete instrument specification with data availability"""

    key: str  # Full position key: venue:position_type:symbol
    venue: str
    position_type: str
    symbol: str
    display_name: str  # User-friendly name for logging
    has_data: bool  # Whether we have CSV data for this instrument
    data_path_pattern: Optional[str]  # CSV file path pattern if has_data=True

    def __post_init__(self):
        # Validate key format
        expected_key = f"{self.venue}:{self.position_type}:{self.symbol}"
        if self.key != expected_key:
            raise ValueError(f"Key mismatch: {self.key} != {expected_key}")

        # Validate venue exists
        if not Venue.validate_venue(self.venue):
            raise ValueError(f"Unknown venue: {self.venue}")


# Canonical Instrument Registry
# Based on data availability from SCRIPTS_DATA_GUIDE.md and INSTRUMENT_DEFINITIONS.md

INSTRUMENTS: Dict[str, InstrumentDefinition] = {
    # ============= WALLET BASE TOKENS =============
    "wallet:BaseToken:USDT": InstrumentDefinition(
        key="wallet:BaseToken:USDT",
        venue="wallet",
        position_type="BaseToken",
        symbol="USDT",
        display_name="Wallet USDT",
        has_data=True,  # USDT is always $1.00
        data_path_pattern=None,  # Hardcoded to 1.0
    ),
    "wallet:BaseToken:ETH": InstrumentDefinition(
        key="wallet:BaseToken:ETH",
        venue="wallet",
        position_type="BaseToken",
        symbol="ETH",
        display_name="Wallet ETH",
        has_data=True,
        data_path_pattern="data/market_data/spot_prices/eth_usd/*.csv",
    ),
    "wallet:BaseToken:BTC": InstrumentDefinition(
        key="wallet:BaseToken:BTC",
        venue="wallet",
        position_type="BaseToken",
        symbol="BTC",
        display_name="Wallet BTC",
        has_data=True,
        data_path_pattern="data/market_data/spot_prices/btc_usd/*.csv",
    ),
    "wallet:BaseToken:WETH": InstrumentDefinition(
        key="wallet:BaseToken:WETH",
        venue="wallet",
        position_type="BaseToken",
        symbol="WETH",
        display_name="Wallet WETH",
        has_data=True,
        data_path_pattern="data/market_data/spot_prices/eth_usd/*.csv",  # WETH = ETH
    ),
    "wallet:BaseToken:EIGEN": InstrumentDefinition(
        key="wallet:BaseToken:EIGEN",
        venue="wallet",
        position_type="BaseToken",
        symbol="EIGEN",
        display_name="Wallet EIGEN (Dust)",
        has_data=True,
        data_path_pattern="data/market_data/spot_prices/protocol_tokens/eigen_eth_ratio_*.csv",
    ),
    "wallet:BaseToken:ETHFI": InstrumentDefinition(
        key="wallet:BaseToken:ETHFI",
        venue="wallet",
        position_type="BaseToken",
        symbol="ETHFI",
        display_name="Wallet ETHFI (Dust)",
        has_data=True,
        data_path_pattern="data/market_data/spot_prices/protocol_tokens/ethfi_eth_ratio_*.csv",
    ),
    # ============= BINANCE SPOT =============
    "binance:BaseToken:USDT": InstrumentDefinition(
        key="binance:BaseToken:USDT",
        venue="binance",
        position_type="BaseToken",
        symbol="USDT",
        display_name="Binance USDT Balance",
        has_data=True,
        data_path_pattern=None,  # Always $1.00
    ),
    "binance:BaseToken:BTC": InstrumentDefinition(
        key="binance:BaseToken:BTC",
        venue="binance",
        position_type="BaseToken",
        symbol="BTC",
        display_name="Binance BTC Spot",
        has_data=True,
        data_path_pattern="data/market_data/spot_prices/btc_usd/binance_BTCUSDT_1h_*.csv",
    ),
    "binance:BaseToken:ETH": InstrumentDefinition(
        key="binance:BaseToken:ETH",
        venue="binance",
        position_type="BaseToken",
        symbol="ETH",
        display_name="Binance ETH Spot",
        has_data=True,
        data_path_pattern="data/market_data/spot_prices/eth_usd/binance_ETHUSDT_1h_*.csv",
    ),
    # ============= BINANCE PERPS =============
    "binance:Perp:BTCUSDT": InstrumentDefinition(
        key="binance:Perp:BTCUSDT",
        venue="binance",
        position_type="Perp",
        symbol="BTCUSDT",
        display_name="Binance BTC Perpetual (USDT-margined)",
        has_data=True,
        data_path_pattern="data/market_data/derivatives/futures_ohlcv/binance_BTCUSDT_perp_1h_*.csv",
    ),
    "binance:Perp:ETHUSDT": InstrumentDefinition(
        key="binance:Perp:ETHUSDT",
        venue="binance",
        position_type="Perp",
        symbol="ETHUSDT",
        display_name="Binance ETH Perpetual (USDT-margined)",
        has_data=True,
        data_path_pattern="data/market_data/derivatives/futures_ohlcv/binance_ETHUSDT_perp_1h_*.csv",
    ),
    # ============= BYBIT =============
    "bybit:BaseToken:USDT": InstrumentDefinition(
        key="bybit:BaseToken:USDT",
        venue="bybit",
        position_type="BaseToken",
        symbol="USDT",
        display_name="Bybit USDT Balance",
        has_data=True,
        data_path_pattern=None,
    ),
    "bybit:Perp:BTCUSDT": InstrumentDefinition(
        key="bybit:Perp:BTCUSDT",
        venue="bybit",
        position_type="Perp",
        symbol="BTCUSDT",
        display_name="Bybit BTC Perpetual (USDT-margined)",
        has_data=True,
        data_path_pattern="data/market_data/derivatives/futures_ohlcv/bybit_BTCUSDT_perp_1h_*.csv",
    ),
    "bybit:Perp:ETHUSDT": InstrumentDefinition(
        key="bybit:Perp:ETHUSDT",
        venue="bybit",
        position_type="Perp",
        symbol="ETHUSDT",
        display_name="Bybit ETH Perpetual (USDT-margined)",
        has_data=True,
        data_path_pattern="data/market_data/derivatives/futures_ohlcv/bybit_ETHUSDT_perp_1h_*.csv",
    ),
    # ============= OKX =============
    "okx:BaseToken:USDT": InstrumentDefinition(
        key="okx:BaseToken:USDT",
        venue="okx",
        position_type="BaseToken",
        symbol="USDT",
        display_name="OKX USDT Balance",
        has_data=True,
        data_path_pattern=None,
    ),
    "okx:Perp:BTCUSDT": InstrumentDefinition(
        key="okx:Perp:BTCUSDT",
        venue="okx",
        position_type="Perp",
        symbol="BTCUSDT",
        display_name="OKX BTC Perpetual (USDT-margined)",
        has_data=True,
        data_path_pattern="data/market_data/derivatives/futures_ohlcv/binance_BTCUSDT_perp_1h_*.csv",  # Uses Binance data
    ),
    "okx:Perp:ETHUSDT": InstrumentDefinition(
        key="okx:Perp:ETHUSDT",
        venue="okx",
        position_type="Perp",
        symbol="ETHUSDT",
        display_name="OKX ETH Perpetual (USDT-margined)",
        has_data=True,
        data_path_pattern="data/market_data/derivatives/futures_ohlcv/binance_ETHUSDT_perp_1h_*.csv",  # Uses Binance data
    ),
    # ============= AAVE V3 =============
    "aave_v3:aToken:aUSDT": InstrumentDefinition(
        key="aave_v3:aToken:aUSDT",
        venue="aave_v3",
        position_type="aToken",
        symbol="aUSDT",
        display_name="AAVE V3 Supplied USDT",
        has_data=True,
        data_path_pattern="data/protocol_data/aave/rates/aave_v3_aave-v3-ethereum_USDT_rates_*.csv",
    ),
    "aave_v3:debtToken:debtUSDT": InstrumentDefinition(
        key="aave_v3:debtToken:debtUSDT",
        venue="aave_v3",
        position_type="debtToken",
        symbol="debtUSDT",
        display_name="AAVE V3 Borrowed USDT",
        has_data=True,
        data_path_pattern="data/protocol_data/aave/rates/aave_v3_aave-v3-ethereum_USDT_rates_*.csv",
    ),
    "aave_v3:aToken:aWETH": InstrumentDefinition(
        key="aave_v3:aToken:aWETH",
        venue="aave_v3",
        position_type="aToken",
        symbol="aWETH",
        display_name="AAVE V3 Supplied WETH",
        has_data=True,
        data_path_pattern="data/protocol_data/aave/rates/aave_v3_aave-v3-ethereum_WETH_rates_*.csv",
    ),
    "aave_v3:debtToken:debtWETH": InstrumentDefinition(
        key="aave_v3:debtToken:debtWETH",
        venue="aave_v3",
        position_type="debtToken",
        symbol="debtWETH",
        display_name="AAVE V3 Borrowed WETH",
        has_data=True,
        data_path_pattern="data/protocol_data/aave/rates/aave_v3_aave-v3-ethereum_WETH_rates_*.csv",
    ),
    "aave_v3:aToken:aweETH": InstrumentDefinition(
        key="aave_v3:aToken:aweETH",
        venue="aave_v3",
        position_type="aToken",
        symbol="aweETH",
        display_name="AAVE V3 Supplied weETH",
        has_data=True,
        data_path_pattern="data/protocol_data/aave/rates/aave_v3_aave-v3-ethereum_weETH_rates_*.csv",
    ),
    # ============= ETHERFI =============
    "etherfi:LST:weETH": InstrumentDefinition(
        key="etherfi:LST:weETH",
        venue="etherfi",
        position_type="LST",
        symbol="weETH",
        display_name="EtherFi Staked ETH (weETH)",
        has_data=True,
        data_path_pattern="data/protocol_data/aave/oracle/aave_v3_aave-v3-ethereum_weETH_oracle_*.csv",
    ),
    # ============= LIDO =============
    "lido:LST:stETH": InstrumentDefinition(
        key="lido:LST:stETH",
        venue="lido",
        position_type="LST",
        symbol="stETH",
        display_name="Lido Staked ETH (stETH)",
        has_data=True,
        data_path_pattern="data/market_data/spot_prices/lst_eth_ratios/lido_steth_eth_ratio_*.csv",
    ),
    "lido:LST:wstETH": InstrumentDefinition(
        key="lido:LST:wstETH",
        venue="lido",
        position_type="LST",
        symbol="wstETH",
        display_name="Lido Wrapped Staked ETH (wstETH)",
        has_data=True,
        data_path_pattern="data/market_data/spot_prices/lst_eth_ratios/lido_wsteth_eth_ratio_*.csv",
    ),
}


# Validation helpers
def validate_instrument_key(key: str) -> bool:
    """Validate instrument key exists in registry"""
    return key in INSTRUMENTS


def get_instrument(key: str) -> InstrumentDefinition:
    """Get instrument definition with validation"""
    if key not in INSTRUMENTS:
        raise ValueError(
            f"Unknown instrument key: {key}. Must use canonical keys from INSTRUMENTS registry."
        )
    return INSTRUMENTS[key]


def get_display_name(key: str) -> str:
    """Get user-friendly display name for logging"""
    return get_instrument(key).display_name


def has_data_for_instrument(key: str) -> bool:
    """Check if we have CSV data for this instrument"""
    return get_instrument(key).has_data


def get_instruments_by_venue(venue: str) -> List[str]:
    """Get all instrument keys for a specific venue"""
    return [key for key, instrument in INSTRUMENTS.items() if instrument.venue == venue]


def get_instruments_by_position_type(position_type: str) -> List[str]:
    """Get all instrument keys for a specific position type"""
    return [
        key for key, instrument in INSTRUMENTS.items() if instrument.position_type == position_type
    ]


def get_instruments_with_data() -> List[str]:
    """Get all instrument keys that have CSV data available"""
    return [key for key, instrument in INSTRUMENTS.items() if instrument.has_data]


def get_instruments_without_data() -> List[str]:
    """Get all instrument keys that don't have CSV data (live mode only)"""
    return [key for key, instrument in INSTRUMENTS.items() if not instrument.has_data]


def validate_instrument_keys(keys: List[str]) -> None:
    """Validate a list of instrument keys, raising ValueError if any are invalid"""
    invalid_keys = [key for key in keys if not validate_instrument_key(key)]
    if invalid_keys:
        raise ValueError(
            f"Invalid instrument keys: {invalid_keys}. Must use canonical keys from INSTRUMENTS registry."
        )


def validate_instrument_for_venue(instrument_key: str, venue: str) -> bool:
    """Validate that an instrument can exist on a given venue"""
    if instrument_key not in INSTRUMENTS:
        return False
    return INSTRUMENTS[instrument_key].venue == venue


# Convenience constants for common instrument groups
WALLET_INSTRUMENTS = get_instruments_by_venue("wallet")
BINANCE_INSTRUMENTS = get_instruments_by_venue("binance")
BYBIT_INSTRUMENTS = get_instruments_by_venue("bybit")
OKX_INSTRUMENTS = get_instruments_by_venue("okx")
AAVE_INSTRUMENTS = get_instruments_by_venue("aave_v3")
STAKING_INSTRUMENTS = get_instruments_by_position_type("LST")
PERP_INSTRUMENTS = get_instruments_by_position_type("Perp")
BASE_TOKEN_INSTRUMENTS = get_instruments_by_position_type("BaseToken")
INSTRUMENTS_WITH_DATA = get_instruments_with_data()
INSTRUMENTS_WITHOUT_DATA = get_instruments_without_data()


def instrument_key_to_price_key(instrument_key: str) -> str:
    """
    Convert position key to data provider price key.

    Examples:
        wallet:BaseToken:BTC → BTC
        binance:Perp:BTCUSDT → BTC_binance
        etherfi:LST:weETH → weETH

    Returns:
        Uppercase data key for price lookup
    """
    venue, position_type, symbol = instrument_key.split(":")

    if position_type == "BaseToken":
        return symbol  # BTC, ETH, USDT (already uppercase)
    elif position_type == "Perp":
        base = symbol.replace("USDT", "").replace("USD", "").replace("PERP", "")
        return f"{base}_{venue}"  # BTC_binance (uppercase base)
    elif position_type == "LST":
        return symbol  # weETH, wstETH (already proper case)
    elif position_type in ["aToken", "debtToken"]:
        return symbol  # aUSDT, debtWETH (already proper case)
    else:
        raise ValueError(f"Unknown position type: {position_type}")


def instrument_key_to_oracle_pair(instrument_key: str, quote_currency: str = "USD") -> str:
    """
    Convert LST position key to oracle price pair format.

    Examples:
        etherfi:LST:weETH, 'USD' → weETH/USD
        etherfi:LST:weETH, 'ETH' → weETH/ETH
        lido:LST:wstETH, 'USD' → wstETH/USD

    Returns:
        BASE/QUOTE format for oracle price lookup
    """
    venue, position_type, symbol = instrument_key.split(":")

    if position_type != "LST":
        raise ValueError(f"Oracle pairs only for LST positions, got: {position_type}")

    return f"{symbol}/{quote_currency}"


def validate_data_key_format(data_key: str) -> bool:
    """
    Validate data key follows uppercase convention.

    Checks:
    - Asset symbols are uppercase (BTC, ETH, not btc, eth)
    - Venue suffixes use underscore: {ASSET}_{venue}
    - Oracle pairs use slash: {BASE}/{QUOTE}
    """
    # Check for lowercase violations
    if "_" in data_key:
        asset, venue = data_key.split("_", 1)
        if not asset.isupper():
            return False
    elif "/" in data_key:
        base, quote = data_key.split("/", 1)
        # Allow mixed case for LST tokens (weETH, wstETH)
        if not (base[0].islower() or base.isupper()):
            return False
    else:
        # Simple asset - check first char uppercase or lowercase for LST
        if not (data_key[0].isupper() or data_key[0].islower()):
            return False

    return True


def validate_instrument_in_registry(instrument_key: str) -> bool:
    """Validate position key exists in INSTRUMENTS registry."""
    return validate_instrument_key(instrument_key)
