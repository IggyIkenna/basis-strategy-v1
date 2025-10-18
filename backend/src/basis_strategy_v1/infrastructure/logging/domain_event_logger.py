"""
Domain Event Logger

Writes domain events to JSONL files for comprehensive system observability.

Each event type gets its own JSONL file in the events/ subdirectory:
- positions.jsonl
- exposures.jsonl
- risk_assessments.jsonl
- pnl_calculations.jsonl
- orders.jsonl
- operation_executions.jsonl
- atomic_operation_groups.jsonl
- execution_deltas.jsonl
- reconciliations.jsonl
- tight_loop_executions.jsonl
- event_logger_operations.jsonl
- strategy_decisions.jsonl

Reference: docs/LOGGING_GUIDE.md - Domain Event Logging
"""

import json
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone

from ...core.models.domain_events import (
    PositionSnapshot,
    ExposureSnapshot,
    RiskAssessment,
    PnLCalculation,
    OrderEvent,
    OperationExecutionEvent,
    AtomicOperationGroupEvent,
    ExecutionDeltaEvent,
    ReconciliationEvent,
    TightLoopExecutionEvent,
    EventLoggingOperationEvent,
    StrategyDecision
)


class DomainEventLogger:
    """
    Logs domain events to JSONL files.
    
    Each event type is written to a separate JSONL file for easy
    querying and analysis.
    """
    
    def __init__(self, log_dir: Path):
        """
        Initialize domain event logger.
        
        Args:
            log_dir: Path to log directory (logs/{correlation_id}/{pid}/)
        """
        self.log_dir = Path(log_dir)
        self.events_dir = self.log_dir / "events"
        
        # Ensure events directory exists
        self.events_dir.mkdir(parents=True, exist_ok=True)
        
        # Event file mapping
        self.event_files = {
            'positions': self.events_dir / 'positions.jsonl',
            'exposures': self.events_dir / 'exposures.jsonl',
            'risk_assessments': self.events_dir / 'risk_assessments.jsonl',
            'pnl_calculations': self.events_dir / 'pnl_calculations.jsonl',
            'orders': self.events_dir / 'orders.jsonl',
            'operation_executions': self.events_dir / 'operation_executions.jsonl',
            'atomic_operation_groups': self.events_dir / 'atomic_operation_groups.jsonl',
            'execution_deltas': self.events_dir / 'execution_deltas.jsonl',
            'reconciliations': self.events_dir / 'reconciliations.jsonl',
            'tight_loop_executions': self.events_dir / 'tight_loop_executions.jsonl',
            'event_logger_operations': self.events_dir / 'event_logger_operations.jsonl',
            'strategy_decisions': self.events_dir / 'strategy_decisions.jsonl'
        }
    
    def log_position_snapshot(self, event: PositionSnapshot) -> None:
        """
        Log a position snapshot event.
        
        Args:
            event: PositionSnapshot event
        """
        self._write_event('positions', event)
    
    def log_exposure_snapshot(self, event: ExposureSnapshot) -> None:
        """
        Log an exposure snapshot event.
        
        Args:
            event: ExposureSnapshot event
        """
        self._write_event('exposures', event)
    
    def log_risk_assessment(self, event: RiskAssessment) -> None:
        """
        Log a risk assessment event.
        
        Args:
            event: RiskAssessment event
        """
        self._write_event('risk_assessments', event)
    
    def log_pnl_calculation(self, event: PnLCalculation) -> None:
        """
        Log a P&L calculation event.
        
        Args:
            event: PnLCalculation event
        """
        self._write_event('pnl_calculations', event)
    
    def log_order_event(self, event: OrderEvent) -> None:
        """
        Log an order event.
        
        Args:
            event: OrderEvent event
        """
        self._write_event('orders', event)
    
    def log_operation_execution(self, event: OperationExecutionEvent) -> None:
        """
        Log an operation execution event.
        
        Args:
            event: OperationExecutionEvent event
        """
        self._write_event('operation_executions', event)
    
    def log_atomic_group(self, event: AtomicOperationGroupEvent) -> None:
        """
        Log an atomic operation group event.
        
        Args:
            event: AtomicOperationGroupEvent event
        """
        self._write_event('atomic_operation_groups', event)
    
    def log_execution_delta(self, event: ExecutionDeltaEvent) -> None:
        """
        Log an execution delta event.
        
        Args:
            event: ExecutionDeltaEvent event
        """
        self._write_event('execution_deltas', event)
    
    def log_reconciliation(self, event: ReconciliationEvent) -> None:
        """
        Log a reconciliation event.
        
        Args:
            event: ReconciliationEvent event
        """
        self._write_event('reconciliations', event)
    
    def log_tight_loop_execution(self, event: TightLoopExecutionEvent) -> None:
        """
        Log a tight loop execution event.
        
        Args:
            event: TightLoopExecutionEvent event
        """
        self._write_event('tight_loop_executions', event)
    
    def log_event_logging_operation(self, event: EventLoggingOperationEvent) -> None:
        """
        Log an event logging operation (meta-logging).
        
        Args:
            event: EventLoggingOperationEvent event
        """
        self._write_event('event_logger_operations', event)
    
    def log_strategy_decision(self, event: StrategyDecision) -> None:
        """
        Log a strategy decision event.
        
        Args:
            event: StrategyDecision event
        """
        self._write_event('strategy_decisions', event)
    
    def _write_event(self, event_type: str, event: any) -> None:
        """
        Write event to JSONL file.
        
        Args:
            event_type: Event type key
            event: Pydantic event model instance
        """
        try:
            file_path = self.event_files.get(event_type)
            
            if not file_path:
                # Log error but don't fail
                print(f"ERROR: Unknown event type: {event_type}")
                return
            
            # Serialize event to JSON
            event_json = event.model_dump_json()
            
            # Append to JSONL file
            with open(file_path, 'a') as f:
                f.write(event_json + '\n')
                f.flush()  # Ensure immediate write
            
        except Exception as e:
            # Log error but don't fail (avoid recursive logging issues)
            print(f"ERROR: Failed to write {event_type} event: {e}")
            # Could log meta-event here, but avoid recursion
    
    def flush_all(self) -> None:
        """
        Flush all event file buffers.
        
        This ensures all events are written to disk immediately.
        """
        # Python file handles auto-flush on close, but we can
        # ensure by explicitly flushing if files are open
        pass  # No-op for now since we flush after each write
    
    def get_event_count(self, event_type: str) -> int:
        """
        Get count of events in a specific event file.
        
        Args:
            event_type: Event type key
            
        Returns:
            Number of events (lines) in the file
        """
        file_path = self.event_files.get(event_type)
        
        if not file_path or not file_path.exists():
            return 0
        
        with open(file_path, 'r') as f:
            return sum(1 for _ in f)
    
    def read_events(self, event_type: str, limit: Optional[int] = None) -> list:
        """
        Read events from a specific event file.
        
        Args:
            event_type: Event type key
            limit: Maximum number of events to read (None = all)
            
        Returns:
            List of event dictionaries
        """
        file_path = self.event_files.get(event_type)
        
        if not file_path or not file_path.exists():
            return []
        
        events = []
        with open(file_path, 'r') as f:
            for i, line in enumerate(f):
                if limit and i >= limit:
                    break
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"WARNING: Failed to parse event line {i+1}: {e}")
        
        return events
    
    def get_latest_event(self, event_type: str) -> Optional[dict]:
        """
        Get the most recent event of a specific type.
        
        Args:
            event_type: Event type key
            
        Returns:
            Latest event dictionary or None
        """
        file_path = self.event_files.get(event_type)
        
        if not file_path or not file_path.exists():
            return None
        
        # Read last line
        with open(file_path, 'rb') as f:
            try:
                f.seek(-2, 2)  # Jump to second-to-last byte
                while f.read(1) != b'\n':  # Find last newline
                    f.seek(-2, 1)
                last_line = f.readline().decode()
                return json.loads(last_line)
            except:
                return None

