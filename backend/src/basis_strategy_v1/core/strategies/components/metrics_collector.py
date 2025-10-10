"""
Mode-Agnostic Metrics Collector

Provides mode-agnostic metrics collection that works for both backtest and live modes.
Collects metrics across all venues and provides generic metrics logic.

Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Section 7 (Generic vs Mode-Specific)
Reference: docs/specs/21_METRICS_COLLECTOR.md - Mode-agnostic metrics collection
"""

from typing import Dict, List, Any, Optional
import logging
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

class MetricsCollector:
    """Mode-agnostic metrics collector that works for both backtest and live modes"""
    
    def __init__(self, config: Dict[str, Any], data_provider, utility_manager):
        """
        Initialize metrics collector.
        
        Args:
            config: Strategy configuration
            data_provider: Data provider instance
            utility_manager: Centralized utility manager
        """
        self.config = config
        self.data_provider = data_provider
        self.utility_manager = utility_manager
        
        # Metrics tracking
        self.collected_metrics = {}
        self.metrics_history = []
        
        logger.info("MetricsCollector initialized (mode-agnostic)")
    
    def collect_metrics(self, metrics_data: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """
        Collect metrics regardless of mode (backtest or live).
        
        Args:
            metrics_data: Metrics data to collect
            timestamp: Current timestamp
            
        Returns:
            Dictionary with metrics collection results
        """
        try:
            # Validate metrics data
            validation_result = self._validate_metrics_data(metrics_data)
            if not validation_result['valid']:
                return {
                    'status': 'failed',
                    'error': validation_result['error'],
                    'timestamp': timestamp
                }
            
            # Collect various metrics
            system_metrics = self._collect_system_metrics(metrics_data, timestamp)
            performance_metrics = self._collect_performance_metrics(metrics_data, timestamp)
            business_metrics = self._collect_business_metrics(metrics_data, timestamp)
            operational_metrics = self._collect_operational_metrics(metrics_data, timestamp)
            
            # Calculate overall metrics
            overall_metrics = self._calculate_overall_metrics(
                system_metrics, performance_metrics, business_metrics, operational_metrics
            )
            
            # Update collected metrics
            self._update_collected_metrics(overall_metrics, timestamp)
            
            return {
                'status': 'success',
                'timestamp': timestamp,
                'overall_metrics': overall_metrics,
                'metrics_categories': {
                    'system': system_metrics,
                    'performance': performance_metrics,
                    'business': business_metrics,
                    'operational': operational_metrics
                }
            }
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': timestamp
            }
    
    def get_collected_metrics(self) -> Dict[str, Any]:
        """Get collected metrics."""
        try:
            return {
                'collected_metrics': self.collected_metrics,
                'metrics_history': self.metrics_history,
                'mode_agnostic': True
            }
        except Exception as e:
            logger.error(f"Error getting collected metrics: {e}")
            return {
                'collected_metrics': {},
                'metrics_history': [],
                'mode_agnostic': True,
                'error': str(e)
            }
    
    def _validate_metrics_data(self, metrics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate metrics data before collection."""
        try:
            # Check if metrics_data is a dictionary
            if not isinstance(metrics_data, dict):
                return {
                    'valid': False,
                    'error': "Metrics data must be a dictionary"
                }
            
            # Check for required fields
            required_fields = ['timestamp', 'total_usdt_balance', 'total_share_class_balance']
            for field in required_fields:
                if field not in metrics_data:
                    return {
                        'valid': False,
                        'error': f"Missing required field: {field}"
                    }
            
            return {'valid': True}
        except Exception as e:
            logger.error(f"Error validating metrics data: {e}")
            return {
                'valid': False,
                'error': str(e)
            }
    
    def _collect_system_metrics(self, metrics_data: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Collect system metrics."""
        try:
            system_metrics = {
                'cpu_usage': 0.0,
                'memory_usage': 0.0,
                'disk_usage': 0.0,
                'network_usage': 0.0,
                'system_load': 0.0
            }
            
            # Extract system data
            system_data = metrics_data.get('system_data', {})
            
            if system_data:
                # Collect CPU usage
                system_metrics['cpu_usage'] = system_data.get('cpu_usage', 0.0)
                
                # Collect memory usage
                system_metrics['memory_usage'] = system_data.get('memory_usage', 0.0)
                
                # Collect disk usage
                system_metrics['disk_usage'] = system_data.get('disk_usage', 0.0)
                
                # Collect network usage
                system_metrics['network_usage'] = system_data.get('network_usage', 0.0)
                
                # Collect system load
                system_metrics['system_load'] = system_data.get('system_load', 0.0)
            
            return system_metrics
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return {
                'cpu_usage': 0.0,
                'memory_usage': 0.0,
                'disk_usage': 0.0,
                'network_usage': 0.0,
                'system_load': 0.0
            }
    
    def _collect_performance_metrics(self, metrics_data: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Collect performance metrics."""
        try:
            performance_metrics = {
                'response_time': 0.0,
                'throughput': 0.0,
                'error_rate': 0.0,
                'availability': 0.0,
                'latency': 0.0
            }
            
            # Extract performance data
            performance_data = metrics_data.get('performance_data', {})
            
            if performance_data:
                # Collect response time
                performance_metrics['response_time'] = performance_data.get('response_time', 0.0)
                
                # Collect throughput
                performance_metrics['throughput'] = performance_data.get('throughput', 0.0)
                
                # Collect error rate
                performance_metrics['error_rate'] = performance_data.get('error_rate', 0.0)
                
                # Collect availability
                performance_metrics['availability'] = performance_data.get('availability', 0.0)
                
                # Collect latency
                performance_metrics['latency'] = performance_data.get('latency', 0.0)
            
            return performance_metrics
        except Exception as e:
            logger.error(f"Error collecting performance metrics: {e}")
            return {
                'response_time': 0.0,
                'throughput': 0.0,
                'error_rate': 0.0,
                'availability': 0.0,
                'latency': 0.0
            }
    
    def _collect_business_metrics(self, metrics_data: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Collect business metrics."""
        try:
            business_metrics = {
                'total_balance': 0.0,
                'total_pnl': 0.0,
                'total_exposure': 0.0,
                'total_risk': 0.0,
                'total_executions': 0
            }
            
            # Extract business data
            business_data = metrics_data.get('business_data', {})
            
            if business_data:
                # Collect total balance
                business_metrics['total_balance'] = business_data.get('total_balance', 0.0)
                
                # Collect total P&L
                business_metrics['total_pnl'] = business_data.get('total_pnl', 0.0)
                
                # Collect total exposure
                business_metrics['total_exposure'] = business_data.get('total_exposure', 0.0)
                
                # Collect total risk
                business_metrics['total_risk'] = business_data.get('total_risk', 0.0)
                
                # Collect total executions
                business_metrics['total_executions'] = business_data.get('total_executions', 0)
            
            return business_metrics
        except Exception as e:
            logger.error(f"Error collecting business metrics: {e}")
            return {
                'total_balance': 0.0,
                'total_pnl': 0.0,
                'total_exposure': 0.0,
                'total_risk': 0.0,
                'total_executions': 0
            }
    
    def _collect_operational_metrics(self, metrics_data: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Collect operational metrics."""
        try:
            operational_metrics = {
                'active_connections': 0,
                'active_subscriptions': 0,
                'active_orders': 0,
                'active_strategies': 0,
                'system_health': 0.0
            }
            
            # Extract operational data
            operational_data = metrics_data.get('operational_data', {})
            
            if operational_data:
                # Collect active connections
                operational_metrics['active_connections'] = operational_data.get('active_connections', 0)
                
                # Collect active subscriptions
                operational_metrics['active_subscriptions'] = operational_data.get('active_subscriptions', 0)
                
                # Collect active orders
                operational_metrics['active_orders'] = operational_data.get('active_orders', 0)
                
                # Collect active strategies
                operational_metrics['active_strategies'] = operational_data.get('active_strategies', 0)
                
                # Collect system health
                operational_metrics['system_health'] = operational_data.get('system_health', 0.0)
            
            return operational_metrics
        except Exception as e:
            logger.error(f"Error collecting operational metrics: {e}")
            return {
                'active_connections': 0,
                'active_subscriptions': 0,
                'active_orders': 0,
                'active_strategies': 0,
                'system_health': 0.0
            }
    
    def _calculate_overall_metrics(self, system_metrics: Dict[str, Any], performance_metrics: Dict[str, Any], 
                                 business_metrics: Dict[str, Any], operational_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall metrics."""
        try:
            overall_metrics = {
                'timestamp': pd.Timestamp.now(),
                'system_score': self._calculate_system_score(system_metrics),
                'performance_score': self._calculate_performance_score(performance_metrics),
                'business_score': self._calculate_business_score(business_metrics),
                'operational_score': self._calculate_operational_score(operational_metrics),
                'overall_score': 0.0,
                'metrics_summary': {
                    'system': system_metrics,
                    'performance': performance_metrics,
                    'business': business_metrics,
                    'operational': operational_metrics
                }
            }
            
            # Calculate overall score
            overall_metrics['overall_score'] = (
                overall_metrics['system_score'] * 0.2 +
                overall_metrics['performance_score'] * 0.3 +
                overall_metrics['business_score'] * 0.3 +
                overall_metrics['operational_score'] * 0.2
            )
            
            return overall_metrics
        except Exception as e:
            logger.error(f"Error calculating overall metrics: {e}")
            return {
                'timestamp': pd.Timestamp.now(),
                'system_score': 0.0,
                'performance_score': 0.0,
                'business_score': 0.0,
                'operational_score': 0.0,
                'overall_score': 0.0,
                'metrics_summary': {}
            }
    
    def _calculate_system_score(self, system_metrics: Dict[str, Any]) -> float:
        """Calculate system score."""
        try:
            # Calculate system score based on system metrics
            cpu_usage = system_metrics.get('cpu_usage', 0.0)
            memory_usage = system_metrics.get('memory_usage', 0.0)
            disk_usage = system_metrics.get('disk_usage', 0.0)
            network_usage = system_metrics.get('network_usage', 0.0)
            system_load = system_metrics.get('system_load', 0.0)
            
            # Normalize system score (0-1 scale, lower usage is better)
            system_score = 1.0 - (
                cpu_usage * 0.3 +
                memory_usage * 0.3 +
                disk_usage * 0.2 +
                network_usage * 0.1 +
                system_load * 0.1
            )
            
            return max(system_score, 0.0)
        except Exception as e:
            logger.error(f"Error calculating system score: {e}")
            return 0.0
    
    def _calculate_performance_score(self, performance_metrics: Dict[str, Any]) -> float:
        """Calculate performance score."""
        try:
            # Calculate performance score based on performance metrics
            response_time = performance_metrics.get('response_time', 0.0)
            throughput = performance_metrics.get('throughput', 0.0)
            error_rate = performance_metrics.get('error_rate', 0.0)
            availability = performance_metrics.get('availability', 0.0)
            latency = performance_metrics.get('latency', 0.0)
            
            # Normalize performance score (0-1 scale)
            performance_score = (
                availability * 0.4 +
                (1.0 - error_rate) * 0.3 +
                min(throughput / 1000.0, 1.0) * 0.2 +
                max(0.0, 1.0 - response_time / 1000.0) * 0.1
            )
            
            return min(performance_score, 1.0)
        except Exception as e:
            logger.error(f"Error calculating performance score: {e}")
            return 0.0
    
    def _calculate_business_score(self, business_metrics: Dict[str, Any]) -> float:
        """Calculate business score."""
        try:
            # Calculate business score based on business metrics
            total_balance = business_metrics.get('total_balance', 0.0)
            total_pnl = business_metrics.get('total_pnl', 0.0)
            total_exposure = business_metrics.get('total_exposure', 0.0)
            total_risk = business_metrics.get('total_risk', 0.0)
            total_executions = business_metrics.get('total_executions', 0)
            
            # Normalize business score (0-1 scale)
            business_score = (
                min(total_balance / 10000.0, 1.0) * 0.3 +
                min(total_pnl / 1000.0, 1.0) * 0.3 +
                min(total_exposure / 10000.0, 1.0) * 0.2 +
                (1.0 - total_risk) * 0.1 +
                min(total_executions / 100.0, 1.0) * 0.1
            )
            
            return min(business_score, 1.0)
        except Exception as e:
            logger.error(f"Error calculating business score: {e}")
            return 0.0
    
    def _calculate_operational_score(self, operational_metrics: Dict[str, Any]) -> float:
        """Calculate operational score."""
        try:
            # Calculate operational score based on operational metrics
            active_connections = operational_metrics.get('active_connections', 0)
            active_subscriptions = operational_metrics.get('active_subscriptions', 0)
            active_orders = operational_metrics.get('active_orders', 0)
            active_strategies = operational_metrics.get('active_strategies', 0)
            system_health = operational_metrics.get('system_health', 0.0)
            
            # Normalize operational score (0-1 scale)
            operational_score = (
                system_health * 0.4 +
                min(active_connections / 10.0, 1.0) * 0.2 +
                min(active_subscriptions / 20.0, 1.0) * 0.2 +
                min(active_orders / 50.0, 1.0) * 0.1 +
                min(active_strategies / 5.0, 1.0) * 0.1
            )
            
            return min(operational_score, 1.0)
        except Exception as e:
            logger.error(f"Error calculating operational score: {e}")
            return 0.0
    
    def _update_collected_metrics(self, overall_metrics: Dict[str, Any], timestamp: pd.Timestamp):
        """Update collected metrics."""
        try:
            self.collected_metrics = overall_metrics
            
            # Add to metrics history
            self.metrics_history.append({
                'metrics': overall_metrics,
                'timestamp': timestamp
            })
        except Exception as e:
            logger.error(f"Error updating collected metrics: {e}")
