"""
Unit tests for Order model validation and functionality.

Tests all OrderOperation types, validation rules, and helper methods.
"""

import pytest
from pydantic import ValidationError
from datetime import datetime

from backend.src.basis_strategy_v1.core.models.order import Order, OrderOperation, VenueType


class TestOrderModel:
    """Test Order model validation and functionality."""
    
    def test_cex_spot_trade_creation(self):
        """Test creating a valid CEX spot trade order."""
        order = Order(
            operation_id='test_spot_001',
            venue='binance',
            operation=OrderOperation.SPOT_TRADE,
            pair='BTC/USDT',
            side='BUY',
            amount=0.5,
            price=45000.0,
            source_venue='wallet',
            target_venue='binance',
            source_token='USDT',
            target_token='BTC',
            expected_deltas={
                'wallet:BaseToken:USDT': -22500.0,
                'binance:BaseToken:BTC': 0.5
            }
        )
        
        assert order.venue == 'binance'
        assert order.operation == OrderOperation.SPOT_TRADE
        assert order.pair == 'BTC/USDT'
        assert order.side == 'BUY'
        assert order.amount == 0.5
        assert order.price == 45000.0
        assert order.is_cex_trade() is True
        assert order.is_defi_operation() is False
        assert order.is_wallet_transfer() is False
        assert order.get_venue_type() == VenueType.CEX
    
    def test_cex_perp_trade_creation(self):
        """Test creating a valid CEX perp trade order."""
        order = Order(
            operation_id='test_perp_001',
            venue='bybit',
            operation=OrderOperation.PERP_TRADE,
            pair='BTCUSDT',
            side='SHORT',
            amount=1.0,
            take_profit=44000.0,
            stop_loss=46000.0,
            source_venue='wallet',
            target_venue='bybit',
            source_token='USDT',
            target_token='BTC',
            expected_deltas={
                'wallet:BaseToken:USDT': 50000.0,
                'bybit:Perp:BTCUSDT': -1.0
            }
        )
        
        assert order.venue == 'bybit'
        assert order.operation == OrderOperation.PERP_TRADE
        assert order.pair == 'BTCUSDT'
        assert order.side == 'SHORT'
        assert order.amount == 1.0
        assert order.take_profit == 44000.0
        assert order.stop_loss == 46000.0
        assert order.is_cex_trade() is True
    
    def test_defi_supply_creation(self):
        """Test creating a valid DeFi supply order."""
        order = Order(
            operation_id='test_supply_001',
            venue='aave',
            operation=OrderOperation.SUPPLY,
            token_in='USDT',
            token_out='aUSDT',
            amount=10000.0,
            source_venue='wallet',
            target_venue='aave',
            source_token='USDT',
            target_token='aUSDT',
            expected_deltas={
                'wallet:BaseToken:USDT': -10000.0,
                'aave:aToken:aUSDT': 9900.0
            }
        )
        
        assert order.venue == 'aave'
        assert order.operation == OrderOperation.SUPPLY
        assert order.token_in == 'USDT'
        assert order.token_out == 'aUSDT'
        assert order.amount == 10000.0
        assert order.is_defi_operation() is True
        assert order.get_venue_type() == VenueType.DEFI
    
    def test_defi_stake_creation(self):
        """Test creating a valid DeFi staking order."""
        order = Order(
            operation_id='test_stake_001',
            venue='etherfi',
            operation=OrderOperation.STAKE,
            token_in='ETH',
            token_out='weETH',
            amount=2.0,
            source_venue='wallet',
            target_venue='etherfi',
            source_token='ETH',
            target_token='weETH',
            expected_deltas={
                'wallet:BaseToken:ETH': -2.0,
                'etherfi:LST:weETH': 1.9
            }
        )
        
        assert order.venue == 'etherfi'
        assert order.operation == OrderOperation.STAKE
        assert order.token_in == 'ETH'
        assert order.token_out == 'weETH'
        assert order.amount == 2.0
        assert order.is_defi_operation() is True
    
    def test_wallet_transfer_creation(self):
        """Test creating a valid wallet transfer order."""
        order = Order(
            operation_id='test_transfer_001',
            venue='wallet',
            operation=OrderOperation.TRANSFER,
            source_venue='wallet',
            target_venue='binance',
            token='USDT',
            amount=5000.0,
            source_token='USDT',
            target_token='USDT',
            expected_deltas={
                'wallet:BaseToken:USDT': -5000.0,
                'binance:BaseToken:USDT': 5000.0
            }
        )
        
        assert order.venue == 'wallet'
        assert order.operation == OrderOperation.TRANSFER
        assert order.source_venue == 'wallet'
        assert order.target_venue == 'binance'
        assert order.token == 'USDT'
        assert order.amount == 5000.0
        assert order.is_wallet_transfer() is True
        assert order.get_venue_type() == VenueType.WALLET
    
    def test_atomic_group_creation(self):
        """Test creating orders in an atomic group."""
        order1 = Order(
            operation_id='test_atomic_001',
            venue='instadapp',
            operation=OrderOperation.FLASH_BORROW,
            token_out='WETH',
            amount=10.0,
            execution_mode='atomic',
            atomic_group_id='leverage_1',
            sequence_in_group=1,
            source_venue='instadapp',
            target_venue='wallet',
            source_token='WETH',
            target_token='WETH',
            expected_deltas={
                'instadapp:BaseToken:WETH': 10.0,
                'wallet:BaseToken:WETH': 10.0
            }
        )
        
        order2 = Order(
            operation_id='test_atomic_002',
            venue='aave',
            operation=OrderOperation.SUPPLY,
            token_in='weETH',
            amount=20.0,
            execution_mode='atomic',
            atomic_group_id='leverage_1',
            sequence_in_group=2,
            source_venue='wallet',
            target_venue='aave',
            source_token='weETH',
            target_token='aweETH',
            expected_deltas={
                'wallet:BaseToken:weETH': -20.0,
                'aave:aToken:aweETH': 20.0
            }
        )
        
        assert order1.is_atomic() is True
        assert order2.is_atomic() is True
        assert order1.atomic_group_id == order2.atomic_group_id
        assert order1.sequence_in_group == 1
        assert order2.sequence_in_group == 2
    
    def test_cex_trade_validation_missing_pair(self):
        """Test that CEX trades require pair parameter."""
        with pytest.raises(ValidationError) as exc_info:
            Order(
                operation_id='test_validation_001',
                venue='binance',
                operation=OrderOperation.SPOT_TRADE,
                side='BUY',
                amount=0.5,
                source_venue='wallet',
                target_venue='binance',
                source_token='USDT',
                target_token='BTC',
                expected_deltas={}
            )
        
        assert "requires 'pair' parameter" in str(exc_info.value)
    
    def test_cex_trade_validation_missing_side(self):
        """Test that CEX trades require side parameter."""
        with pytest.raises(ValidationError) as exc_info:
            Order(
                operation_id='test_validation_002',
                venue='binance',
                operation=OrderOperation.SPOT_TRADE,
                pair='BTC/USDT',
                amount=0.5,
                source_venue='wallet',
                target_venue='binance',
                source_token='USDT',
                target_token='BTC',
                expected_deltas={}
            )
        assert "requires 'side' parameter" in str(exc_info.value)
    
    def test_defi_operation_validation_missing_token_in(self):
        """Test that DeFi operations require token_in parameter."""
        with pytest.raises(ValidationError) as exc_info:
            Order(
                operation_id='test_validation_003',
                venue='aave',
                operation=OrderOperation.SUPPLY,
                token_out='aUSDT',
                amount=10000.0,
                source_venue='wallet',
                target_venue='aave',
                source_token='USDT',
                target_token='aUSDT',
                expected_deltas={}
            )
        assert "requires 'token_in' parameter" in str(exc_info.value)
    
    def test_transfer_validation_missing_source_venue(self):
        """Test that transfers require source_venue parameter."""
        with pytest.raises(ValidationError) as exc_info:
            Order(
                operation_id='test_validation_004',
                venue='wallet',
                operation=OrderOperation.TRANSFER,
                target_venue='binance',
                amount=5000.0,
                source_token='USDT',
                target_token='USDT',
                expected_deltas={}
            )
        
        assert "Field required" in str(exc_info.value) and "source_venue" in str(exc_info.value)
    
    def test_transfer_validation_missing_target_venue(self):
        """Test that transfers require target_venue parameter."""
        with pytest.raises(ValidationError) as exc_info:
            Order(
                operation_id='test_validation_005',
                venue='wallet',
                operation=OrderOperation.TRANSFER,
                source_venue='wallet',
                amount=5000.0,
                source_token='USDT',
                target_token='USDT',
                expected_deltas={}
            )
        assert "Field required" in str(exc_info.value) and "target_venue" in str(exc_info.value)
    
    def test_transfer_validation_missing_token(self):
        """Test that transfers require token parameter."""
        with pytest.raises(ValidationError) as exc_info:
            Order(
                operation_id='test_validation_006',
                venue='wallet',
                operation=OrderOperation.TRANSFER,
                source_venue='wallet',
                target_venue='binance',
                amount=5000.0,
                expected_deltas={}
            )
        assert "Field required" in str(exc_info.value) and "source_token" in str(exc_info.value)
    
    def test_atomic_validation_missing_group_id(self):
        """Test that atomic execution requires atomic_group_id."""
        with pytest.raises(ValidationError) as exc_info:
            Order(
                operation_id='test_validation_007',
                venue='aave',
                operation=OrderOperation.SUPPLY,
                token_in='USDT',
                token_out='aUSDT',
                amount=10000.0,
                execution_mode='atomic',
                source_venue='wallet',
                target_venue='aave',
                source_token='USDT',
                target_token='aUSDT',
                expected_deltas={}
            )
        
        assert "atomic_group_id required when execution_mode is atomic" in str(exc_info.value)
    
    def test_atomic_validation_missing_sequence(self):
        """Test that atomic_group_id requires sequence_in_group."""
        with pytest.raises(ValidationError) as exc_info:
            Order(
                operation_id='test_validation_008',
                venue='aave',
                operation=OrderOperation.SUPPLY,
                token_in='USDT',
                token_out='aUSDT',
                amount=10000.0,
                atomic_group_id='test_group',
                source_venue='wallet',
                target_venue='aave',
                source_token='USDT',
                target_token='aUSDT',
                expected_deltas={}
            )
        
        assert "sequence_in_group required when atomic_group_id is provided" in str(exc_info.value)
    
    def test_amount_validation_negative(self):
        """Test that amount must be positive."""
        with pytest.raises(ValidationError) as exc_info:
            Order(
                venue='binance',
                operation=OrderOperation.SPOT_TRADE,
                pair='BTC/USDT',
                side='BUY',
                amount=-0.5
            )
        
        assert "amount must be positive" in str(exc_info.value)
    
    def test_amount_validation_zero(self):
        """Test that amount cannot be zero."""
        with pytest.raises(ValidationError) as exc_info:
            Order(
                venue='binance',
                operation=OrderOperation.SPOT_TRADE,
                pair='BTC/USDT',
                side='BUY',
                amount=0.0
            )
        
        assert "amount must be positive" in str(exc_info.value)
    
    def test_price_validation_negative(self):
        """Test that price must be positive if provided."""
        with pytest.raises(ValidationError) as exc_info:
            Order(
                venue='binance',
                operation=OrderOperation.SPOT_TRADE,
                pair='BTC/USDT',
                side='BUY',
                amount=0.5,
                price=-45000.0
            )
        
        assert "price must be positive" in str(exc_info.value)
    
    def test_take_profit_validation_long(self):
        """Test take profit validation for LONG positions."""
        with pytest.raises(ValidationError) as exc_info:
            Order(
                operation_id='test_validation_009',
                venue='binance',
                operation=OrderOperation.PERP_TRADE,
                pair='BTCUSDT',
                side='LONG',
                amount=1.0,
                price=45000.0,
                take_profit=44000.0,  # Lower than entry price
                source_venue='wallet',
                target_venue='binance',
                source_token='USDT',
                target_token='BTC',
                expected_deltas={}
            )
        
        assert "take_profit must be higher than entry price for LONG positions" in str(exc_info.value)
    
    def test_take_profit_validation_short(self):
        """Test take profit validation for SHORT positions."""
        with pytest.raises(ValidationError) as exc_info:
            Order(
                operation_id='test_validation_010',
                venue='binance',
                operation=OrderOperation.PERP_TRADE,
                pair='BTCUSDT',
                side='SHORT',
                amount=1.0,
                price=45000.0,
                take_profit=46000.0,  # Higher than entry price
                source_venue='wallet',
                target_venue='binance',
                source_token='USDT',
                target_token='BTC',
                expected_deltas={}
            )
        
        assert "take_profit must be lower than entry price for SHORT positions" in str(exc_info.value)
    
    def test_stop_loss_validation_long(self):
        """Test stop loss validation for LONG positions."""
        with pytest.raises(ValidationError) as exc_info:
            Order(
                operation_id='test_validation_011',
                venue='binance',
                operation=OrderOperation.PERP_TRADE,
                pair='BTCUSDT',
                side='LONG',
                amount=1.0,
                price=45000.0,
                stop_loss=46000.0,  # Higher than entry price
                source_venue='wallet',
                target_venue='binance',
                source_token='USDT',
                target_token='BTC',
                expected_deltas={}
            )
        
        assert "stop_loss must be lower than entry price for LONG positions" in str(exc_info.value)
    
    def test_stop_loss_validation_short(self):
        """Test stop loss validation for SHORT positions."""
        with pytest.raises(ValidationError) as exc_info:
            Order(
                operation_id='test_validation_012',
                venue='binance',
                operation=OrderOperation.PERP_TRADE,
                pair='BTCUSDT',
                side='SHORT',
                amount=1.0,
                price=45000.0,
                stop_loss=44000.0,  # Lower than entry price
                source_venue='wallet',
                target_venue='binance',
                source_token='USDT',
                target_token='BTC',
                expected_deltas={}
            )
        
        assert "stop_loss must be higher than entry price for SHORT positions" in str(exc_info.value)
    
    def test_venue_type_detection(self):
        """Test venue type detection for different venues."""
        # CEX venues
        binance_order = Order(
            operation_id='test_venue_001',
            venue='binance',
            operation=OrderOperation.SPOT_TRADE,
            pair='BTC/USDT',
            side='BUY',
            amount=0.5,
            source_venue='wallet',
            target_venue='binance',
            source_token='USDT',
            target_token='BTC',
            expected_deltas={
                'wallet:BaseToken:USDT': -25000.0,
                'binance:BaseToken:BTC': 0.5
            }
        )
        assert binance_order.get_venue_type() == VenueType.CEX
        
        bybit_order = Order(
            operation_id='test_venue_002',
            venue='bybit',
            operation=OrderOperation.PERP_TRADE,
            pair='BTCUSDT',
            side='SHORT',
            amount=1.0,
            source_venue='wallet',
            target_venue='bybit',
            source_token='USDT',
            target_token='BTC',
            expected_deltas={
                'wallet:BaseToken:USDT': 50000.0,
                'bybit:Perp:BTCUSDT': -1.0
            }
        )
        assert bybit_order.get_venue_type() == VenueType.CEX
        
        # DeFi venues
        aave_order = Order(
            operation_id='test_venue_003',
            venue='aave',
            operation=OrderOperation.SUPPLY,
            token_in='USDT',
            amount=10000.0,
            source_venue='wallet',
            target_venue='aave',
            source_token='USDT',
            target_token='aUSDT',
            expected_deltas={
                'wallet:BaseToken:USDT': -10000.0,
                'aave:aToken:aUSDT': 9900.0
            }
        )
        assert aave_order.get_venue_type() == VenueType.DEFI
        
        etherfi_order = Order(
            operation_id='test_venue_004',
            venue='etherfi',
            operation=OrderOperation.STAKE,
            token_in='ETH',
            amount=2.0,
            source_venue='wallet',
            target_venue='etherfi',
            source_token='ETH',
            target_token='weETH',
            expected_deltas={
                'wallet:BaseToken:ETH': -2.0,
                'etherfi:weETH:weETH': 2.0
            }
        )
        assert etherfi_order.get_venue_type() == VenueType.DEFI
        
        # DeFi middleware
        instadapp_order = Order(
            operation_id='test_venue_005',
            venue='instadapp',
            operation=OrderOperation.FLASH_BORROW,
            token_out='WETH',
            amount=10.0,
            source_venue='instadapp',
            target_venue='wallet',
            source_token='WETH',
            target_token='WETH',
            expected_deltas={
                'instadapp:BaseToken:WETH': -10.0,
                'wallet:BaseToken:WETH': 10.0
            }
        )
        assert instadapp_order.get_venue_type() == VenueType.DEFI_MIDDLEWARE
        
        # Wallet
        wallet_order = Order(
            operation_id='test_venue_006',
            venue='wallet',
            operation=OrderOperation.TRANSFER,
            source_venue='wallet',
            target_venue='binance',
            token='USDT',
            amount=5000.0,
            source_token='USDT',
            target_token='USDT',
            expected_deltas={
                'wallet:BaseToken:USDT': -5000.0,
                'binance:BaseToken:USDT': 5000.0
            }
        )
        assert wallet_order.get_venue_type() == VenueType.WALLET
    
    def test_to_dict_conversion(self):
        """Test converting order to dictionary."""
        order = Order(
            operation_id='test_dict_001',
            venue='binance',
            operation=OrderOperation.SPOT_TRADE,
            pair='BTC/USDT',
            side='BUY',
            amount=0.5,
            price=45000.0,
            strategy_intent='entry_full',
            source_venue='wallet',
            target_venue='binance',
            source_token='USDT',
            target_token='BTC',
            expected_deltas={
                'wallet:BaseToken:USDT': -25000.0,
                'binance:BaseToken:BTC': 0.5
            }
        )
        
        order_dict = order.to_dict()
        
        assert order_dict['venue'] == 'binance'
        assert order_dict['operation'] == 'spot_trade'
        assert order_dict['pair'] == 'BTC/USDT'
        assert order_dict['side'] == 'BUY'
        assert order_dict['amount'] == 0.5
        assert order_dict['price'] == 45000.0
        assert order_dict['strategy_intent'] == 'entry_full'
    
    def test_operation_type_checks(self):
        """Test operation type checking methods."""
        # CEX trade
        spot_order = Order(
            operation_id='test_ops_001',
            venue='binance',
            operation=OrderOperation.SPOT_TRADE,
            pair='BTC/USDT',
            side='BUY',
            amount=0.5,
            source_venue='wallet',
            target_venue='binance',
            source_token='USDT',
            target_token='BTC',
            expected_deltas={
                'wallet:BaseToken:USDT': -25000.0,
                'binance:BaseToken:BTC': 0.5
            }
        )
        assert spot_order.is_cex_trade() is True
        assert spot_order.is_defi_operation() is False
        assert spot_order.is_wallet_transfer() is False
        
        perp_order = Order(
            operation_id='test_ops_002',
            venue='bybit',
            operation=OrderOperation.PERP_TRADE,
            pair='BTCUSDT',
            side='SHORT',
            amount=1.0,
            source_venue='wallet',
            target_venue='bybit',
            source_token='USDT',
            target_token='BTC',
            expected_deltas={
                'wallet:BaseToken:USDT': 50000.0,
                'bybit:Perp:BTCUSDT': -1.0
            }
        )
        assert perp_order.is_cex_trade() is True
        
        # DeFi operation
        supply_order = Order(
            operation_id='test_ops_003',
            venue='aave',
            operation=OrderOperation.SUPPLY,
            token_in='USDT',
            amount=10000.0,
            source_venue='wallet',
            target_venue='aave',
            source_token='USDT',
            target_token='aUSDT',
            expected_deltas={
                'wallet:BaseToken:USDT': -10000.0,
                'aave:aToken:aUSDT': 9900.0
            }
        )
        assert supply_order.is_defi_operation() is True
        assert supply_order.is_cex_trade() is False
        assert supply_order.is_wallet_transfer() is False
        
        stake_order = Order(
            operation_id='test_ops_004',
            venue='etherfi',
            operation=OrderOperation.STAKE,
            token_in='ETH',
            amount=2.0,
            source_venue='wallet',
            target_venue='etherfi',
            source_token='ETH',
            target_token='weETH',
            expected_deltas={
                'wallet:BaseToken:ETH': -2.0,
                'etherfi:weETH:weETH': 2.0
            }
        )
        assert stake_order.is_defi_operation() is True
        
        # Wallet transfer
        transfer_order = Order(
            operation_id='test_ops_005',
            venue='wallet',
            operation=OrderOperation.TRANSFER,
            source_venue='wallet',
            target_venue='binance',
            token='USDT',
            amount=5000.0,
            source_token='USDT',
            target_token='USDT',
            expected_deltas={
                'wallet:BaseToken:USDT': -5000.0,
                'binance:BaseToken:USDT': 5000.0
            }
        )
        assert transfer_order.is_wallet_transfer() is True
        assert transfer_order.is_cex_trade() is False
        assert transfer_order.is_defi_operation() is False
    
    def test_metadata_fields(self):
        """Test metadata fields for debugging and tracking."""
        order = Order(
            operation_id='test_meta_001',
            venue='binance',
            operation=OrderOperation.SPOT_TRADE,
            pair='BTC/USDT',
            side='BUY',
            amount=0.5,
            timestamp_group='phase_1_funding',
            strategy_intent='entry_full',
            source_venue='wallet',
            target_venue='binance',
            source_token='USDT',
            target_token='BTC',
            expected_deltas={
                'wallet:BaseToken:USDT': -25000.0,
                'binance:BaseToken:BTC': 0.5
            }
        )
        
        assert order.timestamp_group == 'phase_1_funding'
        assert order.strategy_intent == 'entry_full'
        assert order.execution_mode == 'sequential'  # Default
    
    def test_additional_parameters(self):
        """Test additional parameters for specific operations."""
        order = Order(
            operation_id='test_params_001',
            venue='aave',
            operation=OrderOperation.SUPPLY,
            token_in='USDT',
            token_out='aUSDT',
            amount=10000.0,
            ltv_target=0.8,
            gas_cost_type='COLLATERAL_SUPPLIED',
            source_venue='wallet',
            target_venue='aave',
            source_token='USDT',
            target_token='aUSDT',
            expected_deltas={
                'wallet:BaseToken:USDT': -10000.0,
                'aave:aToken:aUSDT': 9900.0
            }
        )
        
        assert order.ltv_target == 0.8
        assert order.gas_cost_type == 'COLLATERAL_SUPPLIED'
    
    def test_all_order_operations(self):
        """Test that all OrderOperation enum values can be used."""
        operations = [
            OrderOperation.SPOT_TRADE,
            OrderOperation.PERP_TRADE,
            OrderOperation.SUPPLY,
            OrderOperation.BORROW,
            OrderOperation.REPAY,
            OrderOperation.WITHDRAW,
            OrderOperation.STAKE,
            OrderOperation.UNSTAKE,
            OrderOperation.SWAP,
            OrderOperation.FLASH_BORROW,
            OrderOperation.FLASH_REPAY,
            OrderOperation.TRANSFER
        ]
        
        for operation in operations:
            # Create minimal valid order for each operation
            if operation in [OrderOperation.SPOT_TRADE, OrderOperation.PERP_TRADE]:
                order = Order(
            operation_id=f'test_ops_{operation.value}',
            venue='binance',
            operation=operation,
            pair='BTC/USDT',
            side='BUY',
            amount=0.5,
            source_venue='wallet',
            target_venue='binance',
            source_token='USDT',
            target_token='BTC',
            expected_deltas={
                'wallet:BaseToken:USDT': -25000.0,
                'binance:BaseToken:BTC': 0.5
            }
        )
            elif operation in [OrderOperation.SUPPLY, OrderOperation.STAKE, OrderOperation.SWAP]:
                order = Order(
            operation_id=f'test_ops_{operation.value}',
            venue='aave',
            operation=operation,
            token_in='USDT',
            amount=1000.0,
            source_venue='wallet',
            target_venue='aave',
            source_token='USDT',
            target_token='aUSDT',
            expected_deltas={
                'wallet:BaseToken:USDT': -1000.0,
                'aave:aToken:aUSDT': 990.0
            }
        )
            elif operation == OrderOperation.TRANSFER:
                order = Order(
                    operation_id=f'test_ops_{operation.value}',
                    venue='wallet',
                    operation=operation,
                    source_venue='wallet',
                    target_venue='binance',
                    token='USDT',
                    amount=1000.0,
                    source_token='USDT',
                    target_token='USDT',
                    expected_deltas={
                        'wallet:BaseToken:USDT': -1000.0,
                        'binance:BaseToken:USDT': 1000.0
                    }
                )
            else:
                # For other operations (BORROW, REPAY, WITHDRAW, UNSTAKE, FLASH_BORROW, FLASH_REPAY), create minimal order
                order = Order(
            operation_id=f'test_ops_{operation.value}',
            venue='aave',
            operation=operation,
            amount=1000.0,
            source_venue='wallet',
            target_venue='aave',
            source_token='USDT',
            target_token='aUSDT',
            expected_deltas={
                'wallet:BaseToken:USDT': -1000.0,
                'aave:aToken:aUSDT': 990.0
            }
        )
            
            assert order.operation == operation
