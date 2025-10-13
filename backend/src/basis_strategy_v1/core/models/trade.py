"""
Trade Model - Execution Summary

Execution summary for completed (or failed) orders.
Returned by venue interfaces after order execution.

Reference: docs/ARCHITECTURAL_DECISION_RECORDS.md - ADR-XXX (to be created)
Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Updated execution flow
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal
from enum import Enum
from datetime import datetime

from .order import Order


class TradeStatus(str, Enum):
    """Execution status for trades."""
    PENDING = "pending"
    EXECUTED = "executed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Trade(BaseModel):
    """
    Execution summary for completed (or failed) orders.
    
    Returned by venue interfaces after order execution.
    Contains all information needed for position monitoring and reconciliation.
    
    Examples:
        # Successful CEX trade
        Trade(
            order=Order(venue='binance', operation='spot_trade', pair='BTC/USDT', side='BUY', amount=0.5),
            status='executed',
            trade_id='binance_12345',
            executed_amount=0.5,
            executed_price=45000.0,
            position_deltas={'BTC': 0.5, 'USDT': -22500.0},
            fee_amount=22.5,
            fee_currency='USDT'
        )
        
        # Failed DeFi operation
        Trade(
            order=Order(venue='aave', operation='supply', token_in='USDT', amount=10000),
            status='failed',
            error_code='INSUFFICIENT_BALANCE',
            error_message='Not enough USDT balance'
        )
    """
    
    # Order reference
    order: Order = Field(..., description="Original order specification")
    
    # Execution results
    status: TradeStatus = Field(..., description="Execution status")
    trade_id: Optional[str] = Field(None, description="Venue-specific trade ID")
    
    # Actual execution details
    executed_amount: float = Field(0.0, description="Actually executed amount")
    executed_price: Optional[float] = Field(None, description="Average execution price")
    
    # Position deltas (for position monitor updates)
    position_deltas: Dict[str, float] = Field(default_factory=dict, description="Net position changes by asset")
    
    # Costs and fees
    fee_amount: float = Field(0.0, description="Trading/gas fee amount")
    fee_currency: str = Field("USDT", description="Fee currency")
    slippage: Optional[float] = Field(None, description="Actual slippage (executed - expected price)")
    
    # Timing
    submitted_at: datetime = Field(default_factory=datetime.now, description="When order was submitted")
    executed_at: Optional[datetime] = Field(None, description="When order was executed")
    
    # Error handling
    error_code: Optional[str] = Field(None, description="Error code if failed")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    # Venue-specific metadata
    venue_metadata: Dict[str, Any] = Field(default_factory=dict, description="Venue-specific execution details")
    
    # Backtest vs Live
    simulated: bool = Field(False, description="True if backtest simulation")
    
    model_config = {
        "use_enum_values": True,
        "validate_assignment": True,
        "extra": "forbid"  # Prevent additional fields
    }
    
    def was_successful(self) -> bool:
        """Check if trade executed successfully."""
        return self.status == TradeStatus.EXECUTED
    
    def was_failed(self) -> bool:
        """Check if trade failed."""
        return self.status == TradeStatus.FAILED
    
    def is_pending(self) -> bool:
        """Check if trade is still pending."""
        return self.status == TradeStatus.PENDING
    
    def to_position_delta(self) -> Dict[str, float]:
        """Extract position deltas for Position Monitor."""
        return self.position_deltas.copy()
    
    def get_net_cost(self) -> float:
        """Calculate net cost including fees."""
        if self.order.is_cex_trade():
            # For trades, cost is the executed amount * price + fees
            if self.executed_price:
                return (self.executed_amount * self.executed_price) + self.fee_amount
        elif self.order.is_wallet_transfer():
            # For transfers, cost is just the fee
            return self.fee_amount
        elif self.order.is_defi_operation():
            # For DeFi operations, cost is the gas fee
            return self.fee_amount
        
        return self.fee_amount
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get summary of execution for logging/debugging."""
        return {
            'order_id': f"{self.order.venue}_{self.order.operation}_{self.order.amount}",
            'status': self.status,
            'executed_amount': self.executed_amount,
            'executed_price': self.executed_price,
            'fee_amount': self.fee_amount,
            'fee_currency': self.fee_currency,
            'position_deltas': self.position_deltas,
            'error_code': self.error_code,
            'error_message': self.error_message,
            'simulated': self.simulated
        }
    
    def validate_execution(self) -> bool:
        """Validate that execution results make sense."""
        if self.was_successful():
            # For successful trades, we should have execution details
            if self.executed_amount <= 0:
                return False
            
            # For CEX trades, we should have a price
            if self.order.is_cex_trade() and not self.executed_price:
                return False
            
            # Position deltas should be non-empty for successful trades
            if not self.position_deltas:
                return False
        
        elif self.was_failed():
            # For failed trades, we should have error information
            if not self.error_code or not self.error_message:
                return False
        
        return True
    
    @classmethod
    def create_successful_trade(
        cls,
        order: Order,
        trade_id: str,
        executed_amount: float,
        executed_price: Optional[float] = None,
        position_deltas: Optional[Dict[str, float]] = None,
        fee_amount: float = 0.0,
        fee_currency: str = "USDT",
        slippage: Optional[float] = None,
        venue_metadata: Optional[Dict[str, Any]] = None,
        simulated: bool = False
    ) -> 'Trade':
        """Create a successful trade result."""
        return cls(
            order=order,
            status=TradeStatus.EXECUTED,
            trade_id=trade_id,
            executed_amount=executed_amount,
            executed_price=executed_price,
            position_deltas=position_deltas or {},
            fee_amount=fee_amount,
            fee_currency=fee_currency,
            slippage=slippage,
            executed_at=datetime.now(),
            venue_metadata=venue_metadata or {},
            simulated=simulated
        )
    
    @classmethod
    def create_failed_trade(
        cls,
        order: Order,
        error_code: str,
        error_message: str,
        venue_metadata: Optional[Dict[str, Any]] = None,
        simulated: bool = False
    ) -> 'Trade':
        """Create a failed trade result."""
        return cls(
            order=order,
            status=TradeStatus.FAILED,
            error_code=error_code,
            error_message=error_message,
            venue_metadata=venue_metadata or {},
            simulated=simulated
        )
    
    @classmethod
    def create_pending_trade(
        cls,
        order: Order,
        trade_id: Optional[str] = None,
        venue_metadata: Optional[Dict[str, Any]] = None,
        simulated: bool = False
    ) -> 'Trade':
        """Create a pending trade result."""
        return cls(
            order=order,
            status=TradeStatus.PENDING,
            trade_id=trade_id,
            venue_metadata=venue_metadata or {},
            simulated=simulated
        )
