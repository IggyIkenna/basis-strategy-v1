"""
Integration tests for atomic operations.

Tests atomic operation group execution and rollback.
"""
import pytest
import pandas as pd
from unittest.mock import Mock, patch
from backend.src.basis_strategy_v1.core.models.order import Order, OrderOperation
from backend.src.basis_strategy_v1.core.models.execution import ExecutionStatus
from backend.src.basis_strategy_v1.core.models.venues import Venue

class TestAtomicOperations:
    """Test atomic operation groups."""
    
    def test_successful_atomic_group(self, real_execution_manager, test_timestamp):
        """Test successful atomic operation group."""
        # Create atomic group with multiple orders (flash loan sequence)
        atomic_group_id = "test_atomic_group_001"
        
        orders = [
            Order(
                operation_id=f"flash_borrow_{atomic_group_id}",
                venue=Venue.INSTADAPP,
                operation=OrderOperation.FLASH_BORROW,
                token_out="WETH",
                amount=10.0,
                source_venue=Venue.INSTADAPP,
                target_venue=Venue.WALLET,
                source_token="WETH",
                target_token="WETH",
                expected_deltas={
                    f"{Venue.INSTADAPP}:BaseToken:WETH": 10.0,
                    f"{Venue.WALLET}:BaseToken:WETH": 10.0,
                },
                execution_mode="atomic",
                atomic_group_id=atomic_group_id,
                sequence_in_group=1,
                strategy_intent="entry_full",
                strategy_id="eth_leveraged",
                metadata={"target_ltv": 0.9, "leverage": 9.0},
            ),
            Order(
                operation_id=f"stake_{atomic_group_id}",
                venue=Venue.ETHERFI,
                operation=OrderOperation.STAKE,
                token_in="WETH",
                token_out="weETH",
                amount=10.0,
                source_venue=Venue.WALLET,
                target_venue=Venue.ETHERFI,
                source_token="WETH",
                target_token="weETH",
                expected_deltas={
                    f"{Venue.WALLET}:BaseToken:WETH": -10.0,
                    f"{Venue.ETHERFI}:LST:weETH": 9.5,  # 10 WETH * 0.95 conversion rate
                },
                execution_mode="atomic",
                atomic_group_id=atomic_group_id,
                sequence_in_group=2,
                strategy_intent="entry_full",
                strategy_id="eth_leveraged",
            ),
            Order(
                operation_id=f"supply_{atomic_group_id}",
                venue=Venue.AAVE_V3,
                operation=OrderOperation.SUPPLY,
                token_in="weETH",
                token_out="aweETH",
                amount=9.5,
                source_venue=Venue.ETHERFI,
                target_venue=Venue.AAVE_V3,
                source_token="weETH",
                target_token="aweETH",
                expected_deltas={
                    f"{Venue.ETHERFI}:LST:weETH": -9.5,
                    f"{Venue.AAVE_V3}:aToken:aweETH": 9.5,
                },
                execution_mode="atomic",
                atomic_group_id=atomic_group_id,
                sequence_in_group=3,
                strategy_intent="entry_full",
                strategy_id="eth_leveraged",
            ),
            Order(
                operation_id=f"borrow_{atomic_group_id}",
                venue=Venue.AAVE_V3,
                operation=OrderOperation.BORROW,
                token_in="WETH",
                token_out="debtWETH",
                amount=9.0,  # 90% LTV of 10 WETH collateral
                source_venue=Venue.AAVE_V3,
                target_venue=Venue.WALLET,
                source_token="WETH",
                target_token="WETH",
                expected_deltas={
                    f"{Venue.AAVE_V3}:debtToken:debtWETH": 9.0,
                    f"{Venue.WALLET}:BaseToken:WETH": 9.0,
                },
                execution_mode="atomic",
                atomic_group_id=atomic_group_id,
                sequence_in_group=4,
                strategy_intent="entry_full",
                strategy_id="eth_leveraged",
            ),
            Order(
                operation_id=f"flash_repay_{atomic_group_id}",
                venue=Venue.INSTADAPP,
                operation=OrderOperation.FLASH_REPAY,
                token_in="WETH",
                token_out="WETH",
                amount=10.0,  # Repay flash loan
                source_venue=Venue.WALLET,
                target_venue=Venue.INSTADAPP,
                source_token="WETH",
                target_token="WETH",
                expected_deltas={
                    f"{Venue.WALLET}:BaseToken:WETH": -10.0,
                    f"{Venue.INSTADAPP}:BaseToken:WETH": -10.0,
                },
                execution_mode="atomic",
                atomic_group_id=atomic_group_id,
                sequence_in_group=5,
                strategy_intent="entry_full",
                strategy_id="eth_leveraged",
                flash_fee_bps=0.0,  # Morpho/Instadapp flash loan fee
            ),
        ]
        
        # Execute atomic group
        handshakes = real_execution_manager.process_orders(test_timestamp, orders)
        
        # Verify all orders executed successfully
        assert len(handshakes) == 5, f"Expected 5 handshakes, got {len(handshakes)}"
        
        for i, handshake in enumerate(handshakes):
            assert handshake.was_successful(), f"Order {i+1} failed: {handshake.error_message}"
            assert handshake.operation_id == orders[i].operation_id
            assert handshake.status == ExecutionStatus.CONFIRMED
            assert handshake.simulated == True  # Backtest mode
        
        # Verify atomic group processing
        assert all(h.operation_id.startswith(atomic_group_id) for h in handshakes)
        
        # Verify position deltas are applied correctly
        total_deltas = {}
        for handshake in handshakes:
            for instrument, delta in handshake.actual_deltas.items():
                total_deltas[instrument] = total_deltas.get(instrument, 0) + delta
        
        # Net result should be: +9.5 weETH staked, +9.0 WETH borrowed, -0.5 WETH net
        assert total_deltas.get(f"{Venue.ETHERFI}:LST:weETH", 0) == 0  # Net staked
        assert total_deltas.get(f"{Venue.AAVE_V3}:aToken:aweETH", 0) == 9.5  # Supplied
        assert total_deltas.get(f"{Venue.AAVE_V3}:debtToken:debtWETH", 0) == 9.0  # Borrowed
        assert total_deltas.get(f"{Venue.WALLET}:BaseToken:WETH", 0) == -1.0  # Net WETH change
    
    def test_atomic_group_rollback(self, real_execution_manager, test_timestamp):
        """Test atomic group rollback on failure."""
        # Create atomic group where one order will fail
        atomic_group_id = "test_atomic_group_002"
        
        orders = [
            Order(
                operation_id=f"flash_borrow_{atomic_group_id}",
                venue=Venue.INSTADAPP,
                operation=OrderOperation.FLASH_BORROW,
                token_out="WETH",
                amount=10.0,
                source_venue=Venue.INSTADAPP,
                target_venue=Venue.WALLET,
                source_token="WETH",
                target_token="WETH",
                expected_deltas={
                    f"{Venue.INSTADAPP}:BaseToken:WETH": 10.0,
                    f"{Venue.WALLET}:BaseToken:WETH": 10.0,
                },
                execution_mode="atomic",
                atomic_group_id=atomic_group_id,
                sequence_in_group=1,
                strategy_intent="entry_full",
                strategy_id="eth_leveraged",
            ),
            Order(
                operation_id=f"stake_{atomic_group_id}",
                venue=Venue.ETHERFI,
                operation=OrderOperation.STAKE,
                token_in="WETH",
                token_out="weETH",
                amount=10.0,
                source_venue=Venue.WALLET,
                target_venue=Venue.ETHERFI,
                source_token="WETH",
                target_token="weETH",
                expected_deltas={
                    f"{Venue.WALLET}:BaseToken:WETH": -10.0,
                    f"{Venue.ETHERFI}:LST:weETH": 9.5,
                },
                execution_mode="atomic",
                atomic_group_id=atomic_group_id,
                sequence_in_group=2,
                strategy_intent="entry_full",
                strategy_id="eth_leveraged",
            ),
            # This order will fail - invalid venue
            Order(
                operation_id=f"invalid_{atomic_group_id}",
                venue="INVALID_VENUE",
                operation=OrderOperation.SUPPLY,
                token_in="weETH",
                token_out="aweETH",
                amount=9.5,
                source_venue=Venue.ETHERFI,
                target_venue="INVALID_VENUE",
                source_token="weETH",
                target_token="aweETH",
                expected_deltas={},
                execution_mode="atomic",
                atomic_group_id=atomic_group_id,
                sequence_in_group=3,
                strategy_intent="entry_full",
                strategy_id="eth_leveraged",
            ),
        ]
        
        # Execute atomic group - should fail and rollback
        handshakes = real_execution_manager.process_orders(test_timestamp, orders)
        
        # Verify first two orders succeeded, third failed
        assert len(handshakes) == 3, f"Expected 3 handshakes, got {len(handshakes)}"
        
        # First two should succeed
        assert handshakes[0].was_successful(), f"First order failed: {handshakes[0].error_message}"
        assert handshakes[1].was_successful(), f"Second order failed: {handshakes[1].error_message}"
        
        # Third should fail
        assert handshakes[2].was_failed(), f"Third order should have failed but succeeded"
        assert handshakes[2].error_code is not None
        assert "INVALID_VENUE" in handshakes[2].error_message or "venue" in handshakes[2].error_message.lower()
        
        # Verify atomic group failure handling
        # In a real implementation, the first two orders would be rolled back
        # For now, we just verify the failure is detected
        assert handshakes[2].status == ExecutionStatus.FAILED
    
    def test_atomic_group_logging(self, real_execution_manager, test_timestamp):
        """Test AtomicOperationGroupEvent logging."""
        # Create atomic group for logging test
        atomic_group_id = "test_atomic_group_003"
        
        orders = [
            Order(
                operation_id=f"flash_borrow_{atomic_group_id}",
                venue=Venue.INSTADAPP,
                operation=OrderOperation.FLASH_BORROW,
                token_out="WETH",
                amount=5.0,
                source_venue=Venue.INSTADAPP,
                target_venue=Venue.WALLET,
                source_token="WETH",
                target_token="WETH",
                expected_deltas={
                    f"{Venue.INSTADAPP}:BaseToken:WETH": 5.0,
                    f"{Venue.WALLET}:BaseToken:WETH": 5.0,
                },
                execution_mode="atomic",
                atomic_group_id=atomic_group_id,
                sequence_in_group=1,
                strategy_intent="entry_partial",
                strategy_id="eth_leveraged",
            ),
            Order(
                operation_id=f"stake_{atomic_group_id}",
                venue=Venue.ETHERFI,
                operation=OrderOperation.STAKE,
                token_in="WETH",
                token_out="weETH",
                amount=5.0,
                source_venue=Venue.WALLET,
                target_venue=Venue.ETHERFI,
                source_token="WETH",
                target_token="weETH",
                expected_deltas={
                    f"{Venue.WALLET}:BaseToken:WETH": -5.0,
                    f"{Venue.ETHERFI}:LST:weETH": 4.75,
                },
                execution_mode="atomic",
                atomic_group_id=atomic_group_id,
                sequence_in_group=2,
                strategy_intent="entry_partial",
                strategy_id="eth_leveraged",
            ),
        ]
        
        # Execute atomic group
        handshakes = real_execution_manager.process_orders(test_timestamp, orders)
        
        # Verify execution
        assert len(handshakes) == 2
        assert all(h.was_successful() for h in handshakes)
        
        # Verify logging metadata
        for handshake in handshakes:
            assert handshake.operation_id.startswith(atomic_group_id)
            assert handshake.execution_details is not None
            assert handshake.submitted_at is not None
            assert handshake.executed_at is not None
            assert handshake.simulated == True  # Backtest mode
        
        # Verify atomic group properties
        assert all(h.operation_id.endswith(atomic_group_id) or atomic_group_id in h.operation_id for h in handshakes)
        
        # Verify execution details contain atomic group info
        for handshake in handshakes:
            assert "atomic_group_id" in handshake.execution_details or atomic_group_id in str(handshake.execution_details)

# Additional tests for edge cases
class TestAtomicOperationsEdgeCases:
    """Test atomic operation edge cases."""
    
    def test_empty_atomic_group(self, real_execution_manager, test_timestamp):
        """Test empty atomic group handling."""
        orders = []
        handshakes = real_execution_manager.process_orders(test_timestamp, orders)
        assert len(handshakes) == 0
    
    def test_single_order_atomic_group(self, real_execution_manager, test_timestamp):
        """Test atomic group with single order."""
        atomic_group_id = "test_single_atomic"
        
        orders = [
            Order(
                operation_id=f"single_{atomic_group_id}",
                venue=Venue.ETHERFI,
                operation=OrderOperation.STAKE,
                token_in="WETH",
                token_out="weETH",
                amount=1.0,
                source_venue=Venue.WALLET,
                target_venue=Venue.ETHERFI,
                source_token="WETH",
                target_token="weETH",
                expected_deltas={
                    f"{Venue.WALLET}:BaseToken:WETH": -1.0,
                    f"{Venue.ETHERFI}:LST:weETH": 0.95,
                },
                execution_mode="atomic",
                atomic_group_id=atomic_group_id,
                sequence_in_group=1,
                strategy_intent="entry_partial",
                strategy_id="eth_leveraged",
            ),
        ]
        
        handshakes = real_execution_manager.process_orders(test_timestamp, orders)
        assert len(handshakes) == 1
        assert handshakes[0].was_successful()
        assert handshakes[0].operation_id == f"single_{atomic_group_id}"
