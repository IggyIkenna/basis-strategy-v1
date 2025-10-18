"""
Core Models Package

Unified Order and ExecutionHandshake models for the basis-strategy-v1 platform.
Replaces the previous StrategyAction, Trade, and instruction block abstractions.

Reference: docs/ARCHITECTURAL_DECISION_RECORDS.md - ADR-059 (Unified Execution Flow)
Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Updated execution flow
"""

from .order import Order, OrderOperation, VenueType
from .execution import ExecutionHandshake, OperationType, ExecutionStatus
from .domain_events import (
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

__all__ = [
    # Order model
    'Order',
    'OrderOperation', 
    'VenueType',
    
    # Execution models
    'ExecutionHandshake',
    'OperationType',
    'ExecutionStatus',
    
    # Domain event models
    'PositionSnapshot',
    'ExposureSnapshot',
    'RiskAssessment',
    'PnLCalculation',
    'OrderEvent',
    'OperationExecutionEvent',
    'AtomicOperationGroupEvent',
    'ExecutionDeltaEvent',
    'ReconciliationEvent',
    'TightLoopExecutionEvent',
    'EventLoggingOperationEvent',
    'StrategyDecision'
]
