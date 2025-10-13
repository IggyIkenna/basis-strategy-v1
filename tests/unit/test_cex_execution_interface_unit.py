"""Unit tests for CEX Execution Interface."""

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from basis_strategy_v1.core.interfaces.cex_execution_interface import CEXExecutionInterface, ERROR_CODES


class TestCEXExecutionInterface:
    """Test CEX Execution Interface functionality."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for CEX execution interface."""
        return {
            'venues': {
                'binance': {
                    'spot_api_key': 'test_spot_key',
                    'spot_secret_key': 'test_spot_secret',
                    'futures_api_key': 'test_futures_key',
                    'futures_secret_key': 'test_futures_secret'
                },
                'bybit': {
                    'api_key': 'test_bybit_key',
                    'secret_key': 'test_bybit_secret'
                }
            },
            'execution': {
                'max_retries': 3,
                'timeout': 30
            }
        }

    @pytest.fixture
    def cex_interface(self, mock_config):
        """Create CEX execution interface instance."""
        with patch('ccxt.binance'), patch('ccxt.bybit'), patch('ccxt.okx'):
            return CEXExecutionInterface('backtest', mock_config)

    def test_initialization_backtest_mode(self, mock_config):
        """Test CEX execution interface initialization in backtest mode."""
        with patch('ccxt.binance'), patch('ccxt.bybit'), patch('ccxt.okx'):
            interface = CEXExecutionInterface('backtest', mock_config)
            
            assert interface.execution_mode == 'backtest'
            assert interface.config == mock_config
            assert interface.exchange_clients == {}

    def test_initialization_live_mode(self, mock_config):
        """Test CEX execution interface initialization in live mode."""
        with patch('ccxt.binance'), patch('ccxt.bybit'), patch('ccxt.okx'):
            interface = CEXExecutionInterface('live', mock_config)
            
            assert interface.execution_mode == 'live'
            assert interface.config == mock_config

    @pytest.mark.asyncio
    async def test_execute_trade_backtest_mode(self, cex_interface):
        """Test trade execution in backtest mode."""
        trade_data = {
            'venue': 'binance',
            'trade_type': 'SPOT',
            'pair': 'ETH/USDT',
            'side': 'BUY',
            'amount': 1000.0
        }
        market_data = {'ETH': 3000.0}
        
        result = await cex_interface.execute_trade(trade_data, market_data)
        
        assert result['status'] == 'FILLED'
        assert result['execution_mode'] == 'backtest'
        assert 'order_id' in result
        assert result['venue'] == 'binance'
        assert result['symbol'] == 'ETH/USDT'
        assert result['side'] == 'BUY'
        assert result['amount'] == 1000.0

    @pytest.mark.asyncio
    async def test_execute_trade_live_mode(self, mock_config):
        """Test trade execution in live mode."""
        with patch('ccxt.binance'), patch('ccxt.bybit'), patch('ccxt.okx'):
            interface = CEXExecutionInterface('live', mock_config)
            
            trade_data = {
                'venue': 'binance',
                'trade_type': 'SPOT',
                'pair': 'ETH/USDT',
                'side': 'BUY',
                'amount': 1000.0
            }
            market_data = {'ETH': 3000.0}
            
            with patch.object(interface, '_execute_live_trade', new_callable=AsyncMock) as mock_live_trade:
                mock_live_trade.return_value = {
                    'status': 'FILLED',
                    'execution_mode': 'live',
                    'order_id': 'test_order_123'
                }
                
                result = await interface.execute_trade(trade_data, market_data)
                
                assert result['status'] == 'FILLED'
                assert result['execution_mode'] == 'live'
                mock_live_trade.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_trade_binance_spot(self, cex_interface):
        """Test Binance spot trade execution."""
        trade_data = {
            'venue': 'binance',
            'trade_type': 'SPOT',
            'pair': 'ETH/USDT',
            'side': 'BUY',
            'amount': 1000.0
        }
        market_data = {'ETH': 3000.0}
        
        result = await cex_interface.execute_trade(trade_data, market_data)
        
        assert result['status'] == 'FILLED'
        assert result['venue'] == 'binance'

    @pytest.mark.asyncio
    async def test_execute_trade_binance_futures(self, cex_interface):
        """Test Binance futures trade execution."""
        trade_data = {
            'venue': 'binance',
            'trade_type': 'FUTURES',
            'pair': 'ETHUSDT',
            'side': 'SELL',
            'amount': 1000.0,
            'leverage': 10
        }
        market_data = {'ETH': 3000.0}
        
        result = await cex_interface.execute_trade(trade_data, market_data)
        
        assert result['status'] == 'FILLED'
        assert result['venue'] == 'binance'

    @pytest.mark.asyncio
    async def test_execute_trade_bybit_spot(self, cex_interface):
        """Test Bybit spot trade execution."""
        trade_data = {
            'venue': 'bybit',
            'trade_type': 'SPOT',
            'pair': 'ETH/USDT',  # Use standard format to avoid parsing issues
            'side': 'BUY',
            'amount': 1000.0
        }
        market_data = {'ETH': 3000.0}
        
        result = await cex_interface.execute_trade(trade_data, market_data)
        
        assert result['status'] == 'FILLED'
        assert result['venue'] == 'bybit'

    @pytest.mark.asyncio
    async def test_execute_trade_okx_spot(self, cex_interface):
        """Test OKX spot trade execution."""
        trade_data = {
            'venue': 'okx',
            'trade_type': 'SPOT',
            'pair': 'ETH/USDT',  # Use standard format to avoid parsing issues
            'side': 'BUY',
            'amount': 1000.0
        }
        market_data = {'ETH': 3000.0}
        
        result = await cex_interface.execute_trade(trade_data, market_data)
        
        assert result['status'] == 'FILLED'
        assert result['venue'] == 'okx'

    @pytest.mark.asyncio
    async def test_execute_trade_error_handling(self, cex_interface):
        """Test trade execution error handling."""
        trade_data = {
            'venue': 'binance',
            'trade_type': 'SPOT',
            'pair': 'ETH/USDT',
            'side': 'BUY',
            'amount': 1000.0
        }
        market_data = {'ETH': 3000.0}
        
        # Mock an error in the execution
        with patch.object(cex_interface, '_execute_backtest_trade', side_effect=Exception("Execution error")):
            with pytest.raises(Exception, match="Execution error"):
                await cex_interface.execute_trade(trade_data, market_data)

    def test_error_codes_defined(self):
        """Test that all error codes are properly defined."""
        expected_codes = [
            'CEX-IF-001', 'CEX-IF-002', 'CEX-IF-003', 'CEX-IF-004',
            'CEX-IF-005', 'CEX-IF-006', 'CEX-IF-007', 'CEX-IF-008'
        ]
        
        for code in expected_codes:
            assert code in ERROR_CODES
            assert ERROR_CODES[code] is not None
            assert len(ERROR_CODES[code]) > 0

    @pytest.mark.asyncio
    async def test_execute_trade_different_sides(self, cex_interface):
        """Test trade execution with different sides."""
        market_data = {'ETH': 3000.0}
        
        # Test BUY side
        buy_trade = {
            'venue': 'binance',
            'trade_type': 'SPOT',
            'pair': 'ETH/USDT',
            'side': 'BUY',
            'amount': 1000.0
        }
        
        buy_result = await cex_interface.execute_trade(buy_trade, market_data)
        assert buy_result['side'] == 'BUY'
        assert buy_result['amount'] == 1000.0
        
        # Test SELL side
        sell_trade = {
            'venue': 'binance',
            'trade_type': 'SPOT',
            'pair': 'ETH/USDT',
            'side': 'SELL',
            'amount': 500.0
        }
        
        sell_result = await cex_interface.execute_trade(sell_trade, market_data)
        assert sell_result['side'] == 'SELL'
        assert sell_result['amount'] == 500.0

    @pytest.mark.asyncio
    async def test_execute_trade_different_amounts(self, cex_interface):
        """Test trade execution with different amounts."""
        trade_data = {
            'venue': 'binance',
            'trade_type': 'SPOT',
            'pair': 'ETH/USDT',
            'side': 'BUY'
        }
        market_data = {'ETH': 3000.0}
        
        # Test small amount
        small_trade = {**trade_data, 'amount': 0.001}
        small_result = await cex_interface.execute_trade(small_trade, market_data)
        assert small_result['amount'] == 0.001
        
        # Test large amount
        large_trade = {**trade_data, 'amount': 1000000.0}
        large_result = await cex_interface.execute_trade(large_trade, market_data)
        assert large_result['amount'] == 1000000.0

    @pytest.mark.asyncio
    async def test_execute_trade_market_price_handling(self, cex_interface):
        """Test trade execution with different market prices."""
        trade_data = {
            'venue': 'binance',
            'trade_type': 'SPOT',
            'pair': 'ETH/USDT',
            'side': 'BUY',
            'amount': 1000.0
        }
        
        # Test with specific market price
        market_data = {'binance_spot_price': 2500.0}
        result = await cex_interface.execute_trade(trade_data, market_data)
        assert result['market_price'] == 2500.0
        
        # Test with fallback price (the implementation uses eth_usd_price as fallback)
        market_data = {'eth_usd_price': 3500.0}
        result = await cex_interface.execute_trade(trade_data, market_data)
        assert result['market_price'] == 3500.0

    @pytest.mark.asyncio
    async def test_execute_trade_slippage_calculation(self, cex_interface):
        """Test trade execution slippage calculation."""
        trade_data = {
            'venue': 'binance',
            'trade_type': 'SPOT',
            'pair': 'ETH/USDT',
            'side': 'BUY',
            'amount': 1000.0
        }
        market_data = {'ETH': 3000.0}
        
        result = await cex_interface.execute_trade(trade_data, market_data)
        
        # Check that slippage is calculated
        assert 'slippage' in result
        assert 'price' in result
        assert 'market_price' in result
        
        # For BUY orders, fill price should be higher than market price due to slippage
        assert result['price'] >= result['market_price']

    @pytest.mark.asyncio
    async def test_execute_trade_timestamp_generation(self, cex_interface):
        """Test trade execution timestamp generation."""
        trade_data = {
            'venue': 'binance',
            'trade_type': 'SPOT',
            'pair': 'ETH/USDT',
            'side': 'BUY',
            'amount': 1000.0
        }
        market_data = {'ETH': 3000.0}
        
        result = await cex_interface.execute_trade(trade_data, market_data)
        
        # Check that timestamp is generated
        assert 'timestamp' in result
        assert result['timestamp'] is not None

    @pytest.mark.asyncio
    async def test_execute_trade_order_id_generation(self, cex_interface):
        """Test trade execution order ID generation."""
        trade_data = {
            'venue': 'binance',
            'trade_type': 'SPOT',
            'pair': 'ETH/USDT',
            'side': 'BUY',
            'amount': 1000.0
        }
        market_data = {'ETH': 3000.0}
        
        result = await cex_interface.execute_trade(trade_data, market_data)
        
        # Check that order ID is generated
        assert 'order_id' in result
        assert result['order_id'] is not None
        assert 'backtest' in result['order_id']
        assert 'binance' in result['order_id']

    def test_edge_case_zero_amount(self, cex_interface):
        """Test edge case with zero amount."""
        trade_data = {
            'venue': 'binance',
            'trade_type': 'SPOT',
            'pair': 'ETH/USDT',
            'side': 'BUY',
            'amount': 0.0
        }
        market_data = {'ETH': 3000.0}
        
        # Should still execute but with zero amount
        import asyncio
        result = asyncio.run(cex_interface.execute_trade(trade_data, market_data))
        assert result['amount'] == 0.0

    def test_boundary_conditions(self, cex_interface):
        """Test boundary conditions for trade execution."""
        market_data = {'ETH': 3000.0}
        
        # Test minimum valid amount
        trade_data = {
            'venue': 'binance',
            'trade_type': 'SPOT',
            'pair': 'ETH/USDT',
            'side': 'BUY',
            'amount': 0.000001  # Very small amount
        }
        
        import asyncio
        result = asyncio.run(cex_interface.execute_trade(trade_data, market_data))
        assert result['amount'] == 0.000001
        assert result['status'] == 'FILLED'
