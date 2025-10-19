#!/usr/bin/env python3
"""
Fix last remaining Order model tests by adding required fields.
"""

import re

def fix_last_remaining_tests():
    """Fix last remaining Order model tests by adding required fields."""
    
    test_file = "tests/unit/models/test_order_model.py"
    
    with open(test_file, 'r') as f:
        content = f.read()
    
    # Fix stop loss validation short test
    content = re.sub(
        r'def test_stop_loss_validation_short\(self\):\s*"""Test stop loss validation for SHORT positions\."""\s*with pytest\.raises\(ValidationError\) as exc_info:\s*Order\(\s*venue=\'binance\',\s*operation=OrderOperation\.PERP_TRADE,\s*pair=\'BTCUSDT\',\s*side=\'SHORT\',\s*amount=1\.0,\s*price=45000\.0,\s*stop_loss=44000\.0\s*\)\s*assert "stop_loss must be higher than entry price for SHORT positions" in str\(exc_info\.value\)',
        '''def test_stop_loss_validation_short(self):
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
    
    print("Fixed last remaining tests!")

if __name__ == "__main__":
    fix_last_remaining_tests()

