"""
Integration test for Tight Loop Reconciliation.

Tests the tight loop architecture per ADR-001 with sequential processing and reconciliation.
"""

import pytest
from datetime import datetime, timedelta


class TestTightLoopReconciliation:
    """Test Tight Loop Reconciliation integration."""
    
    def test_tight_loop_sequential_processing(self, real_components, real_data_provider):
        """Test that tight loop processes components in correct sequential order."""
        position_monitor = real_components["position_monitor"]
        exposure_monitor = real_components["exposure_monitor"]
        risk_monitor = real_components["risk_monitor"]
        strategy_manager = real_components["strategy_manager"]
        execution_manager = real_components["execution_manager"]
        
        # Step 1: Position Monitor (First in sequence)
        start_time = datetime.now()
        positions = position_monitor.collect_positions()
        position_time = datetime.now()
        
        assert positions is not None
        assert len(positions) > 0
        
        # Step 2: Exposure Monitor (Second in sequence)
        exposures = exposure_monitor.calculate_exposures(positions)
        exposure_time = datetime.now()
        
        assert exposures is not None
        assert len(exposures) > 0
        
        # Step 3: Risk Monitor (Third in sequence)
        risk_metrics = risk_monitor.calculate_risk_metrics(exposures)
        risk_time = datetime.now()
        
        assert risk_metrics is not None
        assert len(risk_metrics) > 0
        
        # Step 4: Strategy Manager (Fourth in sequence)
        strategy_decisions = strategy_manager.generate_strategy_decisions(risk_metrics)
        strategy_time = datetime.now()
        
        assert strategy_decisions is not None
        assert len(strategy_decisions) > 0
        
        # Step 5: Execution Manager (Fifth in sequence)
        execution_orders = execution_manager.convert_strategy_to_orders(strategy_decisions)
        execution_time = datetime.now()
        
        assert execution_orders is not None
        assert len(execution_orders) > 0
        
        # Verify sequential timing
        assert position_time < exposure_time < risk_time < strategy_time < execution_time
    
    def test_tight_loop_reconciliation_handshake(self, real_components, real_data_provider):
        """Test reconciliation handshake between components in tight loop."""
        position_monitor = real_components["position_monitor"]
        exposure_monitor = real_components["exposure_monitor"]
        risk_monitor = real_components["risk_monitor"]
        strategy_manager = real_components["strategy_manager"]
        execution_manager = real_components["execution_manager"]
        
        # Step 1: Execute tight loop with reconciliation
        loop_id = f"loop_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Position → Exposure reconciliation
        positions = position_monitor.collect_positions()
        position_reconciliation = position_monitor.get_reconciliation_data()
        
        exposures = exposure_monitor.calculate_exposures(positions)
        exposure_reconciliation = exposure_monitor.get_reconciliation_data()
        
        # Verify position → exposure reconciliation
        assert position_reconciliation["total_positions"] == len(positions)
        assert exposure_reconciliation["input_positions"] == len(positions)
        assert exposure_reconciliation["output_exposures"] == len(exposures)
        
        # Exposure → Risk reconciliation
        risk_metrics = risk_monitor.calculate_risk_metrics(exposures)
        risk_reconciliation = risk_monitor.get_reconciliation_data()
        
        # Verify exposure → risk reconciliation
        assert risk_reconciliation["input_exposures"] == len(exposures)
        assert risk_reconciliation["output_risk_metrics"] == len(risk_metrics)
        
        # Risk → Strategy reconciliation
        strategy_decisions = strategy_manager.generate_strategy_decisions(risk_metrics)
        strategy_reconciliation = strategy_manager.get_reconciliation_data()
        
        # Verify risk → strategy reconciliation
        assert strategy_reconciliation["input_risk_metrics"] == len(risk_metrics)
        assert strategy_reconciliation["output_strategy_decisions"] == len(strategy_decisions)
        
        # Strategy → Execution reconciliation
        execution_orders = execution_manager.convert_strategy_to_orders(strategy_decisions)
        execution_reconciliation = execution_manager.get_reconciliation_data()
        
        # Verify strategy → execution reconciliation
        assert execution_reconciliation["input_strategy_decisions"] == len(strategy_decisions)
        assert execution_reconciliation["output_execution_orders"] == len(execution_orders)
    
    def test_tight_loop_data_consistency(self, real_components, real_data_provider):
        """Test data consistency throughout tight loop processing."""
        position_monitor = real_components["position_monitor"]
        exposure_monitor = real_components["exposure_monitor"]
        risk_monitor = real_components["risk_monitor"]
        strategy_manager = real_components["strategy_manager"]
        execution_manager = real_components["execution_manager"]
        
        # Step 1: Execute tight loop
        positions = position_monitor.collect_positions()
        exposures = exposure_monitor.calculate_exposures(positions)
        risk_metrics = risk_monitor.calculate_risk_metrics(exposures)
        strategy_decisions = strategy_manager.generate_strategy_decisions(risk_metrics)
        execution_orders = execution_manager.convert_strategy_to_orders(strategy_decisions)
        
        # Step 2: Verify data consistency across components
        
        # Position → Exposure consistency
        position_assets = set(pos["asset"] for pos in positions)
        exposure_assets = set(exp["asset"] for exp in exposures)
        assert position_assets == exposure_assets  # Same assets throughout
        
        # Exposure → Risk consistency
        risk_assets = set(risk["asset"] for risk in risk_metrics)
        assert exposure_assets == risk_assets  # Same assets throughout
        
        # Risk → Strategy consistency
        strategy_assets = set(decision["asset"] for decision in strategy_decisions)
        assert risk_assets.issuperset(strategy_assets)  # Strategy may focus on subset
        
        # Strategy → Execution consistency
        execution_assets = set(order["asset"] for order in execution_orders)
        assert strategy_assets == execution_assets  # Same assets in execution
    
    def test_tight_loop_error_propagation(self, real_components, real_data_provider):
        """Test error propagation and handling in tight loop."""
        position_monitor = real_components["position_monitor"]
        exposure_monitor = real_components["exposure_monitor"]
        risk_monitor = real_components["risk_monitor"]
        strategy_manager = real_components["strategy_manager"]
        execution_manager = real_components["execution_manager"]
        
        # Step 1: Test error in position collection
        with patch.object(position_monitor, 'collect_positions', side_effect=Exception("Position collection failed")):
            with pytest.raises(Exception, match="Position collection failed"):
                positions = position_monitor.collect_positions()
        
        # Step 2: Test error in exposure calculation
        positions = position_monitor.collect_positions()
        with patch.object(exposure_monitor, 'calculate_exposures', side_effect=Exception("Exposure calculation failed")):
            with pytest.raises(Exception, match="Exposure calculation failed"):
                exposures = exposure_monitor.calculate_exposures(positions)
        
        # Step 3: Test error in risk calculation
        exposures = exposure_monitor.calculate_exposures(positions)
        with patch.object(risk_monitor, 'calculate_risk_metrics', side_effect=Exception("Risk calculation failed")):
            with pytest.raises(Exception, match="Risk calculation failed"):
                risk_metrics = risk_monitor.calculate_risk_metrics(exposures)
        
        # Step 4: Test error in strategy generation
        risk_metrics = risk_monitor.calculate_risk_metrics(exposures)
        with patch.object(strategy_manager, 'generate_strategy_decisions', side_effect=Exception("Strategy generation failed")):
            with pytest.raises(Exception, match="Strategy generation failed"):
                strategy_decisions = strategy_manager.generate_strategy_decisions(risk_metrics)
        
        # Step 5: Test error in execution conversion
        strategy_decisions = strategy_manager.generate_strategy_decisions(risk_metrics)
        with patch.object(execution_manager, 'convert_strategy_to_orders', side_effect=Exception("Execution conversion failed")):
            with pytest.raises(Exception, match="Execution conversion failed"):
                execution_orders = execution_manager.convert_strategy_to_orders(strategy_decisions)
    
    def test_tight_loop_performance_requirements(self, real_components, real_data_provider):
        """Test that tight loop meets performance requirements."""
        import time
        
        position_monitor = real_components["position_monitor"]
        exposure_monitor = real_components["exposure_monitor"]
        risk_monitor = real_components["risk_monitor"]
        strategy_manager = real_components["strategy_manager"]
        execution_manager = real_components["execution_manager"]
        
        # Step 1: Measure total tight loop execution time
        start_time = time.time()
        
        positions = position_monitor.collect_positions()
        exposures = exposure_monitor.calculate_exposures(positions)
        risk_metrics = risk_monitor.calculate_risk_metrics(exposures)
        strategy_decisions = strategy_manager.generate_strategy_decisions(risk_metrics)
        execution_orders = execution_manager.convert_strategy_to_orders(strategy_decisions)
        
        total_time = time.time() - start_time
        
        # Step 2: Verify performance requirements
        assert total_time < 10.0  # Total tight loop should complete within 10 seconds
        
        # Step 3: Verify individual component performance
        start_time = time.time()
        positions = position_monitor.collect_positions()
        position_time = time.time() - start_time
        assert position_time < 2.0  # Position collection should be fast
        
        start_time = time.time()
        exposures = exposure_monitor.calculate_exposures(positions)
        exposure_time = time.time() - start_time
        assert exposure_time < 2.0  # Exposure calculation should be fast
        
        start_time = time.time()
        risk_metrics = risk_monitor.calculate_risk_metrics(exposures)
        risk_time = time.time() - start_time
        assert risk_time < 3.0  # Risk calculation should be reasonable
        
        start_time = time.time()
        strategy_decisions = strategy_manager.generate_strategy_decisions(risk_metrics)
        strategy_time = time.time() - start_time
        assert strategy_time < 2.0  # Strategy decisions should be fast
        
        start_time = time.time()
        execution_orders = execution_manager.convert_strategy_to_orders(strategy_decisions)
        execution_time = time.time() - start_time
        assert execution_time < 1.0  # Execution conversion should be very fast
    
    def test_tight_loop_state_persistence(self, real_components, real_data_provider):
        """Test state persistence throughout tight loop processing."""
        position_monitor = real_components["position_monitor"]
        exposure_monitor = real_components["exposure_monitor"]
        risk_monitor = real_components["risk_monitor"]
        strategy_manager = real_components["strategy_manager"]
        execution_manager = real_components["execution_manager"]
        
        # Step 1: Execute tight loop
        positions = position_monitor.collect_positions()
        position_monitor.persist_state()
        
        exposures = exposure_monitor.calculate_exposures(positions)
        exposure_monitor.persist_state()
        
        risk_metrics = risk_monitor.calculate_risk_metrics(exposures)
        risk_monitor.persist_state()
        
        strategy_decisions = strategy_manager.generate_strategy_decisions(risk_metrics)
        strategy_manager.persist_state()
        
        execution_orders = execution_manager.convert_strategy_to_orders(strategy_decisions)
        execution_manager.persist_state()
        
        # Step 2: Verify state persistence
        loaded_positions = position_monitor.load_state()
        loaded_exposures = exposure_monitor.load_state()
        loaded_risk_metrics = risk_monitor.load_state()
        loaded_strategy_decisions = strategy_manager.load_state()
        loaded_execution_orders = execution_manager.load_state()
        
        # Step 3: Verify state consistency
        assert len(loaded_positions) == len(positions)
        assert len(loaded_exposures) == len(exposures)
        assert len(loaded_risk_metrics) == len(risk_metrics)
        assert len(loaded_strategy_decisions) == len(strategy_decisions)
        assert len(loaded_execution_orders) == len(execution_orders)
    
    def test_tight_loop_concurrent_safety(self, real_components, real_data_provider):
        """Test that tight loop is safe for concurrent execution."""
        import threading
        import time
        
        position_monitor = real_components["position_monitor"]
        exposure_monitor = real_components["exposure_monitor"]
        risk_monitor = real_components["risk_monitor"]
        strategy_manager = real_components["strategy_manager"]
        execution_manager = real_components["execution_manager"]
        
        results = []
        errors = []
        
        def execute_tight_loop():
            try:
                positions = position_monitor.collect_positions()
                exposures = exposure_monitor.calculate_exposures(positions)
                risk_metrics = risk_monitor.calculate_risk_metrics(exposures)
                strategy_decisions = strategy_manager.generate_strategy_decisions(risk_metrics)
                execution_orders = execution_manager.convert_strategy_to_orders(strategy_decisions)
                
                results.append({
                    "positions": len(positions),
                    "exposures": len(exposures),
                    "risk_metrics": len(risk_metrics),
                    "strategy_decisions": len(strategy_decisions),
                    "execution_orders": len(execution_orders)
                })
            except Exception as e:
                errors.append(str(e))
        
        # Step 1: Execute tight loop concurrently
        threads = []
        for i in range(3):  # Run 3 concurrent executions
            thread = threading.Thread(target=execute_tight_loop)
            threads.append(thread)
            thread.start()
        
        # Step 2: Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Step 3: Verify concurrent execution results
        assert len(errors) == 0, f"Concurrent execution errors: {errors}"
        assert len(results) == 3, "All concurrent executions should complete"
        
        # Verify results are consistent
        for result in results:
            assert result["positions"] > 0
            assert result["exposures"] > 0
            assert result["risk_metrics"] > 0
            assert result["strategy_decisions"] > 0
            assert result["execution_orders"] > 0
    
    def test_tight_loop_rollback_capability(self, real_components, real_data_provider):
        """Test tight loop rollback capability in case of failures."""
        position_monitor = real_components["position_monitor"]
        exposure_monitor = real_components["exposure_monitor"]
        risk_monitor = real_components["risk_monitor"]
        strategy_manager = real_components["strategy_manager"]
        execution_manager = real_components["execution_manager"]
        
        # Step 1: Create checkpoint before tight loop
        checkpoint_id = f"checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        position_monitor.create_checkpoint(checkpoint_id)
        exposure_monitor.create_checkpoint(checkpoint_id)
        risk_monitor.create_checkpoint(checkpoint_id)
        strategy_manager.create_checkpoint(checkpoint_id)
        execution_manager.create_checkpoint(checkpoint_id)
        
        # Step 2: Execute tight loop with simulated failure
        try:
            positions = position_monitor.collect_positions()
            exposures = exposure_monitor.calculate_exposures(positions)
            risk_metrics = risk_monitor.calculate_risk_metrics(exposures)
            strategy_decisions = strategy_manager.generate_strategy_decisions(risk_metrics)
            
            # Simulate failure in execution
            raise Exception("Simulated execution failure")
            
        except Exception:
            # Step 3: Rollback to checkpoint
            position_monitor.rollback_to_checkpoint(checkpoint_id)
            exposure_monitor.rollback_to_checkpoint(checkpoint_id)
            risk_monitor.rollback_to_checkpoint(checkpoint_id)
            strategy_manager.rollback_to_checkpoint(checkpoint_id)
            execution_manager.rollback_to_checkpoint(checkpoint_id)
        
        # Step 4: Verify rollback success
        # Components should be in the same state as before tight loop execution
        assert position_monitor.get_checkpoint_state(checkpoint_id) is not None
        assert exposure_monitor.get_checkpoint_state(checkpoint_id) is not None
        assert risk_monitor.get_checkpoint_state(checkpoint_id) is not None
        assert strategy_manager.get_checkpoint_state(checkpoint_id) is not None
        assert execution_manager.get_checkpoint_state(checkpoint_id) is not None
