"""
Mode-Agnostic Performance Monitor

Provides mode-agnostic performance monitoring that works for both backtest and live modes.
Monitors performance across all venues and provides generic performance logic.

Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Section 7 (Generic vs Mode-Specific)
Reference: docs/specs/20_PERFORMANCE_MONITOR.md - Mode-agnostic performance monitoring
"""

from typing import Dict, List, Any, Optional
import logging
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Mode-agnostic performance monitor that works for both backtest and live modes"""
    
    def __init__(self, config: Dict[str, Any], data_provider, utility_manager):
        """
        Initialize performance monitor.
        
        Args:
            config: Strategy configuration
            data_provider: Data provider instance
            utility_manager: Centralized utility manager
        """
        self.config = config
        self.data_provider = data_provider
        self.utility_manager = utility_manager
        
        # Performance tracking
        self.performance_history = []
        self.current_performance = {}
        
        logger.info("PerformanceMonitor initialized (mode-agnostic)")
    
    def monitor_performance(self, performance_data: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """
        Monitor performance regardless of mode (backtest or live).
        
        Args:
            performance_data: Performance data to monitor
            timestamp: Current timestamp
            
        Returns:
            Dictionary with performance monitoring results
        """
        try:
            # Validate performance data
            validation_result = self._validate_performance_data(performance_data)
            if not validation_result['valid']:
                return {
                    'status': 'failed',
                    'error': validation_result['error'],
                    'timestamp': timestamp
                }
            
            # Monitor various performance metrics
            pnl_performance = self._monitor_pnl_performance(performance_data, timestamp)
            risk_performance = self._monitor_risk_performance(performance_data, timestamp)
            execution_performance = self._monitor_execution_performance(performance_data, timestamp)
            strategy_performance = self._monitor_strategy_performance(performance_data, timestamp)
            
            # Calculate overall performance score
            overall_performance = self._calculate_overall_performance(
                pnl_performance, risk_performance, execution_performance, strategy_performance
            )
            
            # Calculate performance metrics
            performance_metrics = self._calculate_performance_metrics(
                pnl_performance, risk_performance, execution_performance, strategy_performance
            )
            
            # Update current performance
            self._update_current_performance(overall_performance, timestamp)
            
            return {
                'status': 'success',
                'timestamp': timestamp,
                'overall_performance': overall_performance,
                'performance_metrics': performance_metrics,
                'performance_categories': {
                    'pnl': pnl_performance,
                    'risk': risk_performance,
                    'execution': execution_performance,
                    'strategy': strategy_performance
                }
            }
            
        except Exception as e:
            logger.error(f"Error monitoring performance: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': timestamp
            }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        try:
            return {
                'current_performance': self.current_performance,
                'performance_history': self.performance_history,
                'mode_agnostic': True
            }
        except Exception as e:
            logger.error(f"Error getting performance summary: {e}")
            return {
                'current_performance': {},
                'performance_history': [],
                'mode_agnostic': True,
                'error': str(e)
            }
    
    def _validate_performance_data(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate performance data before monitoring."""
        try:
            # Check if performance_data is a dictionary
            if not isinstance(performance_data, dict):
                return {
                    'valid': False,
                    'error': "Performance data must be a dictionary"
                }
            
            # Check for required fields
            required_fields = ['timestamp', 'total_usdt_balance', 'total_share_class_balance']
            for field in required_fields:
                if field not in performance_data:
                    return {
                        'valid': False,
                        'error': f"Missing required field: {field}"
                    }
            
            return {'valid': True}
        except Exception as e:
            logger.error(f"Error validating performance data: {e}")
            return {
                'valid': False,
                'error': str(e)
            }
    
    def _monitor_pnl_performance(self, performance_data: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Monitor P&L performance."""
        try:
            pnl_performance = {
                'total_pnl': 0.0,
                'pnl_change': 0.0,
                'pnl_attribution': {},
                'pnl_score': 0.0
            }
            
            # Extract P&L data
            pnl_data = performance_data.get('pnl_data', {})
            
            if pnl_data:
                # Monitor total P&L
                pnl_performance['total_pnl'] = pnl_data.get('total_pnl', 0.0)
                
                # Monitor P&L change
                pnl_performance['pnl_change'] = pnl_data.get('pnl_change', 0.0)
                
                # Monitor P&L attribution
                pnl_attribution = pnl_data.get('pnl_attribution', {})
                for attribution, value in pnl_attribution.items():
                    pnl_performance['pnl_attribution'][attribution] = value
                
                # Calculate P&L score
                pnl_performance['pnl_score'] = self._calculate_pnl_score(pnl_data)
            
            return pnl_performance
        except Exception as e:
            logger.error(f"Error monitoring P&L performance: {e}")
            return {
                'total_pnl': 0.0,
                'pnl_change': 0.0,
                'pnl_attribution': {},
                'pnl_score': 0.0
            }
    
    def _monitor_risk_performance(self, performance_data: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Monitor risk performance."""
        try:
            risk_performance = {
                'overall_risk': 0.0,
                'risk_by_category': {},
                'risk_metrics': {},
                'risk_score': 0.0
            }
            
            # Extract risk data
            risk_data = performance_data.get('risk_data', {})
            
            if risk_data:
                # Monitor overall risk
                risk_performance['overall_risk'] = risk_data.get('overall_risk', 0.0)
                
                # Monitor risk by category
                risk_by_category = risk_data.get('risk_by_category', {})
                for category, risk in risk_by_category.items():
                    risk_performance['risk_by_category'][category] = risk
                
                # Monitor risk metrics
                risk_metrics = risk_data.get('risk_metrics', {})
                for metric, value in risk_metrics.items():
                    risk_performance['risk_metrics'][metric] = value
                
                # Calculate risk score
                risk_performance['risk_score'] = self._calculate_risk_score(risk_data)
            
            return risk_performance
        except Exception as e:
            logger.error(f"Error monitoring risk performance: {e}")
            return {
                'overall_risk': 0.0,
                'risk_by_category': {},
                'risk_metrics': {},
                'risk_score': 0.0
            }
    
    def _monitor_execution_performance(self, performance_data: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Monitor execution performance."""
        try:
            execution_performance = {
                'total_executions': 0,
                'successful_executions': 0,
                'failed_executions': 0,
                'execution_by_type': {},
                'execution_score': 0.0
            }
            
            # Extract execution data
            execution_data = performance_data.get('execution_data', {})
            
            if execution_data:
                # Monitor total executions
                execution_performance['total_executions'] = execution_data.get('total_executions', 0)
                
                # Monitor successful executions
                execution_performance['successful_executions'] = execution_data.get('successful_executions', 0)
                
                # Monitor failed executions
                execution_performance['failed_executions'] = execution_data.get('failed_executions', 0)
                
                # Monitor execution by type
                execution_by_type = execution_data.get('execution_by_type', {})
                for exec_type, count in execution_by_type.items():
                    execution_performance['execution_by_type'][exec_type] = count
                
                # Calculate execution score
                execution_performance['execution_score'] = self._calculate_execution_score(execution_data)
            
            return execution_performance
        except Exception as e:
            logger.error(f"Error monitoring execution performance: {e}")
            return {
                'total_executions': 0,
                'successful_executions': 0,
                'failed_executions': 0,
                'execution_by_type': {},
                'execution_score': 0.0
            }
    
    def _monitor_strategy_performance(self, performance_data: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Monitor strategy performance."""
        try:
            strategy_performance = {
                'active_strategies': 0,
                'strategy_by_type': {},
                'strategy_metrics': {},
                'strategy_score': 0.0
            }
            
            # Extract strategy data
            strategy_data = performance_data.get('strategy_data', {})
            
            if strategy_data:
                # Monitor active strategies
                strategy_performance['active_strategies'] = strategy_data.get('active_strategies', 0)
                
                # Monitor strategy by type
                strategy_by_type = strategy_data.get('strategy_by_type', {})
                for strategy_type, count in strategy_by_type.items():
                    strategy_performance['strategy_by_type'][strategy_type] = count
                
                # Monitor strategy metrics
                strategy_metrics = strategy_data.get('strategy_metrics', {})
                for metric, value in strategy_metrics.items():
                    strategy_performance['strategy_metrics'][metric] = value
                
                # Calculate strategy score
                strategy_performance['strategy_score'] = self._calculate_strategy_score(strategy_data)
            
            return strategy_performance
        except Exception as e:
            logger.error(f"Error monitoring strategy performance: {e}")
            return {
                'active_strategies': 0,
                'strategy_by_type': {},
                'strategy_metrics': {},
                'strategy_score': 0.0
            }
    
    def _calculate_overall_performance(self, pnl_performance: Dict[str, Any], risk_performance: Dict[str, Any], 
                                     execution_performance: Dict[str, Any], strategy_performance: Dict[str, Any]) -> float:
        """Calculate overall performance score."""
        try:
            # Weight different performance categories
            weights = {
                'pnl': 0.4,        # 40% weight for P&L performance
                'risk': 0.3,       # 30% weight for risk performance
                'execution': 0.2,  # 20% weight for execution performance
                'strategy': 0.1    # 10% weight for strategy performance
            }
            
            # Calculate weighted average
            overall_performance = (
                pnl_performance['pnl_score'] * weights['pnl'] +
                risk_performance['risk_score'] * weights['risk'] +
                execution_performance['execution_score'] * weights['execution'] +
                strategy_performance['strategy_score'] * weights['strategy']
            )
            
            return min(overall_performance, 1.0)  # Cap at 1.0
        except Exception as e:
            logger.error(f"Error calculating overall performance: {e}")
            return 0.0
    
    def _calculate_performance_metrics(self, pnl_performance: Dict[str, Any], risk_performance: Dict[str, Any], 
                                     execution_performance: Dict[str, Any], strategy_performance: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate performance metrics."""
        try:
            metrics = {
                'pnl_score': pnl_performance['pnl_score'],
                'risk_score': risk_performance['risk_score'],
                'execution_score': execution_performance['execution_score'],
                'strategy_score': strategy_performance['strategy_score'],
                'performance_level': self._get_performance_level(pnl_performance, risk_performance, execution_performance, strategy_performance),
                'performance_trend': self._get_performance_trend()
            }
            
            return metrics
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {e}")
            return {}
    
    def _get_performance_level(self, pnl_performance: Dict[str, Any], risk_performance: Dict[str, Any], 
                             execution_performance: Dict[str, Any], strategy_performance: Dict[str, Any]) -> str:
        """Get performance level based on performance categories."""
        try:
            # Calculate overall performance score
            overall_performance = self._calculate_overall_performance(
                pnl_performance, risk_performance, execution_performance, strategy_performance
            )
            
            # Determine performance level
            if overall_performance >= 0.9:
                return 'EXCELLENT'
            elif overall_performance >= 0.8:
                return 'GOOD'
            elif overall_performance >= 0.6:
                return 'FAIR'
            elif overall_performance >= 0.4:
                return 'POOR'
            else:
                return 'CRITICAL'
        except Exception as e:
            logger.error(f"Error getting performance level: {e}")
            return 'UNKNOWN'
    
    def _get_performance_trend(self) -> str:
        """Get performance trend."""
        try:
            # Placeholder for actual performance trend calculation
            # In real implementation, this would compare current performance with historical performance
            return 'STABLE'
        except Exception as e:
            logger.error(f"Error getting performance trend: {e}")
            return 'UNKNOWN'
    
    def _calculate_pnl_score(self, pnl_data: Dict[str, Any]) -> float:
        """Calculate P&L score."""
        try:
            # Calculate P&L score based on total P&L and change
            total_pnl = pnl_data.get('total_pnl', 0.0)
            pnl_change = pnl_data.get('pnl_change', 0.0)
            
            # Normalize P&L score (0-1 scale)
            if total_pnl > 0:
                pnl_score = min(pnl_change / total_pnl, 1.0)
            else:
                pnl_score = 0.0
            
            return pnl_score
        except Exception as e:
            logger.error(f"Error calculating P&L score: {e}")
            return 0.0
    
    def _calculate_risk_score(self, risk_data: Dict[str, Any]) -> float:
        """Calculate risk score."""
        try:
            # Calculate risk score based on overall risk
            overall_risk = risk_data.get('overall_risk', 0.0)
            
            # Normalize risk score (0-1 scale, lower risk is better)
            risk_score = 1.0 - overall_risk
            
            return risk_score
        except Exception as e:
            logger.error(f"Error calculating risk score: {e}")
            return 0.0
    
    def _calculate_execution_score(self, execution_data: Dict[str, Any]) -> float:
        """Calculate execution score."""
        try:
            # Calculate execution score based on success rate
            total_executions = execution_data.get('total_executions', 0)
            successful_executions = execution_data.get('successful_executions', 0)
            
            # Normalize execution score (0-1 scale)
            if total_executions > 0:
                execution_score = successful_executions / total_executions
            else:
                execution_score = 0.0
            
            return execution_score
        except Exception as e:
            logger.error(f"Error calculating execution score: {e}")
            return 0.0
    
    def _calculate_strategy_score(self, strategy_data: Dict[str, Any]) -> float:
        """Calculate strategy score."""
        try:
            # Calculate strategy score based on active strategies
            active_strategies = strategy_data.get('active_strategies', 0)
            
            # Normalize strategy score (0-1 scale)
            if active_strategies > 0:
                strategy_score = min(active_strategies / 10.0, 1.0)  # Cap at 10 strategies
            else:
                strategy_score = 0.0
            
            return strategy_score
        except Exception as e:
            logger.error(f"Error calculating strategy score: {e}")
            return 0.0
    
    def _update_current_performance(self, overall_performance: float, timestamp: pd.Timestamp):
        """Update current performance."""
        try:
            self.current_performance = {
                'overall_performance': overall_performance,
                'timestamp': timestamp
            }
            
            # Add to performance history
            self.performance_history.append({
                'overall_performance': overall_performance,
                'timestamp': timestamp
            })
        except Exception as e:
            logger.error(f"Error updating current performance: {e}")
