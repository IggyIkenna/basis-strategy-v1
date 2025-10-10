"""
Execution Manager Component

Manages trade execution across multiple venues with proper error handling,
position tracking, and reconciliation.

Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Section 7 (Execution Architecture)
Reference: docs/specs/05_EXECUTION_MANAGER.md - Execution manager specification
"""

import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ...interfaces.execution_interface import ExecutionInterface
from ...interfaces.position_interface import PositionInterface
from ...interfaces.risk_interface import RiskInterface
from ...infrastructure.logging.structured_logger import get_execution_manager_logger


class ExecutionStatus(Enum):
    """Execution status enumeration."""
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ExecutionRequest:
    """Execution request data structure."""
    request_id: str
    strategy_name: str
    venue: str
    asset: str
    side: str  # 'buy' or 'sell'
    quantity: float
    price: Optional[float] = None
    order_type: str = 'market'  # 'market', 'limit', 'stop'
    time_in_force: str = 'GTC'  # 'GTC', 'IOC', 'FOK'
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ExecutionResult:
    """Execution result data structure."""
    request_id: str
    status: ExecutionStatus
    venue: str
    asset: str
    side: str
    quantity: float
    executed_quantity: float
    average_price: float
    fees: float
    timestamp: float
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ExecutionManager:
    """Manages trade execution across multiple venues."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = get_execution_manager_logger()
        self.execution_interface = None
        self.position_interface = None
        self.risk_interface = None
        
        # Execution state
        self.pending_requests: Dict[str, ExecutionRequest] = {}
        self.completed_requests: Dict[str, ExecutionResult] = {}
        self.failed_requests: Dict[str, ExecutionResult] = {}
        
        # Venue configurations
        self.venue_configs = config.get('venues', {})
        self.venue_limits = config.get('venue_limits', {})
        
        self.logger.info("Execution Manager initialized", event_type='initialization')
    
    def set_interfaces(
        self,
        execution_interface: ExecutionInterface,
        position_interface: PositionInterface,
        risk_interface: RiskInterface
    ):
        """Set required interfaces."""
        self.execution_interface = execution_interface
        self.position_interface = position_interface
        self.risk_interface = risk_interface
        
        self.logger.info("Execution interfaces set", event_type='configuration')
    
    def execute_trade(
        self,
        strategy_name: str,
        venue: str,
        asset: str,
        side: str,
        quantity: float,
        price: Optional[float] = None,
        order_type: str = 'market',
        **kwargs
    ) -> str:
        """
        Execute a trade request.
        
        Args:
            strategy_name: Name of the strategy requesting execution
            venue: Venue to execute on
            asset: Asset to trade
            side: 'buy' or 'sell'
            quantity: Quantity to trade
            price: Price for limit orders
            order_type: Type of order ('market', 'limit', 'stop')
            **kwargs: Additional parameters
            
        Returns:
            Request ID for tracking
        """
        request_id = f"{strategy_name}_{venue}_{asset}_{int(time.time() * 1000)}"
        
        # Validate request
        if not self._validate_execution_request(venue, asset, side, quantity, price):
            error_msg = f"Invalid execution request: {venue}, {asset}, {side}, {quantity}"
            self.logger.error(error_msg, event_type='validation_error')
            raise ValueError(error_msg)
        
        # Check risk limits
        if not self._check_risk_limits(strategy_name, venue, asset, side, quantity):
            error_msg = f"Risk limits exceeded for {strategy_name}"
            self.logger.warning(error_msg, event_type='risk_limit_exceeded')
            raise ValueError(error_msg)
        
        # Create execution request
        request = ExecutionRequest(
            request_id=request_id,
            strategy_name=strategy_name,
            venue=venue,
            asset=asset,
            side=side,
            quantity=quantity,
            price=price,
            order_type=order_type,
            time_in_force=kwargs.get('time_in_force', 'GTC'),
            metadata=kwargs.get('metadata', {})
        )
        
        # Add to pending requests
        self.pending_requests[request_id] = request
        
        # Execute asynchronously (in real implementation)
        self._execute_request_async(request)
        
        self.logger.info(
            f"Trade execution requested: {request_id}",
            event_type='execution_requested',
            request_id=request_id,
            strategy_name=strategy_name,
            venue=venue,
            asset=asset,
            side=side,
            quantity=quantity
        )
        
        return request_id
    
    def get_execution_status(self, request_id: str) -> Optional[ExecutionResult]:
        """Get execution status for a request."""
        if request_id in self.completed_requests:
            return self.completed_requests[request_id]
        elif request_id in self.failed_requests:
            return self.failed_requests[request_id]
        elif request_id in self.pending_requests:
            # Still pending
            request = self.pending_requests[request_id]
            return ExecutionResult(
                request_id=request_id,
                status=ExecutionStatus.PENDING,
                venue=request.venue,
                asset=request.asset,
                side=request.side,
                quantity=request.quantity,
                executed_quantity=0.0,
                average_price=0.0,
                fees=0.0,
                timestamp=time.time()
            )
        else:
            return None
    
    def cancel_execution(self, request_id: str) -> bool:
        """Cancel a pending execution request."""
        if request_id not in self.pending_requests:
            self.logger.warning(f"Cannot cancel non-pending request: {request_id}")
            return False
        
        request = self.pending_requests[request_id]
        
        # In real implementation, would cancel with venue
        # For now, just mark as cancelled
        result = ExecutionResult(
            request_id=request_id,
            status=ExecutionStatus.CANCELLED,
            venue=request.venue,
            asset=request.asset,
            side=request.side,
            quantity=request.quantity,
            executed_quantity=0.0,
            average_price=0.0,
            fees=0.0,
            timestamp=time.time()
        )
        
        # Move from pending to completed
        del self.pending_requests[request_id]
        self.completed_requests[request_id] = result
        
        self.logger.info(f"Execution cancelled: {request_id}", event_type='execution_cancelled')
        return True
    
    def get_execution_history(
        self,
        strategy_name: Optional[str] = None,
        venue: Optional[str] = None,
        asset: Optional[str] = None
    ) -> List[ExecutionResult]:
        """Get execution history with optional filters."""
        all_results = list(self.completed_requests.values()) + list(self.failed_requests.values())
        
        filtered_results = []
        for result in all_results:
            if strategy_name and result.request_id.split('_')[0] != strategy_name:
                continue
            if venue and result.venue != venue:
                continue
            if asset and result.asset != asset:
                continue
            filtered_results.append(result)
        
        return sorted(filtered_results, key=lambda x: x.timestamp, reverse=True)
    
    def _validate_execution_request(
        self,
        venue: str,
        asset: str,
        side: str,
        quantity: float,
        price: Optional[float]
    ) -> bool:
        """Validate execution request parameters."""
        # Check venue exists
        if venue not in self.venue_configs:
            self.logger.error(f"Unknown venue: {venue}")
            return False
        
        # Check side is valid
        if side not in ['buy', 'sell']:
            self.logger.error(f"Invalid side: {side}")
            return False
        
        # Check quantity is positive
        if quantity <= 0:
            self.logger.error(f"Invalid quantity: {quantity}")
            return False
        
        # Check price for limit orders
        if price is not None and price <= 0:
            self.logger.error(f"Invalid price: {price}")
            return False
        
        return True
    
    def _check_risk_limits(
        self,
        strategy_name: str,
        venue: str,
        asset: str,
        side: str,
        quantity: float
    ) -> bool:
        """Check risk limits before execution."""
        if not self.risk_interface:
            self.logger.warning("No risk interface available, skipping risk checks")
            return True
        
        try:
            # Check position limits
            current_position = self.position_interface.get_position(strategy_name, asset)
            new_position = current_position + (quantity if side == 'buy' else -quantity)
            
            # Check if new position exceeds limits
            max_position = self.venue_limits.get(venue, {}).get('max_position', float('inf'))
            if abs(new_position) > max_position:
                self.logger.warning(
                    f"Position limit exceeded: {new_position} > {max_position}",
                    event_type='risk_limit_exceeded'
                )
                return False
            
            # Check daily volume limits
            daily_volume = self._get_daily_volume(strategy_name, venue, asset)
            max_daily_volume = self.venue_limits.get(venue, {}).get('max_daily_volume', float('inf'))
            if daily_volume + quantity > max_daily_volume:
                self.logger.warning(
                    f"Daily volume limit exceeded: {daily_volume + quantity} > {max_daily_volume}",
                    event_type='risk_limit_exceeded'
                )
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Risk check failed: {e}", event_type='risk_check_error')
            return False
    
    def _get_daily_volume(self, strategy_name: str, venue: str, asset: str) -> float:
        """Get daily volume for a strategy/venue/asset combination."""
        # In real implementation, would query position interface
        # For now, return 0
        return 0.0
    
    def _execute_request_async(self, request: ExecutionRequest):
        """Execute request asynchronously (simulated)."""
        # In real implementation, would use async execution
        # For now, simulate execution
        
        # Simulate execution delay
        time.sleep(0.1)
        
        # Simulate successful execution
        result = ExecutionResult(
            request_id=request.request_id,
            status=ExecutionStatus.COMPLETED,
            venue=request.venue,
            asset=request.asset,
            side=request.side,
            quantity=request.quantity,
            executed_quantity=request.quantity,
            average_price=request.price or 100.0,  # Simulated price
            fees=request.quantity * 0.001,  # 0.1% fee
            timestamp=time.time(),
            metadata=request.metadata
        )
        
        # Move from pending to completed
        del self.pending_requests[request.request_id]
        self.completed_requests[request.request_id] = result
        
        # Update position interface
        if self.position_interface:
            try:
                self.position_interface.update_position(
                    request.strategy_name,
                    request.asset,
                    request.executed_quantity if request.side == 'buy' else -request.executed_quantity,
                    request.average_price
                )
            except Exception as e:
                self.logger.error(f"Failed to update position: {e}", event_type='position_update_error')
        
        self.logger.info(
            f"Execution completed: {request.request_id}",
            event_type='execution_completed',
            request_id=request.request_id,
            executed_quantity=result.executed_quantity,
            average_price=result.average_price,
            fees=result.fees
        )
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get execution manager health status."""
        return {
            'status': 'healthy',
            'pending_requests': len(self.pending_requests),
            'completed_requests': len(self.completed_requests),
            'failed_requests': len(self.failed_requests),
            'venues_configured': len(self.venue_configs),
            'interfaces_connected': {
                'execution': self.execution_interface is not None,
                'position': self.position_interface is not None,
                'risk': self.risk_interface is not None
            }
        }