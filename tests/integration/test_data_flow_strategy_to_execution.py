"""
Integration test for Strategy → Execution data flow.

Tests the data flow from Strategy Manager to Execution Manager per WORKFLOW_GUIDE.md.
"""

import pytest
from datetime import datetime, timedelta


class TestDataFlowStrategyToExecution:
    """Test Strategy → Execution data flow integration."""
    
    def test_strategy_to_execution_data_flow(self, real_components, real_data_provider):
        """Test complete data flow from strategy decisions to execution orders."""
        strategy_manager = real_components["strategy_manager"]
        execution_manager = real_components["execution_manager"]
        
        # Step 1: Generate strategy decisions
        positions = real_components["position_monitor"].collect_positions()
        exposures = real_components["exposure_monitor"].calculate_exposures(positions)
        risk_metrics = real_components["risk_monitor"].calculate_risk_metrics(exposures)
        strategy_decisions = strategy_manager.generate_strategy_decisions(risk_metrics)
        
        assert strategy_decisions is not None
        assert len(strategy_decisions) > 0
        
        # Step 2: Convert strategy decisions to execution orders
        execution_orders = execution_manager.convert_strategy_to_orders(strategy_decisions)
        
        assert execution_orders is not None
        assert len(execution_orders) > 0
        
        # Step 3: Verify data flow integrity
        for order in execution_orders:
            assert "order_id" in order
            assert "strategy_decision_id" in order
            assert "action_type" in order
            assert "asset" in order
            assert "size" in order
            assert "venue" in order
            assert "order_type" in order
            assert "priority" in order
    
    def test_strategy_decision_routing_to_execution(self, real_components, real_data_provider):
        """Test that strategy decisions are routed correctly to appropriate execution venues."""
        strategy_manager = real_components["strategy_manager"]
        execution_manager = real_components["execution_manager"]
        
        # Step 1: Generate strategy decisions with venue preferences
        positions = real_components["position_monitor"].collect_positions()
        exposures = real_components["exposure_monitor"].calculate_exposures(positions)
        risk_metrics = real_components["risk_monitor"].calculate_risk_metrics(exposures)
        strategy_decisions = strategy_manager.generate_strategy_decisions(risk_metrics)
        
        # Step 2: Route decisions to execution venues
        routed_orders = execution_manager.route_orders_to_venues(strategy_decisions)
        
        # Step 3: Verify routing logic
        for order in routed_orders:
            assert "venue" in order
            assert order["venue"] in ["binance", "okx", "bybit", "aave", "morpho"]
            
            # Verify venue selection logic
            if order["action_type"] == "lend":
                assert order["venue"] in ["aave", "morpho"]
            elif order["action_type"] in ["buy", "sell"]:
                assert order["venue"] in ["binance", "okx", "bybit"]
    
    def test_strategy_priority_to_execution_sequence(self, real_components, real_data_provider):
        """Test that strategy decision priorities flow correctly to execution sequence."""
        strategy_manager = real_components["strategy_manager"]
        execution_manager = real_components["execution_manager"]
        
        # Step 1: Generate strategy decisions with priorities
        positions = real_components["position_monitor"].collect_positions()
        exposures = real_components["exposure_monitor"].calculate_exposures(positions)
        risk_metrics = real_components["risk_monitor"].calculate_risk_metrics(exposures)
        strategy_decisions = strategy_manager.generate_strategy_decisions(risk_metrics)
        
        # Step 2: Convert to execution orders with priority sequencing
        execution_orders = execution_manager.convert_strategy_to_orders(strategy_decisions)
        sequenced_orders = execution_manager.sequence_orders_by_priority(execution_orders)
        
        # Step 3: Verify priority sequencing
        priorities = [order["priority"] for order in sequenced_orders]
        assert priorities == sorted(priorities, reverse=True)  # Higher priority first
        
        # Verify priority mapping
        for order in sequenced_orders:
            if "risk_mitigation" in order["action_type"]:
                assert order["priority"] >= 8  # High priority for risk mitigation
            elif "rebalance" in order["action_type"]:
                assert order["priority"] >= 6  # Medium-high priority for rebalancing
            else:
                assert order["priority"] >= 4  # Standard priority for other actions
    
    def test_strategy_size_validation_to_execution(self, real_components, real_data_provider):
        """Test that strategy decision sizes are validated before execution."""
        strategy_manager = real_components["strategy_manager"]
        execution_manager = real_components["execution_manager"]
        
        # Step 1: Generate strategy decisions
        positions = real_components["position_monitor"].collect_positions()
        exposures = real_components["exposure_monitor"].calculate_exposures(positions)
        risk_metrics = real_components["risk_monitor"].calculate_risk_metrics(exposures)
        strategy_decisions = strategy_manager.generate_strategy_decisions(risk_metrics)
        
        # Step 2: Validate and convert to execution orders
        validated_orders = execution_manager.validate_and_convert_orders(strategy_decisions)
        
        # Step 3: Verify size validation
        for order in validated_orders:
            assert order["size"] > 0  # All orders should have positive size
            assert order["size"] <= 1000000  # Should not exceed maximum position size
            
            # Verify size is within venue limits
            venue_limits = execution_manager.get_venue_limits(order["venue"])
            assert order["size"] >= venue_limits["min_order_size"]
            assert order["size"] <= venue_limits["max_order_size"]
    
    def test_strategy_timing_to_execution_scheduling(self, real_components, real_data_provider):
        """Test that strategy timing flows correctly to execution scheduling."""
        strategy_manager = real_components["strategy_manager"]
        execution_manager = real_components["execution_manager"]
        
        # Step 1: Generate strategy decisions with timing requirements
        positions = real_components["position_monitor"].collect_positions()
        exposures = real_components["exposure_monitor"].calculate_exposures(positions)
        risk_metrics = real_components["risk_monitor"].calculate_risk_metrics(exposures)
        strategy_decisions = strategy_manager.generate_strategy_decisions(risk_metrics)
        
        # Step 2: Schedule execution orders
        scheduled_orders = execution_manager.schedule_orders(strategy_decisions)
        
        # Step 3: Verify scheduling logic
        for order in scheduled_orders:
            assert "scheduled_time" in order
            assert "execution_window" in order
            
            # Verify timing constraints
            if "immediate" in order["action_type"]:
                assert order["execution_window"] <= 60  # Within 1 minute
            elif "urgent" in order["action_type"]:
                assert order["execution_window"] <= 300  # Within 5 minutes
            else:
                assert order["execution_window"] <= 1800  # Within 30 minutes
    
    def test_strategy_risk_controls_to_execution_limits(self, real_components, real_data_provider):
        """Test that strategy risk controls flow correctly to execution limits."""
        strategy_manager = real_components["strategy_manager"]
        execution_manager = real_components["execution_manager"]
        
        # Step 1: Generate strategy decisions with risk controls
        positions = real_components["position_monitor"].collect_positions()
        exposures = real_components["exposure_monitor"].calculate_exposures(positions)
        risk_metrics = real_components["risk_monitor"].calculate_risk_metrics(exposures)
        strategy_decisions = strategy_manager.generate_strategy_decisions(risk_metrics)
        
        # Step 2: Apply execution limits based on risk controls
        limited_orders = execution_manager.apply_risk_limits(strategy_decisions)
        
        # Step 3: Verify risk limit application
        for order in limited_orders:
            assert "risk_limits_applied" in order
            assert "max_execution_size" in order
            assert "stop_loss_trigger" in order
            assert "take_profit_trigger" in order
            
            # Verify size doesn't exceed risk limits
            assert order["size"] <= order["max_execution_size"]
    
    def test_strategy_execution_monitoring(self, real_components, real_data_provider):
        """Test that strategy decisions are properly monitored during execution."""
        strategy_manager = real_components["strategy_manager"]
        execution_manager = real_components["execution_manager"]
        
        # Step 1: Generate and execute strategy decisions
        positions = real_components["position_monitor"].collect_positions()
        exposures = real_components["exposure_monitor"].calculate_exposures(positions)
        risk_metrics = real_components["risk_monitor"].calculate_risk_metrics(exposures)
        strategy_decisions = strategy_manager.generate_strategy_decisions(risk_metrics)
        
        execution_orders = execution_manager.convert_strategy_to_orders(strategy_decisions)
        
        # Step 2: Monitor execution progress
        execution_status = execution_manager.monitor_execution_progress(execution_orders)
        
        # Step 3: Verify monitoring data
        assert execution_status is not None
        assert "total_orders" in execution_status
        assert "completed_orders" in execution_status
        assert "failed_orders" in execution_status
        assert "pending_orders" in execution_status
        assert "execution_rate" in execution_status
        
        # Verify execution rate calculation
        total = execution_status["total_orders"]
        completed = execution_status["completed_orders"]
        if total > 0:
            assert execution_status["execution_rate"] == completed / total
    
    def test_strategy_to_execution_performance(self, real_components, real_data_provider):
        """Test performance of strategy to execution data flow."""
        import time
        
        strategy_manager = real_components["strategy_manager"]
        execution_manager = real_components["execution_manager"]
        
        # Step 1: Generate strategy decisions
        positions = real_components["position_monitor"].collect_positions()
        exposures = real_components["exposure_monitor"].calculate_exposures(positions)
        risk_metrics = real_components["risk_monitor"].calculate_risk_metrics(exposures)
        start_time = time.time()
        strategy_decisions = strategy_manager.generate_strategy_decisions(risk_metrics)
        strategy_time = time.time() - start_time
        
        # Step 2: Convert to execution orders
        start_time = time.time()
        execution_orders = execution_manager.convert_strategy_to_orders(strategy_decisions)
        execution_time = time.time() - start_time
        
        # Step 3: Verify performance is within acceptable limits
        assert strategy_time < 3.0  # Strategy decisions should be fast
        assert execution_time < 2.0  # Order conversion should be very fast
        
        # Step 4: Verify data flow produces results
        assert len(strategy_decisions) > 0
        assert len(execution_orders) > 0
    
    def test_strategy_to_execution_error_handling(self, real_components, real_data_provider):
        """Test error handling in strategy to execution data flow."""
        strategy_manager = real_components["strategy_manager"]
        execution_manager = real_components["execution_manager"]
        
        # Step 1: Test with invalid strategy decisions
        invalid_strategy_decisions = [
            {"action_type": "INVALID", "asset": "USDT", "size": -1000.0},  # Negative size
            {"action_type": "buy", "asset": "", "size": 1000.0},          # Empty asset
            {"action_type": "sell", "asset": "USDT", "size": "invalid"}   # Wrong type
        ]
        
        # Step 2: Verify execution manager handles invalid data gracefully
        try:
            execution_orders = execution_manager.convert_strategy_to_orders(invalid_strategy_decisions)
            # Should either return empty results or handle gracefully
            assert isinstance(execution_orders, list)
        except Exception as e:
            # Should be a specific, informative error
            assert "strategy" in str(e).lower() or "execution" in str(e).lower()
    
    def test_strategy_to_execution_data_validation(self, real_components, real_data_provider):
        """Test data validation in strategy to execution data flow."""
        strategy_manager = real_components["strategy_manager"]
        execution_manager = real_components["execution_manager"]
        
        # Step 1: Generate strategy decisions
        positions = real_components["position_monitor"].collect_positions()
        exposures = real_components["exposure_monitor"].calculate_exposures(positions)
        risk_metrics = real_components["risk_monitor"].calculate_risk_metrics(exposures)
        strategy_decisions = strategy_manager.generate_strategy_decisions(risk_metrics)
        
        # Step 2: Validate strategy decision structure
        for decision in strategy_decisions:
            assert "action_type" in decision
            assert "asset" in decision
            assert "size" in decision
            assert "reasoning" in decision
            assert isinstance(decision["size"], (int, float))
            assert decision["size"] >= 0
        
        # Step 3: Convert and validate execution orders
        execution_orders = execution_manager.convert_strategy_to_orders(strategy_decisions)
        
        for order in execution_orders:
            assert "order_id" in order
            assert "strategy_decision_id" in order
            assert "action_type" in order
            assert "asset" in order
            assert "size" in order
            assert "venue" in order
            assert "order_type" in order
            assert "priority" in order
            assert isinstance(order["size"], (int, float))
            assert order["size"] > 0
            assert 1 <= order["priority"] <= 10
