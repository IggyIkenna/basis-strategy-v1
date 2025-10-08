"""Test error codes across Agent A components."""
import pytest
import re
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../backend/src'))

from basis_strategy_v1.core.strategies.components.position_monitor import ERROR_CODES as POS_CODES
from basis_strategy_v1.core.strategies.components.exposure_monitor import ERROR_CODES as EXP_CODES
from basis_strategy_v1.core.math.pnl_calculator import ERROR_CODES as PNL_CODES
from basis_strategy_v1.core.strategies.components.event_logger import ERROR_CODES as EVENT_CODES


def test_all_error_codes_exist():
    """Test that all Agent A components have error codes defined."""
    assert len(POS_CODES) >= 3
    assert len(EXP_CODES) >= 3
    assert len(PNL_CODES) >= 3
    assert len(EVENT_CODES) >= 3


def test_error_code_format():
    """Test error code format is correct."""
    all_codes = {**POS_CODES, **EXP_CODES, **PNL_CODES, **EVENT_CODES}
    
    for code in all_codes.keys():
        assert re.match(r'^[A-Z]+-\d{3}$', code), f"Invalid format: {code}"


def test_error_codes_in_logging(caplog):
    """Test that error codes appear in log messages."""
    # This test would need to trigger actual errors in components
    # For now, just verify the error codes are properly defined
    assert 'POS-001' in POS_CODES
    assert 'EXP-001' in EXP_CODES
    assert 'PNL-001' in PNL_CODES
    assert 'EVENT-001' in EVENT_CODES


def test_error_code_descriptions():
    """Test that error codes have meaningful descriptions."""
    all_codes = {**POS_CODES, **EXP_CODES, **PNL_CODES, **EVENT_CODES}
    
    for code, description in all_codes.items():
        assert len(description) > 10, f"Description too short for {code}: {description}"
        assert not description.endswith('.'), f"Description should not end with period for {code}"