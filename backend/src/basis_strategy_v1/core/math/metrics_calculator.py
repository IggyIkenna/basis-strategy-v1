"""Metrics Calculator - Pure calculation functions for performance metrics."""

from decimal import Decimal
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Error codes for Metrics Calculator
ERROR_CODES = {
    'METRICS-001': 'Portfolio metrics calculation failed',
    'METRICS-002': 'Return calculation failed',
    'METRICS-003': 'Balance count calculation failed',
    'METRICS-004': 'Net exposure calculation failed',
    'METRICS-005': 'Metrics validation failed'
}


class MetricsCalculator:
    """Pure metrics calculation functions - no side effects or I/O."""
    
    @staticmethod
    def calculate_metrics(
        portfolio,
        initial_capital: Decimal,
        timestamp: datetime
    ) -> Dict[str, any]:
        """
        Calculate portfolio metrics.
        
        Args:
            portfolio: Portfolio state
            initial_capital: Initial capital
            timestamp: Current timestamp
            
        Returns:
            Dictionary of metrics
        """
        metrics = {
            'timestamp': timestamp.isoformat(),
            'portfolio_value': float(portfolio.total_value_usd),
            'initial_capital': float(initial_capital),
            'total_return': float(
                (portfolio.total_value_usd - initial_capital) / initial_capital
                if initial_capital > 0 else Decimal("0")
            ),
            'balance_count': sum(
                len(balances) for balances in portfolio.balances.values()
            ),
            'debt_count': sum(
                len(debts) for debts in portfolio.debts.values()
            ),
            'position_count': len(portfolio.positions)
        }
        
        # Calculate net exposure
        total_assets = sum(
            sum(balances.values(), Decimal("0"))
            for balances in portfolio.balances.values()
        )
        total_debts = sum(
            sum(debts.values(), Decimal("0"))
            for debts in portfolio.debts.values()
        )
        
        metrics['total_assets'] = float(total_assets)
        metrics['total_debts'] = float(total_debts)
        metrics['net_value'] = float(total_assets - total_debts)
        
        return metrics



