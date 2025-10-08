"""
Analysis scripts for post-facto data analysis and validation.

This module contains analyzers for:
- AAVE interest rate impact analysis
- Performance metrics calculation
- Risk assessment tools
"""

from .analyze_aave_rate_impact import AAVERateImpactAnalyzer

__all__ = [
    "AAVERateImpactAnalyzer",
]