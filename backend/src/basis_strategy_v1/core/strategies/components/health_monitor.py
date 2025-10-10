"""
Mode-Agnostic Health Monitor

Provides mode-agnostic health monitoring that works for both backtest and live modes.
Monitors health across all venues and provides generic health logic.

Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Section 7 (Generic vs Mode-Specific)
Reference: docs/specs/13_HEALTH_MONITOR.md - Mode-agnostic health monitoring
"""

from typing import Dict, List, Any, Optional
import logging
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

class HealthMonitor:
    """Mode-agnostic health monitor that works for both backtest and live modes"""
    
    def __init__(self, config: Dict[str, Any], data_provider, utility_manager):
        """
        Initialize health monitor.
        
        Args:
            config: Strategy configuration
            data_provider: Data provider instance
            utility_manager: Centralized utility manager
        """
        self.config = config
        self.data_provider = data_provider
        self.utility_manager = utility_manager
        
        # Health tracking
        self.health_history = []
        self.current_health = {}
        
        logger.info("HealthMonitor initialized (mode-agnostic)")
    
    def check_health(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """
        Check health regardless of mode (backtest or live).
        
        Args:
            timestamp: Current timestamp
            
        Returns:
            Dictionary with health check results
        """
        try:
            # Check various health metrics
            data_health = self._check_data_health(timestamp)
            venue_health = self._check_venue_health(timestamp)
            component_health = self._check_component_health(timestamp)
            system_health = self._check_system_health(timestamp)
            
            # Calculate overall health score
            overall_health = self._calculate_overall_health(
                data_health, venue_health, component_health, system_health
            )
            
            # Calculate health metrics
            health_metrics = self._calculate_health_metrics(
                data_health, venue_health, component_health, system_health
            )
            
            # Update current health
            self._update_current_health(overall_health, timestamp)
            
            return {
                'timestamp': timestamp,
                'overall_health': overall_health,
                'health_metrics': health_metrics,
                'health_checks': {
                    'data': data_health,
                    'venue': venue_health,
                    'component': component_health,
                    'system': system_health
                }
            }
            
        except Exception as e:
            logger.error(f"Error checking health: {e}")
            return {
                'timestamp': timestamp,
                'overall_health': 0.0,
                'health_metrics': {},
                'health_checks': {},
                'error': str(e)
            }
    
    def _check_data_health(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Check data health."""
        try:
            data_health = {
                'status': 'healthy',
                'score': 1.0,
                'issues': []
            }
            
            # Check data provider health
            try:
                # Test data provider functionality
                test_data = self.data_provider.get_test_data(timestamp)
                if not test_data:
                    data_health['issues'].append('Data provider not responding')
                    data_health['score'] -= 0.3
            except Exception as e:
                data_health['issues'].append(f'Data provider error: {str(e)}')
                data_health['score'] -= 0.5
            
            # Check data freshness
            try:
                data_freshness = self._check_data_freshness(timestamp)
                if data_freshness < 0.8:
                    data_health['issues'].append('Data freshness below threshold')
                    data_health['score'] -= 0.2
            except Exception as e:
                data_health['issues'].append(f'Data freshness check error: {str(e)}')
                data_health['score'] -= 0.2
            
            # Check data completeness
            try:
                data_completeness = self._check_data_completeness(timestamp)
                if data_completeness < 0.9:
                    data_health['issues'].append('Data completeness below threshold')
                    data_health['score'] -= 0.2
            except Exception as e:
                data_health['issues'].append(f'Data completeness check error: {str(e)}')
                data_health['score'] -= 0.2
            
            # Update status based on score
            if data_health['score'] < 0.5:
                data_health['status'] = 'critical'
            elif data_health['score'] < 0.8:
                data_health['status'] = 'warning'
            
            return data_health
        except Exception as e:
            logger.error(f"Error checking data health: {e}")
            return {
                'status': 'error',
                'score': 0.0,
                'issues': [str(e)]
            }
    
    def _check_venue_health(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Check venue health."""
        try:
            venue_health = {
                'status': 'healthy',
                'score': 1.0,
                'issues': [],
                'venue_status': {}
            }
            
            # Get venue configurations
            venues = self.config.get('venues', {})
            
            for venue_name, venue_config in venues.items():
                try:
                    # Check venue connectivity
                    venue_status = self._check_venue_connectivity(venue_name, timestamp)
                    venue_health['venue_status'][venue_name] = venue_status
                    
                    if venue_status['status'] != 'healthy':
                        venue_health['issues'].append(f'{venue_name}: {venue_status["status"]}')
                        venue_health['score'] -= 0.1
                        
                except Exception as e:
                    venue_health['issues'].append(f'{venue_name}: Error checking connectivity - {str(e)}')
                    venue_health['score'] -= 0.1
                    venue_health['venue_status'][venue_name] = {
                        'status': 'error',
                        'error': str(e)
                    }
            
            # Update status based on score
            if venue_health['score'] < 0.5:
                venue_health['status'] = 'critical'
            elif venue_health['score'] < 0.8:
                venue_health['status'] = 'warning'
            
            return venue_health
        except Exception as e:
            logger.error(f"Error checking venue health: {e}")
            return {
                'status': 'error',
                'score': 0.0,
                'issues': [str(e)],
                'venue_status': {}
            }
    
    def _check_component_health(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Check component health."""
        try:
            component_health = {
                'status': 'healthy',
                'score': 1.0,
                'issues': [],
                'component_status': {}
            }
            
            # Define components to check
            components = [
                'data_provider', 'utility_manager', 'position_monitor',
                'exposure_monitor', 'risk_monitor', 'pnl_monitor',
                'data_subscriptions', 'execution_interface', 'results_store',
                'event_logger'
            ]
            
            for component_name in components:
                try:
                    # Check component health
                    component_status = self._check_component_status(component_name, timestamp)
                    component_health['component_status'][component_name] = component_status
                    
                    if component_status['status'] != 'healthy':
                        component_health['issues'].append(f'{component_name}: {component_status["status"]}')
                        component_health['score'] -= 0.1
                        
                except Exception as e:
                    component_health['issues'].append(f'{component_name}: Error checking status - {str(e)}')
                    component_health['score'] -= 0.1
                    component_health['component_status'][component_name] = {
                        'status': 'error',
                        'error': str(e)
                    }
            
            # Update status based on score
            if component_health['score'] < 0.5:
                component_health['status'] = 'critical'
            elif component_health['score'] < 0.8:
                component_health['status'] = 'warning'
            
            return component_health
        except Exception as e:
            logger.error(f"Error checking component health: {e}")
            return {
                'status': 'error',
                'score': 0.0,
                'issues': [str(e)],
                'component_status': {}
            }
    
    def _check_system_health(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Check system health."""
        try:
            system_health = {
                'status': 'healthy',
                'score': 1.0,
                'issues': []
            }
            
            # Check memory usage
            try:
                memory_usage = self._check_memory_usage()
                if memory_usage > 0.9:
                    system_health['issues'].append('High memory usage')
                    system_health['score'] -= 0.2
            except Exception as e:
                system_health['issues'].append(f'Memory check error: {str(e)}')
                system_health['score'] -= 0.1
            
            # Check disk space
            try:
                disk_usage = self._check_disk_usage()
                if disk_usage > 0.9:
                    system_health['issues'].append('High disk usage')
                    system_health['score'] -= 0.2
            except Exception as e:
                system_health['issues'].append(f'Disk check error: {str(e)}')
                system_health['score'] -= 0.1
            
            # Check network connectivity
            try:
                network_status = self._check_network_connectivity()
                if not network_status:
                    system_health['issues'].append('Network connectivity issues')
                    system_health['score'] -= 0.3
            except Exception as e:
                system_health['issues'].append(f'Network check error: {str(e)}')
                system_health['score'] -= 0.1
            
            # Update status based on score
            if system_health['score'] < 0.5:
                system_health['status'] = 'critical'
            elif system_health['score'] < 0.8:
                system_health['status'] = 'warning'
            
            return system_health
        except Exception as e:
            logger.error(f"Error checking system health: {e}")
            return {
                'status': 'error',
                'score': 0.0,
                'issues': [str(e)]
            }
    
    def _calculate_overall_health(self, data_health: Dict[str, Any], venue_health: Dict[str, Any], 
                                component_health: Dict[str, Any], system_health: Dict[str, Any]) -> float:
        """Calculate overall health score."""
        try:
            # Weight different health categories
            weights = {
                'data': 0.3,      # 30% weight for data health
                'venue': 0.25,    # 25% weight for venue health
                'component': 0.25, # 25% weight for component health
                'system': 0.2     # 20% weight for system health
            }
            
            # Calculate weighted average
            overall_health = (
                data_health['score'] * weights['data'] +
                venue_health['score'] * weights['venue'] +
                component_health['score'] * weights['component'] +
                system_health['score'] * weights['system']
            )
            
            return min(overall_health, 1.0)  # Cap at 1.0
        except Exception as e:
            logger.error(f"Error calculating overall health: {e}")
            return 0.0
    
    def _calculate_health_metrics(self, data_health: Dict[str, Any], venue_health: Dict[str, Any], 
                                component_health: Dict[str, Any], system_health: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate health metrics."""
        try:
            metrics = {
                'data_health_score': data_health['score'],
                'venue_health_score': venue_health['score'],
                'component_health_score': component_health['score'],
                'system_health_score': system_health['score'],
                'total_issues': len(data_health['issues']) + len(venue_health['issues']) + 
                              len(component_health['issues']) + len(system_health['issues']),
                'health_level': self._get_health_level(data_health, venue_health, component_health, system_health),
                'health_trend': self._get_health_trend()
            }
            
            return metrics
        except Exception as e:
            logger.error(f"Error calculating health metrics: {e}")
            return {}
    
    def _get_health_level(self, data_health: Dict[str, Any], venue_health: Dict[str, Any], 
                         component_health: Dict[str, Any], system_health: Dict[str, Any]) -> str:
        """Get health level based on health checks."""
        try:
            # Calculate overall health score
            overall_health = self._calculate_overall_health(
                data_health, venue_health, component_health, system_health
            )
            
            # Determine health level
            if overall_health >= 0.9:
                return 'EXCELLENT'
            elif overall_health >= 0.8:
                return 'GOOD'
            elif overall_health >= 0.6:
                return 'FAIR'
            elif overall_health >= 0.4:
                return 'POOR'
            else:
                return 'CRITICAL'
        except Exception as e:
            logger.error(f"Error getting health level: {e}")
            return 'UNKNOWN'
    
    def _get_health_trend(self) -> str:
        """Get health trend."""
        try:
            # Placeholder for actual health trend calculation
            # In real implementation, this would compare current health with historical health
            return 'STABLE'
        except Exception as e:
            logger.error(f"Error getting health trend: {e}")
            return 'UNKNOWN'
    
    def _check_data_freshness(self, timestamp: pd.Timestamp) -> float:
        """Check data freshness."""
        try:
            # Placeholder for actual data freshness calculation
            # In real implementation, this would check the age of the latest data
            return 0.95  # 95% fresh
        except Exception as e:
            logger.error(f"Error checking data freshness: {e}")
            return 0.0
    
    def _check_data_completeness(self, timestamp: pd.Timestamp) -> float:
        """Check data completeness."""
        try:
            # Placeholder for actual data completeness calculation
            # In real implementation, this would check if all required data is available
            return 0.98  # 98% complete
        except Exception as e:
            logger.error(f"Error checking data completeness: {e}")
            return 0.0
    
    def _check_venue_connectivity(self, venue_name: str, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Check venue connectivity."""
        try:
            # Placeholder for actual venue connectivity check
            # In real implementation, this would ping the venue's API
            return {
                'status': 'healthy',
                'response_time': 0.1,
                'last_check': timestamp
            }
        except Exception as e:
            logger.error(f"Error checking venue connectivity for {venue_name}: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'last_check': timestamp
            }
    
    def _check_component_status(self, component_name: str, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Check component status."""
        try:
            # Placeholder for actual component status check
            # In real implementation, this would check if the component is functioning properly
            return {
                'status': 'healthy',
                'last_check': timestamp
            }
        except Exception as e:
            logger.error(f"Error checking component status for {component_name}: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'last_check': timestamp
            }
    
    def _check_memory_usage(self) -> float:
        """Check memory usage."""
        try:
            # Placeholder for actual memory usage check
            # In real implementation, this would use psutil or similar
            return 0.7  # 70% memory usage
        except Exception as e:
            logger.error(f"Error checking memory usage: {e}")
            return 1.0
    
    def _check_disk_usage(self) -> float:
        """Check disk usage."""
        try:
            # Placeholder for actual disk usage check
            # In real implementation, this would use psutil or similar
            return 0.6  # 60% disk usage
        except Exception as e:
            logger.error(f"Error checking disk usage: {e}")
            return 1.0
    
    def _check_network_connectivity(self) -> bool:
        """Check network connectivity."""
        try:
            # Placeholder for actual network connectivity check
            # In real implementation, this would ping external services
            return True
        except Exception as e:
            logger.error(f"Error checking network connectivity: {e}")
            return False
    
    def _update_current_health(self, overall_health: float, timestamp: pd.Timestamp):
        """Update current health."""
        try:
            self.current_health = {
                'overall_health': overall_health,
                'timestamp': timestamp
            }
            
            # Add to health history
            self.health_history.append({
                'overall_health': overall_health,
                'timestamp': timestamp
            })
        except Exception as e:
            logger.error(f"Error updating current health: {e}")
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary."""
        try:
            return {
                'current_health': self.current_health,
                'health_history': self.health_history,
                'mode_agnostic': True
            }
        except Exception as e:
            logger.error(f"Error getting health summary: {e}")
            return {
                'current_health': {},
                'health_history': [],
                'mode_agnostic': True,
                'error': str(e)
            }
