"""
Integration test for Risk → Strategy data flow.

Tests the data flow from Risk Monitor to Strategy Manager per WORKFLOW_GUIDE.md.
"""

import pytest
from datetime import datetime, timedelta


class TestDataFlowRiskToStrategy:
    """Test Risk → Strategy data flow integration."""
    
    def test_risk_to_strategy_data_flow(self, real_components, real_data_provider):
        """Test complete data flow from risk assessment to strategy decisions."""
        risk_monitor = real_components["risk_monitor"]
        strategy_manager = real_components["strategy_manager"]
        
        # Step 1: Calculate risk metrics
        positions = real_components["position_monitor"].collect_positions()
        exposures = real_components["exposure_monitor"].calculate_exposures(positions)
        risk_metrics = risk_monitor.calculate_risk_metrics(exposures)
        
        assert risk_metrics is not None
        assert len(risk_metrics) > 0
        
        # Step 2: Generate strategy decisions based on risk
        strategy_decisions = strategy_manager.generate_strategy_decisions(risk_metrics)
        
        assert strategy_decisions is not None
        assert len(strategy_decisions) > 0
        
        # Step 3: Verify data flow integrity
        for decision in strategy_decisions:
            assert "action_type" in decision
            assert "asset" in decision
            assert "size" in decision
            assert "reasoning" in decision
            assert "risk_justification" in decision
    
    def test_risk_breach_to_strategy_adjustment(self, real_components, real_data_provider):
        """Test that risk breaches trigger appropriate strategy adjustments."""
        risk_monitor = real_components["risk_monitor"]
        strategy_manager = real_components["strategy_manager"]
        
        # Step 1: Calculate risk metrics and check for breaches
        positions = real_components["position_monitor"].collect_positions()
        exposures = real_components["exposure_monitor"].calculate_exposures(positions)
        risk_metrics = risk_monitor.calculate_risk_metrics(exposures)
        breaches = risk_monitor.check_risk_breaches(exposures)
        
        # Step 2: Generate strategy decisions considering breaches
        strategy_decisions = strategy_manager.generate_strategy_decisions(
            risk_metrics, risk_breaches=breaches
        )
        
        # Step 3: Verify breach-driven decisions
        if breaches:
            # Should have risk mitigation actions
            risk_mitigation_actions = [
                decision for decision in strategy_decisions
                if "risk_mitigation" in decision["action_type"] or
                   "reduce_exposure" in decision["action_type"] or
                   "hedge" in decision["action_type"]
            ]
            assert len(risk_mitigation_actions) > 0
    
    def test_risk_limits_to_strategy_constraints(self, real_components, real_data_provider):
        """Test that risk limits flow correctly to strategy constraints."""
        risk_monitor = real_components["risk_monitor"]
        strategy_manager = real_components["strategy_manager"]
        
        # Step 1: Get risk limits and current risk metrics
        risk_limits = risk_monitor.get_risk_limits()
        positions = real_components["position_monitor"].collect_positions()
        exposures = real_components["exposure_monitor"].calculate_exposures(positions)
        risk_metrics = risk_monitor.calculate_risk_metrics(exposures)
        
        # Step 2: Generate strategy decisions with risk constraints
        strategy_decisions = strategy_manager.generate_strategy_decisions(
            risk_metrics, risk_limits=risk_limits
        )
        
        # Step 3: Verify decisions respect risk limits
        for decision in strategy_decisions:
            if decision["action_type"] == "increase_exposure":
                # Should not exceed risk limits
                assert decision["size"] <= risk_limits.get("max_position_size", float('inf'))
    
    def test_risk_correlation_to_strategy_diversification(self, real_components, real_data_provider):
        """Test that risk correlations flow correctly to strategy diversification decisions."""
        risk_monitor = real_components["risk_monitor"]
        strategy_manager = real_components["strategy_manager"]
        
        # Step 1: Calculate correlation risks
        positions = real_components["position_monitor"].collect_positions()
        exposures = real_components["exposure_monitor"].calculate_exposures(positions)
        correlation_risks = risk_monitor.calculate_correlation_risks(exposures)
        
        # Step 2: Generate strategy decisions considering correlations
        strategy_decisions = strategy_manager.generate_strategy_decisions(
            risk_metrics=[], correlation_risks=correlation_risks
        )
        
        # Step 3: Verify diversification decisions
        diversification_actions = [
            decision for decision in strategy_decisions
            if "diversify" in decision["action_type"] or
               "rebalance" in decision["action_type"]
        ]
        
        # Should have diversification actions if high correlations exist
        high_correlations = [
            corr for corr in correlation_risks
            if abs(corr["correlation"]) > 0.7
        ]
        
        if high_correlations:
            assert len(diversification_actions) > 0
    
    def test_risk_volatility_to_strategy_timing(self, real_components, real_data_provider):
        """Test that risk volatility flows correctly to strategy timing decisions."""
        risk_monitor = real_components["risk_monitor"]
        strategy_manager = real_components["strategy_manager"]
        
        # Step 1: Calculate volatility metrics
        positions = real_components["position_monitor"].collect_positions()
        exposures = real_components["exposure_monitor"].calculate_exposures(positions)
        volatility_metrics = risk_monitor.calculate_volatility_metrics(exposures)
        
        # Step 2: Generate strategy decisions considering volatility
        strategy_decisions = strategy_manager.generate_strategy_decisions(
            risk_metrics=[], volatility_metrics=volatility_metrics
        )
        
        # Step 3: Verify volatility-driven timing decisions
        timing_actions = [
            decision for decision in strategy_decisions
            if "wait" in decision["action_type"] or
               "delay" in decision["action_type"] or
               "accelerate" in decision["action_type"]
        ]
        
        # Should have timing adjustments based on volatility
        high_volatility = any(
            vol["volatility"] > 0.3 for vol in volatility_metrics
        )
        
        if high_volatility:
            assert len(timing_actions) > 0
    
    def test_risk_stress_scenarios_to_strategy_contingency(self, real_components, real_data_provider):
        """Test that risk stress scenarios flow correctly to strategy contingency planning."""
        risk_monitor = real_components["risk_monitor"]
        strategy_manager = real_components["strategy_manager"]
        
        # Step 1: Calculate stress scenarios
        positions = real_components["position_monitor"].collect_positions()
        exposures = real_components["exposure_monitor"].calculate_exposures(positions)
        
        stress_scenarios = [
            {"name": "market_crash", "price_shock": -0.20},
            {"name": "volatility_spike", "volatility_multiplier": 2.0}
        ]
        
        stress_results = risk_monitor.calculate_stress_scenarios(exposures, stress_scenarios)
        
        # Step 2: Generate contingency strategy decisions
        contingency_decisions = strategy_manager.generate_contingency_decisions(stress_results)
        
        # Step 3: Verify contingency planning
        assert contingency_decisions is not None
        assert len(contingency_decisions) > 0
        
        for decision in contingency_decisions:
            assert "scenario" in decision
            assert "contingency_action" in decision
            assert "trigger_conditions" in decision
            assert "execution_priority" in decision
    
    def test_risk_historical_to_strategy_learning(self, real_components, real_data_provider):
        """Test that historical risk data flows correctly to strategy learning."""
        risk_monitor = real_components["risk_monitor"]
        strategy_manager = real_components["strategy_manager"]
        
        # Step 1: Get historical risk data
        historical_risk_data = risk_monitor.get_historical_risk_metrics(
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now()
        )
        
        # Step 2: Update strategy based on historical risk patterns
        strategy_updates = strategy_manager.update_strategy_from_risk_history(
            historical_risk_data
        )
        
        # Step 3: Verify strategy learning
        assert strategy_updates is not None
        assert "risk_pattern_analysis" in strategy_updates
        assert "strategy_adjustments" in strategy_updates
        assert "confidence_score" in strategy_updates
    
    def test_risk_to_strategy_performance(self, real_components, real_data_provider):
        """Test performance of risk to strategy data flow."""
        import time
        
        risk_monitor = real_components["risk_monitor"]
        strategy_manager = real_components["strategy_manager"]
        
        # Step 1: Calculate risk metrics
        positions = real_components["position_monitor"].collect_positions()
        exposures = real_components["exposure_monitor"].calculate_exposures(positions)
        start_time = time.time()
        risk_metrics = risk_monitor.calculate_risk_metrics(exposures)
        risk_time = time.time() - start_time
        
        # Step 2: Generate strategy decisions
        start_time = time.time()
        strategy_decisions = strategy_manager.generate_strategy_decisions(risk_metrics)
        strategy_time = time.time() - start_time
        
        # Step 3: Verify performance is within acceptable limits
        assert risk_time < 5.0  # Risk calculation should be reasonable
        assert strategy_time < 3.0  # Strategy decisions should be fast
        
        # Step 4: Verify data flow produces results
        assert len(risk_metrics) > 0
        assert len(strategy_decisions) > 0
    
    def test_risk_to_strategy_error_handling(self, real_components, real_data_provider):
        """Test error handling in risk to strategy data flow."""
        risk_monitor = real_components["risk_monitor"]
        strategy_manager = real_components["strategy_manager"]
        
        # Step 1: Test with invalid risk data
        invalid_risk_metrics = [
            {"asset": "INVALID", "total_risk": -1000.0},  # Negative risk
            {"asset": "USDT", "total_risk": "invalid"},   # Wrong type
            {"asset": "", "total_risk": 1000.0}          # Empty asset
        ]
        
        # Step 2: Verify strategy manager handles invalid data gracefully
        try:
            strategy_decisions = strategy_manager.generate_strategy_decisions(invalid_risk_metrics)
            # Should either return empty results or handle gracefully
            assert isinstance(strategy_decisions, list)
        except Exception as e:
            # Should be a specific, informative error
            assert "risk" in str(e).lower() or "strategy" in str(e).lower()
    
    def test_risk_to_strategy_data_validation(self, real_components, real_data_provider):
        """Test data validation in risk to strategy data flow."""
        risk_monitor = real_components["risk_monitor"]
        strategy_manager = real_components["strategy_manager"]
        
        # Step 1: Calculate risk metrics
        positions = real_components["position_monitor"].collect_positions()
        exposures = real_components["exposure_monitor"].calculate_exposures(positions)
        risk_metrics = risk_monitor.calculate_risk_metrics(exposures)
        
        # Step 2: Validate risk data structure
        for risk in risk_metrics:
            assert "asset" in risk
            assert "total_risk" in risk
            assert "var_95" in risk
            assert "max_drawdown" in risk
            assert isinstance(risk["total_risk"], (int, float))
            assert risk["total_risk"] >= 0
            assert 0 <= risk["var_95"] <= 1
        
        # Step 3: Generate and validate strategy decisions
        strategy_decisions = strategy_manager.generate_strategy_decisions(risk_metrics)
        
        for decision in strategy_decisions:
            assert "action_type" in decision
            assert "asset" in decision
            assert "size" in decision
            assert "reasoning" in decision
            assert isinstance(decision["size"], (int, float))
            assert decision["size"] >= 0
