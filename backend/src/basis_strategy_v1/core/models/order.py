"""
Order Model - Unified Order Specification

Unified order specification for all venue types (CEX, DeFi, wallet transfers).
Used by strategies to specify what they want executed.

Reference: docs/ARCHITECTURAL_DECISION_RECORDS.md - ADR-XXX (to be created)
Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Updated execution flow
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Literal, Dict, Any
from enum import Enum
from datetime import datetime


class VenueType(str, Enum):
    """Venue type classification for routing decisions."""
    CEX = "cex"
    DEFI = "defi"
    DEFI_MIDDLEWARE = "defi_middleware"
    WALLET = "wallet"


class OrderOperation(str, Enum):
    """Types of operations that can be executed across venues."""
    
    # CEX operations
    SPOT_TRADE = "spot_trade"
    PERP_TRADE = "perp_trade"
    
    # DeFi operations
    SUPPLY = "supply"
    BORROW = "borrow"
    REPAY = "repay"
    WITHDRAW = "withdraw"
    STAKE = "stake"
    UNSTAKE = "unstake"
    
    # DEX operations
    SWAP = "swap"
    
    # Flash loan operations
    FLASH_BORROW = "flash_borrow"
    FLASH_REPAY = "flash_repay"
    
    # Wallet operations
    TRANSFER = "transfer"


class Order(BaseModel):
    """
    Unified order specification for all venue types.
    
    Used by strategies to specify what they want executed.
    Replaces the previous StrategyAction and instruction block abstractions.
    
    Examples:
        # CEX spot trade
        Order(venue='binance', operation='spot_trade', pair='BTC/USDT', side='BUY', amount=0.5)
        
        # DeFi supply
        Order(venue='aave', operation='supply', token_in='USDT', token_out='aUSDT', amount=10000)
        
        # Wallet transfer
        Order(venue='wallet', operation='transfer', source_venue='wallet', target_venue='binance', token='USDT', amount=5000)
        
        # Atomic flash loan group
        Order(venue='instadapp', operation='flash_borrow', token_out='WETH', amount=10, 
              execution_mode='atomic', atomic_group_id='leverage_1', sequence_in_group=1)
    """
    
    # Core identification
    venue: str = Field(..., description="Venue identifier (binance, aave, etherfi, wallet, etc)")
    operation: OrderOperation = Field(..., description="Operation type")
    
    # Trading parameters (CEX)
    pair: Optional[str] = Field(None, description="Trading pair (BTC/USDT, ETHUSDT)")
    side: Optional[Literal["BUY", "SELL", "LONG", "SHORT"]] = Field(None, description="Trade side")
    amount: float = Field(..., description="Order amount (in base asset units)")
    price: Optional[float] = Field(None, description="Limit price (None for market orders)")
    order_type: Literal["market", "limit"] = Field("market", description="Order type (market or limit)")
    
    # Smart contract parameters (DeFi)
    token_in: Optional[str] = Field(None, description="Input token symbol")
    token_out: Optional[str] = Field(None, description="Output token symbol")
    
    # Transfer parameters (Wallet)
    source_venue: Optional[str] = Field(None, description="Source venue for transfers")
    target_venue: Optional[str] = Field(None, description="Target venue for transfers")
    token: Optional[str] = Field(None, description="Token symbol for transfers")
    
    # Risk management (CEX perps, ML strategies)
    take_profit: Optional[float] = Field(None, description="Take profit price")
    stop_loss: Optional[float] = Field(None, description="Stop loss price")
    
    # Execution coordination
    execution_mode: Literal["sequential", "atomic"] = Field("sequential", description="Sequential or atomic execution")
    atomic_group_id: Optional[str] = Field(None, description="Group ID for atomic bundling")
    sequence_in_group: Optional[int] = Field(None, description="Order sequence within atomic group")
    
    # Metadata
    timestamp_group: str = Field("default", description="Logical grouping for timing/debugging")
    strategy_intent: Optional[str] = Field(None, description="Human-readable strategy intent (entry_full, exit_partial, etc)")
    strategy_id: Optional[str] = Field(None, description="Strategy identifier")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata for the order")
    
    # Additional parameters for specific operations
    ltv_target: Optional[float] = Field(None, description="Target LTV for AAVE operations")
    slippage_tolerance: Optional[float] = Field(None, description="Slippage tolerance for swaps")
    flash_fee_bps: Optional[float] = Field(None, description="Flash loan fee in basis points")
    gas_cost_type: Optional[str] = Field(None, description="Gas cost categorization")
    
    @field_validator('amount')
    @classmethod
    def validate_amount_positive(cls, v):
        """Amount must be positive."""
        if v <= 0:
            raise ValueError("amount must be positive")
        return v
    
    @field_validator('price')
    @classmethod
    def validate_price_positive(cls, v):
        """Price must be positive if provided."""
        if v is not None and v <= 0:
            raise ValueError("price must be positive")
        return v
    
    @model_validator(mode='after')
    def validate_operation_requirements(self):
        """Validate operation-specific requirements."""
        op = self.operation
        
        # CEX trading validation
        if op in [OrderOperation.SPOT_TRADE, OrderOperation.PERP_TRADE]:
            if not self.pair:
                raise ValueError(f"{op} requires 'pair' parameter")
            if not self.side:
                raise ValueError(f"{op} requires 'side' parameter")
        
        # DeFi operation validation
        if op in [OrderOperation.SUPPLY, OrderOperation.STAKE, OrderOperation.SWAP]:
            if not self.token_in:
                raise ValueError(f"{op} requires 'token_in' parameter")
        
        # Transfer validation
        if op == OrderOperation.TRANSFER:
            if not self.source_venue:
                raise ValueError(f"{op} requires 'source_venue' parameter")
            if not self.target_venue:
                raise ValueError(f"{op} requires 'target_venue' parameter")
            if not self.token:
                raise ValueError(f"{op} requires 'token' parameter")
        
        # Atomic execution validation
        if self.execution_mode == 'atomic' and not self.atomic_group_id:
            raise ValueError("atomic_group_id required when execution_mode is atomic")
        
        if self.atomic_group_id and self.sequence_in_group is None:
            raise ValueError("sequence_in_group required when atomic_group_id is provided")
        
        # Risk management validation
        if self.take_profit is not None:
            if self.side == 'LONG' and self.price and self.take_profit <= self.price:
                raise ValueError("take_profit must be higher than entry price for LONG positions")
            elif self.side == 'SHORT' and self.price and self.take_profit >= self.price:
                raise ValueError("take_profit must be lower than entry price for SHORT positions")
        
        if self.stop_loss is not None:
            if self.side == 'LONG' and self.price and self.stop_loss >= self.price:
                raise ValueError("stop_loss must be lower than entry price for LONG positions")
            elif self.side == 'SHORT' and self.price and self.stop_loss <= self.price:
                raise ValueError("stop_loss must be higher than entry price for SHORT positions")
        
        return self
    
    def is_atomic(self) -> bool:
        """Check if this order is part of an atomic group."""
        return self.execution_mode == 'atomic' and self.atomic_group_id is not None
    
    def is_cex_trade(self) -> bool:
        """Check if this is a CEX trading order."""
        return self.operation in [OrderOperation.SPOT_TRADE, OrderOperation.PERP_TRADE]
    
    def is_defi_operation(self) -> bool:
        """Check if this is a DeFi operation."""
        return self.operation in [
            OrderOperation.SUPPLY, OrderOperation.BORROW, OrderOperation.REPAY, 
            OrderOperation.WITHDRAW, OrderOperation.STAKE, OrderOperation.UNSTAKE, 
            OrderOperation.SWAP, OrderOperation.FLASH_BORROW, OrderOperation.FLASH_REPAY
        ]
    
    def is_wallet_transfer(self) -> bool:
        """Check if this is a wallet transfer."""
        return self.operation == OrderOperation.TRANSFER
    
    def get_venue_type(self) -> VenueType:
        """Determine venue type based on venue name."""
        venue_lower = self.venue.lower()
        if venue_lower in ['binance', 'bybit', 'okx']:
            return VenueType.CEX
        elif venue_lower in ['aave', 'morpho', 'etherfi', 'lido']:
            return VenueType.DEFI
        elif venue_lower in ['instadapp', 'uniswap', 'curve']:
            return VenueType.DEFI_MIDDLEWARE
        elif venue_lower == 'wallet':
            return VenueType.WALLET
        else:
            # Default to DEFI for unknown venues
            return VenueType.DEFI
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for interface compatibility."""
        return self.model_dump()
    
    model_config = {
        "use_enum_values": True,
        "validate_assignment": True,
        "extra": "forbid"  # Prevent additional fields
    }
