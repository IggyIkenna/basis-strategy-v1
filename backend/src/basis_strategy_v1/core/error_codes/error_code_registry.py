"""
Error Code Registry

Centralized registry for all error codes across the system.
Provides validation, lookup, and management of error codes.
"""

import logging
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorCodeInfo:
    """Information about an error code."""
    code: str
    message: str
    component: str
    severity: ErrorSeverity
    description: Optional[str] = None
    resolution: Optional[str] = None


class ErrorCodeRegistry:
    """Centralized registry for all error codes."""
    
    def __init__(self):
        self._error_codes: Dict[str, ErrorCodeInfo] = {}
        self._component_codes: Dict[str, List[str]] = {}
        self._severity_codes: Dict[ErrorSeverity, List[str]] = {}
        
        # Initialize with all error codes
        self._register_all_error_codes()
    
    def _register_all_error_codes(self):
        """Register all error codes from all components."""
        
        # Position Monitor
        self._register_component_codes("POS", {
            'POS-001': ('Balance drift detected during reconciliation', ErrorSeverity.MEDIUM),
            'POS-002': ('Negative balance in unexpected token', ErrorSeverity.HIGH),
            'POS-003': ('CEX account balance mismatch', ErrorSeverity.MEDIUM),
            'POS-004': ('Invalid venue specified in balance update', ErrorSeverity.MEDIUM),
            'POS-005': ('Redis connection lost during publish', ErrorSeverity.HIGH)
        })
        
        # Exposure Monitor
        self._register_component_codes("EXP", {
            'EXP-001': ('Market data missing for timestamp', ErrorSeverity.HIGH),
            'EXP-002': ('AAVE index calculation failed', ErrorSeverity.HIGH),
            'EXP-003': ('Oracle price unavailable for LST conversion', ErrorSeverity.HIGH),
            'EXP-004': ('Net delta calculation overflow', ErrorSeverity.MEDIUM),
            'EXP-005': ('Position snapshot invalid structure', ErrorSeverity.MEDIUM)
        })
        
        # Risk Monitor
        self._register_component_codes("RISK", {
            'RISK-001': ('Health factor below safe threshold', ErrorSeverity.CRITICAL),
            'RISK-002': ('Margin ratio critical', ErrorSeverity.CRITICAL),
            'RISK-003': ('Delta drift excessive', ErrorSeverity.HIGH),
            'RISK-004': ('Config validation failed', ErrorSeverity.HIGH),
            'RISK-005': ('Exposure data missing required fields', ErrorSeverity.HIGH),
            'RISK-006': ('AAVE liquidation simulation failed', ErrorSeverity.MEDIUM),
            'RISK-007': ('CEX liquidation simulation failed', ErrorSeverity.MEDIUM),
            'RISK-008': ('LST price deviation critical', ErrorSeverity.HIGH),
            'RISK-009': ('Risk calculation error', ErrorSeverity.MEDIUM)
        })
        
        # Strategy Manager
        self._register_component_codes("STRAT", {
            'STRAT-001': ('Strategy mode detection failed', ErrorSeverity.HIGH),
            'STRAT-002': ('Invalid strategy mode configuration', ErrorSeverity.HIGH),
            'STRAT-003': ('Desired position calculation failed', ErrorSeverity.HIGH),
            'STRAT-004': ('Strategy decision generation failed', ErrorSeverity.HIGH),
            'STRAT-005': ('Component orchestration failed', ErrorSeverity.MEDIUM),
            'STRAT-006': ('Position change handling failed', ErrorSeverity.MEDIUM),
            'STRAT-007': ('Instruction generation failed', ErrorSeverity.MEDIUM),
            'STRAT-008': ('Rebalancing check failed', ErrorSeverity.MEDIUM),
            'STRAT-009': ('KING token management failed', ErrorSeverity.MEDIUM),
            'STRAT-010': ('Redis communication failed', ErrorSeverity.HIGH)
        })
        
        # CEX Execution Manager
        self._register_component_codes("CEX", {
            'CEX-001': ('Trade execution failed', ErrorSeverity.HIGH),
            'CEX-002': ('Insufficient margin for trade', ErrorSeverity.HIGH),
            'CEX-003': ('Price slippage excessive', ErrorSeverity.MEDIUM),
            'CEX-004': ('Exchange client initialization failed', ErrorSeverity.HIGH),
            'CEX-005': ('Order placement failed', ErrorSeverity.HIGH),
            'CEX-006': ('Balance retrieval failed', ErrorSeverity.MEDIUM),
            'CEX-007': ('Position retrieval failed', ErrorSeverity.MEDIUM),
            'CEX-008': ('Slippage simulation failed', ErrorSeverity.LOW),
            'CEX-009': ('Exchange API connection failed', ErrorSeverity.HIGH),
            'CEX-010': ('Trade instruction validation failed', ErrorSeverity.MEDIUM),
            'CEX-011': ('Market data unavailable', ErrorSeverity.MEDIUM),
            'CEX-012': ('Exchange rate limit exceeded', ErrorSeverity.MEDIUM)
        })
        
        # OnChain Execution Manager
        self._register_component_codes("CHAIN", {
            'CHAIN-001': ('Transaction execution failed', ErrorSeverity.HIGH),
            'CHAIN-002': ('Insufficient gas for operation', ErrorSeverity.HIGH),
            'CHAIN-003': ('Flash loan execution failed', ErrorSeverity.HIGH),
            'CHAIN-004': ('Contract interaction failed', ErrorSeverity.HIGH),
            'CHAIN-005': ('Web3 client initialization failed', ErrorSeverity.HIGH),
            'CHAIN-006': ('Gas cost calculation failed', ErrorSeverity.MEDIUM),
            'CHAIN-007': ('Atomic leverage loop failed', ErrorSeverity.HIGH),
            'CHAIN-008': ('Sequential leverage loop failed', ErrorSeverity.HIGH),
            'CHAIN-009': ('Position unwind failed', ErrorSeverity.HIGH),
            'CHAIN-010': ('KING token unwrap failed', ErrorSeverity.MEDIUM),
            'CHAIN-011': ('Alchemy client connection failed', ErrorSeverity.HIGH),
            'CHAIN-012': ('Contract ABI loading failed', ErrorSeverity.MEDIUM)
        })
        
        # Data Provider
        self._register_component_codes("DATA", {
            'DATA-001': ('Data file not found', ErrorSeverity.HIGH),
            'DATA-002': ('Data file parsing failed', ErrorSeverity.HIGH),
            'DATA-003': ('Data validation failed', ErrorSeverity.HIGH),
            'DATA-004': ('Timestamp alignment violated', ErrorSeverity.MEDIUM),
            'DATA-005': ('Missing data for period', ErrorSeverity.MEDIUM),
            'DATA-006': ('Data synchronization failed', ErrorSeverity.MEDIUM),
            'DATA-007': ('Market data snapshot failed', ErrorSeverity.MEDIUM),
            'DATA-008': ('Data source unavailable', ErrorSeverity.HIGH),
            'DATA-009': ('Data loading timeout', ErrorSeverity.MEDIUM),
            'DATA-010': ('Data format invalid', ErrorSeverity.MEDIUM),
            'DATA-011': ('Backtest start date before available data range', ErrorSeverity.HIGH),
            'DATA-012': ('Backtest end date after available data range', ErrorSeverity.HIGH),
            'DATA-013': ('Environment variables for data range not set', ErrorSeverity.CRITICAL)
        })
        
        # Event Logger
        self._register_component_codes("EVENT", {
            'EVENT-001': ('Event logging failed', ErrorSeverity.MEDIUM),
            'EVENT-002': ('Event serialization failed', ErrorSeverity.MEDIUM),
            'EVENT-003': ('Event storage failed', ErrorSeverity.MEDIUM),
            'EVENT-004': ('Event retrieval failed', ErrorSeverity.LOW),
            'EVENT-005': ('Event validation failed', ErrorSeverity.MEDIUM)
        })
        
        # Configuration components
        self._register_component_codes("CONFIG", {
            'CONFIG-001': ('Configuration file not found', ErrorSeverity.CRITICAL),
            'CONFIG-002': ('Configuration file parsing failed', ErrorSeverity.CRITICAL),
            'CONFIG-003': ('Required configuration section missing', ErrorSeverity.CRITICAL),
            'CONFIG-004': ('Configuration validation failed', ErrorSeverity.CRITICAL),
            'CONFIG-005': ('Environment variable missing', ErrorSeverity.HIGH),
            'CONFIG-006': ('Mode configuration invalid', ErrorSeverity.HIGH),
            'CONFIG-007': ('Venue configuration invalid', ErrorSeverity.HIGH),
            'CONFIG-008': ('Share class configuration invalid', ErrorSeverity.HIGH),
            'CONFIG-009': ('Business logic validation failed', ErrorSeverity.HIGH),
            'CONFIG-010': ('Configuration structure invalid', ErrorSeverity.HIGH)
        })
        
        # Live Data Provider
        self._register_component_codes("LIVE", {
            'LIVE-001': ('Live data source connection failed', ErrorSeverity.HIGH),
            'LIVE-002': ('API rate limit exceeded', ErrorSeverity.MEDIUM),
            'LIVE-003': ('Data source timeout', ErrorSeverity.MEDIUM),
            'LIVE-004': ('Invalid API response', ErrorSeverity.MEDIUM),
            'LIVE-005': ('Cache operation failed', ErrorSeverity.LOW),
            'LIVE-006': ('Data source authentication failed', ErrorSeverity.HIGH),
            'LIVE-007': ('Data source unavailable', ErrorSeverity.HIGH),
            'LIVE-008': ('Data parsing failed', ErrorSeverity.MEDIUM),
            'LIVE-009': ('Network connection failed', ErrorSeverity.HIGH),
            'LIVE-010': ('Data source configuration invalid', ErrorSeverity.HIGH)
        })
        
        # Math Calculators
        self._register_component_codes("AAVE", {
            'AAVE-001': ('Rate model not found for asset', ErrorSeverity.HIGH),
            'AAVE-002': ('Rate calculation failed', ErrorSeverity.HIGH),
            'AAVE-003': ('Market impact calculation failed', ErrorSeverity.MEDIUM),
            'AAVE-004': ('Calibration validation failed', ErrorSeverity.MEDIUM),
            'AAVE-005': ('Utilization impact calculation failed', ErrorSeverity.MEDIUM),
            'AAVE-006': ('Invalid rate model parameters', ErrorSeverity.HIGH),
            'AAVE-007': ('Asset lookup failed', ErrorSeverity.MEDIUM),
            'AAVE-008': ('Rate model configuration invalid', ErrorSeverity.HIGH)
        })
        
        self._register_component_codes("HEALTH", {
            'HEALTH-001': ('Health factor calculation failed', ErrorSeverity.HIGH),
            'HEALTH-002': ('Weighted health factor calculation failed', ErrorSeverity.HIGH),
            'HEALTH-003': ('Distance to liquidation calculation failed', ErrorSeverity.HIGH),
            'HEALTH-004': ('Risk score calculation failed', ErrorSeverity.MEDIUM),
            'HEALTH-005': ('Safe withdrawal calculation failed', ErrorSeverity.MEDIUM),
            'HEALTH-006': ('Safe borrow calculation failed', ErrorSeverity.MEDIUM),
            'HEALTH-007': ('Cascade risk calculation failed', ErrorSeverity.MEDIUM),
            'HEALTH-008': ('Required collateral calculation failed', ErrorSeverity.MEDIUM)
        })
        
        # Add more math calculators...
        self._register_component_codes("LTV", {
            'LTV-001': ('LTV calculation failed', ErrorSeverity.HIGH),
            'LTV-002': ('Projected LTV calculation failed', ErrorSeverity.HIGH),
            'LTV-003': ('Max LTV calculation failed', ErrorSeverity.HIGH),
            'LTV-004': ('Leverage capacity calculation failed', ErrorSeverity.HIGH),
            'LTV-005': ('Health factor calculation failed', ErrorSeverity.HIGH),
            'LTV-006': ('LTV safety validation failed', ErrorSeverity.HIGH),
            'LTV-007': ('E-mode eligibility check failed', ErrorSeverity.MEDIUM),
            'LTV-008': ('Leverage headroom calculation failed', ErrorSeverity.MEDIUM)
        })
        
        self._register_component_codes("MARGIN", {
            'MARGIN-001': ('Margin capacity calculation failed', ErrorSeverity.HIGH),
            'MARGIN-002': ('Basis margin estimation failed', ErrorSeverity.HIGH),
            'MARGIN-003': ('Margin requirement calculation failed', ErrorSeverity.HIGH),
            'MARGIN-004': ('Maintenance margin calculation failed', ErrorSeverity.HIGH),
            'MARGIN-005': ('Margin ratio calculation failed', ErrorSeverity.HIGH),
            'MARGIN-006': ('Liquidation price calculation failed', ErrorSeverity.HIGH),
            'MARGIN-007': ('Available margin calculation failed', ErrorSeverity.HIGH),
            'MARGIN-008': ('Cross margin calculation failed', ErrorSeverity.MEDIUM),
            'MARGIN-009': ('Funding payment calculation failed', ErrorSeverity.MEDIUM),
            'MARGIN-010': ('Portfolio margin calculation failed', ErrorSeverity.MEDIUM),
            'MARGIN-011': ('Margin health calculation failed', ErrorSeverity.HIGH),
            'MARGIN-012': ('Basis margin calculation failed', ErrorSeverity.HIGH)
        })
        
        self._register_component_codes("YIELD", {
            'YIELD-001': ('APY to APR conversion failed', ErrorSeverity.MEDIUM),
            'YIELD-002': ('APR to APY conversion failed', ErrorSeverity.MEDIUM),
            'YIELD-003': ('Simple yield calculation failed', ErrorSeverity.MEDIUM),
            'YIELD-004': ('Compound yield calculation failed', ErrorSeverity.MEDIUM),
            'YIELD-005': ('Net yield calculation failed', ErrorSeverity.MEDIUM),
            'YIELD-006': ('Staking yield calculation failed', ErrorSeverity.MEDIUM),
            'YIELD-007': ('Funding yield calculation failed', ErrorSeverity.MEDIUM),
            'YIELD-008': ('Lending yield calculation failed', ErrorSeverity.MEDIUM),
            'YIELD-009': ('Blended APR calculation failed', ErrorSeverity.MEDIUM),
            'YIELD-010': ('Effective yield calculation failed', ErrorSeverity.MEDIUM),
            'YIELD-011': ('Impermanent loss calculation failed', ErrorSeverity.MEDIUM),
            'YIELD-012': ('Total return calculation failed', ErrorSeverity.MEDIUM)
        })
        
        # Execution Interfaces
        self._register_component_codes("FACTORY", {
            'FACTORY-001': ('Interface creation failed', ErrorSeverity.HIGH),
            'FACTORY-002': ('Unsupported interface type', ErrorSeverity.HIGH),
            'FACTORY-003': ('Interface initialization failed', ErrorSeverity.HIGH),
            'FACTORY-004': ('Dependency injection failed', ErrorSeverity.HIGH),
            'FACTORY-005': ('Interface configuration invalid', ErrorSeverity.HIGH),
            'FACTORY-006': ('Interface connection failed', ErrorSeverity.HIGH)
        })
        
        self._register_component_codes("CEX-IF", {
            'CEX-IF-001': ('CEX trade execution failed', ErrorSeverity.HIGH),
            'CEX-IF-002': ('Exchange client not available', ErrorSeverity.HIGH),
            'CEX-IF-003': ('Order execution failed', ErrorSeverity.HIGH),
            'CEX-IF-004': ('Balance retrieval failed', ErrorSeverity.MEDIUM),
            'CEX-IF-005': ('Position retrieval failed', ErrorSeverity.MEDIUM),
            'CEX-IF-006': ('Transfer execution failed', ErrorSeverity.HIGH),
            'CEX-IF-007': ('Exchange client initialization failed', ErrorSeverity.HIGH),
            'CEX-IF-008': ('CCXT library not available', ErrorSeverity.HIGH)
        })
        
        self._register_component_codes("TRANSFER-IF", {
            'TRANSFER-IF-001': ('Transfer execution failed', ErrorSeverity.HIGH),
            'TRANSFER-IF-002': ('Transfer manager not initialized', ErrorSeverity.HIGH),
            'TRANSFER-IF-003': ('Transfer planning failed', ErrorSeverity.HIGH),
            'TRANSFER-IF-004': ('Transfer trade execution failed', ErrorSeverity.HIGH),
            'TRANSFER-IF-005': ('Transfer completion failed', ErrorSeverity.HIGH),
            'TRANSFER-IF-006': ('Transfer interface connection failed', ErrorSeverity.HIGH),
            'TRANSFER-IF-007': ('Transfer mapping failed', ErrorSeverity.MEDIUM)
        })
        
        self._register_component_codes("ONCHAIN-IF", {
            'ONCHAIN-IF-001': ('On-chain operation execution failed', ErrorSeverity.HIGH),
            'ONCHAIN-IF-002': ('Web3 client not available', ErrorSeverity.HIGH),
            'ONCHAIN-IF-003': ('Transaction building failed', ErrorSeverity.HIGH),
            'ONCHAIN-IF-004': ('Transaction signing failed', ErrorSeverity.HIGH),
            'ONCHAIN-IF-005': ('Transaction sending failed', ErrorSeverity.HIGH),
            'ONCHAIN-IF-006': ('Gas cost calculation failed', ErrorSeverity.MEDIUM),
            'ONCHAIN-IF-007': ('Contract interaction failed', ErrorSeverity.HIGH),
            'ONCHAIN-IF-008': ('Web3 library not available', ErrorSeverity.HIGH)
        })
    
    def _register_component_codes(self, component: str, codes: Dict[str, tuple]):
        """Register error codes for a component."""
        if component not in self._component_codes:
            self._component_codes[component] = []
        
        for code, (message, severity) in codes.items():
            error_info = ErrorCodeInfo(
                code=code,
                message=message,
                component=component,
                severity=severity
            )
            
            self._error_codes[code] = error_info
            self._component_codes[component].append(code)
            
            if severity not in self._severity_codes:
                self._severity_codes[severity] = []
            self._severity_codes[severity].append(code)
    
    def get_error_info(self, code: str) -> Optional[ErrorCodeInfo]:
        """Get error code information."""
        return self._error_codes.get(code)
    
    def get_component_codes(self, component: str) -> List[str]:
        """Get all error codes for a component."""
        return self._component_codes.get(component, [])
    
    def get_severity_codes(self, severity: ErrorSeverity) -> List[str]:
        """Get all error codes for a severity level."""
        return self._severity_codes.get(severity, [])
    
    def get_all_codes(self) -> List[str]:
        """Get all registered error codes."""
        return list(self._error_codes.keys())
    
    def validate_code(self, code: str) -> bool:
        """Validate if an error code exists."""
        return code in self._error_codes
    
    def get_critical_codes(self) -> List[str]:
        """Get all critical error codes."""
        return self.get_severity_codes(ErrorSeverity.CRITICAL)
    
    def get_high_severity_codes(self) -> List[str]:
        """Get all high and critical error codes."""
        return (self.get_severity_codes(ErrorSeverity.HIGH) + 
                self.get_severity_codes(ErrorSeverity.CRITICAL))
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of all error codes."""
        return {
            'total_codes': len(self._error_codes),
            'components': len(self._component_codes),
            'by_severity': {
                severity.value: len(codes) 
                for severity, codes in self._severity_codes.items()
            },
            'by_component': {
                component: len(codes) 
                for component, codes in self._component_codes.items()
            }
        }


# Global error code registry instance
error_code_registry = ErrorCodeRegistry()


def get_error_info(code: str) -> Optional[ErrorCodeInfo]:
    """Get error code information from global registry."""
    return error_code_registry.get_error_info(code)


def validate_error_code(code: str) -> bool:
    """Validate error code from global registry."""
    return error_code_registry.validate_code(code)


def get_component_error_codes(component: str) -> List[str]:
    """Get error codes for a component from global registry."""
    return error_code_registry.get_component_codes(component)
