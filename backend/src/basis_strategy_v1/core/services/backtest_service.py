"""New Backtest Service using the refactored components.

This service coordinates the core components to run backtests.
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
import pandas as pd

from ..event_engine.event_driven_strategy_engine import EventDrivenStrategyEngine
from ...infrastructure.data.historical_data_provider import DataProvider
from ..strategies.strategy_factory import StrategyFactory

logger = logging.getLogger(__name__)

# Error codes for Backtest Service
ERROR_CODES = {
    'BT-001': 'Backtest request validation failed',
    'BT-002': 'Config creation failed',
    'BT-003': 'Strategy engine initialization failed',
    'BT-004': 'Backtest execution failed',
    'BT-005': 'Result processing failed'
}


@dataclass
class BacktestRequest:
    """Request object for backtest execution."""
    strategy_name: str
    start_date: datetime
    end_date: datetime
    initial_capital: Decimal
    share_class: str
    config_overrides: Dict[str, Any] = field(default_factory=dict)
    debug_mode: bool = False
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def validate(self) -> List[str]:
        """Validate request parameters."""
        errors = []
        
        if not self.strategy_name:
            errors.append("strategy_name is required")
        
        if self.initial_capital <= 0:
            errors.append("initial_capital must be positive")
        
        if self.end_date <= self.start_date:
            errors.append("end_date must be after start_date")
        
        if self.share_class not in ['USDT', 'ETH']:
            errors.append("share_class must be 'USDT' or 'ETH'")
        
        return errors


class BacktestService:
    """Service for running backtests using the new component architecture."""
    
    def __init__(self):
        self.running_backtests: Dict[str, Dict[str, Any]] = {}
        self.completed_backtests: Dict[str, Dict[str, Any]] = {}
    
    def create_request(self, strategy_name: str, start_date: datetime, end_date: datetime,
                      initial_capital: Decimal, share_class: str, 
                      config_overrides: Dict[str, Any] = None,
                      debug_mode: bool = False) -> BacktestRequest:
        """Create a backtest request."""
        return BacktestRequest(
            strategy_name=strategy_name,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            share_class=share_class,
            config_overrides=config_overrides or {},
            debug_mode=debug_mode
        )
    
    async def run_backtest(self, request: BacktestRequest) -> str:
        """
        Run a backtest using Phase 3 architecture with proper dependency injection.
        
        Phase 4: Uses injected config manager, data provider, and component initialization.
        """
        # Validate request
        errors = request.validate()
        if errors:
            logger.error(f"[BT-001] Backtest request validation failed: {', '.join(errors)}")
            raise ValueError(f"Invalid request: {', '.join(errors)}")
        
        try:
            # Phase 4: Use new architecture with proper dependency injection
            from ...infrastructure.config.config_manager import get_config_manager
            from ...infrastructure.data.data_provider_factory import create_data_provider
            
            # Get validated config for the specific strategy mode
            config_manager = get_config_manager()
            config = config_manager.get_complete_config(mode=request.strategy_name)
            
            # Apply config overrides from request
            if request.config_overrides:
                config.update(request.config_overrides)
            
            # Get data provider (on-demand loading with date validation)
            import os
            data_provider = create_data_provider(
                data_dir=config_manager.get_data_directory(),
                execution_mode=os.getenv('BASIS_EXECUTION_MODE'),
                data_mode=os.getenv('BASIS_DATA_MODE'),
                config=config,
                mode=request.strategy_name,
                backtest_start_date=request.start_date.strftime('%Y-%m-%d'),
                backtest_end_date=request.end_date.strftime('%Y-%m-%d')
            )
            
            # Phase 3: Initialize strategy engine with proper dependency injection
            strategy_engine = EventDrivenStrategyEngine(
                config=config,
                execution_mode=os.getenv('BASIS_EXECUTION_MODE'),
                data_provider=data_provider,
                initial_capital=float(request.initial_capital),  # From API request
                share_class=request.share_class,  # From API request
                debug_mode=request.debug_mode
            )
            
            # Store request info
            self.running_backtests[request.request_id] = {
                'request': request,
                'config': config,
                'strategy_engine': strategy_engine,
                'status': 'running',
                'started_at': datetime.utcnow(),
                'progress': 0
            }
            
            logger.info(f"✅ Backtest initialized: {request.strategy_name} mode, {request.share_class} share class, {request.initial_capital} capital")
            
            # Debug: Print initial position monitor state
            if request.debug_mode:
                strategy_engine.debug_print_position_monitor()
            
            # Execute backtest synchronously (Phase 4: no background tasks)
            results = await self._execute_backtest_sync(request.request_id)
            
            return request.request_id
            
        except Exception as e:
            logger.error(f"[BT-003] Strategy engine initialization failed: {e}")
            raise
    
    async def _execute_backtest_sync(self, request_id: str) -> Dict[str, Any]:
        """
        Execute backtest synchronously using Phase 3 component architecture.
        
        Phase 4: Synchronous execution with real component orchestration.
        """
        if request_id not in self.running_backtests:
            raise ValueError(f"Backtest request not found: {request_id}")
        
        backtest_info = self.running_backtests[request_id]
        request = backtest_info['request']
        strategy_engine = backtest_info['strategy_engine']
        
        try:
            logger.info(f"🔄 Executing backtest: {request.strategy_name} from {request.start_date} to {request.end_date}")
            
            # Run backtest using the strategy engine with all components
            results = await strategy_engine.run_backtest(
                start_date=request.start_date.strftime('%Y-%m-%d'),
                end_date=request.end_date.strftime('%Y-%m-%d')
            )
            
            # Debug: Print final position monitor state
            if request.debug_mode:
                strategy_engine.debug_print_position_monitor()
            
            # Update status
            backtest_info['status'] = 'completed'
            backtest_info['progress'] = 1.0
            backtest_info['completed_at'] = datetime.utcnow()
            backtest_info['results'] = results
            
            # Move to completed backtests
            self.completed_backtests[request_id] = backtest_info
            
            # Clean up running backtests to free memory and prevent state persistence
            if request_id in self.running_backtests:
                del self.running_backtests[request_id]
            
            # Save results to filesystem for quality gates
            try:
                from ...infrastructure.persistence.result_store import ResultStore
                result_store = ResultStore()
                
                # Create result data in the format expected by ResultStore
                result_data = {
                    'request_id': request_id,
                    'strategy_name': request.strategy_name,
                    'share_class': request.share_class,
                    'start_date': request.start_date.isoformat(),
                    'end_date': request.end_date.isoformat(),
                    'initial_capital': str(request.initial_capital),
                    'final_value': str(results.get('final_value', 0)),
                    'total_return': str(results.get('total_return', 0)),
                    'annualized_return': str(results.get('annualized_return', 0)),
                    'sharpe_ratio': str(results.get('sharpe_ratio', 0)),
                    'max_drawdown': str(results.get('max_drawdown', 0)),
                    'target_apy': results.get('target_apy'),
                    'target_max_drawdown': results.get('target_max_drawdown'),
                    'apy_vs_target': results.get('apy_vs_target'),
                    'drawdown_vs_target': results.get('drawdown_vs_target'),
                    'total_trades': results.get('total_trades', 0),
                    'winning_trades': results.get('winning_trades'),
                    'losing_trades': results.get('losing_trades'),
                    'total_fees': str(results.get('total_fees', 0)),
                    'equity_curve': results.get('equity_curve'),
                    'metrics_summary': results.get('metrics_summary', {})
                }
                
                await result_store.save_result(request_id, result_data)
                logger.info(f"✅ Results saved to filesystem for request {request_id}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to save results to filesystem: {e}")
                # Continue without failing the backtest
            
            logger.info(f"✅ Backtest completed successfully: {request_id}")
            return results
            
        except Exception as e:
            # Update status to failed
            backtest_info['status'] = 'failed'
            backtest_info['error'] = str(e)
            backtest_info['completed_at'] = datetime.utcnow()
            
            # Clean up running backtests even on failure to free memory
            if request_id in self.running_backtests:
                del self.running_backtests[request_id]
            
            logger.error(f"❌ Backtest failed: {request_id} - {e}")
            raise ValueError(f"Backtest execution failed: {e}")
    
    def _create_config(self, request: BacktestRequest) -> Dict[str, Any]:
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
            
            # Add request-specific overrides
            base_config.update({
                'share_class': request.share_class,
                'initial_capital': float(request.initial_capital),
                'backtest': {
                    'start_date': request.start_date.isoformat(),
                    'end_date': request.end_date.isoformat(),
                    'initial_capital': float(request.initial_capital)
                }
            })
            
            return base_config
            
        except Exception as e:
            logger.error(f"[BT-002] Config creation failed: {e}")
            raise
    
    def _map_strategy_to_mode(self, strategy_name: str) -> str:
        """Map strategy name to mode."""
        mode_map = {
            'pure_lending': 'pure_lending',
            'btc_basis': 'btc_basis',
            'eth_leveraged': 'eth_leveraged',
            'usdt_market_neutral': 'usdt_market_neutral',
            'usdt_market_neutral_no_leverage': 'usdt_market_neutral_no_leverage',
            'eth_staking_only': 'eth_staking_only'
        }
        return mode_map.get(strategy_name, 'pure_lending')
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    async def _execute_backtest(self, request_id: str):
        """Execute the backtest."""
        try:
            backtest_info = self.running_backtests[request_id]
            strategy_engine = backtest_info['strategy_engine']
            request = backtest_info['request']
            
            # Update progress
            backtest_info['progress'] = 0.1
            
            # Data provider initialization handled by strategy engine
            backtest_info['progress'] = 0.2
            
            # Run the backtest
            result = await strategy_engine.run_backtest(
                start_date=request.start_date,
                end_date=request.end_date
            )
            
            backtest_info['progress'] = 0.9
            
            # Extract performance data from the result
            performance = result.get('performance', {})
            logger.info(f"Backtest Service: Event engine result keys = {list(result.keys())}")
            logger.info(f"Backtest Service: Performance data = {performance}")
            
            # Store result
            self.completed_backtests[request_id] = {
                'request_id': request_id,
                'strategy_name': request.strategy_name,
                'start_date': request.start_date,
                'end_date': request.end_date,
                'initial_capital': request.initial_capital,
                'final_value': performance.get('final_value', request.initial_capital),
                'total_return': performance.get('total_return', 0.0),
                'annualized_return': performance.get('total_return_pct', 0.0),  # Use total_return_pct as annualized_return
                'sharpe_ratio': 0.0,  # Not calculated yet
                'max_drawdown': 0.0,  # Not calculated yet
                'total_trades': 0,  # Not calculated yet
                'total_fees': 0.0,  # Not calculated yet
                # Performance validation against targets
                'target_apy': result.get('config', {}).get('strategy', {}).get('target_apy'),
                'target_max_drawdown': result.get('config', {}).get('strategy', {}).get('max_drawdown'),
                'apy_vs_target': self._validate_apy_vs_target(performance.get('total_return_pct', 0.0), result.get('config', {}).get('strategy', {}).get('target_apy')),
                'drawdown_vs_target': self._validate_drawdown_vs_target(0.0, result.get('config', {}).get('strategy', {}).get('max_drawdown')),
                'metrics_history': result.get('pnl_history', []),
                'metrics_summary': result.get('metrics_summary', {}),
                'completed_at': datetime.utcnow()
            }
            
            # Update status
            backtest_info['status'] = 'completed'
            backtest_info['progress'] = 1.0
            backtest_info['completed_at'] = datetime.utcnow()
            
            logger.info(f"Backtest {request_id} completed successfully")
            
        except Exception as e:
            logger.error(f"[BT-004] Backtest {request_id} failed: {e}", exc_info=True)
            backtest_info = self.running_backtests[request_id]
            backtest_info['status'] = 'failed'
            backtest_info['error'] = str(e)
            backtest_info['completed_at'] = datetime.utcnow()
    
    async def get_status(self, request_id: str) -> Dict[str, Any]:
        """Get the status of a backtest."""
        if request_id in self.running_backtests:
            backtest_info = self.running_backtests[request_id]
            return {
                'status': backtest_info['status'],
                'progress': backtest_info['progress'],
                'started_at': backtest_info['started_at'],
                'completed_at': backtest_info.get('completed_at'),
                'error': backtest_info.get('error')
            }
        elif request_id in self.completed_backtests:
            return {
                'status': 'completed',
                'progress': 1.0,
                'started_at': self.completed_backtests[request_id].get('started_at'),
                'completed_at': self.completed_backtests[request_id]['completed_at']
            }
        else:
            return {'status': 'not_found'}
    
    async def get_result(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get the result of a completed backtest."""
        if request_id in self.completed_backtests:
            backtest_info = self.completed_backtests[request_id]
            
            # Extract the actual results from the event engine
            raw_results = backtest_info.get('results', {})
            performance = raw_results.get('performance', {})
            
            logger.info(f"Backtest Service get_result: raw_results keys = {list(raw_results.keys()) if raw_results else 'None'}")
            logger.info(f"Backtest Service get_result: performance = {performance}")
            
            # Return the performance data in the expected format
            return {
                'request_id': request_id,
                'strategy_name': backtest_info.get('request', {}).strategy_name if hasattr(backtest_info.get('request', {}), 'strategy_name') else 'pure_lending',
                'start_date': backtest_info.get('request', {}).start_date if hasattr(backtest_info.get('request', {}), 'start_date') else None,
                'end_date': backtest_info.get('request', {}).end_date if hasattr(backtest_info.get('request', {}), 'end_date') else None,
                'initial_capital': performance.get('initial_capital', 100000),
                'final_value': performance.get('final_value', 0),
                'total_return': performance.get('total_return', 0),
                'annualized_return': performance.get('total_return_pct', 0),
                'sharpe_ratio': 0.0,  # Not calculated yet
                'max_drawdown': 0.0,  # Not calculated yet
                'total_trades': len(raw_results.get('events', [])),
                'total_fees': 0.0,  # Not calculated yet
                'metrics_history': raw_results.get('pnl_history', []),
                'metrics_summary': {}
            }
        elif request_id in self.running_backtests:
            backtest_info = self.running_backtests[request_id]
            if backtest_info['status'] == 'completed':
                return await self.get_result(request_id)  # Recursive call to handle completed backtests
        return None
    
    async def cancel_backtest(self, request_id: str) -> bool:
        """Cancel a running backtest."""
        if request_id in self.running_backtests:
            backtest_info = self.running_backtests[request_id]
            if backtest_info['status'] == 'running':
                backtest_info['status'] = 'cancelled'
                backtest_info['completed_at'] = datetime.utcnow()
                return True
        return False
    
    def _validate_apy_vs_target(self, actual_apy: float, target_apy: Optional[float]) -> Dict[str, Any]:
        """Validate actual APY against target APY."""
        if target_apy is None:
            return {'status': 'no_target', 'message': 'No target APY specified'}
        
        if actual_apy >= target_apy:
            return {
                'status': 'meets_target',
                'message': f'APY {actual_apy:.2%} meets target {target_apy:.2%}',
                'actual': actual_apy,
                'target': target_apy,
                'difference': actual_apy - target_apy
            }
        else:
            return {
                'status': 'below_target',
                'message': f'APY {actual_apy:.2%} below target {target_apy:.2%}',
                'actual': actual_apy,
                'target': target_apy,
                'difference': actual_apy - target_apy
            }
    
    def _validate_drawdown_vs_target(self, actual_drawdown: float, target_drawdown: Optional[float]) -> Dict[str, Any]:
        """Validate actual max drawdown against target max drawdown."""
        if target_drawdown is None:
            return {'status': 'no_target', 'message': 'No target max drawdown specified'}
        
        # Convert to positive values for comparison (drawdowns are negative)
        actual_abs = abs(actual_drawdown)
        target_abs = abs(target_drawdown)
        
        if actual_abs <= target_abs:
            return {
                'status': 'within_target',
                'message': f'Max drawdown {actual_drawdown:.2%} within target {target_drawdown:.2%}',
                'actual': actual_drawdown,
                'target': target_drawdown,
                'difference': actual_abs - target_abs
            }
        else:
            return {
                'status': 'exceeds_target',
                'message': f'Max drawdown {actual_drawdown:.2%} exceeds target {target_drawdown:.2%}',
                'actual': actual_drawdown,
                'target': target_drawdown,
                'difference': actual_abs - target_abs
            }


class MockExecutionEngine:
    """Mock execution engine for backtesting."""
    
    def __init__(self):
        self.trades = []
    
    async def execute_trade(self, trade_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock trade execution."""
        trade_result = {
            'trade_id': f"trade_{len(self.trades) + 1}",
            'status': 'filled',
            'executed_price': trade_data.get('price', 100.0),
            'executed_quantity': trade_data.get('quantity', 1.0),
            'fees': trade_data.get('quantity', 1.0) * 0.001,  # 0.1% fee
            'timestamp': datetime.utcnow()
        }
        
        self.trades.append(trade_result)
        return trade_result
    
    async def get_balance(self, asset: str) -> float:
        """Mock balance retrieval."""
        return 1000.0  # Mock balance
    
    async def get_positions(self) -> Dict[str, float]:
        """Mock positions retrieval."""
        return {'BTC': 0.1, 'ETH': 1.0, 'USDT': 10000.0}