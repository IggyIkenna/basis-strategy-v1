"""
Mode-Agnostic Results Aggregator

Provides mode-agnostic results aggregation that works for both backtest and live modes.
Manages results aggregation across all venues and provides generic aggregation logic.

Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Section 7 (Generic vs Mode-Specific)
Reference: docs/specs/18_RESULTS_AGGREGATOR.md - Mode-agnostic results aggregation
"""

from typing import Dict, List, Any, Optional
import logging
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

class ResultsAggregator:
    """Mode-agnostic results aggregator that works for both backtest and live modes"""
    
    def __init__(self, config: Dict[str, Any], data_provider, utility_manager):
        """
        Initialize results aggregator.
        
        Args:
            config: Strategy configuration
            data_provider: Data provider instance
            utility_manager: Centralized utility manager
        """
        self.config = config
        self.data_provider = data_provider
        self.utility_manager = utility_manager
        
        # Results tracking
        self.aggregated_results = {}
        self.aggregation_history = []
        
        logger.info("ResultsAggregator initialized (mode-agnostic)")
    
    def aggregate_results(self, results_data: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """
        Aggregate results regardless of mode (backtest or live).
        
        Args:
            results_data: Results data to aggregate
            timestamp: Current timestamp
            
        Returns:
            Dictionary with aggregated results
        """
        try:
            # Validate results data
            validation_result = self._validate_results_data(results_data)
            if not validation_result['valid']:
                return {
                    'status': 'failed',
                    'error': validation_result['error'],
                    'timestamp': timestamp
                }
            
            # Aggregate results by category
            pnl_aggregation = self._aggregate_pnl_results(results_data, timestamp)
            exposure_aggregation = self._aggregate_exposure_results(results_data, timestamp)
            risk_aggregation = self._aggregate_risk_results(results_data, timestamp)
            position_aggregation = self._aggregate_position_results(results_data, timestamp)
            execution_aggregation = self._aggregate_execution_results(results_data, timestamp)
            
            # Calculate overall aggregation
            overall_aggregation = self._calculate_overall_aggregation(
                pnl_aggregation, exposure_aggregation, risk_aggregation, 
                position_aggregation, execution_aggregation
            )
            
            # Update aggregated results
            self._update_aggregated_results(overall_aggregation, timestamp)
            
            return {
                'status': 'success',
                'timestamp': timestamp,
                'overall_aggregation': overall_aggregation,
                'category_aggregations': {
                    'pnl': pnl_aggregation,
                    'exposure': exposure_aggregation,
                    'risk': risk_aggregation,
                    'position': position_aggregation,
                    'execution': execution_aggregation
                }
            }
            
        except Exception as e:
            logger.error(f"Error aggregating results: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': timestamp
            }
    
    def get_aggregated_results(self) -> Dict[str, Any]:
        """Get aggregated results."""
        try:
            return {
                'aggregated_results': self.aggregated_results,
                'aggregation_history': self.aggregation_history,
                'mode_agnostic': True
            }
        except Exception as e:
            logger.error(f"Error getting aggregated results: {e}")
            return {
                'aggregated_results': {},
                'aggregation_history': [],
                'mode_agnostic': True,
                'error': str(e)
            }
    
    def _validate_results_data(self, results_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate results data before aggregation."""
        try:
            # Check if results_data is a dictionary
            if not isinstance(results_data, dict):
                return {
                    'valid': False,
                    'error': "Results data must be a dictionary"
                }
            
            # Check for required fields
            required_fields = ['timestamp', 'total_usdt_balance', 'total_share_class_balance']
            for field in required_fields:
                if field not in results_data:
                    return {
                        'valid': False,
                        'error': f"Missing required field: {field}"
                    }
            
            return {'valid': True}
        except Exception as e:
            logger.error(f"Error validating results data: {e}")
            return {
                'valid': False,
                'error': str(e)
            }
    
    def _aggregate_pnl_results(self, results_data: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Aggregate P&L results."""
        try:
            pnl_aggregation = {
                'total_pnl': 0.0,
                'pnl_by_category': {},
                'pnl_attribution': {},
                'cumulative_pnl': 0.0
            }
            
            # Extract P&L data
            pnl_data = results_data.get('pnl_data', {})
            
            if pnl_data:
                # Aggregate total P&L
                pnl_aggregation['total_pnl'] = pnl_data.get('total_pnl', 0.0)
                
                # Aggregate P&L by category
                pnl_by_category = pnl_data.get('pnl_by_category', {})
                for category, pnl in pnl_by_category.items():
                    pnl_aggregation['pnl_by_category'][category] = pnl
                
                # Aggregate P&L attribution
                pnl_attribution = pnl_data.get('pnl_attribution', {})
                for attribution, value in pnl_attribution.items():
                    pnl_aggregation['pnl_attribution'][attribution] = value
                
                # Aggregate cumulative P&L
                pnl_aggregation['cumulative_pnl'] = pnl_data.get('cumulative_pnl', 0.0)
            
            return pnl_aggregation
        except Exception as e:
            logger.error(f"Error aggregating P&L results: {e}")
            return {
                'total_pnl': 0.0,
                'pnl_by_category': {},
                'pnl_attribution': {},
                'cumulative_pnl': 0.0
            }
    
    def _aggregate_exposure_results(self, results_data: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Aggregate exposure results."""
        try:
            exposure_aggregation = {
                'total_exposure': 0.0,
                'exposure_by_category': {},
                'exposure_metrics': {},
                'exposure_concentration': 0.0
            }
            
            # Extract exposure data
            exposure_data = results_data.get('exposure_data', {})
            
            if exposure_data:
                # Aggregate total exposure
                exposure_aggregation['total_exposure'] = exposure_data.get('total_exposure', 0.0)
                
                # Aggregate exposure by category
                exposure_by_category = exposure_data.get('exposure_by_category', {})
                for category, exposure in exposure_by_category.items():
                    exposure_aggregation['exposure_by_category'][category] = exposure
                
                # Aggregate exposure metrics
                exposure_metrics = exposure_data.get('exposure_metrics', {})
                for metric, value in exposure_metrics.items():
                    exposure_aggregation['exposure_metrics'][metric] = value
                
                # Aggregate exposure concentration
                exposure_aggregation['exposure_concentration'] = exposure_data.get('exposure_concentration', 0.0)
            
            return exposure_aggregation
        except Exception as e:
            logger.error(f"Error aggregating exposure results: {e}")
            return {
                'total_exposure': 0.0,
                'exposure_by_category': {},
                'exposure_metrics': {},
                'exposure_concentration': 0.0
            }
    
    def _aggregate_risk_results(self, results_data: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Aggregate risk results."""
        try:
            risk_aggregation = {
                'overall_risk': 0.0,
                'risk_by_category': {},
                'risk_metrics': {},
                'risk_level': 'UNKNOWN'
            }
            
            # Extract risk data
            risk_data = results_data.get('risk_data', {})
            
            if risk_data:
                # Aggregate overall risk
                risk_aggregation['overall_risk'] = risk_data.get('overall_risk', 0.0)
                
                # Aggregate risk by category
                risk_by_category = risk_data.get('risk_by_category', {})
                for category, risk in risk_by_category.items():
                    risk_aggregation['risk_by_category'][category] = risk
                
                # Aggregate risk metrics
                risk_metrics = risk_data.get('risk_metrics', {})
                for metric, value in risk_metrics.items():
                    risk_aggregation['risk_metrics'][metric] = value
                
                # Aggregate risk level
                risk_aggregation['risk_level'] = risk_data.get('risk_level', 'UNKNOWN')
            
            return risk_aggregation
        except Exception as e:
            logger.error(f"Error aggregating risk results: {e}")
            return {
                'overall_risk': 0.0,
                'risk_by_category': {},
                'risk_metrics': {},
                'risk_level': 'UNKNOWN'
            }
    
    def _aggregate_position_results(self, results_data: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Aggregate position results."""
        try:
            position_aggregation = {
                'total_position': 0.0,
                'position_by_category': {},
                'position_metrics': {},
                'position_concentration': 0.0
            }
            
            # Extract position data
            position_data = results_data.get('position_data', {})
            
            if position_data:
                # Aggregate total position
                position_aggregation['total_position'] = position_data.get('total_position', 0.0)
                
                # Aggregate position by category
                position_by_category = position_data.get('position_by_category', {})
                for category, position in position_by_category.items():
                    position_aggregation['position_by_category'][category] = position
                
                # Aggregate position metrics
                position_metrics = position_data.get('position_metrics', {})
                for metric, value in position_metrics.items():
                    position_aggregation['position_metrics'][metric] = value
                
                # Aggregate position concentration
                position_aggregation['position_concentration'] = position_data.get('position_concentration', 0.0)
            
            return position_aggregation
        except Exception as e:
            logger.error(f"Error aggregating position results: {e}")
            return {
                'total_position': 0.0,
                'position_by_category': {},
                'position_metrics': {},
                'position_concentration': 0.0
            }
    
    def _aggregate_execution_results(self, results_data: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Aggregate execution results."""
        try:
            execution_aggregation = {
                'total_executions': 0,
                'successful_executions': 0,
                'failed_executions': 0,
                'execution_by_type': {},
                'execution_metrics': {}
            }
            
            # Extract execution data
            execution_data = results_data.get('execution_data', {})
            
            if execution_data:
                # Aggregate total executions
                execution_aggregation['total_executions'] = execution_data.get('total_executions', 0)
                
                # Aggregate successful executions
                execution_aggregation['successful_executions'] = execution_data.get('successful_executions', 0)
                
                # Aggregate failed executions
                execution_aggregation['failed_executions'] = execution_data.get('failed_executions', 0)
                
                # Aggregate execution by type
                execution_by_type = execution_data.get('execution_by_type', {})
                for exec_type, count in execution_by_type.items():
                    execution_aggregation['execution_by_type'][exec_type] = count
                
                # Aggregate execution metrics
                execution_metrics = execution_data.get('execution_metrics', {})
                for metric, value in execution_metrics.items():
                    execution_aggregation['execution_metrics'][metric] = value
            
            return execution_aggregation
        except Exception as e:
            logger.error(f"Error aggregating execution results: {e}")
            return {
                'total_executions': 0,
                'successful_executions': 0,
                'failed_executions': 0,
                'execution_by_type': {},
                'execution_metrics': {}
            }
    
    def _calculate_overall_aggregation(self, pnl_aggregation: Dict[str, Any], exposure_aggregation: Dict[str, Any], 
                                     risk_aggregation: Dict[str, Any], position_aggregation: Dict[str, Any], 
                                     execution_aggregation: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall aggregation."""
        try:
            overall_aggregation = {
                'timestamp': pd.Timestamp.now(),
                'total_usdt_balance': 0.0,
                'total_share_class_balance': 0.0,
                'overall_pnl': pnl_aggregation['total_pnl'],
                'overall_exposure': exposure_aggregation['total_exposure'],
                'overall_risk': risk_aggregation['overall_risk'],
                'overall_position': position_aggregation['total_position'],
                'overall_executions': execution_aggregation['total_executions'],
                'aggregation_metrics': {
                    'pnl_score': self._calculate_pnl_score(pnl_aggregation),
                    'exposure_score': self._calculate_exposure_score(exposure_aggregation),
                    'risk_score': self._calculate_risk_score(risk_aggregation),
                    'position_score': self._calculate_position_score(position_aggregation),
                    'execution_score': self._calculate_execution_score(execution_aggregation)
                }
            }
            
            return overall_aggregation
        except Exception as e:
            logger.error(f"Error calculating overall aggregation: {e}")
            return {
                'timestamp': pd.Timestamp.now(),
                'total_usdt_balance': 0.0,
                'total_share_class_balance': 0.0,
                'overall_pnl': 0.0,
                'overall_exposure': 0.0,
                'overall_risk': 0.0,
                'overall_position': 0.0,
                'overall_executions': 0,
                'aggregation_metrics': {}
            }
    
    def _calculate_pnl_score(self, pnl_aggregation: Dict[str, Any]) -> float:
        """Calculate P&L score."""
        try:
            # Calculate P&L score based on total P&L and attribution
            total_pnl = pnl_aggregation.get('total_pnl', 0.0)
            cumulative_pnl = pnl_aggregation.get('cumulative_pnl', 0.0)
            
            # Normalize P&L score (0-1 scale)
            if cumulative_pnl > 0:
                pnl_score = min(total_pnl / cumulative_pnl, 1.0)
            else:
                pnl_score = 0.0
            
            return pnl_score
        except Exception as e:
            logger.error(f"Error calculating P&L score: {e}")
            return 0.0
    
    def _calculate_exposure_score(self, exposure_aggregation: Dict[str, Any]) -> float:
        """Calculate exposure score."""
        try:
            # Calculate exposure score based on total exposure and concentration
            total_exposure = exposure_aggregation.get('total_exposure', 0.0)
            exposure_concentration = exposure_aggregation.get('exposure_concentration', 0.0)
            
            # Normalize exposure score (0-1 scale)
            if total_exposure > 0:
                exposure_score = 1.0 - exposure_concentration  # Lower concentration is better
            else:
                exposure_score = 0.0
            
            return exposure_score
        except Exception as e:
            logger.error(f"Error calculating exposure score: {e}")
            return 0.0
    
    def _calculate_risk_score(self, risk_aggregation: Dict[str, Any]) -> float:
        """Calculate risk score."""
        try:
            # Calculate risk score based on overall risk
            overall_risk = risk_aggregation.get('overall_risk', 0.0)
            
            # Normalize risk score (0-1 scale, lower risk is better)
            risk_score = 1.0 - overall_risk
            
            return risk_score
        except Exception as e:
            logger.error(f"Error calculating risk score: {e}")
            return 0.0
    
    def _calculate_position_score(self, position_aggregation: Dict[str, Any]) -> float:
        """Calculate position score."""
        try:
            # Calculate position score based on total position and concentration
            total_position = position_aggregation.get('total_position', 0.0)
            position_concentration = position_aggregation.get('position_concentration', 0.0)
            
            # Normalize position score (0-1 scale)
            if total_position > 0:
                position_score = 1.0 - position_concentration  # Lower concentration is better
            else:
                position_score = 0.0
            
            return position_score
        except Exception as e:
            logger.error(f"Error calculating position score: {e}")
            return 0.0
    
    def _calculate_execution_score(self, execution_aggregation: Dict[str, Any]) -> float:
        """Calculate execution score."""
        try:
            # Calculate execution score based on success rate
            total_executions = execution_aggregation.get('total_executions', 0)
            successful_executions = execution_aggregation.get('successful_executions', 0)
            
            # Normalize execution score (0-1 scale)
            if total_executions > 0:
                execution_score = successful_executions / total_executions
            else:
                execution_score = 0.0
            
            return execution_score
        except Exception as e:
            logger.error(f"Error calculating execution score: {e}")
            return 0.0
    
    def _update_aggregated_results(self, overall_aggregation: Dict[str, Any], timestamp: pd.Timestamp):
        """Update aggregated results."""
        try:
            self.aggregated_results = overall_aggregation
            
            # Add to aggregation history
            self.aggregation_history.append({
                'aggregation': overall_aggregation,
                'timestamp': timestamp
            })
        except Exception as e:
            logger.error(f"Error updating aggregated results: {e}")
