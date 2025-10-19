"""
Unit tests for ExecutionHandshake model.

Tests the execution result model that replaces Trade.
"""
import pytest
from datetime import datetime
from backend.src.basis_strategy_v1.core.models.execution import (
    ExecutionHandshake,
    ExecutionStatus,
    OperationType
)

class TestExecutionHandshake:
    """Test ExecutionHandshake model validation."""
    
    def test_successful_cex_trade(self):
        """Test successful CEX spot trade execution."""
        handshake = ExecutionHandshake(
            operation_id="spot_001",
            status=ExecutionStatus.CONFIRMED,
            actual_deltas={
                "binance:BaseToken:BTC": 0.5,
                "binance:BaseToken:USDT": -22500.0
            },
            execution_details={
                "executed_price": 45000.0,
                "executed_amount": 0.5
            },
            fee_amount=22.5,
            fee_currency="USDT",
            submitted_at=datetime.now(),
            executed_at=datetime.now(),
            simulated=False
        )
        
        assert handshake.was_successful()
        assert not handshake.was_failed()
        assert handshake.get_total_cost() > 0
    
    def test_failed_defi_operation(self):
        """Test failed DeFi supply operation."""
        handshake = ExecutionHandshake(
            operation_id="supply_001",
            status=ExecutionStatus.FAILED,
            actual_deltas={},
            execution_details={},
            error_code="EXEC-001",
            error_message="Insufficient balance",
            submitted_at=datetime.now(),
            simulated=True
        )
        
        assert handshake.was_failed()
        assert not handshake.was_successful()
        assert handshake.error_code == "EXEC-001"
    
    def test_pending_operation(self):
        """Test pending operation status."""
        handshake = ExecutionHandshake(
            operation_id="pending_001",
            status=ExecutionStatus.PENDING,
            actual_deltas={},
            execution_details={},
            submitted_at=datetime.now(),
            simulated=True
        )
        
        assert handshake.status == ExecutionStatus.PENDING
        assert not handshake.was_successful()
        assert not handshake.was_failed()
    
    def test_rolled_back_operation(self):
        """Test atomic group rollback."""
        handshake = ExecutionHandshake(
            operation_id="rollback_001",
            status=ExecutionStatus.ROLLED_BACK,
            actual_deltas={},
            execution_details={},
            submitted_at=datetime.now(),
            executed_at=datetime.now(),
            simulated=True
        )
        
        assert handshake.status == ExecutionStatus.ROLLED_BACK
        assert not handshake.was_successful()
        assert not handshake.was_failed()

# TODO: Add tests for:
# - validation errors
# - edge cases (zero amounts, negative fees, etc.)
# - simulated vs real execution
# - position delta calculations
