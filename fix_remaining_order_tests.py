#!/usr/bin/env python3
"""
Fix remaining Order model tests by adding required fields.
"""

import re

def fix_remaining_order_tests():
    """Fix remaining Order model tests by adding required fields."""
    
    test_file = "tests/unit/models/test_order_model.py"
    
    with open(test_file, 'r') as f:
        content = f.read()
    
    # Fix transfer validation missing source_venue test
    content = re.sub(
        r'def test_transfer_validation_missing_source_venue\(self\):\s*"""Test that transfers require source_venue parameter\."""\s*with pytest\.raises\(ValidationError\) as exc_info:\s*Order\(\s*venue=\'wallet\',\s*operation=OrderOperation\.TRANSFER,\s*token=\'USDT\',\s*amount=5000\.0\s*\)\s*assert "requires \'source_venue\' parameter" in str\(exc_info\.value\)',
        '''def test_transfer_validation_missing_source_venue(self):
        """Test that transfers require source_venue parameter."""
        with pytest.raises(ValidationError) as exc_info:
            Order(
                operation_id='test_validation_004',
                venue='wallet',
                operation=OrderOperation.TRANSFER,
                token='USDT',
                amount=5000.0,
                source_venue='wallet',
                target_venue='binance',
                source_token='USDT',
                target_token='USDT',
                expected_deltas={}
            )
        assert "requires 'source_venue' parameter" in str(exc_info.value)''',
        content,
        flags=re.DOTALL
    )
    
    # Fix transfer validation missing target_venue test
    content = re.sub(
        r'def test_transfer_validation_missing_target_venue\(self\):\s*"""Test that transfers require target_venue parameter\."""\s*with pytest\.raises\(ValidationError\) as exc_info:\s*Order\(\s*venue=\'wallet\',\s*operation=OrderOperation\.TRANSFER,\s*token=\'USDT\',\s*amount=5000\.0\s*\)\s*assert "requires \'target_venue\' parameter" in str\(exc_info\.value\)',
        '''def test_transfer_validation_missing_target_venue(self):
        """Test that transfers require target_venue parameter."""
        with pytest.raises(ValidationError) as exc_info:
            Order(
                operation_id='test_validation_005',
                venue='wallet',
                operation=OrderOperation.TRANSFER,
                token='USDT',
                amount=5000.0,
                source_venue='wallet',
                target_venue='binance',
                source_token='USDT',
                target_token='USDT',
                expected_deltas={}
            )
        assert "requires 'target_venue' parameter" in str(exc_info.value)''',
        content,
        flags=re.DOTALL
    )
    
    # Fix transfer validation missing token test
    content = re.sub(
        r'def test_transfer_validation_missing_token\(self\):\s*"""Test that transfers require token parameter\."""\s*with pytest\.raises\(ValidationError\) as exc_info:\s*Order\(\s*venue=\'wallet\',\s*operation=OrderOperation\.TRANSFER,\s*source_venue=\'wallet\',\s*target_venue=\'binance\',\s*amount=5000\.0\s*\)\s*assert "requires \'token\' parameter" in str\(exc_info\.value\)',
        '''def test_transfer_validation_missing_token(self):
        """Test that transfers require token parameter."""
        with pytest.raises(ValidationError) as exc_info:
            Order(
                operation_id='test_validation_006',
                venue='wallet',
                operation=OrderOperation.TRANSFER,
                source_venue='wallet',
                target_venue='binance',
                amount=5000.0,
                source_token='USDT',
                target_token='USDT',
                expected_deltas={}
            )
        assert "requires 'token' parameter" in str(exc_info.value)''',
        content,
        flags=re.DOTALL
    )
    
    # Fix atomic validation missing group_id test
    content = re.sub(
        r'def test_atomic_validation_missing_group_id\(self\):\s*"""Test that atomic execution requires group_id\."""\s*with pytest\.raises\(ValidationError\) as exc_info:\s*Order\(\s*venue=\'aave\',\s*operation=OrderOperation\.SUPPLY,\s*token_in=\'USDT\',\s*token_out=\'aUSDT\',\s*amount=10000\.0,\s*execution_mode=\'atomic\'\s*\)\s*assert "atomic_group_id required when execution_mode is atomic" in str\(exc_info\.value\)',
        '''def test_atomic_validation_missing_group_id(self):
        """Test that atomic execution requires group_id."""
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
        assert "atomic_group_id required when execution_mode is atomic" in str(exc_info.value)''',
        content,
        flags=re.DOTALL
    )
    
    # Fix atomic validation missing sequence test
    content = re.sub(
        r'def test_atomic_validation_missing_sequence\(self\):\s*"""Test that atomic groups require sequence\."""\s*with pytest\.raises\(ValidationError\) as exc_info:\s*Order\(\s*venue=\'aave\',\s*operation=OrderOperation\.SUPPLY,\s*token_in=\'USDT\',\s*token_out=\'aUSDT\',\s*amount=10000\.0,\s*atomic_group_id=\'test_group\'\s*\)\s*assert "sequence_in_group required when atomic_group_id is provided" in str\(exc_info\.value\)',
        '''def test_atomic_validation_missing_sequence(self):
        """Test that atomic groups require sequence."""
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
        assert "sequence_in_group required when atomic_group_id is provided" in str(exc_info.value)''',
        content,
        flags=re.DOTALL
    )
    
    # Fix take profit validation long test
    content = re.sub(
        r'def test_take_profit_validation_long\(self\):\s*"""Test take profit validation for LONG positions\."""\s*with pytest\.raises\(ValidationError\) as exc_info:\s*Order\(\s*venue=\'binance\',\s*operation=OrderOperation\.SPOT_TRADE,\s*pair=\'BTC/USDT\',\s*side=\'BUY\',\s*amount=0\.5,\s*price=45000\.0,\s*take_profit=44000\.0\s*\)\s*assert "take_profit must be higher than entry price for LONG positions" in str\(exc_info\.value\)',
        '''def test_take_profit_validation_long(self):
        """Test take profit validation for LONG positions."""
        with pytest.raises(ValidationError) as exc_info:
            Order(
                operation_id='test_validation_009',
                venue='binance',
                operation=OrderOperation.SPOT_TRADE,
                pair='BTC/USDT',
                side='BUY',
                amount=0.5,
                price=45000.0,
                take_profit=44000.0,
                source_venue='wallet',
                target_venue='binance',
                source_token='USDT',
                target_token='BTC',
                expected_deltas={}
            )
        assert "take_profit must be higher than entry price for LONG positions" in str(exc_info.value)''',
        content,
        flags=re.DOTALL
    )
    
    # Fix take profit validation short test
    content = re.sub(
        r'def test_take_profit_validation_short\(self\):\s*"""Test take profit validation for SHORT positions\."""\s*with pytest\.raises\(ValidationError\) as exc_info:\s*Order\(\s*venue=\'binance\',\s*operation=OrderOperation\.SPOT_TRADE,\s*pair=\'BTC/USDT\',\s*side=\'SHORT\',\s*amount=0\.5,\s*price=45000\.0,\s*take_profit=46000\.0\s*\)\s*assert "take_profit must be lower than entry price for SHORT positions" in str\(exc_info\.value\)',
        '''def test_take_profit_validation_short(self):
        """Test take profit validation for SHORT positions."""
        with pytest.raises(ValidationError) as exc_info:
            Order(
                operation_id='test_validation_010',
                venue='binance',
                operation=OrderOperation.SPOT_TRADE,
                pair='BTC/USDT',
                side='SHORT',
                amount=0.5,
                price=45000.0,
                take_profit=46000.0,
                source_venue='wallet',
                target_venue='binance',
                source_token='USDT',
                target_token='BTC',
                expected_deltas={}
            )
        assert "take_profit must be lower than entry price for SHORT positions" in str(exc_info.value)''',
        content,
        flags=re.DOTALL
    )
    
    # Fix stop loss validation long test
    content = re.sub(
        r'def test_stop_loss_validation_long\(self\):\s*"""Test stop loss validation for LONG positions\."""\s*with pytest\.raises\(ValidationError\) as exc_info:\s*Order\(\s*venue=\'binance\',\s*operation=OrderOperation\.SPOT_TRADE,\s*pair=\'BTC/USDT\',\s*side=\'BUY\',\s*amount=0\.5,\s*price=45000\.0,\s*stop_loss=46000\.0\s*\)\s*assert "stop_loss must be lower than entry price for LONG positions" in str\(exc_info\.value\)',
        '''def test_stop_loss_validation_long(self):
        """Test stop loss validation for LONG positions."""
        with pytest.raises(ValidationError) as exc_info:
            Order(
                operation_id='test_validation_011',
                venue='binance',
                operation=OrderOperation.SPOT_TRADE,
                pair='BTC/USDT',
                side='BUY',
                amount=0.5,
                price=45000.0,
                stop_loss=46000.0,
                source_venue='wallet',
                target_venue='binance',
                source_token='USDT',
                target_token='BTC',
                expected_deltas={}
            )
        assert "stop_loss must be lower than entry price for LONG positions" in str(exc_info.value)''',
        content,
        flags=re.DOTALL
    )
    
    # Fix stop loss validation short test
    content = re.sub(
        r'def test_stop_loss_validation_short\(self\):\s*"""Test stop loss validation for SHORT positions\."""\s*with pytest\.raises\(ValidationError\) as exc_info:\s*Order\(\s*venue=\'binance\',\s*operation=OrderOperation\.SPOT_TRADE,\s*pair=\'BTC/USDT\',\s*side=\'SHORT\',\s*amount=0\.5,\s*price=45000\.0,\s*stop_loss=44000\.0\s*\)\s*assert "stop_loss must be higher than entry price for SHORT positions" in str\(exc_info\.value\)',
        '''def test_stop_loss_validation_short(self):
        """Test stop loss validation for SHORT positions."""
        with pytest.raises(ValidationError) as exc_info:
            Order(
                operation_id='test_validation_012',
                venue='binance',
                operation=OrderOperation.SPOT_TRADE,
                pair='BTC/USDT',
                side='SHORT',
                amount=0.5,
                price=45000.0,
                stop_loss=44000.0,
                source_venue='wallet',
                target_venue='binance',
                source_token='USDT',
                target_token='BTC',
                expected_deltas={}
            )
        assert "stop_loss must be higher than entry price for SHORT positions" in str(exc_info.value)''',
        content,
        flags=re.DOTALL
    )
    
    # Fix venue type detection test
    content = re.sub(
        r'aave_order = Order\(\s*venue=\'aave\',\s*operation=OrderOperation\.SUPPLY,\s*token_in=\'USDT\',\s*amount=10000\.0\s*\)',
        '''aave_order = Order(
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
        )''',
        content
    )
    
    # Fix to_dict conversion test
    content = re.sub(
        r'order = Order\(\s*venue=\'binance\',\s*operation=OrderOperation\.SPOT_TRADE,\s*pair=\'BTC/USDT\',\s*side=\'BUY\',\s*amount=0\.5,\s*strategy_intent=\'entry_full\'\s*\)',
        '''order = Order(
            operation_id='test_dict_001',
            venue='binance',
            operation=OrderOperation.SPOT_TRADE,
            pair='BTC/USDT',
            side='BUY',
            amount=0.5,
            strategy_intent='entry_full',
            source_venue='wallet',
            target_venue='binance',
            source_token='USDT',
            target_token='BTC',
            expected_deltas={
                'wallet:BaseToken:USDT': -25000.0,
                'binance:BaseToken:BTC': 0.5
            }
        )''',
        content
    )
    
    # Fix operation type checks test
    content = re.sub(
        r'supply_order = Order\(\s*venue=\'aave\',\s*operation=OrderOperation\.SUPPLY,\s*token_in=\'USDT\',\s*amount=10000\.0\s*\)',
        '''supply_order = Order(
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
        )''',
        content
    )
    
    # Fix metadata fields test
    content = re.sub(
        r'order = Order\(\s*venue=\'binance\',\s*operation=OrderOperation\.SPOT_TRADE,\s*pair=\'BTC/USDT\',\s*side=\'BUY\',\s*amount=0\.5,\s*strategy_intent=\'entry_full\'\s*\)',
        '''order = Order(
            operation_id='test_meta_001',
            venue='binance',
            operation=OrderOperation.SPOT_TRADE,
            pair='BTC/USDT',
            side='BUY',
            amount=0.5,
            strategy_intent='entry_full',
            source_venue='wallet',
            target_venue='binance',
            source_token='USDT',
            target_token='BTC',
            expected_deltas={
                'wallet:BaseToken:USDT': -25000.0,
                'binance:BaseToken:BTC': 0.5
            }
        )''',
        content
    )
    
    # Fix additional parameters test
    content = re.sub(
        r'order = Order\(\s*venue=\'aave\',\s*operation=OrderOperation\.SUPPLY,\s*token_in=\'USDT\',\s*token_out=\'aUSDT\',\s*amount=10000\.0,\s*ltv_target=0\.8,\s*operation_details=\{\'collateral_type\': \'COLLATERAL_SUPPLIED\'\}\s*\)',
        '''order = Order(
            operation_id='test_params_001',
            venue='aave',
            operation=OrderOperation.SUPPLY,
            token_in='USDT',
            token_out='aUSDT',
            amount=10000.0,
            ltv_target=0.8,
            operation_details={'collateral_type': 'COLLATERAL_SUPPLIED'},
            source_venue='wallet',
            target_venue='aave',
            source_token='USDT',
            target_token='aUSDT',
            expected_deltas={
                'wallet:BaseToken:USDT': -10000.0,
                'aave:aToken:aUSDT': 9900.0
            }
        )''',
        content
    )
    
    # Fix all order operations test
    content = re.sub(
        r'order = Order\(\s*venue=\'aave\',\s*operation=operation,\s*amount=1000\.0\s*\)',
        '''order = Order(
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
        )''',
        content
    )
    
    with open(test_file, 'w') as f:
        f.write(content)
    
    print("Fixed remaining Order model tests!")

if __name__ == "__main__":
    fix_remaining_order_tests()

