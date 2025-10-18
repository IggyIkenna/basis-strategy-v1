#!/usr/bin/env python3
"""
Script to update all Order creation calls in ETH Leveraged strategy
to include required fields: operation_id, expected_deltas, source_venue, target_venue, source_token, target_token
"""

import re

def update_order_calls(content):
    """Update Order creation calls to include required fields"""
    
    # Pattern to match Order( calls that are missing required fields
    order_pattern = r'Order\(\s*venue=([^,]+),\s*operation=([^,]+),\s*([^)]*)\)'
    
    def replace_order(match):
        venue = match.group(1).strip()
        operation = match.group(2).strip()
        other_params = match.group(3)
        
        # Extract existing parameters
        params = {}
        for param in other_params.split(','):
            if '=' in param:
                key, value = param.split('=', 1)
                params[key.strip()] = value.strip()
        
        # Determine operation type and set appropriate fields
        if 'FLASH_BORROW' in operation:
            operation_id = f"flash_borrow_{int(pd.Timestamp.now().timestamp() * 1000000)}"
            source_venue = 'instadapp'
            target_venue = 'wallet'
            source_token = 'WETH'
            target_token = 'WETH'
            expected_deltas = {
                'instadapp:BaseToken:WETH': params.get('amount', 'debt_amount'),
                'wallet:BaseToken:WETH': params.get('amount', 'debt_amount')
            }
        elif 'FLASH_REPAY' in operation:
            operation_id = f"flash_repay_{int(pd.Timestamp.now().timestamp() * 1000000)}"
            source_venue = 'wallet'
            target_venue = 'instadapp'
            source_token = 'WETH'
            target_token = 'WETH'
            expected_deltas = {
                'wallet:BaseToken:WETH': f"-{params.get('amount', 'debt_amount')}",
                'instadapp:BaseToken:WETH': f"-{params.get('amount', 'debt_amount')}"
            }
        elif 'STAKE' in operation:
            operation_id = f"stake_{int(pd.Timestamp.now().timestamp() * 1000000)}"
            source_venue = 'wallet'
            target_venue = 'etherfi'  # or self.staking_protocol
            source_token = 'WETH'
            target_token = 'weeth'  # or self.lst_type
            expected_deltas = {
                'wallet:BaseToken:WETH': f"-{params.get('amount', 'eth_amount')}",
                'etherfi:aToken:weeth': params.get('amount', 'eth_amount')
            }
        elif 'SUPPLY' in operation:
            operation_id = f"supply_{int(pd.Timestamp.now().timestamp() * 1000000)}"
            source_venue = 'wallet'
            target_venue = 'aave_v3'
            source_token = 'weeth'  # or self.lst_type
            target_token = 'aweeth'  # or f'a{self.lst_type}'
            expected_deltas = {
                'wallet:BaseToken:weeth': f"-{params.get('amount', 'supply_amount')}",
                'aave_v3:aToken:aweeth': params.get('amount', 'supply_amount')
            }
        elif 'BORROW' in operation:
            operation_id = f"borrow_{int(pd.Timestamp.now().timestamp() * 1000000)}"
            source_venue = 'aave_v3'
            target_venue = 'wallet'
            source_token = 'WETH'
            target_token = 'WETH'
            expected_deltas = {
                'aave_v3:debtToken:debtWETH': params.get('amount', 'debt_amount'),
                'wallet:BaseToken:WETH': params.get('amount', 'debt_amount')
            }
        elif 'UNSTAKE' in operation:
            operation_id = f"unstake_{int(pd.Timestamp.now().timestamp() * 1000000)}"
            source_venue = 'etherfi'  # or self.staking_protocol
            target_venue = 'wallet'
            source_token = 'weeth'  # or self.lst_type
            target_token = 'WETH'
            expected_deltas = {
                'etherfi:aToken:weeth': f"-{params.get('amount', 'lst_amount')}",
                'wallet:BaseToken:WETH': params.get('amount', 'lst_amount')
            }
        elif 'WITHDRAW' in operation:
            operation_id = f"withdraw_{int(pd.Timestamp.now().timestamp() * 1000000)}"
            source_venue = 'aave_v3'
            target_venue = 'wallet'
            source_token = 'aweeth'  # or f'a{self.lst_type}'
            target_token = 'weeth'  # or self.lst_type
            expected_deltas = {
                'aave_v3:aToken:aweeth': f"-{params.get('amount', 'supply_amount')}",
                'wallet:BaseToken:weeth': params.get('amount', 'supply_amount')
            }
        elif 'REPAY' in operation:
            operation_id = f"repay_{int(pd.Timestamp.now().timestamp() * 1000000)}"
            source_venue = 'wallet'
            target_venue = 'aave_v3'
            source_token = 'WETH'
            target_token = 'WETH'
            expected_deltas = {
                'wallet:BaseToken:WETH': f"-{params.get('amount', 'debt_amount')}",
                'aave_v3:debtToken:debtWETH': f"-{params.get('amount', 'debt_amount')}"
            }
        elif 'TRANSFER' in operation:
            operation_id = f"transfer_{int(pd.Timestamp.now().timestamp() * 1000000)}"
            source_venue = 'wallet'
            target_venue = 'wallet'
            source_token = params.get('token', 'token')
            target_token = 'ETH'  # or self.share_class
            expected_deltas = {
                f'wallet:BaseToken:{source_token}': f"-{params.get('amount', 'amount')}",
                'wallet:BaseToken:ETH': params.get('amount', 'amount')
            }
        else:
            # Default case
            operation_id = f"operation_{int(pd.Timestamp.now().timestamp() * 1000000)}"
            source_venue = 'wallet'
            target_venue = 'wallet'
            source_token = 'token'
            target_token = 'token'
            expected_deltas = {}
        
        # Build the new Order call
        new_order = f"""Order(
                    operation_id={operation_id},
                    venue={venue},
                    operation={operation}"""
        
        # Add existing parameters
        for key, value in params.items():
            if key not in ['operation_id', 'source_venue', 'target_venue', 'source_token', 'target_token', 'expected_deltas']:
                new_order += f",\n                    {key}={value}"
        
        # Add required fields
        new_order += f""",
                    source_venue='{source_venue}',
                    target_venue='{target_venue}',
                    source_token='{source_token}',
                    target_token='{target_token}',
                    expected_deltas={expected_deltas}"""
        
        # Add operation_details if not present
        if 'operation_details' not in params:
            new_order += f""",
                    operation_details={{'operation_type': '{operation.replace('OrderOperation.', '')}'}}"""
        
        new_order += "\n                )"
        
        return new_order
    
    # Apply the replacement
    updated_content = re.sub(order_pattern, replace_order, content, flags=re.MULTILINE | re.DOTALL)
    
    return updated_content

if __name__ == "__main__":
    # Read the file
    with open('/Users/ikennaigboaka/Documents/basis-strategy-v1/backend/src/basis_strategy_v1/core/strategies/eth_leveraged_strategy.py', 'r') as f:
        content = f.read()
    
    # Update the content
    updated_content = update_order_calls(content)
    
    # Write back to file
    with open('/Users/ikennaigboaka/Documents/basis-strategy-v1/backend/src/basis_strategy_v1/core/strategies/eth_leveraged_strategy.py', 'w') as f:
        f.write(updated_content)
    
    print("Updated ETH Leveraged strategy Order calls")
