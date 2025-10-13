"""Unit tests for OnChain Execution Interface."""

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from basis_strategy_v1.core.interfaces.onchain_execution_interface import OnChainExecutionInterface, ERROR_CODES


class TestOnChainExecutionInterface:
    """Test OnChain Execution Interface functionality."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for OnChain execution interface."""
        return {
            'venues': {
                'aave': {
                    'rpc_url': 'https://eth-mainnet.alchemyapi.io/v2/test',
                    'private_key': 'test_private_key'
                },
                'etherfi': {
                    'rpc_url': 'https://eth-mainnet.alchemyapi.io/v2/test',
                    'private_key': 'test_private_key'
                },
                'lido': {
                    'rpc_url': 'https://eth-mainnet.alchemyapi.io/v2/test',
                    'private_key': 'test_private_key'
                }
            },
            'execution': {
                'max_retries': 3,
                'timeout': 30,
                'gas_limit': 500000
            }
        }

    @pytest.fixture
    def mock_data_provider(self):
        """Mock data provider for OnChain execution interface."""
        return Mock()

    @pytest.fixture
    def onchain_interface(self, mock_config, mock_data_provider):
        """Create OnChain execution interface instance."""
        with patch('web3.Web3'), patch('web3.eth.Eth'):
            return OnChainExecutionInterface('backtest', mock_config, mock_data_provider)

    def test_initialization_backtest_mode(self, mock_config, mock_data_provider):
        """Test OnChain execution interface initialization in backtest mode."""
        with patch('web3.Web3'), patch('web3.eth.Eth'):
            interface = OnChainExecutionInterface('backtest', mock_config, mock_data_provider)
            
            assert interface.execution_mode == 'backtest'
            assert interface.config == mock_config
            assert interface.data_provider == mock_data_provider
            assert interface.web3_clients == {}

    def test_initialization_live_mode(self, mock_config, mock_data_provider):
        """Test OnChain execution interface initialization in live mode."""
        with patch('web3.Web3'), patch('web3.eth.Eth'):
            interface = OnChainExecutionInterface('live', mock_config, mock_data_provider)
            
            assert interface.execution_mode == 'live'
            assert interface.config == mock_config
            assert interface.data_provider == mock_data_provider

    @pytest.mark.asyncio
    async def test_execute_trade_backtest_mode(self, onchain_interface):
        """Test trade execution in backtest mode."""
        trade_data = {
            'operation': 'supply',
            'token': 'USDT',
            'amount': 1000.0,
            'venue': 'aave'
        }
        market_data = {'USDT': 1.0}
        
        result = await onchain_interface.execute_trade(trade_data, market_data)
        
        assert result['status'] == 'SUCCESS'
        assert result['execution_mode'] == 'backtest'
        assert 'transaction_hash' in result
        assert result['venue'] == 'aave'
        assert result['operation'] == 'supply'
        assert result['token'] == 'USDT'
        assert result['amount'] == 1000.0

    @pytest.mark.asyncio
    async def test_execute_trade_live_mode(self, mock_config, mock_data_provider):
        """Test trade execution in live mode."""
        with patch('web3.Web3'), patch('web3.eth.Eth'):
            interface = OnChainExecutionInterface('live', mock_config, mock_data_provider)
            
            trade_data = {
                'operation': 'supply',
                'token': 'USDT',
                'amount': 1000.0,
                'venue': 'aave'
            }
            market_data = {'USDT': 1.0}
            
            with patch.object(interface, '_execute_live_trade', new_callable=AsyncMock) as mock_live_trade:
                mock_live_trade.return_value = {
                    'status': 'SUCCESS',
                    'execution_mode': 'live',
                    'transaction_hash': '0x1234567890abcdef'
                }
                
                result = await interface.execute_trade(trade_data, market_data)
                
                assert result['status'] == 'SUCCESS'
                assert result['execution_mode'] == 'live'
                mock_live_trade.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_trade_aave_supply(self, onchain_interface):
        """Test Aave supply operation."""
        trade_data = {
            'operation': 'supply',
            'token': 'USDT',
            'amount': 1000.0,
            'venue': 'aave'
        }
        market_data = {'USDT': 1.0}
        
        result = await onchain_interface.execute_trade(trade_data, market_data)
        
        assert result['status'] == 'SUCCESS'
        assert result['venue'] == 'aave'
        assert result['operation'] == 'supply'

    @pytest.mark.asyncio
    async def test_execute_trade_aave_borrow(self, onchain_interface):
        """Test Aave borrow operation."""
        trade_data = {
            'operation': 'borrow',
            'token': 'USDT',
            'amount': 500.0,
            'venue': 'aave'
        }
        market_data = {'USDT': 1.0}
        
        result = await onchain_interface.execute_trade(trade_data, market_data)
        
        assert result['status'] == 'SUCCESS'
        assert result['venue'] == 'aave'
        assert result['operation'] == 'borrow'

    @pytest.mark.asyncio
    async def test_execute_trade_etherfi_stake(self, onchain_interface):
        """Test EtherFi stake operation."""
        trade_data = {
            'operation': 'stake',
            'token': 'ETH',
            'amount': 10.0,
            'venue': 'etherfi'
        }
        market_data = {'ETH': 3000.0}
        
        result = await onchain_interface.execute_trade(trade_data, market_data)
        
        assert result['status'] == 'SUCCESS'
        assert result['venue'] == 'etherfi'
        assert result['operation'] == 'stake'

    @pytest.mark.asyncio
    async def test_execute_trade_lido_stake(self, onchain_interface):
        """Test Lido stake operation."""
        trade_data = {
            'operation': 'stake',
            'token': 'ETH',
            'amount': 5.0,
            'venue': 'lido'
        }
        market_data = {'ETH': 3000.0}
        
        result = await onchain_interface.execute_trade(trade_data, market_data)
        
        assert result['status'] == 'SUCCESS'
        assert result['venue'] == 'lido'
        assert result['operation'] == 'stake'

    @pytest.mark.asyncio
    async def test_execute_trade_error_handling(self, onchain_interface):
        """Test trade execution error handling."""
        trade_data = {
            'operation': 'supply',
            'token': 'USDT',
            'amount': 1000.0,
            'venue': 'aave'
        }
        market_data = {'USDT': 1.0}
        
        # Mock an error in the execution
        with patch.object(onchain_interface, '_execute_backtest_trade', side_effect=Exception("Execution error")):
            with pytest.raises(Exception, match="Execution error"):
                await onchain_interface.execute_trade(trade_data, market_data)

    def test_error_codes_defined(self):
        """Test that all error codes are properly defined."""
        expected_codes = [
            'ONCHAIN-IF-001', 'ONCHAIN-IF-002', 'ONCHAIN-IF-003', 'ONCHAIN-IF-004',
            'ONCHAIN-IF-005', 'ONCHAIN-IF-006', 'ONCHAIN-IF-007', 'ONCHAIN-IF-008'
        ]
        
        for code in expected_codes:
            assert code in ERROR_CODES
            assert ERROR_CODES[code] is not None
            assert len(ERROR_CODES[code]) > 0

    @pytest.mark.asyncio
    async def test_execute_trade_different_operations(self, onchain_interface):
        """Test trade execution with different operations."""
        market_data = {'USDT': 1.0}
        
        # Test supply operation
        supply_trade = {
            'operation': 'supply',
            'token': 'USDT',
            'amount': 1000.0,
            'venue': 'aave'
        }
        
        supply_result = await onchain_interface.execute_trade(supply_trade, market_data)
        assert supply_result['operation'] == 'supply'
        
        # Test borrow operation
        borrow_trade = {
            'operation': 'borrow',
            'token': 'USDT',
            'amount': 500.0,
            'venue': 'aave'
        }
        
        borrow_result = await onchain_interface.execute_trade(borrow_trade, market_data)
        assert borrow_result['operation'] == 'borrow'

    @pytest.mark.asyncio
    async def test_execute_trade_different_tokens(self, onchain_interface):
        """Test trade execution with different tokens."""
        trade_data = {
            'operation': 'supply',
            'venue': 'aave'
        }
        
        # Test USDT
        usdt_trade = {**trade_data, 'token': 'USDT', 'amount': 1000.0}
        usdt_result = await onchain_interface.execute_trade(usdt_trade, {'USDT': 1.0})
        assert usdt_result['token'] == 'USDT'
        
        # Test ETH
        eth_trade = {**trade_data, 'token': 'ETH', 'amount': 10.0}
        eth_result = await onchain_interface.execute_trade(eth_trade, {'ETH': 3000.0})
        assert eth_result['token'] == 'ETH'

    @pytest.mark.asyncio
    async def test_execute_trade_different_amounts(self, onchain_interface):
        """Test trade execution with different amounts."""
        trade_data = {
            'operation': 'supply',
            'token': 'USDT',
            'venue': 'aave'
        }
        market_data = {'USDT': 1.0}
        
        # Test small amount
        small_trade = {**trade_data, 'amount': 0.001}
        small_result = await onchain_interface.execute_trade(small_trade, market_data)
        assert small_result['amount'] == 0.001
        
        # Test large amount
        large_trade = {**trade_data, 'amount': 1000000.0}
        large_result = await onchain_interface.execute_trade(large_trade, market_data)
        assert large_result['amount'] == 1000000.0

    @pytest.mark.asyncio
    async def test_execute_trade_gas_estimation(self, onchain_interface):
        """Test trade execution gas estimation."""
        trade_data = {
            'operation': 'supply',
            'token': 'USDT',
            'amount': 1000.0,
            'venue': 'aave'
        }
        market_data = {'USDT': 1.0}
        
        result = await onchain_interface.execute_trade(trade_data, market_data)
        
        # Check that gas information is included
        assert 'gas_used' in result
        assert 'gas_price' in result
        assert 'transaction_cost' in result

    @pytest.mark.asyncio
    async def test_execute_trade_transaction_hash_generation(self, onchain_interface):
        """Test trade execution transaction hash generation."""
        trade_data = {
            'operation': 'supply',
            'token': 'USDT',
            'amount': 1000.0,
            'venue': 'aave'
        }
        market_data = {'USDT': 1.0}
        
        result = await onchain_interface.execute_trade(trade_data, market_data)
        
        # Check that transaction hash is generated
        assert 'transaction_hash' in result
        assert result['transaction_hash'] is not None
        assert result['transaction_hash'].startswith('0x')

    @pytest.mark.asyncio
    async def test_execute_trade_timestamp_generation(self, onchain_interface):
        """Test trade execution timestamp generation."""
        trade_data = {
            'operation': 'supply',
            'token': 'USDT',
            'amount': 1000.0,
            'venue': 'aave'
        }
        market_data = {'USDT': 1.0}
        
        result = await onchain_interface.execute_trade(trade_data, market_data)
        
        # Check that timestamp is generated
        assert 'timestamp' in result
        assert result['timestamp'] is not None

    def test_edge_case_zero_amount(self, onchain_interface):
        """Test edge case with zero amount."""
        trade_data = {
            'operation': 'supply',
            'token': 'USDT',
            'amount': 0.0,
            'venue': 'aave'
        }
        market_data = {'USDT': 1.0}
        
        # Should still execute but with zero amount
        import asyncio
        result = asyncio.run(onchain_interface.execute_trade(trade_data, market_data))
        assert result['amount'] == 0.0

    def test_boundary_conditions(self, onchain_interface):
        """Test boundary conditions for trade execution."""
        market_data = {'USDT': 1.0}
        
        # Test minimum valid amount
        trade_data = {
            'operation': 'supply',
            'token': 'USDT',
            'amount': 0.000001,  # Very small amount
            'venue': 'aave'
        }
        
        import asyncio
        result = asyncio.run(onchain_interface.execute_trade(trade_data, market_data))
        assert result['amount'] == 0.000001
        assert result['status'] == 'SUCCESS'

    @pytest.mark.asyncio
    async def test_execute_trade_unsupported_venue(self, onchain_interface):
        """Test trade execution with unsupported venue."""
        trade_data = {
            'operation': 'supply',
            'token': 'USDT',
            'amount': 1000.0,
            'venue': 'unsupported_venue'
        }
        market_data = {'USDT': 1.0}
        
        # Should still execute in backtest mode (simulated)
        result = await onchain_interface.execute_trade(trade_data, market_data)
        assert result['status'] == 'SUCCESS'
        assert result['venue'] == 'unsupported_venue'

    @pytest.mark.asyncio
    async def test_execute_trade_unsupported_operation(self, onchain_interface):
        """Test trade execution with unsupported operation."""
        trade_data = {
            'operation': 'unsupported_operation',
            'token': 'USDT',
            'amount': 1000.0,
            'venue': 'aave'
        }
        market_data = {'USDT': 1.0}
        
        # Should still execute in backtest mode (simulated)
        result = await onchain_interface.execute_trade(trade_data, market_data)
        assert result['status'] == 'SUCCESS'
        assert result['operation'] == 'unsupported_operation'