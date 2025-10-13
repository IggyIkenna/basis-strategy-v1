"""
Integration test for Exposure → Risk data flow.

Tests the data flow from Exposure Monitor to Risk Monitor per WORKFLOW_GUIDE.md.
"""

import pytest
from datetime import datetime, timedelta


class TestDataFlowExposureToRisk:
    """Test Exposure → Risk data flow integration."""
    
    def test_exposure_to_risk_data_flow(self, real_components, real_data_provider):
        """Test complete data flow from exposure calculation to risk assessment."""
        exposure_monitor = real_components["exposure_monitor"]
        risk_monitor = real_components["risk_monitor"]
        
        # Step 1: Calculate exposures
        positions = real_components["position_monitor"].collect_positions()
        exposures = exposure_monitor.calculate_exposures(positions)
        
        assert exposures is not None
        assert len(exposures) > 0
        
        # Step 2: Calculate risk metrics from exposures
        risk_metrics = risk_monitor.calculate_risk_metrics(exposures)
        
        assert risk_metrics is not None
        assert len(risk_metrics) > 0
        
        # Step 3: Verify data flow integrity
        for risk in risk_metrics:
            assert "asset" in risk
            assert "total_risk" in risk
            assert "var_95" in risk
            assert "max_drawdown" in risk
            assert "correlation_risk" in risk
    
    def test_exposure_aggregation_to_risk(self, real_components, real_data_provider):
        """Test that exposure aggregation flows correctly to risk calculations."""
        exposure_monitor = real_components["exposure_monitor"]
        risk_monitor = real_components["risk_monitor"]
        
        # Step 1: Calculate exposures for multiple assets
        positions = real_components["position_monitor"].collect_positions()
        exposures = exposure_monitor.calculate_exposures(positions)
        
        # Step 2: Calculate portfolio-level risk from aggregated exposures
        portfolio_risk = risk_monitor.calculate_portfolio_risk(exposures)
        
        assert portfolio_risk is not None
        assert "total_portfolio_risk" in portfolio_risk
        assert "portfolio_var_95" in portfolio_risk
        assert "diversification_ratio" in portfolio_risk
        
        # Step 3: Verify portfolio risk is calculated from individual exposures
        individual_risks = [risk["total_risk"] for risk in risk_monitor.calculate_risk_metrics(exposures)]
        assert portfolio_risk["total_portfolio_risk"] >= 0
        assert portfolio_risk["total_portfolio_risk"] <= sum(individual_risks)  # Diversification benefit
    
    def test_exposure_venue_risk_breakdown(self, real_components, real_data_provider):
        """Test that exposure venue breakdown flows correctly to venue risk analysis."""
        exposure_monitor = real_components["exposure_monitor"]
        risk_monitor = real_components["risk_monitor"]
        
        # Step 1: Calculate exposures with venue breakdown
        positions = real_components["position_monitor"].collect_positions()
        exposures = exposure_monitor.calculate_exposures(positions)
        
        # Step 2: Calculate venue-specific risk metrics
        venue_risks = risk_monitor.calculate_venue_risks(exposures)
        
        assert venue_risks is not None
        assert len(venue_risks) > 0
        
        # Step 3: Verify venue risk structure
        for venue_risk in venue_risks:
            assert "venue" in venue_risk
            assert "venue_risk" in venue_risk
            assert "liquidity_risk" in venue_risk
    
    def test_exposure_correlation_to_risk(self, real_components, real_data_provider):
        """Test that exposure correlations flow correctly to correlation risk calculations."""
        exposure_monitor = real_components["exposure_monitor"]
        risk_monitor = real_components["risk_monitor"]
        
        # Step 1: Calculate exposures for multiple assets
        positions = real_components["position_monitor"].collect_positions()
        exposures = exposure_monitor.calculate_exposures(positions)
        
        # Step 2: Calculate correlation risk from exposures
        correlation_risks = risk_monitor.calculate_correlation_risks(exposures)
        
        assert correlation_risks is not None
        assert len(correlation_risks) > 0
        
        # Step 3: Verify correlation risk structure
        for corr_risk in correlation_risks:
            assert "asset_pair" in corr_risk
            assert "correlation" in corr_risk
            assert "correlation_risk" in corr_risk
            assert -1.0 <= corr_risk["correlation"] <= 1.0
    
    def test_exposure_limits_to_risk_breach_detection(self, real_components, real_data_provider):
        """Test that exposure limits flow correctly to risk breach detection."""
        exposure_monitor = real_components["exposure_monitor"]
        risk_monitor = real_components["risk_monitor"]
        
        # Step 1: Calculate exposures
        positions = real_components["position_monitor"].collect_positions()
        exposures = exposure_monitor.calculate_exposures(positions)
        
        # Step 2: Check for risk limit breaches
        breaches = risk_monitor.check_risk_breaches(exposures)
        
        assert breaches is not None
        assert isinstance(breaches, list)
        
        # Step 3: Verify breach structure if any breaches exist
        for breach in breaches:
            assert "breach_type" in breach
            assert "asset" in breach
            assert "current_value" in breach
            assert "limit_value" in breach
            assert "severity" in breach
    
    def test_exposure_historical_to_risk_metrics(self, real_components, real_data_provider):
        """Test that historical exposure data flows correctly to risk metrics calculation."""
        exposure_monitor = real_components["exposure_monitor"]
        risk_monitor = real_components["risk_monitor"]
        
        # Step 1: Calculate current exposures
        positions = real_components["position_monitor"].collect_positions()
        current_exposures = exposure_monitor.calculate_exposures(positions)
        
        # Step 2: Get historical exposure data
        historical_exposures = exposure_monitor.get_historical_exposures(
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now()
        )
        
        # Step 3: Calculate risk metrics using historical data
        historical_risk_metrics = risk_monitor.calculate_historical_risk_metrics(
            historical_exposures
        )
        
        assert historical_risk_metrics is not None
        assert "volatility" in historical_risk_metrics
        assert "sharpe_ratio" in historical_risk_metrics
        assert "max_drawdown" in historical_risk_metrics
        assert "var_95" in historical_risk_metrics
    
    def test_exposure_stress_testing_to_risk(self, real_components, real_data_provider):
        """Test that exposure stress testing flows correctly to stress risk scenarios."""
        exposure_monitor = real_components["exposure_monitor"]
        risk_monitor = real_components["risk_monitor"]
        
        # Step 1: Calculate base exposures
        positions = real_components["position_monitor"].collect_positions()
        base_exposures = exposure_monitor.calculate_exposures(positions)
        
        # Step 2: Apply stress scenarios to exposures
        stress_scenarios = [
            {"name": "market_crash", "price_shock": -0.20},
            {"name": "volatility_spike", "volatility_multiplier": 2.0},
            {"name": "liquidity_crisis", "liquidity_reduction": 0.5}
        ]
        
        stress_results = risk_monitor.calculate_stress_scenarios(base_exposures, stress_scenarios)
        
        assert stress_results is not None
        assert len(stress_results) == len(stress_scenarios)
        
        # Step 3: Verify stress scenario structure
        for stress_result in stress_results:
            assert "scenario_name" in stress_result
            assert "portfolio_impact" in stress_result
            assert "worst_case_loss" in stress_result
            assert "recovery_time_estimate" in stress_result
    
    def test_exposure_to_risk_performance(self, real_components, real_data_provider):
        """Test performance of exposure to risk data flow."""
        import time
        
        exposure_monitor = real_components["exposure_monitor"]
        risk_monitor = real_components["risk_monitor"]
        
        # Step 1: Calculate exposures
        positions = real_components["position_monitor"].collect_positions()
        start_time = time.time()
        exposures = exposure_monitor.calculate_exposures(positions)
        exposure_time = time.time() - start_time
        
        # Step 2: Calculate risk metrics
        start_time = time.time()
        risk_metrics = risk_monitor.calculate_risk_metrics(exposures)
        risk_time = time.time() - start_time
        
        # Step 3: Verify performance is within acceptable limits
        assert exposure_time < 3.0  # Exposure calculation should be fast
        assert risk_time < 5.0  # Risk calculation should be reasonable
        
        # Step 4: Verify data flow produces results
        assert len(exposures) > 0
        assert len(risk_metrics) > 0
    
    def test_exposure_to_risk_error_handling(self, real_components, real_data_provider):
        """Test error handling in exposure to risk data flow."""
        exposure_monitor = real_components["exposure_monitor"]
        risk_monitor = real_components["risk_monitor"]
        
        # Step 1: Test with invalid exposure data
        invalid_exposures = [
            {"asset": "INVALID", "total_exposure": -1000.0},  # Negative exposure
            {"asset": "USDT", "total_exposure": "invalid"},   # Wrong type
            {"asset": "", "total_exposure": 1000.0}          # Empty asset
        ]
        
        # Step 2: Verify risk monitor handles invalid data gracefully
        try:
            risk_metrics = risk_monitor.calculate_risk_metrics(invalid_exposures)
            # Should either return empty results or handle gracefully
            assert isinstance(risk_metrics, list)
        except Exception as e:
            # Should be a specific, informative error
            assert "exposure" in str(e).lower() or "risk" in str(e).lower()
    
    def test_exposure_to_risk_data_validation(self, real_components, real_data_provider):
        """Test data validation in exposure to risk data flow."""
        exposure_monitor = real_components["exposure_monitor"]
        risk_monitor = real_components["risk_monitor"]
        
        # Step 1: Calculate exposures
        positions = real_components["position_monitor"].collect_positions()
        exposures = exposure_monitor.calculate_exposures(positions)
        
        # Step 2: Validate exposure data structure
        for exposure in exposures:
            assert "asset" in exposure
            assert "total_exposure" in exposure
            assert "net_delta" in exposure
            assert "venue_breakdown" in exposure
            assert isinstance(exposure["total_exposure"], (int, float))
            assert exposure["total_exposure"] >= 0
        
        # Step 3: Calculate and validate risk metrics
        risk_metrics = risk_monitor.calculate_risk_metrics(exposures)
        
        for risk in risk_metrics:
            assert "asset" in risk
            assert "total_risk" in risk
            assert "var_95" in risk
            assert "max_drawdown" in risk
            assert isinstance(risk["total_risk"], (int, float))
            assert risk["total_risk"] >= 0
            assert 0 <= risk["var_95"] <= 1  # VaR should be between 0 and 1
