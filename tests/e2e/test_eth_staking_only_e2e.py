"""
E2E test for ETH Staking Only strategy.

Tests complete ETH staking strategy execution with real data.
"""

import pytest
from datetime import datetime, timedelta


class TestETHStakingOnlyE2E:
    """Test ETH Staking Only strategy end-to-end."""
    
    def test_eth_staking_only_strategy_execution(self, real_data_provider, real_components):
        """Test complete ETH staking only strategy execution."""
        strategy_manager = real_components["strategy_manager"]
        execution_manager = real_components["execution_manager"]
        
        # Step 1: Configure ETH staking only strategy
        strategy_config = {
            "strategy_mode": "eth_staking_only",
            "share_class": "ETH",
            "asset": "ETH",
            "initial_capital": 100.0,  # 100 ETH
            "max_drawdown": 0.1,
            "leverage_enabled": False,
            "staking_parameters": {
                "min_staking_amount": 32.0,
                "staking_rewards_rate": 0.05,  # 5% APY
                "unstaking_period_days": 7
            }
        }
        
        # Step 2: Execute strategy
        strategy_result = strategy_manager.execute_strategy(strategy_config)
        
        assert strategy_result is not None
        assert strategy_result["strategy_mode"] == "eth_staking_only"
        assert strategy_result["share_class"] == "ETH"
        assert strategy_result["initial_capital"] == 100.0
        
        # Step 3: Verify strategy execution
        assert "execution_orders" in strategy_result
        assert "final_pnl" in strategy_result
        assert "execution_time" in strategy_result
        
        # Step 4: Verify staking-specific results
        staking_orders = [
            order for order in strategy_result["execution_orders"]
            if order["action_type"] == "stake"
        ]
        
        assert len(staking_orders) > 0
        assert all(order["asset"] == "ETH" for order in staking_orders)
        assert all(order["venue"] == "ethereum_staking" for order in staking_orders)
    
    def test_eth_staking_only_apy_calculation(self, real_data_provider, real_components):
        """Test ETH staking only APY calculation accuracy."""
        strategy_manager = real_components["strategy_manager"]
        
        # Step 1: Configure strategy with known parameters
        strategy_config = {
            "strategy_mode": "eth_staking_only",
            "share_class": "ETH",
            "asset": "ETH",
            "initial_capital": 100.0,
            "staking_parameters": {
                "staking_rewards_rate": 0.05,  # 5% APY
                "staking_duration_days": 365
            }
        }
        
        # Step 2: Execute strategy
        strategy_result = strategy_manager.execute_strategy(strategy_config)
        
        # Step 3: Verify APY calculation
        expected_annual_return = 100.0 * 0.05  # 5 ETH
        actual_return = strategy_result["final_pnl"] - strategy_result["initial_capital"]
        
        # Allow for some variance in calculation
        assert abs(actual_return - expected_annual_return) < 1.0  # Within 1 ETH
        
        # Step 4: Verify APY is reasonable (3-8% range)
        calculated_apy = (actual_return / strategy_result["initial_capital"]) * 100
        assert 3.0 <= calculated_apy <= 8.0
    
    def test_eth_staking_only_risk_management(self, real_data_provider, real_components):
        """Test ETH staking only risk management."""
        strategy_manager = real_components["strategy_manager"]
        risk_monitor = real_components["risk_monitor"]
        
        # Step 1: Configure strategy with risk limits
        strategy_config = {
            "strategy_mode": "eth_staking_only",
            "share_class": "ETH",
            "asset": "ETH",
            "initial_capital": 100.0,
            "max_drawdown": 0.1,  # 10% max drawdown
            "risk_parameters": {
                "max_staking_ratio": 0.95,  # Max 95% in staking
                "min_liquidity_ratio": 0.05  # Min 5% liquid
            }
        }
        
        # Step 2: Execute strategy
        strategy_result = strategy_manager.execute_strategy(strategy_config)
        
        # Step 3: Verify risk management
        assert strategy_result["max_drawdown"] <= 0.1
        
        # Step 4: Verify staking ratio limits
        total_staked = sum(
            order["size"] for order in strategy_result["execution_orders"]
            if order["action_type"] == "stake"
        )
        
        staking_ratio = total_staked / strategy_result["initial_capital"]
        assert staking_ratio <= 0.95  # Should not exceed max staking ratio
        
        # Step 5: Verify liquidity maintenance
        total_liquid = strategy_result["initial_capital"] - total_staked
        liquidity_ratio = total_liquid / strategy_result["initial_capital"]
        assert liquidity_ratio >= 0.05  # Should maintain min liquidity
    
    def test_eth_staking_only_unstaking_flow(self, real_data_provider, real_components):
        """Test ETH staking only unstaking flow."""
        strategy_manager = real_components["strategy_manager"]
        
        # Step 1: Configure strategy with unstaking
        strategy_config = {
            "strategy_mode": "eth_staking_only",
            "share_class": "ETH",
            "asset": "ETH",
            "initial_capital": 100.0,
            "staking_parameters": {
                "unstaking_period_days": 7,
                "unstaking_trigger_conditions": ["max_drawdown_reached", "strategy_end"]
            }
        }
        
        # Step 2: Execute strategy
        strategy_result = strategy_manager.execute_strategy(strategy_config)
        
        # Step 3: Verify unstaking orders
        unstaking_orders = [
            order for order in strategy_result["execution_orders"]
            if order["action_type"] == "unstake"
        ]
        
        if unstaking_orders:
            assert all(order["asset"] == "ETH" for order in unstaking_orders)
            assert all(order["venue"] == "ethereum_staking" for order in unstaking_orders)
            
            # Verify unstaking timing
            for order in unstaking_orders:
                assert "unstaking_delay_days" in order
                assert order["unstaking_delay_days"] == 7
    
    def test_eth_staking_only_slashing_protection(self, real_data_provider, real_components):
        """Test ETH staking only slashing protection."""
        strategy_manager = real_components["strategy_manager"]
        
        # Step 1: Configure strategy with slashing protection
        strategy_config = {
            "strategy_mode": "eth_staking_only",
            "share_class": "ETH",
            "asset": "ETH",
            "initial_capital": 100.0,
            "staking_parameters": {
                "slashing_protection": True,
                "max_slashing_risk": 0.01,  # Max 1% slashing risk
                "validator_diversification": True
            }
        }
        
        # Step 2: Execute strategy
        strategy_result = strategy_manager.execute_strategy(strategy_config)
        
        # Step 3: Verify slashing protection
        assert "slashing_risk_analysis" in strategy_result
        assert strategy_result["slashing_risk_analysis"]["max_slashing_risk"] <= 0.01
        
        # Step 4: Verify validator diversification
        if "validator_breakdown" in strategy_result:
            validator_breakdown = strategy_result["validator_breakdown"]
            assert len(validator_breakdown) > 1  # Should use multiple validators
            
            # No single validator should have more than 50% of stake
            max_validator_share = max(validator_breakdown.values())
            assert max_validator_share <= 0.5
    
    def test_eth_staking_only_rewards_distribution(self, real_data_provider, real_components):
        """Test ETH staking only rewards distribution."""
        strategy_manager = real_components["strategy_manager"]
        
        # Step 1: Configure strategy
        strategy_config = {
            "strategy_mode": "eth_staking_only",
            "share_class": "ETH",
            "asset": "ETH",
            "initial_capital": 100.0,
            "staking_parameters": {
                "rewards_distribution": "proportional",
                "rewards_compounding": True
            }
        }
        
        # Step 2: Execute strategy
        strategy_result = strategy_manager.execute_strategy(strategy_config)
        
        # Step 3: Verify rewards distribution
        assert "rewards_breakdown" in strategy_result
        rewards_breakdown = strategy_result["rewards_breakdown"]
        
        assert "staking_rewards" in rewards_breakdown
        assert "total_rewards" in rewards_breakdown
        assert "rewards_rate" in rewards_breakdown
        
        # Step 4: Verify rewards are positive
        assert rewards_breakdown["staking_rewards"] > 0
        assert rewards_breakdown["total_rewards"] > 0
        assert rewards_breakdown["rewards_rate"] > 0
    
    def test_eth_staking_only_performance_metrics(self, real_data_provider, real_components):
        """Test ETH staking only performance metrics."""
        strategy_manager = real_components["strategy_manager"]
        
        # Step 1: Configure strategy
        strategy_config = {
            "strategy_mode": "eth_staking_only",
            "share_class": "ETH",
            "asset": "ETH",
            "initial_capital": 100.0,
            "performance_tracking": True
        }
        
        # Step 2: Execute strategy
        strategy_result = strategy_manager.execute_strategy(strategy_config)
        
        # Step 3: Verify performance metrics
        assert "performance_metrics" in strategy_result
        performance = strategy_result["performance_metrics"]
        
        assert "total_return" in performance
        assert "annualized_return" in performance
        assert "sharpe_ratio" in performance
        assert "max_drawdown" in performance
        assert "volatility" in performance
        
        # Step 4: Verify metrics are reasonable
        assert performance["total_return"] > 0  # Should be profitable
        assert 3.0 <= performance["annualized_return"] <= 8.0  # Reasonable APY
        assert performance["max_drawdown"] <= 0.1  # Should not exceed max drawdown
        assert performance["volatility"] >= 0  # Volatility should be non-negative
    
    def test_eth_staking_only_error_handling(self, real_data_provider, real_components):
        """Test ETH staking only error handling."""
        strategy_manager = real_components["strategy_manager"]
        
        # Step 1: Test with invalid configuration
        invalid_config = {
            "strategy_mode": "eth_staking_only",
            "share_class": "ETH",
            "asset": "ETH",
            "initial_capital": -100.0,  # Invalid negative capital
            "staking_parameters": {
                "min_staking_amount": 32.0
            }
        }
        
        # Step 2: Verify error handling
        with pytest.raises(ValueError, match="initial_capital must be positive"):
            strategy_manager.execute_strategy(invalid_config)
        
        # Step 3: Test with insufficient capital
        insufficient_config = {
            "strategy_mode": "eth_staking_only",
            "share_class": "ETH",
            "asset": "ETH",
            "initial_capital": 10.0,  # Less than min staking amount
            "staking_parameters": {
                "min_staking_amount": 32.0
            }
        }
        
        # Step 4: Verify insufficient capital handling
        with pytest.raises(ValueError, match="Insufficient capital for staking"):
            strategy_manager.execute_strategy(insufficient_config)
    
    def test_eth_staking_only_data_validation(self, real_data_provider, real_components):
        """Test ETH staking only data validation."""
        strategy_manager = real_components["strategy_manager"]
        
        # Step 1: Configure strategy
        strategy_config = {
            "strategy_mode": "eth_staking_only",
            "share_class": "ETH",
            "asset": "ETH",
            "initial_capital": 100.0,
            "staking_parameters": {
                "min_staking_amount": 32.0,
                "staking_rewards_rate": 0.05,
                "unstaking_period_days": 7
            }
        }
        
        # Step 2: Execute strategy
        strategy_result = strategy_manager.execute_strategy(strategy_config)
        
        # Step 3: Validate result structure
        assert isinstance(strategy_result, dict)
        assert "strategy_mode" in strategy_result
        assert "share_class" in strategy_result
        assert "initial_capital" in strategy_result
        assert "final_pnl" in strategy_result
        assert "execution_orders" in strategy_result
        
        # Step 4: Validate execution orders
        for order in strategy_result["execution_orders"]:
            assert "action_type" in order
            assert "asset" in order
            assert "size" in order
            assert "venue" in order
            assert order["asset"] == "ETH"
            assert order["size"] > 0
            assert order["venue"] in ["ethereum_staking", "ethereum"]
        
        # Step 5: Validate numerical values
        assert strategy_result["initial_capital"] > 0
        assert strategy_result["final_pnl"] >= 0  # Should not lose money in staking
        assert len(strategy_result["execution_orders"]) > 0
