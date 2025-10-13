"""
Unit tests for Trade model functionality and helper methods.

Tests Trade creation, validation, and position delta extraction.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from backend.src.basis_strategy_v1.core.models.order import Order, OrderOperation
from backend.src.basis_strategy_v1.core.models.trade import Trade, TradeStatus


class TestTradeModel:
    """Test Trade model functionality and helper methods."""
    
    def test_successful_cex_trade_creation(self):
        """Test creating a successful CEX trade."""
        order = Order(
            venue='binance',
            operation=OrderOperation.SPOT_TRADE,
            pair='BTC/USDT',
            side='BUY',
            amount=0.5,
            price=45000.0
        )
        
        trade = Trade.create_successful_trade(
            order=order,
            trade_id='binance_12345',
            executed_amount=0.5,
            executed_price=45000.0,
            position_deltas={'BTC': 0.5, 'USDT': -22500.0},
            fee_amount=22.5,
            fee_currency='USDT',
            slippage=0.0
        )
        
        assert trade.order == order
        assert trade.status == TradeStatus.EXECUTED
        assert trade.trade_id == 'binance_12345'
        assert trade.executed_amount == 0.5
        assert trade.executed_price == 45000.0
        assert trade.position_deltas == {'BTC': 0.5, 'USDT': -22500.0}
        assert trade.fee_amount == 22.5
        assert trade.fee_currency == 'USDT'
        assert trade.slippage == 0.0
        assert trade.was_successful() is True
        assert trade.was_failed() is False
        assert trade.is_pending() is False
        assert trade.simulated is False
    
    def test_failed_trade_creation(self):
        """Test creating a failed trade."""
        order = Order(
            venue='aave',
            operation=OrderOperation.SUPPLY,
            token_in='USDT',
            amount=10000.0
        )
        
        trade = Trade.create_failed_trade(
            order=order,
            error_code='INSUFFICIENT_BALANCE',
            error_message='Not enough USDT balance'
        )
        
        assert trade.order == order
        assert trade.status == TradeStatus.FAILED
        assert trade.error_code == 'INSUFFICIENT_BALANCE'
        assert trade.error_message == 'Not enough USDT balance'
        assert trade.was_successful() is False
        assert trade.was_failed() is True
        assert trade.is_pending() is False
    
    def test_pending_trade_creation(self):
        """Test creating a pending trade."""
        order = Order(
            venue='binance',
            operation=OrderOperation.PERP_TRADE,
            pair='BTCUSDT',
            side='SHORT',
            amount=1.0
        )
        
        trade = Trade.create_pending_trade(
            order=order,
            trade_id='binance_pending_123'
        )
        
        assert trade.order == order
        assert trade.status == TradeStatus.PENDING
        assert trade.trade_id == 'binance_pending_123'
        assert trade.was_successful() is False
        assert trade.was_failed() is False
        assert trade.is_pending() is True
    
    def test_backtest_simulated_trade(self):
        """Test creating a simulated trade for backtest."""
        order = Order(
            venue='binance',
            operation=OrderOperation.SPOT_TRADE,
            pair='BTC/USDT',
            side='BUY',
            amount=0.5
        )
        
        trade = Trade.create_successful_trade(
            order=order,
            trade_id='sim_12345',
            executed_amount=0.5,
            executed_price=45000.0,
            position_deltas={'BTC': 0.5, 'USDT': -22500.0},
            simulated=True
        )
        
        assert trade.simulated is True
        assert trade.was_successful() is True
    
    def test_position_delta_extraction(self):
        """Test extracting position deltas."""
        order = Order(
            venue='aave',
            operation=OrderOperation.SUPPLY,
            token_in='USDT',
            amount=10000.0
        )
        
        position_deltas = {'USDT': -10000.0, 'aUSDT': 10000.0}
        
        trade = Trade.create_successful_trade(
            order=order,
            trade_id='aave_123',
            executed_amount=10000.0,
            position_deltas=position_deltas
        )
        
        extracted_deltas = trade.to_position_delta()
        assert extracted_deltas == position_deltas
        
        # Ensure it's a copy, not reference
        extracted_deltas['USDT'] = -5000.0
        assert trade.position_deltas['USDT'] == -10000.0  # Original unchanged
    
    def test_net_cost_calculation_cex_trade(self):
        """Test net cost calculation for CEX trades."""
        order = Order(
            venue='binance',
            operation=OrderOperation.SPOT_TRADE,
            pair='BTC/USDT',
            side='BUY',
            amount=0.5,
            price=45000.0
        )
        
        trade = Trade.create_successful_trade(
            order=order,
            trade_id='binance_123',
            executed_amount=0.5,
            executed_price=45000.0,
            fee_amount=22.5
        )
        
        # Net cost = (0.5 * 45000) + 22.5 = 22500 + 22.5 = 22522.5
        expected_cost = (0.5 * 45000.0) + 22.5
        assert trade.get_net_cost() == expected_cost
    
    def test_net_cost_calculation_wallet_transfer(self):
        """Test net cost calculation for wallet transfers."""
        order = Order(
            venue='wallet',
            operation=OrderOperation.TRANSFER,
            source_venue='wallet',
            target_venue='binance',
            token='USDT',
            amount=5000.0
        )
        
        trade = Trade.create_successful_trade(
            order=order,
            trade_id='transfer_123',
            executed_amount=5000.0,
            fee_amount=5.0  # Gas fee
        )
        
        # For transfers, cost is just the fee
        assert trade.get_net_cost() == 5.0
    
    def test_net_cost_calculation_defi_operation(self):
        """Test net cost calculation for DeFi operations."""
        order = Order(
            venue='aave',
            operation=OrderOperation.SUPPLY,
            token_in='USDT',
            amount=10000.0
        )
        
        trade = Trade.create_successful_trade(
            order=order,
            trade_id='aave_123',
            executed_amount=10000.0,
            fee_amount=15.0  # Gas fee
        )
        
        # For DeFi operations, cost is just the gas fee
        assert trade.get_net_cost() == 15.0
    
    def test_execution_summary(self):
        """Test execution summary generation."""
        order = Order(
            venue='binance',
            operation=OrderOperation.SPOT_TRADE,
            pair='BTC/USDT',
            side='BUY',
            amount=0.5,
            price=45000.0
        )
        
        trade = Trade.create_successful_trade(
            order=order,
            trade_id='binance_123',
            executed_amount=0.5,
            executed_price=45000.0,
            position_deltas={'BTC': 0.5, 'USDT': -22500.0},
            fee_amount=22.5
        )
        
        summary = trade.get_execution_summary()
        
        assert summary['order_id'] == 'binance_spot_trade_0.5'
        assert summary['status'] == TradeStatus.EXECUTED
        assert summary['executed_amount'] == 0.5
        assert summary['executed_price'] == 45000.0
        assert summary['fee_amount'] == 22.5
        assert summary['fee_currency'] == 'USDT'
        assert summary['position_deltas'] == {'BTC': 0.5, 'USDT': -22500.0}
        assert summary['error_code'] is None
        assert summary['error_message'] is None
        assert summary['simulated'] is False
    
    def test_execution_validation_successful_trade(self):
        """Test execution validation for successful trades."""
        order = Order(
            venue='binance',
            operation=OrderOperation.SPOT_TRADE,
            pair='BTC/USDT',
            side='BUY',
            amount=0.5
        )
        
        # Valid successful trade
        trade = Trade.create_successful_trade(
            order=order,
            trade_id='binance_123',
            executed_amount=0.5,
            executed_price=45000.0,
            position_deltas={'BTC': 0.5, 'USDT': -22500.0}
        )
        
        assert trade.validate_execution() is True
        
        # Invalid successful trade - no executed amount
        trade_invalid = Trade(
            order=order,
            status=TradeStatus.EXECUTED,
            trade_id='binance_123',
            executed_amount=0.0,  # Invalid
            executed_price=45000.0,
            position_deltas={'BTC': 0.5, 'USDT': -22500.0}
        )
        
        assert trade_invalid.validate_execution() is False
        
        # Invalid successful trade - no price for CEX trade
        trade_no_price = Trade(
            order=order,
            status=TradeStatus.EXECUTED,
            trade_id='binance_123',
            executed_amount=0.5,
            executed_price=None,  # Invalid for CEX trade
            position_deltas={'BTC': 0.5, 'USDT': -22500.0}
        )
        
        assert trade_no_price.validate_execution() is False
        
        # Invalid successful trade - no position deltas
        trade_no_deltas = Trade(
            order=order,
            status=TradeStatus.EXECUTED,
            trade_id='binance_123',
            executed_amount=0.5,
            executed_price=45000.0,
            position_deltas={}  # Invalid
        )
        
        assert trade_no_deltas.validate_execution() is False
    
    def test_execution_validation_failed_trade(self):
        """Test execution validation for failed trades."""
        order = Order(
            venue='aave',
            operation=OrderOperation.SUPPLY,
            token_in='USDT',
            amount=10000.0
        )
        
        # Valid failed trade
        trade = Trade.create_failed_trade(
            order=order,
            error_code='INSUFFICIENT_BALANCE',
            error_message='Not enough USDT balance'
        )
        
        assert trade.validate_execution() is True
        
        # Invalid failed trade - no error code
        trade_no_code = Trade(
            order=order,
            status=TradeStatus.FAILED,
            error_code=None,  # Invalid
            error_message='Not enough USDT balance'
        )
        
        assert trade_no_code.validate_execution() is False
        
        # Invalid failed trade - no error message
        trade_no_message = Trade(
            order=order,
            status=TradeStatus.FAILED,
            error_code='INSUFFICIENT_BALANCE',
            error_message=None  # Invalid
        )
        
        assert trade_no_message.validate_execution() is False
    
    def test_venue_metadata(self):
        """Test venue-specific metadata storage."""
        order = Order(
            venue='binance',
            operation=OrderOperation.SPOT_TRADE,
            pair='BTC/USDT',
            side='BUY',
            amount=0.5
        )
        
        venue_metadata = {
            'binance_order_id': '12345',
            'binance_client_order_id': 'client_123',
            'binance_time_in_force': 'GTC',
            'binance_order_type': 'LIMIT'
        }
        
        trade = Trade.create_successful_trade(
            order=order,
            trade_id='binance_123',
            executed_amount=0.5,
            executed_price=45000.0,
            venue_metadata=venue_metadata
        )
        
        assert trade.venue_metadata == venue_metadata
        assert trade.venue_metadata['binance_order_id'] == '12345'
    
    def test_timing_fields(self):
        """Test timing fields for trade tracking."""
        order = Order(
            venue='binance',
            operation=OrderOperation.SPOT_TRADE,
            pair='BTC/USDT',
            side='BUY',
            amount=0.5
        )
        
        submitted_time = datetime(2024, 1, 1, 12, 0, 0)
        executed_time = datetime(2024, 1, 1, 12, 0, 5)
        
        trade = Trade(
            order=order,
            status=TradeStatus.EXECUTED,
            trade_id='binance_123',
            executed_amount=0.5,
            executed_price=45000.0,
            submitted_at=submitted_time,
            executed_at=executed_time
        )
        
        assert trade.submitted_at == submitted_time
        assert trade.executed_at == executed_time
    
    def test_trade_status_enum(self):
        """Test all TradeStatus enum values."""
        order = Order(
            venue='binance',
            operation=OrderOperation.SPOT_TRADE,
            pair='BTC/USDT',
            side='BUY',
            amount=0.5
        )
        
        # Test all status values
        statuses = [TradeStatus.PENDING, TradeStatus.EXECUTED, TradeStatus.FAILED, TradeStatus.CANCELLED]
        
        for status in statuses:
            trade = Trade(
                order=order,
                status=status,
                trade_id='test_123'
            )
            
            assert trade.status == status
            
            if status == TradeStatus.EXECUTED:
                assert trade.was_successful() is True
                assert trade.was_failed() is False
                assert trade.is_pending() is False
            elif status == TradeStatus.FAILED:
                assert trade.was_successful() is False
                assert trade.was_failed() is True
                assert trade.is_pending() is False
            elif status == TradeStatus.PENDING:
                assert trade.was_successful() is False
                assert trade.was_failed() is False
                assert trade.is_pending() is True
            elif status == TradeStatus.CANCELLED:
                assert trade.was_successful() is False
                assert trade.was_failed() is False
                assert trade.is_pending() is False
    
    def test_slippage_calculation(self):
        """Test slippage calculation and storage."""
        order = Order(
            venue='binance',
            operation=OrderOperation.SPOT_TRADE,
            pair='BTC/USDT',
            side='BUY',
            amount=0.5,
            price=45000.0  # Expected price
        )
        
        trade = Trade.create_successful_trade(
            order=order,
            trade_id='binance_123',
            executed_amount=0.5,
            executed_price=45100.0,  # Actual price (worse)
            slippage=100.0  # 100 USDT worse execution
        )
        
        assert trade.slippage == 100.0
        assert trade.executed_price > order.price  # Worse execution for buy
    
    def test_defi_operation_trade(self):
        """Test DeFi operation trade creation."""
        order = Order(
            venue='aave',
            operation=OrderOperation.SUPPLY,
            token_in='USDT',
            token_out='aUSDT',
            amount=10000.0
        )
        
        trade = Trade.create_successful_trade(
            order=order,
            trade_id='aave_tx_123',
            executed_amount=10000.0,
            position_deltas={'USDT': -10000.0, 'aUSDT': 10000.0},
            fee_amount=15.0,  # Gas fee
            fee_currency='ETH'
        )
        
        assert trade.order.operation == OrderOperation.SUPPLY
        assert trade.executed_amount == 10000.0
        assert trade.position_deltas == {'USDT': -10000.0, 'aUSDT': 10000.0}
        assert trade.fee_currency == 'ETH'
        assert trade.get_net_cost() == 15.0  # Just gas fee
