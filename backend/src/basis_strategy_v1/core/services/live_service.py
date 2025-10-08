"""Live Trading Service using the refactored components.

This service coordinates the new Agent A and Agent B components to run live trading strategies.
"""

from decimal import Decimal
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
import asyncio
import uuid
from dataclasses import dataclass, field
from pathlib import Path
import pytz

from ..event_engine.event_driven_strategy_engine import EventDrivenStrategyEngine
from ..config import load_and_validate_config
from ...infrastructure.data.historical_data_provider import DataProvider

logger = logging.getLogger(__name__)

# Error codes for Live Service
ERROR_CODES = {
    'LT-001': 'Live trading request validation failed',
    'LT-002': 'Config creation failed',
    'LT-003': 'Strategy engine initialization failed',
    'LT-004': 'Live trading execution failed',
    'LT-005': 'Live trading monitoring failed',
    'LT-006': 'Live trading stop failed',
    'LT-007': 'Risk check failed'
}


@dataclass
class LiveTradingRequest:
    """Request object for live trading execution."""
    strategy_name: str
    initial_capital: Decimal
    share_class: str
    config_overrides: Dict[str, Any] = field(default_factory=dict)
    risk_limits: Dict[str, Any] = field(default_factory=dict)
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def validate(self) -> List[str]:
        """Validate request parameters."""
        errors = []
        
        if not self.strategy_name:
            errors.append("strategy_name is required")
        
        if self.initial_capital <= 0:
            errors.append("initial_capital must be positive")
        
        if self.share_class not in ['USDT', 'ETH']:
            errors.append("share_class must be 'USDT' or 'ETH'")
        
        # Validate risk limits
        if self.risk_limits:
            max_drawdown = self.risk_limits.get('max_drawdown')
            if max_drawdown is not None and (max_drawdown <= 0 or max_drawdown > 1):
                errors.append("max_drawdown must be between 0 and 1")
            
            max_position_size = self.risk_limits.get('max_position_size')
            if max_position_size is not None and max_position_size <= 0:
                errors.append("max_position_size must be positive")
        
        return errors


class LiveTradingService:
    """Service for running live trading strategies using the new component architecture."""
    
    def __init__(self):
        self.running_strategies: Dict[str, Dict[str, Any]] = {}
        self.completed_strategies: Dict[str, Dict[str, Any]] = {}
        self.monitoring_tasks: Dict[str, asyncio.Task] = {}
    
    def create_request(self, strategy_name: str, initial_capital: Decimal, share_class: str,
                      config_overrides: Dict[str, Any] = None, 
                      risk_limits: Dict[str, Any] = None) -> LiveTradingRequest:
        """Create a live trading request."""
        return LiveTradingRequest(
            strategy_name=strategy_name,
            initial_capital=initial_capital,
            share_class=share_class,
            config_overrides=config_overrides or {},
            risk_limits=risk_limits or {}
        )
    
    async def start_live_trading(self, request: LiveTradingRequest) -> str:
        """Start live trading asynchronously."""
        # Validate request
        errors = request.validate()
        if errors:
            logger.error(f"[LT-001] Live trading request validation failed: {', '.join(errors)}")
            raise ValueError(f"Invalid request: {', '.join(errors)}")
        
        try:
            # Create config for live trading using config infrastructure
            config = self._create_config(request)
            
            # Initialize strategy engine (creates its own components internally)
            strategy_engine = EventDrivenStrategyEngine(config)
            
            # Store request info
            self.running_strategies[request.request_id] = {
                'request': request,
                'config': config,
                'strategy_engine': strategy_engine,
                'status': 'starting',
                'started_at': datetime.utcnow(),
                'last_heartbeat': datetime.utcnow(),
                'total_trades': 0,
                'total_pnl': 0.0,
                'current_drawdown': 0.0,
                'risk_breaches': []
            }
            
            # Start live trading in background
            monitoring_task = asyncio.create_task(self._execute_live_trading(request.request_id))
            self.monitoring_tasks[request.request_id] = monitoring_task
            
            return request.request_id
            
        except Exception as e:
            logger.error(f"[LT-003] Strategy engine initialization failed: {e}")
            raise
    
    def _create_config(self, request: LiveTradingRequest) -> Dict[str, Any]:
        """Create configuration using existing config infrastructure."""
        try:
            from ...infrastructure.config.config_loader import get_config_loader
            
            # Get config loader
            config_loader = get_config_loader()
            
            # Load base config for the mode
            mode = self._map_strategy_to_mode(request.strategy_name)
            base_config = config_loader.get_complete_config(mode=mode)
            
            # Apply user overrides
            if request.config_overrides:
                base_config = self._deep_merge(base_config, request.config_overrides)
            
            # Add request-specific overrides for live trading
            base_config.update({
                'share_class': request.share_class,
                'initial_capital': float(request.initial_capital),
                'execution_mode': 'live',
                'live_trading': {
                    'initial_capital': float(request.initial_capital),
                    'risk_limits': request.risk_limits,
                    'started_at': datetime.utcnow().isoformat()
                }
            })
            
            return base_config
            
        except Exception as e:
            logger.error(f"[LT-002] Config creation failed: {e}")
            raise
    
    def _map_strategy_to_mode(self, strategy_name: str) -> str:
        """Map strategy name to mode."""
        strategy_mode_map = {
            'pure_lending': 'pure_lending',
            'btc_basis': 'btc_basis',
            'eth_leveraged': 'eth_leveraged',
            'usdt_market_neutral': 'usdt_market_neutral',
            'usdt_market_neutral_no_leverage': 'usdt_market_neutral_no_leverage',
            'eth_staking_only': 'eth_staking_only'
        }
        return strategy_mode_map.get(strategy_name, 'pure_lending')
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    async def _execute_live_trading(self, request_id: str):
        """Execute the live trading strategy."""
        try:
            strategy_info = self.running_strategies[request_id]
            strategy_engine = strategy_info['strategy_engine']
            request = strategy_info['request']
            
            # Update status to running
            strategy_info['status'] = 'running'
            strategy_info['last_heartbeat'] = datetime.utcnow()
            
            logger.info(f"Starting live trading for strategy {request_id}")
            
            # Start the strategy engine in live mode
            await strategy_engine.run_live()
            
        except Exception as e:
            logger.error(f"[LT-004] Live trading {request_id} failed: {e}", exc_info=True)
            strategy_info = self.running_strategies[request_id]
            strategy_info['status'] = 'failed'
            strategy_info['error'] = str(e)
            strategy_info['completed_at'] = datetime.utcnow()
    
    async def stop_live_trading(self, request_id: str) -> bool:
        """Stop a running live trading strategy."""
        if request_id not in self.running_strategies:
            return False
        
        try:
            strategy_info = self.running_strategies[request_id]
            strategy_engine = strategy_info['strategy_engine']
            
            # Stop the strategy engine
            strategy_engine.stop()
            
            # Cancel monitoring task
            if request_id in self.monitoring_tasks:
                self.monitoring_tasks[request_id].cancel()
                del self.monitoring_tasks[request_id]
            
            # Update status
            strategy_info['status'] = 'stopped'
            strategy_info['completed_at'] = datetime.utcnow()
            
            # Move to completed strategies
            self.completed_strategies[request_id] = strategy_info.copy()
            del self.running_strategies[request_id]
            
            logger.info(f"Live trading {request_id} stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"[LT-006] Failed to stop live trading {request_id}: {e}")
            return False
    
    async def get_status(self, request_id: str) -> Dict[str, Any]:
        """Get the status of a live trading strategy."""
        if request_id in self.running_strategies:
            strategy_info = self.running_strategies[request_id]
            return {
                'status': strategy_info['status'],
                'started_at': strategy_info['started_at'],
                'last_heartbeat': strategy_info['last_heartbeat'],
                'total_trades': strategy_info['total_trades'],
                'total_pnl': strategy_info['total_pnl'],
                'current_drawdown': strategy_info['current_drawdown'],
                'risk_breaches': strategy_info['risk_breaches'],
                'error': strategy_info.get('error')
            }
        elif request_id in self.completed_strategies:
            strategy_info = self.completed_strategies[request_id]
            return {
                'status': strategy_info['status'],
                'started_at': strategy_info['started_at'],
                'completed_at': strategy_info.get('completed_at'),
                'total_trades': strategy_info['total_trades'],
                'total_pnl': strategy_info['total_pnl'],
                'final_drawdown': strategy_info['current_drawdown'],
                'risk_breaches': strategy_info['risk_breaches'],
                'error': strategy_info.get('error')
            }
        else:
            return {'status': 'not_found'}
    
    async def get_performance_metrics(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get performance metrics for a live trading strategy."""
        if request_id not in self.running_strategies:
            return None
        
        try:
            strategy_info = self.running_strategies[request_id]
            strategy_engine = strategy_info['strategy_engine']
            
            # Get current status from strategy engine
            engine_status = await strategy_engine.get_status()
            
            # Calculate performance metrics
            initial_capital = strategy_info['request'].initial_capital
            current_pnl = strategy_info['total_pnl']
            current_value = float(initial_capital) + current_pnl
            return_pct = (current_pnl / float(initial_capital)) * 100
            
            return {
                'initial_capital': float(initial_capital),
                'current_value': current_value,
                'total_pnl': current_pnl,
                'return_pct': return_pct,
                'total_trades': strategy_info['total_trades'],
                'current_drawdown': strategy_info['current_drawdown'],
                'uptime_hours': (datetime.utcnow() - strategy_info['started_at']).total_seconds() / 3600,
                'engine_status': engine_status,
                'last_heartbeat': strategy_info['last_heartbeat']
            }
            
        except Exception as e:
            logger.error(f"[LT-005] Failed to get performance metrics for {request_id}: {e}")
            return None
    
    async def check_risk_limits(self, request_id: str) -> Dict[str, Any]:
        """Check if risk limits are being breached."""
        if request_id not in self.running_strategies:
            return {'status': 'not_found'}
        
        try:
            strategy_info = self.running_strategies[request_id]
            request = strategy_info['request']
            risk_limits = request.risk_limits
            
            if not risk_limits:
                return {'status': 'no_limits', 'message': 'No risk limits configured'}
            
            breaches = []
            
            # Check max drawdown
            max_drawdown = risk_limits.get('max_drawdown')
            if max_drawdown is not None:
                current_drawdown = abs(strategy_info['current_drawdown'])
                if current_drawdown > max_drawdown:
                    breaches.append({
                        'type': 'max_drawdown',
                        'limit': max_drawdown,
                        'current': current_drawdown,
                        'breach_pct': ((current_drawdown - max_drawdown) / max_drawdown) * 100
                    })
            
            # Check max position size (would need to get from position monitor)
            max_position_size = risk_limits.get('max_position_size')
            if max_position_size is not None:
                # This would require integration with position monitor
                # For now, we'll skip this check
                pass
            
            # Check max daily loss
            max_daily_loss = risk_limits.get('max_daily_loss')
            if max_daily_loss is not None:
                # Calculate daily P&L (would need historical data)
                # For now, we'll skip this check
                pass
            
            if breaches:
                strategy_info['risk_breaches'].extend(breaches)
                return {
                    'status': 'breach_detected',
                    'breaches': breaches,
                    'action_required': True
                }
            else:
                return {
                    'status': 'within_limits',
                    'breaches': [],
                    'action_required': False
                }
                
        except Exception as e:
            logger.error(f"[LT-007] Risk check failed for {request_id}: {e}")
            return {'status': 'error', 'error': str(e)}
    
    async def emergency_stop(self, request_id: str, reason: str = "Emergency stop") -> bool:
        """Emergency stop a live trading strategy."""
        logger.warning(f"Emergency stop requested for {request_id}: {reason}")
        
        # Stop the strategy
        success = await self.stop_live_trading(request_id)
        
        if success and request_id in self.completed_strategies:
            # Add emergency stop info
            self.completed_strategies[request_id]['emergency_stop'] = {
                'reason': reason,
                'stopped_at': datetime.utcnow()
            }
        
        return success
    
    async def get_all_running_strategies(self) -> List[Dict[str, Any]]:
        """Get all currently running strategies."""
        return [
            {
                'request_id': request_id,
                'strategy_name': info['request'].strategy_name,
                'share_class': info['request'].share_class,
                'status': info['status'],
                'started_at': info['started_at'],
                'last_heartbeat': info['last_heartbeat']
            }
            for request_id, info in self.running_strategies.items()
        ]
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all running strategies."""
        health_status = {
            'total_strategies': len(self.running_strategies),
            'healthy_strategies': 0,
            'unhealthy_strategies': 0,
            'strategies': []
        }
        
        current_time = datetime.utcnow()
        
        for request_id, strategy_info in self.running_strategies.items():
            last_heartbeat = strategy_info['last_heartbeat']
            time_since_heartbeat = (current_time - last_heartbeat).total_seconds()
            
            # Consider unhealthy if no heartbeat for more than 5 minutes
            is_healthy = time_since_heartbeat < 300
            
            if is_healthy:
                health_status['healthy_strategies'] += 1
            else:
                health_status['unhealthy_strategies'] += 1
            
            health_status['strategies'].append({
                'request_id': request_id,
                'strategy_name': strategy_info['request'].strategy_name,
                'is_healthy': is_healthy,
                'last_heartbeat': last_heartbeat,
                'time_since_heartbeat_seconds': time_since_heartbeat
            })
        
        return health_status


# Global instance for the service
live_trading_service = LiveTradingService()
