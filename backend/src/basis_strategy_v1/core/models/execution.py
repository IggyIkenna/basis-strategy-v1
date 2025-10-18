"""
Execution Models - ExecutionHandshake and Related Enums

This module defines the execution result models that replace the legacy Trade model.
ExecutionHandshake represents the result of an operation execution at a venue.

Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Unified Execution Flow
Reference: docs/ARCHITECTURAL_DECISION_RECORDS.md - ADR-059 (Unified Execution Flow)
"""

from enum import Enum
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime


class OperationType(str, Enum):
    """
    All operation types supported across venues.
    
    These operation types cover CEX trades, DeFi operations, transfers,
    and flash loan operations.
    """
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
    SWAP = "swap"
    
    # Flash loan operations
    FLASH_BORROW = "flash_borrow"
    FLASH_REPAY = "flash_repay"
    
    # Transfer operations
    TRANSFER = "transfer"


class ExecutionStatus(str, Enum):
    """
    Execution status for operation results.
    
    Status meanings:
    - CONFIRMED: Operation executed successfully
    - PENDING: Operation submitted but not yet confirmed
    - FAILED: Operation failed to execute
    - ROLLED_BACK: Operation was part of atomic group that failed (all rolled back)
    """
    CONFIRMED = "confirmed"
    PENDING = "pending"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class ExecutionHandshake(BaseModel):
    """
    Execution result from venue interface.
    
    REPLACES the legacy Trade model with a cleaner, more focused interface.
    Contains actual execution results including deltas, fees, and status.
    
    This is the runtime execution result - kept simple for performance.
    For comprehensive logging, use OperationExecutionEvent from domain_events.py
    
    Examples:
        # Successful CEX trade
        ExecutionHandshake(
            operation_id="spot_001",
            status=ExecutionStatus.CONFIRMED,
            actual_deltas={"binance:BaseToken:BTC": 0.5, "binance:BaseToken:USDT": -22500.0},
            execution_details={"executed_price": 45000.0, "executed_amount": 0.5},
            fee_amount=22.5,
            fee_currency="USDT",
            submitted_at=datetime.now(),
            executed_at=datetime.now(),
            simulated=False
        )
        
        # Failed DeFi operation
        ExecutionHandshake(
            operation_id="supply_001",
            status=ExecutionStatus.FAILED,
            actual_deltas={},
            execution_details={},
            error_code="EXEC-001",
            error_message="Insufficient balance",
            submitted_at=datetime.now(),
            simulated=True
        )
    """
    
    # Core identification
    operation_id: str = Field(..., description="Unique operation identifier matching the Order")
    status: ExecutionStatus = Field(..., description="Execution status")
    
    # Execution results (simple runtime format for performance)
    actual_deltas: Dict[str, float] = Field(
        ..., 
        description="Actual position deltas: position_key -> delta_amount (simple dict for runtime)"
    )
    execution_details: Dict[str, Any] = Field(
        ..., 
        description="Venue-specific execution details (price, amount, etc.)"
    )
    
    # Costs
    fee_amount: float = Field(0.0, description="Execution fee amount")
    fee_currency: str = Field("USDT", description="Fee currency")
    
    # Error handling
    error_code: Optional[str] = Field(None, description="Error code if execution failed")
    error_message: Optional[str] = Field(None, description="Error message if execution failed")
    
    # Timing
    submitted_at: datetime = Field(..., description="When operation was submitted to venue")
    executed_at: Optional[datetime] = Field(None, description="When operation was executed (None if failed)")
    
    # Venue metadata
    venue_metadata: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Additional venue-specific metadata"
    )
    
    # Mode indicator
    simulated: bool = Field(False, description="True if backtest simulation, False if live execution")
    
    model_config = {
        "use_enum_values": True,
        "validate_assignment": True,
        "extra": "forbid"
    }
    
    def was_successful(self) -> bool:
        """Check if execution was successful."""
        return self.status == ExecutionStatus.CONFIRMED
    
    def was_failed(self) -> bool:
        """Check if execution failed."""
        return self.status == ExecutionStatus.FAILED
    
    def is_pending(self) -> bool:
        """Check if execution is still pending."""
        return self.status == ExecutionStatus.PENDING
    
    def was_rolled_back(self) -> bool:
        """Check if execution was rolled back (atomic group failure)."""
        return self.status == ExecutionStatus.ROLLED_BACK
    
    def get_net_position_change(self) -> Dict[str, float]:
        """Get position deltas (alias for actual_deltas)."""
        return self.actual_deltas.copy()
    
    def get_total_cost(self) -> float:
        """Calculate total cost including fees."""
        # For trades: executed value + fees
        # For transfers/operations: just fees
        executed_value = self.execution_details.get('executed_value', 0.0)
        return executed_value + self.fee_amount

