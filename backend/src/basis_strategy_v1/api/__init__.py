"""API layer package for basis_strategy_v1_v1.

FastAPI application layer following service-oriented architecture.
Provides REST endpoints for backtest execution, strategy management, and results.
"""

from .main import create_application

__all__ = [
    "create_application",
]
